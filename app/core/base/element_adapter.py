#!/usr/bin/env python3
"""
玩家模型与基础元素系统的适配器

将现有的Player模型转换为基础元素表示，
使得基于元素的裁决系统能够与现有代码兼容。
"""

from typing import Dict, List, Any
from .game_elements import (
    BaseElement, CardElement, HealthElement, FactionElement, 
    EquipmentElement, DistanceElement
)


class ElementPlayerAdapter:
    """玩家模型到基础元素的适配器"""
    
    @staticmethod
    def convert_player_to_elements(player, all_players: List[Any] = None) -> Dict[str, BaseElement]:
        """将Player对象转换为基础元素字典"""
        elements = {}
        
        # 卡牌元素
        hand_cards = getattr(player, 'hand_cards', [])
        elements['card'] = CardElement(hand_cards)
        
        # 血量元素
        current_hp = getattr(player, 'hp', 0)
        max_hp = getattr(player.character, 'max_hp', 0) if hasattr(player, 'character') else current_hp
        elements['health'] = HealthElement(current_hp, max_hp)
        
        # 势力元素
        faction = getattr(player.character, 'kingdom', None) if hasattr(player, 'character') else None
        if faction:
            faction_name = faction.value if hasattr(faction, 'value') else str(faction)
            elements['faction'] = FactionElement(faction_name)
        
        # 装备元素
        weapon = getattr(player, 'weapon', None)
        armor = getattr(player, 'defense', None)  # Player模型中防具叫defense
        attack_horse = getattr(player, 'attack_horse', None)
        defense_horse = getattr(player, 'defense_horse', None)
        elements['equipment'] = EquipmentElement(weapon, armor, attack_horse, defense_horse)
        
        # 距离元素
        position = getattr(player, 'position', 0)
        total_players = len(all_players) if all_players else 2  # 默认2人游戏
        elements['distance'] = DistanceElement(position, total_players)
        
        return elements
    
    @staticmethod
    def create_interaction_context(source_player, target_player=None, all_players=None, 
                                 action_type: str = None, cards: List[Any] = None) -> Dict[str, Any]:
        """创建基于元素的交互上下文"""
        context = {
            'action_type': action_type,
            'cards': cards or [],
            'source_elements': ElementPlayerAdapter.convert_player_to_elements(source_player, all_players),
        }
        
        if target_player:
            context['target_elements'] = ElementPlayerAdapter.convert_player_to_elements(target_player, all_players)
        
        return context
    
    @staticmethod
    def check_basic_card_usage(source_player, target_player, card_name: str, 
                             all_players: List[Any] = None) -> Dict[str, Any]:
        """检查基本卡牌使用条件"""
        from .element_based_adjudication import element_adjudication_engine
        
        source_elements = ElementPlayerAdapter.convert_player_to_elements(source_player, all_players)
        target_elements = ElementPlayerAdapter.convert_player_to_elements(target_player, all_players) if target_player else None
        
        result = {
            'can_use': True,
            'reasons': [],
            'failed_checks': []
        }
        
        # 基本检查：是否有该卡牌
        if not element_adjudication_engine.check_element_condition(
            'has_card', source_elements, target_elements, card_name=card_name):
            result['can_use'] = False
            result['failed_checks'].append('has_card')
            result['reasons'].append(f'没有{card_name}卡牌')
        
        # 如果有目标，检查目标是否存活
        if target_player:
            if not element_adjudication_engine.check_element_condition(
                'is_alive', target_elements):
                result['can_use'] = False
                result['failed_checks'].append('target_alive')
                result['reasons'].append('目标已死亡')
        
        # 对于杀卡牌，检查攻击范围
        if card_name == '杀' and target_player:
            if not element_adjudication_engine.check_element_condition(
                'in_attack_range', source_elements, target_elements):
                result['can_use'] = False
                result['failed_checks'].append('attack_range')
                result['reasons'].append('目标不在攻击范围内')
        
        return result
    
    @staticmethod
    def check_skill_usage(source_player, skill_name: str, target_player=None, 
                         all_players: List[Any] = None) -> Dict[str, Any]:
        """检查技能使用条件"""
        from .element_based_adjudication import element_adjudication_engine
        
        source_elements = ElementPlayerAdapter.convert_player_to_elements(source_player, all_players)
        target_elements = ElementPlayerAdapter.convert_player_to_elements(target_player, all_players) if target_player else None
        
        result = {
            'can_use': True,
            'reasons': [],
            'failed_checks': []
        }
        
        # 检查技能的基础元素需求
        if not element_adjudication_engine.check_skill_requirements(skill_name, source_elements, target_elements):
            result['can_use'] = False
            result['failed_checks'].append('skill_requirements')
            result['reasons'].append(f'不满足技能{skill_name}的使用条件')
        
        return result
    
    @staticmethod
    def calculate_damage_with_elements(attacker, defender, base_damage: int = 1, 
                                     damage_source: str = None, all_players: List[Any] = None) -> Dict[str, Any]:
        """基于元素计算伤害"""
        attacker_elements = ElementPlayerAdapter.convert_player_to_elements(attacker, all_players)
        defender_elements = ElementPlayerAdapter.convert_player_to_elements(defender, all_players)
        
        final_damage = base_damage
        damage_modifiers = []
        
        # 武器伤害加成
        attacker_equipment = attacker_elements['equipment']
        if attacker_equipment.has_weapon():
            weapon = attacker_equipment.state.current_value['weapon']
            if weapon and hasattr(weapon, 'name'):
                # 古锭刀：对无手牌目标伤害+1
                if weapon.name == '古锭刀':
                    defender_cards = defender_elements['card']
                    if defender_cards.count_cards() == 0:
                        final_damage += 1
                        damage_modifiers.append('古锭刀效果：对无手牌目标伤害+1')
        
        # 防具伤害减免
        defender_equipment = defender_elements['equipment']
        if defender_equipment.has_armor():
            armor = defender_equipment.state.current_value['armor']
            if armor and hasattr(armor, 'name'):
                # 白银狮子：受到超过1点伤害时减免到1点
                if armor.name == '白银狮子' and final_damage > 1:
                    final_damage = 1
                    damage_modifiers.append('白银狮子效果：伤害减免到1点')
        
        return {
            'final_damage': final_damage,
            'base_damage': base_damage,
            'modifiers': damage_modifiers,
            'can_prevent': False  # 可以扩展为检查是否可以防止伤害
        }
    
    @staticmethod
    def get_element_summary(player, all_players: List[Any] = None) -> Dict[str, Any]:
        """获取玩家的基础元素摘要"""
        elements = ElementPlayerAdapter.convert_player_to_elements(player, all_players)
        
        summary = {}
        
        # 卡牌摘要
        card_element = elements['card']
        summary['cards'] = {
            'total_count': card_element.count_cards(),
            'has_sha': card_element.has_card('杀'),
            'has_shan': card_element.has_card('闪'),
            'has_tao': card_element.has_card('桃'),
            'basic_cards': card_element.count_cards() if card_element.has_card_type('basic') else 0,
            'trick_cards': card_element.count_cards() if card_element.has_card_type('trick') else 0,
            'equipment_cards': card_element.count_cards() if card_element.has_card_type('equipment') else 0
        }
        
        # 血量摘要
        health_element = elements['health']
        summary['health'] = {
            'current': health_element.state.current_value,
            'max': health_element.state.max_value,
            'is_alive': health_element.is_alive(),
            'is_dying': health_element.is_dying(),
            'is_full': health_element.is_full_health()
        }
        
        # 势力摘要
        if 'faction' in elements:
            faction_element = elements['faction']
            summary['faction'] = {
                'name': faction_element.state.current_value
            }
        
        # 装备摘要
        equipment_element = elements['equipment']
        summary['equipment'] = {
            'has_weapon': equipment_element.has_weapon(),
            'has_armor': equipment_element.has_armor(),
            'has_attack_horse': equipment_element.has_horse('attack'),
            'has_defense_horse': equipment_element.has_horse('defense'),
            'attack_range_bonus': equipment_element.get_attack_range_bonus()
        }
        
        # 距离摘要
        distance_element = elements['distance']
        summary['distance'] = {
            'position': distance_element.state.current_value['position'],
            'total_players': distance_element.state.current_value['total_players']
        }
        
        return summary


# 便捷函数
def quick_check_card_usage(source_player, target_player, card_name: str, all_players: List[Any] = None) -> bool:
    """快速检查卡牌使用条件"""
    result = ElementPlayerAdapter.check_basic_card_usage(source_player, target_player, card_name, all_players)
    return result['can_use']


def quick_check_skill_usage(source_player, skill_name: str, target_player=None, all_players: List[Any] = None) -> bool:
    """快速检查技能使用条件"""
    result = ElementPlayerAdapter.check_skill_usage(source_player, skill_name, target_player, all_players)
    return result['can_use']


def quick_calculate_damage(attacker, defender, base_damage: int = 1, damage_source: str = None, all_players: List[Any] = None) -> int:
    """快速计算伤害"""
    result = ElementPlayerAdapter.calculate_damage_with_elements(attacker, defender, base_damage, damage_source, all_players)
    return result['final_damage']