#!/usr/bin/env python3
"""
武器和防御装备效果测试
测试各种武器的攻击效果和防御装备的防护效果
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.models.player import Player
from app.models.character import Character, Kingdom
from app.models.card import Card
from app.core.equipment_judgment import equipment_judgment


def create_test_card(name, card_type="装备", suit="红桃", point=1, damage_type=None):
    """创建测试卡牌"""
    card = Card(name=name, card_type=card_type, suit=suit, point=point)
    if damage_type:
        card.damage_type = damage_type
    return card


def create_test_players():
    """创建测试玩家"""
    characters = [
        ("刘备", Kingdom.SHU, "male"),
        ("关羽", Kingdom.SHU, "male"), 
        ("张飞", Kingdom.SHU, "male"),
        ("貂蝉", Kingdom.QUN, "female"),
        ("曹操", Kingdom.WEI, "male")
    ]
    
    players = []
    for i, (name, kingdom, gender) in enumerate(characters):
        character = Character(name, kingdom, 4, [])
        character.gender = gender  # 添加性别属性用于雌雄双股剑测试
        player = Player(character)
        player.position = i
        players.append(player)
    
    return players


def test_weapon_attack_ranges():
    """测试武器攻击范围"""
    print("=== 测试武器攻击范围 ===")
    
    players = create_test_players()
    attacker = players[0]
    
    weapons = [
        ("青龙偃月刀", 3),
        ("丈八蛇矛", 3),
        ("方天画戟", 4),
        ("麒麟弓", 5),
        ("古锭刀", 2),
        ("朱雀羽扇", 4),
        ("雌雄双股剑", 2)
    ]
    
    for weapon_name, expected_range in weapons:
        weapon = create_test_card(weapon_name)
        attacker.weapon = weapon
        actual_range = attacker.get_attack_range()
        status = "✓" if actual_range == expected_range else "✗"
        print(f"{weapon_name}: 期望范围={expected_range}, 实际范围={actual_range} {status}")
    
    print()


def test_weapon_effects():
    """测试武器特殊效果"""
    print("=== 测试武器特殊效果 ===")
    
    players = create_test_players()
    attacker = players[0]
    target = players[1]
    
    # 测试青龙偃月刀
    print("1. 测试青龙偃月刀效果:")
    attacker.weapon = create_test_card("青龙偃月刀")
    attacker.hand_cards = [create_test_card("杀", "基本牌")]
    sha_card = create_test_card("杀", "基本牌")
    
    context = {"trigger": "sha_dodged"}
    result = equipment_judgment.judge_weapon_effect(attacker, target, sha_card, context)
    print(f"  杀被闪抵消时: {result['description'] if result['can_trigger'] else '无法触发'}")
    
    # 测试丈八蛇矛
    print("\n2. 测试丈八蛇矛效果:")
    attacker.weapon = create_test_card("丈八蛇矛")
    attacker.hand_cards = [create_test_card("桃", "基本牌"), create_test_card("闪", "基本牌")]
    
    context = {"trigger": "need_sha"}
    result = equipment_judgment.judge_weapon_effect(attacker, target, None, context)
    print(f"  需要杀时: {result['description'] if result['can_trigger'] else '无法触发'}")
    
    # 测试方天画戟
    print("\n3. 测试方天画戟效果:")
    attacker.weapon = create_test_card("方天画戟")
    attacker.hand_cards = [create_test_card("杀", "基本牌")]  # 最后一张手牌
    sha_card = create_test_card("杀", "基本牌")
    
    context = {"trigger": "use_sha"}
    result = equipment_judgment.judge_weapon_effect(attacker, target, sha_card, context)
    print(f"  使用最后手牌杀时: {result['description'] if result['can_trigger'] else '无法触发'}")
    
    # 测试麒麟弓
    print("\n4. 测试麒麟弓效果:")
    attacker.weapon = create_test_card("麒麟弓")
    target.equipped = [create_test_card("八卦阵")]  # 目标有装备
    
    context = {"trigger": "sha_damage"}
    result = equipment_judgment.judge_weapon_effect(attacker, target, sha_card, context)
    print(f"  杀造成伤害时: {result['description'] if result['can_trigger'] else '无法触发'}")
    
    # 测试古锭刀
    print("\n5. 测试古锭刀效果:")
    attacker.weapon = create_test_card("古锭刀")
    target.hand_cards = []  # 目标无手牌
    
    context = {"trigger": "sha_damage"}
    result = equipment_judgment.judge_weapon_effect(attacker, target, sha_card, context)
    print(f"  对无手牌目标造成伤害: {result['description'] if result['can_trigger'] else '无法触发'}")
    
    # 测试雌雄双股剑
    print("\n6. 测试雌雄双股剑效果:")
    attacker.weapon = create_test_card("雌雄双股剑")
    female_target = players[3]  # 貂蝉（女性）
    
    context = {"trigger": "sha_target"}
    result = equipment_judgment.judge_weapon_effect(attacker, female_target, sha_card, context)
    print(f"  对异性目标使用杀: {result['description'] if result['can_trigger'] else '无法触发'}")
    
    print()


def test_defense_equipment_effects():
    """测试防御装备效果"""
    print("=== 测试防御装备效果 ===")
    
    players = create_test_players()
    attacker = players[0]
    defender = players[1]
    
    # 测试八卦阵
    print("1. 测试八卦阵效果:")
    defender.defense = create_test_card("八卦阵")
    
    context = {"trigger": "need_shan"}
    result = equipment_judgment.judge_defense_effect(defender, attacker, None, context)
    print(f"  需要闪时: {result['description'] if result['can_trigger'] else '无法触发'}")
    
    # 测试仁王盾
    print("\n2. 测试仁王盾效果:")
    defender.defense = create_test_card("仁王盾")
    black_sha = create_test_card("杀", "基本牌", "黑桃")
    red_sha = create_test_card("杀", "基本牌", "红桃")
    
    context = {"trigger": "receive_sha"}
    result1 = equipment_judgment.judge_defense_effect(defender, attacker, black_sha, context)
    result2 = equipment_judgment.judge_defense_effect(defender, attacker, red_sha, context)
    print(f"  受到黑色杀: {result1['description'] if result1['can_trigger'] else '无法触发'}")
    print(f"  受到红色杀: {result2['description'] if result2['can_trigger'] else '无法触发'}")
    
    # 测试白银狮子
    print("\n3. 测试白银狮子效果:")
    defender.defense = create_test_card("白银狮子")
    
    context1 = {"trigger": "receive_damage", "damage_amount": 2}
    context2 = {"trigger": "receive_damage", "damage_amount": 1}
    result1 = equipment_judgment.judge_defense_effect(defender, attacker, None, context1)
    result2 = equipment_judgment.judge_defense_effect(defender, attacker, None, context2)
    print(f"  受到2点伤害: {result1['description'] if result1['can_trigger'] else '无法触发'}")
    print(f"  受到1点伤害: {result2['description'] if result2['can_trigger'] else '无法触发'}")
    
    # 测试藤甲
    print("\n4. 测试藤甲效果:")
    defender.defense = create_test_card("藤甲")
    normal_sha = create_test_card("杀", "基本牌")
    fire_sha = create_test_card("杀", "基本牌", damage_type="fire")
    nanman = create_test_card("南蛮入侵", "锦囊牌")
    
    context = {"trigger": "receive_damage"}
    result1 = equipment_judgment.judge_defense_effect(defender, attacker, normal_sha, context)
    result2 = equipment_judgment.judge_defense_effect(defender, attacker, fire_sha, context)
    result3 = equipment_judgment.judge_defense_effect(defender, attacker, nanman, context)
    print(f"  受到普通杀: {result1['description'] if result1['can_trigger'] else '无法触发'}")
    print(f"  受到火杀: {result2['description'] if result2['can_trigger'] else '无法触发'}")
    print(f"  受到南蛮入侵: {result3['description'] if result3['can_trigger'] else '无法触发'}")
    
    print()


def test_damage_calculation():
    """测试伤害计算"""
    print("=== 测试伤害计算 ===")
    
    players = create_test_players()
    attacker = players[0]
    defender = players[1]
    
    # 测试古锭刀伤害增强
    print("1. 测试古锭刀伤害增强:")
    attacker.weapon = create_test_card("古锭刀")
    defender.hand_cards = []  # 无手牌
    sha_card = create_test_card("杀", "基本牌")
    
    base_damage = 1
    final_damage = equipment_judgment.calculate_final_damage(attacker, defender, base_damage, sha_card)
    print(f"  基础伤害: {base_damage}, 最终伤害: {final_damage}")
    
    # 测试白银狮子伤害减免
    print("\n2. 测试白银狮子伤害减免:")
    attacker.weapon = None
    defender.defense = create_test_card("白银狮子")
    
    base_damage = 3
    final_damage = equipment_judgment.calculate_final_damage(attacker, defender, base_damage, sha_card)
    print(f"  基础伤害: {base_damage}, 最终伤害: {final_damage}")
    
    # 测试藤甲火焰伤害增强
    print("\n3. 测试藤甲火焰伤害:")
    defender.defense = create_test_card("藤甲")
    fire_sha = create_test_card("杀", "基本牌", damage_type="fire")
    
    base_damage = 1
    final_damage = equipment_judgment.calculate_final_damage(attacker, defender, base_damage, fire_sha)
    print(f"  基础火焰伤害: {base_damage}, 最终伤害: {final_damage}")
    
    print()


def test_complex_scenarios():
    """测试复杂场景"""
    print("=== 测试复杂场景 ===")
    
    players = create_test_players()
    attacker = players[0]
    defender = players[1]
    
    # 场景1: 古锭刀 vs 白银狮子
    print("1. 古锭刀 vs 白银狮子:")
    attacker.weapon = create_test_card("古锭刀")
    defender.defense = create_test_card("白银狮子")
    defender.hand_cards = []  # 无手牌触发古锭刀
    
    sha_card = create_test_card("杀", "基本牌")
    base_damage = 1
    final_damage = equipment_judgment.calculate_final_damage(attacker, defender, base_damage, sha_card)
    print(f"  古锭刀+1伤害，白银狮子减免到1点，最终伤害: {final_damage}")
    
    # 场景2: 朱雀羽扇火杀 vs 藤甲
    print("\n2. 朱雀羽扇火杀 vs 藤甲:")
    attacker.weapon = create_test_card("朱雀羽扇")
    defender.defense = create_test_card("藤甲")
    
    fire_sha = create_test_card("杀", "基本牌", damage_type="fire")
    base_damage = 1
    final_damage = equipment_judgment.calculate_final_damage(attacker, defender, base_damage, fire_sha)
    print(f"  火杀对藤甲+1伤害，最终伤害: {final_damage}")
    
    # 场景3: 麒麟弓破坏装备
    print("\n3. 麒麟弓破坏装备测试:")
    attacker.weapon = create_test_card("麒麟弓")
    defender.equipped = [create_test_card("八卦阵"), create_test_card("赤兔")]
    
    context = {"trigger": "sha_damage"}
    result = equipment_judgment.judge_weapon_effect(attacker, defender, sha_card, context)
    print(f"  {result['description'] if result['can_trigger'] else '无法触发'}")
    print(f"  目标装备数量: {len(defender.equipped)}")
    
    print()


def main():
    """主测试函数"""
    print("武器和防御装备效果测试")
    print("=" * 50)
    
    test_weapon_attack_ranges()
    test_weapon_effects()
    test_defense_equipment_effects()
    test_damage_calculation()
    test_complex_scenarios()
    
    print("所有测试完成！")


if __name__ == "__main__":
    main()