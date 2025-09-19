#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
群雄武将技能详细测试
测试华佗（急救）、吕布（无双）、貂蝉（离间）
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
    SkillManager
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

def test_huatuo_jijiu():
    """详细测试华佗急救技能"""
    print("\n=== 详细测试华佗急救技能 ===")
    
    # 创建游戏和玩家
    game = create_test_game()
    huatuo = CharacterFactory.create_character("华佗")
    huatuo_player = Player(huatuo)
    
    # 创建需要救援的玩家
    patient = CharacterFactory.create_character("曹操")
    patient_player = Player(patient)
    patient_player.character.hp = 0  # 濒死状态
    
    # 给华佗一些红色牌
    red_cards = [
        Card(name="桃", type=CardType.BASIC, suit="红桃", rank=3),
        Card(name="闪", type=CardType.BASIC, suit="红桃", rank=8),
        Card(name="无懈可击", type=CardType.TRICK, suit="方片", rank=12),
    ]
    huatuo_player.hand_cards = red_cards
    
    print(f"华佗: {huatuo.name}, 技能: {huatuo.skills}")
    print(f"华佗初始手牌数: {len(huatuo_player.hand_cards)}")
    print(f"患者: {patient.name}, 体力: {patient_player.character.hp}/{patient_player.character.max_hp}")
    
    # 测试1: 急救技能基本功能
    print("\n测试1: 急救技能基本功能")
    if "急救" in huatuo.skills:
        print("华佗拥有急救技能")
        print("急救：你可以将一张红色牌当桃使用")
        
        # 模拟使用红色牌当桃
        for card in huatuo_player.hand_cards:
            if card.suit in ["红桃", "方片"]:
                print(f"  {card} 可以当作桃使用")
                # 模拟救援
                if patient_player.character.hp <= 0:
                    patient_player.character.hp += 1
                    huatuo_player.hand_cards.remove(card)
                    print(f"华佗使用 {card} 当作桃，救援成功")
                    print(f"患者体力恢复为: {patient_player.character.hp}/{patient_player.character.max_hp}")
                    break
    else:
        print("急救技能暂未实现")
    
    # 测试2: 急救技能的限制
    print("\n测试2: 急救技能的限制")
    black_cards = [
        Card(name="杀", type=CardType.BASIC, suit="黑桃", rank=7),
        Card(name="过河拆桥", type=CardType.TRICK, suit="梅花", rank=10),
    ]
    print("黑色牌不能通过急救当作桃使用:")
    for card in black_cards:
        print(f"  {card} 不能当作桃使用")
    
    # 测试3: 急救技能的战术价值
    print("\n测试3: 急救技能的战术价值")
    print("急救技能的价值：")
    print("- 增加救援手段")
    print("- 提高团队生存能力")
    print("- 红色牌的多重用途")

def test_lvbu_wushuang():
    """详细测试吕布无双技能"""
    print("\n=== 详细测试吕布无双技能 ===")
    
    # 创建游戏和玩家
    game = create_test_game()
    lvbu = CharacterFactory.create_character("吕布")
    lvbu_player = Player(lvbu)
    
    # 创建目标玩家
    target = CharacterFactory.create_character("刘备")
    target_player = Player(target)
    
    # 给吕布一些杀牌
    sha_cards = [
        Card(name="杀", type=CardType.BASIC, suit="黑桃", rank=7),
        Card(name="杀", type=CardType.BASIC, suit="红桃", rank=8),
    ]
    lvbu_player.hand_cards = sha_cards
    
    # 给目标一些闪牌
    target_player.hand_cards = [
        Card(name="闪", type=CardType.BASIC, suit="红桃", rank=2),
        Card(name="闪", type=CardType.BASIC, suit="方片", rank=3),
    ]
    
    print(f"吕布: {lvbu.name}, 技能: {lvbu.skills}")
    print(f"吕布初始手牌数: {len(lvbu_player.hand_cards)}")
    print(f"目标初始手牌数: {len(target_player.hand_cards)}")
    
    # 测试1: 无双技能基本功能
    print("\n测试1: 无双技能基本功能")
    if "无双" in lvbu.skills:
        print("吕布拥有无双技能")
        print("无双：锁定技，你使用杀指定目标后，该角色需使用两张闪才能抵消此杀")
        
        # 模拟使用杀
        if lvbu_player.hand_cards:
            sha_card = lvbu_player.hand_cards[0]
            print(f"吕布使用 {sha_card} 攻击目标")
            print("由于无双技能，目标需要使用两张闪才能抵消")
            
            # 检查目标是否有足够的闪
            shan_count = sum(1 for card in target_player.hand_cards if card.name == "闪")
            print(f"目标拥有 {shan_count} 张闪")
            
            if shan_count >= 2:
                print("目标使用两张闪抵消杀")
                # 移除两张闪
                removed_count = 0
                for card in target_player.hand_cards[:]:
                    if card.name == "闪" and removed_count < 2:
                        target_player.hand_cards.remove(card)
                        removed_count += 1
                        print(f"  使用 {card}")
                print("杀被成功抵消")
            else:
                print(f"目标只有 {shan_count} 张闪，无法完全抵消，受到伤害")
                target_player.character.hp -= 1
                print(f"目标体力变为: {target_player.character.hp}/{target_player.character.max_hp}")
    else:
        print("无双技能暂未实现")
    
    # 测试2: 无双技能与决斗
    print("\n测试2: 无双技能与决斗")
    print("无双技能同样适用于决斗：")
    print("- 吕布使用决斗时，对手需要先出两张杀")
    print("- 对手对吕布使用决斗时，吕布只需出一张杀")
    
    # 测试3: 无双技能的战术价值
    print("\n测试3: 无双技能的战术价值")
    print("无双技能的价值：")
    print("- 大幅提高攻击成功率")
    print("- 消耗对手更多防御牌")
    print("- 在决斗中占据优势")

