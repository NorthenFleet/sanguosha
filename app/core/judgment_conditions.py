#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
三国杀判断条件实现
包含各种卡牌使用、技能触发的判断条件
"""

from typing import Dict, List, Callable
from .interaction_model import InteractionContext, InteractionType
import logging

logger = logging.getLogger(__name__)


class JudgmentConditions:
    """判断条件集合"""
    
    # 基本卡牌使用条件
    @staticmethod
    def can_use_sha(context: InteractionContext) -> bool:
        """判断是否可以使用杀"""
        if not context.source_player or not context.target_player:
            return False
        
        # 检查是否有杀
        if not hasattr(context.source_player, 'has_card_name') or not context.source_player.has_card_name("杀"):
            logger.debug("没有杀卡牌")
            return False
        
        # 检查目标是否存活
        if not hasattr(context.target_player, 'is_alive') or not context.target_player.is_alive():
            logger.debug("目标已死亡")
            return False
        
        # 检查是否在攻击范围内
        if hasattr(context.source_player, 'get_attack_range'):
            attack_range = context.source_player.get_attack_range()
            if hasattr(context.source_player, 'get_distance_to'):
                distance = context.source_player.get_distance_to(context.target_player)
                if distance > attack_range:
                    logger.debug(f"目标超出攻击范围: {distance} > {attack_range}")
                    return False
        
        # 检查出杀次数限制
        if hasattr(context.source_player, 'sha_count_this_turn'):
            sha_count = getattr(context.source_player, 'sha_count_this_turn', 0)
            max_sha_count = getattr(context.source_player, 'max_sha_per_turn', 1)
            if sha_count >= max_sha_count:
                logger.debug(f"本回合出杀次数已达上限: {sha_count}/{max_sha_count}")
                return False
        
        return True
    
    @staticmethod
    def can_use_shan(context: InteractionContext) -> bool:
        """判断是否可以使用闪"""
        if not context.source_player:
            return False
        
        # 检查是否有闪
        if not hasattr(context.source_player, 'has_card_name') or not context.source_player.has_card_name("闪"):
            logger.debug("没有闪卡牌")
            return False
        
        # 闪通常是被动响应，这里检查是否在响应杀
        if context.interaction_type == InteractionType.CARD_PLAY:
            # 检查上下文中是否有需要响应的杀
            if 'responding_to' in context.additional_data:
                responding_card = context.additional_data['responding_to']
                if hasattr(responding_card, 'name') and responding_card.name == "杀":
                    return True
        
        return False
    
    @staticmethod
    def can_use_tao(context: InteractionContext) -> bool:
        """判断是否可以使用桃"""
        if not context.source_player:
            return False
        
        # 检查是否有桃
        if not hasattr(context.source_player, 'has_card_name') or not context.source_player.has_card_name("桃"):
            logger.debug("没有桃卡牌")
            return False
        
        # 确定目标（如果没有指定目标，默认为自己）
        target = context.target_player or context.source_player
        
        # 检查目标是否需要回复
        if hasattr(target, 'character') and hasattr(target.character, 'hp') and hasattr(target.character, 'max_hp'):
            if target.character.hp >= target.character.max_hp:
                logger.debug("目标体力已满")
                return False
        
        return True
    
    # 装备卡牌使用条件
    @staticmethod
    def can_equip_weapon(context: InteractionContext) -> bool:
        """判断是否可以装备武器"""
        if not context.source_player or not context.card:
            return False
        
        # 检查卡牌是否为武器
        if not hasattr(context.card, 'category') or context.card.category != 'equipment':
            return False
        
        if not hasattr(context.card, 'equipment_type') or context.card.equipment_type != 'weapon':
            return False
        
        return True
    
    @staticmethod
    def can_equip_armor(context: InteractionContext) -> bool:
        """判断是否可以装备防具"""
        if not context.source_player or not context.card:
            return False
        
        # 检查卡牌是否为防具
        if not hasattr(context.card, 'category') or context.card.category != 'equipment':
            return False
        
        if not hasattr(context.card, 'equipment_type') or context.card.equipment_type != 'armor':
            return False
        
        return True
    
    # 锦囊卡牌使用条件
    @staticmethod
    def can_use_wuxiekeji(context: InteractionContext) -> bool:
        """判断是否可以使用无懈可击"""
        if not context.source_player:
            return False
        
        # 检查是否有无懈可击
        if not hasattr(context.source_player, 'has_card_name') or not context.source_player.has_card_name("无懈可击"):
            logger.debug("没有无懈可击卡牌")
            return False
        
        # 检查是否有需要无懈的锦囊
        if 'responding_to' in context.additional_data:
            responding_card = context.additional_data['responding_to']
            if hasattr(responding_card, 'category') and responding_card.category == 'trick':
                return True
        
        return False
    
    @staticmethod
    def can_use_guohechaiqiao(context: InteractionContext) -> bool:
        """判断是否可以使用过河拆桥"""
        if not context.source_player or not context.target_player:
            return False
        
        # 检查是否有过河拆桥
        if not hasattr(context.source_player, 'has_card_name') or not context.source_player.has_card_name("过河拆桥"):
            logger.debug("没有过河拆桥卡牌")
            return False
        
        # 检查目标是否有牌可以拆
        if hasattr(context.target_player, 'hand_cards') and hasattr(context.target_player, 'equipment_area'):
            total_cards = len(context.target_player.hand_cards)
            if hasattr(context.target_player.equipment_area, '__len__'):
                total_cards += len([eq for eq in context.target_player.equipment_area.values() if eq is not None])
            
            if total_cards == 0:
                logger.debug("目标没有可拆的牌")
                return False
        
        return True
    
    # 技能使用条件
    @staticmethod
    def can_use_jianxiong(context: InteractionContext) -> bool:
        """判断是否可以使用奸雄技能"""
        if not context.source_player:
            return False
        
        # 检查是否有奸雄技能
        if not hasattr(context.source_player, 'has_skill') or not context.source_player.has_skill("奸雄"):
            return False
        
        # 奸雄技能在受到伤害后触发
        if context.interaction_type == InteractionType.DAMAGE:
            if 'damage_card' in context.additional_data:
                return True
        
        return False
    
    @staticmethod
    def can_use_rende(context: InteractionContext) -> bool:
        """判断是否可以使用仁德技能"""
        if not context.source_player:
            return False
        
        # 检查是否有仁德技能
        if not hasattr(context.source_player, 'has_skill') or not context.source_player.has_skill("仁德"):
            return False
        
        # 检查是否有手牌可以给出
        if hasattr(context.source_player, 'hand_cards') and len(context.source_player.hand_cards) == 0:
            logger.debug("没有手牌可以给出")
            return False
        
        # 检查目标玩家
        if not context.target_player or context.target_player == context.source_player:
            logger.debug("无效的目标玩家")
            return False
        
        return True
    
    @staticmethod
    def can_use_paoxiao(context: InteractionContext) -> bool:
        """判断是否可以使用咆哮技能"""
        if not context.source_player:
            return False
        
        # 检查是否有咆哮技能
        if not hasattr(context.source_player, 'has_skill') or not context.source_player.has_skill("咆哮"):
            return False
        
        # 咆哮是锁定技，自动生效，无需额外条件
        return True


class JudgmentRegistry:
    """判断条件注册器"""
    
    def __init__(self):
        self.conditions: Dict[str, List[Callable[[InteractionContext], bool]]] = {}
    
    def register_condition(self, interaction_key: str, condition: Callable[[InteractionContext], bool]):
        """注册判断条件"""
        if interaction_key not in self.conditions:
            self.conditions[interaction_key] = []
        self.conditions[interaction_key].append(condition)
    
    def get_conditions(self, interaction_key: str) -> List[Callable[[InteractionContext], bool]]:
        """获取判断条件"""
        return self.conditions.get(interaction_key, [])
    
    def check_all_conditions(self, interaction_key: str, context: InteractionContext) -> bool:
        """检查所有条件"""
        conditions = self.get_conditions(interaction_key)
        for condition in conditions:
            if not condition(context):
                return False
        return True


# 创建默认的判断条件注册器
default_judgment_registry = JudgmentRegistry()

# 注册基本卡牌条件
default_judgment_registry.register_condition("use_sha", JudgmentConditions.can_use_sha)
default_judgment_registry.register_condition("use_shan", JudgmentConditions.can_use_shan)
default_judgment_registry.register_condition("use_tao", JudgmentConditions.can_use_tao)

# 注册装备条件
default_judgment_registry.register_condition("equip_weapon", JudgmentConditions.can_equip_weapon)
default_judgment_registry.register_condition("equip_armor", JudgmentConditions.can_equip_armor)

# 注册锦囊条件
default_judgment_registry.register_condition("use_wuxiekeji", JudgmentConditions.can_use_wuxiekeji)
default_judgment_registry.register_condition("use_guohechaiqiao", JudgmentConditions.can_use_guohechaiqiao)

# 注册技能条件
default_judgment_registry.register_condition("use_jianxiong", JudgmentConditions.can_use_jianxiong)
default_judgment_registry.register_condition("use_rende", JudgmentConditions.can_use_rende)
default_judgment_registry.register_condition("use_paoxiao", JudgmentConditions.can_use_paoxiao)