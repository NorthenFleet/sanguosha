#!/usr/bin/env python3
"""
测试顺手牵羊卡牌功能
1. 测试顺手牵羊被无懈可击响应后出牌阶段继续
2. 测试顺手牵羊未被响应时正常获得对方手牌
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from models.game import Game
from models.character import Character
from models.deck import Deck

def test_shunshou_qianyang_with_wuxie():
    """测试顺手牵羊被无懈可击响应"""
    print("=== 测试1: 顺手牵羊被无懈可击响应 ===")
    
    # 创建游戏和武将
    game = Game()
    caocao = Character("曹操", "魏", 4, [])
    liubei = Character("刘备", "蜀", 4, [])
    
    game.add_player(caocao)
    game.add_player(liubei)
    
    # 初始化游戏
    game.start_game()
    
    # 清空手牌，添加测试卡牌
    game.players[0].hand_cards = []  # 曹操
    game.players[1].hand_cards = []  # 刘备
    
    # 给曹操添加顺手牵羊和杀
    from app.models.game import Card
    shunshou_card = Card("顺手牵羊", "trick", "♥", 1)
    sha_card = Card("杀", "basic", "♠", 1)
    game.players[0].hand_cards.extend([shunshou_card, sha_card])
    
    # 给刘备添加无懈可击
    wuxie_card = Card("无懈可击", "trick", "♠", 1)
    game.players[1].hand_cards.append(wuxie_card)
    
    print("初始手牌:")
    print(f"曹操手牌: {[c.name for c in game.players[0].hand_cards]}")
    print(f"刘备手牌: {[c.name for c in game.players[1].hand_cards]}")
    
    # 模拟出牌阶段
    print("\n--- 曹操的出牌阶段 ---")
    
    # 使用顺手牵羊
    print("曹操使用顺手牵羊...")
    result = game.handle_response(game.players[0], shunshou_card, test_mode=True)
    
    print(f"\n处理结果: {result}")
    
    # 检查结果
    if result == "continue_play_phase":
        print("✓ 顺手牵羊被无懈可击响应，出牌阶段继续")
        
        # 曹操可以继续使用杀
        print("曹操继续使用杀...")
        sha_result = game.handle_response(game.players[0], sha_card, test_mode=True)
        if sha_result:
            print("✓ 曹操成功使用杀，刘备受到1点伤害")
            print(f"刘备剩余血量: {game.players[1].character.hp}")
        else:
            print("✗ 杀使用失败")
    else:
        print("✗ 出牌阶段未继续")
    
    print(f"最终曹操手牌: {[c.name for c in game.players[0].hand_cards]}")
    print(f"最终刘备手牌: {[c.name for c in game.players[1].hand_cards]}")

def test_shunshou_qianyang_without_wuxie():
    """测试顺手牵羊未被响应"""
    print("\n=== 测试2: 顺手牵羊未被响应 ===")
    
    # 创建游戏和武将
    game = Game()
    caocao = Character("曹操", "魏", 4, [])
    liubei = Character("刘备", "蜀", 4, [])
    
    game.add_player(caocao)
    game.add_player(liubei)
    
    # 初始化游戏
    game.start_game()
    
    # 清空手牌，添加测试卡牌
    game.players[0].hand_cards = []  # 曹操
    game.players[1].hand_cards = []  # 刘备
    
    # 给曹操添加顺手牵羊
    from app.models.game import Card
    shunshou_card = Card("顺手牵羊", "trick", "♥", 1)
    game.players[0].hand_cards.append(shunshou_card)
    
    # 给刘备添加一张手牌（万箭齐发）
    from app.models.game import Card
    wanjian_card = Card("万箭齐发", "trick", "♠", 1)
    game.players[1].hand_cards.append(wanjian_card)
    
    print("初始手牌:")
    print(f"曹操手牌: {[c.name for c in game.players[0].hand_cards]}")
    print(f"刘备手牌: {[c.name for c in game.players[1].hand_cards]}")
    
    # 模拟出牌阶段
    print("\n--- 曹操的出牌阶段 ---")
    
    # 使用顺手牵羊
    print("曹操使用顺手牵羊...")
    result = game.handle_response(game.players[0], shunshou_card, test_mode=True)
    
    print(f"\n处理结果: {result}")
    
    # 检查结果
    if result == True:
        print("✓ 顺手牵羊成功执行")
        
        # 检查手牌变化
        caocao_has_wanjian = any(c.name == "万箭齐发" for c in game.players[0].hand_cards)
        liubei_has_wanjian = any(c.name == "万箭齐发" for c in game.players[1].hand_cards)
        
        if caocao_has_wanjian and not liubei_has_wanjian:
            print("✓ 曹操成功获得刘备的万箭齐发")
        else:
            print("✗ 手牌转移失败")
    else:
        print("✗ 顺手牵羊执行失败")
    
    print(f"最终曹操手牌: {[c.name for c in game.players[0].hand_cards]}")
    print(f"最终刘备手牌: {[c.name for c in game.players[1].hand_cards]}")

if __name__ == "__main__":
    print("开始测试顺手牵羊卡牌功能...")
    
    # 测试1: 顺手牵羊被无懈可击响应
    test_shunshou_qianyang_with_wuxie()
    
    # 测试2: 顺手牵羊未被响应
    test_shunshou_qianyang_without_wuxie()
    
    print("\n=== 测试完成 ===")