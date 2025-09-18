#!/usr/bin/env python3
"""
过河拆桥交互功能测试脚本
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.models.card import Card
from app.models.player import Player
from app.models.character import Character
from app.models.enums import CardType
from app.models.card_actions import GuoHeChaiQiaoAction
from app.core.game import Game
from app.core.event_system import EventManager

def create_test_game():
    """创建测试游戏环境"""
    event_manager = EventManager()
    game = Game(event_manager)
    
    # 创建测试角色
    character1 = Character("曹操", "魏", 4, ["奸雄"])
    character2 = Character("刘备", "蜀", 4, ["仁德"])
    
    # 创建玩家
    player1 = Player(character1)
    player2 = Player(character2)
    
    # 添加玩家到游戏
    game.add_player(player1)
    game.add_player(player2)
    
    return game, player1, player2

def setup_test_cards(player):
    """为玩家设置测试卡牌"""
    # 添加手牌
    hand_cards = [
        Card("杀", CardType.BASIC, "♠", 7),
        Card("闪", CardType.BASIC, "♥", 2),
        Card("桃", CardType.BASIC, "♦", 3)
    ]
    player.hand_cards.extend(hand_cards)
    
    # 添加装备
    weapon = Card("青龙偃月刀", CardType.EQUIP, "♠", 5)
    armor = Card("八卦阵", CardType.EQUIP, "♠", 2)
    player.equipped.extend([weapon, armor])
    player.weapon = weapon
    player.armor = armor
    
    # 添加判定区卡牌
    judgment_card = Card("乐不思蜀", CardType.TRICK, "♥", 6)
    player.judgment_area.append(judgment_card)

def test_guohe_selection():
    """测试过河拆桥的选择功能"""
    print("=== 过河拆桥选择功能测试 ===")
    
    # 创建游戏环境
    game, player1, player2 = create_test_game()
    
    # 设置测试卡牌
    setup_test_cards(player2)
    
    # 显示目标玩家状态
    print(f"\n目标玩家 {player2.character.name} 的状态:")
    print(f"手牌数量: {len(player2.hand_cards)}")
    for i, card in enumerate(player2.hand_cards):
        print(f"  手牌{i+1}: {card.name}")
    
    print(f"装备数量: {len(player2.equipped)}")
    for i, card in enumerate(player2.equipped):
        print(f"  装备{i+1}: {card.name}")
    
    print(f"判定区数量: {len(player2.judgment_area)}")
    for i, card in enumerate(player2.judgment_area):
        print(f"  判定区{i+1}: {card.name}")
    
    # 创建过河拆桥动作
    action = GuoHeChaiQiaoAction()
    
    # 测试选择机制（测试模式）
    print("\n--- 测试模式选择 ---")
    selected_card, area_type = action._select_card_from_opponent(
        player2, game, player1, test_mode=True
    )
    print(f"测试模式自动选择: {selected_card.name} (来自{area_type})")
    
    # 测试完整的apply_effect方法
    print("\n--- 测试完整效果 ---")
    original_counts = {
        'hand': len(player2.hand_cards),
        'equipment': len(player2.equipped),
        'judgment': len(player2.judgment_area)
    }
    
    # 设置测试模式
    game.current_phase = "test"
    
    # 执行过河拆桥
    result = action.apply_effect(game, player1, player2)
    
    print(f"执行结果: {result}")
    print(f"手牌变化: {original_counts['hand']} -> {len(player2.hand_cards)}")
    print(f"装备变化: {original_counts['equipment']} -> {len(player2.equipped)}")
    print(f"判定区变化: {original_counts['judgment']} -> {len(player2.judgment_area)}")
    
    return True

def test_area_selection_logic():
    """测试区域选择逻辑"""
    print("\n=== 区域选择逻辑测试 ===")
    
    # 创建游戏环境
    game, player1, player2 = create_test_game()
    
    # 创建过河拆桥动作
    action = GuoHeChaiQiaoAction()
    
    # 测试1: 只有手牌
    print("\n--- 测试1: 只有手牌 ---")
    player2.hand_cards = [Card("杀", CardType.BASIC, "♠", 7)]
    player2.equipped = []
    player2.judgment_area = []
    
    selected_card, area_type = action._select_card_from_opponent(
        player2, game, player1, test_mode=True
    )
    print(f"选择结果: {selected_card.name if selected_card else 'None'} (来自{area_type})")
    
    # 测试2: 只有装备
    print("\n--- 测试2: 只有装备 ---")
    player2.hand_cards = []
    player2.equipped = [Card("青龙偃月刀", CardType.EQUIP, "♠", 5)]
    player2.judgment_area = []
    
    selected_card, area_type = action._select_card_from_opponent(
        player2, game, player1, test_mode=True
    )
    print(f"选择结果: {selected_card.name if selected_card else 'None'} (来自{area_type})")
    
    # 测试3: 只有判定区
    print("\n--- 测试3: 只有判定区 ---")
    player2.hand_cards = []
    player2.equipped = []
    player2.judgment_area = [Card("乐不思蜀", CardType.TRICK, "♥", 6)]
    
    selected_card, area_type = action._select_card_from_opponent(
        player2, game, player1, test_mode=True
    )
    print(f"选择结果: {selected_card.name if selected_card else 'None'} (来自{area_type})")
    
    # 测试4: 没有任何牌
    print("\n--- 测试4: 没有任何牌 ---")
    player2.hand_cards = []
    player2.equipped = []
    player2.judgment_area = []
    
    selected_card, area_type = action._select_card_from_opponent(
        player2, game, player1, test_mode=True
    )
    print(f"选择结果: {selected_card.name if selected_card else 'None'} (来自{area_type})")
    
    return True

def main():
    """主函数"""
    print("过河拆桥功能测试")
    print("=" * 40)
    
    try:
        # 测试选择功能
        test_guohe_selection()
        
        # 测试区域选择逻辑
        test_area_selection_logic()
        
        print("\n" + "=" * 40)
        print("所有测试完成！")
        
    except Exception as e:
        print(f"测试过程中出现错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()