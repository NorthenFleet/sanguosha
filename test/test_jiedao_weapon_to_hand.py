#!/usr/bin/env python3
"""
测试借刀杀人中武器转移到手牌的功能
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.base.game import Game
from app.models.card import Card
from app.models.character import Character, Kingdom
from app.models.player import Player
from app.models.deck import Deck
from app.models.card_actions import JieDaoShaRenAction

class MockEventManager:
    def emit(self, event_name, **kwargs):
        pass

def test_jiedao_weapon_to_hand():
    """测试借刀杀人中武器转移到手牌的功能"""
    print("=== 测试借刀杀人武器转移到手牌 ===")
    
    # 创建游戏
    game = Game(MockEventManager())
    game.current_phase = "test"  # 测试模式
    
    # 创建玩家
    player1 = Player(Character("刘备", Kingdom.SHU, 4, []))  # 使用借刀杀人的玩家
    player2 = Player(Character("曹操", Kingdom.WEI, 4, []))  # 装备武器的玩家
    player3 = Player(Character("孙权", Kingdom.WU, 4, []))   # 攻击目标
    
    # 给玩家2装备武器
    weapon = Card(name="青龙偃月刀", category="equipment", subtype="weapon", suit="黑桃", rank=5)
    player2.equipped = [weapon]
    player2.weapon = weapon
    
    # 玩家2没有杀
    player2.hand_cards = []
    
    # 给玩家1借刀杀人
    jiedao = Card(name="借刀杀人", category="trick", subtype="借刀杀人", suit="梅花", rank=12)
    player1.hand_cards = [jiedao]
    
    game.players = [player1, player2, player3]
    game.current_player = player1
    
    # 初始化牌堆
    game.deck = Deck()
    
    print(f"初始状态:")
    print(f"玩家1({player1.character.name})手牌: {[c.name for c in player1.hand_cards]}")
    print(f"玩家2({player2.character.name})装备: {[c.name for c in player2.equipped]}")
    print(f"玩家2({player2.character.name})手牌: {[c.name for c in player2.hand_cards]}")
    
    # 使用借刀杀人
    action = JieDaoShaRenAction()
    
    print("\n执行借刀杀人...")
    result = action.apply_effect(game, player1)
    
    print(f"\n结果:")
    print(f"玩家1({player1.character.name})手牌: {[c.name for c in player1.hand_cards]}")
    print(f"玩家2({player2.character.name})装备: {[c.name for c in player2.equipped]}")
    print(f"玩家2({player2.character.name})手牌: {[c.name for c in player2.hand_cards]}")
    print(f"借刀杀人执行结果: {result}")
    
    # 检查结果：武器应该转移到玩家1的手牌中
    weapon_in_hand = any(c.name == "青龙偃月刀" for c in player1.hand_cards)
    weapon_removed_from_p2 = len(player2.equipped) == 0 and player2.weapon is None
    
    if weapon_in_hand and weapon_removed_from_p2:
        print("✓ 测试通过：武器正确转移到玩家1的手牌中")
        return True
    else:
        print("✗ 测试失败：武器没有正确转移到手牌")
        return False

if __name__ == "__main__":
    test_jiedao_weapon_to_hand()