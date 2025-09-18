#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
三国杀卡牌系统测试脚本
测试增强的牌堆管理、卡牌显示和实时状态功能
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.models.deck import EnhancedDeck
from app.models.card import Card
from app.ui.card_display import CardDisplayManager, GameDisplayInterface

def test_enhanced_deck():
    """测试增强牌堆功能"""
    print("\n" + "="*50)
    print("测试1: 增强牌堆基本功能")
    print("="*50)
    
    # 创建牌堆
    deck = EnhancedDeck()
    
    # 测试初始状态
    print("\n--- 初始状态测试 ---")
    deck.display_deck_info()
    
    assert deck.get_total_cards_count() > 0, "牌堆应该有卡牌"
    assert deck.get_draw_pile_count() > 0, "摸牌堆应该有卡牌"
    assert deck.get_discard_pile_count() == 0, "弃牌堆应该为空"
    print("✅ 初始状态测试通过")
    
    # 测试摸牌功能
    print("\n--- 摸牌功能测试 ---")
    initial_count = deck.get_draw_pile_count()
    
    # 摸单张牌
    card = deck.draw_card()
    assert card is not None, "应该能摸到卡牌"
    assert deck.get_draw_pile_count() == initial_count - 1, "摸牌堆数量应该减1"
    print(f"✅ 摸到卡牌: {card}")
    
    # 摸多张牌
    cards = deck.draw_cards(5)
    assert len(cards) == 5, "应该摸到5张牌"
    print(f"✅ 摸到5张牌: {[str(c) for c in cards]}")
    
    # 测试弃牌功能
    print("\n--- 弃牌功能测试 ---")
    deck.discard_card(card)
    assert deck.get_discard_pile_count() == 1, "弃牌堆应该有1张牌"
    
    deck.discard_cards(cards[:3])
    assert deck.get_discard_pile_count() == 4, "弃牌堆应该有4张牌"
    print("✅ 弃牌功能测试通过")
    
    # 测试查看牌堆顶
    print("\n--- 查看牌堆顶测试 ---")
    top_card = deck.peek_top_card()
    if top_card:
        print(f"牌堆顶: {top_card}")
        # 摸牌后应该是同一张牌
        drawn_card = deck.draw_card()
        assert str(top_card) == str(drawn_card), "查看的牌堆顶应该与摸到的牌相同"
        print("✅ 查看牌堆顶功能正确")
    
    # 测试重新洗牌
    print("\n--- 重新洗牌测试 ---")
    # 摸完所有牌
    while not deck.is_draw_pile_empty():
        deck.draw_card()
    
    assert deck.is_draw_pile_empty(), "摸牌堆应该为空"
    
    # 再摸一张牌，应该触发重新洗牌
    if not deck.is_discard_pile_empty():
        card = deck.draw_card()
        assert card is not None, "重新洗牌后应该能摸到牌"
        print("✅ 重新洗牌功能正常")
    
    return deck

def test_card_display():
    """测试卡牌显示功能"""
    print("\n" + "="*50)
    print("测试2: 卡牌显示功能")
    print("="*50)
    
    # 创建牌堆和显示管理器
    deck = EnhancedDeck()
    display_manager = CardDisplayManager(deck)
    
    # 测试实时状态获取
    print("\n--- 实时状态测试 ---")
    status = display_manager.get_real_time_status()
    
    required_keys = ['draw_pile', 'discard_pile', 'removed_cards', 'total_cards']
    for key in required_keys:
        assert key in status, f"状态应该包含 {key}"
    
    print("✅ 实时状态获取正常")
    
    # 测试紧凑显示
    print("\n--- 紧凑显示测试 ---")
    compact_display = display_manager.display_compact_status()
    assert "摸牌堆" in compact_display, "紧凑显示应该包含摸牌堆信息"
    print(f"紧凑显示: {compact_display}")
    print("✅ 紧凑显示功能正常")
    
    # 测试详细显示
    print("\n--- 详细显示测试 ---")
    detailed_display = display_manager.display_detailed_status()
    assert "卡牌状态详情" in detailed_display, "详细显示应该包含标题"
    print(detailed_display)
    print("✅ 详细显示功能正常")
    
    # 测试ASCII可视化
    print("\n--- ASCII可视化测试 ---")
    ascii_display = display_manager.display_ascii_visual()
    assert "牌堆可视化" in ascii_display, "ASCII显示应该包含标题"
    print(ascii_display)
    print("✅ ASCII可视化功能正常")
    
    return display_manager

def test_game_interface():
    """测试游戏界面功能"""
    print("\n" + "="*50)
    print("测试3: 游戏界面功能")
    print("="*50)
    
    # 创建游戏界面
    deck = EnhancedDeck()
    game_interface = GameDisplayInterface(deck)
    
    # 模拟玩家手牌
    print("\n--- 玩家手牌测试 ---")
    hand1 = deck.draw_cards(5)
    hand2 = deck.draw_cards(4)
    
    game_interface.update_player_hand("玩家1", hand1)
    game_interface.update_player_hand("玩家2", hand2)
    
    # 测试不同显示模式
    modes = ["compact", "detailed", "visual"]
    for mode in modes:
        display = game_interface.display_game_status(mode)
        assert len(display) > 0, f"{mode}模式显示不应为空"
        print(f"✅ {mode}模式显示正常")
    
    # 测试完整游戏信息
    print("\n--- 完整游戏信息测试 ---")
    full_info = game_interface.display_full_game_info()
    assert "玩家1" in full_info, "完整信息应该包含玩家1"
    assert "玩家2" in full_info, "完整信息应该包含玩家2"
    print(full_info)
    print("✅ 完整游戏信息显示正常")
    
    return game_interface

