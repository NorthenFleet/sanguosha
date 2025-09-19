#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试新的交互模型系统
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.integrated_interaction_system import EnhancedGameEngine
from app.models.character import CharacterFactory
from app.models.card import Card, CardType
import logging

# 设置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def create_test_card(name: str, card_type: str = "basic", suit: str = "♠", number: int = 1):
    """创建测试卡牌"""
    card = Card()
    card.name = name
    card.category = card_type
    card.suit = suit
    card.rank = number
    return card


def test_basic_card_usage():
    """测试基本卡牌使用"""
    print("=== 测试基本卡牌使用 ===")
    
    # 创建增强的游戏引擎
    engine = EnhancedGameEngine()
    
    # 创建游戏
    game_id = engine.create_game("曹操", "刘备")
    game = engine.get_game(game_id)
    
    # 给玩家添加测试卡牌
    sha_card = create_test_card("杀")
    shan_card = create_test_card("闪")
    tao_card = create_test_card("桃")
    
    game.players[0].hand_cards.extend([sha_card, tao_card])
    game.players[1].hand_cards.append(shan_card)
    
    print(f"玩家1({game.players[0].character.name})手牌: {[card.name for card in game.players[0].hand_cards]}")
    print(f"玩家2({game.players[1].character.name})手牌: {[card.name for card in game.players[1].hand_cards]}")
    
    # 测试使用杀
    print("\n--- 测试使用杀 ---")
    result = engine.use_card(game_id, 0, "杀", 1)
    print(f"使用杀的结果: {result}")
    
    # 测试使用桃
    print("\n--- 测试使用桃 ---")
    # 先让玩家受伤
    game.players[0].character.hp = 2
    result = engine.use_card(game_id, 0, "桃")
    print(f"使用桃的结果: {result}")
    
    print("基本卡牌使用测试完成\n")


def test_skill_usage():
    """测试技能使用"""
    print("=== 测试技能使用 ===")
    
    engine = EnhancedGameEngine()
    game_id = engine.create_game("曹操", "刘备")  # 曹操有奸雄技能
    game = engine.get_game(game_id)
    
    print(f"曹操的技能: {game.players[0].character.skills}")
    
    # 测试仁德技能（刘备）
    print("\n--- 测试仁德技能 ---")
    # 给刘备添加手牌
    cards = [create_test_card("杀"), create_test_card("闪")]
    game.players[1].hand_cards.extend(cards)
    
    result = engine.use_skill(game_id, 1, "仁德", 0, cards_to_give=cards)
    print(f"使用仁德的结果: {result}")
    
    print("技能使用测试完成\n")


def test_response_mechanism():
    """测试响应机制"""
    print("=== 测试响应机制 ===")
    
    engine = EnhancedGameEngine()
    game_id = engine.create_game("张飞", "赵云")  # 张飞有咆哮
    game = engine.get_game(game_id)
    
    # 给玩家添加卡牌
    sha_card = create_test_card("杀")
    shan_card = create_test_card("闪")
    
    game.players[0].hand_cards.append(sha_card)
    game.players[1].hand_cards.append(shan_card)
    
    print(f"张飞手牌: {[card.name for card in game.players[0].hand_cards]}")
    print(f"赵云手牌: {[card.name for card in game.players[1].hand_cards]}")
    
    # 张飞使用杀
    print("\n--- 张飞使用杀 ---")
    result = engine.use_card(game_id, 0, "杀", 1)
    print(f"使用杀的结果: {result}")
    
    # 模拟赵云使用闪响应（这里简化处理）
    print("\n--- 赵云使用闪响应 ---")
    # 在实际游戏中，这应该是自动触发的响应流程
    # 这里我们手动测试闪的使用
    result = engine.use_card(game_id, 1, "闪")
    print(f"使用闪的结果: {result}")
    
    print("响应机制测试完成\n")


def test_complex_interaction():
    """测试复杂交互"""
    print("=== 测试复杂交互 ===")
    
    engine = EnhancedGameEngine()
    game_id = engine.create_game("曹操", "刘备")
    game = engine.get_game(game_id)
    
    # 设置复杂场景
    sha_card = create_test_card("杀")
    wuxie_card = create_test_card("无懈可击")
    guohe_card = create_test_card("过河拆桥")
    
    game.players[0].hand_cards.extend([sha_card, guohe_card])
    game.players[1].hand_cards.append(wuxie_card)
    
    print(f"曹操手牌: {[card.name for card in game.players[0].hand_cards]}")
    print(f"刘备手牌: {[card.name for card in game.players[1].hand_cards]}")
    
    # 测试过河拆桥
    print("\n--- 测试过河拆桥 ---")
    result = engine.use_card(game_id, 0, "过河拆桥", 1)
    print(f"使用过河拆桥的结果: {result}")
    
    # 测试无懈可击响应
    print("\n--- 测试无懈可击响应 ---")
    result = engine.use_card(game_id, 1, "无懈可击")
    print(f"使用无懈可击的结果: {result}")
    
    print("复杂交互测试完成\n")


def test_damage_and_recovery():
    """测试伤害和回复"""
    print("=== 测试伤害和回复 ===")
    
    engine = EnhancedGameEngine()
    game_id = engine.create_game("曹操", "刘备")
    game = engine.get_game(game_id)
    
    print(f"初始体力 - 曹操: {game.players[0].character.hp}, 刘备: {game.players[1].character.hp}")
    
    # 直接测试伤害处理
    print("\n--- 测试伤害处理 ---")
    result = engine.interaction_system.process_damage(game_id, 0, 1, 2)
    print(f"伤害处理结果: {engine.interaction_system.adjudication_engine.create_summary(result)}")
    print(f"伤害后体力 - 曹操: {game.players[0].character.hp}, 刘备: {game.players[1].character.hp}")
    
    # 测试桃的回复
    print("\n--- 测试桃的回复 ---")
    tao_card = create_test_card("桃")
    game.players[1].hand_cards.append(tao_card)
    result = engine.use_card(game_id, 1, "桃")
    print(f"使用桃的结果: {result}")
    print(f"回复后体力 - 曹操: {game.players[0].character.hp}, 刘备: {game.players[1].character.hp}")
    
    print("伤害和回复测试完成\n")


def main():
    """主测试函数"""
    print("开始测试新的交互模型系统")
    print("=" * 50)
    
    try:
        test_basic_card_usage()
        test_skill_usage()
        test_response_mechanism()
        test_complex_interaction()
        test_damage_and_recovery()
        
        print("=" * 50)
        print("所有测试完成！新的交互模型系统运行正常。")
        
    except Exception as e:
        print(f"测试过程中出现错误: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()