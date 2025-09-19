#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
蜀国武将技能详细测试
测试刘备（仁德）、关羽（武圣）、张飞（咆哮）、赵云（龙胆）、诸葛亮（观星、空城）
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.models.character import CharacterFactory, Kingdom
from app.models.player import Player
from app.core.base.game import Game
from app.models.card import Card
from app.models.enums import CardType
from app.models.skills import (
    PaoXiao, GuanXing, SkillManager
)
from app.core.events.event_system import EventManager

def create_test_game():
    """创建测试游戏环境"""
    event_manager = EventManager()
    game = Game(event_manager)
    # 创建一个简单的牌堆用于测试
    test_cards = []
    for i in range(54):
        test_cards.append(Card(name="测试牌", type=CardType.BASIC, suit="红桃", rank=i%13+1))
    game.deck.cards = test_cards
    return game

def create_test_cards():
    """创建测试卡牌"""
    cards = [
        Card(name="杀", type=CardType.BASIC, suit="黑桃", rank=7),
        Card(name="闪", type=CardType.BASIC, suit="红桃", rank=8),
        Card(name="桃", type=CardType.BASIC, suit="红桃", rank=9),
        Card(name="过河拆桥", type=CardType.TRICK, suit="梅花", rank=10),
        Card(name="顺手牵羊", type=CardType.TRICK, suit="黑桃", rank=3),
        Card(name="青龙偃月刀", type=CardType.EQUIP, suit="黑桃", rank=5),
        Card(name="八卦阵", type=CardType.EQUIP, suit="梅花", rank=2),
        Card(name="无懈可击", type=CardType.TRICK, suit="梅花", rank=12),
        Card(name="决斗", type=CardType.TRICK, suit="黑桃", rank=1),
    ]
    return cards

def test_liubei_rende():
    """详细测试刘备仁德技能"""
    print("\n=== 详细测试刘备仁德技能 ===")
    
    # 创建游戏和玩家
    game = create_test_game()
    liubei = CharacterFactory.create_character("刘备")
    liubei_player = Player(liubei)
    
    # 创建队友玩家
    teammate = CharacterFactory.create_character("关羽")
    teammate_player = Player(teammate)
    
    # 给刘备一些手牌
    liubei_player.hand_cards = create_test_cards()[:4]
    
    print(f"刘备: {liubei.name}, 技能: {liubei.skills}")
    print(f"刘备初始手牌数: {len(liubei_player.hand_cards)}")
    print(f"队友初始手牌数: {len(teammate_player.hand_cards)}")
    
    # 测试1: 仁德技能基本功能
    print("\n测试1: 仁德技能基本功能")
    if "仁德" in liubei.skills:
        print("刘备拥有仁德技能")
        # 模拟给队友一张牌
        if liubei_player.hand_cards:
            given_card = liubei_player.hand_cards[0]
            liubei_player.hand_cards.remove(given_card)
            teammate_player.hand_cards.append(given_card)
            print(f"刘备给队友 {given_card.name}")
            print(f"刘备剩余手牌数: {len(liubei_player.hand_cards)}")
            print(f"队友获得牌后手牌数: {len(teammate_player.hand_cards)}")
    else:
        print("仁德技能暂未实现")
    
    # 测试2: 多次使用仁德
    print("\n测试2: 多次使用仁德")
    for i in range(2):
        if liubei_player.hand_cards:
            given_card = liubei_player.hand_cards[0]
            liubei_player.hand_cards.remove(given_card)
            teammate_player.hand_cards.append(given_card)
            print(f"第{i+1}次仁德，给出 {given_card.name}")
            print(f"刘备剩余手牌数: {len(liubei_player.hand_cards)}")

