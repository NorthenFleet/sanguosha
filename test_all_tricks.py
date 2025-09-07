#!/usr/bin/env python3
"""
测试所有锦囊牌功能的脚本
"""
import sys
import os
import random

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.models.game import Game, Character, Card, CardType

def test_all_trick_cards():
    """测试所有锦囊牌功能"""
    print("=== 测试所有锦囊牌功能 ===")
    
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
    
    # 测试所有锦囊牌
    trick_cards = [
        ("过河拆桥", "弃置目标角色区域内的一张牌"),
        ("顺手牵羊", "获得目标角色区域内的一张牌"),
        ("无中生有", "摸两张牌"),
        ("决斗", "与目标角色进行决斗，对方必须连续使用杀"),
        ("南蛮入侵", "所有角色需要打出一张杀，否则受到1点伤害"),
        ("万箭齐发", "所有角色需要打出一张闪，否则受到1点伤害")
    ]
    
    for card_name, description in trick_cards:
        print(f"\n=== 测试 {card_name} ===")
        print(f"效果: {description}")
        
        # 创建锦囊牌
        trick_card = Card(card_name, CardType.TRICK, random.choice(["♥", "♦", "♠", "♣"]), random.randint(1, 13))
        game.players[0].hand_cards.append(trick_card)
        
        print(f"{game.players[0].character.name} 获得了 {card_name}")
        print(f"当前手牌: {[card.name for card in game.players[0].hand_cards]}")
        
        # 使用锦囊牌
        card_index = len(game.players[0].hand_cards) - 1
        used_card = game.players[0].play_card(card_index)
        
        if used_card:
            card_action = game.create_card_action(used_card)
            
            if card_name in ["决斗", "南蛮入侵", "万箭齐发"]:
                # 这些牌需要处理响应
                result = card_action.handle_response(game, game.players[0])
                print(f"{card_name} 结果: {result}")
            else:
                # 直接应用效果
                result = card_action.apply_effect(game, game.players[0])
                print(f"{card_name} 结果: {result}")
        
        print(f"{game.players[0].character.name} 血量: {game.players[0].character.hp}")
        print(f"{game.players[1].character.name} 血量: {game.players[1].character.hp}")
        print(f"{game.players[0].character.name} 手牌: {[card.name for card in game.players[0].hand_cards]}")
        print(f"{game.players[1].character.name} 手牌: {[card.name for card in game.players[1].hand_cards]}")
    
    print("\n=== 所有锦囊牌测试完成 ===")

def test_trick_card_in_game():
    """在游戏环境中测试锦囊牌"""
    print("\n=== 在游戏环境中测试锦囊牌 ===")
    
    # 创建游戏实例
    game = Game()
    
    # 创建武将
    caocao = Character("曹操", "魏", 4, ["奸雄"])
    liubei = Character("刘备", "蜀", 4, ["仁德"])
    
    # 添加玩家
    game.add_player(caocao)
    game.add_player(liubei)
    
    # 开始游戏
    game.start_game()
    
    # 手动给玩家一些锦囊牌
    from app.models.game import Card, CardType
    
    # 给曹操一些锦囊牌
    trick_cards_for_caocao = [
        Card("过河拆桥", CardType.TRICK, "♠", 7),
        Card("顺手牵羊", CardType.TRICK, "♥", 8),
        Card("无中生有", CardType.TRICK, "♦", 9)
    ]
    
    for card in trick_cards_for_caocao:
        game.players[0].hand_cards.append(card)
    
    # 给刘备一些响应牌
    response_cards_for_liubei = [
        Card("杀", CardType.BASIC, "♠", 10),
        Card("闪", CardType.BASIC, "♥", 11),
        Card("杀", CardType.BASIC, "♣", 12)
    ]
    
    for card in response_cards_for_liubei:
        game.players[1].hand_cards.append(card)
    
    print("\n游戏开始后的手牌:")
    print(f"曹操: {[card.name for card in game.players[0].hand_cards]}")
    print(f"刘备: {[card.name for card in game.players[1].hand_cards]}")
    
    print("\n=== 游戏环境测试完成 ===")

if __name__ == "__main__":
    test_all_trick_cards()
    test_trick_card_in_game()