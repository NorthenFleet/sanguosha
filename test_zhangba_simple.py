#!/usr/bin/env python3
"""简化的丈八蛇矛测试脚本"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.models.player import Player
from app.models.character import Character
from app.models.card import Card
from app.models.card_actions import ZhangBaSheMaoAction, ShaAction
from app.core.events.event_manager import EventManager

class MockGame:
    """模拟游戏类，避免复杂的初始化"""
    def __init__(self):
        self.players = []
        self.current_player = None
        self.current_phase = "test"
        self.event_manager = EventManager()
        self.deck = MockDeck()
    
    def select_target(self, player, message, test_mode=False):
        """模拟目标选择"""
        # 返回另一个玩家作为目标
        for p in self.players:
            if p != player:
                return p
        return None
    
    def get_opponent(self, player):
        """获取对手"""
        for p in self.players:
            if p != player:
                return p
        return None

class MockDeck:
    """模拟牌堆类"""
    def __init__(self):
        self.discard_pile = []
    
    def discard(self, card):
        """将卡牌放入弃牌堆"""
        self.discard_pile.append(card)
        print(f"卡牌 {card.name} 进入弃牌堆")

def test_zhangba_response():
    """测试丈八蛇矛发动后的完整杀流程"""
    print("=== 测试丈八蛇矛修正后的响应流程 ===")
    
    # 创建模拟游戏
    game = MockGame()
    
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
    
    # 记录初始状态
    initial_p1_cards = len(player1.hand_cards)
    initial_p2_cards = len(player2.hand_cards)
    initial_p2_hp = player2.character.hp
    
    # 测试丈八蛇矛发动
    zhangba_action = ZhangBaSheMaoAction()
    
    print(f"\n--- 测试丈八蛇矛发动 ---")
    print(f"{player1.character.name} 发动丈八蛇矛...")
    
    # 执行丈八蛇矛效果
    result = zhangba_action.apply_effect(game, player1, player2)
    
    print(f"\n--- 测试结果 ---")
    print(f"丈八蛇矛执行结果: {result}")
    print(f"{player1.character.name} 剩余手牌: {[c.name for c in player1.hand_cards]} ({len(player1.hand_cards)}张)")
    print(f"{player2.character.name} 剩余手牌: {[c.name for c in player2.hand_cards]} ({len(player2.hand_cards)}张)")
    print(f"{player2.character.name} 当前血量: {player2.character.hp}")
    print(f"弃牌堆: {[c.name for c in game.deck.discard_pile]} ({len(game.deck.discard_pile)}张)")
    
    # 分析结果
    cards_used = initial_p1_cards - len(player1.hand_cards)
    opponent_cards_used = initial_p2_cards - len(player2.hand_cards)
    hp_lost = initial_p2_hp - player2.character.hp
    
    print(f"\n--- 分析 ---")
    print(f"刘备使用了 {cards_used} 张手牌")
    print(f"曹操使用了 {opponent_cards_used} 张手牌")
    print(f"曹操失去了 {hp_lost} 点血量")
    
    # 判断是否正确处理了响应
    if opponent_cards_used > 0:
        print("✅ 对手进行了响应，丈八蛇矛修正成功！")
        return True
    elif hp_lost > 0:
        print("✅ 对手没有响应，受到了伤害，流程正确！")
        return True
    else:
        print("❌ 丈八蛇矛没有正确执行杀的流程")
        return False

def test_sha_direct():
    """测试普通杀的直接调用"""
    print("\n=== 测试普通杀的直接调用（对比） ===")
    
    # 创建模拟游戏
    game = MockGame()
    
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
    
    # 记录初始状态
    initial_p2_cards = len(player2.hand_cards)
    initial_p2_hp = player2.character.hp
    
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
    print(f"{player2.character.name} 剩余手牌: {[c.name for c in player2.hand_cards]} ({len(player2.hand_cards)}张)")
    print(f"{player2.character.name} 当前血量: {player2.character.hp}")
    
    # 分析结果
    opponent_cards_used = initial_p2_cards - len(player2.hand_cards)
    hp_lost = initial_p2_hp - player2.character.hp
    
    print(f"\n--- 分析 ---")
    print(f"曹操使用了 {opponent_cards_used} 张手牌")
    print(f"曹操失去了 {hp_lost} 点血量")
    
    return result

if __name__ == "__main__":
    try:
        # 测试丈八蛇矛修正后的流程
        zhangba_result = test_zhangba_response()
        
        # 测试普通杀的流程作为对比
        sha_result = test_sha_direct()
        
        print(f"\n=== 总结 ===")
        print(f"丈八蛇矛测试: {'通过' if zhangba_result else '失败'}")
        print(f"普通杀测试: {'通过' if sha_result is not None else '失败'}")
        
        if zhangba_result:
            print("✅ 丈八蛇矛修正成功，现在能正确处理对手响应！")
        else:
            print("❌ 丈八蛇矛仍有问题，需要进一步检查")
            
    except Exception as e:
        print(f"测试过程中出现错误: {e}")
        import traceback
        traceback.print_exc()