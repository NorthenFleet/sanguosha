#!/usr/bin/env python3
"""
三国杀AI奖励系统
设计复杂的奖励函数来指导AI学习最优策略
"""

import numpy as np
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass
from enum import Enum
import math

from app.core.base.game import Game
from app.core.base.player import Player
from app.core.base.card import Card

class RewardType(Enum):
    """奖励类型枚举"""
    SURVIVAL = "survival"           # 生存奖励
    DAMAGE = "damage"              # 伤害奖励
    HEALING = "healing"            # 治疗奖励
    CARD_ADVANTAGE = "card_advantage"  # 手牌优势
    EQUIPMENT = "equipment"        # 装备奖励
    SKILL_USAGE = "skill_usage"    # 技能使用
    STRATEGIC = "strategic"        # 策略奖励
    EFFICIENCY = "efficiency"      # 效率奖励
    GAME_OUTCOME = "game_outcome"  # 游戏结果

@dataclass
class RewardConfig:
    """奖励配置参数"""
    # 基础奖励权重
    survival_weight: float = 1.0
    damage_weight: float = 0.8
    healing_weight: float = 0.6
    card_advantage_weight: float = 0.4
    equipment_weight: float = 0.3
    skill_weight: float = 0.5
    strategic_weight: float = 0.7
    efficiency_weight: float = 0.2
    
    # 游戏结果奖励
    win_reward: float = 100.0
    lose_penalty: float = -50.0
    draw_reward: float = 0.0
    
    # 动作奖励
    valid_action_reward: float = 0.1
    invalid_action_penalty: float = -5.0
    
    # 特殊情况奖励
    kill_enemy_reward: float = 30.0
    save_ally_reward: float = 15.0
    critical_hp_penalty: float = -10.0  # 血量过低惩罚
    
    # 时间相关
    turn_length_penalty: float = -0.01  # 回合过长惩罚
    game_length_bonus: float = 0.05     # 快速结束游戏奖励

class GameStateAnalyzer:
    """游戏状态分析器"""
    
    def __init__(self):
        self.previous_states = {}  # 存储之前的状态用于比较
    
    def analyze_player_advantage(self, player: Player, all_players: List[Player]) -> Dict[str, float]:
        """分析玩家优势"""
        analysis = {}
        
        # HP优势
        total_hp = sum(p.hp for p in all_players if p.hp > 0)
        if total_hp > 0:
            analysis['hp_ratio'] = player.hp / total_hp
        else:
            analysis['hp_ratio'] = 0.0
        
        # 手牌优势
        total_cards = sum(len(p.hand_cards) for p in all_players)
        if total_cards > 0:
            analysis['card_ratio'] = len(player.hand_cards) / total_cards
        else:
            analysis['card_ratio'] = 0.0
        
        # 装备优势
        player_equipment_count = len([e for e in [player.weapon, player.armor, player.horse_plus, player.horse_minus] if e is not None])
        total_equipment = sum(len([e for e in [p.weapon, p.armor, p.horse_plus, p.horse_minus] if e is not None]) for p in all_players)
        if total_equipment > 0:
            analysis['equipment_ratio'] = player_equipment_count / total_equipment
        else:
            analysis['equipment_ratio'] = 0.0
        
        # 生存状态
        analysis['is_alive'] = 1.0 if player.hp > 0 else 0.0
        analysis['hp_percentage'] = player.hp / player.character.max_hp if player.character else 0.0
        
        # 威胁评估
        enemies = [p for p in all_players if p != player and p.hp > 0]
        analysis['enemy_count'] = len(enemies)
        analysis['threat_level'] = self._calculate_threat_level(player, enemies)
        
        return analysis
    
    def _calculate_threat_level(self, player: Player, enemies: List[Player]) -> float:
        """计算威胁等级"""
        if not enemies:
            return 0.0
        
        threat = 0.0
        for enemy in enemies:
            # 基于敌人的攻击力和血量计算威胁
            enemy_attack = enemy.get_attack_range() if hasattr(enemy, 'get_attack_range') else 1
            enemy_hp = enemy.hp
            distance_factor = 1.0  # 简化：假设距离为1
            
            enemy_threat = (enemy_attack * enemy_hp) / distance_factor
            threat += enemy_threat
        
        return threat / len(enemies)
    
    def analyze_card_value(self, cards: List[Card]) -> Dict[str, float]:
        """分析手牌价值"""
        if not cards:
            return {'total_value': 0.0, 'offensive_value': 0.0, 'defensive_value': 0.0, 'utility_value': 0.0}
        
        offensive_cards = ['杀', '决斗', '万箭齐发', '南蛮入侵']
        defensive_cards = ['闪', '桃', '酒']
        utility_cards = ['无懈可击', '顺手牵羊', '过河拆桥', '借刀杀人']
        
        offensive_value = sum(1.0 for card in cards if card.name in offensive_cards)
        defensive_value = sum(1.0 for card in cards if card.name in defensive_cards)
        utility_value = sum(1.0 for card in cards if card.name in utility_cards)
        
        total_value = offensive_value + defensive_value + utility_value
        
        return {
            'total_value': total_value,
            'offensive_value': offensive_value,
            'defensive_value': defensive_value,
            'utility_value': utility_value,
            'balance_score': min(offensive_value, defensive_value, utility_value) / max(total_value, 1.0)
        }