def test_card_properties():
    """测试卡牌属性功能"""
    print("\n" + "="*50)
    print("测试4: 卡牌属性功能")
    print("="*50)
    
    # 创建测试卡牌
    cards = [
        Card(name="杀", suit="红桃", rank=5, card_type="基本牌", category="basic"),
        Card(name="闪", suit="黑桃", rank=8, card_type="基本牌", category="basic"),
        Card(name="无中生有", suit="红桃", rank=7, card_type="锦囊牌", category="trick"),
        Card(name="青龙偃月刀", suit="黑桃", rank=5, card_type="装备牌", category="equipment", subtype="weapon")
    ]
    
    # 测试颜色判断
    print("\n--- 颜色判断测试 ---")
    assert cards[0].is_red(), "红桃杀应该是红色"
    assert cards[1].is_black(), "黑桃闪应该是黑色"
    print("✅ 颜色判断功能正常")
    
    # 测试类型判断
    print("\n--- 类型判断测试 ---")
    assert cards[0].is_basic_card(), "杀应该是基本牌"
    assert cards[2].is_trick_card(), "无中生有应该是锦囊牌"
    assert cards[3].is_equipment_card(), "青龙偃月刀应该是装备牌"
    assert cards[3].is_weapon(), "青龙偃月刀应该是武器"
    print("✅ 类型判断功能正常")
    
    # 测试显示功能
    print("\n--- 卡牌显示测试 ---")
    for card in cards:
        full_display = card.get_full_display()
        assert len(full_display) > 0, "完整显示不应为空"
        print(f"卡牌显示: {full_display}")
    print("✅ 卡牌显示功能正常")
    
    return cards

def test_edge_cases():
    """测试边界情况"""
    print("\n" + "="*50)
    print("测试5: 边界情况测试")
    print("="*50)
    
    deck = EnhancedDeck()
    
    # 测试空牌堆情况
    print("\n--- 空牌堆测试 ---")
    # 摸完所有牌
    all_cards = []
    while not deck.is_draw_pile_empty() or not deck.is_discard_pile_empty():
        card = deck.draw_card()
        if card:
            all_cards.append(card)
        else:
            break
    
    # 尝试再摸牌
    empty_card = deck.draw_card()
    assert empty_card is None, "空牌堆应该返回None"
    print("✅ 空牌堆处理正常")
    
    # 测试大量操作
    print("\n--- 大量操作测试 ---")
    deck.reset_deck()  # 重置牌堆
    
    for i in range(10):
        cards = deck.draw_cards(3)
        if cards:
            deck.discard_cards(cards[:2])
            if len(cards) > 2:
                deck.remove_card(cards[2])
    
    status = deck.get_deck_status()
    total = status['draw_pile'] + status['discard_pile'] + status['removed_cards']
    print(f"大量操作后总卡牌数: {total}")
    print("✅ 大量操作处理正常")
    
    # 测试警告系统
    print("\n--- 警告系统测试 ---")
    display_manager = CardDisplayManager(deck)
    
    # 制造低卡牌警告
    while deck.get_draw_pile_count() > 3:
        deck.draw_card()
    
    warnings = display_manager.get_warning_messages()
    print(f"警告信息: {warnings}")
    print("✅ 警告系统正常")

def run_performance_test():
    """性能测试"""
    print("\n" + "="*50)
    print("测试6: 性能测试")
    print("="*50)
    
    import time
    
    # 测试大量摸牌弃牌操作的性能
    deck = EnhancedDeck()
    display_manager = CardDisplayManager(deck)
    
    start_time = time.time()
    
    # 执行1000次摸牌弃牌操作
    for i in range(1000):
        card = deck.draw_card()
        if card:
            deck.discard_card(card)
        
        # 每100次获取一次状态
        if i % 100 == 0:
            status = display_manager.get_real_time_status()
    
    end_time = time.time()
    elapsed_time = end_time - start_time
    
    print(f"1000次操作耗时: {elapsed_time:.3f}秒")
    print(f"平均每次操作: {elapsed_time/1000*1000:.3f}毫秒")
    
    if elapsed_time < 1.0:
        print("✅ 性能测试通过")
    else:
        print("⚠️  性能可能需要优化")

def main():
    """主测试函数"""
    print("三国杀卡牌系统综合测试")
    print("="*60)
    
    try:
        # 运行所有测试
        test_enhanced_deck()
        test_card_display()
        test_game_interface()
        test_card_properties()
        test_edge_cases()
        run_performance_test()
        
        print("\n" + "="*60)
        print("🎉 所有测试通过！卡牌系统运行正常")
        print("="*60)
        
        # 显示最终演示
        print("\n=== 最终演示 ===")
        deck = EnhancedDeck()
        game_interface = GameDisplayInterface(deck)
        
        # 模拟游戏场景
        hand1 = deck.draw_cards(4)
        hand2 = deck.draw_cards(4)
        
        game_interface.update_player_hand("玩家1", hand1)
        game_interface.update_player_hand("玩家2", hand2)
        
        print(game_interface.display_full_game_info())
        
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)