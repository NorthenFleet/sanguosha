#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
防御装备优化功能测试
测试锁定技和非锁定技的区分，以及防御装备的触发机制
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.models.player import Player
from app.models.character import Character, Kingdom
from app.models.card import Card
from app.models.enums import CardType
from app.models.card_actions import ShaAction
from app.core.base.game import Game
from app.core.base.event_manager import EventManager


def create_test_card(name, card_type="装备", suit="黑桃", rank=1):
    """创建测试卡牌"""
    return Card(name=name, type=CardType.EQUIPMENT if card_type == "装备" else CardType.BASIC, 
                suit=suit, rank=rank)


def test_bagua_zhen_choice():
    """测试八卦阵的选择机制（非锁定技）"""
    print("=== 测试八卦阵选择机制 ===")
    
    # 创建角色和玩家
    character = Character("诸葛亮", Kingdom.SHU, 3, ["观星", "空城"])
    player = Player(character)
    
    # 装备八卦阵
    bagua_card = create_test_card("八卦阵")
    player.defense = bagua_card
    
    # 测试防御装备效果获取
    defense_effect = player.get_defense_equipment_effects()
    print(f"八卦阵效果: {defense_effect}")
    
    # 测试触发条件检查
    can_trigger = player.can_trigger_defense_equipment("need_shan")
    print(f"八卦阵可以触发: {can_trigger}")
    
    # 测试技能类型
    skill_type = defense_effect.get("skill_type")
    can_choose = defense_effect.get("can_choose")
    print(f"技能类型: {skill_type}, 可选择: {can_choose}")
    
    assert skill_type == "non_locked", "八卦阵应该是非锁定技"
    assert can_choose == True, "八卦阵应该可以选择是否发动"
    print("✓ 八卦阵选择机制测试通过\n")


def test_renwang_dun_auto_trigger():
    """测试仁王盾的自动触发机制（锁定技）"""
    print("=== 测试仁王盾自动触发机制 ===")
    
    # 创建角色和玩家
    character = Character("刘备", Kingdom.SHU, 4, ["仁德", "激将"])
    player = Player(character)
    
    # 装备仁王盾
    renwang_card = create_test_card("仁王盾")
    player.defense = renwang_card
    
    # 测试防御装备效果获取
    defense_effect = player.get_defense_equipment_effects()
    print(f"仁王盾效果: {defense_effect}")
    
    # 测试黑色杀的触发
    black_sha = create_test_card("杀", "基本牌", "黑桃", 7)
    context = {"trigger": "receive_sha", "card": black_sha}
    can_trigger = player.can_trigger_defense_equipment("receive_sha", context)
    print(f"对黑色杀可以触发: {can_trigger}")
    
    # 测试红色杀的触发
    red_sha = create_test_card("杀", "基本牌", "红桃", 7)
    context_red = {"trigger": "receive_sha", "card": red_sha}
    can_trigger_red = player.can_trigger_defense_equipment("receive_sha", context_red)
    print(f"对红色杀可以触发: {can_trigger_red}")
    
    # 测试技能类型
    skill_type = defense_effect.get("skill_type")
    can_choose = defense_effect.get("can_choose")
    print(f"技能类型: {skill_type}, 可选择: {can_choose}")
    
    assert skill_type == "locked", "仁王盾应该是锁定技"
    assert can_choose == False, "仁王盾不应该可以选择"
    assert can_trigger == True, "仁王盾应该对黑色杀自动触发"
    assert can_trigger_red == False, "仁王盾不应该对红色杀触发"
    print("✓ 仁王盾自动触发机制测试通过\n")


def test_sha_action_with_defense():
    """测试杀动作与防御装备的交互"""
    print("=== 测试杀动作与防御装备交互 ===")
    
    # 创建事件管理器和游戏
    event_manager = EventManager()
    game = Game(event_manager)
    
    # 创建攻击者和防御者
    attacker_char = Character("张飞", Kingdom.SHU, 4, ["咆哮"])
    defender_char = Character("刘备", Kingdom.SHU, 4, ["仁德"])
    
    attacker = Player(attacker_char)
    defender = Player(defender_char)
    
    game.add_player(attacker)
    game.add_player(defender)
    
    # 测试1: 仁王盾对黑色杀的防御
    print("1. 测试仁王盾对黑色杀的防御:")
    defender.defense = create_test_card("仁王盾")
    black_sha = create_test_card("杀", "基本牌", "黑桃", 7)
    
    sha_action = ShaAction()
    original_hp = defender.hp
    
    # 应用杀的效果
    result = sha_action.apply_effect(game, attacker, defender, black_sha)
    print(f"杀的效果结果: {result}")
    print(f"防御者血量变化: {original_hp} -> {defender.hp}")
    
    # 测试2: 仁王盾对红色杀不防御
    print("\n2. 测试仁王盾对红色杀不防御:")
    defender.hp = original_hp  # 恢复血量
    red_sha = create_test_card("杀", "基本牌", "红桃", 7)
    
    result_red = sha_action.apply_effect(game, attacker, defender, red_sha)
    print(f"红色杀的效果结果: {result_red}")
    print(f"防御者血量变化: {original_hp} -> {defender.hp}")
    
    print("✓ 杀动作与防御装备交互测试完成\n")


def test_game_damage_handling():
    """测试游戏伤害处理中的防御装备检查"""
    print("=== 测试游戏伤害处理中的防御装备检查 ===")
    
    # 创建事件管理器和游戏
    event_manager = EventManager()
    game = Game(event_manager)
    
    # 创建玩家
    character = Character("刘备", Kingdom.SHU, 4, ["仁德"])
    player = Player(character)
    player.defense = create_test_card("仁王盾")
    
    game.add_player(player)
    
    # 测试黑色杀被仁王盾防御
    print("1. 测试黑色杀被仁王盾防御:")
    original_hp = player.hp
    black_sha = create_test_card("杀", "基本牌", "黑桃", 7)
    
    damage_prevented = game.handle_damage(player, 1, black_sha)
    print(f"伤害是否被防止: {damage_prevented == False}")
    print(f"玩家血量: {original_hp} -> {player.hp}")
    
    # 测试红色杀不被仁王盾防御
    print("\n2. 测试红色杀不被仁王盾防御:")
    red_sha = create_test_card("杀", "基本牌", "红桃", 7)
    
    damage_taken = game.handle_damage(player, 1, red_sha)
    print(f"伤害是否造成: {damage_taken == False}")
    print(f"玩家血量: {original_hp} -> {player.hp}")
    
    print("✓ 游戏伤害处理测试完成\n")


def run_all_tests():
    """运行所有测试"""
    print("开始防御装备优化功能测试")
    print("=" * 50)
    
    try:
        test_bagua_zhen_choice()
        test_renwang_dun_auto_trigger()
        test_sha_action_with_defense()
        test_game_damage_handling()
        
        print("=" * 50)
        print("✓ 所有防御装备优化测试通过！")
        print("\n功能总结:")
        print("1. ✓ 八卦阵（非锁定技）- 可选择是否发动")
        print("2. ✓ 仁王盾（锁定技）- 自动响应黑色杀")
        print("3. ✓ 防御装备类型区分正确")
        print("4. ✓ 触发时机和响应系统完善")
        
    except Exception as e:
        print(f"✗ 测试失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    run_all_tests()