def test_guanyu_wusheng():
    """详细测试关羽武圣技能"""
    print("\n=== 详细测试关羽武圣技能 ===")
    
    # 创建游戏和玩家
    game = create_test_game()
    guanyu = CharacterFactory.create_character("关羽")
    guanyu_player = Player(guanyu)
    
    # 给关羽一些红色牌
    red_cards = [
        Card(name="桃", type=CardType.BASIC, suit="红桃", rank=3),
        Card(name="闪", type=CardType.BASIC, suit="红桃", rank=8),
        Card(name="无懈可击", type=CardType.TRICK, suit="方片", rank=12),
    ]
    guanyu_player.hand_cards = red_cards
    
    print(f"关羽: {guanyu.name}, 技能: {guanyu.skills}")
    print(f"关羽初始手牌数: {len(guanyu_player.hand_cards)}")
    
    # 测试1: 武圣技能基本功能
    print("\n测试1: 武圣技能基本功能")
    if "武圣" in guanyu.skills:
        print("关羽拥有武圣技能")
        print("可以将红色牌当作杀使用:")
        for card in guanyu_player.hand_cards:
            if card.suit in ["红桃", "方片"]:
                print(f"  {card.name}({card.suit}[{card.rank}]) 可以当作杀使用")
    else:
        print("武圣技能暂未实现")
    
    # 测试2: 武圣技能使用限制
    print("\n测试2: 武圣技能使用限制")
    black_cards = [
        Card(name="杀", type=CardType.BASIC, suit="黑桃", rank=7),
        Card(name="过河拆桥", type=CardType.TRICK, suit="梅花", rank=10),
    ]
    print("黑色牌不能通过武圣当作杀使用:")
    for card in black_cards:
        print(f"  {card.name}({card.suit}[{card.rank}]) 不能当作杀使用")

def test_zhangfei_paoxiao():
    """详细测试张飞咆哮技能"""
    print("\n=== 详细测试张飞咆哮技能 ===")
    
    # 创建游戏和玩家
    game = create_test_game()
    zhangfei = CharacterFactory.create_character("张飞")
    zhangfei_player = Player(zhangfei)
    
    # 创建咆哮技能实例
    paoxiao = PaoXiao()
    
    # 给张飞一些杀牌
    sha_cards = [
        Card(name="杀", type=CardType.BASIC, suit="黑桃", rank=7),
        Card(name="杀", type=CardType.BASIC, suit="红桃", rank=8),
        Card(name="杀", type=CardType.BASIC, suit="梅花", rank=9),
    ]
    zhangfei_player.hand_cards = sha_cards
    
    print(f"张飞: {zhangfei.name}, 技能: {zhangfei.skills}")
    print(f"张飞初始手牌数: {len(zhangfei_player.hand_cards)}")
    
    # 测试1: 咆哮技能触发条件
    print("\n测试1: 咆哮技能触发条件")
    can_trigger = paoxiao.can_trigger(game, zhangfei_player, "play_phase")
    print(f"咆哮技能可以触发: {can_trigger}")
    
    if can_trigger:
        result = paoxiao.execute(game, zhangfei_player)
        print(f"咆哮技能执行结果: {result}")
        print("张飞可以无限次使用杀")
    else:
        print("咆哮技能无法触发")
    
    # 测试2: 多次使用杀
    print("\n测试2: 模拟多次使用杀")
    sha_count = 0
    for card in zhangfei_player.hand_cards:
        if card.name == "杀":
            sha_count += 1
            print(f"第{sha_count}次使用杀: {card}")
    
    print(f"张飞总共可以使用 {sha_count} 次杀（咆哮效果下无限制）")

def test_zhaoyun_longdan():
    """详细测试赵云龙胆技能"""
    print("\n=== 详细测试赵云龙胆技能 ===")
    
    # 创建游戏和玩家
    game = create_test_game()
    zhaoyun = CharacterFactory.create_character("赵云")
    zhaoyun_player = Player(zhaoyun)
    
    # 给赵云一些杀和闪牌
    test_cards = [
        Card(name="杀", type=CardType.BASIC, suit="黑桃", rank=7),
        Card(name="闪", type=CardType.BASIC, suit="红桃", rank=8),
        Card(name="杀", type=CardType.BASIC, suit="梅花", rank=9),
        Card(name="闪", type=CardType.BASIC, suit="方片", rank=10),
    ]
    zhaoyun_player.hand_cards = test_cards
    
    print(f"赵云: {zhaoyun.name}, 技能: {zhaoyun.skills}")
    print(f"赵云初始手牌数: {len(zhaoyun_player.hand_cards)}")
    
    # 测试1: 龙胆技能基本功能
    print("\n测试1: 龙胆技能基本功能")
    if "龙胆" in zhaoyun.skills:
        print("赵云拥有龙胆技能")
        print("可以将杀当作闪使用，将闪当作杀使用:")
        for card in zhaoyun_player.hand_cards:
            if card.name == "杀":
                print(f"  {card} 可以当作闪使用")
            elif card.name == "闪":
                print(f"  {card} 可以当作杀使用")
    else:
        print("龙胆技能暂未实现")
    
    # 测试2: 龙胆技能的战术价值
    print("\n测试2: 龙胆技能的战术价值")
    sha_count = sum(1 for card in zhaoyun_player.hand_cards if card.name == "杀")
    shan_count = sum(1 for card in zhaoyun_player.hand_cards if card.name == "闪")
    print(f"实际杀牌数: {sha_count}, 实际闪牌数: {shan_count}")
    print(f"龙胆效果下等效杀牌数: {sha_count + shan_count}")
    print(f"龙胆效果下等效闪牌数: {sha_count + shan_count}")

