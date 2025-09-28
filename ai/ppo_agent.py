#!/usr/bin/env python3
"""
PPO (Proximal Policy Optimization) 智能体实现
用于训练三国杀决策AI
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
import torch.optim as optim
import numpy as np
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from collections import deque
import random

from .neural_networks import ActorCriticNetwork, create_networks
from .game_state_encoder import GameStateEncoder

@dataclass
class PPOConfig:
    """PPO配置参数"""
    # 网络参数
    state_dim: int = 366
    action_dim: int = 50
    hidden_dim: int = 512
    
    # PPO超参数
    learning_rate: float = 3e-4
    gamma: float = 0.99              # 折扣因子
    gae_lambda: float = 0.95         # GAE参数
    clip_epsilon: float = 0.2        # PPO裁剪参数
    entropy_coef: float = 0.01       # 熵正则化系数
    value_coef: float = 0.5          # 价值损失系数
    max_grad_norm: float = 0.5       # 梯度裁剪
    
    # 训练参数
    batch_size: int = 64
    mini_batch_size: int = 16
    ppo_epochs: int = 4              # PPO更新轮数
    buffer_size: int = 2048          # 经验缓冲区大小
    
    # 探索参数
    exploration_noise: float = 0.1
    temperature: float = 1.0         # 动作选择温度

@dataclass
class Experience:
    """经验数据结构"""
    state: np.ndarray
    action: int
    reward: float
    next_state: np.ndarray
    done: bool
    log_prob: float
    value: float
    action_mask: Optional[np.ndarray] = None

class PPOBuffer:
    """PPO经验缓冲区"""
    
    def __init__(self, capacity: int, state_dim: int):
        self.capacity = capacity
        self.state_dim = state_dim
        self.clear()
    
    def clear(self):
        """清空缓冲区"""
        self.states = []
        self.actions = []
        self.rewards = []
        self.next_states = []
        self.dones = []
        self.log_probs = []
        self.values = []
        self.action_masks = []
        self.advantages = []
        self.returns = []
        self.size = 0
    
    def add(self, experience: Experience):
        """添加经验"""
        if self.size < self.capacity:
            self.states.append(experience.state)
            self.actions.append(experience.action)
            self.rewards.append(experience.reward)
            self.next_states.append(experience.next_state)
            self.dones.append(experience.done)
            self.log_probs.append(experience.log_prob)
            self.values.append(experience.value)
            self.action_masks.append(experience.action_mask)
            self.size += 1
        else:
            # 缓冲区满时，替换最旧的经验
            idx = self.size % self.capacity
            self.states[idx] = experience.state
            self.actions[idx] = experience.action
            self.rewards[idx] = experience.reward
            self.next_states[idx] = experience.next_state
            self.dones[idx] = experience.done
            self.log_probs[idx] = experience.log_prob
            self.values[idx] = experience.value
            self.action_masks[idx] = experience.action_mask
    
    def compute_gae(self, gamma: float, gae_lambda: float, next_value: float = 0.0):
        """计算GAE优势估计"""
        self.advantages = []
        self.returns = []
        
        gae = 0
        for i in reversed(range(self.size)):
            if i == self.size - 1:
                next_non_terminal = 1.0 - self.dones[i]
                next_value_est = next_value
            else:
                next_non_terminal = 1.0 - self.dones[i]
                next_value_est = self.values[i + 1]
            
            delta = self.rewards[i] + gamma * next_value_est * next_non_terminal - self.values[i]
            gae = delta + gamma * gae_lambda * next_non_terminal * gae
            
            self.advantages.insert(0, gae)
            self.returns.insert(0, gae + self.values[i])
        
        # 标准化优势
        advantages = np.array(self.advantages)
        self.advantages = (advantages - advantages.mean()) / (advantages.std() + 1e-8)
    
    def get_batches(self, batch_size: int):
        """获取训练批次"""
        indices = list(range(self.size))
        random.shuffle(indices)
        
        for start in range(0, self.size, batch_size):
            end = min(start + batch_size, self.size)
            batch_indices = indices[start:end]
            
            yield {
                'states': torch.FloatTensor([self.states[i] for i in batch_indices]),
                'actions': torch.LongTensor([self.actions[i] for i in batch_indices]),
                'old_log_probs': torch.FloatTensor([self.log_probs[i] for i in batch_indices]),
                'advantages': torch.FloatTensor([self.advantages[i] for i in batch_indices]),
                'returns': torch.FloatTensor([self.returns[i] for i in batch_indices]),
                'action_masks': torch.FloatTensor([self.action_masks[i] if self.action_masks[i] is not None 
                                                 else np.ones(50) for i in batch_indices])  # 默认动作掩码
            }

class PPOAgent:
    """PPO智能体"""
    
    def __init__(self, config: PPOConfig):
        self.config = config
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        
        # 初始化网络
        self.network = ActorCriticNetwork(
            config.state_dim, 
            config.action_dim, 
            config.hidden_dim
        ).to(self.device)
        
        # 优化器
        self.optimizer = optim.Adam(self.network.parameters(), lr=config.learning_rate)
        
        # 经验缓冲区
        self.buffer = PPOBuffer(config.buffer_size, config.state_dim)
        
        # 状态编码器
        self.state_encoder = GameStateEncoder()
        
        # 训练统计
        self.training_stats = {
            'policy_loss': [],
            'value_loss': [],
            'entropy_loss': [],
            'total_loss': [],
            'kl_divergence': [],
            'clip_fraction': []
        }
    
    def select_action(self, game_state, current_player, action_mask=None, training=True, deterministic=False):
        """
        选择动作
        Args:
            game_state: 游戏状态
            current_player: 当前玩家
            action_mask: 动作掩码
            training: 是否为训练模式
            deterministic: 是否使用确定性策略（评估时使用）
        Returns:
            action: 选择的动作
            log_prob: 动作的对数概率
            value: 状态价值估计
        """
        # 编码游戏状态
        state_vector = self.state_encoder.encode_game_state(game_state, current_player)
        state_tensor = torch.FloatTensor(state_vector.to_vector()).unsqueeze(0).to(self.device)
        
        # 处理动作掩码
        if action_mask is not None:
            mask_tensor = torch.FloatTensor(action_mask).unsqueeze(0).to(self.device)
        else:
            mask_tensor = torch.ones(1, self.config.action_dim).to(self.device)
        
        with torch.no_grad():
            if deterministic:
                # 确定性策略：选择概率最高的动作
                action_probs, value = self.network(state_tensor, mask_tensor)
                action = torch.argmax(action_probs, dim=-1)
                return action.item(), 0.0, value.item()
            else:
                # 随机策略：根据概率分布采样
                action, log_prob, value, entropy = self.network.get_action_and_value(state_tensor, mask_tensor)
        
        if training:
            return action.item(), log_prob.item(), value.item()
        else:
            return action.item(), 0.0, value.item()
    
    def store_experience(self, state, action, reward, next_state, done, log_prob, value, action_mask=None):
        """存储经验"""
        experience = Experience(
            state=state,
            action=action,
            reward=reward,
            next_state=next_state,
            done=done,
            log_prob=log_prob,
            value=value,
            action_mask=action_mask
        )
        self.buffer.add(experience)
    
    def update(self):
        """PPO更新"""
        if self.buffer.size < self.config.batch_size:
            return
        
        # 计算GAE
        self.buffer.compute_gae(self.config.gamma, self.config.gae_lambda)
        
        # 多轮PPO更新
        for epoch in range(self.config.ppo_epochs):
            for batch in self.buffer.get_batches(self.config.mini_batch_size):
                self._update_network(batch)
        
        # 清空缓冲区
        self.buffer.clear()
    
    def _update_network(self, batch):
        """更新网络参数"""
        states = batch['states'].to(self.device)
        actions = batch['actions'].to(self.device)
        old_log_probs = batch['old_log_probs'].to(self.device)
        advantages = batch['advantages'].to(self.device)
        returns = batch['returns'].to(self.device)
        action_masks = batch['action_masks'].to(self.device)
        
        # 前向传播
        action_probs, values = self.network(states, action_masks)
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
        value_loss = F.mse_loss(values, returns)
        
        # 熵损失
        entropy_loss = -entropy.mean()
        
        # 总损失
        total_loss = (policy_loss + 
                     self.config.value_coef * value_loss + 
                     self.config.entropy_coef * entropy_loss)
        
        # 反向传播
        self.optimizer.zero_grad()
        total_loss.backward()
        torch.nn.utils.clip_grad_norm_(self.network.parameters(), self.config.max_grad_norm)
        self.optimizer.step()
        
        # 记录统计信息
        with torch.no_grad():
            kl_div = (old_log_probs - new_log_probs).mean()
            clip_fraction = ((ratio - 1.0).abs() > self.config.clip_epsilon).float().mean()
            
            self.training_stats['policy_loss'].append(policy_loss.item())
            self.training_stats['value_loss'].append(value_loss.item())
            self.training_stats['entropy_loss'].append(entropy_loss.item())
            self.training_stats['total_loss'].append(total_loss.item())
            self.training_stats['kl_divergence'].append(kl_div.item())
            self.training_stats['clip_fraction'].append(clip_fraction.item())
    
    def save_model(self, filepath: str):
        """保存模型"""
        torch.save({
            'network_state_dict': self.network.state_dict(),
            'optimizer_state_dict': self.optimizer.state_dict(),
            'config': self.config,
            'training_stats': self.training_stats
        }, filepath)
    
    def load_model(self, filepath: str):
        """加载模型"""
        checkpoint = torch.load(filepath, map_location=self.device)
        self.network.load_state_dict(checkpoint['network_state_dict'])
        self.optimizer.load_state_dict(checkpoint['optimizer_state_dict'])
        self.training_stats = checkpoint.get('training_stats', self.training_stats)
    
    def get_training_stats(self) -> Dict:
        """获取训练统计信息"""
        if not self.training_stats['total_loss']:
            return {}
        
        return {
            'avg_policy_loss': np.mean(self.training_stats['policy_loss'][-100:]),
            'avg_value_loss': np.mean(self.training_stats['value_loss'][-100:]),
            'avg_entropy_loss': np.mean(self.training_stats['entropy_loss'][-100:]),
            'avg_total_loss': np.mean(self.training_stats['total_loss'][-100:]),
            'avg_kl_divergence': np.mean(self.training_stats['kl_divergence'][-100:]),
            'avg_clip_fraction': np.mean(self.training_stats['clip_fraction'][-100:])
        }

class MultiAgentPPO:
    """多智能体PPO，支持自对弈训练"""
    
    def __init__(self, config: PPOConfig, num_agents: int = 2):
        self.config = config
        self.num_agents = num_agents
        self.agents = [PPOAgent(config) for _ in range(num_agents)]
        
    def select_actions(self, game_states, current_players, action_masks=None, training=True):
        """为所有智能体选择动作"""
        actions = []
        log_probs = []
        values = []
        
        for i, (game_state, player) in enumerate(zip(game_states, current_players)):
            mask = action_masks[i] if action_masks else None
            action, log_prob, value = self.agents[i].select_action(
                game_state, player, mask, training
            )
            actions.append(action)
            log_probs.append(log_prob)
            values.append(value)
        
        return actions, log_probs, values
    
    def update_all(self):
        """更新所有智能体"""
        for agent in self.agents:
            agent.update()
    
    def save_all_models(self, filepath_prefix: str):
        """保存所有模型"""
        for i, agent in enumerate(self.agents):
            agent.save_model(f"{filepath_prefix}_agent_{i}.pth")
    
    def load_all_models(self, filepath_prefix: str):
        """加载所有模型"""
        for i, agent in enumerate(self.agents):
            agent.load_model(f"{filepath_prefix}_agent_{i}.pth")

if __name__ == "__main__":
    # 测试PPO智能体
    config = PPOConfig()
    agent = PPOAgent(config)
    
    print(f"PPO智能体初始化完成")
    print(f"设备: {agent.device}")
    print(f"网络参数数量: {sum(p.numel() for p in agent.network.parameters())}")
    print(f"状态维度: {config.state_dim}")
    print(f"动作维度: {config.action_dim}")