#!/usr/bin/env python3
"""
三国杀游戏状态编码器
将复杂的游戏状态转换为神经网络可处理的向量表示
"""

import numpy as np
from typing import Dict, List, Tuple, Any
from dataclasses import dataclass
from enum import Enum

class StateFeatureType(Enum):
    """状态特征类型"""
    PLAYER_INFO = "player_info"
    HAND_CARDS = "hand_cards"
    EQUIPMENT = "equipment"
    GAME_PHASE = "game_phase"
    BOARD_STATE = "board_state"

@dataclass
class GameStateVector:
    """游戏状态向量"""
    player_features: np.ndarray      # 玩家特征 [hp, max_hp, hand_count, ...]
    opponent_features: np.ndarray    # 对手特征 [hp, max_hp, visible_info, ...]
    hand_cards: np.ndarray          # 手牌编码 [card_type_one_hot, ...]
    equipment: np.ndarray           # 装备编码 [weapon, armor, horses, ...]
    game_phase: np.ndarray          # 游戏阶段编码 [phase_one_hot]
    board_state: np.ndarray         # 棋盘状态 [deck_count, discard_count, ...]
    
    def to_vector(self) -> np.ndarray:
        """转换为单一向量"""
        return np.concatenate([
            self.player_features,
            self.opponent_features,
            self.hand_cards,
            self.equipment,
            self.game_phase,
            self.board_state
        ])

