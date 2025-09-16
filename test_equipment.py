#!/usr/bin/env python3
"""
测试装备系统功能
"""

from app.models.player import Player
from app.models.character import Character
from app.models.card import Card, CardType
from app.models.card_actions import ShaAction, create_card_action
from app.core.game import Game

def test_equipment_system():
    print("=== 测试装备系统功能 ===")
    
    # 创建测试角色和玩家
    from app.models.character import Kingdom
    cao_cao = Character("曹操", Kingdom.WEI, 4, ["奸雄"])
    sima_yi = Character("司马懿", Kingdom.WEI, 3, ["反馈", "鬼才"])
    
    player1 = Player(cao_cao)
    player2 = Player(sima_yi)
    
    # 创建装备卡牌
    qinglong = Card("青龙偃月刀", type=CardType.EQUIP, suit="红桃", point=11)
    bagua = Card("八卦阵", type=CardType.EQUIP, suit="梅花", point=12)
    chitu = Card("赤兔", type=CardType.EQUIP, suit="方片", point=13)
    jueying = Card("绝影", type=CardType.EQUIP, suit="黑桃", point=13)
    sha_card = Card("杀", type=CardType.BASIC, suit="方片", point=8)
    shan_card = Card("闪", type=CardType.BASIC, suit="红桃", point=2)
    
    # 测试1: 基础攻击范围
    print("\n1. 测试基础攻击范围:")
    print(f"玩家1基础攻击范围: {player1.get_attack_range()}")
    print(f"玩家1到玩家2的距离: {player1.get_distance_to(player2)}")
    print(f"玩家1能否攻击玩家2: {player1.can_attack(player2)}")
    
    # 测试2: 装备青龙偃月刀
    print("\n2. 测试装备青龙偃月刀:")
    player1.hand_cards.append(qinglong)
    player1.use_card(qinglong)
    print(f"装备青龙偃月刀后攻击范围: {player1.get_attack_range()}")
    print(f"是否装备了青龙偃月刀: {player1.has_weapon_effect('青龙偃月刀')}")
    
    # 测试3: 装备八卦阵
    print("\n3. 测试装备八卦阵:")
    player2.hand_cards.append(bagua)
    player2.use_card(bagua)
    print(f"是否装备了八卦阵: {player2.has_defense_equipment('八卦阵')}")
    
    # 测试4: 装备马匹
    print("\n4. 测试装备马匹:")
    player1.hand_cards.append(chitu)
    player1.use_card(chitu)  # 进攻马
    player2.hand_cards.append(jueying)
    player2.use_card(jueying)  # 防御马
    
    print(f"装备马匹后，玩家1到玩家2的距离: {player1.get_distance_to(player2)}")
    print(f"玩家1能否攻击玩家2: {player1.can_attack(player2)}")
    
    # 测试5: 八卦阵判定
    print("\n5. 测试八卦阵判定:")
    for i in range(3):
        print(f"第{i+1}次判定:")
        result = player2.can_dodge_with_bagua()
        print(f"判定结果: {'成功' if result else '失败'}")
    
    # 测试6: 杀的攻击范围检查
    print("\n6. 测试杀的攻击范围检查:")
    sha_action = ShaAction()
    player1.hand_cards.append(sha_card)
    
    # 创建简化的游戏对象用于测试
    class MockGame:
        def get_opponent(self, player):
            return player2 if player == player1 else player1
    
    mock_game = MockGame()
    
    print(f"使用杀前检查攻击范围...")
    can_use = sha_action.apply_effect(mock_game, player1)
    print(f"能否使用杀: {can_use}")
    
    print("\n=== 装备系统测试完成 ===")

if __name__ == "__main__":
    test_equipment_system()