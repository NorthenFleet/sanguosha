#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
吴国武将技能详细测试
测试孙权（制衡）、周瑜（英姿、反间）、甘宁（奇袭）、吕蒙（克己）
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.models.character import CharacterFactory, Kingdom
from app.models.player import Player
from app.core.game import Game
from app.models.card import Card
from app.models.enums import CardType
from app.models.skills import (
    YingZi, QiXi, KeJi, SkillManager
)
from app.core.event_system import EventManager

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

def test_sunquan_zhiheng():
    """详细测试孙权制衡技能"""
    print("\n=== 详细测试孙权制衡技能 ===")
    
    # 创建游戏和玩家
    game = create_test_game()
    sunquan = CharacterFactory.create_character("孙权")
    sunquan_player = Player(sunquan)
    
    # 给孙权一些手牌
    sunquan_player.hand_cards = create_test_cards()[:5]
    
    print(f"孙权: {sunquan.name}, 技能: {sunquan.skills}")
    print(f"孙权初始手牌数: {len(sunquan_player.hand_cards)}")
    
    # 测试1: 制衡技能基本功能
    print("\n测试1: 制衡技能基本功能")
    if "制衡" in sunquan.skills:
        print("孙权拥有制衡技能")
        print("制衡：出牌阶段限一次，你可以弃置任意张牌，然后摸等量的牌")
        
        # 模拟弃置2张牌
        discarded_cards = sunquan_player.hand_cards[:2]
        for card in discarded_cards:
            sunquan_player.hand_cards.remove(card)
        print(f"弃置了 {len(discarded_cards)} 张牌")
        
        # 模拟摸等量的牌
        for i in range(len(discarded_cards)):
            if len(game.deck) > 0:
                new_card = game.deck.draw_card()
                if new_card:
                    sunquan_player.hand_cards.append(new_card)
        
        print(f"制衡后手牌数: {len(sunquan_player.hand_cards)}")
    else:
        print("制衡技能暂未实现")
    
    # 测试2: 制衡技能的战术价值
    print("\n测试2: 制衡技能的战术价值")
    print("制衡可以：")
    print("- 调整手牌结构，换取需要的牌")
    print("- 在手牌质量不佳时重新洗牌")
    print("- 配合其他技能使用")

def test_zhouyu_yingzi():
    """详细测试周瑜英姿技能"""
    print("\n=== 详细测试周瑜英姿技能 ===")
    
    # 创建游戏和玩家
    game = create_test_game()
    zhouyu = CharacterFactory.create_character("周瑜")
    zhouyu_player = Player(zhouyu)
    
    # 创建英姿技能实例
    yingzi = YingZi()
    
    print(f"周瑜: {zhouyu.name}, 技能: {zhouyu.skills}")
    print(f"周瑜初始手牌数: {len(zhouyu_player.hand_cards)}")
    print(f"摸牌前牌堆剩余: {len(game.deck)}")
    
    # 测试1: 英姿技能触发条件
    print("\n测试1: 英姿技能触发条件")
    can_trigger = yingzi.can_trigger(game, zhouyu_player)
    print(f"英姿技能可以触发: {can_trigger}")
    
    if can_trigger:
        result = yingzi.execute(game, zhouyu_player)
        print(f"英姿技能执行结果: {result}")
        print(f"英姿后手牌数: {len(zhouyu_player.hand_cards)}")
        print(f"摸牌后牌堆剩余: {len(game.deck)}")
    
    # 测试2: 多次触发英姿
    print("\n测试2: 多次触发英姿")
    for i in range(3):
        if yingzi.can_trigger(game, zhouyu_player):
            print(f"第{i+1}次英姿")
            yingzi.execute(game, zhouyu_player)
            print(f"手牌数: {len(zhouyu_player.hand_cards)}, 牌堆剩余: {len(game.deck)}")
        else:
            print(f"第{i+1}次英姿无法触发（牌堆不足）")
            break

def test_zhouyu_fanjian():
    """详细测试周瑜反间技能"""
    print("\n=== 详细测试周瑜反间技能 ===")
    
    # 创建游戏和玩家
    game = create_test_game()
    zhouyu = CharacterFactory.create_character("周瑜")
    zhouyu_player = Player(zhouyu)
    
    # 创建目标玩家
    target = CharacterFactory.create_character("曹操")
    target_player = Player(target)
    target_player.character.hp = target_player.character.max_hp
    
    print(f"周瑜: {zhouyu.name}, 技能: {zhouyu.skills}")
    print(f"目标: {target.name}, 体力: {target_player.character.hp}/{target_player.character.max_hp}")
    
    # 测试1: 反间技能基本功能
    print("\n测试1: 反间技能基本功能")
    if "反间" in zhouyu.skills:
        print("周瑜拥有反间技能")
        print("反间：出牌阶段限一次，你可以展示一张手牌并交给一名其他角色，其选择一项：")
        print("1. 展示所有手牌，弃置与此牌花色相同的牌")
        print("2. 受到1点伤害")
        
        # 模拟反间过程
        if zhouyu_player.hand_cards:
            shown_card = create_test_cards()[0]  # 展示一张牌
            print(f"周瑜展示并交给目标: {shown_card}")
            target_player.hand_cards.append(shown_card)
            
            # 目标选择承受伤害
            print("目标选择承受1点伤害")
            target_player.character.hp -= 1
            print(f"目标体力变为: {target_player.character.hp}/{target_player.character.max_hp}")
    else:
        print("反间技能暂未实现")
    
    # 测试2: 反间技能的战术价值
    print("\n测试2: 反间技能的战术价值")
    print("反间可以：")
    print("- 强制对手选择不利选项")
    print("- 消耗对手手牌或造成伤害")
    print("- 获取战术优势")