class RewardCalculator:
    """奖励计算器"""
    
    def __init__(self, config: RewardConfig):
        self.config = config
        self.analyzer = GameStateAnalyzer()
        self.episode_history = []  # 存储整局游戏的历史
    
    def calculate_step_reward(self, 
                            game: Game, 
                            player: Player, 
                            action: int, 
                            action_valid: bool,
                            previous_state: Optional[Dict] = None) -> Tuple[float, Dict[str, float]]:
        """
        计算单步奖励
        Args:
            game: 游戏状态
            player: 当前玩家
            action: 执行的动作
            action_valid: 动作是否有效
            previous_state: 之前的状态（用于计算变化）
        Returns:
            total_reward: 总奖励
            reward_breakdown: 奖励分解
        """
        rewards = {}
        
        # 1. 动作有效性奖励
        if action_valid:
            rewards['action_validity'] = self.config.valid_action_reward
        else:
            rewards['action_validity'] = self.config.invalid_action_penalty
        
        # 2. 生存奖励
        rewards['survival'] = self._calculate_survival_reward(player)
        
        # 3. 血量变化奖励
        if previous_state:
            hp_change = player.hp - previous_state.get('hp', player.hp)
            if hp_change > 0:
                rewards['healing'] = hp_change * self.config.healing_weight
            elif hp_change < 0:
                rewards['damage_taken'] = hp_change * self.config.damage_weight
        
        # 4. 手牌优势奖励
        rewards['card_advantage'] = self._calculate_card_advantage_reward(player, game.players)
        
        # 5. 装备奖励
        rewards['equipment'] = self._calculate_equipment_reward(player)
        
        # 6. 策略奖励
        rewards['strategic'] = self._calculate_strategic_reward(player, game, action)
        
        # 7. 效率奖励
        rewards['efficiency'] = self._calculate_efficiency_reward(game)
        
        # 8. 特殊情况奖励
        rewards.update(self._calculate_special_rewards(player, game, previous_state))
        
        # 应用权重并计算总奖励
        weighted_rewards = {}
        for reward_type, value in rewards.items():
            if reward_type in ['survival']:
                weighted_rewards[reward_type] = value * self.config.survival_weight
            elif reward_type in ['healing', 'damage_taken']:
                weighted_rewards[reward_type] = value * self.config.damage_weight
            elif reward_type in ['card_advantage']:
                weighted_rewards[reward_type] = value * self.config.card_advantage_weight
            elif reward_type in ['equipment']:
                weighted_rewards[reward_type] = value * self.config.equipment_weight
            elif reward_type in ['strategic']:
                weighted_rewards[reward_type] = value * self.config.strategic_weight
            elif reward_type in ['efficiency']:
                weighted_rewards[reward_type] = value * self.config.efficiency_weight
            else:
                weighted_rewards[reward_type] = value
        
        total_reward = sum(weighted_rewards.values())
        
        return total_reward, weighted_rewards
    
    def calculate_episode_reward(self, 
                               game: Game, 
                               player: Player, 
                               game_result: str,
                               episode_length: int) -> Tuple[float, Dict[str, float]]:
        """
        计算整局游戏奖励
        Args:
            game: 最终游戏状态
            player: 玩家
            game_result: 游戏结果 ('win', 'lose', 'draw')
            episode_length: 游戏长度
        Returns:
            total_reward: 总奖励
            reward_breakdown: 奖励分解
        """
        rewards = {}
        
        # 1. 游戏结果奖励
        if game_result == 'win':
            rewards['game_outcome'] = self.config.win_reward
        elif game_result == 'lose':
            rewards['game_outcome'] = self.config.lose_penalty
        else:
            rewards['game_outcome'] = self.config.draw_reward
        
        # 2. 游戏长度奖励（鼓励高效游戏）
        if game_result == 'win':
            # 获胜时，游戏越短奖励越高
            length_bonus = max(0, (500 - episode_length) * self.config.game_length_bonus)
            rewards['game_length'] = length_bonus
        else:
            # 失败时，游戏过长有惩罚
            length_penalty = min(0, (episode_length - 300) * self.config.turn_length_penalty)
            rewards['game_length'] = length_penalty
        
        # 3. 最终状态奖励
        final_analysis = self.analyzer.analyze_player_advantage(player, game.players)
        rewards['final_hp_ratio'] = final_analysis['hp_ratio'] * 10.0
        rewards['final_card_ratio'] = final_analysis['card_ratio'] * 5.0
        
        # 4. 整局表现奖励
        rewards['consistency'] = self._calculate_consistency_reward()
        
        total_reward = sum(rewards.values())
        return total_reward, rewards
    
    def _calculate_survival_reward(self, player: Player) -> float:
        """计算生存奖励"""
        if player.hp <= 0:
            return -20.0  # 死亡重惩罚
        
        # 基于血量百分比的生存奖励
        hp_ratio = player.hp / player.character.max_hp if player.character else 0.0
        
        if hp_ratio >= 0.8:
            return 2.0  # 血量充足
        elif hp_ratio >= 0.5:
            return 1.0  # 血量一般
        elif hp_ratio >= 0.3:
            return 0.0  # 血量偏低
        else:
            return self.config.critical_hp_penalty  # 血量危险
    
    def _calculate_card_advantage_reward(self, player: Player, all_players: List[Player]) -> float:
        """计算手牌优势奖励"""
        card_analysis = self.analyzer.analyze_card_value(player.hand_cards)
        
        # 基础手牌价值奖励
        base_reward = card_analysis['total_value'] * 0.5
        
        # 手牌平衡奖励
        balance_reward = card_analysis['balance_score'] * 2.0
        
        # 手牌数量奖励（适中最好）
        hand_size = len(player.hand_cards)
        if 3 <= hand_size <= 5:
            size_reward = 1.0
        elif 2 <= hand_size <= 6:
            size_reward = 0.5
        else:
            size_reward = -0.5  # 手牌过多或过少都不好
        
        return base_reward + balance_reward + size_reward
    
    def _calculate_equipment_reward(self, player: Player) -> float:
        """计算装备奖励"""
        equipment_count = 0
        equipment_value = 0.0
        
        if player.weapon:
            equipment_count += 1
            equipment_value += 2.0  # 武器价值较高
        
        if player.armor:
            equipment_count += 1
            equipment_value += 1.5  # 防具价值中等
        
        if player.horse_plus:
            equipment_count += 1
            equipment_value += 1.0  # +1马价值一般
        
        if player.horse_minus:
            equipment_count += 1
            equipment_value += 1.0  # -1马价值一般
        
        # 装备齐全奖励
        if equipment_count >= 3:
            equipment_value += 2.0
        
        return equipment_value
    
    def _calculate_strategic_reward(self, player: Player, game: Game, action: int) -> float:
        """计算策略奖励"""
        strategic_reward = 0.0
        
        # 根据游戏阶段调整策略
        alive_players = [p for p in game.players if p.hp > 0]
        game_stage = len(alive_players) / len(game.players)
        
        if game_stage > 0.7:  # 游戏早期
            # 鼓励发育和积累资源
            if len(player.hand_cards) > 3:
                strategic_reward += 1.0
        elif game_stage > 0.4:  # 游戏中期
            # 鼓励主动出击
            strategic_reward += 0.5
        else:  # 游戏后期
            # 鼓励保守策略
            if player.hp > 1:
                strategic_reward += 1.0
        
        # 目标选择奖励
        if hasattr(player, 'last_target'):
            # 优先攻击血量低的敌人
            target = player.last_target
            if target and target.hp <= 2:
                strategic_reward += 2.0
        
        return strategic_reward
    
    def _calculate_efficiency_reward(self, game: Game) -> float:
        """计算效率奖励"""
        # 基于回合数的效率评估
        turn_efficiency = max(0, (50 - game.turn_number) * 0.1)
        
        # 基于游戏进度的效率评估
        alive_players = len([p for p in game.players if p.hp > 0])
        total_players = len(game.players)
        progress_efficiency = (total_players - alive_players) / total_players * 2.0
        
        return turn_efficiency + progress_efficiency
    
    def _calculate_special_rewards(self, player: Player, game: Game, previous_state: Optional[Dict]) -> Dict[str, float]:
        """计算特殊情况奖励"""
        special_rewards = {}
        
        if previous_state:
            # 击杀敌人奖励
            prev_alive_enemies = previous_state.get('alive_enemies', 0)
            current_alive_enemies = len([p for p in game.players if p != player and p.hp > 0])
            if current_alive_enemies < prev_alive_enemies:
                special_rewards['kill_enemy'] = self.config.kill_enemy_reward
            
            # 救援队友奖励（如果有队友系统）
            # 这里简化处理，实际需要根据游戏模式调整
            
        # 连击奖励
        if hasattr(player, 'consecutive_actions') and player.consecutive_actions > 2:
            special_rewards['combo'] = player.consecutive_actions * 0.5
        
        return special_rewards
    
    def _calculate_consistency_reward(self) -> float:
        """计算整局一致性奖励"""
        # 基于整局表现的一致性评估
        # 这里可以分析玩家的决策模式，奖励稳定的策略
        return 0.0  # 简化实现
    
    def reset_episode(self):
        """重置局游戏统计"""
        self.episode_history = []
    
    def add_step_to_history(self, step_info: Dict):
        """添加步骤信息到历史"""
        self.episode_history.append(step_info)

