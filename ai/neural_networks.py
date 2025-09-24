#!/usr/bin/env python3
"""
三国杀AI神经网络架构
包括策略网络、价值网络和注意力机制
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
import numpy as np
from typing import Tuple, Dict, List

class AttentionLayer(nn.Module):
    """注意力机制层，用于关注重要的游戏状态特征"""
    
    def __init__(self, input_dim: int, attention_dim: int = 64):
        super(AttentionLayer, self).__init__()
        self.attention_dim = attention_dim
        
        self.query = nn.Linear(input_dim, attention_dim)
        self.key = nn.Linear(input_dim, attention_dim)
        self.value = nn.Linear(input_dim, attention_dim)
        self.output = nn.Linear(attention_dim, input_dim)
        
    def forward(self, x):
        # x shape: (batch_size, seq_len, input_dim)
        Q = self.query(x)
        K = self.key(x)
        V = self.value(x)
        
        # 计算注意力权重
        attention_weights = F.softmax(torch.matmul(Q, K.transpose(-2, -1)) / np.sqrt(self.attention_dim), dim=-1)
        
        # 应用注意力
        attended = torch.matmul(attention_weights, V)
        output = self.output(attended)
        
        return output + x  # 残差连接

class StateEncoder(nn.Module):
    """状态编码器，将游戏状态编码为特征向量"""
    
    def __init__(self, state_dim: int, hidden_dim: int = 512):
        super(StateEncoder, self).__init__()
        
        # 玩家特征编码器
        self.player_encoder = nn.Sequential(
            nn.Linear(20, 64),  # 玩家+对手特征
            nn.ReLU(),
            nn.Linear(64, 128),
            nn.ReLU()
        )
        
        # 手牌编码器
        self.hand_encoder = nn.Sequential(
            nn.Linear(320, 128),  # 手牌特征
            nn.ReLU(),
            nn.Linear(128, 64),
            nn.ReLU()
        )
        
        # 装备编码器
        self.equipment_encoder = nn.Sequential(
            nn.Linear(12, 32),
            nn.ReLU(),
            nn.Linear(32, 64),
            nn.ReLU()
        )
        
        # 游戏状态编码器
        self.game_state_encoder = nn.Sequential(
            nn.Linear(14, 32),  # 阶段+棋盘状态
            nn.ReLU(),
            nn.Linear(32, 64),
            nn.ReLU()
        )
        
        # 特征融合层
        total_feature_dim = 128 + 64 + 64 + 64  # 320
        self.feature_fusion = nn.Sequential(
            nn.Linear(total_feature_dim, hidden_dim),
            nn.ReLU(),
            nn.Dropout(0.2),
            nn.Linear(hidden_dim, hidden_dim),
            nn.ReLU()
        )
        
        # 注意力层
        self.attention = AttentionLayer(hidden_dim)
        
    def forward(self, state_vector):
        """
        编码游戏状态
        Args:
            state_vector: 游戏状态向量
        Returns:
            encoded_state: 编码后的状态特征
        """
        # 分解状态向量
        player_features = state_vector[:, :20]
        hand_features = state_vector[:, 20:340]
        equipment_features = state_vector[:, 340:352]
        game_features = state_vector[:, 352:366]
        
        # 分别编码各部分特征
        player_encoded = self.player_encoder(player_features)
        hand_encoded = self.hand_encoder(hand_features)
        equipment_encoded = self.equipment_encoder(equipment_features)
        game_encoded = self.game_state_encoder(game_features)
        
        # 特征融合
        combined_features = torch.cat([
            player_encoded, hand_encoded, 
            equipment_encoded, game_encoded
        ], dim=-1)
        
        fused_features = self.feature_fusion(combined_features)
        
        # 应用注意力机制
        attended_features = self.attention(fused_features.unsqueeze(1)).squeeze(1)
        
        return attended_features

class PolicyNetwork(nn.Module):
    """策略网络，输出动作概率分布"""
    
    def __init__(self, state_dim: int, action_dim: int, hidden_dim: int = 512):
        super(PolicyNetwork, self).__init__()
        
        self.state_encoder = StateEncoder(state_dim, hidden_dim)
        
        # 策略头
        self.policy_head = nn.Sequential(
            nn.Linear(hidden_dim, hidden_dim // 2),
            nn.ReLU(),
            nn.Dropout(0.1),
            nn.Linear(hidden_dim // 2, hidden_dim // 4),
            nn.ReLU(),
            nn.Linear(hidden_dim // 4, action_dim)
        )
        
    def forward(self, state, action_mask=None):
        """
        前向传播
        Args:
            state: 游戏状态
            action_mask: 动作掩码，标识合法动作
        Returns:
            action_probs: 动作概率分布
        """
        encoded_state = self.state_encoder(state)
        logits = self.policy_head(encoded_state)
        
        # 应用动作掩码
        if action_mask is not None:
            logits = logits + (action_mask - 1) * 1e9  # 将非法动作的logit设为很小的值
        
        action_probs = F.softmax(logits, dim=-1)
        return action_probs
    
    def get_action_and_log_prob(self, state, action_mask=None):
        """获取动作和对数概率"""
        action_probs = self.forward(state, action_mask)
        dist = torch.distributions.Categorical(action_probs)
        action = dist.sample()
        log_prob = dist.log_prob(action)
        return action, log_prob, action_probs

class ValueNetwork(nn.Module):
    """价值网络，估计状态价值"""
    
    def __init__(self, state_dim: int, hidden_dim: int = 512):
        super(ValueNetwork, self).__init__()
        
        self.state_encoder = StateEncoder(state_dim, hidden_dim)
        
        # 价值头
        self.value_head = nn.Sequential(
            nn.Linear(hidden_dim, hidden_dim // 2),
            nn.ReLU(),
            nn.Dropout(0.1),
            nn.Linear(hidden_dim // 2, hidden_dim // 4),
            nn.ReLU(),
            nn.Linear(hidden_dim // 4, 1)
        )
        
    def forward(self, state):
        """
        前向传播
        Args:
            state: 游戏状态
        Returns:
            value: 状态价值估计
        """
        encoded_state = self.state_encoder(state)
        value = self.value_head(encoded_state)
        return value.squeeze(-1)

class ActorCriticNetwork(nn.Module):
    """Actor-Critic网络，结合策略和价值网络"""
    
    def __init__(self, state_dim: int, action_dim: int, hidden_dim: int = 512):
        super(ActorCriticNetwork, self).__init__()
        
        # 共享的状态编码器
        self.shared_encoder = StateEncoder(state_dim, hidden_dim)
        
        # Actor头（策略网络）
        self.actor_head = nn.Sequential(
            nn.Linear(hidden_dim, hidden_dim // 2),
            nn.ReLU(),
            nn.Dropout(0.1),
            nn.Linear(hidden_dim // 2, action_dim)
        )
        
        # Critic头（价值网络）
        self.critic_head = nn.Sequential(
            nn.Linear(hidden_dim, hidden_dim // 2),
            nn.ReLU(),
            nn.Dropout(0.1),
            nn.Linear(hidden_dim // 2, 1)
        )
        
    def forward(self, state, action_mask=None):
        """
        前向传播
        Args:
            state: 游戏状态
            action_mask: 动作掩码
        Returns:
            action_probs: 动作概率分布
            value: 状态价值估计
        """
        encoded_state = self.shared_encoder(state)
        
        # 计算动作概率
        logits = self.actor_head(encoded_state)
        if action_mask is not None:
            logits = logits + (action_mask - 1) * 1e9
        action_probs = F.softmax(logits, dim=-1)
        
        # 计算状态价值
        value = self.critic_head(encoded_state).squeeze(-1)
        
        return action_probs, value
    
    def get_action_and_value(self, state, action_mask=None):
        """获取动作、对数概率和价值"""
        action_probs, value = self.forward(state, action_mask)
        dist = torch.distributions.Categorical(action_probs)
        action = dist.sample()
        log_prob = dist.log_prob(action)
        entropy = dist.entropy()
        
        return action, log_prob, value, entropy

class DuelingNetwork(nn.Module):
    """Dueling网络架构，分离状态价值和动作优势"""
    
    def __init__(self, state_dim: int, action_dim: int, hidden_dim: int = 512):
        super(DuelingNetwork, self).__init__()
        
        self.state_encoder = StateEncoder(state_dim, hidden_dim)
        
        # 状态价值流
        self.value_stream = nn.Sequential(
            nn.Linear(hidden_dim, hidden_dim // 2),
            nn.ReLU(),
            nn.Linear(hidden_dim // 2, 1)
        )
        
        # 动作优势流
        self.advantage_stream = nn.Sequential(
            nn.Linear(hidden_dim, hidden_dim // 2),
            nn.ReLU(),
            nn.Linear(hidden_dim // 2, action_dim)
        )
        
    def forward(self, state, action_mask=None):
        """
        前向传播
        Args:
            state: 游戏状态
            action_mask: 动作掩码
        Returns:
            q_values: Q值
        """
        encoded_state = self.state_encoder(state)
        
        # 计算状态价值和动作优势
        value = self.value_stream(encoded_state)
        advantage = self.advantage_stream(encoded_state)
        
        # Dueling架构：Q(s,a) = V(s) + A(s,a) - mean(A(s,a))
        q_values = value + advantage - advantage.mean(dim=-1, keepdim=True)
        
        # 应用动作掩码
        if action_mask is not None:
            q_values = q_values + (action_mask - 1) * 1e9
        
        return q_values

def create_networks(state_dim: int, action_dim: int, network_type: str = "actor_critic"):
    """
    创建神经网络
    Args:
        state_dim: 状态维度
        action_dim: 动作维度
        network_type: 网络类型 ("actor_critic", "separate", "dueling")
    Returns:
        networks: 神经网络字典
    """
    if network_type == "actor_critic":
        return {
            "actor_critic": ActorCriticNetwork(state_dim, action_dim)
        }
    elif network_type == "separate":
        return {
            "policy": PolicyNetwork(state_dim, action_dim),
            "value": ValueNetwork(state_dim)
        }
    elif network_type == "dueling":
        return {
            "dueling": DuelingNetwork(state_dim, action_dim)
        }
    else:
        raise ValueError(f"Unknown network type: {network_type}")

if __name__ == "__main__":
    # 测试网络架构
    state_dim = 366  # 根据状态编码器的输出维度
    action_dim = 50   # 假设的动作空间大小
    batch_size = 32
    
    # 创建测试数据
    test_state = torch.randn(batch_size, state_dim)
    test_action_mask = torch.ones(batch_size, action_dim)
    
    # 测试Actor-Critic网络
    ac_network = ActorCriticNetwork(state_dim, action_dim)
    action_probs, values = ac_network(test_state, test_action_mask)
    print(f"Actor-Critic输出 - 动作概率形状: {action_probs.shape}, 价值形状: {values.shape}")
    
    # 测试Dueling网络
    dueling_network = DuelingNetwork(state_dim, action_dim)
    q_values = dueling_network(test_state, test_action_mask)
    print(f"Dueling网络输出 - Q值形状: {q_values.shape}")
    
    print("神经网络架构测试完成！")