#!/usr/bin/env python3
"""
测试杀只造成1点伤害的修复
"""
import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.models.game import Game, Card, CardType
from app.models.character import CharacterFactory

def test_sha_damage_fix():
    """测试杀只造成1点伤害"""
    print("=== 测试杀只造成1点伤害 ===")
    
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
    
    # 清空手牌，只给玩家1一张杀
    player1.hand_cards = []
    player2.hand_cards = []
    
    sha_card = Card("杀", CardType.BASIC, "♥", 1)
    player1.hand_cards.append(sha_card)
    
    # 设置初始血量
    player2.character.hp = 4
    print(f"初始状态: {player1.character.name} 血量: {player1.character.hp}/4")
    print(f"初始状态: {player2.character.name} 血量: {player2.character.hp}/4")
    
    # 玩家1使用杀
    print(f"\n{player1.character.name} 使用杀...")
    
    # 使用handle_response方法来模拟游戏中的实际调用
    result = game.handle_response(player1, sha_card, test_mode=True)
    print(f"杀使用结果: {result}")
    
    # 验证血量减少
    print(f"使用后状态: {player1.character.name} 血量: {player1.character.hp}/4")
    print(f"使用后状态: {player2.character.name} 血量: {player2.character.hp}/4")
    
    if player2.character.hp == 3:
        print("✅ 测试通过: 杀只造成1点伤害")
    else:
        print(f"❌ 测试失败: 期望血量3，实际血量{player2.character.hp}")

def test_sha_damage_multiple():
    """测试多次杀造成累计伤害"""
    print("\n=== 测试多次杀造成累计伤害 ===")
    
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
    
    # 清空手牌，给玩家1多张杀
    player1.hand_cards = []
    player2.hand_cards = []
    
    # 添加3张杀
    for _ in range(3):
        sha_card = Card("杀", CardType.BASIC, "♥", 1)
        player1.hand_cards.append(sha_card)
    
    # 设置初始血量
    player2.character.hp = 4
    print(f"初始状态: {player2.character.name} 血量: {player2.character.hp}/4")
    
    # 连续使用3次杀
    for i in range(3):
        sha_card = player1.hand_cards[0]  # 使用第一张杀
        print(f"\n第{i+1}次使用杀...")
        
        result = game.handle_response(player1, sha_card, test_mode=True)
        print(f"第{i+1}次杀使用结果: {result}")
        print(f"第{i+1}次杀后血量: {player2.character.hp}/4")
        
        # 移除已使用的杀
        player1.hand_cards.pop(0)
    
    if player2.character.hp == 1:
        print("✅ 测试通过: 多次杀造成累计伤害正确")
    else:
        print(f"❌ 测试失败: 期望血量1，实际血量{player2.character.hp}")

if __name__ == "__main__":
    test_sha_damage_fix()
    test_sha_damage_multiple()