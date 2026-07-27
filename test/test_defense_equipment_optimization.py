#!/usr/bin/env python3
"""
防御装备优化功能测试
测试八卦阵（非锁定技）和仁王盾（锁定技）的功能
"""
import sys
import os

from app.models.player import Player
from app.models.character import Character, Kingdom
from app.models.card import Card
from app.models.enums import CardType
from app.models.card_actions import ShaAction
from app.core.base.game import Game
from app.core.events.event_system import EventManager

def test_bagua_choice_mechanism():
    """测试八卦阵的选择机制（非锁定技）"""
    print("=== 测试八卦阵选择机制 ===")
    
    # 创建测试玩家
    character = Character("诸葛亮", Kingdom.SHU, 3, ["观星", "空城"])
    player = Player(character)
    
    # 装备八卦阵
    bagua_card = Card("八卦阵", CardType.EQUIP, "红桃", 2)
    bagua_card.equipment_type = "armor"
    bagua_card.defense_effect = "need_shan"
    bagua_card.is_locked_skill = False
    player.defense = bagua_card
    player.equipped.append(bagua_card)
    
    # 测试触发条件检查
    can_trigger = player.can_trigger_defense_equipment("need_shan", "receive_sha")
    print(f"八卦阵可以触发: {can_trigger}")
    
    # 创建杀卡牌
    sha_card = Card("杀", CardType.BASIC, "红桃", 7)
    sha_action = ShaAction()
    
    # 测试响应卡牌获取
    response_cards = sha_action.get_response_cards(player)
    print(f"可响应卡牌: {response_cards}")
    
    print("八卦阵选择机制测试完成\n")

def test_renwang_auto_trigger():
    """测试仁王盾的自动触发机制（锁定技）"""
    print("=== 测试仁王盾自动触发机制 ===")
    
    # 创建测试玩家
    character = Character("刘备", Kingdom.SHU, 4, ["仁德", "激将"])
    player = Player(character)
    
    # 装备仁王盾
    renwang_card = Card("仁王盾", CardType.EQUIP, "梅花", 2)
    renwang_card.equipment_type = "armor"
    renwang_card.defense_effect = "prevent_black_sha"
    renwang_card.is_locked_skill = True
    player.defense = renwang_card
    player.equipped.append(renwang_card)
    
    # 测试黑色杀的触发
    black_sha = Card("杀", CardType.BASIC, "黑桃", 7)
    can_trigger_black = player.can_trigger_defense_equipment("receive_sha", {"card": black_sha})
    print(f"仁王盾对黑桃杀可以触发: {can_trigger_black}")
    
    # 测试红色杀的触发
    red_sha = Card("杀", CardType.BASIC, "红桃", 7)
    can_trigger_red = player.can_trigger_defense_equipment("receive_sha", {"card": red_sha})
    print(f"仁王盾对红桃杀可以触发: {can_trigger_red}")
    
    print("仁王盾自动触发机制测试完成\n")

def test_sha_defense_interaction():
    """测试杀与防御装备的交互"""
    print("=== 测试杀与防御装备交互 ===")
    
    # 创建测试玩家
    character = Character("关羽", Kingdom.SHU, 4, ["武圣", "义绝"])
    player = Player(character)
    
    # 装备仁王盾
    renwang_card = Card("仁王盾", CardType.EQUIP, "梅花", 2)
    renwang_card.equipment_type = "armor"
    renwang_card.defense_effect = "prevent_black_sha"
    renwang_card.is_locked_skill = True
    player.defense = renwang_card
    player.equipped.append(renwang_card)
    
    # 创建黑色杀
    black_sha = Card("杀", CardType.BASIC, "黑桃", 7)
    sha_action = ShaAction()
    
    # 测试杀的效果应用（需要创建游戏实例和目标玩家）
    from app.core.events.event_system import EventManager
    
    event_manager = EventManager()
    game = Game(event_manager)
    
    # 创建攻击者
    attacker_character = Character("张飞", Kingdom.SHU, 4, ["咆哮"])
    attacker = Player(attacker_character)
    attacker.hand_cards.append(black_sha)  # 给攻击者添加黑色杀
    
    # 创建红色杀
    red_sha = Card("杀", CardType.BASIC, "红桃", 7)
    red_sha_action = ShaAction()
    
    # 测试仁王盾对黑色杀的防护
    try:
        result = sha_action.apply_effect(game, attacker, player)
        print(f"黑桃杀对装备仁王盾的玩家效果: {result}")
    except Exception as e:
        print(f"黑桃杀测试出现异常: {e}")
    
    # 测试红色杀
    attacker.hand_cards.clear()
    attacker.hand_cards.append(red_sha)  # 给攻击者添加红色杀
    
    try:
        result_red = red_sha_action.apply_effect(game, attacker, player)
        print(f"红桃杀对装备仁王盾的玩家效果: {result_red}")
    except Exception as e:
        print(f"红桃杀测试出现异常: {e}")
    
    print("杀与防御装备交互测试完成\n")

def test_game_damage_defense_check():
    """测试游戏伤害处理中的防御装备检查"""
    print("=== 测试游戏伤害处理中的防御装备检查 ===")
    
    # 创建游戏实例
    from app.core.events.event_system import EventManager
    
    event_manager = EventManager()
    game = Game(event_manager)
    
    # 创建玩家
    character = Character("关羽", Kingdom.SHU, 4, ["武圣"])
    player = Player(character)
    
    # 装备仁王盾
    renwang_card = Card("仁王盾", CardType.EQUIP, "黑桃", 2)
    player.defense = renwang_card
    player.equipped.append(renwang_card)
    
    # 创建伤害卡牌
    black_sha = Card("杀", CardType.BASIC, "黑桃", 7)
    red_sha = Card("杀", CardType.BASIC, "红桃", 7)
    
    # 测试游戏伤害处理
    print(f"玩家初始血量: {player.hp}")
    
    # 测试黑色杀造成的伤害（应该被仁王盾防护）
    try:
        game.handle_damage(player, 1, black_sha)
        print(f"黑色杀攻击后血量: {player.hp}")
    except Exception as e:
        print(f"黑色杀伤害处理异常: {e}")
    
    # 测试红色杀造成的伤害（应该正常造成伤害）
    try:
        game.handle_damage(player, 1, red_sha)
        print(f"红色杀攻击后血量: {player.hp}")
    except Exception as e:
        print(f"红色杀伤害处理异常: {e}")
    
    print("游戏伤害处理中的防御装备检查测试完成\n")

def run_all_tests():
    """运行所有测试"""
    print("开始防御装备优化功能测试...\n")
    
    try:
        test_bagua_choice_mechanism()
        test_renwang_auto_trigger()
        test_sha_defense_interaction()
        test_game_damage_defense_check()
        
        print("所有测试完成！")
        
    except Exception as e:
        print(f"测试过程中出现错误: {e}")
        import traceback
        traceback.print_exc()

