#!/usr/bin/env python3
"""
PPO训练器实现
基于PPO算法训练方案文档的完整训练系统
"""

import torch
import torch.nn as nn
import torch.optim as optim
import numpy as np
import time
import os
import json
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass, field
from collections import deque
import logging

from ..ppo_agent import PPOAgent, PPOConfig, MultiAgentPPO
from ..training_environment import SanguoshaEnvironment, TrainingConfig
from ..game_state_encoder import GameStateEncoder
from ..neural_networks import ActorCriticNetwork

@dataclass
class PPOTrainingConfig:
    """PPO训练配置"""
    # 基础训练参数
    max_episodes: int = 100000
    max_steps_per_episode: int = 1000
    rollout_steps: int = 2048
    evaluation_interval: int = 1000
    save_interval: int = 5000
    
    # PPO特定参数
    ppo_epochs: int = 4
    mini_batch_size: int = 64
    clip_epsilon: float = 0.2
    learning_rate: float = 3e-4
    gamma: float = 0.99
    gae_lambda: float = 0.95
    entropy_coef: float = 0.01
    value_coef: float = 0.5
    max_grad_norm: float = 0.5
    
    # 网络架构参数
    state_dim: int = 366
    action_dim: int = 61
    hidden_dim: int = 512
    attention_heads: int = 8
    
    # 课程学习参数
    curriculum_learning: bool = True
    curriculum_stages: List[Dict] = field(default_factory=lambda: [
        {"name": "basic", "episodes": 20000, "difficulty": 0.3},
        {"name": "intermediate", "episodes": 40000, "difficulty": 0.6},
        {"name": "advanced", "episodes": 40000, "difficulty": 1.0}
    ])
    
    # 自对弈参数
    self_play: bool = True
    opponent_update_interval: int = 2000
    
    # 日志和保存路径
    log_dir: str = "logs/ppo"
    model_dir: str = "models/ppo"
    experiment_name: str = "ppo_sanguosha"

class ExperienceCollector:
    """经验收集器"""
    
    def __init__(self, env: SanguoshaEnvironment, agent: PPOAgent, config: PPOTrainingConfig):
        self.env = env
        self.agent = agent
        self.config = config
        self.state_encoder = GameStateEncoder()
        
    def collect_experiences(self, num_steps: int) -> Dict:
        """收集指定步数的经验"""
        experiences = {
            'states': [],
            'actions': [],
            'rewards': [],
            'next_states': [],
            'dones': [],
            'log_probs': [],
            'values': [],
            'action_masks': []
        }
        
        state = self.env.reset()
        episode_reward = 0
        episode_length = 0
        
        for step in range(num_steps):
            # 编码当前状态
            current_player = self.env.current_player
            state_vector = self.state_encoder.encode_game_state(state, current_player)
            action_mask = self.env.get_action_mask()
            
            # 选择动作
            action, log_prob, value = self.agent.select_action(
                state, current_player, action_mask, training=True
            )
            
            # 执行动作
            next_state, reward, done, info = self.env.step(action)
            
            # 存储经验
            experiences['states'].append(state_vector.to_vector())
            experiences['actions'].append(action)
            experiences['rewards'].append(reward)
            experiences['next_states'].append(next_state)
            experiences['dones'].append(done)
            experiences['log_probs'].append(log_prob)
            experiences['values'].append(value)
            experiences['action_masks'].append(action_mask)
            
            episode_reward += reward
            episode_length += 1
            
            if done or episode_length >= self.config.max_steps_per_episode:
                state = self.env.reset()
                episode_reward = 0
                episode_length = 0
            else:
                state = next_state
        
        # 转换为张量
        for key in experiences:
            if key in ['states', 'next_states', 'action_masks']:
                experiences[key] = torch.FloatTensor(experiences[key])
            elif key in ['actions']:
                experiences[key] = torch.LongTensor(experiences[key])
            else:
                experiences[key] = torch.FloatTensor(experiences[key])
        
        return experiences

