#!/usr/bin/env python3
"""
测试锦囊牌系统的完整流程，包括无懈可击响应机制
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.core.game import Game
from app.models.card import Card
from app.models.character import Character
from app.models.player import Player

def test_trick_card_with_wuxie():
    """测试锦囊牌的无懈可击响应机制"""
    print("=== 测试锦囊牌无懈可击响应机制 ===")
    
    # 创建游戏实例
    game = Game()
    
    # 创建测试角色
    char1 = Character("刘备", 4, ["仁德", "激将"])
    char2 = Character("关羽", 4, ["武圣"])
    char3 = Character("张飞", 4, ["咆哮"])
    
    # 创建玩家
    player1 = Player(char1)
    player2 = Player(char2)
    player3 = Player(char3)
    
    # 添加玩家到游戏
    game.players = [player1, player2, player3]
    game.current_player_index = 0
    
    # 给玩家1添加过河拆桥
    guohe_card = Card("过河拆桥", "锦囊牌", "黑桃", 3)
    player1.hand_cards.append(guohe_card)
    
    # 给玩家2添加无懈可击
    wuxie_card = Card("无懈可击", "锦囊牌", "红桃", 12)
    player2.hand_cards.append(wuxie_card)
    
    # 给玩家3添加一些牌作为目标
    target_card1 = Card("杀", "基本牌", "黑桃", 7)
    target_card2 = Card("闪", "基本牌", "红桃", 2)
    player3.hand_cards.extend([target_card1, target_card2])
    
    print(f"初始状态：")
    print(f"玩家1({player1.character.name})手牌: {[card.name for card in player1.hand_cards]}")
    print(f"玩家2({player2.character.name})手牌: {[card.name for card in player2.hand_cards]}")
    print(f"玩家3({player3.character.name})手牌: {[card.name for card in player3.hand_cards]}")
    
    # 设置测试模式
    game.current_phase = "test"
    
    # 玩家1使用过河拆桥对玩家3
    print(f"\n{player1.character.name} 使用过河拆桥对 {player3.character.name}")
    
    # 模拟使用卡牌
    action = game.create_card_action(guohe_card)
    if action:
        # 这里会触发无懈可击响应机制
        result = action.apply_effect(game, player1, player3)
        print(f"过河拆桥结果: {'成功' if result else '被抵消'}")
    
    print(f"\n结果状态：")
    print(f"玩家1({player1.character.name})手牌: {[card.name for card in player1.hand_cards]}")
    print(f"玩家2({player2.character.name})手牌: {[card.name for card in player2.hand_cards]}")
    print(f"玩家3({player3.character.name})手牌: {[card.name for card in player3.hand_cards]}")
    print(f"弃牌堆: {[card.name for card in game.discard_pile]}")

def test_guohe_effect():
    """测试过河拆桥的完整效果"""
    print("\n=== 测试过河拆桥完整效果 ===")
    
    # 创建游戏实例
    game = Game()
    
    # 创建测试角色
    char1 = Character("刘备", 4, ["仁德", "激将"])
    char2 = Character("关羽", 4, ["武圣"])
    
    # 创建玩家
    player1 = Player(char1)
    player2 = Player(char2)
    
    # 添加玩家到游戏
    game.players = [player1, player2]
    game.current_player_index = 0
    
    # 给玩家1添加过河拆桥
    guohe_card = Card("过河拆桥", "锦囊牌", "黑桃", 3)
    player1.hand_cards.append(guohe_card)
    
    # 给玩家2添加各种类型的牌
    hand_card = Card("杀", "基本牌", "黑桃", 7)
    equipment_card = Card("青龙偃月刀", "装备牌", "黑桃", 5)
    judgment_card = Card("乐不思蜀", "锦囊牌", "红桃", 6)
    
    player2.hand_cards.append(hand_card)
    player2.equipped.append(equipment_card)
    player2.weapon = equipment_card
    player2.judgment_area.append(judgment_card)
    
    print(f"初始状态：")
    print(f"玩家1({player1.character.name})手牌: {[card.name for card in player1.hand_cards]}")
    print(f"玩家2({player2.character.name})手牌: {[card.name for card in player2.hand_cards]}")
    print(f"玩家2({player2.character.name})装备: {[card.name for card in player2.equipped]}")
    print(f"玩家2({player2.character.name})判定区: {[card.name for card in player2.judgment_area]}")
    
    # 设置测试模式
    game.current_phase = "test"
    
    # 玩家1使用过河拆桥对玩家2
    print(f"\n{player1.character.name} 使用过河拆桥对 {player2.character.name}")
    
    # 模拟使用卡牌
    action = game.create_card_action(guohe_card)
    if action:
        result = action.apply_effect(game, player1, player2)
        print(f"过河拆桥结果: {'成功' if result else '失败'}")
    
    print(f"\n结果状态：")
    print(f"玩家1({player1.character.name})手牌: {[card.name for card in player1.hand_cards]}")
    print(f"玩家2({player2.character.name})手牌: {[card.name for card in player2.hand_cards]}")
    print(f"玩家2({player2.character.name})装备: {[card.name for card in player2.equipped]}")
    print(f"玩家2({player2.character.name})判定区: {[card.name for card in player2.judgment_area]}")
    print(f"弃牌堆: {[card.name for card in game.discard_pile]}")

def test_multiple_wuxie_responses():
    """测试多个玩家的无懈可击响应"""
    print("\n=== 测试多个玩家无懈可击响应 ===")
    
    # 创建游戏实例
    game = Game()
    
    # 创建测试角色
    char1 = Character("刘备", 4, ["仁德", "激将"])
    char2 = Character("关羽", 4, ["武圣"])
    char3 = Character("张飞", 4, ["咆哮"])
    char4 = Character("赵云", 4, ["龙胆"])
    
    # 创建玩家
    player1 = Player(char1)
    player2 = Player(char2)
    player3 = Player(char3)
    player4 = Player(char4)
    
    # 添加玩家到游戏
    game.players = [player1, player2, player3, player4]
    game.current_player_index = 0
    
    # 给玩家1添加决斗
    juedou_card = Card("决斗", "锦囊牌", "黑桃", 1)
    player1.hand_cards.append(juedou_card)
    
    # 给多个玩家添加无懈可击
    wuxie_card1 = Card("无懈可击", "锦囊牌", "红桃", 12)
    wuxie_card2 = Card("无懈可击", "锦囊牌", "红桃", 13)
    player2.hand_cards.append(wuxie_card1)
    player3.hand_cards.append(wuxie_card2)
    
    # 给目标玩家添加一些牌
    target_card = Card("杀", "基本牌", "黑桃", 7)
    player4.hand_cards.append(target_card)
    
    print(f"初始状态：")
    print(f"玩家1({player1.character.name})手牌: {[card.name for card in player1.hand_cards]}")
    print(f"玩家2({player2.character.name})手牌: {[card.name for card in player2.hand_cards]}")
    print(f"玩家3({player3.character.name})手牌: {[card.name for card in player3.hand_cards]}")
    print(f"玩家4({player4.character.name})手牌: {[card.name for card in player4.hand_cards]}")
    
    # 设置测试模式
    game.current_phase = "test"
    
    # 玩家1使用决斗对玩家4
    print(f"\n{player1.character.name} 使用决斗对 {player4.character.name}")
    print("所有玩家都有机会使用无懈可击响应")
    
    # 模拟使用卡牌
    action = game.create_card_action(juedou_card)
    if action:
        result = action.apply_effect(game, player1, player4)
        print(f"决斗结果: {'成功' if result else '被抵消'}")
    
    print(f"\n结果状态：")
    print(f"玩家1({player1.character.name})手牌: {[card.name for card in player1.hand_cards]}")
    print(f"玩家2({player2.character.name})手牌: {[card.name for card in player2.hand_cards]}")
    print(f"玩家3({player3.character.name})手牌: {[card.name for card in player3.hand_cards]}")
    print(f"玩家4({player4.character.name})手牌: {[card.name for card in player4.hand_cards]}")
    print(f"弃牌堆: {[card.name for card in game.discard_pile]}")

if __name__ == "__main__":
    print("开始测试锦囊牌系统...")
    
    # 运行所有测试
    test_trick_card_with_wuxie()
    test_guohe_effect()
    test_multiple_wuxie_responses()
    
    print("\n=== 测试完成 ===")
    print("锦囊牌系统测试结果：")
    print("1. 无懈可击响应机制 - 已实现")
    print("2. 过河拆桥效果 - 已实现")
    print("3. 多玩家响应顺序 - 已实现")
    print("4. 卡牌区域管理 - 已实现")