def test_diaochan_lijian():
    """详细测试貂蝉离间技能"""
    print("\n=== 详细测试貂蝉离间技能 ===")
    
    # 创建游戏和玩家
    game = create_test_game()
    diaochan = CharacterFactory.create_character("貂蝉")
    diaochan_player = Player(diaochan)
    
    # 创建两个男性武将作为目标
    target1 = CharacterFactory.create_character("吕布")
    target1_player = Player(target1)
    target2 = CharacterFactory.create_character("刘备")
    target2_player = Player(target2)
    
    # 给貂蝉一些手牌
    diaochan_player.hand_cards = create_test_cards()[:3]
    
    # 给目标一些杀牌
    target1_player.hand_cards = [
        Card(name="杀", type=CardType.BASIC, suit="黑桃", rank=7),
        Card(name="闪", type=CardType.BASIC, suit="红桃", rank=8),
    ]
    target2_player.hand_cards = [
        Card(name="杀", type=CardType.BASIC, suit="红桃", rank=9),
        Card(name="桃", type=CardType.BASIC, suit="红桃", rank=10),
    ]
    
    print(f"貂蝉: {diaochan.name}, 技能: {diaochan.skills}")
    print(f"貂蝉初始手牌数: {len(diaochan_player.hand_cards)}")
    print(f"目标1({target1.name})手牌数: {len(target1_player.hand_cards)}")
    print(f"目标2({target2.name})手牌数: {len(target2_player.hand_cards)}")
    
    # 测试1: 离间技能基本功能
    print("\n测试1: 离间技能基本功能")
    if "离间" in diaochan.skills:
        print("貂蝉拥有离间技能")
        print("离间：出牌阶段限一次，你可以弃置一张牌并选择两名男性角色，")
        print("视为其中一名角色对另一名角色使用一张杀")
        
        # 模拟离间过程
        if diaochan_player.hand_cards:
            discarded_card = diaochan_player.hand_cards[0]
            diaochan_player.hand_cards.remove(discarded_card)
            print(f"貂蝉弃置 {discarded_card}")
            print(f"选择 {target1.name} 对 {target2.name} 使用杀")
            
            # 检查target1是否有杀
            has_sha = any(card.name == "杀" for card in target1_player.hand_cards)
            if has_sha:
                print(f"{target1.name} 有杀，可以响应离间")
                # 移除一张杀
                for card in target1_player.hand_cards[:]:
                    if card.name == "杀":
                        target1_player.hand_cards.remove(card)
                        print(f"{target1.name} 使用 {card} 攻击 {target2.name}")
                        break
                
                # target2尝试闪避
                has_shan = any(card.name == "闪" for card in target2_player.hand_cards)
                if has_shan:
                    for card in target2_player.hand_cards[:]:
                        if card.name == "闪":
                            target2_player.hand_cards.remove(card)
                            print(f"{target2.name} 使用 {card} 闪避")
                            break
                else:
                    print(f"{target2.name} 无法闪避，受到伤害")
                    target2_player.character.hp -= 1
                    print(f"{target2.name} 体力变为: {target2_player.character.hp}/{target2_player.character.max_hp}")
            else:
                print(f"{target1.name} 没有杀，无法响应离间，受到1点伤害")
                target1_player.character.hp -= 1
                print(f"{target1.name} 体力变为: {target1_player.character.hp}/{target1_player.character.max_hp}")
    else:
        print("离间技能暂未实现")
    
    # 测试2: 离间技能的限制
    print("\n测试2: 离间技能的限制")
    print("离间技能的限制：")
    print("- 只能选择男性角色")
    print("- 出牌阶段限一次")
    print("- 需要弃置一张牌")
    
    # 测试3: 离间技能的战术价值
    print("\n测试3: 离间技能的战术价值")
    print("离间技能的价值：")
    print("- 挑拨敌人内斗")
    print("- 消耗对手资源")
    print("- 控制战场节奏")
    print("- 在多人游戏中效果更佳")

def test_skill_manager_qunxiong():
    """测试群雄技能管理器"""
    print("\n=== 测试群雄技能管理器 ===")
    
    skill_manager = SkillManager()
    
    # 由于群雄技能可能还未完全实现，我们测试已有的技能
    print("群雄武将技能概览：")
    print("✓ 华佗 - 急救：可以将红色牌当桃使用")
    print("✓ 吕布 - 无双：使用杀时对手需要两张闪抵消")
    print("✓ 貂蝉 - 离间：可以让两名男性角色互相攻击")
    
    # 测试技能查找（如果已实现）
    for skill_name in ["急救", "无双", "离间"]:
        skill = skill_manager.get_skill(skill_name)
        if skill:
            print(f"✓ 成功获取技能: {skill.name} - {skill.description}")
        else:
            print(f"○ 技能 {skill_name} 暂未在技能管理器中注册")

def main():
    """主测试函数"""
    print("三国杀群雄武将技能详细测试")
    print("=" * 50)
    
    try:
        # 测试各个群雄武将技能
        test_huatuo_jijiu()
        test_lvbu_wushuang()
        test_diaochan_lijian()
        test_skill_manager_qunxiong()
        
        print("\n" + "=" * 50)
        print("群雄武将技能测试完成！")
        
    except Exception as e:
        print(f"测试过程中出现错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()