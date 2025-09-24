#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试修正后的卡牌系统功能
"""

import json
import sys
import os

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.models.card import Card, CardType

def test_card_loading():
    """测试卡牌加载功能"""
    print("=== 测试1: 卡牌数据加载 ===")
    
    try:
        with open('app/data/cards.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        cards_data = data['cards']
        print(f"✓ 成功加载 {len(cards_data)} 张卡牌")
        
        # 验证JSON格式
        for i, card_data in enumerate(cards_data):
            required_fields = ['name', 'type', 'suit', 'rank', 'category']
            for field in required_fields:
                if field not in card_data:
                    print(f"✗ 卡牌 {i+1} 缺少必需字段: {field}")
                    return False
        
        print("✓ 所有卡牌数据格式正确")
        return True
        
    except Exception as e:
        print(f"✗ 卡牌加载失败: {e}")
        return False

def test_card_creation():
    """测试卡牌对象创建"""
    print("\n=== 测试2: 卡牌对象创建 ===")
    
    try:
        # 测试基本牌创建
        sha_card = Card("杀", CardType.BASIC, "黑桃", 7)
        print(f"✓ 基本牌创建成功: {sha_card.name} {sha_card.suit}{sha_card.rank}")
        
        # 测试锦囊牌创建
        trick_card = Card("无懈可击", CardType.TRICK, "红桃", 11)
        print(f"✓ 锦囊牌创建成功: {trick_card.name} {trick_card.suit}{trick_card.rank}")
        
        # 测试装备牌创建
        equipment_card = Card("丈八蛇矛", CardType.EQUIP, "黑桃", 12)
        print(f"✓ 装备牌创建成功: {equipment_card.name} {equipment_card.suit}{equipment_card.rank}")
        
        return True
        
    except Exception as e:
        print(f"✗ 卡牌对象创建失败: {e}")
        return False

def test_card_types():
    """测试卡牌类型分类"""
    print("\n=== 测试3: 卡牌类型分类 ===")
    
    try:
        with open('app/data/cards.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        cards_data = data['cards']
        
        # 统计各类型卡牌
        basic_count = len([c for c in cards_data if c['category'] == 'basic'])
        trick_count = len([c for c in cards_data if c['category'] == 'trick'])
        equipment_count = len([c for c in cards_data if c['category'] == 'equipment'])
        
        print(f"✓ 基本牌: {basic_count} 张")
        print(f"✓ 锦囊牌: {trick_count} 张")
        print(f"✓ 装备牌: {equipment_count} 张")
        
        # 验证总数
        total = basic_count + trick_count + equipment_count
        if total == 104:
            print(f"✓ 总卡牌数量正确: {total} 张")
            return True
        else:
            print(f"✗ 总卡牌数量错误: {total} 张，应为104张")
            return False
            
    except Exception as e:
        print(f"✗ 卡牌类型分类测试失败: {e}")
        return False

def test_specific_cards():
    """测试特定卡牌的存在性"""
    print("\n=== 测试4: 特定卡牌存在性 ===")
    
    try:
        with open('app/data/cards.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        cards_data = data['cards']
        card_names = [c['name'] for c in cards_data]
        
        # 测试关键卡牌
        key_cards = ['杀', '闪', '桃', '无懈可击', '南蛮入侵', '万箭齐发', '丈八蛇矛', '诸葛连弩', '八卦阵']
        
        for card_name in key_cards:
            if card_name in card_names:
                count = card_names.count(card_name)
                print(f"✓ {card_name}: {count} 张")
            else:
                print(f"✗ 缺少关键卡牌: {card_name}")
                return False
        
        return True
        
    except Exception as e:
        print(f"✗ 特定卡牌测试失败: {e}")
        return False

def test_card_suits_and_ranks():
    """测试卡牌花色和点数"""
    print("\n=== 测试5: 卡牌花色和点数 ===")
    
    try:
        with open('app/data/cards.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        cards_data = data['cards']
        
        # 验证花色
        valid_suits = ['黑桃', '红桃', '梅花', '方块']
        suits = [c['suit'] for c in cards_data]
        
        for suit in suits:
            if suit not in valid_suits:
                print(f"✗ 无效花色: {suit}")
                return False
        
        print("✓ 所有花色有效")
        
        # 验证点数
        ranks = [c['rank'] for c in cards_data]
        for rank in ranks:
            if not (1 <= rank <= 13):
                print(f"✗ 无效点数: {rank}")
                return False
        
        print("✓ 所有点数有效 (1-13)")
        
        # 统计花色分布
        suit_counts = {}
        for suit in suits:
            suit_counts[suit] = suit_counts.get(suit, 0) + 1
        
        print("花色分布:")
        for suit, count in suit_counts.items():
            print(f"  {suit}: {count} 张")
        
        return True
        
    except Exception as e:
        print(f"✗ 花色点数测试失败: {e}")
        return False

def main():
    """主测试函数"""
    print("开始测试修正后的卡牌系统...")
    
    tests = [
        test_card_loading,
        test_card_creation,
        test_card_types,
        test_specific_cards,
        test_card_suits_and_ranks
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
        else:
            print("测试失败，停止后续测试")
            break
    
    print(f"\n=== 测试结果 ===")
    print(f"通过: {passed}/{total}")
    
    if passed == total:
        print("✓ 所有测试通过！卡牌系统配置正确。")
        return True
    else:
        print("✗ 部分测试失败，需要进一步修正。")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)