class AdaptiveRewardSystem:
    """自适应奖励系统"""
    
    def __init__(self, base_config: RewardConfig):
        self.base_config = base_config
        self.performance_history = []
        self.adaptation_rate = 0.01
    
    def adapt_rewards(self, recent_performance: Dict[str, float]) -> RewardConfig:
        """根据最近表现调整奖励参数"""
        adapted_config = RewardConfig()
        
        # 复制基础配置
        for attr in dir(self.base_config):
            if not attr.startswith('_'):
                setattr(adapted_config, attr, getattr(self.base_config, attr))
        
        # 根据表现调整权重
        win_rate = recent_performance.get('win_rate', 0.5)
        avg_game_length = recent_performance.get('avg_game_length', 300)
        
        # 如果胜率过低，增加生存奖励权重
        if win_rate < 0.3:
            adapted_config.survival_weight *= (1 + self.adaptation_rate)
            adapted_config.damage_weight *= (1 - self.adaptation_rate)
        
        # 如果游戏过长，增加效率奖励权重
        if avg_game_length > 400:
            adapted_config.efficiency_weight *= (1 + self.adaptation_rate)
        
        return adapted_config
    
    def update_performance_history(self, performance: Dict[str, float]):
        """更新表现历史"""
        self.performance_history.append(performance)
        
        # 只保留最近100局的记录
        if len(self.performance_history) > 100:
            self.performance_history = self.performance_history[-100:]

if __name__ == "__main__":
    # 测试奖励系统
    config = RewardConfig()
    calculator = RewardCalculator(config)
    
    print("奖励系统初始化完成")
    print(f"基础配置: 生存权重={config.survival_weight}, 伤害权重={config.damage_weight}")
    
    # 创建自适应系统
    adaptive_system = AdaptiveRewardSystem(config)
    
    # 模拟性能数据
    performance = {'win_rate': 0.25, 'avg_game_length': 450}
    adapted_config = adaptive_system.adapt_rewards(performance)
    
    print(f"自适应后配置: 生存权重={adapted_config.survival_weight:.3f}, 效率权重={adapted_config.efficiency_weight:.3f}")