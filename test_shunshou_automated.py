#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
sys.path.append('.')

from app.models.player import Player
from app.models.character import Character, Kingdom
from app.models.card import Card
from app.models.card_actions import ShunShouQianYangAction
from app.core.base.game import Game
from app.core.events.event_system import EventManager

def create_test_game():
    """创建测试游戏环境"""
    event_manager = EventManager()
    game = Game(event_manager)
    
    # 创建角色
    attacker_char = Character("曹操", Kingdom.WEI, 4, ["奸雄"])
    defender_char = Character("刘备", Kingdom.SHU, 4, ["仁德"])
    
    # 创建玩家
    attacker = Player(attacker_char)
    defender = Player(defender_char)
    
    # 添加到游戏
    game.players = [attacker, defender]
    game.current_player_index = 0
    game.current_phase = "test"  # 设置为测试模式
    
    return game, attacker, defender

def test_shunshou_with_hand_cards():
    """测试顺手牵羊获得手牌"""
    print("=== 测试顺手牵羊获得手牌 ===")
    
    game, attacker, defender = create_test_game()
    
    # 给攻击者顺手牵羊
    shunshou_card = Card("顺手牵羊", "trick", "黑桃", 3)
    attacker.hand_cards.append(shunshou_card)
    
    # 给防御者手牌
    shan_card = Card("闪", "basic", "红桃", 2)
    sha_card = Card("杀", "basic", "黑桃", 7)
    defender.hand_cards.extend([shan_card, sha_card])
    
    print(f"初始状态：")
    print(f"攻击者手牌: {[card.name for card in attacker.hand_cards]}")
    print(f"防御者手牌: {[card.name for card in defender.hand_cards]}")
    
    # 创建顺手牵羊动作
    shunshou_action = ShunShouQianYangAction()
    
    # 执行顺手牵羊（测试模式，自动选择）
    result = shunshou_action.apply_effect(game, attacker, defender)
    
    print(f"结果：")
    print(f"顺手牵羊结果: {'成功' if result else '失败'}")
    print(f"攻击者手牌: {[card.name for card in attacker.hand_cards]}")
    print(f"防御者手牌: {[card.name for card in defender.hand_cards]}")
    
    # 验证结果
    assert result == True, "顺手牵羊应该成功"
    assert len(attacker.hand_cards) == 2, "攻击者应该有2张牌（原来1张+获得1张）"
    assert len(defender.hand_cards) == 1, "防御者应该剩余1张牌"
    
    print("✓ 手牌测试通过\n")
    return True

def test_shunshou_with_equipment():
    """测试顺手牵羊获得装备牌"""
    print("=== 测试顺手牵羊获得装备牌 ===")
    
    game, attacker, defender = create_test_game()
    
    # 给攻击者顺手牵羊
    shunshou_card = Card("顺手牵羊", "trick", "黑桃", 3)
    attacker.hand_cards.append(shunshou_card)
    
    # 给防御者装备牌
    weapon_card = Card("青龙偃月刀", "equipment", "黑桃", 5)
    defender._equip_card(weapon_card)
    
    print(f"初始状态：")
    print(f"攻击者手牌: {[card.name for card in attacker.hand_cards]}")
    print(f"防御者装备: {[card.name for card in defender.equipped]}")
    
    # 创建顺手牵羊动作
    shunshou_action = ShunShouQianYangAction()
    
    # 执行顺手牵羊（测试模式，自动选择）
    result = shunshou_action.apply_effect(game, attacker, defender)
    
    print(f"结果：")
    print(f"顺手牵羊结果: {'成功' if result else '失败'}")
    print(f"攻击者手牌: {[card.name for card in attacker.hand_cards]}")
    print(f"防御者装备: {[card.name for card in defender.equipped]}")
    
    # 验证结果
    assert result == True, "顺手牵羊应该成功"
    assert len(attacker.hand_cards) == 2, "攻击者应该有2张牌（原来1张+获得1张）"
    assert len(defender.equipped) == 0, "防御者装备应该被拿走"
    
    print("✓ 装备牌测试通过\n")
    return True

def test_shunshou_with_judgment():
    """测试顺手牵羊获得判定牌"""
    print("=== 测试顺手牵羊获得判定牌 ===")
    
    game, attacker, defender = create_test_game()
    
    # 给攻击者顺手牵羊
    shunshou_card = Card("顺手牵羊", "trick", "黑桃", 3)
    attacker.hand_cards.append(shunshou_card)
    
    # 给防御者判定牌
    judgment_card = Card("乐不思蜀", "trick", "红桃", 6)
    defender.judgment_area.append(judgment_card)
    
    print(f"初始状态：")
    print(f"攻击者手牌: {[card.name for card in attacker.hand_cards]}")
    print(f"防御者判定区: {[card.name for card in defender.judgment_area]}")
    
    # 创建顺手牵羊动作
    shunshou_action = ShunShouQianYangAction()
    
    # 执行顺手牵羊（测试模式，自动选择）
    result = shunshou_action.apply_effect(game, attacker, defender)
    
    print(f"结果：")
    print(f"顺手牵羊结果: {'成功' if result else '失败'}")
    print(f"攻击者手牌: {[card.name for card in attacker.hand_cards]}")
    print(f"防御者判定区: {[card.name for card in defender.judgment_area]}")
    
    # 验证结果
    assert result == True, "顺手牵羊应该成功"
    assert len(attacker.hand_cards) == 2, "攻击者应该有2张牌（原来1张+获得1张）"
    assert len(defender.judgment_area) == 0, "防御者判定区应该被拿走"
    
    print("✓ 判定牌测试通过\n")
    return True

def test_shunshou_no_cards():
    """测试顺手牵羊对没有牌的目标"""
    print("=== 测试顺手牵羊对没有牌的目标 ===")
    
    game, attacker, defender = create_test_game()
    
    # 给攻击者顺手牵羊
    shunshou_card = Card("顺手牵羊", "trick", "黑桃", 3)
    attacker.hand_cards.append(shunshou_card)
    
    # 防御者没有任何牌
    
    print(f"初始状态：")
    print(f"攻击者手牌: {[card.name for card in attacker.hand_cards]}")
    print(f"防御者手牌: {len(defender.hand_cards)}张")
    print(f"防御者装备: {len(defender.equipped)}张")
    print(f"防御者判定区: {len(defender.judgment_area)}张")
    
    # 创建顺手牵羊动作
    shunshou_action = ShunShouQianYangAction()
    
    # 执行顺手牵羊（测试模式，自动选择）
    result = shunshou_action.apply_effect(game, attacker, defender)
    
    print(f"结果：")
    print(f"顺手牵羊结果: {'成功' if result else '失败'}")
    print(f"攻击者手牌: {[card.name for card in attacker.hand_cards]}")
    
    # 验证结果
    assert result == True, "顺手牵羊应该成功（即使没有获得牌）"
    assert len(attacker.hand_cards) == 1, "攻击者手牌数量不变（没有获得牌）"
    
    print("✓ 无牌目标测试通过\n")
    return True

def main():
    print("=== 顺手牵羊自动化测试 ===")
    print("测试顺手牵羊的新选择逻辑在测试模式下的工作情况\n")
    
    try:
        test_shunshou_with_hand_cards()
        test_shunshou_with_equipment()
        test_shunshou_with_judgment()
        test_shunshou_no_cards()
        
        print("🎉 所有测试通过！")
        print("顺手牵羊的新交互逻辑工作正常")
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        return False
    
    return True

if __name__ == "__main__":
    main()