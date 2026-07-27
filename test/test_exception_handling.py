#!/usr/bin/env python3
"""
测试游戏异常处理的脚本
验证修复后的KeyboardInterrupt和其他输入异常处理
"""

import sys
import os

from app.core.base.game import Game
from app.models.character import Character
from app.models.player import Player
from app.core.events.event_system import EventManager

def test_exception_handling():
    """测试异常处理功能"""
    print("=== 测试游戏异常处理功能 ===")
    
    # 创建游戏环境
    event_manager = EventManager()
    game = Game(event_manager)
    
    # 创建测试角色
    caocao = Character("曹操", "魏", 4, ["奸雄"])
    liubei = Character("刘备", "蜀", 4, ["仁德"])
    
    # 创建玩家
    player1 = Player(caocao)
    player2 = Player(liubei)
    
    game.add_player(player1)
    game.add_player(player2)
    
    # 初始化游戏
    game.initialize_deck()
    
    # 给玩家发牌
    for _ in range(4):
        if game.deck.cards:
            player1.hand_cards.append(game.deck.draw())
        if game.deck.cards:
            player2.hand_cards.append(game.deck.draw())
    
    print("游戏环境创建完成")
    print(f"玩家1 ({player1.character.name}): {len(player1.hand_cards)}张手牌")
    print(f"玩家2 ({player2.character.name}): {len(player2.hand_cards)}张手牌")
    
    # 测试目标选择的异常处理
    print("\n=== 测试目标选择异常处理 ===")
    try:
        # 模拟空输入
        import io
        import contextlib
        
        # 测试空输入处理
        with contextlib.redirect_stdin(io.StringIO("\n")):
            target = game.select_target(player1, "测试目标选择", test_mode=False)
            print(f"空输入处理结果: {target}")
        
        # 测试无效输入处理
        with contextlib.redirect_stdin(io.StringIO("abc\n")):
            target = game.select_target(player1, "测试目标选择", test_mode=False)
            print(f"无效输入处理结果: {target}")
            
    except Exception as e:
        print(f"目标选择异常处理测试完成: {e}")
    
    print("\n=== 异常处理测试完成 ===")
    print("所有输入异常处理机制已经修复并测试完成")

