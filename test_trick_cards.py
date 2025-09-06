#!/usr/bin/env python3
"""
测试锦囊牌功能的脚本
"""
import sys
import os
import random

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.models.game import Game, Character
from app.models.deck import Deck

def test_trick_cards():
    """测试锦囊牌功能"""
    print("=== 测试锦囊牌功能 ===")
    
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
    
    # 测试过河拆桥
    print("\n=== 测试过河拆桥 ===")
    # 手动创建过河拆桥卡牌
    from app.models.game import Card, CardType
    guohe_card = Card("过河拆桥", CardType.TRICK, "♠", 7)
    game.players[0].hand_cards.append(guohe_card)
    
    print(f"{game.players[0].character.name} 获得了 过河拆桥")
    print(f"当前手牌: {[card.name for card in game.players[0].hand_cards]}")
    
    # 使用过河拆桥
    card_index = len(game.players[0].hand_cards) - 1
    used_card = game.players[0].play_card(card_index)
    if used_card:
        card_action = game.create_card_action(used_card)
        card_action.apply_effect(game, game.players[0])
    
    print(f"{game.players[1].character.name} 剩余手牌: {[card.name for card in game.players[1].hand_cards]}")
    
    # 测试顺手牵羊
    print("\n=== 测试顺手牵羊 ===")
    shunshou_card = Card("顺手牵羊", CardType.TRICK, "♥", 8)
    game.players[0].hand_cards.append(shunshou_card)
    
    print(f"{game.players[0].character.name} 获得了 顺手牵羊")
    print(f"当前手牌: {[card.name for card in game.players[0].hand_cards]}")
    
    # 使用顺手牵羊
    card_index = len(game.players[0].hand_cards) - 1
    used_card = game.players[0].play_card(card_index)
    if used_card:
        card_action = game.create_card_action(used_card)
        card_action.apply_effect(game, game.players[0])
    
    print(f"{game.players[0].character.name} 手牌: {[card.name for card in game.players[0].hand_cards]}")
    print(f"{game.players[1].character.name} 手牌: {[card.name for card in game.players[1].hand_cards]}")
    
    # 测试无中生有
    print("\n=== 测试无中生有 ===")
    wuzhong_card = Card("无中生有", CardType.TRICK, "♦", 9)
    game.players[0].hand_cards.append(wuzhong_card)
    
    print(f"{game.players[0].character.name} 获得了 无中生有")
    print(f"当前手牌: {[card.name for card in game.players[0].hand_cards]}")
    
    # 使用无中生有
    card_index = len(game.players[0].hand_cards) - 1
    used_card = game.players[0].play_card(card_index)
    if used_card:
        card_action = game.create_card_action(used_card)
        card_action.apply_effect(game, game.players[0])
    
    print(f"{game.players[0].character.name} 手牌: {[card.name for card in game.players[0].hand_cards]}")
    
    # 测试决斗
    print("\n=== 测试决斗 ===")
    # 给对手一些杀牌
    from app.models.game import Card, CardType
    for _ in range(2):
        sha_card = Card("杀", CardType.BASIC, "♠", random.randint(1, 13))
        game.players[1].hand_cards.append(sha_card)
    
    juedou_card = Card("决斗", CardType.TRICK, "♣", 10)
    game.players[0].hand_cards.append(juedou_card)
    
    print(f"{game.players[0].character.name} 获得了 决斗")
    print(f"{game.players[1].character.name} 手牌: {[card.name for card in game.players[1].hand_cards]}")
    
    # 使用决斗
    card_index = len(game.players[0].hand_cards) - 1
    used_card = game.players[0].play_card(card_index)
    if used_card:
        card_action = game.create_card_action(used_card)
        # 手动处理响应
        result = card_action.handle_response(game, game.players[0])
        print(f"决斗结果: {result}")
    
    print(f"{game.players[0].character.name} 血量: {game.players[0].character.hp}")
    print(f"{game.players[1].character.name} 血量: {game.players[1].character.hp}")
    
    print("\n=== 锦囊牌测试完成 ===")

if __name__ == "__main__":
    test_trick_cards()