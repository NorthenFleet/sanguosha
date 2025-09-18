#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
弃牌堆数量显示测试脚本
验证卡牌使用后是否正确进入弃牌堆
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.models.deck import Deck
from app.core.game import Game, Character
from app.models.player import Player
from app.models.enums import CardType

def test_discard_pile_count():
    """测试弃牌堆数量显示"""
    print("\n=== 弃牌堆数量显示测试 ===")
    
    try:
        # 创建游戏实例
        game = Game(None)
        
        # 创建角色和玩家
        caocao = Character("曹操", "魏", 4, ["奸雄"])
        liubei = Character("刘备", "蜀", 4, ["仁德"])
        
        player1 = Player(caocao)
        player2 = Player(liubei)
        
        game.add_player(player1)
        game.add_player(player2)
        
        # 初始化牌堆
        game.initialize_deck()
        
        print(f"初始状态:")
        print(f"  摸牌堆: {len(game.deck.cards)} 张")
        print(f"  弃牌堆: {len(game.deck.discard_pile)} 张")
        
        # 给玩家发手牌
        for _ in range(4):
            card = game.deck.draw_card()
            if card:
                player1.hand_cards.append(card)
        
        print(f"\n发牌后状态:")
        print(f"  摸牌堆: {len(game.deck.cards)} 张")
        print(f"  弃牌堆: {len(game.deck.discard_pile)} 张")
        print(f"  玩家1手牌: {len(player1.hand_cards)} 张")
        
        # 模拟使用卡牌
        if player1.hand_cards:
            used_card = player1.hand_cards.pop(0)
            print(f"\n玩家1使用卡牌: {used_card.name}")
            
            # 卡牌进入弃牌堆
            game.deck.discard(used_card)
            print(f"卡牌 {used_card.name} 进入弃牌堆")
            
            print(f"\n使用卡牌后状态:")
            print(f"  摸牌堆: {len(game.deck.cards)} 张")
            print(f"  弃牌堆: {len(game.deck.discard_pile)} 张")
            print(f"  玩家1手牌: {len(player1.hand_cards)} 张")
        
        # 模拟弃牌阶段
        if player1.hand_cards:
            discarded_card = player1.hand_cards.pop()
            print(f"\n弃牌阶段: 玩家1弃置 {discarded_card.name}")
            
            # 弃牌进入弃牌堆
            game.deck.discard(discarded_card)
            print(f"弃牌 {discarded_card.name} 进入弃牌堆")
            
            print(f"\n弃牌后状态:")
            print(f"  摸牌堆: {len(game.deck.cards)} 张")
            print(f"  弃牌堆: {len(game.deck.discard_pile)} 张")
            print(f"  玩家1手牌: {len(player1.hand_cards)} 张")
        
        # 验证弃牌堆数量
        expected_discard_count = 2  # 使用1张 + 弃置1张
        actual_discard_count = len(game.deck.discard_pile)
        
        if actual_discard_count == expected_discard_count:
            print(f"\n✅ 弃牌堆数量显示正确: {actual_discard_count} 张")
            return True
        else:
            print(f"\n❌ 弃牌堆数量显示错误: 期望 {expected_discard_count} 张，实际 {actual_discard_count} 张")
            return False
            
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        return False

def test_card_usage_in_game():
    """测试游戏中卡牌使用的弃牌堆逻辑"""
    print("\n=== 游戏中卡牌使用测试 ===")
    
    try:
        # 创建游戏实例
        game = Game(None)
        
        # 创建角色和玩家
        caocao = Character("曹操", "魏", 4, ["奸雄"])
        liubei = Character("刘备", "蜀", 4, ["仁德"])
        
        player1 = Player(caocao)
        player2 = Player(liubei)
        
        game.add_player(player1)
        game.add_player(player2)
        
        # 初始化牌堆
        game.initialize_deck()
        
        # 给玩家发手牌
        for _ in range(3):
            card = game.deck.draw_card()
            if card:
                player1.hand_cards.append(card)
        
        initial_discard_count = len(game.deck.discard_pile)
        initial_hand_count = len(player1.hand_cards)
        print(f"初始弃牌堆数量: {initial_discard_count}")
        print(f"初始手牌数量: {initial_hand_count}")
        
        # 检查第一张手牌的类型
        first_card = player1.hand_cards[0] if player1.hand_cards else None
        if first_card:
            print(f"将要使用的卡牌: {first_card.name}({first_card.type.value})")
        
        # 模拟出牌阶段（测试模式）
        if player1.hand_cards:
            print(f"\n模拟出牌阶段...")
            
            # 模拟使用一张牌
            game.play_phase(player1, test_mode=True)
            
            final_discard_count = len(game.deck.discard_pile)
            final_hand_count = len(player1.hand_cards)
            print(f"出牌后弃牌堆数量: {final_discard_count}")
            print(f"出牌后手牌数量: {final_hand_count}")
            
            # 验证卡牌使用逻辑
            if first_card and first_card.type.value == "装备牌":
                # 装备牌不应该进入弃牌堆，但手牌数量应该减少
                if final_hand_count == initial_hand_count - 1 and final_discard_count == initial_discard_count:
                    print(f"✅ 装备牌使用正确：手牌减少1张，弃牌堆数量不变")
                    return True
                else:
                    print(f"❌ 装备牌使用逻辑错误")
                    return False
            else:
                # 非装备牌应该进入弃牌堆
                if final_discard_count > initial_discard_count:
                    print(f"✅ 非装备牌使用后正确进入弃牌堆，数量增加了 {final_discard_count - initial_discard_count} 张")
                    return True
                else:
                    print(f"❌ 非装备牌使用后没有进入弃牌堆")
                    return False
        else:
            print("❌ 玩家没有手牌可以使用")
            return False
            
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        return False

if __name__ == "__main__":
    print("🎯 开始弃牌堆数量显示测试...")
    
    test1_result = test_discard_pile_count()
    test2_result = test_card_usage_in_game()
    
    print("\n" + "="*50)
    print("📊 测试结果汇总")
    print("="*50)
    print(f"  基础弃牌堆测试        {'✅ 通过' if test1_result else '❌ 失败'}")
    print(f"  游戏中卡牌使用测试    {'✅ 通过' if test2_result else '❌ 失败'}")
    
    total_tests = 2
    passed_tests = sum([test1_result, test2_result])
    
    print(f"\n🎯 总体结果: {passed_tests}/{total_tests} 测试通过")
    print(f"📈 通过率: {passed_tests/total_tests*100:.1f}%")
    
    if passed_tests == total_tests:
        print("\n🎉 所有测试通过！弃牌堆数量显示功能正常！")
    else:
        print("\n⚠️  部分测试失败，需要进一步检查弃牌堆逻辑。")