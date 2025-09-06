#!/usr/bin/env python3
"""
测试桃不需要对方响应的功能
"""
import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.models.game import Game, Card, CardType
from app.models.character import CharacterFactory

def test_tao_no_response():
    """测试桃不需要对方响应"""
    print("=== 测试桃不需要对方响应 ===")
    
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
    player1.character.hp = 3
    print(f"初始状态: {player1.character.name} 血量: {player1.character.hp}/4")
    print(f"初始状态: {player2.character.name} 血量: {player2.character.hp}/4")
    
    # 玩家1使用桃
    print(f"\n{player1.character.name} 使用桃...")
    
    # 创建桃动作实例
    card_action = game.create_card_action(tao_card)
    
    # 检查是否需要响应
    response_cards = card_action.get_response_cards(player2)
    print(f"可以响应的卡牌: {response_cards}")
    
    if not response_cards:
        print("桃不需要对方响应，直接生效")
        
        # 执行桃的效果
        result = card_action.apply_effect(game, player1)
        print(f"桃使用结果: {result}")
        
        # 验证血量恢复
        print(f"使用后状态: {player1.character.name} 血量: {player1.character.hp}/4")
        
        if player1.character.hp == 4:
            print("✅ 测试通过: 桃成功恢复1点血量，不需要对方响应")
        else:
            print("❌ 测试失败: 桃未能正确恢复血量")
    else:
        print("❌ 测试失败: 桃需要对方响应")

if __name__ == "__main__":
    test_tao_no_response()