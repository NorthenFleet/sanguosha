#!/usr/bin/env python3
"""
简单装备系统测试
"""

import sys
sys.path.append('.')

from app.models.player import Player
from app.models.character import Character
from app.models.card import Card, Deck
from app.models.enums import CardType

# 创建测试用的装备牌
weapon_card = Card(name="青龙偃月刀", type=CardType.EQUIP, category="equipment", suit="红桃", rank=11, subtype="weapon")
armor_card = Card(name="八卦阵", type=CardType.EQUIP, category="equipment", suit="梅花", rank=12, subtype="armor")
horse_card = Card(name="赤兔", type=CardType.EQUIP, category="equipment", suit="方片", rank=5, subtype="horse")

print("=== 测试装备安装功能 ===")

# 创建玩家
character = Character("关羽", "蜀", 4, ["武圣"])
player = Player(character)

# 添加装备牌到手牌
player.hand_cards = [weapon_card, armor_card, horse_card]

print(f"初始手牌数量: {len(player.hand_cards)}")
print(f"初始装备: 武器={player.weapon}, 防御={player.defense}, 进攻马={player.attack_horse}")

# 测试装备牌类型检测
print(f"\n装备牌类型检测:")
print(f"青龙偃月刀 - type: {weapon_card.type}, category: {weapon_card.category}, subtype: {weapon_card.subtype}")
print(f"八卦阵 - type: {armor_card.type}, category: {armor_card.category}, subtype: {armor_card.subtype}")
print(f"赤兔 - type: {horse_card.type}, category: {horse_card.category}, subtype: {horse_card.subtype}")

# 使用装备牌
print(f"\n使用青龙偃月刀...")
player.use_card(weapon_card)
print(f"装备后: 武器={player.weapon.name if player.weapon else '无'}")
print(f"手牌数量: {len(player.hand_cards)}")

print(f"\n使用八卦阵...")
player.use_card(armor_card)
print(f"装备后: 防御={player.defense.name if player.defense else '无'}")
print(f"手牌数量: {len(player.hand_cards)}")

print(f"\n使用赤兔...")
player.use_card(horse_card)
print(f"装备后: 进攻马={player.attack_horse.name if player.attack_horse else '无'}")
print(f"手牌数量: {len(player.hand_cards)}")

print(f"\n最终装备列表: {[eq.name for eq in player.equipped]}")

# 验证装备是否正确安装
success = (
    player.weapon and player.weapon.name == "青龙偃月刀" and
    player.defense and player.defense.name == "八卦阵" and
    player.attack_horse and player.attack_horse.name == "赤兔" and
    len(player.hand_cards) == 0
)

print(f"\n装备安装测试: {'✅ 成功' if success else '❌ 失败'}")

def test_equipment_installation():
    """测试装备安装功能"""
    return success

if __name__ == "__main__":
    test_equipment_installation()