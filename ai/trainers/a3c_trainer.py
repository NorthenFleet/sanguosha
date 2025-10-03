#!/usr/bin/env python3
"""
A3C训练器实现
基于A3C算法训练方案文档的完整异步训练系统
"""

import torch
import torch.nn as nn
import torch.optim as optim
import torch.multiprocessing as mp
import numpy as np
import time
import os
import json
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass, field
from collections import deque
import logging
import threading

from ..training_environment import SanguoshaEnvironment, TrainingConfig
from ..game_state_encoder import GameStateEncoder
from ..neural_networks import ActorCriticNetwork

@dataclass
class A3CTrainingConfig:
    """A3C训练配置"""
    # 基础训练参数
    max_global_steps: int = 10000000
    max_episodes: int = 100000
    max_steps_per_episode: int = 1000
    evaluation_interval: int = 1000
    save_interval: int = 5000
    
    # A3C特定参数
    learning_rate: float = 1e-4
    gamma: float = 0.99
    gae_lambda: float = 0.95
    entropy_coef: float = 0.01
    value_coef: float = 0.5
    max_grad_norm: float = 40.0
    n_steps: int = 20  # 每次更新的步数
    
    # 网络架构参数
    state_dim: int = 366
    action_dim: int = 61
    hidden_dim: int = 512
    use_lstm: bool = False
    lstm_hidden_dim: int = 256
    
    # 多进程参数
    num_workers: int = 8
    
    # GAE参数
    use_gae: bool = True
    
    # 课程学习参数
    curriculum_learning: bool = True
    curriculum_stages: List[Dict] = field(default_factory=lambda: [
        {"name": "basic", "steps": 2000000, "difficulty": 0.3},
        {"name": "intermediate", "steps": 4000000, "difficulty": 0.6},
        {"name": "advanced", "steps": 4000000, "difficulty": 1.0}
    ])
    
    # 日志和保存路径
    log_dir: str = "logs/a3c"
    model_dir: str = "models/a3c"
    experiment_name: str = "a3c_sanguosha"

