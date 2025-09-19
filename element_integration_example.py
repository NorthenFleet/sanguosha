#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
基础元素裁决系统与现有系统集成示例

这个文件展示了如何将基于基础元素的裁决系统与现有的三国杀游戏系统集成，
实现技能的灵活处理和裁决逻辑的统一管理。
"""

from typing import Dict, List, Any, Optional
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# 更新导入路径以使用base模块
from app.core.base import (
    ElementBasedAdjudicationEngine, 
    BaseElement,
    CardElement, HealthElement, FactionElement, EquipmentElement, DistanceElement,
    ElementPlayerAdapter
)
from app.models.player import Player
from app.models.card import Card
from app.models.character import Character, CharacterFactory
import json


class IntegratedAdjudicationSystem:
    """集成的裁决系统，结合基础元素和现有游戏逻辑"""
    
    def __init__(self):
        self.element_engine = ElementBasedAdjudicationEngine()
        self.adapter = ElementPlayerAdapter()
        self.load_skill_compositions()
    
    def load_skill_compositions(self):
        """加载技能组合配置"""
        try:
            with open('skill_element_compositions.json', 'r', encoding='utf-8') as f:
                self.skill_configs = json.load(f)
        except FileNotFoundError:
            print("警告：未找到技能配置文件，使用默认配置")
            self.skill_configs = {}
    
    def adjudicate_skill_usage(self, player: Player, skill_name: str, 
                             target: Optional[Player] = None, 
                             context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        裁决技能使用
        
        Args:
            player: 使用技能的玩家
            skill_name: 技能名称
            target: 目标玩家（如果有）
            context: 额外上下文信息
            
        Returns:
            裁决结果字典
        """
        # 获取玩家的基础元素
        elements = self.adapter.convert_player_to_elements(player)
        
        # 获取技能配置
        skill_config = self.skill_configs.get('skills', {}).get(skill_name, {})
        
        if not skill_config:
            return {
                'success': False,
                'reason': f'未找到技能 {skill_name} 的配置',
                'elements_checked': elements
            }
        
        # 检查技能触发条件
        trigger_conditions = skill_config.get('trigger_conditions', [])
        condition_results = []
        
        for condition in trigger_conditions:
            result = self._check_element_condition(elements, condition, target)
            condition_results.append({
                'condition': condition,
                'result': result
            })
        
        # 所有条件都满足才能使用技能
        can_use_skill = all(r['result'] for r in condition_results)
        
        if not can_use_skill:
            return {
                'success': False,
                'reason': '技能使用条件不满足',
                'condition_results': condition_results,
                'elements_checked': elements
            }
        
        # 计算技能效果
        effects = self._calculate_skill_effects(player, skill_config, target, context)
        
        return {
            'success': True,
            'skill_name': skill_name,
            'condition_results': condition_results,
            'effects': effects,
            'elements_used': elements
        }
    
    def _check_element_condition(self, elements: Dict[str, BaseElement], 
                               condition: Dict[str, Any], 
                               target: Optional[Player] = None) -> bool:
        """检查基础元素条件"""
        element_type = condition.get('element_type')
        check_type = condition.get('check_type')
        value = condition.get('value')
        
        if element_type not in elements:
            return False
        
        element = elements[element_type]
        
        # 根据元素类型和检查类型进行判断
        if element_type == 'card':
            if check_type == 'has_card_type':
                return element.has_card_type(value)
            elif check_type == 'card_count_gte':
                return element.count_cards() >= value
            elif check_type == 'hand_empty':
                return element.count_cards() == 0
        
        elif element_type == 'health':
            if check_type == 'is_alive':
                return element.is_alive()
            elif check_type == 'is_dying':
                return element.is_dying()
            elif check_type == 'hp_gte':
                return element.current >= value
        
        elif element_type == 'faction':
            if check_type == 'same_faction' and target:
                target_elements = self.adapter.convert_player_to_elements(target)
                target_faction = target_elements.get('faction')
                return element.is_same_faction(target_faction.state.current_value) if target_faction else False
        
        elif element_type == 'equipment':
            if check_type == 'has_weapon':
                return element.has_weapon()
            elif check_type == 'has_armor':
                return element.has_armor()
        
        return False
    
    def _calculate_skill_effects(self, player: Player, skill_config: Dict[str, Any], 
                               target: Optional[Player] = None, 
                               context: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """计算技能效果"""
        effects = []
        skill_effects = skill_config.get('effects', [])
        
        for effect_config in skill_effects:
            effect_type = effect_config.get('type')
            
            if effect_type == 'draw_cards':
                count = effect_config.get('count', 1)
                effects.append({
                    'type': 'draw_cards',
                    'count': count,
                    'description': f'摸{count}张牌'
                })
            
            elif effect_type == 'damage':
                base_damage = effect_config.get('damage', 1)
                # 可以根据装备等因素调整伤害
                damage_result = self.adapter.calculate_damage_with_elements(player, target, base_damage)
                final_damage = damage_result.get('final_damage', base_damage)
                effects.append({
                    'type': 'damage',
                    'base_damage': base_damage,
                    'final_damage': final_damage,
                    'description': f'造成{final_damage}点伤害'
                })
            
            elif effect_type == 'heal':
                heal_amount = effect_config.get('amount', 1)
                effects.append({
                    'type': 'heal',
                    'amount': heal_amount,
                    'description': f'回复{heal_amount}点体力'
                })
        
        return effects
    
    def get_available_skills(self, player: Player) -> List[Dict[str, Any]]:
        """获取玩家当前可用的技能列表"""
        available_skills = []
        elements = self.adapter.convert_player_to_elements(player)
        
        # 获取角色技能
        character_skills = getattr(player.character, 'skills', [])
        
        for skill_name in character_skills:
            skill_config = self.skill_configs.get('skills', {}).get(skill_name, {})
            if not skill_config:
                continue
            
            # 检查技能是否可用
            trigger_conditions = skill_config.get('trigger_conditions', [])
            can_use = all(
                self._check_element_condition(elements, condition) 
                for condition in trigger_conditions
            )
            
            available_skills.append({
                'name': skill_name,
                'can_use': can_use,
                'description': skill_config.get('description', ''),
                'conditions': trigger_conditions
            })
        
        return available_skills
    
    def analyze_game_state(self, players: List[Player]) -> Dict[str, Any]:
        """分析当前游戏状态的基础元素分布"""
        analysis = {
            'total_players': len(players),
            'alive_players': 0,
            'faction_distribution': {},
            'card_distribution': {},
            'equipment_summary': {},
            'health_summary': {}
        }
        
        for i, player in enumerate(players):
            elements = self.adapter.convert_player_to_elements(player, players)
            
            # 统计存活玩家
            if elements['health'].is_alive():
                analysis['alive_players'] += 1
            
            # 统计势力分布
            faction = elements['faction'].state.current_value
            analysis['faction_distribution'][faction] = analysis['faction_distribution'].get(faction, 0) + 1
            
            # 统计卡牌分布
            card_count = elements['card'].count_cards()
            analysis['card_distribution'][f'player_{i}'] = card_count
            
            # 统计装备情况
            equipment = elements['equipment']
            analysis['equipment_summary'][f'player_{i}'] = {
                'weapon': equipment.has_weapon(),
                'armor': equipment.has_armor(),
                'attack_range': equipment.get_attack_range_bonus()
            }
            
            # 统计血量情况
            health = elements['health']
            analysis['health_summary'][f'player_{i}'] = {
                'current': health.state.current_value,
                'max': health.state.max_value,
                'percentage': health.state.current_value / health.state.max_value if health.state.max_value > 0 else 0
            }
        
        return analysis


def demo_integrated_system():
    """演示集成系统的使用"""
    print("=== 基础元素裁决系统集成演示 ===\n")
    
    # 创建集成系统
    system = IntegratedAdjudicationSystem()
    
    # 创建测试玩家
    character1 = CharacterFactory.create_character("曹操")
    character2 = CharacterFactory.create_character("刘备")
    
    player1 = Player(character1)
    player1.position = 0
    player2 = Player(character2)
    player2.position = 1
    
    # 添加一些卡牌和装备
    player1.hand_cards = [
        Card("杀", "basic", "spade", 7),
        Card("闪", "basic", "diamond", 2)
    ]
    player1.weapon = Card("青龙偃月刀", "equipment", "spade", 5)
    
    player2.hand_cards = [
        Card("桃", "basic", "heart", 3)
    ]
    
    print("1. 分析游戏状态")
    game_analysis = system.analyze_game_state([player1, player2])
    print(f"  存活玩家: {game_analysis['alive_players']}/{game_analysis['total_players']}")
    print(f"  势力分布: {game_analysis['faction_distribution']}")
    print(f"  卡牌分布: {game_analysis['card_distribution']}")
    print()
    
    print("2. 获取可用技能")
    available_skills = system.get_available_skills(player1)
    print(f"  {player1.character.name}的可用技能:")
    for skill in available_skills:
        status = "✓" if skill['can_use'] else "✗"
        print(f"    {status} {skill['name']}: {skill['description']}")
    print()
    
    print("3. 裁决技能使用")
    # 尝试使用奸雄技能
    result = system.adjudicate_skill_usage(player1, "奸雄", context={'damage_received': True})
    print(f"  使用奸雄技能: {'成功' if result['success'] else '失败'}")
    if result['success']:
        print(f"    技能效果: {[effect['description'] for effect in result['effects']]}")
    else:
        print(f"    失败原因: {result['reason']}")
    print()
    
    print("4. 裁决卡牌使用")
    # 尝试使用杀
    card_result = system.adjudicate_skill_usage(player1, "使用杀", target=player2)
    print(f"  对{player2.character.name}使用杀: {'成功' if card_result.get('success', False) else '失败'}")
    print()
    
    print("=== 演示完成 ===")


if __name__ == "__main__":
    demo_integrated_system()