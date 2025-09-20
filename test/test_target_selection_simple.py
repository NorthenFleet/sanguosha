#!/usr/bin/env python3
"""
简化的锦囊牌目标选择功能测试
专门测试目标选择机制，不涉及无懈可击等复杂逻辑
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.base.game import Game
from app.models.player import Player
from app.models.character import Character, Kingdom
from app.models.card import Card
from app.core.events.event_system import EventManager
from app.core.target_selection import CardTargetSelector


def create_test_game():
    """创建测试游戏环境"""
    # 创建事件管理器
    event_manager = EventManager()
    
    # 创建游戏
    game = Game(event_manager)
    
    # 创建角色
    char1 = Character("刘备", Kingdom.SHU, 4, ["仁德", "激将"])
    char2 = Character("关羽", Kingdom.SHU, 4, ["武圣"])
    char3 = Character("张飞", Kingdom.SHU, 4, ["咆哮"])
    char4 = Character("诸葛亮", Kingdom.SHU, 3, ["观星", "空城"])
    
    # 创建玩家
    player1 = Player(char1)
    player2 = Player(char2)
    player3 = Player(char3)
    player4 = Player(char4)
    
    # 添加玩家到游戏
    game.players = [player1, player2, player3, player4]
    
    return game, player1, player2, player3, player4


def test_jiedao_target_selection():
    """测试借刀杀人的目标选择"""
    print("\n=== 测试借刀杀人目标选择 ===")
    
    game, player1, player2, player3, player4 = create_test_game()
    
    # 给player2装备武器
    weapon = Card(name="青龙偃月刀", category="equipment", subtype="weapon", suit="黑桃", rank=5)
    player2.equipped.append(weapon)
    player2.weapon = weapon
    
    # 给player2一张杀
    player2.hand_cards = [Card(name="杀", category="basic", suit="黑桃", rank=7)]
    
    print(f"玩家2({player2.character.name})装备: {player2.weapon.name if player2.weapon else '无'}")
    print(f"玩家2({player2.character.name})手牌: {[card.name for card in player2.hand_cards]}")
    
    # 创建目标选择器
    selector = CardTargetSelector()
    
    # 测试借刀杀人目标选择
    print(f"\n{player1.character.name} 使用借刀杀人")
    weapon_holder, attack_target = selector.select_jiedao_targets(game, player1)
    
    if weapon_holder and attack_target:
        print(f"选择的武器持有者: {weapon_holder.character.name}")
        print(f"选择的攻击目标: {attack_target.character.name}")
        print("借刀杀人目标选择: ✓ 成功")
        return True
    else:
        print("借刀杀人目标选择: ✗ 失败")
        return False


def test_guohe_target_selection():
    """测试过河拆桥的目标选择"""
    print("\n=== 测试过河拆桥目标选择 ===")
    
    game, player1, player2, player3, player4 = create_test_game()
    
    # 给其他玩家一些手牌和装备
    player2.hand_cards = [Card(name="杀", category="basic", suit="黑桃", rank=7)]
    armor = Card(name="八卦阵", category="equipment", subtype="armor", suit="梅花", rank=2)
    player3.equipped.append(armor)
    player3.armor = armor
    
    print(f"玩家2({player2.character.name})手牌: {[card.name for card in player2.hand_cards]}")
    print(f"玩家3({player3.character.name})装备: {[card.name for card in player3.equipped]}")
    
    # 创建目标选择器
    selector = CardTargetSelector()
    
    # 测试过河拆桥目标选择
    print(f"\n{player1.character.name} 使用过河拆桥")
    target = selector.select_guohe_target(game, player1)
    
    if target:
        print(f"选择的目标: {target.character.name}")
        print("过河拆桥目标选择: ✓ 成功")
        return True
    else:
        print("过河拆桥目标选择: ✗ 失败")
        return False


def test_shunshou_target_selection():
    """测试顺手牵羊的目标选择"""
    print("\n=== 测试顺手牵羊目标选择 ===")
    
    game, player1, player2, player3, player4 = create_test_game()
    
    # 给相邻玩家一些手牌（距离为1）
    player2.hand_cards = [Card(name="杀", category="basic", suit="黑桃", rank=7)]
    player4.hand_cards = [Card(name="桃", category="basic", suit="红桃", rank=9)]
    
    print(f"玩家2({player2.character.name})手牌: {[card.name for card in player2.hand_cards]}")
    print(f"玩家4({player4.character.name})手牌: {[card.name for card in player4.hand_cards]}")
    
    # 创建目标选择器
    selector = CardTargetSelector()
    
    # 测试顺手牵羊目标选择
    print(f"\n{player1.character.name} 使用顺手牵羊")
    target = selector.select_shunshou_target(game, player1)
    
    if target:
        print(f"选择的目标: {target.character.name}")
        print("顺手牵羊目标选择: ✓ 成功")
        return True
    else:
        print("顺手牵羊目标选择: ✗ 失败")
        return False


def test_juedou_target_selection():
    """测试决斗的目标选择"""
    print("\n=== 测试决斗目标选择 ===")
    
    game, player1, player2, player3, player4 = create_test_game()
    
    # 给玩家一些手牌
    player1.hand_cards = [Card(name="杀", category="basic", suit="黑桃", rank=7)]
    player2.hand_cards = [Card(name="杀", category="basic", suit="红桃", rank=8)]
    
    print(f"玩家1({player1.character.name})手牌: {[card.name for card in player1.hand_cards]}")
    print(f"玩家2({player2.character.name})手牌: {[card.name for card in player2.hand_cards]}")
    
    # 创建目标选择器
    selector = CardTargetSelector()
    
    # 测试决斗目标选择
    print(f"\n{player1.character.name} 使用决斗")
    target = selector.select_juedou_target(game, player1)
    
    if target:
        print(f"选择的目标: {target.character.name}")
        print("决斗目标选择: ✓ 成功")
        return True
    else:
        print("决斗目标选择: ✗ 失败")
        return False


def main():
    """主测试函数"""
    print("开始测试锦囊牌目标选择功能...")
    
    # 测试各种锦囊牌的目标选择
    results = []
    
    try:
        results.append(("借刀杀人", test_jiedao_target_selection()))
        results.append(("过河拆桥", test_guohe_target_selection()))
        results.append(("顺手牵羊", test_shunshou_target_selection()))
        results.append(("决斗", test_juedou_target_selection()))
    except Exception as e:
        print(f"测试过程中出现异常: {e}")
        import traceback
        traceback.print_exc()
    
    # 输出测试结果
    print("\n=== 测试结果汇总 ===")
    for card_name, result in results:
        status = "✓ 通过" if result else "✗ 失败"
        print(f"{card_name}: {status}")
    
    all_passed = all(result for _, result in results)
    print(f"\n总体结果: {'所有测试通过' if all_passed else '部分测试失败'}")
    
    return all_passed


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)