#!/usr/bin/env python3
"""
测试借刀杀人效果的修复
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
from app.models.card_actions import JieDaoShaRenAction

def test_jiedaosharen():
    print("=== 测试借刀杀人 ===")
    
    # 创建事件管理器
    event_manager = EventManager()
    
    # 创建游戏实例
    game = Game(event_manager)
    
    # 创建角色和玩家
    character1 = Character("张飞", Kingdom.SHU, 4, ["咆哮"])  # 使用者
    character2 = Character("关羽", Kingdom.SHU, 4, ["武圣"])  # 装备武器的角色
    character3 = Character("曹操", Kingdom.WEI, 4, ["奸雄"])  # 攻击目标
    
    player1 = Player(character1)
    player2 = Player(character2)
    player3 = Player(character3)
    
    # 添加玩家到游戏
    game.add_player(player1)
    game.add_player(player2)
    game.add_player(player3)  # 确保添加第三个玩家
    game.current_player_index = 0
    
    # 给player2装备武器
    weapon_card = Card(name="青龙偃月刀", type=CardType.EQUIP, suit="黑桃", rank=5)
    player2.equipped.append(weapon_card)
    player2.weapon = weapon_card
    
    # 给player2一张杀
    sha_card = Card(name="杀", type=CardType.BASIC, suit="红桃", rank=7)
    player2.hand_cards.append(sha_card)
    
    print(f"使用借刀杀人前:")
    print(f"  {character1.name}: 手牌数 {len(player1.hand_cards)}")
    print(f"  {character2.name}: 装备武器 {player2.weapon.name if player2.weapon else '无'}, 手牌数 {len(player2.hand_cards)}")
    print(f"  {character3.name}: 体力 {character3.hp}")
    
    # 测试距离计算
    print(f"\n距离测试:")
    print(f"  游戏中的玩家: {[p.character.name for p in game.players]}")
    print(f"  {character2.name}的攻击范围: {player2.get_attack_range()}")
    print(f"  {character2.name}到{character3.name}的距离: {player2.get_distance_to(player3, game.players)}")
    print(f"  {character2.name}能否攻击{character3.name}: {player2.can_attack(player3, game.players)}")
    
    # 检查攻击目标筛选逻辑
    print(f"\n攻击目标筛选:")
    for p in game.players:
        if p != player2 and p != player1:  # 不能攻击自己和借刀杀人的使用者
            print(f"  候选目标: {p.character.name}, 可攻击: {player2.can_attack(p, game.players)}")
    
    # 创建借刀杀人牌
    jdsr_card = Card(name="借刀杀人", type=CardType.TRICK, suit="梅花", rank=12)
    
    # 创建借刀杀人动作
    jdsr_action = JieDaoShaRenAction()
    
    # 设置测试模式
    game.current_phase = "test"
    
    # 应用借刀杀人效果
    result = jdsr_action.apply_effect(game, player1, player2)
    
    print(f"\n使用借刀杀人后:")
    print(f"  {character1.name}: 手牌数 {len(player1.hand_cards)}")
    print(f"  {character2.name}: 装备武器 {player2.weapon.name if player2.weapon else '无'}, 手牌数 {len(player2.hand_cards)}")
    print(f"  {character3.name}: 体力 {character3.hp}")
    
    if result and character3.hp == 3:
        print("✓ 借刀杀人效果正常工作")
    else:
        print("✗ 借刀杀人效果有问题")

def test_jiedaosharen_no_sha():
    print("\n=== 测试借刀杀人（目标没有杀）===")
    
    # 创建事件管理器
    event_manager = EventManager()
    
    # 创建游戏实例
    game = Game(event_manager)
    
    # 创建角色和玩家
    character1 = Character("张飞", Kingdom.SHU, 4, ["咆哮"])  # 使用者
    character2 = Character("关羽", Kingdom.SHU, 4, ["武圣"])  # 装备武器的角色
    character3 = Character("曹操", Kingdom.WEI, 4, ["奸雄"])  # 攻击目标
    
    player1 = Player(character1)
    player2 = Player(character2)
    player3 = Player(character3)
    
    # 添加玩家到游戏
    game.add_player(player1)
    game.add_player(player2)
    game.add_player(player3)
    game.current_player_index = 0
    
    # 给player2装备武器
    weapon_card = Card(name="青龙偃月刀", type=CardType.EQUIP, suit="黑桃", rank=5)
    player2.equipped.append(weapon_card)
    player2.weapon = weapon_card
    
    # 不给player2杀牌
    
    print(f"使用借刀杀人前:")
    print(f"  {character1.name}: 装备武器 {player1.weapon.name if player1.weapon else '无'}")
    print(f"  {character2.name}: 装备武器 {player2.weapon.name if player2.weapon else '无'}, 手牌数 {len(player2.hand_cards)}")
    print(f"  {character3.name}: 体力 {character3.hp}")
    
    # 创建借刀杀人动作
    jdsr_action = JieDaoShaRenAction()
    
    # 设置测试模式
    game.current_phase = "test"
    
    # 应用借刀杀人效果
    result = jdsr_action.apply_effect(game, player1, player2)
    
    print(f"\n使用借刀杀人后:")
    print(f"  {character1.name}: 装备武器 {player1.weapon.name if player1.weapon else '无'}")
    print(f"  {character2.name}: 装备武器 {player2.weapon.name if player2.weapon else '无'}, 手牌数 {len(player2.hand_cards)}")
    print(f"  {character3.name}: 体力 {character3.hp}")
    
    if result and player1.weapon and player1.weapon.name == "青龙偃月刀":
        print("✓ 借刀杀人（获得武器）效果正常工作")
    else:
        print("✗ 借刀杀人（获得武器）效果有问题")

