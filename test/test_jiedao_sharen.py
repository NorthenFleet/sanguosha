#!/usr/bin/env python3
"""
测试借刀杀人的响应机制
"""

import sys
import os

from app.core.base.game import Game
from app.core.events.event_system import EventManager
from app.models.card import Card
from app.models.character import Character, Kingdom
from app.models.player import Player

def test_jiedao_with_sha():
    """测试借刀杀人 - 目标有杀的情况"""
    print("=== 测试借刀杀人 - 目标有杀 ===")
    
    # 创建事件管理器和游戏实例
    event_manager = EventManager()
    game = Game(event_manager)
    
    # 创建测试角色
    char1 = Character("曹操", Kingdom.WEI, 4, ["奸雄", "护驾"])
    char2 = Character("刘备", Kingdom.SHU, 4, ["仁德", "激将"])
    char3 = Character("关羽", Kingdom.SHU, 4, ["武圣"])
    
    # 创建玩家
    player1 = Player(char1)  # 使用借刀杀人的玩家
    player2 = Player(char2)  # 装备武器的玩家
    player3 = Player(char3)  # 被攻击的目标
    
    # 添加玩家到游戏
    game.players = [player1, player2, player3]
    game.current_player_index = 0
    
    # 给玩家1添加借刀杀人
    jiedao_card = Card("借刀杀人", "锦囊牌", "梅花", 12)
    player1.hand_cards.append(jiedao_card)
    
    # 给玩家2装备武器和杀
    weapon_card = Card("青龙偃月刀", "装备牌", "黑桃", 5)
    sha_card = Card("杀", "基本牌", "黑桃", 7)
    player2.equipped.append(weapon_card)
    player2.weapon = weapon_card
    player2.hand_cards.append(sha_card)
    
    # 给玩家3添加一些牌
    shan_card = Card("闪", "基本牌", "红桃", 2)
    player3.hand_cards.append(shan_card)
    
    print(f"初始状态：")
    print(f"玩家1({player1.character.name})手牌: {[card.name for card in player1.hand_cards]}")
    print(f"玩家2({player2.character.name})手牌: {[card.name for card in player2.hand_cards]}, 武器: {player2.weapon.name if player2.weapon else '无'}")
    print(f"玩家3({player3.character.name})手牌: {[card.name for card in player3.hand_cards]}")
    
    # 设置测试模式
    game.current_phase = "test"
    
    # 玩家1使用借刀杀人
    print(f"\n{player1.character.name} 使用借刀杀人")
    
    # 模拟使用卡牌
    action = game.create_card_action(jiedao_card)
    if action:
        result = action.apply_effect(game, player1, player2)
        print(f"借刀杀人结果: {'成功' if result else '失败'}")
    
    print(f"\n结果状态：")
    print(f"玩家1({player1.character.name})手牌: {[card.name for card in player1.hand_cards]}, 武器: {player1.weapon.name if player1.weapon else '无'}")
    print(f"玩家2({player2.character.name})手牌: {[card.name for card in player2.hand_cards]}, 武器: {player2.weapon.name if player2.weapon else '无'}")
    print(f"玩家3({player3.character.name})手牌: {[card.name for card in player3.hand_cards]}, 血量: {player3.character.hp}")
    print(f"弃牌堆: {[card.name for card in game.discard_pile]}")

