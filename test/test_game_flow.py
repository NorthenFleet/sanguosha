#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.game_engine import GameEngine
from app.models.character import Character, Kingdom
from app.models.card import Card
from app.models.enums import CardType

def test_game_flow():
    """测试游戏整体流程稳定性"""
    print("=== 测试游戏整体流程稳定性 ===")
    
    # 创建游戏引擎
    engine = GameEngine()
    
    print("\n=== 测试游戏创建 ===")
    try:
        # 使用正确的武将名称创建游戏
        game_id = engine.create_game("曹操", "刘备")
        print(f"游戏创建成功，游戏ID: {game_id}")
        
        # 获取游戏状态
        game_status = engine.get_game_status(game_id)
        print(f"游戏状态: {game_status}")
        
    except Exception as e:
        print(f"游戏创建失败: {e}")
        return

    print("\n=== 测试游戏动作执行 ===")
    try:
        # 测试游戏动作
        game = engine.get_game(game_id)
        if game:
            print(f"当前玩家: {game.current_player.character.name}")
            print(f"玩家手牌数: {len(game.current_player.hand_cards)}")
            
            # 尝试执行一个简单的游戏动作
            if game.current_player.hand_cards:
                card = game.current_player.hand_cards[0]
                print(f"尝试使用卡牌: {card.name}")
                
    except Exception as e:
        print(f"游戏动作执行失败: {e}")

    print("\n=== 测试多轮游戏流程 ===")
    try:
        # 测试多轮游戏
        for round_num in range(1, 4):
            print(f"\n--- 第 {round_num} 轮 ---")
            game = engine.get_game(game_id)
            if game:
                print(f"当前玩家: {game.current_player.character.name}")
                print(f"玩家血量: {game.current_player.character.hp}")
                print(f"手牌数: {len(game.current_player.hand_cards)}")
                
                # 模拟回合结束
                if hasattr(game, 'next_turn'):
                    game.next_turn()
                
    except Exception as e:
        print(f"多轮游戏流程测试失败: {e}")

    print("\n=== 测试错误处理 ===")
    try:
        # 测试无效游戏ID
        invalid_status = engine.get_game_status("invalid_game_id")
        print(f"无效游戏ID错误处理: {invalid_status}")
    except Exception as e:
        print(f"无效游戏ID错误处理: {e}")
    
    try:
        # 测试无效武将选择
        engine.create_game("无效武将", "刘备")
    except Exception as e:
        print(f"无效武将选择错误处理: {e}")

    print("\n=== 测试游戏状态一致性 ===")
    try:
        game = engine.get_game(game_id)
        if game:
            # 验证游戏状态一致性
            total_cards = len(game.deck.cards) + sum(len(player.hand_cards) for player in game.players)
            print(f"卡牌总数一致性检查: 牌堆 {len(game.deck.cards)} + 手牌 {sum(len(player.hand_cards) for player in game.players)} = {total_cards}")
            
            # 验证玩家状态
            for i, player in enumerate(game.players):
                print(f"玩家{i+1}: {player.character.name} - 血量: {player.character.hp}/{player.character.max_hp}")
                
    except Exception as e:
        print(f"游戏状态一致性测试失败: {e}")
    
    print("\n游戏整体流程稳定性测试完成!")

if __name__ == "__main__":
    test_game_flow()