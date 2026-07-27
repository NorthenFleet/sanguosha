#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
魏国武将技能详细测试
测试曹操（奸雄）、司马懿（反馈）、夏侯惇（刚烈）、张辽（突袭）
"""

import sys
import os

from app.models.character import CharacterFactory, Kingdom
from app.models.player import Player
from app.core.base.game import Game
from app.models.card import Card
from app.models.enums import CardType
from app.models.skills import (
    JianXiong, FanKui, GangLie, SkillManager
)
from app.core.events.event_system import EventManager

def create_test_game():
    """创建测试游戏环境"""
    event_manager = EventManager()
    game = Game(event_manager)
    # 创建一个简单的牌堆用于测试
    test_cards = []
    for i in range(54):
        test_cards.append(Card(name="测试牌", type=CardType.BASIC, suit="红桃", point=i%13+1))
    game.deck.cards = test_cards
    return game

def create_test_cards():
    """创建测试卡牌"""
    cards = [
        Card(name="杀", type=CardType.BASIC, suit="黑桃", point=7),
        Card(name="闪", type=CardType.BASIC, suit="红桃", point=8),
        Card(name="桃", type=CardType.BASIC, suit="红桃", point=9),
        Card(name="过河拆桥", type=CardType.TRICK, suit="梅花", point=10),
        Card(name="顺手牵羊", type=CardType.TRICK, suit="黑桃", point=3),
        Card(name="青龙偃月刀", type=CardType.EQUIP, suit="黑桃", point=5),
        Card(name="八卦阵", type=CardType.EQUIP, suit="梅花", point=2),
    ]
    return cards

def test_caocao_jianxiong():
    """详细测试曹操奸雄技能"""
    print("\n=== 详细测试曹操奸雄技能 ===")
    
    # 创建游戏和玩家
    game = create_test_game()
    caocao = CharacterFactory.create_character("曹操")
    caocao_player = Player(caocao)
    
    # 创建奸雄技能实例
    jianxiong = JianXiong()
    
    print(f"曹操初始状态: 体力{caocao_player.hp}/{caocao_player.character.max_hp}, 手牌{len(caocao_player.hand_cards)}张")
    
    # 测试1: 受到伤害时触发奸雄
    print("\n测试1: 受到伤害时触发奸雄")
    damage_card = Card(name="杀", type=CardType.BASIC, suit="黑桃", point=7)
    
    # 检查技能是否可以触发
    can_trigger = jianxiong.can_trigger(game, caocao_player, "damage_taken", damage_source=damage_card)
    print(f"奸雄技能可以触发: {can_trigger}")
    
    if can_trigger:
        # 执行技能
        result = jianxiong.execute(game, caocao_player, damage_source=damage_card)
        print(f"奸雄技能执行结果: {result}")
        print(f"曹操获得伤害牌后手牌数: {len(caocao_player.hand_cards)}")
        if caocao_player.hand_cards:
            print(f"获得的牌: {caocao_player.hand_cards[-1]}")
    
    # 测试2: 多次受到伤害
    print("\n测试2: 多次受到伤害")
    for i in range(3):
        damage_card = Card(name=f"杀{i+1}", type=CardType.BASIC, suit="黑桃", point=7+i)
        if jianxiong.can_trigger(game, caocao_player, "damage_taken", damage_source=damage_card):
            jianxiong.execute(game, caocao_player, damage_source=damage_card)
            print(f"第{i+1}次触发奸雄后，手牌数: {len(caocao_player.hand_cards)}")
    
    print(f"曹操最终状态: 手牌{len(caocao_player.hand_cards)}张")

def test_simayi_fankui():
    """详细测试司马懿反馈技能"""
    print("\n=== 详细测试司马懿反馈技能 ===")
    
    # 创建游戏和玩家
    game = create_test_game()
    simayi = CharacterFactory.create_character("司马懿")
    simayi_player = Player(simayi)
    
    # 创建敌人玩家
    enemy = CharacterFactory.create_character("曹操")
    enemy_player = Player(enemy)
    enemy_player.hand_cards = create_test_cards()[:3]  # 给敌人3张手牌
    
    # 创建反馈技能实例
    fankui = FanKui()
    
    print(f"司马懿初始手牌数: {len(simayi_player.hand_cards)}")
    print(f"敌人初始手牌数: {len(enemy_player.hand_cards)}")
    
    # 测试1: 受到伤害时触发反馈
    print("\n测试1: 受到伤害时触发反馈")
    can_trigger = fankui.can_trigger(game, simayi_player, enemy_player)
    print(f"反馈技能可以触发: {can_trigger}")
    
    if can_trigger:
        result = fankui.execute(game, simayi_player, enemy_player)
        print(f"反馈技能执行结果: {result}")
        print(f"司马懿获得牌后手牌数: {len(simayi_player.hand_cards)}")
        print(f"敌人失去牌后手牌数: {len(enemy_player.hand_cards)}")
    
    # 测试2: 敌人没有手牌时
    print("\n测试2: 敌人没有手牌时")
    enemy_player.hand_cards.clear()
    can_trigger = fankui.can_trigger(game, simayi_player, enemy_player)
    print(f"敌人无手牌时反馈技能可以触发: {can_trigger}")
    
    # 测试3: 多个敌人的情况
    print("\n测试3: 多个敌人的情况")
    enemy2 = CharacterFactory.create_character("张辽")
    enemy2_player = Player(enemy2)
    enemy2_player.hand_cards = create_test_cards()[3:5]  # 给敌人2两张手牌
    
    print(f"敌人2手牌数: {len(enemy2_player.hand_cards)}")
    if fankui.can_trigger(game, simayi_player, enemy2_player):
        fankui.execute(game, simayi_player, enemy2_player)
        print(f"对敌人2使用反馈后，司马懿手牌数: {len(simayi_player.hand_cards)}")
        print(f"敌人2剩余手牌数: {len(enemy2_player.hand_cards)}")

def test_xiahou_ganglie():
    """详细测试夏侯惇刚烈技能"""
    print("\n=== 详细测试夏侯惇刚烈技能 ===")
    
    # 创建游戏和玩家
    game = create_test_game()
    xiahou = CharacterFactory.create_character("夏侯惇")
    xiahou_player = Player(xiahou)
    
    # 创建敌人玩家
    enemy = CharacterFactory.create_character("曹操")
    enemy_player = Player(enemy)
    enemy_player.hand_cards = create_test_cards()[:4]  # 给敌人4张手牌
    
    # 创建刚烈技能实例
    ganglie = GangLie()
    
    print(f"夏侯惇初始状态: 体力{xiahou_player.hp}/{xiahou_player.character.max_hp}")
    print(f"敌人初始手牌数: {len(enemy_player.hand_cards)}")
    
    # 测试1: 受到伤害时触发刚烈
    print("\n测试1: 受到伤害时触发刚烈")
    can_trigger = ganglie.can_trigger(game, xiahou_player, enemy_player)
    print(f"刚烈技能可以触发: {can_trigger}")
    
    if can_trigger:
        print("模拟判定阶段...")
        result = ganglie.execute(game, xiahou_player, enemy_player)
        print(f"刚烈技能执行结果: {result}")
        print(f"敌人剩余手牌数: {len(enemy_player.hand_cards)}")
    
    # 测试2: 多次触发刚烈
    print("\n测试2: 多次触发刚烈")
    for i in range(2):
        if ganglie.can_trigger(game, xiahou_player, enemy_player):
            print(f"第{i+1}次触发刚烈")
            ganglie.execute(game, xiahou_player, enemy_player)
            print(f"敌人剩余手牌数: {len(enemy_player.hand_cards)}")
    
    # 测试3: 敌人没有手牌时
    print("\n测试3: 敌人没有手牌时")
    enemy_player.hand_cards.clear()
    can_trigger = ganglie.can_trigger(game, xiahou_player, enemy_player)
    print(f"敌人无手牌时刚烈技能可以触发: {can_trigger}")
    if can_trigger:
        result = ganglie.execute(game, xiahou_player, enemy_player)
        print(f"无手牌时刚烈执行结果: {result}")

def test_zhangliao_tuxi():
    """测试张辽突袭技能（如果已实现）"""
    print("\n=== 测试张辽突袭技能 ===")
    
    # 创建游戏和玩家
    game = create_test_game()
    zhangliao = CharacterFactory.create_character("张辽")
    zhangliao_player = Player(zhangliao)
    
    print(f"张辽: {zhangliao.name}, 技能: {zhangliao.skills}")
    
    # 检查是否有突袭技能实现
    tuxi_skill = None
    for skill_name in zhangliao.skills:
        if "突袭" in skill_name or "tuxi" in skill_name.lower():
            print(f"找到突袭相关技能: {skill_name}")
            # 这里需要根据实际的技能实现来测试
            break
    
    if not tuxi_skill:
        print("突袭技能暂未实现，跳过测试")

def test_skill_manager_wei():
    """测试魏国技能管理器"""
    print("\n=== 测试魏国技能管理器 ===")
    
    skill_manager = SkillManager()
    
    # 注册魏国技能
    wei_skills = [
        JianXiong(),
        FanKui(),
        GangLie(),
    ]
    
    for skill in wei_skills:
        skill_manager.register_skill(skill)
        print(f"✓ 注册魏国技能: {skill.name}")
    
    # 测试技能获取
    for skill_name in ["奸雄", "反馈", "刚烈"]:
        skill = skill_manager.get_skill(skill_name)
        if skill:
            print(f"✓ 成功获取技能: {skill.name} - {skill.description}")
        else:
            print(f"✗ 未找到技能: {skill_name}")

def main():
    """主测试函数"""
    print("三国杀魏国武将技能详细测试")
    print("=" * 50)
    
    try:
        # 测试各个魏国武将技能
        test_caocao_jianxiong()
        test_simayi_fankui()
        test_xiahou_ganglie()
        test_zhangliao_tuxi()
        test_skill_manager_wei()
        
        print("\n" + "=" * 50)
        print("魏国武将技能测试完成！")
        
    except Exception as e:
        print(f"测试过程中出现错误: {e}")
        import traceback
        traceback.print_exc()

