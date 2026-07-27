#!/usr/bin/env python3
"""
测试修复后的借刀杀人逻辑 - 2人游戏场景
"""

import sys
import os

from app.models.player import Player
from app.models.character import Character, Kingdom
from app.models.card import Card
from app.models.deck import Deck
from app.core.events.event_system import EventManager
from app.core.base.game import Game
from app.models.card_actions import JieDaoShaRenAction

class MockEventManager:
    def __init__(self):
        pass
    
    def emit(self, event_type, data=None):
        pass
    
    def trigger(self, event_type, data=None):
        pass

def test_jiedao_2player_with_sha():
    """测试2人游戏中借刀杀人 - 目标有杀的情况"""
    print("=== 测试2人游戏借刀杀人（目标有杀）===")
    
    # 创建游戏
    game = Game(MockEventManager())
    game.current_phase = "test"  # 测试模式
    
    # 创建玩家
    player1 = Player(Character("刘备", Kingdom.SHU, 4, []))  # 使用借刀杀人的玩家
    player2 = Player(Character("曹操", Kingdom.WEI, 4, []))  # 装备武器的玩家
    
    # 给玩家2装备武器
    weapon = Card(name="丈八蛇矛", category="equipment", subtype="weapon")
    player2.equipped = [weapon]
    player2.weapon = weapon
    
    # 给玩家2一张杀
    sha_card = Card("杀", "基本", "杀")
    player2.hand_cards = [sha_card]
    
    # 给玩家1借刀杀人
    jiedao = Card("借刀杀人", "锦囊", "借刀杀人")
    player1.hand_cards = [jiedao]
    
    game.players = [player1, player2]
    game.current_player = player1
    
    # 初始化牌堆
    game.deck = Deck()
    
    # 为牌堆添加discard方法（向后兼容）
    if not hasattr(game.deck, 'discard'):
        game.deck.discard = game.deck.discard_card
    
    print(f"玩家1({player1.character.name})手牌: {[c.name for c in player1.hand_cards]}")
    print(f"玩家2({player2.character.name})装备: {[c.name for c in player2.equipped]}")
    print(f"玩家2({player2.character.name})手牌: {[c.name for c in player2.hand_cards]}")
    print(f"玩家1血量: {player1.hp}")
    
    # 使用借刀杀人
    action = JieDaoShaRenAction()
    
    print("\n执行借刀杀人...")
    result = action.apply_effect(game, player1)
    
    print(f"\n结果:")
    print(f"玩家2手牌: {[c.name for c in player2.hand_cards]}")
    print(f"玩家1血量: {player1.hp}")
    print(f"借刀杀人执行结果: {result}")
    
    # 检查结果
    assert len(player2.hand_cards) == 0, "玩家2没有使用杀"
    print("✓ 测试通过：玩家2使用了杀攻击玩家1")

def test_jiedao_2player_no_sha():
    """测试2人游戏中借刀杀人 - 目标没有杀的情况"""
    print("\n=== 测试2人游戏借刀杀人（目标没有杀）===")
    
    # 创建游戏
    game = Game(MockEventManager())
    game.current_phase = "test"  # 测试模式
    
    # 创建玩家
    player1 = Player(Character("刘备", Kingdom.SHU, 4, []))  # 使用借刀杀人的玩家
    player2 = Player(Character("曹操", Kingdom.WEI, 4, []))  # 装备武器的玩家
    
    # 给玩家2装备武器
    weapon = Card(name="丈八蛇矛", category="equipment", subtype="weapon")
    player2.equipped = [weapon]
    player2.weapon = weapon
    
    # 玩家2没有杀
    player2.hand_cards = []
    
    # 给玩家1借刀杀人
    jiedao = Card("借刀杀人", "锦囊", "借刀杀人")
    player1.hand_cards = [jiedao]
    
    game.players = [player1, player2]
    game.current_player = player1
    
    # 初始化牌堆
    game.deck = Deck()
    
    # 为牌堆添加discard方法（向后兼容）
    if not hasattr(game.deck, 'discard'):
        game.deck.discard = game.deck.discard_card
    
    print(f"玩家1({player1.character.name})手牌: {[c.name for c in player1.hand_cards]}")
    print(f"玩家2({player2.character.name})装备: {[c.name for c in player2.equipped]}")
    print(f"玩家2({player2.character.name})手牌: {[c.name for c in player2.hand_cards]}")
    print(f"玩家1装备: {[c.name for c in player1.equipped]}")
    
    # 使用借刀杀人
    action = JieDaoShaRenAction()
    
    print("\n执行借刀杀人...")
    result = action.apply_effect(game, player1)
    
    print(f"\n结果:")
    print(f"玩家2装备: {[c.name for c in player2.equipped]}")
    print(f"玩家1装备: {[c.name for c in player1.equipped]}")
    print(f"借刀杀人执行结果: {result}")
    
    # 检查结果：武器应进入使用者手牌，而不是自动装备。
    assert not player2.equipped and player2.weapon is None
    assert any(card.name == "丈八蛇矛" for card in player1.hand_cards), "武器没有转移到手牌"
    print("✓ 测试通过：武器转移到玩家1手牌")
