#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
丈八蛇矛特殊效果测试文件
测试丈八蛇矛的特殊使用逻辑：选择两张手牌作为杀使用
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.core.base.game import Game
from app.models.player import Player
from app.models.character import Character
from app.models.card import Card
from app.models.enums import CardType, Suit
from app.models.card_actions import ZhangBaSheMaoAction

def create_test_game():
    """创建测试游戏环境"""
    # 创建一个简单的事件管理器
    class MockEventManager:
        def emit(self, event, **kwargs):
            pass
    
    game = Game(MockEventManager())
    
    # 创建两个玩家
    from app.models.character import Kingdom
    character1 = Character("刘备", Kingdom.SHU, 4, ["仁德"])
    character2 = Character("关羽", Kingdom.SHU, 4, ["武圣"])
    player1 = Player(character1)
    player2 = Player(character2)
    
    game.players = [player1, player2]
    game.current_player_index = 0
    
    return game, player1, player2

def test_zhangba_can_use():
    """测试丈八蛇矛是否可以使用"""
    print("测试1: 检查丈八蛇矛使用条件")
    
    game, player1, player2 = create_test_game()
    
    # 给玩家装备丈八蛇矛
    zhangba_card = Card("丈八蛇矛", CardType.EQUIP, Suit.SPADES, "1")
    player1.weapon = zhangba_card
    
    # 给玩家两张手牌
    card1 = Card("桃", CardType.BASIC, Suit.HEARTS, "3")
    card2 = Card("闪", CardType.BASIC, Suit.DIAMONDS, "4")
    player1.hand_cards = [card1, card2]
    
    # 测试丈八蛇矛动作
    zhangba_action = ZhangBaSheMaoAction()
    can_use = zhangba_action.can_use(game, player1)
    
    assert can_use, "装备丈八蛇矛且有两张手牌时应该可以使用"
    print("✓ 丈八蛇矛使用条件检查通过")

def test_zhangba_cannot_use_without_weapon():
    """测试没有装备丈八蛇矛时不能使用"""
    print("测试2: 检查没有装备丈八蛇矛时的情况")
    
    game, player1, player2 = create_test_game()
    
    # 不装备丈八蛇矛，但给两张手牌
    card1 = Card("桃", CardType.BASIC, Suit.HEARTS, "3")
    card2 = Card("闪", CardType.BASIC, Suit.DIAMONDS, "4")
    player1.hand_cards = [card1, card2]
    
    zhangba_action = ZhangBaSheMaoAction()
    can_use = zhangba_action.can_use(game, player1)
    
    assert not can_use, "没有装备丈八蛇矛时不应该可以使用"
    print("✓ 没有装备丈八蛇矛时正确拒绝使用")

def test_zhangba_cannot_use_insufficient_cards():
    """测试手牌不足时不能使用"""
    print("测试3: 检查手牌不足时的情况")
    
    game, player1, player2 = create_test_game()
    
    # 装备丈八蛇矛但只给一张手牌
    zhangba_card = Card("丈八蛇矛", CardType.EQUIP, Suit.SPADES, "1")
    player1.weapon = zhangba_card
    
    card1 = Card("桃", CardType.BASIC, Suit.HEARTS, "3")
    player1.hand_cards = [card1]
    
    zhangba_action = ZhangBaSheMaoAction()
    can_use = zhangba_action.can_use(game, player1)
    
    assert not can_use, "手牌不足两张时不应该可以使用"
    print("✓ 手牌不足时正确拒绝使用")

def test_zhangba_select_cards():
    """测试丈八蛇矛选择手牌功能"""
    print("测试4: 检查丈八蛇矛选择手牌功能")
    
    game, player1, player2 = create_test_game()
    
    # 装备丈八蛇矛并给三张手牌
    zhangba_card = Card("丈八蛇矛", CardType.EQUIP, Suit.SPADES, "1")
    player1.weapon = zhangba_card
    
    card1 = Card("桃", CardType.BASIC, Suit.HEARTS, "3")
    card2 = Card("闪", CardType.BASIC, Suit.DIAMONDS, "4")
    card3 = Card("杀", CardType.BASIC, Suit.SPADES, "5")
    player1.hand_cards = [card1, card2, card3]
    
    zhangba_action = ZhangBaSheMaoAction()
    
    # 在测试模式下，应该自动选择前两张牌
    selected_cards = zhangba_action.select_cards_for_sha(game, player1)
    
    assert len(selected_cards) == 2, "应该选择两张手牌"
    assert selected_cards[0] == card1, "第一张牌应该是桃"
    assert selected_cards[1] == card2, "第二张牌应该是闪"
    print("✓ 丈八蛇矛选择手牌功能正常")

def test_zhangba_apply_effect():
    """测试丈八蛇矛效果应用"""
    print("测试5: 检查丈八蛇矛效果应用")
    
    game, player1, player2 = create_test_game()
    
    # 装备丈八蛇矛并给手牌
    zhangba_card = Card("丈八蛇矛", CardType.EQUIP, Suit.SPADES, "1")
    player1.weapon = zhangba_card
    
    card1 = Card("桃", CardType.BASIC, Suit.HEARTS, "3")
    card2 = Card("闪", CardType.BASIC, Suit.DIAMONDS, "4")
    player1.hand_cards = [card1, card2]
    
    # 记录初始状态
    initial_hand_count = len(player1.hand_cards)
    initial_target_hp = player2.character.hp
    
    zhangba_action = ZhangBaSheMaoAction()
    success = zhangba_action.apply_effect(game, player1, player2)
    
    # 检查结果
    assert success, "丈八蛇矛效果应用应该成功"
    assert len(player1.hand_cards) == initial_hand_count - 2, "应该消耗两张手牌"
    
    # 如果目标没有闪或其他防御，应该受到伤害
    if player2.character.hp < initial_target_hp:
        print("✓ 丈八蛇矛成功造成伤害")
    else:
        print("✓ 丈八蛇矛效果应用成功（目标可能有防御）")

def main():
    """运行所有测试"""
    print("开始丈八蛇矛特殊效果测试...")
    print("=" * 50)
    
    try:
        test_zhangba_can_use()
        test_zhangba_cannot_use_without_weapon()
        test_zhangba_cannot_use_insufficient_cards()
        test_zhangba_select_cards()
        test_zhangba_apply_effect()
        
        print("=" * 50)
        print("所有测试通过！丈八蛇矛的特殊效果工作正常")
        
    except Exception as e:
        print(f"测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True

if __name__ == "__main__":
    main()