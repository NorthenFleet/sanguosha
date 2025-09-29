#!/usr/bin/env python3
"""直接测试丈八蛇矛修正的脚本"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.models.player import Player
from app.models.character import Character
from app.models.card import Card
from app.models.card_actions import ZhangBaSheMaoAction, ShaAction
from app.core.events.event_system import EventManager

class TestGame:
    """测试用的游戏类"""
    def __init__(self):
        self.players = []
        self.current_player = None
        self.current_phase = "test"
        self.event_manager = EventManager()
        self.response_called = False
        self.handle_response_called = False
    
    def select_target(self, player, message, test_mode=False):
        """模拟目标选择"""
        for p in self.players:
            if p != player:
                return p
        return None

def test_zhangba_fix():
    """测试丈八蛇矛修正"""
    print("=== 测试丈八蛇矛修正 ===")
    
    # 创建测试游戏
    game = TestGame()
    
    # 创建测试玩家
    char1 = Character("刘备", 4, "蜀", ["仁德", "激将"])
    char2 = Character("曹操", 4, "魏", ["奸雄", "护驾"])
    
    player1 = Player(char1)
    player2 = Player(char2)
    
    # 添加模拟牌堆
    class MockDeck:
        def discard(self, card):
            print(f"卡牌 {card.name} 进入弃牌堆")
    
    game.deck = MockDeck()
    game.players = [player1, player2]
    game.current_player = player1
    
    # 创建测试卡牌
    card1 = Card("红桃", 7, "basic", "桃")
    card2 = Card("黑桃", 8, "basic", "杀")
    
    player1.hand_cards = [card1, card2]
    
    # 装备丈八蛇矛
    zhangba_card = Card("方片", 12, "equipment", "丈八蛇矛")
    player1.weapon = zhangba_card
    player1.equipped = [zhangba_card]
    
    # 创建丈八蛇矛动作
    zhangba_action = ZhangBaSheMaoAction()
    
    # 重写handle_response方法来检测是否被调用
    original_handle_response = zhangba_action.handle_response
    def mock_handle_response(*args, **kwargs):
        print("✅ handle_response 被调用了！")
        game.handle_response_called = True
        return original_handle_response(*args, **kwargs)
    
    zhangba_action.handle_response = mock_handle_response
    
    # 执行丈八蛇矛效果
    print("执行丈八蛇矛效果...")
    try:
        zhangba_action.apply_effect(game, player1, player2)
        if game.handle_response_called:
            print("✅ 修正成功：丈八蛇矛现在会调用handle_response处理对手响应")
            return True
        else:
            print("❌ 修正失败：handle_response未被调用")
            return False
    except Exception as e:
        print(f"执行过程中出现错误: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    result = test_zhangba_fix()
    print(f"\n=== 测试结果 ===")
    if result:
        print("🎉 丈八蛇矛修正验证成功！")
    else:
        print("💥 丈八蛇矛修正验证失败！")