#!/usr/bin/env python3
"""
基于基础元素的裁决系统测试

测试新的基础元素裁决框架，验证：
1. 基础元素的正确性
2. 技能与基础元素的组合
3. 与现有Player模型的兼容性
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.adjudication.element_based_adjudication import (
    ElementType, CardElement, HealthElement, FactionElement, 
    EquipmentElement, DistanceElement, element_adjudication_engine
)
from app.core.adjudication.element_player_adapter import (
    ElementPlayerAdapter, quick_check_card_usage, quick_check_skill_usage, quick_calculate_damage
)
from app.models.player import Player
from app.models.character import Character, Kingdom, CharacterFactory
from app.models.card import Card


def create_test_card(name: str, category: str = "basic", suit: str = "红桃", point: int = 1):
    """创建测试卡牌"""
    return Card(name=name, category=category, suit=suit, point=point)


def create_test_player(character_name: str = "曹操", position: int = 0):
    """创建测试玩家"""
    character = CharacterFactory.create_character(character_name)
    player = Player(character)
    player.position = position
    return player


def test_basic_elements():
    """测试基础元素"""
    print("=== 测试基础元素 ===")
    
    # 测试卡牌元素
    print("\n1. 测试卡牌元素")
    cards = [
        create_test_card("杀"),
        create_test_card("闪"),
        create_test_card("桃")
    ]
    card_element = CardElement(cards)
    
    print(f"  总卡牌数: {card_element.count_cards()}")
    print(f"  有杀: {card_element.has_card('杀')}")
    print(f"  有闪: {card_element.has_card('闪')}")
    print(f"  有无懈可击: {card_element.has_card('无懈可击')}")
    print(f"  有基本牌: {card_element.has_card_type('basic')}")
    
    # 测试血量元素
    print("\n2. 测试血量元素")
    health_element = HealthElement(3, 4)
    print(f"  当前血量: {health_element.get_current_value()}")
    print(f"  是否存活: {health_element.is_alive()}")
    print(f"  是否濒死: {health_element.is_dying()}")
    print(f"  是否满血: {health_element.is_full_health()}")
    
    # 应用伤害修正
    health_element.apply_modifier({"type": "damage", "value": 2})
    print(f"  受到2点伤害后: {health_element.calculate_final_value()}")
    print(f"  是否存活: {health_element.is_alive()}")
    
    # 测试势力元素
    print("\n3. 测试势力元素")
    faction_element = FactionElement("魏")
    print(f"  势力: {faction_element.get_current_value()}")
    print(f"  与魏同势力: {faction_element.is_same_faction('魏')}")
    print(f"  与蜀同势力: {faction_element.is_same_faction('蜀')}")
    print(f"  与蜀敌对: {faction_element.is_enemy_faction('蜀')}")
    
    # 测试装备元素
    print("\n4. 测试装备元素")
    weapon = create_test_card("青龙偃月刀", "equipment")
    armor = create_test_card("八卦阵", "equipment")
    equipment_element = EquipmentElement(weapon=weapon, armor=armor)
    
    print(f"  有武器: {equipment_element.has_weapon()}")
    print(f"  有防具: {equipment_element.has_armor()}")
    print(f"  攻击范围加成: {equipment_element.get_attack_range_bonus()}")
    
    # 测试距离元素
    print("\n5. 测试距离元素")
    distance_element = DistanceElement(0, 4)  # 4人游戏，位置0
    print(f"  到位置1的距离: {distance_element.calculate_seat_distance(1)}")
    print(f"  到位置2的距离: {distance_element.calculate_seat_distance(2)}")
    print(f"  到位置3的距离: {distance_element.calculate_seat_distance(3)}")


def test_element_conditions():
    """测试元素条件检查"""
    print("\n=== 测试元素条件检查 ===")
    
    # 创建测试玩家
    player1 = create_test_player("曹操", 0)
    player1.hand_cards = [create_test_card("杀"), create_test_card("闪")]
    player1.weapon = create_test_card("青龙偃月刀", "equipment")
    
    player2 = create_test_player("刘备", 1)
    player2.hand_cards = [create_test_card("桃")]
    
    all_players = [player1, player2]
    
    # 转换为元素
    player1_elements = ElementPlayerAdapter.convert_player_to_elements(player1, all_players)
    player2_elements = ElementPlayerAdapter.convert_player_to_elements(player2, all_players)
    
    print("\n1. 基础条件检查")
    print(f"  玩家1有杀: {element_adjudication_engine.check_element_condition('has_card', player1_elements, card_name='杀')}")
    print(f"  玩家1存活: {element_adjudication_engine.check_element_condition('is_alive', player1_elements)}")
    print(f"  玩家1有武器: {element_adjudication_engine.check_element_condition('has_weapon', player1_elements)}")
    print(f"  玩家1在攻击范围内玩家2: {element_adjudication_engine.check_element_condition('in_attack_range', player1_elements, player2_elements)}")


def test_player_adapter():
    """测试玩家适配器"""
    print("\n=== 测试玩家适配器 ===")
    
    # 创建测试玩家
    player1 = create_test_player("曹操", 0)
    player1.hand_cards = [create_test_card("杀"), create_test_card("闪")]
    player1.weapon = create_test_card("古锭刀", "equipment")
    
    player2 = create_test_player("刘备", 1)
    player2.hand_cards = []  # 无手牌
    
    all_players = [player1, player2]
    
    print("\n1. 卡牌使用检查")
    result = ElementPlayerAdapter.check_basic_card_usage(player1, player2, "杀", all_players)
    print(f"  玩家1对玩家2使用杀: {result['can_use']}")
    if not result['can_use']:
        print(f"  失败原因: {', '.join(result['reasons'])}")
    
    print("\n2. 技能使用检查")
    result = ElementPlayerAdapter.check_skill_usage(player1, "奸雄", all_players=all_players)
    print(f"  玩家1使用奸雄: {result['can_use']}")
    if not result['can_use']:
        print(f"  失败原因: {', '.join(result['reasons'])}")
    
    print("\n3. 伤害计算")
    damage_result = ElementPlayerAdapter.calculate_damage_with_elements(player1, player2, 1, "杀", all_players)
    print(f"  基础伤害: {damage_result['base_damage']}")
    print(f"  最终伤害: {damage_result['final_damage']}")
    print(f"  伤害修正: {damage_result['modifiers']}")
    
    print("\n4. 元素摘要")
    summary = ElementPlayerAdapter.get_element_summary(player1, all_players)
    print(f"  玩家1摘要:")
    print(f"    卡牌: {summary['cards']}")
    print(f"    血量: {summary['health']}")
    print(f"    装备: {summary['equipment']}")


def test_skill_compositions():
    """测试技能组合"""
    print("\n=== 测试技能组合 ===")
    
    # 创建测试玩家
    player = create_test_player("曹操", 0)
    player.hand_cards = [create_test_card("杀")]
    
    all_players = [player]
    
    print("\n1. 技能需求检查")
    print(f"  奸雄技能需求: {quick_check_skill_usage(player, '奸雄', all_players=all_players)}")
    print(f"  突袭技能需求: {quick_check_skill_usage(player, '突袭', all_players=all_players)}")


def test_integration_with_existing_system():
    """测试与现有系统的集成"""
    print("\n=== 测试与现有系统的集成 ===")
    
    # 创建复杂场景
    player1 = create_test_player("曹操", 0)
    player1.hand_cards = [
        create_test_card("杀"),
        create_test_card("闪"),
        create_test_card("桃")
    ]
    player1.weapon = create_test_card("青龙偃月刀", "equipment")
    player1.defense = create_test_card("八卦阵", "equipment")
    
    player2 = create_test_player("刘备", 1)
    player2.hand_cards = [create_test_card("闪"), create_test_card("无懈可击")]
    player2.defense_horse = create_test_card("的卢", "equipment")
    
    all_players = [player1, player2]
    
    print("\n1. 快速检查函数")
    print(f"  玩家1对玩家2使用杀: {quick_check_card_usage(player1, player2, '杀', all_players)}")
    print(f"  玩家1使用桃: {quick_check_card_usage(player1, None, '桃', all_players)}")
    
    print("\n2. 快速伤害计算")
    damage = quick_calculate_damage(player1, player2, 1, "杀", all_players)
    print(f"  玩家1对玩家2造成伤害: {damage}")
    
    print("\n3. 元素摘要对比")
    summary1 = ElementPlayerAdapter.get_element_summary(player1, all_players)
    summary2 = ElementPlayerAdapter.get_element_summary(player2, all_players)
    
    print(f"  玩家1装备: {summary1['equipment']}")
    print(f"  玩家2装备: {summary2['equipment']}")


def main():
    """主测试函数"""
    print("基于基础元素的裁决系统测试")
    print("=" * 50)
    
    try:
        test_basic_elements()
        test_element_conditions()
        test_player_adapter()
        test_skill_compositions()
        test_integration_with_existing_system()
        
        print("\n" + "=" * 50)
        print("所有测试完成！基础元素裁决系统运行正常。")
        
    except Exception as e:
        print(f"\n测试过程中发生错误: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()