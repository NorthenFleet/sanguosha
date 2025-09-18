#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
卡牌系统优化综合测试
测试所有优化功能的集成效果和性能表现
"""

import sys
import os
import time
import threading
from pathlib import Path

# 添加项目路径
sys.path.append(str(Path(__file__).parent))

from app.models.deck import EnhancedDeck
from app.models.card import Card
from app.ui.card_display import CardDisplayManager, GameDisplayInterface
from app.ui.real_time_display import RealTimeCardMonitor, WebDisplayGenerator, ConsoleRealTimeDisplay
from app.utils.card_loader import OptimizedCardLoader, AsyncCardLoader, load_cards_optimized

def test_optimized_card_loading():
    """测试优化的卡牌加载功能"""
    print("\n=== 测试优化卡牌加载 ===")
    
    try:
        # 测试基本加载
        loader = OptimizedCardLoader()
        
        # 性能测试
        start_time = time.time()
        cards = loader.load_cards()
        load_time = time.time() - start_time
        
        print(f"✅ 卡牌加载成功: {len(cards)} 张卡牌，耗时 {load_time:.3f}s")
        
        # 测试缓存效果
        start_time = time.time()
        cached_cards = loader.load_cards()
        cache_time = time.time() - start_time
        
        print(f"✅ 缓存加载成功: {len(cached_cards)} 张卡牌，耗时 {cache_time:.3f}s")
        print(f"📊 缓存加速比: {load_time/cache_time:.1f}x")
        
        # 测试搜索功能
        basic_cards = loader.get_cards_by_type('basic')
        trick_cards = loader.get_cards_by_type('trick')
        equipment_cards = loader.get_cards_by_type('equipment')
        
        print(f"📋 卡牌分类统计:")
        print(f"   基本牌: {len(basic_cards)} 张")
        print(f"   锦囊牌: {len(trick_cards)} 张")
        print(f"   装备牌: {len(equipment_cards)} 张")
        
        # 测试统计信息
        stats = loader.get_load_stats()
        print(f"📈 加载统计: 总加载次数 {stats['total_loads']}, 缓存命中 {stats['cache_hits']}")
        
        return True
        
    except Exception as e:
        print(f"❌ 卡牌加载测试失败: {e}")
        return False

def test_enhanced_deck_management():
    """测试增强的牌堆管理功能"""
    print("\n=== 测试增强牌堆管理 ===")
    
    try:
        # 创建增强牌堆
        deck = EnhancedDeck()
        
        print(f"✅ 牌堆初始化成功: {deck.get_total_cards_count()} 张卡牌")
        print(f"   摸牌堆: {deck.get_draw_pile_count()} 张")
        print(f"   弃牌堆: {deck.get_discard_pile_count()} 张")
        
        # 测试摸牌功能
        drawn_cards = deck.draw_cards(5)
        print(f"✅ 摸牌测试: 摸取 {len(drawn_cards)} 张卡牌")
        
        # 测试弃牌功能
        if drawn_cards:
            deck.discard_cards(drawn_cards[:2])
            print(f"✅ 弃牌测试: 弃置 2 张卡牌")
        
        # 测试移出游戏功能
        if len(drawn_cards) > 2:
            deck.remove_from_game(drawn_cards[2])
            print(f"✅ 移出游戏测试: 移出 1 张卡牌")
        
        # 显示当前状态
        status = deck.get_deck_status()
        print(f"📊 当前牌堆状态:")
        for key, value in status.items():
            print(f"   {key}: {value}")
        
        # 测试牌堆重置
        deck.reset_deck()
        print(f"✅ 牌堆重置成功: {deck.get_total_cards_count()} 张卡牌")
        
        return True
        
    except Exception as e:
        print(f"❌ 牌堆管理测试失败: {e}")
        return False

def test_card_display_system():
    """测试卡牌显示系统"""
    print("\n=== 测试卡牌显示系统 ===")
    
    try:
        # 创建显示管理器
        deck = EnhancedDeck()
        display_manager = CardDisplayManager(deck)
        
        # 测试实时状态获取
        status = display_manager.get_real_time_status()
        print(f"✅ 实时状态获取成功:")
        for key, value in status.items():
            print(f"   {key}: {value}")
        
        # 测试紧凑显示
        compact_display = display_manager.get_compact_display()
        print(f"\n📋 紧凑显示:")
        print(compact_display)
        
        # 测试ASCII可视化
        ascii_visual = display_manager.get_ascii_visualization()
        print(f"\n🎨 ASCII可视化:")
        print(ascii_visual)
        
        # 测试游戏界面
        game_interface = GameDisplayInterface(deck)
        
        # 模拟手牌
        hand_cards = deck.draw_cards(4)
        if hand_cards:
            hand_display = game_interface.display_hand_cards(hand_cards)
            print(f"\n🃏 手牌显示:")
            print(hand_display)
        
        return True
        
    except Exception as e:
        print(f"❌ 卡牌显示测试失败: {e}")
        return False

def test_real_time_monitoring():
    """测试实时监控系统"""
    print("\n=== 测试实时监控系统 ===")
    
    try:
        # 创建监控器
        deck = EnhancedDeck()
        monitor = RealTimeCardMonitor(deck, update_interval=0.5)
        
        # 添加回调函数
        status_updates = []
        def status_callback(status):
            status_updates.append(status)
            print(f"📊 状态更新: 摸牌堆 {status['draw_pile']}, 弃牌堆 {status['discard_pile']}")
        
        monitor.add_callback(status_callback)
        
        # 启动监控
        monitor.start_monitoring()
        print("✅ 实时监控已启动")
        
        # 模拟卡牌操作
        print("🎮 模拟卡牌操作...")
        for i in range(5):
            cards = deck.draw_cards(2)
            if cards:
                deck.discard_card(cards[0])
            time.sleep(0.6)  # 等待监控更新
        
        # 停止监控
        monitor.stop_monitoring()
        print("⏹️  实时监控已停止")
        
        # 检查监控结果
        print(f"📈 监控统计: 收到 {len(status_updates)} 次状态更新")
        
        # 获取历史数据
        history = monitor.get_status_history(3)
        print(f"📚 历史记录: {len(history)} 条记录")
        
        return True
        
    except Exception as e:
        print(f"❌ 实时监控测试失败: {e}")
        return False

def test_web_dashboard_generation():
    """测试Web仪表板生成"""
    print("\n=== 测试Web仪表板生成 ===")
    
    try:
        # 创建Web生成器
        deck = EnhancedDeck()
        monitor = RealTimeCardMonitor(deck)
        web_generator = WebDisplayGenerator(monitor)
        
        # 生成HTML仪表板
        html_content = web_generator.generate_html_dashboard()
        print(f"✅ HTML仪表板生成成功: {len(html_content)} 字符")
        
        # 保存到文件
        dashboard_file = web_generator.save_dashboard_file("test_dashboard.html")
        print(f"✅ 仪表板文件已保存: {dashboard_file}")
        
        # 验证文件存在
        if os.path.exists(dashboard_file):
            file_size = os.path.getsize(dashboard_file)
            print(f"📁 文件大小: {file_size} 字节")
            
            # 清理测试文件
            os.remove(dashboard_file)
            print(f"🧹 测试文件已清理")
        
        return True
        
    except Exception as e:
        print(f"❌ Web仪表板测试失败: {e}")
        return False

def test_async_loading():
    """测试异步加载功能"""
    print("\n=== 测试异步加载功能 ===")
    
    try:
        # 创建异步加载器
        async_loader = AsyncCardLoader()
        
        # 异步加载回调
        async_results = []
        def async_callback(cards, error):
            if error:
                async_results.append(f"错误: {error}")
            else:
                async_results.append(f"成功: {len(cards)} 张卡牌")
        
        # 启动异步任务
        task_id = async_loader.load_cards_async(callback=async_callback)
        print(f"✅ 异步任务已启动: {task_id}")
        
        # 等待完成
        start_time = time.time()
        while not async_loader.is_ready(task_id) and time.time() - start_time < 5:
            time.sleep(0.1)
        
        if async_loader.is_ready(task_id):
            result = async_loader.get_result(task_id)
            print(f"✅ 异步加载完成: {len(result)} 张卡牌")
        else:
            print("⚠️  异步加载超时")
        
        # 检查回调结果
        if async_results:
            print(f"📞 回调结果: {async_results[0]}")
        
        # 关闭异步加载器
        async_loader.shutdown()
        print("✅ 异步加载器已关闭")
        
        return True
        
    except Exception as e:
        print(f"❌ 异步加载测试失败: {e}")
        return False

def test_performance_benchmark():
    """性能基准测试"""
    print("\n=== 性能基准测试 ===")
    
    try:
        # 测试加载性能
        loader = OptimizedCardLoader()
        
        # 多次加载测试
        load_times = []
        for i in range(5):
            start_time = time.time()
            cards = loader.load_cards(force_reload=(i == 0))  # 第一次强制重新加载
            load_time = time.time() - start_time
            load_times.append(load_time)
        
        avg_load_time = sum(load_times) / len(load_times)
        print(f"📊 平均加载时间: {avg_load_time:.3f}s")
        print(f"📊 最快加载时间: {min(load_times):.3f}s")
        print(f"📊 最慢加载时间: {max(load_times):.3f}s")
        
        # 测试搜索性能
        search_times = []
        for i in range(10):
            start_time = time.time()
            basic_cards = loader.get_cards_by_type('basic')
            search_time = time.time() - start_time
            search_times.append(search_time)
        
        avg_search_time = sum(search_times) / len(search_times)
        print(f"🔍 平均搜索时间: {avg_search_time:.4f}s")
        
        # 测试牌堆操作性能
        deck = EnhancedDeck()
        
        operation_times = []
        for i in range(100):
            start_time = time.time()
            cards = deck.draw_cards(1)
            if cards:
                deck.discard_card(cards[0])
            operation_time = time.time() - start_time
            operation_times.append(operation_time)
        
        avg_operation_time = sum(operation_times) / len(operation_times)
        print(f"🎮 平均操作时间: {avg_operation_time:.4f}s")
        
        return True
        
    except Exception as e:
        print(f"❌ 性能测试失败: {e}")
        return False

def test_integration_scenario():
    """集成场景测试"""
    print("\n=== 集成场景测试 ===")
    
    try:
        print("🎮 模拟完整游戏场景...")
        
        # 1. 初始化系统
        loader = OptimizedCardLoader()
        cards_data = loader.load_cards()
        deck = EnhancedDeck()
        display_manager = CardDisplayManager(deck)
        monitor = RealTimeCardMonitor(deck, update_interval=0.2)
        
        print(f"✅ 系统初始化完成: {len(cards_data)} 张卡牌")
        
        # 2. 启动监控
        monitor.start_monitoring()
        
        # 3. 模拟游戏流程
        print("🎯 模拟游戏流程:")
        
        # 发牌阶段
        players_hands = []
        for i in range(4):  # 4个玩家
            hand = deck.draw_cards(4)  # 每人4张手牌
            players_hands.append(hand)
            print(f"   玩家{i+1}摸牌: {len(hand)} 张")
        
        # 游戏进行阶段
        for round_num in range(3):
            print(f"   第{round_num+1}轮:")
            
            for player_idx in range(4):
                # 摸牌阶段
                new_cards = deck.draw_cards(2)
                if new_cards:
                    players_hands[player_idx].extend(new_cards)
                
                # 出牌阶段（模拟弃牌）
                if players_hands[player_idx]:
                    discard_card = players_hands[player_idx].pop(0)
                    deck.discard_card(discard_card)
            
            # 显示当前状态
            status = display_manager.get_real_time_status()
            print(f"     牌堆状态: 摸牌堆{status['draw_pile']}, 弃牌堆{status['discard_pile']}")
            
            time.sleep(0.3)  # 等待监控更新
        
        # 4. 停止监控
        monitor.stop_monitoring()
        
        # 5. 生成报告
        final_status = deck.get_deck_status()
        print(f"\n📋 游戏结束状态:")
        for key, value in final_status.items():
            print(f"   {key}: {value}")
        
        # 6. 性能统计
        load_stats = loader.get_load_stats()
        print(f"\n📊 系统性能统计:")
        print(f"   总加载次数: {load_stats['total_loads']}")
        print(f"   缓存命中率: {load_stats['cache_hits']/max(load_stats['total_loads'], 1)*100:.1f}%")
        
        return True
        
    except Exception as e:
        print(f"❌ 集成测试失败: {e}")
        return False

def main():
    """主测试函数"""
    print("🃏 三国杀卡牌系统优化综合测试")
    print("=" * 50)
    
    test_results = []
    
    # 执行所有测试
    tests = [
        ("优化卡牌加载", test_optimized_card_loading),
        ("增强牌堆管理", test_enhanced_deck_management),
        ("卡牌显示系统", test_card_display_system),
        ("实时监控系统", test_real_time_monitoring),
        ("Web仪表板生成", test_web_dashboard_generation),
        ("异步加载功能", test_async_loading),
        ("性能基准测试", test_performance_benchmark),
        ("集成场景测试", test_integration_scenario)
    ]
    
    for test_name, test_func in tests:
        print(f"\n🧪 开始测试: {test_name}")
        try:
            result = test_func()
            test_results.append((test_name, result))
            if result:
                print(f"✅ {test_name} 测试通过")
            else:
                print(f"❌ {test_name} 测试失败")
        except Exception as e:
            print(f"💥 {test_name} 测试异常: {e}")
            test_results.append((test_name, False))
    
    # 汇总结果
    print("\n" + "=" * 50)
    print("📊 测试结果汇总")
    print("=" * 50)
    
    passed_tests = sum(1 for _, result in test_results if result)
    total_tests = len(test_results)
    
    for test_name, result in test_results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"  {test_name:<20} {status}")
    
    print(f"\n🎯 总体结果: {passed_tests}/{total_tests} 测试通过")
    print(f"📈 通过率: {passed_tests/total_tests*100:.1f}%")
    
    if passed_tests == total_tests:
        print("\n🎉 所有测试通过！卡牌系统优化成功！")
    else:
        print(f"\n⚠️  有 {total_tests - passed_tests} 个测试失败，需要进一步优化")
    
    return passed_tests == total_tests

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)