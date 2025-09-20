#!/usr/bin/env python3
"""
装备牌距离判定系统测试
测试多人游戏中的座位距离计算、进攻马/防御马影响、攻击范围判定等功能
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.models.player import Player
from app.models.character import Character, Kingdom
from app.models.card import Card

def create_test_card(name, card_type="装备", suit="红桃", point=1):
    """创建测试卡牌"""
    return Card(name=name, card_type=card_type, suit=suit, point=point)

def test_seat_distance_calculation():
    """测试座位距离计算"""
    print("=== 测试座位距离计算 ===")
    
    # 创建5个玩家
    characters = ["刘备", "关羽", "张飞", "曹操", "孙权"]
    players = []
    
    for i, char_name in enumerate(characters):
        character = Character(char_name, Kingdom.SHU, 4, [])
        player = Player(character)
        player.position = i
        players.append(player)
    
    # 测试各种座位距离
    test_cases = [
        (0, 1, 1),  # 相邻玩家
        (0, 2, 2),  # 间隔一个玩家
        (0, 3, 2),  # 间隔两个玩家（逆时针更近）
        (0, 4, 1),  # 间隔三个玩家（逆时针更近）
        (1, 3, 2),  # 其他组合
        (2, 4, 2),  # 其他组合
    ]
    
    for from_idx, to_idx, expected_distance in test_cases:
        from_player = players[from_idx]
        to_player = players[to_idx]
        actual_distance = from_player._calculate_seat_distance(to_player, players)
        
        print(f"玩家{from_idx}({from_player.character.name}) -> 玩家{to_idx}({to_player.character.name}): "
              f"期望距离={expected_distance}, 实际距离={actual_distance}, "
              f"{'✓' if actual_distance == expected_distance else '✗'}")
    
    print()

def test_equipment_distance_modification():
    """测试装备对距离的影响"""
    print("=== 测试装备对距离的影响 ===")
    
    # 创建3个玩家
    characters = ["刘备", "关羽", "张飞"]
    players = []
    
    for i, char_name in enumerate(characters):
        character = Character(char_name, Kingdom.SHU, 4, [])
        player = Player(character)
        player.position = i
        players.append(player)
    
    player1, player2, player3 = players
    
    # 基础距离测试
    base_distance = player1.get_distance_to(player2, players)
    print(f"基础距离 {player1.character.name} -> {player2.character.name}: {base_distance}")
    
    # 装备进攻马测试
    player1.attack_horse = create_test_card("赤兔")
    distance_with_attack_horse = player1.get_distance_to(player2, players)
    print(f"装备进攻马后 {player1.character.name} -> {player2.character.name}: {distance_with_attack_horse} (减少1)")
    
    # 装备防御马测试
    player2.defense_horse = create_test_card("的卢")
    distance_with_defense_horse = player1.get_distance_to(player2, players)
    print(f"目标装备防御马后 {player1.character.name} -> {player2.character.name}: {distance_with_defense_horse} (增加1)")
    
    # 测试距离最小为1
    player1.attack_horse = create_test_card("赤兔")
    player2.defense_horse = None
    distance_min = player1.get_distance_to(player2, players)
    print(f"距离最小值测试 {player1.character.name} -> {player2.character.name}: {distance_min} (最小为1)")
    
    print()

def test_attack_range_judgment():
    """测试攻击范围判定"""
    print("=== 测试攻击范围判定 ===")
    
    # 创建4个玩家
    characters = ["刘备", "关羽", "张飞", "曹操"]
    players = []
    
    for i, char_name in enumerate(characters):
        character = Character(char_name, Kingdom.SHU, 4, [])
        player = Player(character)
        player.position = i
        players.append(player)
    
    attacker = players[0]
    targets = players[1:]
    
    # 基础攻击范围测试（范围1）
    print("基础攻击范围测试（范围1）:")
    for target in targets:
        can_attack = attacker.can_attack(target, players)
        distance = attacker.get_distance_to(target, players)
        print(f"  {attacker.character.name} -> {target.character.name}: "
              f"距离={distance}, 可攻击={can_attack}")
    
    # 装备武器测试（青龙偃月刀，范围3）
    print("\n装备青龙偃月刀测试（范围3）:")
    attacker.weapon = create_test_card("青龙偃月刀")
    for target in targets:
        can_attack = attacker.can_attack(target, players)
        distance = attacker.get_distance_to(target, players)
        attack_range = attacker.get_attack_range()
        print(f"  {attacker.character.name} -> {target.character.name}: "
              f"距离={distance}, 攻击范围={attack_range}, 可攻击={can_attack}")
    
    print()

def test_card_usage_judgment():
    """测试使用牌的距离判定"""
    print("=== 测试使用牌的距离判定 ===")
    
    # 创建4个玩家
    characters = ["刘备", "关羽", "张飞", "曹操"]
    players = []
    
    for i, char_name in enumerate(characters):
        character = Character(char_name, Kingdom.SHU, 4, [])
        player = Player(character)
        player.position = i
        players.append(player)
    
    user = players[0]
    
    # 测试对不同距离的目标使用杀
    print("测试使用杀的距离判定:")
    for i, target in enumerate(players[1:], 1):
        print(f"\n对玩家{i}使用杀:")
        can_use = user.can_use_card_on_target(target, "杀", players)
    
    # 装备武器后再测试
    print("\n装备青龙偃月刀后:")
    user.weapon = create_test_card("青龙偃月刀")
    for i, target in enumerate(players[1:], 1):
        print(f"\n对玩家{i}使用杀:")
        can_use = user.can_use_card_on_target(target, "杀", players)
    
    print()

def test_complex_scenarios():
    """测试复杂场景"""
    print("=== 测试复杂场景 ===")
    
    # 创建6个玩家的游戏
    characters = ["刘备", "关羽", "张飞", "曹操", "孙权", "周瑜"]
    players = []
    
    for i, char_name in enumerate(characters):
        character = Character(char_name, Kingdom.SHU if i < 3 else Kingdom.WEI, 4, [])
        player = Player(character)
        player.position = i
        players.append(player)
    
    # 设置复杂装备情况
    players[0].weapon = create_test_card("方天画戟")  # 攻击范围4
    players[0].attack_horse = create_test_card("赤兔")  # 进攻马-1
    players[3].defense_horse = create_test_card("的卢")  # 防御马+1
    players[5].defense_horse = create_test_card("绝影")  # 防御马+1
    
    attacker = players[0]
    
    print(f"{attacker.character.name}的装备:")
    print(f"  武器: {attacker.weapon.name if attacker.weapon else '无'} (攻击范围: {attacker.get_attack_range()})")
    print(f"  进攻马: {attacker.attack_horse.name if attacker.attack_horse else '无'}")
    
    print(f"\n距离判定结果:")
    for i, target in enumerate(players[1:], 1):
        distance = attacker.get_distance_to(target, players)
        can_attack = attacker.can_attack(target, players)
        
        equipment_info = []
        if target.defense_horse:
            equipment_info.append(f"防御马:{target.defense_horse.name}")
        equipment_str = f" ({', '.join(equipment_info)})" if equipment_info else ""
        
        print(f"  -> 玩家{i}({target.character.name}){equipment_str}: "
              f"距离={distance}, 可攻击={can_attack}")
    
    print()

def main():
    """主测试函数"""
    print("装备牌距离判定系统测试")
    print("=" * 50)
    
    test_seat_distance_calculation()
    test_equipment_distance_modification()
    test_attack_range_judgment()
    test_card_usage_judgment()
    test_complex_scenarios()
    
    print("所有测试完成！")

if __name__ == "__main__":
    main()