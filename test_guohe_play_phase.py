#!/usr/bin/env python3
"""
测试过河拆桥被无懈可击响应后出牌阶段继续的功能
"""
import sys
import os
import random

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.models.game import Game, Character, Card, CardType

def test_guohe_play_phase_continue():
    """测试过河拆桥被无懈可击响应后出牌阶段继续"""
    print("=== 测试过河拆桥被无懈可击响应后出牌阶段继续 ===")
    
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
    
    # 给曹操多张手牌，包括过河拆桥
    guohe_card = Card("过河拆桥", CardType.TRICK, "♠", 3)
    game.players[0].hand_cards.append(guohe_card)
    
    # 给曹操其他手牌
    sha_card = Card("杀", CardType.BASIC, "♠", 10)
    game.players[0].hand_cards.append(sha_card)
    
    # 给刘备无懈可击
    wuxie_card = Card("无懈可击", CardType.TRICK, "♠", 8)
    game.players[1].hand_cards.append(wuxie_card)
    
    print(f"\n曹操 获得了 过河拆桥 和 杀")
    print(f"刘备 获得了 无懈可击")
    print(f"曹操 手牌: {[card.name for card in game.players[0].hand_cards]}")
    print(f"刘备 手牌: {[card.name for card in game.players[1].hand_cards]}")
    
    # 测试出牌阶段
    print(f"\n=== 测试曹操的出牌阶段 ===")
    
    # 模拟出牌阶段
    player = game.players[0]
    has_used_kill = False
    
    print(f"{player.character.name} 的出牌阶段开始...")
    
    # 使用过河拆桥
    guohe_index = None
    for i, card in enumerate(player.hand_cards):
        if card.name == "过河拆桥":
            guohe_index = i
            break
    
    if guohe_index is not None:
        used_card = player.play_card(guohe_index)
        print(f"{player.character.name} 使用了 过河拆桥")
        
        # 处理响应
        response_result = game.handle_response(player, used_card, test_mode=False)
        
        if response_result == "continue_play_phase":
            print(f"过河拆桥被无懈可击取消，{player.character.name} 的出牌阶段继续。")
            
            # 检查是否还有其他手牌可以使用
            if player.hand_cards:
                print(f"{player.character.name} 可以继续使用其他手牌")
                print(f"剩余手牌: {[card.name for card in player.hand_cards]}")
                
                # 尝试使用杀
                sha_index = None
                for i, card in enumerate(player.hand_cards):
                    if card.name == "杀":
                        sha_index = i
                        break
                
                if sha_index is not None:
                    used_card = player.play_card(sha_index)
                    print(f"{player.character.name} 使用了 杀")
                    
                    # 处理响应
                    kill_result = game.handle_response(player, used_card, test_mode=False)
                    print(f"杀的使用结果: {kill_result}")
                else:
                    print("没有其他手牌可以使用")
            else:
                print("没有其他手牌可以使用")
        else:
            print(f"过河拆桥生效，{player.character.name} 弃置了刘备一张手牌。")
    
    print(f"\n最终手牌:")
    print(f"曹操: {[card.name for card in game.players[0].hand_cards]}")
    print(f"刘备: {[card.name for card in game.players[1].hand_cards]}")

if __name__ == "__main__":
    test_guohe_play_phase_continue()