class A3CNetwork(nn.Module):
    """A3C网络架构"""
    
    def __init__(self, config: A3CTrainingConfig):
        super(A3CNetwork, self).__init__()
        self.config = config
        
        # 状态编码器
        self.state_encoder = nn.Sequential(
            nn.Linear(config.state_dim, config.hidden_dim),
            nn.ReLU(),
            nn.Linear(config.hidden_dim, config.hidden_dim),
            nn.ReLU()
        )
        
        # LSTM层（可选）
        if config.use_lstm:
            self.lstm = nn.LSTM(config.hidden_dim, config.lstm_hidden_dim, batch_first=True)
            feature_dim = config.lstm_hidden_dim
        else:
            feature_dim = config.hidden_dim
        
        # Actor网络（策略）
        self.actor = nn.Sequential(
            nn.Linear(feature_dim, config.hidden_dim // 2),
            nn.ReLU(),
            nn.Linear(config.hidden_dim // 2, config.action_dim),
            nn.Softmax(dim=-1)
        )
        
        # Critic网络（价值）
        self.critic = nn.Sequential(
            nn.Linear(feature_dim, config.hidden_dim // 2),
            nn.ReLU(),
            nn.Linear(config.hidden_dim // 2, 1)
        )
        
        # 初始化权重
        self._init_weights()
    
    def _init_weights(self):
        """初始化网络权重"""
        for module in self.modules():
            if isinstance(module, nn.Linear):
                nn.init.xavier_uniform_(module.weight)
                nn.init.constant_(module.bias, 0)
    
    def forward(self, state, hidden_state=None, action_mask=None):
        """前向传播"""
        # 状态编码
        features = self.state_encoder(state)
        
        # LSTM处理（如果使用）
        if self.config.use_lstm:
            if len(features.shape) == 2:
                features = features.unsqueeze(1)  # 添加序列维度
            
            if hidden_state is not None:
                features, new_hidden_state = self.lstm(features, hidden_state)
            else:
                features, new_hidden_state = self.lstm(features)
            
            features = features.squeeze(1)  # 移除序列维度
        else:
            new_hidden_state = None
        
        # 策略和价值输出
        action_probs = self.actor(features)
        value = self.critic(features)
        
        # 应用动作掩码
        if action_mask is not None:
            action_probs = action_probs * action_mask
            action_probs = action_probs / (action_probs.sum(dim=-1, keepdim=True) + 1e-8)
        
        return action_probs, value, new_hidden_state
    
    def get_action_and_value(self, state, hidden_state=None, action_mask=None):
        """获取动作和价值"""
        action_probs, value, new_hidden_state = self.forward(state, hidden_state, action_mask)
        
        # 创建分布并采样动作
        dist = torch.distributions.Categorical(action_probs)
        action = dist.sample()
        log_prob = dist.log_prob(action)
        entropy = dist.entropy()
        
        return action, log_prob, value, entropy, new_hidden_state

class A3CGlobalNetwork:
    """A3C全局网络"""
    
    def __init__(self, config: A3CTrainingConfig):
        self.config = config
        self.network = A3CNetwork(config)
        
        # 全局优化器
        self.optimizer = torch.optim.Adam(
            self.network.parameters(),
            lr=config.learning_rate
        )
        
        # 共享参数（用于多进程）
        self.network.share_memory()
        
        # 训练统计（多进程共享）
        self.global_step = mp.Value('i', 0)
        self.global_episode = mp.Value('i', 0)
        self.best_score = mp.Value('f', -float('inf'))
        
        # 锁机制
        self.lock = mp.Lock()
        
        # 训练统计队列
        self.stats_queue = mp.Queue()
        
    def update_global_network(self, local_gradients):
        """更新全局网络参数"""
        with self.lock:
            # 应用梯度
            for global_param, local_grad in zip(self.network.parameters(), local_gradients):
                if global_param.grad is None:
                    global_param.grad = local_grad.clone()
                else:
                    global_param.grad += local_grad
            
            # 梯度裁剪
            torch.nn.utils.clip_grad_norm_(
                self.network.parameters(), 
                self.config.max_grad_norm
            )
            
            # 参数更新
            self.optimizer.step()
            self.optimizer.zero_grad()
            
            # 更新全局步数
            with self.global_step.get_lock():
                self.global_step.value += 1
    
    def get_global_params(self):
        """获取全局网络参数"""
        return self.network.state_dict()
    
    def save_model(self, path):
        """保存模型"""
        torch.save({
            'network_state_dict': self.network.state_dict(),
            'optimizer_state_dict': self.optimizer.state_dict(),
            'config': self.config,
            'global_step': self.global_step.value,
            'global_episode': self.global_episode.value
        }, path)
    
    def load_model(self, path):
        """加载模型"""
        checkpoint = torch.load(path)
        self.network.load_state_dict(checkpoint['network_state_dict'])
        self.optimizer.load_state_dict(checkpoint['optimizer_state_dict'])
        with self.global_step.get_lock():
            self.global_step.value = checkpoint.get('global_step', 0)
        with self.global_episode.get_lock():
            self.global_episode.value = checkpoint.get('global_episode', 0)

class A3CWorker:
    """A3C工作进程"""
    
    def __init__(self, worker_id: int, global_network: A3CGlobalNetwork, config: A3CTrainingConfig):
        self.worker_id = worker_id
        self.global_network = global_network
        self.config = config
        
        # 本地网络
        self.local_network = A3CNetwork(config)
        
        # 环境
        env_config = TrainingConfig()
        self.env = SanguoshaEnvironment(env_config)
        self.state_encoder = GameStateEncoder()
        
        # 训练统计
        self.episode_count = 0
        self.step_count = 0
        self.total_reward = 0
        
        # 经验缓存
        self.reset_experience_cache()
        
    def reset_experience_cache(self):
        """重置经验缓存"""
        self.states = []
        self.actions = []
        self.rewards = []
        self.values = []
        self.log_probs = []
        self.entropies = []
        self.action_masks = []
        self.hidden_states = []
    
    def sync_with_global(self):
        """同步本地网络与全局网络"""
        self.local_network.load_state_dict(self.global_network.get_global_params())
    
    def compute_gae(self, next_value: float = 0.0):
        """计算GAE优势估计"""
        advantages = []
        returns = []
        gae = 0
        
        # 反向计算GAE
        for i in reversed(range(len(self.rewards))):
            if i == len(self.rewards) - 1:
                next_non_terminal = 0.0  # 最后一步
                next_value_est = next_value
            else:
                next_non_terminal = 1.0
                next_value_est = self.values[i + 1]
            
            delta = self.rewards[i] + self.config.gamma * next_value_est * next_non_terminal - self.values[i]
            gae = delta + self.config.gamma * self.config.gae_lambda * next_non_terminal * gae
            
            advantages.insert(0, gae)
            returns.insert(0, gae + self.values[i])
        
        return advantages, returns
    
    def compute_loss(self, advantages, returns):
        """计算A3C损失"""
        # 转换为张量
        states = torch.FloatTensor(self.states)
        actions = torch.LongTensor(self.actions)
        old_log_probs = torch.FloatTensor(self.log_probs)
        advantages = torch.FloatTensor(advantages)
        returns = torch.FloatTensor(returns)
        action_masks = torch.FloatTensor(self.action_masks)
        
        # 前向传播
        action_probs, values, _ = self.local_network(states, action_mask=action_masks)
        
        # 计算新的log概率和熵
        dist = torch.distributions.Categorical(action_probs)
        new_log_probs = dist.log_prob(actions)
        entropy = dist.entropy()
        
        # Actor损失（策略梯度）
        actor_loss = -(new_log_probs * advantages).mean()
        
        # Critic损失（价值函数）
        critic_loss = nn.MSELoss()(values.squeeze(), returns)
        
        # 熵损失（鼓励探索）
        entropy_loss = -entropy.mean()
        
        # 总损失
        total_loss = (actor_loss + 
                     self.config.value_coef * critic_loss + 
                     self.config.entropy_coef * entropy_loss)
        
        return total_loss, actor_loss, critic_loss, entropy_loss
    
    def update_global_network(self):
        """更新全局网络"""
        if len(self.states) == 0:
            return
        
        # 计算下一个状态的价值（用于GAE）
        if len(self.states) > 0:
            last_state = torch.FloatTensor(self.states[-1]).unsqueeze(0)
            with torch.no_grad():
                _, next_value, _ = self.local_network(last_state)
                next_value = next_value.item()
        else:
            next_value = 0.0
        
        # 计算优势和回报
        if self.config.use_gae:
            advantages, returns = self.compute_gae(next_value)
        else:
            # 简单的n步回报
            returns = []
            R = next_value
            for reward in reversed(self.rewards):
                R = reward + self.config.gamma * R
                returns.insert(0, R)
            advantages = [r - v for r, v in zip(returns, self.values)]
        
        # 计算损失
        total_loss, actor_loss, critic_loss, entropy_loss = self.compute_loss(advantages, returns)
        
        # 计算梯度
        self.local_network.zero_grad()
        total_loss.backward()
        
        # 获取梯度
        local_gradients = [param.grad.clone() if param.grad is not None else torch.zeros_like(param) 
                          for param in self.local_network.parameters()]
        
        # 更新全局网络
        self.global_network.update_global_network(local_gradients)
        
        # 同步本地网络
        self.sync_with_global()
        
        # 发送统计信息
        stats = {
            'worker_id': self.worker_id,
            'total_loss': total_loss.item(),
            'actor_loss': actor_loss.item(),
            'critic_loss': critic_loss.item(),
            'entropy_loss': entropy_loss.item(),
            'episode_reward': self.total_reward,
            'episode_length': len(self.states)
        }
        
        try:
            self.global_network.stats_queue.put_nowait(stats)
        except:
            pass  # 队列满时忽略
        
        # 重置经验缓存
        self.reset_experience_cache()
    
    def run(self):
        """Worker主循环"""
        print(f"Worker {self.worker_id} 开始运行...")
        
        # 同步初始参数
        self.sync_with_global()
        
        while self.global_network.global_step.value < self.config.max_global_steps:
            # 运行一个回合
            self.run_episode()
            
            # 更新全局网络
            if len(self.states) >= self.config.n_steps:
                self.update_global_network()
            
            self.episode_count += 1
        
        print(f"Worker {self.worker_id} 完成训练")
    
    def run_episode(self):
        """运行一个训练回合"""
        state = self.env.reset()
        self.total_reward = 0
        episode_length = 0
        hidden_state = None
        
        while episode_length < self.config.max_steps_per_episode:
            # 编码状态
            current_player = self.env.current_player
            state_vector = self.state_encoder.encode_game_state(state, current_player)
            state_tensor = torch.FloatTensor(state_vector.to_vector()).unsqueeze(0)
            
            # 获取动作掩码
            action_mask = self.env.get_action_mask()
            mask_tensor = torch.FloatTensor(action_mask).unsqueeze(0)
            
            # 选择动作
            with torch.no_grad():
                action, log_prob, value, entropy, new_hidden_state = self.local_network.get_action_and_value(
                    state_tensor, hidden_state, mask_tensor
                )
            
            # 执行动作
            next_state, reward, done, info = self.env.step(action.item())
            
            # 存储经验
            self.states.append(state_vector.to_vector())
            self.actions.append(action.item())
            self.rewards.append(reward)
            self.values.append(value.item())
            self.log_probs.append(log_prob.item())
            self.entropies.append(entropy.item())
            self.action_masks.append(action_mask)
            if self.config.use_lstm:
                self.hidden_states.append(hidden_state)
            
            self.total_reward += reward
            episode_length += 1
            self.step_count += 1
            
            # 更新隐藏状态
            hidden_state = new_hidden_state
            
            # 检查是否需要更新网络
            if len(self.states) >= self.config.n_steps or done:
                self.update_global_network()
                hidden_state = None  # 重置LSTM隐藏状态
            
            if done:
                break
            
            state = next_state

class A3CTrainer:
    """A3C训练器主类"""
    
    def __init__(self, config: A3CTrainingConfig):
        self.config = config
        
        # 创建目录
        os.makedirs(config.log_dir, exist_ok=True)
        os.makedirs(config.model_dir, exist_ok=True)
        
        # 设置日志
        self._setup_logging()
        
        # 创建全局网络
        self.global_network = A3CGlobalNetwork(config)
        
        # 训练统计
        self.training_stats = {
            'episode_rewards': deque(maxlen=1000),
            'episode_lengths': deque(maxlen=1000),
            'actor_losses': deque(maxlen=1000),
            'critic_losses': deque(maxlen=1000),
            'entropy_losses': deque(maxlen=1000)
        }
        
        # 最佳模型跟踪
        self.best_score = -float('inf')
        self.best_model_path = None
        
        # 统计收集线程
        self.stats_thread = None
        self.stop_stats_collection = False
        
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
    
    def _collect_stats(self):
        """收集训练统计信息"""
        while not self.stop_stats_collection:
            try:
                stats = self.global_network.stats_queue.get(timeout=1.0)
                
                # 更新统计信息
                self.training_stats['episode_rewards'].append(stats['episode_reward'])
                self.training_stats['episode_lengths'].append(stats['episode_length'])
                self.training_stats['actor_losses'].append(stats['actor_loss'])
                self.training_stats['critic_losses'].append(stats['critic_loss'])
                self.training_stats['entropy_losses'].append(stats['entropy_loss'])
                
                # 检查是否为最佳分数
                if stats['episode_reward'] > self.best_score:
                    self.best_score = stats['episode_reward']
                
            except:
                continue
    
    def train(self):
        """主训练流程"""
        logging.info("开始A3C训练...")
        logging.info(f"使用 {self.config.num_workers} 个worker")
        logging.info(f"配置: {self.config}")
        
        # 启动统计收集线程
        self.stats_thread = threading.Thread(target=self._collect_stats)
        self.stats_thread.start()
        
        # 创建worker进程
        processes = []
        for worker_id in range(self.config.num_workers):
            worker = A3CWorker(worker_id, self.global_network, self.config)
            process = mp.Process(target=worker.run)
            process.start()
            processes.append(process)
        
        # 主进程监控和评估
        self.monitor_training()
        
        # 等待所有worker完成
        for process in processes:
            process.join()
        
        # 停止统计收集
        self.stop_stats_collection = True
        if self.stats_thread:
            self.stats_thread.join()
        
        logging.info("A3C训练完成！")
        return self.best_model_path
    
    def monitor_training(self):
        """监控训练进度"""
        last_eval_step = 0
        last_save_step = 0
        start_time = time.time()
        
        while self.global_network.global_step.value < self.config.max_global_steps:
            current_step = self.global_network.global_step.value
            
            # 评估模型
            if current_step - last_eval_step >= self.config.evaluation_interval:
                eval_metrics = self._evaluate_model()
                self._log_evaluation_metrics(current_step, eval_metrics)
                
                # 保存最佳模型
                if eval_metrics['avg_reward'] > self.best_score:
                    self.best_score = eval_metrics['avg_reward']
                    self.best_model_path = self._save_best_model(current_step)
                
                last_eval_step = current_step
            
            # 定期保存检查点
            if current_step - last_save_step >= self.config.save_interval:
                self._save_checkpoint(current_step)
                last_save_step = current_step
            
            # 打印训练进度
            if current_step % 1000 == 0:
                self._print_training_progress(current_step, start_time)
            
            time.sleep(1)  # 避免过于频繁的检查
    
    def _evaluate_model(self) -> Dict:
        """评估模型性能"""
        eval_episodes = 20
        total_rewards = []
        episode_lengths = []
        
        # 创建评估环境
        env_config = TrainingConfig()
        eval_env = SanguoshaEnvironment(env_config)
        state_encoder = GameStateEncoder()
        
        for _ in range(eval_episodes):
            state = eval_env.reset()
            episode_reward = 0
            episode_length = 0
            done = False
            hidden_state = None
            
            while not done and episode_length < self.config.max_steps_per_episode:
                current_player = eval_env.current_player
                state_vector = state_encoder.encode_game_state(state, current_player)
                state_tensor = torch.FloatTensor(state_vector.to_vector()).unsqueeze(0)
                action_mask = eval_env.get_action_mask()
                mask_tensor = torch.FloatTensor(action_mask).unsqueeze(0)
                
                # 使用确定性策略
                with torch.no_grad():
                    action_probs, _, new_hidden_state = self.global_network.network(
                        state_tensor, hidden_state, mask_tensor
                    )
                    action = torch.argmax(action_probs, dim=-1).item()
                
                state, reward, done, info = eval_env.step(action)
                episode_reward += reward
                episode_length += 1
                hidden_state = new_hidden_state
            
            total_rewards.append(episode_reward)
            episode_lengths.append(episode_length)
        
        return {
            'avg_reward': np.mean(total_rewards),
            'avg_episode_length': np.mean(episode_lengths),
            'reward_std': np.std(total_rewards)
        }
    
    def _log_evaluation_metrics(self