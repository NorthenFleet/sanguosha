#!/usr/bin/env python3
"""
测试修复效果的脚本
"""
import sys
import os

from app.core.events.event_system import EventManager
from app.core.base.game import Game
from app.models.player import Player
from app.models.character import Character, Kingdom
from app.models.card import Card
from app.models.enums import CardType
from app.models.deck import Deck
from app.models.card_actions import ShaAction, WuZhongShengYouAction, GuoHeChaiQiaoAction

def test_sha_damage():
    """测试杀的伤害系统"""
    print("=== 测试杀的伤害系统 ===")
    
    # 创建事件管理器
    event_manager = EventManager()
    
    # 创建游戏实例
    game = Game(event_manager)
    game.current_phase = "test"
    
    # 创建角色和玩家
    character1 = Character("张飞", Kingdom.SHU, 4, ["咆哮"])
    character2 = Character("曹操", Kingdom.WEI, 4, ["奸雄"])
    
    player1 = Player(character1)
    player2 = Player(character2)
    
    # 设置玩家体力
    player1.hp = 4
    player2.hp = 4
    
    # 添加玩家到游戏
    game.add_player(player1)
    game.add_player(player2)
    game.current_player_index = 0
    
    # 创建杀牌
    sha_card = Card(name="杀", type=CardType.BASIC, suit="黑桃", rank=7)
    
    # 创建杀动作并应用效果
    sha_action = ShaAction()
    print(f"使用杀前 - {character2.name}体力: {character2.hp}")
    
    # 直接调用apply_default_effect来测试伤害系统
    sha_action.apply_default_effect(game, player1, player2)
    
    print(f"使用杀后 - {character2.name}体力: {character2.hp}")
    print("杀的伤害系统测试完成\n")
    
    if character2.hp == 3:
        print("✓ 杀的伤害系统正常工作")
    else:
        print("✗ 杀的伤害系统有问题")

def test_wuzhongshengyou():
    """测试无中生有"""
    print("\n=== 测试无中生有 ===")
    
    # 创建事件管理器
    event_manager = EventManager()
    
    # 创建游戏实例
    game = Game(event_manager)
    game.current_phase = "test"
    
    # 创建角色和玩家
    character1 = Character("张飞", Kingdom.SHU, 4, ["咆哮"])
    character2 = Character("曹操", Kingdom.WEI, 4, ["奸雄"])  # 添加第二个玩家以避免索引错误
    player1 = Player(character1)
    player2 = Player(character2)
    
    # 添加玩家到游戏
    game.add_player(player1)
    game.add_player(player2)  # 添加第二个玩家
    game.current_player_index = 0
    
    # 创建牌堆
    game.deck = Deck()
    
    # 记录使用前手牌数
    initial_hand_count = len(player1.hand_cards)
    print(f"使用无中生有前 - 手牌数: {initial_hand_count}")
    
    # 创建无中生有牌
    wzsy_card = Card(name="无中生有", type=CardType.TRICK, suit="红桃", rank=3)
    
    # 创建无中生有动作
    wzsy_action = WuZhongShengYouAction()
    
    # 应用效果
    wzsy_action.apply_effect(game, player1)
    
    final_hand_count = len(player1.hand_cards)
    print(f"使用无中生有后 - 手牌数: {final_hand_count}")
    
    if final_hand_count == initial_hand_count + 2:
        print("✓ 无中生有效果正常")
    else:
        print("✗ 无中生有效果有问题")

def test_guohechaiqiao():
    """测试过河拆桥"""
    print("\n=== 测试过河拆桥 ===")
    
    # 创建事件管理器
    event_manager = EventManager()
    
    # 创建游戏实例
    game = Game(event_manager)
    game.current_phase = "test"
    
    # 创建角色和玩家
    character1 = Character("张飞", Kingdom.SHU, 4, ["咆哮"])
    character2 = Character("曹操", Kingdom.WEI, 4, ["奸雄"])
    
    player1 = Player(character1)
    player2 = Player(character2)
    
    # 给player2一些手牌
    test_card = Card(name="杀", type=CardType.BASIC, suit="黑桃", rank=7)
    player2.hand_cards.append(test_card)
    
    # 添加玩家到游戏
    game.add_player(player1)
    game.add_player(player2)
    game.current_player_index = 0
    
    print(f"使用过河拆桥前 - {character2.name}手牌数: {len(player2.hand_cards)}")
    
    # 创建过河拆桥牌
    ghcq_card = Card(name="过河拆桥", type=CardType.TRICK, suit="梅花", rank=3)
    
    # 创建过河拆桥动作
    ghcq_action = GuoHeChaiQiaoAction()
    
    # 应用效果
    ghcq_action.apply_effect(game, player1, player2)
    
    print(f"使用过河拆桥后 - {character2.name}手牌数: {len(player2.hand_cards)}")
    
    if len(player2.hand_cards) == 0:
        print("✓ 过河拆桥效果正常")
    else:
        print("✗ 过河拆桥效果有问题")
