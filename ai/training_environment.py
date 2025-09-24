#!/usr/bin/env python3
"""
三国杀AI训练环境
连接游戏逻辑与PPO训练框架
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass
import random
import copy

from app.core.base.game import Game
from app.core.base.player import Player
from app.core.base.character import Character
from app.core.base.card import Card
from .game_state_encoder import GameStateEncoder, GameStateVector
from .ppo_agent import PPOAgent, PPOConfig

@dataclass
class TrainingConfig:
    """训练配置"""
    max_episodes: int = 10000
    max_steps_per_episode: int = 500
    save_interval: int = 100
    eval_interval: int = 50
    eval_episodes: int = 10
    
    # 奖励参数
    win_reward: float = 100.0
    lose_reward: float = -100.0
    damage_reward: float = 10.0
    heal_reward: float = 5.0
    card_play_reward: float = 1.0
    invalid_action_penalty: float = -10.0
    
    # 自对弈参数
    self_play_ratio: float = 0.8  # 自对弈比例
    random_opponent_ratio: float = 0.2  # 随机对手比例

class ActionSpace:
    """动作空间定义"""
    
    # 基础动作类型
    PASS = 0
    PLAY_CARD = 1
    USE_SKILL = 2
    EQUIP_WEAPON = 3
    EQUIP_ARMOR = 4
    RESPOND_CARD = 5
    
    # 卡牌动作（1-30）
    CARD_ACTIONS_START = 10
    CARD_ACTIONS_END = 40
    
    # 技能动作（31-45）
    SKILL_ACTIONS_START = 41
    SKILL_ACTIONS_END = 50
    
    @staticmethod
    def get_action_type(action: int) -> str:
        """获取动作类型"""
        if action == ActionSpace.PASS:
            return "pass"
        elif ActionSpace.CARD_ACTIONS_START <= action <= ActionSpace.CARD_ACTIONS_END:
            return "card"
        elif ActionSpace.SKILL_ACTIONS_START <= action <= ActionSpace.SKILL_ACTIONS_END:
            return "skill"
        else:
            return "unknown"
    
    @staticmethod
    def encode_card_action(card_index: int) -> int:
        """编码卡牌动作"""
        return ActionSpace.CARD_ACTIONS_START + card_index
    
    @staticmethod
    def decode_card_action(action: int) -> int:
        """解码卡牌动作"""
        return action - ActionSpace.CARD_ACTIONS_START
    
    @staticmethod
    def encode_skill_action(skill_index: int) -> int:
        """编码技能动作"""
        return ActionSpace.SKILL_ACTIONS_START + skill_index
    
    @staticmethod
    def decode_skill_action(action: int) -> int:
        """解码技能动作"""
        return action - ActionSpace.SKILL_ACTIONS_START

class SanguoshaEnvironment:
    """三国杀训练环境"""
    
    def __init__(self, config: TrainingConfig):
        self.config = config
        self.state_encoder = GameStateEncoder()
        self.action_space = ActionSpace()
        
        # 游戏实例
        self.game = None
        self.current_episode = 0
        self.current_step = 0
        
        # 奖励追踪
        self.episode_rewards = []
        self.step_rewards = []
        
        # 可用武将列表（简化版）
        self.available_characters = [
            "刘备", "关羽", "张飞", "诸葛亮", "赵云",
            "曹操", "司马懿", "许褚", "张辽", "夏侯惇",
            "孙权", "周瑜", "陆逊", "甘宁", "黄盖"
        ]
    
    def reset(self, num_players: int = 2) -> Tuple[GameStateVector, np.ndarray]:
        """
        重置环境
        Returns:
            initial_state: 初始游戏状态
            action_mask: 初始动作掩码
        """
        # 创建新游戏
        self.game = Game()
        
        # 添加玩家
        for i in range(num_players):
            character_name = random.choice(self.available_characters)
            character = Character(character_name)
            player = Player(character)
            self.game.add_player(player)
        
        # 开始游戏
        self.game.start_game()
        
        # 重置计数器
        self.current_step = 0
        self.step_rewards = []
        
        # 获取初始状态
        current_player = self.game.get_current_player()
        state_vector = self.state_encoder.encode_game_state(self.game, current_player)
        action_mask = self._get_action_mask(current_player)
        
        return state_vector, action_mask
    
    def step(self, action: int) -> Tuple[GameStateVector, float, bool, Dict]:
        """
        执行一步动作
        Args:
            action: 动作编码
        Returns:
            next_state: 下一个状态
            reward: 奖励
            done: 是否结束
            info: 额外信息
        """
        self.current_step += 1
        
        # 获取当前玩家
        current_player = self.game.get_current_player()
        prev_hp = current_player.hp
        prev_hand_size = len(current_player.hand_cards)
        
        # 执行动作
        reward, action_valid = self._execute_action(action, current_player)
        
        # 检查游戏是否结束
        done = self._is_game_over() or self.current_step >= self.config.max_steps_per_episode
        
        # 计算额外奖励
        if not done:
            # HP变化奖励
            hp_change = current_player.hp - prev_hp
            if hp_change > 0:
                reward += self.config.heal_reward * hp_change
            elif hp_change < 0:
                reward += self.config.damage_reward * hp_change  # 负奖励
            
            # 手牌变化（简单策略：保持适量手牌）
            hand_change = len(current_player.hand_cards) - prev_hand_size
            if 2 <= len(current_player.hand_cards) <= 5:
                reward += 1.0  # 手牌数量合理
        
        # 游戏结束奖励
        if done:
            if self._is_winner(current_player):
                reward += self.config.win_reward
            else:
                reward += self.config.lose_reward
        
        # 获取下一个状态
        next_player = self.game.get_current_player()
        next_state = self.state_encoder.encode_game_state(self.game, next_player)
        next_action_mask = self._get_action_mask(next_player)
        
        # 记录奖励
        self.step_rewards.append(reward)
        
        info = {
            'action_valid': action_valid,
            'current_player_id': current_player.character.name if current_player.character else "Unknown",
            'game_phase': self.game.current_phase,
            'step': self.current_step,
            'episode_reward': sum(self.step_rewards)
        }
        
        return next_state, reward, done, info
    
    def _execute_action(self, action: int, player: Player) -> Tuple[float, bool]:
        """
        执行具体动作
        Returns:
            reward: 动作奖励
            valid: 动作是否有效
        """
        try:
            action_type = self.action_space.get_action_type(action)
            
            if action == ActionSpace.PASS:
                # 跳过回合
                self.game.end_turn()
                return 0.0, True
            
            elif action_type == "card":
                # 打出卡牌
                card_index = self.action_space.decode_card_action(action)
                if 0 <= card_index < len(player.hand_cards):
                    card = player.hand_cards[card_index]
                    success = self._play_card(player, card)
                    if success:
                        return self.config.card_play_reward, True
                    else:
                        return self.config.invalid_action_penalty, False
                else:
                    return self.config.invalid_action_penalty, False
            
            elif action_type == "skill":
                # 使用技能
                skill_index = self.action_space.decode_skill_action(action)
                success = self._use_skill(player, skill_index)
                if success:
                    return self.config.card_play_reward * 2, True
                else:
                    return self.config.invalid_action_penalty, False
            
            else:
                return self.config.invalid_action_penalty, False
                
        except Exception as e:
            print(f"动作执行错误: {e}")
            return self.config.invalid_action_penalty, False
    
    def _play_card(self, player: Player, card: Card) -> bool:
        """打出卡牌"""
        try:
            # 简化的卡牌使用逻辑
            if card.name == "杀":
                # 选择目标（简化：选择第一个敌人）
                targets = [p for p in self.game.players if p != player and p.hp > 0]
                if targets:
                    target = targets[0]
                    # 执行杀的逻辑（简化）
                    player.discard_card(card)
                    return True
            
            elif card.name == "桃":
                if player.hp < player.character.max_hp:
                    player.hp = min(player.hp + 1, player.character.max_hp)
                    player.discard_card(card)
                    return True
            
            elif card.name == "闪":
                # 闪只能在响应时使用
                return False
            
            else:
                # 其他卡牌的简化处理
                player.discard_card(card)
                return True
                
        except Exception as e:
            print(f"卡牌使用错误: {e}")
            return False
        
        return False
    
    def _use_skill(self, player: Player, skill_index: int) -> bool:
        """使用技能"""
        try:
            if not player.character or not hasattr(player.character, 'skills'):
                return False
            
            # 简化的技能使用逻辑
            # 这里需要根据具体的技能系统实现
            return False
            
        except Exception as e:
            print(f"技能使用错误: {e}")
            return False
    
    def _get_action_mask(self, player: Player) -> np.ndarray:
        """获取动作掩码"""
        mask = np.zeros(50, dtype=np.float32)
        
        # 总是可以跳过
        mask[ActionSpace.PASS] = 1.0
        
        # 检查可用卡牌
        for i, card in enumerate(player.hand_cards[:30]):  # 最多30张手牌
            if self._can_play_card(player, card):
                action_idx = self.action_space.encode_card_action(i)
                if action_idx < 50:
                    mask[action_idx] = 1.0
        
        # 检查可用技能
        if player.character and hasattr(player.character, 'skills'):
            for i, skill in enumerate(player.character.skills[:10]):  # 最多10个技能
                if self._can_use_skill(player, skill):
                    action_idx = self.action_space.encode_skill_action(i)
                    if action_idx < 50:
                        mask[action_idx] = 1.0
        
        return mask
    
    def _can_play_card(self, player: Player, card: Card) -> bool:
        """检查是否可以打出卡牌"""
        if card.name == "杀":
            # 检查是否有目标
            targets = [p for p in self.game.players if p != player and p.hp > 0]
            return len(targets) > 0
        elif card.name == "桃":
            # 检查是否需要回血
            return player.hp < player.character.max_hp
        elif card.name == "闪":
            # 闪只能在响应时使用
            return False
        else:
            return True
    
    def _can_use_skill(self, player: Player, skill) -> bool:
        """检查是否可以使用技能"""
        # 简化的技能检查逻辑
        return False
    
    def _is_game_over(self) -> bool:
        """检查游戏是否结束"""
        alive_players = [p for p in self.game.players if p.hp > 0]
        return len(alive_players) <= 1
    
    def _is_winner(self, player: Player) -> bool:
        """检查玩家是否获胜"""
        if not self._is_game_over():
            return False
        
        alive_players = [p for p in self.game.players if p.hp > 0]
        return player in alive_players
    
    def get_state_action_dimensions(self) -> Tuple[int, int]:
        """获取状态和动作空间维度"""
        return self.state_encoder.get_state_dimension(), 50
    
    def render(self, mode='human'):
        """渲染环境状态"""
        if mode == 'human':
            print(f"\n=== 游戏状态 (第{self.current_step}步) ===")
            for i, player in enumerate(self.game.players):
                status = "存活" if player.hp > 0 else "死亡"
                print(f"玩家{i+1} ({player.character.name if player.character else 'Unknown'}): "
                      f"HP={player.hp}, 手牌={len(player.hand_cards)}, 状态={status}")
            print(f"当前回合: 玩家{self.game.current_player_index + 1}")
            print(f"游戏阶段: {self.game.current_phase}")

class SelfPlayTrainer:
    """自对弈训练器"""
    
    def __init__(self, config: TrainingConfig, ppo_config: PPOConfig):
        self.config = config
        self.ppo_config = ppo_config
        self.env = SanguoshaEnvironment(config)
        
        # 创建智能体
        self.agent = PPOAgent(ppo_config)
        self.opponent_agent = PPOAgent(ppo_config)  # 对手智能体
        
        # 训练统计
        self.episode_rewards = []
        self.win_rates = []
        
    def train(self):
        """开始训练"""
        print("开始自对弈训练...")
        
        for episode in range(self.config.max_episodes):
            episode_reward = self._run_episode(episode)
            self.episode_rewards.append(episode_reward)
            
            # 更新智能体
            if episode % 10 == 0:  # 每10局更新一次
                self.agent.update()
                if random.random() < 0.5:  # 50%概率更新对手
                    self.opponent_agent.update()
            
            # 评估和保存
            if episode % self.config.eval_interval == 0:
                win_rate = self._evaluate()
                self.win_rates.append(win_rate)
                print(f"Episode {episode}: Reward={episode_reward:.2f}, Win Rate={win_rate:.2f}")
            
            if episode % self.config.save_interval == 0:
                self.agent.save_model(f"models/ppo_agent_episode_{episode}.pth")
        
        print("训练完成!")
    
    def _run_episode(self, episode: int) -> float:
        """运行一局游戏"""
        state, action_mask = self.env.reset()
        total_reward = 0.0
        
        while True:
            # 当前玩家选择动作
            current_player_idx = self.env.game.current_player_index
            
            if current_player_idx == 0:  # 训练智能体
                action, log_prob, value = self.agent.select_action(
                    self.env.game, self.env.game.get_current_player(), action_mask.astype(bool)
                )
            else:  # 对手智能体
                action, log_prob, value = self.opponent_agent.select_action(
                    self.env.game, self.env.game.get_current_player(), action_mask.astype(bool)
                )
            
            # 执行动作
            next_state, reward, done, info = self.env.step(action)
            
            # 存储经验（只为训练智能体存储）
            if current_player_idx == 0:
                self.agent.store_experience(
                    state.to_vector(), action, reward, 
                    next_state.to_vector(), done, log_prob, value, action_mask
                )
                total_reward += reward
            
            if done:
                break
            
            state = next_state
            action_mask = self.env._get_action_mask(self.env.game.get_current_player())
        
        return total_reward
    
    def _evaluate(self) -> float:
        """评估智能体性能"""
        wins = 0
        
        for _ in range(self.config.eval_episodes):
            state, action_mask = self.env.reset()
            
            while True:
                current_player_idx = self.env.game.current_player_index
                
                if current_player_idx == 0:
                    action, _, _ = self.agent.select_action(
                        self.env.game, self.env.game.get_current_player(), 
                        action_mask.astype(bool), training=False
                    )
                else:
                    # 随机对手
                    valid_actions = np.where(action_mask > 0)[0]
                    action = random.choice(valid_actions) if len(valid_actions) > 0 else 0
                
                next_state, reward, done, info = self.env.step(action)
                
                if done:
                    if current_player_idx == 0 and reward > 0:
                        wins += 1
                    break
                
                state = next_state
                action_mask = self.env._get_action_mask(self.env.game.get_current_player())
        
        return wins / self.config.eval_episodes

if __name__ == "__main__":
    # 测试训练环境
    training_config = TrainingConfig()
    ppo_config = PPOConfig()
    
    trainer = SelfPlayTrainer(training_config, ppo_config)
    print("训练环境初始化完成")
    
    # 运行少量训练步骤进行测试
    training_config.max_episodes = 10
    trainer.train()