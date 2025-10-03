#!/usr/bin/env python3
"""
DQN训练器实现
基于DQN算法训练方案文档的完整训练系统
"""

import torch
import torch.nn as nn
import torch.optim as optim
import torch.nn.functional as F
import numpy as np
import time
import os
import json
import random
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass, field
from collections import deque, namedtuple
import logging

from ..training_environment import SanguoshaEnvironment, TrainingConfig
from ..game_state_encoder import GameStateEncoder
from ..neural_networks import DuelingNetwork

# 经验元组定义
Experience = namedtuple('Experience', ['state', 'action', 'reward', 'next_state', 'done', 'action_mask'])

@dataclass
class DQNTrainingConfig:
    """DQN训练配置"""
    # 基础训练参数
    max_episodes: int = 100000
    max_steps_per_episode: int = 1000
    evaluation_interval: int = 1000
    save_interval: int = 5000
    
    # DQN特定参数
    learning_rate: float = 1e-4
    gamma: float = 0.99
    epsilon_start: float = 1.0
    epsilon_end: float = 0.01
    epsilon_decay: float = 0.995
    target_update_frequency: int = 1000
    
    # 网络架构参数
    state_dim: int = 366
    action_dim: int = 61
    hidden_dim: int = 512
    use_dueling: bool = True
    use_double_dqn: bool = True
    
    # 经验回放参数
    buffer_size: int = 100000
    batch_size: int = 64
    min_buffer_size: int = 10000
    use_prioritized_replay: bool = True
    alpha: float = 0.6  # 优先级指数
    beta_start: float = 0.4  # 重要性采样指数
    beta_end: float = 1.0
    
    # 探索策略参数
    exploration_strategy: str = "epsilon_greedy"  # epsilon_greedy, ucb, noisy
    ucb_c: float = 2.0  # UCB探索参数
    
    # 多智能体参数
    multi_agent: bool = True
    num_agents: int = 2
    
    # 日志和保存路径
    log_dir: str = "logs/dqn"
    model_dir: str = "models/dqn"
    experiment_name: str = "dqn_sanguosha"

class PrioritizedExperienceReplay:
    """优先级经验回放缓冲区"""
    
    def __init__(self, capacity: int, alpha: float = 0.6):
        self.capacity = capacity
        self.alpha = alpha
        self.buffer = []
        self.priorities = np.zeros((capacity,), dtype=np.float32)
        self.position = 0
        self.size = 0
        
    def add(self, experience: Experience, priority: float = None):
        """添加经验"""
        if priority is None:
            priority = max(self.priorities) if self.size > 0 else 1.0
        
        if self.size < self.capacity:
            self.buffer.append(experience)
        else:
            self.buffer[self.position] = experience
        
        self.priorities[self.position] = priority
        self.position = (self.position + 1) % self.capacity
        self.size = min(self.size + 1, self.capacity)
    
    def sample(self, batch_size: int, beta: float = 0.4):
        """采样经验批次"""
        if self.size < batch_size:
            return None, None, None
        
        # 计算采样概率
        priorities = self.priorities[:self.size]
        probs = priorities ** self.alpha
        probs /= probs.sum()
        
        # 采样索引
        indices = np.random.choice(self.size, batch_size, p=probs)
        
        # 计算重要性采样权重
        weights = (self.size * probs[indices]) ** (-beta)
        weights /= weights.max()
        
        # 获取经验
        experiences = [self.buffer[idx] for idx in indices]
        
        return experiences, indices, weights
    
    def update_priorities(self, indices: np.ndarray, priorities: np.ndarray):
        """更新优先级"""
        for idx, priority in zip(indices, priorities):
            self.priorities[idx] = priority + 1e-6  # 避免零优先级
    
    def __len__(self):
        return self.size

class EpsilonScheduler:
    """ε-贪婪探索调度器"""
    
    def __init__(self, start: float, end: float, decay: float):
        self.start = start
        self.end = end
        self.decay = decay
        self.current = start
    
    def get_epsilon(self, step: int = None) -> float:
        """获取当前ε值"""
        if step is not None:
            self.current = self.end + (self.start - self.end) * np.exp(-step * self.decay)
        else:
            self.current = max(self.end, self.current * self.decay)
        return self.current

