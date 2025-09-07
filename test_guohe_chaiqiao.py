#!/usr/bin/env python3
"""
测试过河拆桥被无懈可击响应的功能
"""
import sys
import os
import random

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.models.game import Game, Character, Card, CardType

def test_guohe_chaiqiao_with_wuxie():
    """测试过河拆桥被无懈可击响应的情况"""
    print("=== 测试过河拆桥被无懈可击响应 ===")
    
    # 创建游戏实例
    game = Game()
    
    # 创建武将
    caocao = Character("曹操", "魏", 4, ["奸雄"])
    liubei = Character("刘备", "蜀", 4, ["仁德"])
    
    # 添加玩家
    game.add_player(caocao)
    game.add_player(liubei)
    
    # 初始化牌堆
    game.initialize_deck()
    
    # 给玩家发牌
    for player in game.players:
        player.draw_card(game.deck, 4)
    
    print("\n初始手牌:")
    for i, player in enumerate(game.players):
        print(f"{player.character.name}: {[card.name for card in player.hand_cards]}")
    
    # 给曹操过河拆桥
    guohe_card = Card("过河拆桥", CardType.TRICK, "♠", 3)
    game.players[0].hand_cards.append(guohe_card)
    
    # 给刘备无懈可击
    wuxie_card = Card("无懈可击", CardType.TRICK, "♠", 8)
    game.players[1].hand_cards.append(wuxie_card)
    
    print(f"\n曹操 获得了 过河拆桥")
    print(f"刘备 获得了 无懈可击")
    print(f"曹操 手牌: {[card.name for card in game.players[0].hand_cards]}")
    print(f"刘备 手牌: {[card.name for card in game.players[1].hand_cards]}")
    
    # 测试过河拆桥被无懈可击响应
    print(f"\n=== 测试过河拆桥被无懈可击响应 ===")
    
    # 使用过河拆桥
    card_index = len(game.players[0].hand_cards) - 1
    used_card = game.players[0].play_card(card_index)
    
    if used_card:
        card_action = game.create_card_action(used_card)
        
        # 处理响应
        result = card_action.handle_response(game, game.players[0])
        
        print(f"过河拆桥响应结果: {result}")
        
        if result == False:
            print("过河拆桥被无懈可击取消，曹操的出牌阶段应该继续。")
        else:
            print("过河拆桥生效，刘备被弃置一张手牌。")
    
    print(f"\n最终手牌:")
    print(f"曹操: {[card.name for card in game.players[0].hand_cards]}")
    print(f"刘备: {[card.name for card in game.players[1].hand_cards]}")

def test_guohe_chaiqiao_without_wuxie():
    """测试过河拆桥没有被无懈可击响应的情况"""
    print("\n=== 测试过河拆桥没有被无懈可击响应 ===")
    
    # 创建游戏实例
    game = Game()
    
    # 创建武将
    caocao = Character("曹操", "魏", 4, ["奸雄"])
    liubei = Character("刘备", "蜀", 4, ["仁德"])
    
    # 添加玩家
    game.add_player(caocao)
    game.add_player(liubei)
    
    # 初始化牌堆
    game.initialize_deck()
    
    # 给玩家发牌
    for player in game.players:
        player.draw_card(game.deck, 4)
    
    print("\n初始手牌:")
    for i, player in enumerate(game.players):
        print(f"{player.character.name}: {[card.name for card in player.hand_cards]}")
    
    # 给曹操过河拆桥
    guohe_card = Card("过河拆桥", CardType.TRICK, "♠", 3)
    game.players[0].hand_cards.append(guohe_card)
    
    # 刘备没有无懈可击
    print(f"\n曹操 获得了 过河拆桥")
    print(f"刘备 没有无懈可击")
    print(f"曹操 手牌: {[card.name for card in game.players[0].hand_cards]}")
    print(f"刘备 手牌: {[card.name for card in game.players[1].hand_cards]}")
    
    # 测试过河拆桥没有被响应
    print(f"\n=== 测试过河拆桥没有被响应 ===")
    
    # 使用过河拆桥
    card_index = len(game.players[0].hand_cards) - 1
    used_card = game.players[0].play_card(card_index)
    
    if used_card:
        card_action = game.create_card_action(used_card)
        
        # 处理响应
        result = card_action.handle_response(game, game.players[0])
        
        print(f"过河拆桥响应结果: {result}")
        
        if result == False:
            print("过河拆桥被无懈可击取消，曹操的出牌阶段应该继续。")
        else:
            print("过河拆桥生效，刘备被弃置一张手牌。")
    
    print(f"\n最终手牌:")
    print(f"曹操: {[card.name for card in game.players[0].hand_cards]}")
    print(f"刘备: {[card.name for card in game.players[1].hand_cards]}")

if __name__ == "__main__":
    test_guohe_chaiqiao_with_wuxie()
    test_guohe_chaiqiao_without_wuxie()