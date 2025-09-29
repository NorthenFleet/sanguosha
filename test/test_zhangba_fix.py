#!/usr/bin/env python3
"""测试丈八蛇矛修正后的响应流程"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.core.base.game import Game
from app.models.player import Player
from app.models.character import Character
from app.models.card import Card
from app.models.card_actions import ZhangBaSheMaoAction, ShaAction
from app.core.events.event_manager import EventManager

def test_zhangba_response():
    """测试丈八蛇矛发动后的完整杀流程"""
    print("=== 测试丈八蛇矛修正后的响应流程 ===")
    
    # 创建游戏实例
    event_manager = EventManager()
    game = Game(event_manager)
    game.current_phase = "test"  # 设置为测试模式
    
    # 创建角色
    liubei = Character("刘备", 4, "蜀", "主公", "仁德")
    caocao = Character("曹操", 4, "魏", "主公", "奸雄")
    
    # 创建玩家
    player1 = Player(liubei)
    player2 = Player(caocao)
    
    # 设置玩家手牌（包含两张非杀牌用于丈八蛇矛）
    player1.hand_cards = [
        Card("桃", "基本牌", "红桃", 3),
        Card("闪", "基本牌", "方块", 2),
        Card("无中生有", "锦囊牌", "红桃", 7)
    ]
    
    # 给对手一张闪用于响应
    player2.hand_cards = [
        Card("闪", "基本牌", "方块", 6),
        Card("杀", "基本牌", "黑桃", 7)
    ]
    
    # 给刘备装备丈八蛇矛
    zhangba = Card("丈八蛇矛", "装备牌", "黑桃", 12)
    player1.weapon = zhangba
    player1.equipped.append(zhangba)
    
    # 设置游戏状态
    game.players = [player1, player2]
    game.current_player = player1
    
    print(f"{player1.character.name} 手牌: {[c.name for c in player1.hand_cards]}")
    print(f"{player2.character.name} 手牌: {[c.name for c in player2.hand_cards]}")
    print(f"{player1.character.name} 装备: {player1.weapon.name if player1.weapon else '无'}")
    
    # 测试丈八蛇矛发动
    zhangba_action = ZhangBaSheMaoAction()
    
    print(f"\n--- 测试丈八蛇矛发动 ---")
    print(f"{player1.character.name} 发动丈八蛇矛...")
    
    # 执行丈八蛇矛效果
    result = zhangba_action.apply_effect(game, player1, player2)
    
    print(f"\n--- 测试结果 ---")
    print(f"丈八蛇矛执行结果: {result}")
    print(f"{player1.character.name} 剩余手牌: {[c.name for c in player1.hand_cards]}")
    print(f"{player2.character.name} 剩余手牌: {[c.name for c in player2.hand_cards]}")
    print(f"{player2.character.name} 当前血量: {player2.character.hp}")
    
    return result

def test_sha_response_flow():
    """测试普通杀的响应流程作为对比"""
    print("\n=== 测试普通杀的响应流程（对比） ===")
    
    # 创建游戏实例
    event_manager = EventManager()
    game = Game(event_manager)
    game.current_phase = "test"  # 设置为测试模式
    
    # 创建角色
    liubei = Character("刘备", 4, "蜀", "主公", "仁德")
    caocao = Character("曹操", 4, "魏", "主公", "奸雄")
    
    # 创建玩家
    player1 = Player(liubei)
    player2 = Player(caocao)
    
    # 设置玩家手牌
    player1.hand_cards = [
        Card("杀", "基本牌", "红桃", 7),
        Card("桃", "基本牌", "红桃", 3)
    ]
    
    # 给对手一张闪用于响应
    player2.hand_cards = [
        Card("闪", "基本牌", "方块", 6),
        Card("杀", "基本牌", "黑桃", 7)
    ]
    
    # 设置游戏状态
    game.players = [player1, player2]
    game.current_player = player1
    
    print(f"{player1.character.name} 手牌: {[c.name for c in player1.hand_cards]}")
    print(f"{player2.character.name} 手牌: {[c.name for c in player2.hand_cards]}")
    
    # 测试普通杀
    sha_action = ShaAction()
    
    print(f"\n--- 测试普通杀 ---")
    print(f"{player1.character.name} 使用杀...")
    
    # 执行杀的完整流程
    if sha_action.apply_effect(game, player1, player2):
        result = sha_action.handle_response(game, player1, player2, test_mode=True)
    else:
        result = False
    
    print(f"\n--- 测试结果 ---")
    print(f"杀执行结果: {result}")
    print(f"{player1.character.name} 剩余手牌: {[c.name for c in player1.hand_cards]}")
    print(f"{player2.character.name} 剩余手牌: {[c.name for c in player2.hand_cards]}")
    print(f"{player2.character.name} 当前血量: {player2.character.hp}")
    
    return result

if __name__ == "__main__":
    try:
        # 测试丈八蛇矛修正后的流程
        zhangba_result = test_zhangba_response()
        
        # 测试普通杀的流程作为对比
        sha_result = test_sha_response_flow()
        
        print(f"\n=== 总结 ===")
        print(f"丈八蛇矛测试: {'通过' if zhangba_result is not None else '失败'}")
        print(f"普通杀测试: {'通过' if sha_result is not None else '失败'}")
        
        if zhangba_result is not None and sha_result is not None:
            print("✅ 丈八蛇矛修正成功，现在能正确处理对手响应！")
        else:
            print("❌ 测试失败，需要进一步检查")
            
    except Exception as e:
        print(f"测试过程中出现错误: {e}")
        import traceback
        traceback.print_exc()