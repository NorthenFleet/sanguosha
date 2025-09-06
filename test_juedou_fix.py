#!/usr/bin/env python3
"""
测试决斗卡牌的正确实现
"""
import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.models.game import Game, Card, CardType
from app.models.character import CharacterFactory

def test_juedou_both_have_sha():
    """测试双方都有杀的情况"""
    print("=== 测试双方都有杀的情况 ===")
    
    # 创建游戏实例
    game = Game()
    
    # 创建两个角色
    character1 = CharacterFactory.create_character("张辽")
    character2 = CharacterFactory.create_character("曹操")
    
    # 添加玩家
    game.add_player(character1)
    game.add_player(character2)
    
    player1 = game.players[0]
    player2 = game.players[1]
    
    # 设置测试模式
    game.test_mode = True
    
    # 清空手牌，给双方都添加杀
    player1.hand_cards = []
    player2.hand_cards = []
    
    # 给双方都添加足够的杀（至少3张，因为可能需要交替出杀多次）
    sha_cards = [
        Card("杀", CardType.BASIC, "♥", 1),
        Card("杀", CardType.BASIC, "♠", 2),
        Card("杀", CardType.BASIC, "♣", 3),
        Card("杀", CardType.BASIC, "♦", 4)
    ]
    
    # 给双方都添加3张杀（创建独立的卡牌对象）
    player1.hand_cards.extend([
        Card("杀", CardType.BASIC, "♥", 1),
        Card("杀", CardType.BASIC, "♠", 2), 
        Card("杀", CardType.BASIC, "♣", 3)
    ])  # 发起方有3张杀
    player2.hand_cards.extend([
        Card("杀", CardType.BASIC, "♦", 4),
        Card("杀", CardType.BASIC, "♥", 5),
        Card("杀", CardType.BASIC, "♠", 6)
    ])  # 响应方有3张杀
    
    # 设置初始血量
    player1.character.hp = 4
    player2.character.hp = 4
    print(f"初始状态: {player1.character.name} 血量: {player1.character.hp}/4")
    print(f"初始状态: {player2.character.name} 血量: {player2.character.hp}/4")
    
    # 创建决斗卡牌动作
    juedou_card = Card("决斗", CardType.TRICK, "♣", 10)
    juedou_action = game.create_card_action(juedou_card)
    
    # 处理决斗响应
    print(f"\n{player1.character.name} 使用决斗...")
    result = juedou_action.handle_response(game, player1)
    
    print(f"决斗结果: {result}")
    print(f"最终状态: {player1.character.name} 血量: {player1.character.hp}/4")
    print(f"最终状态: {player2.character.name} 血量: {player2.character.hp}/4")
    
    # 验证：双方各有3张杀，理论上可以交替出杀6次
    # 决斗流程：张辽使用决斗 → 曹操出杀（第1次）→ 张辽出杀（第2次）→ 曹操出杀（第3次）→ 张辽出杀（第4次）→ 曹操出杀（第5次）→ 张辽出杀（第6次）
    # 此时曹操手牌已空，轮到曹操出杀时无法响应，受到伤害
    if player1.character.hp == 4 and player2.character.hp == 3:
        print("✅ 测试通过: 双方都有杀，曹操先耗尽手牌而受到伤害")
    else:
        print(f"❌ 测试失败: 期望 张辽:4, 曹操:3，实际 {player1.character.name}:{player1.character.hp}, {player2.character.name}:{player2.character.hp}")