def test_jiedao_without_sha():
    """测试借刀杀人 - 目标没有杀的情况"""
    print("\n=== 测试借刀杀人 - 目标没有杀 ===")
    
    # 创建事件管理器和游戏实例
    event_manager = EventManager()
    game = Game(event_manager)
    
    # 创建测试角色
    char1 = Character("曹操", Kingdom.WEI, 4, ["奸雄", "护驾"])
    char2 = Character("刘备", Kingdom.SHU, 4, ["仁德", "激将"])
    char3 = Character("关羽", Kingdom.SHU, 4, ["武圣"])
    
    # 创建玩家
    player1 = Player(char1)  # 使用借刀杀人的玩家
    player2 = Player(char2)  # 装备武器的玩家
    player3 = Player(char3)  # 被攻击的目标
    
    # 添加玩家到游戏
    game.players = [player1, player2, player3]
    game.current_player_index = 0
    
    # 给玩家1添加借刀杀人
    jiedao_card = Card("借刀杀人", "锦囊牌", "梅花", 13)
    player1.hand_cards.append(jiedao_card)
    
    # 给玩家2装备武器但没有杀
    weapon_card = Card("丈八蛇矛", "装备牌", "黑桃", 12)
    tao_card = Card("桃", "基本牌", "红桃", 3)
    player2.equipped.append(weapon_card)
    player2.weapon = weapon_card
    player2.hand_cards.append(tao_card)
    
    # 给玩家3添加一些牌
    shan_card = Card("闪", "基本牌", "红桃", 2)
    player3.hand_cards.append(shan_card)
    
    print(f"初始状态：")
    print(f"玩家1({player1.character.name})手牌: {[card.name for card in player1.hand_cards]}, 武器: {player1.weapon.name if player1.weapon else '无'}")
    print(f"玩家2({player2.character.name})手牌: {[card.name for card in player2.hand_cards]}, 武器: {player2.weapon.name if player2.weapon else '无'}")
    print(f"玩家3({player3.character.name})手牌: {[card.name for card in player3.hand_cards]}")
    
    # 设置测试模式
    game.current_phase = "test"
    
    # 玩家1使用借刀杀人
    print(f"\n{player1.character.name} 使用借刀杀人")
    
    # 模拟使用卡牌
    action = game.create_card_action(jiedao_card)
    if action:
        result = action.apply_effect(game, player1, player2)
        print(f"借刀杀人结果: {'成功' if result else '失败'}")
    
    print(f"\n结果状态：")
    print(f"玩家1({player1.character.name})手牌: {[card.name for card in player1.hand_cards]}, 武器: {player1.weapon.name if player1.weapon else '无'}")
    print(f"玩家2({player2.character.name})手牌: {[card.name for card in player2.hand_cards]}, 武器: {player2.weapon.name if player2.weapon else '无'}")
    print(f"玩家3({player3.character.name})手牌: {[card.name for card in player3.hand_cards]}, 血量: {player3.character.hp}")
    print(f"弃牌堆: {[card.name for card in game.discard_pile]}")

def test_jiedao_with_wuxie():
    """测试借刀杀人被无懈可击响应"""
    print("\n=== 测试借刀杀人被无懈可击响应 ===")
    
    # 创建事件管理器和游戏实例
    event_manager = EventManager()
    game = Game(event_manager)
    
    # 创建测试角色
    char1 = Character("曹操", Kingdom.WEI, 4, ["奸雄", "护驾"])
    char2 = Character("刘备", Kingdom.SHU, 4, ["仁德", "激将"])
    char3 = Character("关羽", Kingdom.SHU, 4, ["武圣"])
    
    # 创建玩家
    player1 = Player(char1)  # 使用借刀杀人的玩家
    player2 = Player(char2)  # 装备武器的玩家
    player3 = Player(char3)  # 有无懈可击的玩家
    
    # 添加玩家到游戏
    game.players = [player1, player2, player3]
    game.current_player_index = 0
    
    # 给玩家1添加借刀杀人
    jiedao_card = Card("借刀杀人", "锦囊牌", "梅花", 12)
    player1.hand_cards.append(jiedao_card)
    
    # 给玩家2装备武器和杀
    weapon_card = Card("青龙偃月刀", "装备牌", "黑桃", 5)
    sha_card = Card("杀", "基本牌", "黑桃", 7)
    player2.equipped.append(weapon_card)
    player2.weapon = weapon_card
    player2.hand_cards.append(sha_card)
    
    # 给玩家3添加无懈可击
    wuxie_card = Card("无懈可击", "锦囊牌", "红桃", 12)
    player3.hand_cards.append(wuxie_card)
    
    print(f"初始状态：")
    print(f"玩家1({player1.character.name})手牌: {[card.name for card in player1.hand_cards]}")
    print(f"玩家2({player2.character.name})手牌: {[card.name for card in player2.hand_cards]}, 武器: {player2.weapon.name if player2.weapon else '无'}")
    print(f"玩家3({player3.character.name})手牌: {[card.name for card in player3.hand_cards]}")
    
    # 设置测试模式
    game.current_phase = "test"
    
    # 玩家1使用借刀杀人
    print(f"\n{player1.character.name} 使用借刀杀人")
    
    # 模拟使用卡牌
    action = game.create_card_action(jiedao_card)
    if action:
        result = action.apply_effect(game, player1, player2)
        print(f"借刀杀人结果: {'成功' if result else '被无懈可击抵消'}")
    
    print(f"\n结果状态：")
    print(f"玩家1({player1.character.name})手牌: {[card.name for card in player1.hand_cards]}")
    print(f"玩家2({player2.character.name})手牌: {[card.name for card in player2.hand_cards]}, 武器: {player2.weapon.name if player2.weapon else '无'}")
    print(f"玩家3({player3.character.name})手牌: {[card.name for card in player3.hand_cards]}")
    print(f"弃牌堆: {[card.name for card in game.discard_pile]}")