class GameStateEncoder:
    """游戏状态编码器"""
    
    def __init__(self):
        # 卡牌类型映射
        self.card_types = {
            "杀": 0, "闪": 1, "桃": 2, "酒": 3,
            "无懈可击": 4, "决斗": 5, "南蛮入侵": 6, "万箭齐发": 7,
            "桃园结义": 8, "五谷丰登": 9, "借刀杀人": 10, "顺手牵羊": 11,
            "过河拆桥": 12, "铁索连环": 13, "闪电": 14, "乐不思蜀": 15
        }
        
        # 装备类型映射
        self.equipment_types = {
            "青龙偃月刀": 0, "丈八蛇矛": 1, "方天画戟": 2, "麒麟弓": 3,
            "八卦阵": 4, "仁王盾": 5, "白银狮子": 6,
            "赤兔马": 7, "的卢": 8, "绝影": 9, "爪黄飞电": 10
        }
        
        # 武将技能映射
        self.character_skills = {
            "奸雄": 0, "护驾": 1, "仁德": 2, "激将": 3,
            "咆哮": 4, "克己": 5, "英姿": 6, "反间": 7
        }
        
        # 游戏阶段映射
        self.game_phases = {
            "准备阶段": 0, "判定阶段": 1, "摸牌阶段": 2,
            "出牌阶段": 3, "弃牌阶段": 4, "结束阶段": 5
        }
        
        # 特征维度定义
        self.PLAYER_FEATURE_DIM = 10      # 玩家基础特征
        self.HAND_CARD_DIM = 20           # 手牌特征（最多20张）
        self.EQUIPMENT_DIM = 12           # 装备特征
        self.PHASE_DIM = 6                # 阶段特征
        self.BOARD_STATE_DIM = 8          # 棋盘状态特征
        
        self.TOTAL_DIM = (
            self.PLAYER_FEATURE_DIM * 2 +  # 自己和对手
            self.HAND_CARD_DIM * len(self.card_types) +
            self.EQUIPMENT_DIM +
            self.PHASE_DIM +
            self.BOARD_STATE_DIM
        )
    
    def encode_game_state(self, game, current_player) -> GameStateVector:
        """编码完整游戏状态"""
        opponent = game.get_opponent(current_player)
        
        # 编码玩家特征
        player_features = self._encode_player_features(current_player, is_self=True)
        opponent_features = self._encode_player_features(opponent, is_self=False)
        
        # 编码手牌
        hand_cards = self._encode_hand_cards(current_player.hand_cards)
        
        # 编码装备
        equipment = self._encode_equipment(current_player)
        
        # 编码游戏阶段
        game_phase = self._encode_game_phase(game.current_phase)
        
        # 编码棋盘状态
        board_state = self._encode_board_state(game)
        
        return GameStateVector(
            player_features=player_features,
            opponent_features=opponent_features,
            hand_cards=hand_cards,
            equipment=equipment,
            game_phase=game_phase,
            board_state=board_state
        )
    
    def _encode_player_features(self, player, is_self=True) -> np.ndarray:
        """编码玩家特征"""
        features = np.zeros(self.PLAYER_FEATURE_DIM)
        
        # 基础属性
        features[0] = player.hp / 4.0                    # 当前体力（归一化）
        features[1] = player.character.hp / 4.0          # 最大体力（归一化）
        features[2] = len(player.hand_cards) / 20.0      # 手牌数量（归一化）
        
        # 装备状态
        features[3] = 1.0 if player.weapon else 0.0
        features[4] = 1.0 if player.defense else 0.0
        features[5] = 1.0 if player.attack_horse else 0.0
        features[6] = 1.0 if player.defense_horse else 0.0
        
        # 状态效果
        features[7] = 1.0 if player.chained else 0.0
        features[8] = 1.0 if hasattr(player, 'has_used_sha') and player.has_used_sha else 0.0
        
        # 武将技能编码（简化为是否拥有某些关键技能）
        if hasattr(player.character, 'skills'):
            for skill in player.character.skills:
                if skill in self.character_skills:
                    skill_idx = self.character_skills[skill]
                    if skill_idx < 2:  # 只编码前2个技能位
                        features[9] = skill_idx / len(self.character_skills)
        
        return features
    
    def _encode_hand_cards(self, hand_cards) -> np.ndarray:
        """编码手牌信息"""
        # 创建卡牌类型计数向量
        card_counts = np.zeros(len(self.card_types))
        
        for card in hand_cards:
            if hasattr(card, 'name') and card.name in self.card_types:
                card_idx = self.card_types[card.name]
                card_counts[card_idx] += 1
        
        # 归一化（假设最多每种牌10张）
        card_counts = np.clip(card_counts / 10.0, 0, 1)
        
        # 扩展到固定维度
        hand_features = np.zeros(self.HAND_CARD_DIM * len(self.card_types))
        hand_features[:len(card_counts)] = card_counts
        
        return hand_features
    
    def _encode_equipment(self, player) -> np.ndarray:
        """编码装备信息"""
        equipment_features = np.zeros(self.EQUIPMENT_DIM)
        
        # 武器编码
        if player.weapon and hasattr(player.weapon, 'name'):
            if player.weapon.name in self.equipment_types:
                weapon_idx = self.equipment_types[player.weapon.name]
                equipment_features[0] = weapon_idx / len(self.equipment_types)
        
        # 防具编码
        if player.defense and hasattr(player.defense, 'name'):
            if player.defense.name in self.equipment_types:
                armor_idx = self.equipment_types[player.defense.name]
                equipment_features[1] = armor_idx / len(self.equipment_types)
        
        # 马匹编码
        if player.attack_horse and hasattr(player.attack_horse, 'name'):
            if player.attack_horse.name in self.equipment_types:
                horse_idx = self.equipment_types[player.attack_horse.name]
                equipment_features[2] = horse_idx / len(self.equipment_types)
                
        if player.defense_horse and hasattr(player.defense_horse, 'name'):
            if player.defense_horse.name in self.equipment_types:
                horse_idx = self.equipment_types[player.defense_horse.name]
                equipment_features[3] = horse_idx / len(self.equipment_types)
        
        return equipment_features
    
    def _encode_game_phase(self, current_phase) -> np.ndarray:
        """编码游戏阶段"""
        phase_features = np.zeros(self.PHASE_DIM)
        
        if current_phase in self.game_phases:
            phase_idx = self.game_phases[current_phase]
            phase_features[phase_idx] = 1.0
        
        return phase_features
    
    def _encode_board_state(self, game) -> np.ndarray:
        """编码棋盘状态"""
        board_features = np.zeros(self.BOARD_STATE_DIM)
        
        # 牌堆信息
        if hasattr(game, 'deck') and hasattr(game.deck, 'cards'):
            board_features[0] = len(game.deck.cards) / 108.0  # 牌堆剩余（归一化）
        
        # 弃牌堆信息
        if hasattr(game, 'discard_pile'):
            board_features[1] = len(game.discard_pile) / 108.0  # 弃牌堆大小
        
        # 回合信息
        if hasattr(game, 'current_player_index'):
            board_features[2] = game.current_player_index  # 当前玩家索引
        
        # 游戏进度（可以根据回合数或其他指标计算）
        board_features[3] = 0.5  # 占位符，可以根据实际需求调整
        
        return board_features
    
    def get_state_dimension(self) -> int:
        """获取状态向量维度"""
        return self.TOTAL_DIM
    
    def decode_action_mask(self, game, current_player) -> np.ndarray:
        """生成动作掩码，标识哪些动作是合法的"""
        # 这里需要根据游戏规则生成动作掩码
        # 暂时返回全1向量，表示所有动作都可用
        action_space_size = self._get_action_space_size()
        return np.ones(action_space_size)
    
    def _get_action_space_size(self) -> int:
        """获取动作空间大小"""
        # 动作空间包括：
        # 1. 出牌动作（每种卡牌类型）
        # 2. 使用技能
        # 3. 结束出牌阶段
        # 4. 响应动作（闪、无懈等）
        return len(self.card_types) + len(self.character_skills) + 10  # 预留其他动作

if __name__ == "__main__":
    # 测试编码器
    encoder = GameStateEncoder()
    print(f"状态向量维度: {encoder.get_state_dimension()}")
    print(f"动作空间大小: {encoder._get_action_space_size()}")