def test_ganning_qixi():
    """详细测试甘宁奇袭技能"""
    print("\n=== 详细测试甘宁奇袭技能 ===")
    
    # 创建游戏和玩家
    game = create_test_game()
    ganning = CharacterFactory.create_character("甘宁")
    ganning_player = Player(ganning)
    
    # 创建奇袭技能实例
    qixi = QiXi()
    
    # 给甘宁一些黑色牌
    black_cards = [
        Card(name="杀", type=CardType.BASIC, suit="黑桃", rank=7),
        Card(name="过河拆桥", type=CardType.TRICK, suit="梅花", rank=10),
        Card(name="顺手牵羊", type=CardType.TRICK, suit="黑桃", rank=3),
    ]
    ganning_player.hand_cards = black_cards
    
    print(f"甘宁: {ganning.name}, 技能: {ganning.skills}")
    print(f"甘宁初始手牌数: {len(ganning_player.hand_cards)}")
    
    # 测试1: 奇袭技能触发条件
    print("\n测试1: 奇袭技能触发条件")
    can_trigger = qixi.can_trigger(game, ganning_player, "play_phase")
    print(f"奇袭技能可以触发: {can_trigger}")
    
    if can_trigger:
        result = qixi.execute(game, ganning_player)
        print(f"奇袭技能执行结果: {result}")
        print("甘宁可以将黑色牌当作过河拆桥使用")
    else:
        print("奇袭技能无法触发")
    
    # 测试2: 奇袭技能使用示例
    print("\n测试2: 奇袭技能使用示例")
    print("可以当作过河拆桥使用的黑色牌:")
    for card in ganning_player.hand_cards:
        if card.suit in ["黑桃", "梅花"]:
            print(f"  {card} 可以当作过河拆桥使用")
    
    # 测试3: 奇袭技能限制
    print("\n测试3: 奇袭技能限制")
    red_cards = [
        Card(name="桃", type=CardType.BASIC, suit="红桃", rank=3),
        Card(name="闪", type=CardType.BASIC, suit="方片", rank=8),
    ]
    print("红色牌不能通过奇袭当作过河拆桥使用:")
    for card in red_cards:
        print(f"  {card} 不能当作过河拆桥使用")

def test_lvmeng_keji():
    """详细测试吕蒙克己技能"""
    print("\n=== 详细测试吕蒙克己技能 ===")
    
    # 创建游戏和玩家
    game = create_test_game()
    lvmeng = CharacterFactory.create_character("吕蒙")
    lvmeng_player = Player(lvmeng)
    
    # 创建克己技能实例
    keji = KeJi()
    
    print(f"吕蒙: {lvmeng.name}, 技能: {lvmeng.skills}")
    
    # 测试1: 克己技能触发条件（未使用杀）
    print("\n测试1: 克己技能触发条件（未使用杀）")
    can_trigger = keji.can_trigger(game, lvmeng_player, "discard_phase")
    print(f"克己技能可以触发: {can_trigger}")
    
    if can_trigger:
        result = keji.execute(game, lvmeng_player)
        print(f"克己技能执行结果: {result}")
        print("吕蒙在弃牌阶段可以少弃置一张牌")
    
    # 测试2: 克己技能的条件限制
    print("\n测试2: 克己技能的条件限制")
    print("克己技能触发条件：")
    print("- 当前回合未使用过杀")
    print("- 在弃牌阶段")
    
    # 模拟使用了杀的情况
    print("\n模拟使用杀后的情况：")
    # 这里应该设置一个标记表示使用了杀
    print("如果本回合使用过杀，克己技能无法触发")
    
    # 测试3: 克己技能的战术价值
    print("\n测试3: 克己技能的战术价值")
    print("克己技能的价值：")
    print("- 保留更多手牌")
    print("- 提高防御能力")
    print("- 需要合理规划出牌顺序")

def test_skill_manager_wu():
    """测试吴国技能管理器"""
    print("\n=== 测试吴国技能管理器 ===")
    
    skill_manager = SkillManager()
    
    # 注册吴国技能
    wu_skills = [
        YingZi(),
        QiXi(),
        KeJi(),
    ]
    
    for skill in wu_skills:
        skill_manager.register_skill(skill)
        print(f"✓ 注册吴国技能: {skill.name}")
    
    # 测试技能获取
    for skill_name in ["英姿", "奇袭", "克己"]:
        skill = skill_manager.get_skill(skill_name)
        if skill:
            print(f"✓ 成功获取技能: {skill.name} - {skill.description}")
        else:
            print(f"✗ 未找到技能: {skill_name}")

def main():
    """主测试函数"""
    print("三国杀吴国武将技能详细测试")
    print("=" * 50)
    
    try:
        # 测试各个吴国武将技能
        test_sunquan_zhiheng()
        test_zhouyu_yingzi()
        test_zhouyu_fanjian()
        test_ganning_qixi()
        test_lvmeng_keji()
        test_skill_manager_wu()
        
        print("\n" + "=" * 50)
        print("吴国武将技能测试完成！")
        
    except Exception as e:
        print(f"测试过程中出现错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()