class CurriculumLearning:
    """课程学习管理器"""
    
    def __init__(self, config: PPOTrainingConfig):
        self.config = config
        self.current_stage = 0
        self.stage_episodes = 0
        self.stages = config.curriculum_stages
        
    def get_current_difficulty(self) -> float:
        """获取当前难度"""
        if self.current_stage >= len(self.stages):
            return 1.0
        return self.stages[self.current_stage]["difficulty"]
    
    def update_stage(self, episode: int):
        """更新课程学习阶段"""
        if self.current_stage >= len(self.stages):
            return
        
        current_stage_info = self.stages[self.current_stage]
        if episode >= current_stage_info["episodes"]:
            self.current_stage += 1
            self.stage_episodes = 0
            if self.current_stage < len(self.stages):
                logging.info(f"进入课程学习阶段: {self.stages[self.current_stage]['name']}")
        else:
            self.stage_episodes += 1

class PPOTrainer:
    """PPO训练器主类"""
    
    def __init__(self, config: PPOTrainingConfig):
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
        
        # 初始化PPO配置
        ppo_config = PPOConfig(
            state_dim=config.state_dim,
            action_dim=config.action_dim,
            hidden_dim=config.hidden_dim,
            learning_rate=config.learning_rate,
            gamma=config.gamma,
            gae_lambda=config.gae_lambda,
            clip_epsilon=config.clip_epsilon,
            entropy_coef=config.entropy_coef,
            value_coef=config.value_coef,
            max_grad_norm=config.max_grad_norm,
            batch_size=config.rollout_steps,
            mini_batch_size=config.mini_batch_size,
            ppo_epochs=config.ppo_epochs
        )
        
        # 初始化智能体
        if config.self_play:
            self.agent = MultiAgentPPO(ppo_config, num_agents=2)
        else:
            self.agent = PPOAgent(ppo_config)
        
        # 经验收集器
        main_agent = self.agent.agents[0] if config.self_play else self.agent
        self.collector = ExperienceCollector(self.env, main_agent, config)
        
        # 课程学习
        if config.curriculum_learning:
            self.curriculum = CurriculumLearning(config)
        
        # 训练统计
        self.training_stats = {
            'episode_rewards': deque(maxlen=1000),
            'episode_lengths': deque(maxlen=1000),
            'win_rates': deque(maxlen=100),
            'policy_losses': deque(maxlen=1000),
            'value_losses': deque(maxlen=1000),
            'entropy_losses': deque(maxlen=1000)
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
        logging.info("开始PPO训练...")
        logging.info(f"设备: {self.device}")
        logging.info(f"配置: {self.config}")
        
        start_time = time.time()
        total_steps = 0
        
        for episode in range(self.config.max_episodes):
            # 更新课程学习阶段
            if self.config.curriculum_learning:
                self.curriculum.update_stage(episode)
                difficulty = self.curriculum.get_current_difficulty()
                self.env.set_difficulty(difficulty)
            
            # 收集经验
            experiences = self.collector.collect_experiences(self.config.rollout_steps)
            total_steps += self.config.rollout_steps
            
            # 计算GAE和回报
            self._compute_gae_and_returns(experiences)
            
            # PPO更新
            training_metrics = self._ppo_update(experiences)
            
            # 记录训练指标
            self._record_training_metrics(training_metrics)
            
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
            
            # 自对弈对手更新
            if (self.config.self_play and 
                episode % self.config.opponent_update_interval == 0 and 
                episode > 0):
                self._update_opponent()
            
            # 打印训练进度
            if episode % 100 == 0:
                self._print_training_progress(episode, total_steps, start_time)
        
        logging.info("PPO训练完成！")
        return self.best_model_path
    
    def _compute_gae_and_returns(self, experiences: Dict):
        """计算GAE优势估计和回报"""
        rewards = experiences['rewards']
        values = experiences['values']
        dones = experiences['dones']
        
        advantages = []
        returns = []
        gae = 0
        
        # 反向计算GAE
        for i in reversed(range(len(rewards))):
            if i == len(rewards) - 1:
                next_non_terminal = 1.0 - dones[i]
                next_value = 0.0  # 终端状态的价值为0
            else:
                next_non_terminal = 1.0 - dones[i]
                next_value = values[i + 1]
            
            delta = rewards[i] + self.config.gamma * next_value * next_non_terminal - values[i]
            gae = delta + self.config.gamma * self.config.gae_lambda * next_non_terminal * gae
            
            advantages.insert(0, gae)
            returns.insert(0, gae + values[i])
        
        # 标准化优势
        advantages = torch.FloatTensor(advantages)
        advantages = (advantages - advantages.mean()) / (advantages.std() + 1e-8)
        
        experiences['advantages'] = advantages
        experiences['returns'] = torch.FloatTensor(returns)
    
    def _ppo_update(self, experiences: Dict) -> Dict:
        """执行PPO更新"""
        training_metrics = {
            'policy_loss': [],
            'value_loss': [],
            'entropy_loss': [],
            'total_loss': [],
            'kl_divergence': [],
            'clip_fraction': []
        }
        
        # 获取主智能体
        main_agent = self.agent.agents[0] if self.config.self_play else self.agent
        
        # 多轮PPO更新
        for epoch in range(self.config.ppo_epochs):
            # 随机打乱数据
            indices = torch.randperm(len(experiences['states']))
            
            # 小批次训练
            for start in range(0, len(indices), self.config.mini_batch_size):
                end = min(start + self.config.mini_batch_size, len(indices))
                batch_indices = indices[start:end]
                
                # 构建批次数据
                batch = {
                    key: value[batch_indices] for key, value in experiences.items()
                }
                
                # 执行单步更新
                step_metrics = self._update_step(main_agent, batch)
                
                # 记录指标
                for key, value in step_metrics.items():
                    training_metrics[key].append(value)
        
        # 计算平均指标
        avg_metrics = {
            key: np.mean(values) for key, values in training_metrics.items()
        }
        
        return avg_metrics
    
    def _update_step(self, agent: PPOAgent, batch: Dict) -> Dict:
        """执行单步网络更新"""
        states = batch['states'].to(self.device)
        actions = batch['actions'].to(self.device)
        old_log_probs = batch['log_probs'].to(self.device)
        advantages = batch['advantages'].to(self.device)
        returns = batch['returns'].to(self.device)
        action_masks = batch['action_masks'].to(self.device)
        
        # 前向传播
        action_probs, values = agent.network(states, action_masks)
        dist = torch.distributions.Categorical(action_probs)
        new_log_probs = dist.log_prob(actions)
        entropy = dist.entropy()
        
        # 计算比率
        ratio = torch.exp(new_log_probs - old_log_probs)
        
        # PPO裁剪损失
        surr1 = ratio * advantages
        surr2 = torch.clamp(ratio, 1 - self.config.clip_epsilon, 1 + self.config.clip_epsilon) * advantages
        policy_loss = -torch.min(surr1, surr2).mean()
        
        # 价值损失
        value_loss = nn.MSELoss()(values.squeeze(), returns)
        
        # 熵损失
        entropy_loss = -entropy.mean()
        
        # 总损失
        total_loss = (policy_loss + 
                     self.config.value_coef * value_loss + 
                     self.config.entropy_coef * entropy_loss)
        
        # 反向传播
        agent.optimizer.zero_grad()
        total_loss.backward()
        torch.nn.utils.clip_grad_norm_(agent.network.parameters(), self.config.max_grad_norm)
        agent.optimizer.step()
        
        # 计算统计指标
        with torch.no_grad():
            kl_div = (old_log_probs - new_log_probs).mean()
            clip_fraction = ((ratio - 1.0).abs() > self.config.clip_epsilon).float().mean()
        
        return {
            'policy_loss': policy_loss.item(),
            'value_loss': value_loss.item(),
            'entropy_loss': entropy_loss.item(),
            'total_loss': total_loss.item(),
            'kl_divergence': kl_div.item(),
            'clip_fraction': clip_fraction.item()
        }
    
    def _evaluate_model(self) -> Dict:
        """评估模型性能"""
        eval_episodes = 50
        wins = 0
        total_rewards = []
        episode_lengths = []
        
        main_agent = self.agent.agents[0] if self.config.self_play else self.agent
        
        for _ in range(eval_episodes):
            state = self.env.reset()
            episode_reward = 0
            episode_length = 0
            done = False
            
            while not done and episode_length < self.config.max_steps_per_episode:
                current_player = self.env.current_player
                action_mask = self.env.get_action_mask()
                
                # 使用确定性策略
                action, _, _ = main_agent.select_action(
                    state, current_player, action_mask, 
                    training=False, deterministic=True
                )
                
                state, reward, done, info = self.env.step(action)
                episode_reward += reward
                episode_length += 1
            
            total_rewards.append(episode_reward)
            episode_lengths.append(episode_length)
            
            # 检查是否获胜
            if info.get('winner') == self.env.current_player:
                wins += 1
        
        return {
            'win_rate': wins / eval_episodes,
            'avg_reward': np.mean(total_rewards),
            'avg_episode_length': np.mean(episode_lengths),
            'reward_std': np.std(total_rewards)
        }
    
    def _record_training_metrics(self, metrics: Dict):
        """记录训练指标"""
        for key, value in metrics.items():
            if key in self.training_stats:
                self.training_stats[key].append(value)
    
    def _log_evaluation_metrics(self, episode: int, metrics: Dict):
        """记录评估指标"""
        logging.info(f"Episode {episode} - 评估结果:")
        for key, value in metrics.items():
            logging.info(f"  {key}: {value:.4f}")
        
        # 更新统计
        self.training_stats['win_rates'].append(metrics['win_rate'])
    
    def _save_best_model(self, episode: int) -> str:
        """保存最佳模型"""
        model_path = os.path.join(self.config.model_dir, f"best_model_episode_{episode}.pth")
        
        if self.config.self_play:
            self.agent.save_all_models(model_path.replace('.pth', ''))
        else:
            self.agent.save_model(model_path)
        
        logging.info(f"保存最佳模型: {model_path} (胜率: {self.best_win_rate:.4f})")
        return model_path
    
    def _save_checkpoint(self, episode: int):
        """保存训练检查点"""
        checkpoint_path = os.path.join(self.config.model_dir, f"checkpoint_episode_{episode}.pth")
        
        checkpoint = {
            'episode': episode,
            'config': self.config,
            'training_stats': dict(self.training_stats),
            'best_win_rate': self.best_win_rate
        }
        
        if self.config.self_play:
            for i, agent in enumerate(self.agent.agents):
                checkpoint[f'agent_{i}_state_dict'] = agent.network.state_dict()
                checkpoint[f'agent_{i}_optimizer'] = agent.optimizer.state_dict()
        else:
            checkpoint['agent_state_dict'] = self.agent.network.state_dict()
            checkpoint['agent_optimizer'] = self.agent.optimizer.state_dict()
        
        torch.save(checkpoint, checkpoint_path)
        logging.info(f"保存检查点: {checkpoint_path}")
    
    def _update_opponent(self):
        """更新自对弈对手"""
        if self.config.self_play and len(self.agent.agents) >= 2:
            # 将当前最佳智能体复制给对手
            self.agent.agents[1].network.load_state_dict(
                self.agent.agents[0].network.state_dict()
            )
            logging.info("更新自对弈对手模型")
    
    def _print_training_progress(self, episode: int, total_steps: int, start_time: float):
        """打印训练进度"""
        elapsed_time = time.time() - start_time
        
        # 计算平均指标
        avg_reward = np.mean(list(self.training_stats['episode_rewards'])[-100:]) if self.training_stats['episode_rewards'] else 0
        avg_length = np.mean(list(self.training_stats['episode_lengths'])[-100:]) if self.training_stats['episode_lengths'] else 0
        recent_win_rate = np.mean(list(self.training_stats['win_rates'])[-10:]) if self.training_stats['win_rates'] else 0
        
        logging.info(f"Episode {episode:6d} | Steps {total_steps:8d} | "
                    f"Reward {avg_reward:7.2f} | Length {avg_length:6.1f} | "
                    f"WinRate {recent_win_rate:5.3f} | Time {elapsed_time:6.1f}s")

def create_ppo_trainer(config_dict: Dict = None) -> PPOTrainer:
    """创建PPO训练器的工厂函数"""
    if config_dict is None:
        config = PPOTrainingConfig()
    else:
        config = PPOTrainingConfig(**config_dict)
    
    return PPOTrainer(config)

if __name__ == "__main__":
    # 测试PPO训练器
    config = PPOTrainingConfig(
        max_episodes=1000,
        evaluation_interval=100,
        save_interval=500
    )
    
    trainer = PPOTrainer(config)
    best_model_path = trainer.train()
    
    print(f"训练完成，最佳模型保存在: {best_model_path}")