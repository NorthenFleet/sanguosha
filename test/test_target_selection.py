#!/usr/bin/env python3
"""
测试锦囊牌目标选择功能
验证借刀杀人、过河拆桥、顺手牵羊、决斗等卡牌的目标选择机制
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.core.base.game import Game
from app.models.player import Player
from app.models.character import Character, Kingdom
from app.models.card import Card
from app.models.card_actions import JieDaoShaRenAction, GuoHeChaiQiaoAction, ShunShouQianYangAction, JueDouAction
from app.core.events.event_system import EventManager


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


def setup_jiedao_test_scenario(game, player1, player2, player3, player4):
    """设置借刀杀人测试场景"""
    # 给player2装备武器
    weapon = Card(name="青龙偃月刀", category="equipment", subtype="weapon", suit="黑桃", rank=5)
    player2.equipped.append(weapon)
    player2.weapon = weapon
    
    # 给player1借刀杀人卡牌
    jiedao_card = Card(name="借刀杀人", category="trick", suit="梅花", rank=12)
    player1.hand_cards = [jiedao_card]
    
    # 给其他玩家一些手牌
    player2.hand_cards = [Card(name="杀", category="basic", suit="黑桃", rank=7)]
    player3.hand_cards = [Card(name="闪", category="basic", suit="红桃", rank=8)]
    player4.hand_cards = [Card(name="桃", category="basic", suit="红桃", rank=9)]
    
    print("=== 借刀杀人测试场景设置完成 ===")
    print(f"玩家1({player1.character.name})手牌: {[card.name for card in player1.hand_cards]}")
    print(f"玩家2({player2.character.name})装备: {player2.weapon.name if player2.weapon else '无'}")
    print(f"玩家2({player2.character.name})手牌: {[card.name for card in player2.hand_cards]}")
    print(f"玩家3({player3.character.name})手牌: {[card.name for card in player3.hand_cards]}")
    print(f"玩家4({player4.character.name})手牌: {[card.name for card in player4.hand_cards]}")


def setup_guohe_test_scenario(game, player1, player2, player3, player4):
    """设置过河拆桥测试场景"""
    # 给player1过河拆桥卡牌
    guohe_card = Card(name="过河拆桥", category="trick", suit="黑桃", rank=3)
    player1.hand_cards = [guohe_card]
    
    # 给其他玩家一些手牌和装备
    player2.hand_cards = [Card(name="杀", category="basic", suit="黑桃", rank=7), 
                          Card(name="闪", category="basic", suit="红桃", rank=8)]
    player3.hand_cards = [Card(name="桃", category="basic", suit="红桃", rank=9)]
    
    # 给player4装备
    armor = Card(name="八卦阵", category="equipment", subtype="armor", suit="梅花", rank=2)
    player4.equipped.append(armor)
    player4.armor = armor
    player4.hand_cards = [Card(name="无懈可击", category="trick", suit="梅花", rank=11)]
    
    print("=== 过河拆桥测试场景设置完成 ===")
    print(f"玩家1({player1.character.name})手牌: {[card.name for card in player1.hand_cards]}")
    print(f"玩家2({player2.character.name})手牌: {[card.name for card in player2.hand_cards]}")
    print(f"玩家3({player3.character.name})手牌: {[card.name for card in player3.hand_cards]}")
    print(f"玩家4({player4.character.name})装备: {[card.name for card in player4.equipped]}")
    print(f"玩家4({player4.character.name})手牌: {[card.name for card in player4.hand_cards]}")


def setup_shunshou_test_scenario(game, player1, player2, player3, player4):
    """设置顺手牵羊测试场景"""
    # 给player1顺手牵羊卡牌
    shunshou_card = Card(name="顺手牵羊", category="trick", suit="黑桃", rank=3)
    player1.hand_cards = [shunshou_card]
    
    # 给相邻玩家一些手牌（距离为1）
    player2.hand_cards = [Card(name="杀", category="basic", suit="黑桃", rank=7), 
                          Card(name="闪", category="basic", suit="红桃", rank=8)]
    player4.hand_cards = [Card(name="桃", category="basic", suit="红桃", rank=9)]
    
    # 给player3装备（距离为2，不能被顺手牵羊）
    weapon = Card(name="丈八蛇矛", category="equipment", subtype="weapon", suit="黑桃", rank=12)
    player3.equipped.append(weapon)
    player3.weapon = weapon
    player3.hand_cards = [Card(name="无懈可击", category="trick", suit="梅花", rank=11)]
    
    print("=== 顺手牵羊测试场景设置完成 ===")
    print(f"玩家1({player1.character.name})手牌: {[card.name for card in player1.hand_cards]}")
    print(f"玩家2({player2.character.name})手牌: {[card.name for card in player2.hand_cards]}")
    print(f"玩家3({player3.character.name})装备: {[card.name for card in player3.equipped]}")
    print(f"玩家4({player4.character.name})手牌: {[card.name for card in player4.hand_cards]}")


def setup_juedou_test_scenario(game, player1, player2, player3, player4):
    """设置决斗测试场景"""
    # 给player1决斗卡牌
    juedou_card = Card(name="决斗", category="trick", suit="黑桃", rank=1)
    player1.hand_cards = [juedou_card, Card(name="杀", category="basic", suit="黑桃", rank=7)]
    
    # 给其他玩家一些手牌
    player2.hand_cards = [Card(name="杀", category="basic", suit="黑桃", rank=7), 
                          Card(name="闪", category="basic", suit="红桃", rank=8)]
    player3.hand_cards = [Card(name="桃", category="basic", suit="红桃", rank=9)]
    player4.hand_cards = [Card(name="无懈可击", category="trick", suit="梅花", rank=11)]
    
    print("=== 决斗测试场景设置完成 ===")
    print(f"玩家1({player1.character.name})手牌: {[card.name for card in player1.hand_cards]}")
    print(f"玩家2({player2.character.name})手牌: {[card.name for card in player2.hand_cards]}")
    print(f"玩家3({player3.character.name})手牌: {[card.name for card in player3.hand_cards]}")
    print(f"玩家4({player4.character.name})手牌: {[card.name for card in player4.hand_cards]}")


def test_jiedao_target_selection():
    """测试借刀杀人的目标选择"""
    print("\n=== 测试借刀杀人目标选择 ===")
    
    game, player1, player2, player3, player4 = create_test_game()
    setup_jiedao_test_scenario(game, player1, player2, player3, player4)
    
    # 设置测试模式
    game.current_phase = "test"
    
    # 创建借刀杀人动作
    jiedao_action = JieDaoShaRenAction()
    
    # 执行借刀杀人
    print(f"\n{player1.character.name} 使用借刀杀人")
    result = jiedao_action.apply_effect(game, player1)
    
    print(f"借刀杀人结果: {'成功' if result else '失败'}")
    return result


def test_guohe_target_selection():
    """测试过河拆桥的目标选择"""
    print("\n=== 测试过河拆桥目标选择 ===")
    
    game, player1, player2, player3, player4 = create_test_game()
    setup_guohe_test_scenario(game, player1, player2, player3, player4)
    
    # 设置测试模式
    game.current_phase = "test"
    
    # 创建过河拆桥动作
    guohe_action = GuoHeChaiQiaoAction()
    
    # 执行过河拆桥
    print(f"\n{player1.character.name} 使用过河拆桥")
    result = guohe_action.apply_effect(game, player1)
    
    print(f"过河拆桥结果: {'成功' if result else '失败'}")
    return result


def test_shunshou_target_selection():
    """测试顺手牵羊的目标选择"""
    print("\n=== 测试顺手牵羊目标选择 ===")
    
    game, player1, player2, player3, player4 = create_test_game()
    setup_shunshou_test_scenario(game, player1, player2, player3, player4)
    
    # 设置测试模式
    game.current_phase = "test"
    
    # 创建顺手牵羊动作
    shunshou_action = ShunShouQianYangAction()
    
    # 执行顺手牵羊
    print(f"\n{player1.character.name} 使用顺手牵羊")
    result = shunshou_action.apply_effect(game, player1)
    
    print(f"顺手牵羊结果: {'成功' if result else '失败'}")
    return result


def test_juedou_target_selection():
    """测试决斗的目标选择"""
    print("\n=== 测试决斗目标选择 ===")
    
    game, player1, player2, player3, player4 = create_test_game()
    setup_juedou_test_scenario(game, player1, player2, player3, player4)
    
    # 设置测试模式
    game.current_phase = "test"
    
    # 创建决斗动作
    juedou_action = JueDouAction()
    
    # 执行决斗
    print(f"\n{player1.character.name} 使用决斗")
    result = juedou_action.apply_effect(game, player1)
    
    print(f"决斗结果: {'成功' if result else '失败'}")
    return result


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