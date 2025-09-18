#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
武将技能测试脚本
测试所有可用武将的技能功能
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
    JianXiong, FanKui, GangLie, PaoXiao, GuanXing, QiXi, KeJi, YingZi, SkillManager
)
from app.core.event_system import EventManager

def create_test_game():
    """创建测试游戏环境"""
    event_manager = EventManager()
    game = Game(event_manager)
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

def test_character_creation():
    """测试武将创建"""
    print("=== 测试武将创建 ===")
    
    available_characters = [
        "曹操", "司马懿", "张辽", "夏侯惇",
        "刘备", "关羽", "张飞", "赵云", "诸葛亮",
        "孙权", "周瑜", "甘宁", "吕蒙",
        "华佗", "吕布", "貂蝉"
    ]
    
    for char_name in available_characters:
        try:
            character = CharacterFactory.create_character(char_name)
            print(f"✓ {char_name}: {character.kingdom.value}, 体力{character.max_hp}, 技能{character.skills}")
        except Exception as e:
            print(f"✗ {char_name}: 创建失败 - {e}")
    
    print()

def test_jianxiong_skill():
    """测试曹操的奸雄技能"""
    print("=== 测试曹操奸雄技能 ===")
    
    game = create_test_game()
    caocao_char = CharacterFactory.create_character("曹操")
    enemy_char = CharacterFactory.create_character("刘备")
    
    caocao_player = Player(caocao_char)
    enemy_player = Player(enemy_char)
    
    game.add_player(caocao_player)
    game.add_player(enemy_player)
    
    # 创建奸雄技能实例
    jianxiong = JianXiong()
    
    # 模拟受到伤害
    damage_card = Card(name="杀", type=CardType.BASIC, suit="黑桃", point=7)
    
    print(f"曹操受到伤害前手牌数: {len(caocao_player.hand_cards)}")
    
    # 测试技能触发
    if jianxiong.can_trigger(game, caocao_player, "damage", damage_card=damage_card):
        result = jianxiong.execute(game, caocao_player, damage_card=damage_card)
        print(f"奸雄技能执行结果: {result}")
        print(f"曹操受到伤害后手牌数: {len(caocao_player.hand_cards)}")
    else:
        print("奸雄技能无法触发")
    
    print()

def test_fankui_skill():
    """测试司马懿的反馈技能"""
    print("=== 测试司马懿反馈技能 ===")
    
    game = create_test_game()
    simayi_char = CharacterFactory.create_character("司马懿")
    enemy_char = CharacterFactory.create_character("曹操")
    
    simayi_player = Player(simayi_char)
    enemy_player = Player(enemy_char)
    
    # 给敌人一些手牌
    test_cards = create_test_cards()
    enemy_player.hand_cards.extend(test_cards[:3])
    
    game.add_player(simayi_player)
    game.add_player(enemy_player)
    
    # 创建反馈技能实例
    fankui = FanKui()
    
    print(f"司马懿受到伤害前手牌数: {len(simayi_player.hand_cards)}")
    print(f"敌人手牌数: {len(enemy_player.hand_cards)}")
    
    # 测试技能触发
    if fankui.can_trigger(game, simayi_player, target=enemy_player):
        result = fankui.execute(game, simayi_player, target=enemy_player)
        print(f"反馈技能执行结果: {result}")
        print(f"司马懿受到伤害后手牌数: {len(simayi_player.hand_cards)}")
        print(f"敌人手牌数: {len(enemy_player.hand_cards)}")
    else:
        print("反馈技能无法触发")
    
    print()

def test_paoxiao_skill():
    """测试张飞的咆哮技能"""
    print("=== 测试张飞咆哮技能 ===")
    
    game = create_test_game()
    zhangfei_char = CharacterFactory.create_character("张飞")
    zhangfei_player = Player(zhangfei_char)
    
    game.add_player(zhangfei_player)
    
    # 创建咆哮技能实例
    paoxiao = PaoXiao()
    
    # 模拟使用杀
    sha_card = Card(name="杀", type=CardType.BASIC, suit="黑桃", point=7)
    
    # 测试技能触发
    if paoxiao.can_trigger(game, zhangfei_player, "play_card", card=sha_card):
        result = paoxiao.execute(game, zhangfei_player, card=sha_card)
        print(f"咆哮技能执行结果: {result}")
    else:
        print("咆哮技能无法触发")
    
    print()