def test_juedou_responder_no_sha():
    """测试响应方没有杀的情况"""
    print("\n=== 测试响应方没有杀的情况 ===")
    
    # 创建游戏实例
    game = Game()
    
    # 创建两个角色
    character1 = CharacterFactory.create_character("张辽")
    character2 = CharacterFactory.create_character("曹操")
    
    # 添加玩家
    game.add_player(character1)
    game.add_player(character2)
    
    player1 = game.players[0]
    player2 = game.players[1]
    
    # 设置测试模式
    game.test_mode = True
    
    # 清空手牌
    player1.hand_cards = []
    player2.hand_cards = []
    
    # 只有发起方有杀，响应方没有杀
    sha_card = Card("杀", CardType.BASIC, "♥", 1)
    player1.hand_cards.append(sha_card)
    
    # 给响应方一张闪，而不是杀
    shan_card = Card("闪", CardType.BASIC, "♦", 2)
    player2.hand_cards.append(shan_card)
    
    # 设置初始血量
    player1.character.hp = 4
    player2.character.hp = 4
    print(f"初始状态: {player1.character.name} 血量: {player1.character.hp}/4")
    print(f"初始状态: {player2.character.name} 血量: {player2.character.hp}/4")
    
    # 创建决斗卡牌动作
    juedou_card = Card("决斗", CardType.TRICK, "♣", 10)
    juedou_action = game.create_card_action(juedou_card)
    
    # 处理决斗响应
    print(f"\n{player1.character.name} 使用决斗...")
    result = juedou_action.handle_response(game, player1)
    
    print(f"决斗结果: {result}")
    print(f"最终状态: {player1.character.name} 血量: {player1.character.hp}/4")
    print(f"最终状态: {player2.character.name} 血量: {player2.character.hp}/4")
    
    # 验证：响应方没有杀，应该受到伤害
    if player1.character.hp == 4 and player2.character.hp == 3:
        print("✅ 测试通过: 响应方没有杀，受到1点伤害")
    else:
        print(f"❌ 测试失败: 期望 {player1.character.name}:4, {player2.character.name}:3，实际 {player1.character.name}:{player1.character.hp}, {player2.character.name}:{player2.character.hp}")

def test_juedou_initiator_no_sha():
    """测试发起方在后续回合没有杀的情况"""
    print("\n=== 测试发起方在后续回合没有杀的情况 ===")
    
    # 创建游戏实例
    game = Game()
    
    # 创建两个角色
    character1 = CharacterFactory.create_character("张辽")
    character2 = CharacterFactory.create_character("曹操")
    
    # 添加玩家
    game.add_player(character1)
    game.add_player(character2)
    
    player1 = game.players[0]
    player2 = game.players[1]
    
    # 设置测试模式
    game.test_mode = True
    
    # 清空手牌
    player1.hand_cards = []
    player2.hand_cards = []
    
    # 响应方有杀，发起方没有杀（在后续回合）
    sha_card = Card("杀", CardType.BASIC, "♥", 1)
    player2.hand_cards.append(sha_card)
    
    # 设置初始血量
    player1.character.hp = 4
    player2.character.hp = 4
    print(f"初始状态: {player1.character.name} 血量: {player1.character.hp}/4")
    print(f"初始状态: {player2.character.name} 血量: {player2.character.hp}/4")
    
    # 创建决斗卡牌动作
    juedou_card = Card("决斗", CardType.TRICK, "♣", 10)
    juedou_action = game.create_card_action(juedou_card)
    
    # 处理决斗响应
    print(f"\n{player1.character.name} 使用决斗...")
    result = juedou_action.handle_response(game, player1)
    
    print(f"决斗结果: {result}")
    print(f"最终状态: {player1.character.name} 血量: {player1.character.hp}/4")
    print(f"最终状态: {player2.character.name} 血量: {player2.character.hp}/4")
    
    # 验证：发起方在后续回合没有杀，应该受到伤害
    if player1.character.hp == 3 and player2.character.hp == 4:
        print("✅ 测试通过: 发起方在后续回合没有杀，受到1点伤害")
    else:
        print(f"❌ 测试失败: 期望 {player1.character.name}:3, {player2.character.name}:4，实际 {player1.character.name}:{player1.character.hp}, {player2.character.name}:{player2.character.hp}")

if __name__ == "__main__":
    test_juedou_both_have_sha()
    test_juedou_responder_no_sha()
    test_juedou_initiator_no_sha()