class UCBExploration:
    """UCB探索策略"""
    
    def __init__(self, action_dim: int, c: float = 2.0):
        self.action_dim = action_dim
        self.c = c
        self.action_counts = np.zeros(action_dim)
        self.total_count = 0
    
    def select_action(self, q_values: np.ndarray, action_mask: np.ndarray = None) -> int:
        """使用UCB策略选择动作"""
        self.total_count += 1
        
        if action_mask is None:
            action_mask = np.ones(self.action_dim)
        
        # 计算UCB值
        ucb_values = np.zeros(self.action_dim)
        for a in range(self.action_dim):
            if action_mask[a] == 0:
                ucb_values[a] = -np.inf
            elif self.action_counts[a] == 0:
                ucb_values[a] = np.inf
            else:
                confidence = self.c * np.sqrt(np.log(self.total_count) / self.action_counts[a])
                ucb_values[a] = q_values[a] + confidence
        
        action = np.argmax(ucb_values)
        self.action_counts[action] += 1
        return action

class DQNNetwork(nn.Module):
    """DQN网络（支持Dueling架构）"""
    
    def __init__(self, state_dim: int, action_dim: int, hidden_dim: int = 512, use_dueling: bool = True):
        super(DQNNetwork, self).__init__()
        self.state_dim = state_dim
        self.action_dim = action_dim
        self.use_dueling = use_dueling
        
        # 状态编码器
        self.state_encoder = nn.Sequential(
            nn.Linear(state_dim, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, hidden_dim),
            nn.ReLU()
        )
        
        if use_dueling:
            # Dueling DQN架构
            self.value_head = nn.Sequential(
                nn.Linear(hidden_dim, hidden_dim // 2),
                nn.ReLU(),
                nn.Linear(hidden_dim // 2, 1)
            )
            
            self.advantage_head = nn.Sequential(
                nn.Linear(hidden_dim, hidden_dim // 2),
                nn.ReLU(),
                nn.Linear(hidden_dim // 2, action_dim)
            )
        else:
            # 标准DQN架构
            self.q_head = nn.Sequential(
                nn.Linear(hidden_dim, hidden_dim // 2),
                nn.ReLU(),
                nn.Linear(hidden_dim // 2, action_dim)
            )
    
    def forward(self, state: torch.Tensor, action_mask: torch.Tensor = None) -> torch.Tensor:
        """前向传播"""
        features = self.state_encoder(state)
        
        if self.use_dueling:
            value = self.value_head(features)
            advantage = self.advantage_head(features)
            
            # Dueling公式：Q(s,a) = V(s) + A(s,a) - mean(A(s,:))
            q_values = value + advantage - advantage.mean(dim=-1, keepdim=True)
        else:
            q_values = self.q_head(features)
        
        # 应用动作掩码
        if action_mask is not None:
            q_values = q_values.masked_fill(action_mask == 0, -float('inf'))
        
        return q_values

class DQNAgent:
    """DQN智能体"""
    
    def __init__(self, config: DQNTrainingConfig):
        self.config = config
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        
        # 初始化网络
        self.q_network = DQNNetwork(
            config.state_dim, 
            config.action_dim, 
            config.hidden_dim,
            config.use_dueling
        ).to(self.device)
        
        self.target_network = DQNNetwork(
            config.state_dim, 
            config.action_dim, 
            config.hidden_dim,
            config.use_dueling
        ).to(self.device)
        
        # 初始化目标网络
        self.target_network.load_state_dict(self.q_network.state_dict())
        
        # 优化器
        self.optimizer = optim.Adam(self.q_network.parameters(), lr=config.learning_rate)
        
        # 经验回放
        if config.use_prioritized_replay:
            self.replay_buffer = PrioritizedExperienceReplay(config.buffer_size, config.alpha)
        else:
            self.replay_buffer = deque(maxlen=config.buffer_size)
        
        # 探索策略
        self.epsilon_scheduler = EpsilonScheduler(
            config.epsilon_start, config.epsilon_end, config.epsilon_decay
        )
        
        if config.exploration_strategy == "ucb":
            self.ucb_explorer = UCBExploration(config.action_dim, config.ucb_c)
        
        # 状态编码器
        self.state_encoder = GameStateEncoder()
        
        # 训练统计
        self.training_step = 0
        self.episode_count = 0
        
    def select_action(self, game_state, current_player, action_mask=None, training=True, deterministic=False):
        """选择动作"""
        # 编码状态
        state_vector = self.state_encoder.encode_game_state(game_state, current_player)
        state_tensor = torch.FloatTensor(state_vector.to_vector()).unsqueeze(0).to(self.device)
        
        # 处理动作掩码
        if action_mask is not None:
            mask_tensor = torch.FloatTensor(action_mask).unsqueeze(0).to(self.device)
        else:
            mask_tensor = torch.ones(1, self.config.action_dim).to(self.device)
        
        with torch.no_grad():
            q_values = self.q_network(state_tensor, mask_tensor)
        
        if deterministic or not training:
            # 确定性策略：选择Q值最高的动作
            action = torch.argmax(q_values, dim=-1).item()
        else:
            # 探索策略
            if self.config.exploration_strategy == "epsilon_greedy":
                epsilon = self.epsilon_scheduler.get_epsilon()
                if random.random() < epsilon:
                    # 随机选择合法动作
                    valid_actions = np.where(action_mask if action_mask is not None else np.ones(self.config.action_dim))[0]
                    action = np.random.choice(valid_actions)
                else:
                    action = torch.argmax(q_values, dim=-1).item()
            
            elif self.config.exploration_strategy == "ucb":
                q_vals = q_values.cpu().numpy().flatten()
                action = self.ucb_explorer.select_action(q_vals, action_mask)
            
            else:  # 默认贪婪策略
                action = torch.argmax(q_values, dim=-1).item()
        
        return action
    
    def store_experience(self, state, action, reward, next_state, done, action_mask=None):
        """存储经验"""
        experience = Experience(state, action, reward, next_state, done, action_mask)
        
        if self.config.use_prioritized_replay:
            self.replay_buffer.add(experience)
        else:
            self.replay_buffer.append(experience)
    
    def update(self):
        """更新网络"""
        if len(self.replay_buffer) < self.config.min_buffer_size:
            return {}
        
        # 采样经验
        if self.config.use_prioritized_replay:
            beta = self.config.beta_start + (self.config.beta_end - self.config.beta_start) * \
                   min(1.0, self.training_step / 100000)
            experiences, indices, weights = self.replay_buffer.sample(self.config.batch_size, beta)
            if experiences is None:
                return {}
        else:
            experiences = random.sample(self.replay_buffer, self.config.batch_size)
            weights = np.ones(self.config.batch_size)
            indices = None
        
        # 准备批次数据
        states = torch.FloatTensor([exp.state for exp in experiences]).to(self.device)
        actions = torch.LongTensor([exp.action for exp in experiences]).to(self.device)
        rewards = torch.FloatTensor([exp.reward for exp in experiences]).to(self.device)
        next_states = torch.FloatTensor([exp.next_state for exp in experiences]).to(self.device)
        dones = torch.BoolTensor([exp.done for exp in experiences]).to(self.device)
        action_masks = torch.FloatTensor([exp.action_mask if exp.action_mask is not None 
                                        else np.ones(self.config.action_dim) for exp in experiences]).to(self.device)
        weights = torch.FloatTensor(weights).to(self.device)
        
        # 计算当前Q值
        current_q_values = self.q_network(states, action_masks).gather(1, actions.unsqueeze(1))
        
        # 计算目标Q值
        with torch.no_grad():
            if self.config.use_double_dqn:
                # Double DQN
                next_actions = self.q_network(next_states, action_masks).argmax(1)
                next_q_values = self.target_network(next_states, action_masks).gather(1, next_actions.unsqueeze(1))
            else:
                # 标准DQN
                next_q_values = self.target_network(next_states, action_masks).max(1)[0].unsqueeze(1)
            
            target_q_values = rewards.unsqueeze(1) + (self.config.gamma * next_q_values * ~dones.unsqueeze(1))
        
        # 计算TD误差
        td_errors = target_q_values - current_q_values
        
        # 计算损失（使用重要性采样权重）
        loss = (weights.unsqueeze(1) * td_errors.pow(2)).mean()
        
        # 反向传播
        self.optimizer.zero_grad()
        loss.backward()
        torch.nn.utils.clip_grad_norm_(self.q_network.parameters(), 10.0)
        self.optimizer.step()
        
        # 更新优先级
        if self.config.use_prioritized_replay and indices is not None:
            priorities = td_errors.abs().detach().cpu().numpy().flatten()
            self.replay_buffer.update_priorities(indices, priorities)
        
        # 更新目标网络
        if self.training_step % self.config.target_update_frequency == 0:
            self.target_network.load_state_dict(self.q_network.state_dict())
        
        self.training_step += 1
        
        return {
            'loss': loss.item(),
            'avg_q_value': current_q_values.mean().item(),
            'td_error': td_errors.abs().mean().item(),
            'epsilon': self.epsilon_scheduler.current
        }
    
    def save_model(self, filepath: str):
        """保存模型"""
        torch.save({
            'q_network_state_dict': self.q_network.state_dict(),
            'target_network_state_dict': self.target_network.state_dict(),
            'optimizer_state_dict': self.optimizer.state_dict(),
            'config': self.config,
            'training_step': self.training_step,
            'episode_count': self.episode_count
        }, filepath)
    
    def load_model(self, filepath: str):
        """加载模型"""
        checkpoint = torch.load(filepath, map_location=self.device)
        self.q_network.load_state_dict(checkpoint['q_network_state_dict'])
        self.target_network.load_state_dict(checkpoint['target_network_state_dict'])
        self.optimizer.load_state_dict(checkpoint['optimizer_state_dict'])
        self.training_step = checkpoint.get('training_step', 0)
        self.episode_count = checkpoint.get('episode_count', 0)

class MultiAgentDQNTrainer:
    """多智能体DQN训练器"""
    
    def __init__(self, config: DQNTrainingConfig):
        self.config = config
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        
        # 创建目录
        os.makedirs(config.log_dir, exist_ok=True)
        os.makedirs(config.model_dir, exist_ok=True)
        
        # 设置日志
        self._setup_logging()
        
        # 初始化环境
        env_config = TrainingConfig()
        self.env = SanguoshaEnvironment(env_config)
        
        # 初始化智能体
        self.agents = [DQNAgent(config) for _ in range(config.num_agents)]
        
        # 训练统计
        self.training_stats = {
            'episode_rewards': deque(maxlen=1000),
            'episode_lengths': deque(maxlen=1000),
            'win_rates': deque(maxlen=100),
            'losses': deque(maxlen=1000),
            'q_values': deque(maxlen=1000)
        }
        
        # 最佳模型跟踪
        self.best_win_rate = 0.0
        self.best_model_path = None
        
    def _setup_logging(self):
        """设置日志系统"""
        log_file = os.path.join(self.config.log_dir, f"{self.config.experiment_name}.log")
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler()
            ]
        )
    
    def train(self):
        """主训练循环"""
        logging.info("开始DQN训练...")
        logging.info(f"设备: {self.device}")
        logging.info(f"配置: {self.config}")
        
        start_time = time.time()
        
        for episode in range(self.config.max_episodes):
            episode_reward, episode_length = self._run_episode()
            
            # 记录统计信息
            self.training_stats['episode_rewards'].append(episode_reward)
            self.training_stats['episode_lengths'].append(episode_length)
            
            # 更新网络
            for agent in self.agents:
                metrics = agent.update()
                if metrics:
                    self.training_stats['losses'].append(metrics['loss'])
                    self.training_stats['q_values'].append(metrics['avg_q_value'])
            
            # 评估模型
            if episode % self.config.evaluation_interval == 0:
                eval_metrics = self._evaluate_model()
                self._log_evaluation_metrics(episode, eval_metrics)
                
                # 保存最佳模型
                if eval_metrics['win_rate'] > self.best_win_rate:
                    self.best_win_rate = eval_metrics['win_rate']
                    self.best_model_path = self._save_best_model(episode)
            
            # 定期保存检查点
            if episode % self.config.save_interval == 0:
                self._save_checkpoint(episode)
            
            # 打印训练进度
            if episode % 100 == 0:
                self._print_training_progress(episode, start_time)
        
        logging.info("DQN训练完成！")
        return self.best_model_path
    
    def _run_episode(self) -> Tuple[float, int]:
        """运行一个训练回合"""
        state = self.env.reset()
        total_reward = 0
        episode_length = 0
        
        while episode_length < self.config.max_steps_per_episode:
            current_player = self.env.current_player
            agent = self.agents[current_player]
            action_mask = self.env.get_action_mask()
            
            # 选择动作
            action = agent.select_action(state, current_player, action_mask, training=True)
            
            # 执行动作
            next_state, reward, done, info = self.env.step(action)
            
            # 存储经验
            state_vector = agent.state_encoder.encode_game_state(state, current_player).to_vector()
            next_state_vector = agent.state_encoder.encode_game_state(next_state, current_player).to_vector()
            
            agent.store_experience(state_vector, action, reward, next_state_vector, done, action_mask)
            
            total_reward += reward
            episode_length += 1
            
            if done:
                break
            
            state = next_state
        
        return total_reward, episode_length
    
    def _evaluate_model(self) -> Dict:
        """评估模型性能"""
        eval_episodes = 50
        wins = 0
        total_rewards = []
        episode_lengths = []
        
        for _ in range(eval_episodes):
            state = self.env.reset()
            episode_reward = 0
            episode_length = 0
            done = False
            
            while not done and episode_length < self.config.max_steps_per_episode:
                current_player = self.env.current_player
                agent = self.agents[current_player]
                action_mask = self.env.get_action_mask()
                
                # 使用确定性策略
                action = agent.select_action(
                    state, current_player, action_mask, 
                    training=False, deterministic=True
                )
                
                state, reward, done, info = self.env.step(action)
                episode_reward += reward
                episode_length += 1
            
            total_rewards.append(episode_reward)
            episode_lengths.append(episode_length)
            
            # 检查是否获胜
            if info.get('winner') == 0:  # 假设智能体0为主要评估对象
                wins += 1
        
        return {
            'win_rate': wins / eval_episodes,
            'avg_reward': np.mean(total_rewards),
            'avg_episode_length': np.mean(episode_lengths),
            'reward_std': np.std(total_rewards)
        }
    
    def _log_evaluation_metrics(self, episode: int, metrics: Dict):
        """记录评估指标"""
        logging.info(f"Episode {episode} - 评估结果:")
        for key, value in metrics.items():
            logging.info(f"  {key}: {value:.4f}")
        
        self.training_stats['win_rates'].append(metrics['win_rate'])
    
    def _save_best_model(self, episode: int) -> str:
        """保存最佳模型"""
        model_path = os.path.join(self.config.model_dir, f"best_dqn_model_episode_{episode}")
        
        for i, agent in enumerate(self.agents):
            agent.save_model(f"{model_path}_agent_{i}.pth")
        
        logging.info(f"保存最佳模型: {model_path} (胜率: {self.best_win_rate:.4f})")
        return model_path
    
    def _save_checkpoint(self, episode: int):
        """保存训练检查点"""
        checkpoint_path = os.path.join(self.config.model_dir, f"dqn_checkpoint_episode_{episode}.pth")
        
        checkpoint = {
            'episode': episode,
            'config': self.config,
            'training_stats': dict(self.training_stats),
            'best_win_rate': self.best_win_rate
        }
        
        for i, agent in enumerate(self.agents):
            checkpoint[f'agent_{i}_q_network'] = agent.q_network.state_dict()
            checkpoint[f'agent_{i}_target_network'] = agent.target_network.state_dict()
            checkpoint[f'agent_{i}_optimizer'] = agent.optimizer.state_dict()
            checkpoint[f'agent_{i}_training_step'] = agent.training_step
        
        torch.save(checkpoint, checkpoint_path)
        logging.info(f"保存检查点: {checkpoint_path}")
    
    def _print_training_progress(self, episode: int, start_time: float):
        """打印训练进度"""
        elapsed_time = time.time() - start_time
        
        # 计算平均指标
        avg_reward = np.mean(list(self.training_stats['episode_rewards'])[-100:]) if self.training_stats['episode_rewards'] else 0
        avg_length = np.mean(list(self.training_stats['episode_lengths'])[-100:]) if self.training_stats['episode_lengths'] else 0
        recent_win_rate = np.mean(list(self.training_stats['win_rates'])[-10:]) if self.training_stats['win_rates'] else 0
        avg_loss = np.mean(list(self.training_stats['losses'])[-100:]) if self.training_stats['losses'] else 0
        
        logging.info(f"Episode {episode:6d} | Reward {avg_reward:7.2f} | Length {avg_length:6.1f} | "
                    f"WinRate {recent_win_rate:5.3f} | Loss {avg_loss:7.4f} | Time {elapsed_time:6.1f}s")

def create_dqn_trainer(config_dict: Dict = None) -> MultiAgentDQNTrainer:
    """创建DQN训练器的工厂函数"""
    if config_dict is None:
        config = DQNTrainingConfig()
    else:
        config = DQNTrainingConfig(**config_dict)
    
    return MultiAgentDQNTrainer(config)

if __name__ == "__main__":
    # 测试DQN训练器
    config = DQNTrainingConfig(
        max_episodes=1000,
        evaluation_interval=100,
        save_interval=500
    )
    
    trainer = MultiAgentDQNTrainer(config)
    best_model_path = trainer.train()
    
    print(f"训练完成，最佳模型保存在: {best_model_path}")