def test_guanxing_skill():
    """测试诸葛亮的观星技能"""
    print("=== 测试诸葛亮观星技能 ===")
    
    game = create_test_game()
    zhugeliang_char = CharacterFactory.create_character("诸葛亮")
    zhugeliang_player = Player(zhugeliang_char)
    
    game.add_player(zhugeliang_player)
    
    # 初始化牌堆
    game.initialize_deck()
    
    # 创建观星技能实例
    guanxing = GuanXing()
    
    print(f"观星前牌堆剩余: {len(game.deck.cards)}")
    
    # 测试技能触发
    if guanxing.can_trigger(game, zhugeliang_player):
        result = guanxing.execute(game, zhugeliang_player)
        print(f"观星技能执行结果: {result}")
        print(f"观星后牌堆剩余: {len(game.deck.cards)}")
    else:
        print("观星技能无法触发")
    
    print()

def test_qixi_skill():
    """测试甘宁的奇袭技能"""
    print("=== 测试甘宁奇袭技能 ===")
    
    game = create_test_game()
    ganning_char = CharacterFactory.create_character("甘宁")
    ganning_player = Player(ganning_char)
    
    # 给甘宁一些黑色牌
    black_cards = [
        Card(name="杀", type=CardType.BASIC, suit="黑桃", point=7),
        Card(name="过河拆桥", type=CardType.TRICK, suit="梅花", point=10),
    ]
    ganning_player.hand_cards.extend(black_cards)
    
    game.add_player(ganning_player)
    
    # 创建奇袭技能实例
    qixi = QiXi()
    
    print(f"奇袭前甘宁手牌数: {len(ganning_player.hand_cards)}")
    
    # 测试技能触发
    if qixi.can_trigger(game, ganning_player):
        result = qixi.execute(game, ganning_player)
        print(f"奇袭技能执行结果: {result}")
        print(f"奇袭后甘宁手牌数: {len(ganning_player.hand_cards)}")
    else:
        print("奇袭技能无法触发")
    
    print()

def test_keji_skill():
    """测试吕蒙的克己技能"""
    print("=== 测试吕蒙克己技能 ===")
    
    game = create_test_game()
    lumeng_char = CharacterFactory.create_character("吕蒙")
    lumeng_player = Player(lumeng_char)
    
    # 设置玩家没有使用过杀
    lumeng_player.has_used_sha = False
    
    game.add_player(lumeng_player)
    
    # 创建克己技能实例
    keji = KeJi()
    
    # 测试技能触发
    if keji.can_trigger(game, lumeng_player):
        result = keji.execute(game, lumeng_player)
        print(f"克己技能执行结果: {result}")
    else:
        print("克己技能无法触发")
    
    print()

def test_yingzi_skill():
    """测试周瑜的英姿技能"""
    print("=== 测试周瑜英姿技能 ===")
    
    game = create_test_game()
    zhouyu_char = CharacterFactory.create_character("周瑜")
    zhouyu_player = Player(zhouyu_char)
    
    game.add_player(zhouyu_player)
    game.current_player = zhouyu_player
    game.current_phase = 'draw'
    
    # 初始化牌堆
    game.initialize_deck()
    
    # 创建英姿技能实例
    yingzi = YingZi()
    
    print(f"英姿前周瑜手牌数: {len(zhouyu_player.hand_cards)}")
    
    # 测试技能触发
    if yingzi.can_trigger(game, zhouyu_player):
        result = yingzi.execute(game, zhouyu_player)
        print(f"英姿技能执行结果: {result}")
        print(f"英姿后周瑜手牌数: {len(zhouyu_player.hand_cards)}")
    else:
        print("英姿技能无法触发")
    
    print()

def test_skill_manager():
    """测试技能管理器"""
    print("=== 测试技能管理器 ===")
    
    skill_manager = SkillManager()
    
    # 注册技能
    skills = [
        JianXiong(), FanKui(), GangLie(), PaoXiao(),
        GuanXing(), QiXi(), KeJi(), YingZi()
    ]
    
    for skill in skills:
        skill_manager.register_skill(skill)
        print(f"✓ 注册技能: {skill.name}")
    
    # 测试获取技能
    jianxiong_skill = skill_manager.get_skill("奸雄")
    if jianxiong_skill:
        print(f"✓ 成功获取技能: {jianxiong_skill.name}")
    else:
        print("✗ 获取技能失败")
    
    print()

def main():
    """主测试函数"""
    print("三国杀武将技能测试")
    print("=" * 50)
    
    try:
        # 测试武将创建
        test_character_creation()
        
        # 测试具体技能
        test_jianxiong_skill()
        test_fankui_skill()
        test_paoxiao_skill()
        test_guanxing_skill()
        test_qixi_skill()
        test_keji_skill()
        test_yingzi_skill()
        
        # 测试技能管理器
        test_skill_manager()
        
        print("=" * 50)
        print("所有技能测试完成！")
        
    except Exception as e:
        print(f"测试过程中出现错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()