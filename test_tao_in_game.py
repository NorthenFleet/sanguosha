#!/usr/bin/env python3
"""
测试桃在游戏流程中的实际使用
"""
import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.models.game import Game, Card, CardType
from app.models.character import CharacterFactory

def test_tao_in_game_flow():
    """测试桃在游戏流程中的使用"""
    print("=== 测试桃在游戏流程中的使用 ===")
    
    # 创建游戏实例
    game = Game()
    
    # 创建两个角色
    character1 = CharacterFactory.create_character("曹操")
    character2 = CharacterFactory.create_character("刘备")
    
    # 添加玩家
    game.add_player(character1)
    game.add_player(character2)
    
    player1 = game.players[0]
    player2 = game.players[1]
    
    # 设置测试模式
    game.test_mode = True
    
    # 清空手牌，只给玩家1一张桃
    player1.hand_cards = []
    player2.hand_cards = []
    
    tao_card = Card("桃", CardType.BASIC, "♥", 1)
    player1.hand_cards.append(tao_card)
    
    # 让玩家1受到1点伤害
    player1.character.hp = 2
    print(f"初始状态: {player1.character.name} 血量: {player1.character.hp}/4")
    print(f"初始状态: {player2.character.name} 血量: {player2.character.hp}/4")
    
    # 模拟游戏流程：玩家1使用桃
    print(f"\n{player1.character.name} 使用桃...")
    
    # 使用handle_response方法来模拟游戏中的实际调用
    result = game.handle_response(player1, tao_card, test_mode=True)
    print(f"桃使用结果: {result}")
    
    # 验证血量恢复
    print(f"使用后状态: {player1.character.name} 血量: {player1.character.hp}/4")
    
    if player1.character.hp == 3:
        print("✅ 测试通过: 桃在游戏流程中成功恢复1点血量")
    else:
        print(f"❌ 测试失败: 期望血量3，实际血量{player1.character.hp}")

def test_tao_full_hp():
    """测试血量已满时使用桃"""
    print("\n=== 测试血量已满时使用桃 ===")
    
    # 创建游戏实例
    game = Game()
    
    # 创建角色
    character1 = CharacterFactory.create_character("曹操")
    
    # 添加玩家
    game.add_player(character1)
    
    player1 = game.players[0]
    
    # 设置测试模式
    game.test_mode = True
    
    # 清空手牌，只给玩家一张桃
    player1.hand_cards = []
    
    tao_card = Card("桃", CardType.BASIC, "♥", 1)
    player1.hand_cards.append(tao_card)
    
    # 玩家血量已满
    player1.character.hp = 4
    print(f"初始状态: {player1.character.name} 血量: {player1.character.hp}/4")
    
    # 使用桃
    print(f"\n{player1.character.name} 使用桃...")
    result = game.handle_response(player1, tao_card, test_mode=True)
    print(f"桃使用结果: {result}")
    
    # 验证血量未变化
    print(f"使用后状态: {player1.character.name} 血量: {player1.character.hp}/4")
    
    if player1.character.hp == 4 and result == False:
        print("✅ 测试通过: 血量已满时无法使用桃")
    else:
        print(f"❌ 测试失败: 期望血量4且返回False，实际血量{player1.character.hp}，返回{result}")

if __name__ == "__main__":
    test_tao_in_game_flow()
    test_tao_full_hp()