#!/usr/bin/env python3
"""最终测试丈八蛇矛修正的脚本"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.models.player import Player
from app.models.character import Character
from app.models.card import Card
from app.models.card_actions import ZhangBaSheMaoAction, ShaAction
from app.core.events.event_system import EventManager

def test_zhangba_response_fix():
    """测试丈八蛇矛修正后是否调用handle_response"""
    print("=== 测试丈八蛇矛修正 ===")
    
    # 创建测试环境
    event_manager = EventManager()
    
    class TestGame:
        def __init__(self):
            self.players = []
            self.current_player = None
            self.current_phase = "test"
            self.event_manager = event_manager
            self.deck = TestDeck()
            self.handle_response_called = False
        
        def select_target(self, player, message, test_mode=False):
            for p in self.players:
                if p != player:
                    return p
            return None
    
    class TestDeck:
        def discard(self, card):
            print(f"卡牌 {card.name} 进入弃牌堆")
    
    # 创建游戏和玩家
    game = TestGame()
    
    char1 = Character("刘备", 4, "蜀", ["仁德", "激将"])
    char2 = Character("曹操", 4, "魏", ["奸雄", "护驾"])
    
    player1 = Player(char1)
    player2 = Player(char2)
    
    game.players = [player1, player2]
    game.current_player = player1
    
    # 为玩家1装备丈八蛇矛并添加手牌
    zhangba_card = Card(name="丈八蛇矛", category="equipment", suit="方片", point=12, subtype="weapon")
    player1.weapon = zhangba_card
    player1.equipped = [zhangba_card]
    
    card1 = Card(name="桃", category="basic", suit="红桃", point=7)
    card2 = Card(name="杀", category="basic", suit="黑桃", point=8)
    player1.hand_cards = [card1, card2]
    
    # 创建丈八蛇矛动作并监控handle_response调用
    zhangba_action = ZhangBaSheMaoAction()
    
    # 重写handle_response方法来检测调用
    original_handle_response = zhangba_action.handle_response
    def mock_handle_response(*args, **kwargs):
        print("✅ handle_response 被调用了！")
        game.handle_response_called = True
        # 模拟返回True表示成功处理
        return True
    
    zhangba_action.handle_response = mock_handle_response
    
    # 执行测试
    print("执行丈八蛇矛效果...")
    print(f"玩家1武器: {player1.weapon.name if player1.weapon else '无'}")
    print(f"玩家1手牌数: {len(player1.hand_cards)}")
    
    try:
        result = zhangba_action.apply_effect(game, player1, player2)
        
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
    result = test_zhangba_response_fix()
    print(f"\n=== 测试结果 ===")
    if result:
        print("🎉 丈八蛇矛修正验证成功！现在能正确处理对手响应流程！")
    else:
        print("💥 丈八蛇矛修正验证失败！")