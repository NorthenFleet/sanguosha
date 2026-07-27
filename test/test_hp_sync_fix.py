#!/usr/bin/env python3
"""
测试血量同步修复效果
"""
import sys
import os

from app.core.events.event_system import EventManager
from app.core.base.game import Game
from app.models.character import Character
from app.models.player import Player
from app.models.card import Card
from app.models.enums import CardType
from app.models.card_actions import ShaAction, TaoAction

def test_hp_sync():
    """测试血量同步"""
    print("=== 测试血量同步修复 ===")
    
    # 创建事件管理器
    event_manager = EventManager()
    
    # 创建游戏实例
    game = Game(event_manager)
    
    # 创建角色和玩家
    character1 = Character("张飞", "蜀", 4, ["咆哮"])
    character2 = Character("刘备", "蜀", 4, ["仁德"])
    
    player1 = Player(character1)
    player2 = Player(character2)
    
    # 添加玩家到游戏
    game.add_player(player1)
    game.add_player(player2)
    game.current_player_index = 0
    
    print(f"初始状态:")
    print(f"  {character1.name}: Character.hp={character1.hp}, Player.hp={player1.hp}")
    print(f"  {character2.name}: Character.hp={character2.hp}, Player.hp={player2.hp}")
    
    # 测试伤害处理
    print(f"\n--- 测试伤害处理 ---")
    sha_action = ShaAction()
    print(f"使用杀前:")
    print(f"  {character2.name}: Character.hp={character2.hp}, Player.hp={player2.hp}")
    
    # 直接调用apply_default_effect来测试伤害系统
    sha_action.apply_default_effect(game, player1, player2)
    
    print(f"使用杀后:")
    print(f"  {character2.name}: Character.hp={character2.hp}, Player.hp={player2.hp}")
    
    # 验证血量同步
    if character2.hp == player2.hp == 3:
        print("✓ 伤害处理血量同步正常")
    else:
        print("✗ 伤害处理血量同步有问题")
        print(f"  Character.hp={character2.hp}, Player.hp={player2.hp}")
    
    # 测试桃的回复
    print(f"\n--- 测试桃的回复 ---")
    tao_action = TaoAction()
    print(f"使用桃前:")
    print(f"  {character2.name}: Character.hp={character2.hp}, Player.hp={player2.hp}")
    
    tao_action.apply_effect(game, player2, player2)
    
    print(f"使用桃后:")
    print(f"  {character2.name}: Character.hp={character2.hp}, Player.hp={player2.hp}")
    
    # 验证血量同步
    if character2.hp == player2.hp == 4:
        print("✓ 桃的回复血量同步正常")
    else:
        print("✗ 桃的回复血量同步有问题")
        print(f"  Character.hp={character2.hp}, Player.hp={player2.hp}")
    
    print("\n血量同步测试完成")