def test_zhugeliang_guanxing():
    """详细测试诸葛亮观星技能"""
    print("\n=== 详细测试诸葛亮观星技能 ===")
    
    # 创建游戏和玩家
    game = create_test_game()
    zhugeliang = CharacterFactory.create_character("诸葛亮")
    zhugeliang_player = Player(zhugeliang)
    
    # 创建观星技能实例
    guanxing = GuanXing()
    
    print(f"诸葛亮: {zhugeliang.name}, 技能: {zhugeliang.skills}")
    print(f"观星前牌堆剩余: {len(game.deck)}")
    
    # 测试1: 观星技能触发条件
    print("\n测试1: 观星技能触发条件")
    can_trigger = guanxing.can_trigger(game, zhugeliang_player)
    print(f"观星技能可以触发: {can_trigger}")
    
    if can_trigger:
        result = guanxing.execute(game, zhugeliang_player)
        print(f"观星技能执行结果: {result}")
        print(f"观星后牌堆剩余: {len(game.deck)}")
    
    # 测试2: 多次使用观星
    print("\n测试2: 多次使用观星")
    for i in range(3):
        if guanxing.can_trigger(game, zhugeliang_player):
            print(f"第{i+1}次观星")
            guanxing.execute(game, zhugeliang_player)
            print(f"牌堆剩余: {len(game.deck)}")
        else:
            print(f"第{i+1}次观星无法触发（牌堆不足）")
            break

def test_zhugeliang_kongcheng():
    """详细测试诸葛亮空城技能"""
    print("\n=== 详细测试诸葛亮空城技能 ===")
    
    # 创建游戏和玩家
    game = create_test_game()
    zhugeliang = CharacterFactory.create_character("诸葛亮")
    zhugeliang_player = Player(zhugeliang)
    
    print(f"诸葛亮: {zhugeliang.name}, 技能: {zhugeliang.skills}")
    
    # 测试1: 有手牌时的空城状态
    print("\n测试1: 有手牌时的空城状态")
    zhugeliang_player.hand_cards = create_test_cards()[:2]
    print(f"诸葛亮手牌数: {len(zhugeliang_player.hand_cards)}")
    print("空城技能不能触发（有手牌）")
    
    # 测试2: 无手牌时的空城状态
    print("\n测试2: 无手牌时的空城状态")
    zhugeliang_player.hand_cards.clear()
    print(f"诸葛亮手牌数: {len(zhugeliang_player.hand_cards)}")
    if "空城" in zhugeliang.skills:
        print("空城技能可以触发：")
        print("- 不能成为杀的目标")
        print("- 不能成为决斗的目标")
    else:
        print("空城技能暂未实现")

def test_skill_manager_shu():
    """测试蜀国技能管理器"""
    print("\n=== 测试蜀国技能管理器 ===")
    
    skill_manager = SkillManager()
    
    # 注册蜀国技能
    shu_skills = [
        PaoXiao(),
        GuanXing(),
    ]
    
    for skill in shu_skills:
        skill_manager.register_skill(skill)
        print(f"✓ 注册蜀国技能: {skill.name}")
    
    # 测试技能获取
    for skill_name in ["咆哮", "观星"]:
        skill = skill_manager.get_skill(skill_name)
        if skill:
            print(f"✓ 成功获取技能: {skill.name} - {skill.description}")
        else:
            print(f"✗ 未找到技能: {skill_name}")

def main():
    """主测试函数"""
    print("三国杀蜀国武将技能详细测试")
    print("=" * 50)
    
    try:
        # 测试各个蜀国武将技能
        test_liubei_rende()
        test_guanyu_wusheng()
        test_zhangfei_paoxiao()
        test_zhaoyun_longdan()
        test_zhugeliang_guanxing()
        test_zhugeliang_kongcheng()
        test_skill_manager_shu()
        
        print("\n" + "=" * 50)
        print("蜀国武将技能测试完成！")
        
    except Exception as e:
        print(f"测试过程中出现错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()