#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
标准规则函数库
实现常用的判断、修正和计算函数，供数据驱动的裁决系统使用
"""

from typing import Dict, List, Optional, Any
import logging
from ..interaction.interaction_model import InteractionContext
from .base_adjudication_model import AdjudicationData

logger = logging.getLogger(__name__)


# ==================== 判断条件函数 ====================

def check_has_sha_card(context: InteractionContext) -> bool:
    """检查是否有杀卡牌"""
    if not context.source_player:
        return False
    
    if hasattr(context.source_player, 'has_card_name'):
        return context.source_player.has_card_name("杀")
    
    # 备用检查方法
    if hasattr(context.source_player, 'hand_cards'):
        for card in context.source_player.hand_cards:
            if hasattr(card, 'name') and card.name == "杀":
                return True
    
    return False


def check_target_alive(context: InteractionContext) -> bool:
    """检查目标是否存活"""
    if not context.target_player:
        return False
    
    if hasattr(context.target_player, 'is_alive'):
        return context.target_player.is_alive()
    
    # 备用检查方法
    if hasattr(context.target_player, 'hp'):
        return context.target_player.hp > 0
    
    return True  # 默认认为存活


def check_attack_range(context: InteractionContext) -> bool:
    """检查是否在攻击范围内"""
    if not context.source_player or not context.target_player:
        return False
    
    # 检查攻击范围
    if hasattr(context.source_player, 'get_attack_range') and hasattr(context.source_player, 'get_distance_to'):
        attack_range = context.source_player.get_attack_range()
        distance = context.source_player.get_distance_to(context.target_player)
        return distance <= attack_range
    
    return True  # 默认认为在范围内


def check_sha_count_limit(context: InteractionContext) -> bool:
    """检查出杀次数限制"""
    if not context.source_player:
        return False
    
    if hasattr(context.source_player, 'sha_count_this_turn') and hasattr(context.source_player, 'max_sha_per_turn'):
        sha_count = getattr(context.source_player, 'sha_count_this_turn', 0)
        max_sha_count = getattr(context.source_player, 'max_sha_per_turn', 1)
        return sha_count < max_sha_count
    
    return True  # 默认允许


def check_has_tao_card(context: InteractionContext) -> bool:
    """检查是否有桃卡牌"""
    if not context.source_player:
        return False
    
    if hasattr(context.source_player, 'has_card_name'):
        return context.source_player.has_card_name("桃")
    
    return False


def check_target_needs_healing(context: InteractionContext) -> bool:
    """检查目标是否需要治疗"""
    if not context.target_player:
        return False
    
    if hasattr(context.target_player, 'hp') and hasattr(context.target_player, 'max_hp'):
        return context.target_player.hp < context.target_player.max_hp
    
    return False


def check_can_equip_weapon(context: InteractionContext) -> bool:
    """检查是否可以装备武器"""
    if not context.source_player or not context.card:
        return False
    
    # 检查卡牌类型
    if hasattr(context.card, 'card_type') and context.card.card_type != "装备":
        return False
    
    if hasattr(context.card, 'sub_type') and context.card.sub_type != "武器":
        return False
    
    return True


# ==================== 修正函数 ====================

def apply_weapon_damage_bonus(context: InteractionContext, data: AdjudicationData) -> Dict[str, Any]:
    """应用武器伤害加成"""
    bonus = 0
    weapon_info = {}
    
    if context.source_player and hasattr(context.source_player, 'weapon'):
        weapon = context.source_player.weapon
        if weapon and hasattr(weapon, 'damage_bonus'):
            bonus = weapon.damage_bonus
            weapon_info = {
                'weapon_name': getattr(weapon, 'name', '未知武器'),
                'damage_bonus': bonus
            }
    
    return {
        'type': 'damage_bonus',
        'value': bonus,
        'source': 'weapon',
        'details': weapon_info
    }


def apply_skill_damage_modification(context: InteractionContext, data: AdjudicationData) -> Dict[str, Any]:
    """应用技能伤害修正"""
    modifications = []
    
    if context.source_player and hasattr(context.source_player, 'active_skills'):
        for skill in context.source_player.active_skills:
            if hasattr(skill, 'modify_damage'):
                mod_result = skill.modify_damage(context)
                if mod_result:
                    modifications.append(mod_result)
    
    return {
        'type': 'skill_modification',
        'modifications': modifications,
        'source': 'skills'
    }


def check_target_defense(context: InteractionContext, data: AdjudicationData) -> Dict[str, Any]:
    """检查目标防御（可能触发嵌套裁决）"""
    defense_options = []
    
    if context.target_player:
        # 检查是否有闪
        if hasattr(context.target_player, 'has_card_name') and context.target_player.has_card_name("闪"):
            defense_options.append({
                'type': 'shan',
                'description': '使用闪抵消杀的效果'
            })
        
        # 检查防御技能
        if hasattr(context.target_player, 'active_skills'):
            for skill in context.target_player.active_skills:
                if hasattr(skill, 'can_defend_against'):
                    if skill.can_defend_against(context):
                        defense_options.append({
                            'type': 'skill_defense',
                            'skill_name': getattr(skill, 'name', '未知技能'),
                            'description': f'使用技能{getattr(skill, "name", "未知技能")}进行防御'
                        })
    
    return {
        'type': 'defense_check',
        'defense_options': defense_options,
        'trigger_nested': len(defense_options) > 0,
        'source': 'target_defense'
    }


def apply_distance_modification(context: InteractionContext, data: AdjudicationData) -> Dict[str, Any]:
    """应用距离修正"""
    distance_mods = []
    
    # 检查装备对距离的影响
    if context.source_player and hasattr(context.source_player, 'equipment'):
        for equipment in context.source_player.equipment:
            if hasattr(equipment, 'distance_modifier'):
                distance_mods.append({
                    'source': equipment.name,
                    'modifier': equipment.distance_modifier
                })
    
    return {
        'type': 'distance_modification',
        'modifications': distance_mods,
        'source': 'equipment'
    }


# ==================== 计算函数 ====================

def calculate_final_damage(context: InteractionContext, data: AdjudicationData) -> Dict[str, Any]:
    """计算最终伤害"""
    base_damage = 1  # 杀的基础伤害
    total_damage = base_damage
    
    # 应用所有伤害修正
    for mod_result in data.modification_results:
        if isinstance(mod_result, dict):
            if mod_result.get('type') == 'damage_bonus':
                total_damage += mod_result.get('value', 0)
            elif mod_result.get('type') == 'skill_modification':
                for skill_mod in mod_result.get('modifications', []):
                    if isinstance(skill_mod, dict) and 'damage_change' in skill_mod:
                        total_damage += skill_mod['damage_change']
    
    # 确保伤害不为负数
    total_damage = max(0, total_damage)
    
    return {
        'base_damage': base_damage,
        'final_damage': total_damage,
        'damage_sources': [mod for mod in data.modification_results if isinstance(mod, dict) and mod.get('type') in ['damage_bonus', 'skill_modification']]
    }


def calculate_card_consumption(context: InteractionContext, data: AdjudicationData) -> Dict[str, Any]:
    """计算卡牌消耗"""
    consumed_cards = []
    
    # 基础消耗：使用的杀
    if context.card:
        consumed_cards.append({
            'card': context.card,
            'reason': '使用杀'
        })
    
    # 检查是否有额外的卡牌消耗
    for mod_result in data.modification_results:
        if isinstance(mod_result, dict) and 'consumed_cards' in mod_result:
            consumed_cards.extend(mod_result['consumed_cards'])
    
    return {
        'consumed_cards': consumed_cards,
        'total_count': len(consumed_cards)
    }


def apply_final_effects(context: InteractionContext, data: AdjudicationData) -> Dict[str, Any]:
    """应用最终效果"""
    effects = []
    
    # 获取最终伤害
    final_damage = 0
    for calc_result in data.calculation_outputs.values():
        if isinstance(calc_result, dict) and 'final_damage' in calc_result:
            final_damage = calc_result['final_damage']
            break
    
    # 应用伤害效果
    if final_damage > 0 and context.target_player:
        effects.append({
            'type': 'damage',
            'target': context.target_player,
            'amount': final_damage,
            'source': context.source_player
        })
    
    # 应用卡牌消耗效果
    for calc_result in data.calculation_outputs.values():
        if isinstance(calc_result, dict) and 'consumed_cards' in calc_result:
            for card_info in calc_result['consumed_cards']:
                effects.append({
                    'type': 'discard_card',
                    'card': card_info['card'],
                    'reason': card_info['reason']
                })
    
    return {
        'effects': effects,
        'success': len(effects) > 0
    }


# ==================== 桃卡牌相关函数 ====================

def calculate_healing_amount(context: InteractionContext, data: AdjudicationData) -> Dict[str, Any]:
    """计算治疗量"""
    base_healing = 1  # 桃的基础治疗量
    total_healing = base_healing
    
    # 应用治疗修正
    for mod_result in data.modification_results:
        if isinstance(mod_result, dict) and mod_result.get('type') == 'healing_bonus':
            total_healing += mod_result.get('value', 0)
    
    return {
        'base_healing': base_healing,
        'final_healing': total_healing
    }


def apply_healing_effects(context: InteractionContext, data: AdjudicationData) -> Dict[str, Any]:
    """应用治疗效果"""
    effects = []
    
    # 获取最终治疗量
    final_healing = 0
    for calc_result in data.calculation_outputs.values():
        if isinstance(calc_result, dict) and 'final_healing' in calc_result:
            final_healing = calc_result['final_healing']
            break
    
    # 应用治疗效果
    if final_healing > 0 and context.target_player:
        effects.append({
            'type': 'heal',
            'target': context.target_player,
            'amount': final_healing,
            'source': context.source_player
        })
    
    return {
        'effects': effects,
        'success': len(effects) > 0
    }


# ==================== 装备相关函数 ====================

def apply_equipment_effects(context: InteractionContext, data: AdjudicationData) -> Dict[str, Any]:
    """应用装备效果"""
    effects = []
    
    if context.card and context.source_player:
        effects.append({
            'type': 'equip',
            'target': context.source_player,
            'equipment': context.card
        })
    
    return {
        'effects': effects,
        'success': len(effects) > 0
    }