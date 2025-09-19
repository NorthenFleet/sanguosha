#!/usr/bin/env python3
"""
测试过河拆桥锦囊牌的功能
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.models.character import Character
from app.models.player import Player
from app.models.card import Card
from app.models.deck import Deck
from app.models.card_actions import GuoHeChaiQiaoAction
from app.core.base.game import Game

def test_guohe_chaiqi_selection():
    """测试过河拆桥的卡牌选择功能"""
    print("=== 测试过河拆桥卡牌选择功能 ===")
    
    # 创建角色和玩家
    char1 = Character("刘备", 4, "蜀")
    char2 = Character("曹操", 4, "魏")
    player1 = Player(char1)
    player2 = Player(char2)
    
    # 创建游戏
    game = Game([player1, player2])
    game.current_phase = "test"  # 设置为测试模式
    
    # 给player2添加各种类型的牌
    # 手牌
    player2.hand_cards = [
        Card("杀", "basic", "红桃", 7),
        Card("闪", "basic", "方片", 2),
        Card("桃", "basic", "红桃", 3)
    ]
    
    # 装备区
    weapon = Card("青龙偃月刀", "equipment", "黑桃", 5)
    defense = Card("八卦阵", "equipment", "黑桃", 2)
    player2.equipped = [weapon, defense]
    player2.weapon = weapon
    player2.defense = defense
    
    # 判定区
    judgment_card = Card("乐不思蜀", "trick", "红桃", 6)
    player2.judgment_area = [judgment_card]
    
    print(f"目标玩家 {player2.character.name} 的牌：")
    print(f"手牌: {len(player2.hand_cards)}张")
    print(f"装备区: {[card.name for card in player2.equipped]}")
    print(f"判定区: {[card.name for card in player2.judgment_area]}")
    
    # 创建过河拆桥动作
    action = GuoHeChaiQiaoAction()
    
    # 测试模式下的选择（应该自动选择第一个区域的第一张牌）
    print("\n--- 测试模式下的自动选择 ---")
    selected_card, area_type = action._select_card_from_opponent(
        player2, game, player1, test_mode=True
    )
    print(f"自动选择了: {selected_card.name} (来自{area_type})")
    
    # 测试apply_effect方法
    print("\n--- 测试apply_effect方法 ---")
    original_hand_count = len(player2.hand_cards)
    original_equipment_count = len(player2.equipped)
    original_judgment_count = len(player2.judgment_area)
    
    # 执行过河拆桥
    result = action.apply_effect(game, player1, player2)
    
    print(f"执行结果: {result}")
    print(f"目标玩家手牌变化: {original_hand_count} -> {len(player2.hand_cards)}")
    print(f"目标玩家装备变化: {original_equipment_count} -> {len(player2.equipped)}")
    print(f"目标玩家判定区变化: {original_judgment_count} -> {len(player2.judgment_area)}")
    
    return True

def test_guohe_chaiqi_interactive():
    """测试过河拆桥的交互式选择（需要手动输入）"""
    print("\n=== 测试过河拆桥交互式选择 ===")
    print("注意：这个测试需要手动输入选择")
    
    # 创建角色和玩家
    char1 = Character("刘备", 4, "蜀")
    char2 = Character("曹操", 4, "魏")
    player1 = Player(char1)
    player2 = Player(char2)
    
    # 创建游戏（非测试模式）
    game = Game([player1, player2])
    game.current_phase = "action"
    
    # 给player2添加各种类型的牌
    player2.hand_cards = [
        Card("杀", "basic", "红桃", 7),
        Card("闪", "basic", "方片", 2)
    ]
    
    weapon = Card("青龙偃月刀", "equipment", "黑桃", 5)
    player2.equipped = [weapon]
    player2.weapon = weapon
    
    judgment_card = Card("乐不思蜀", "trick", "红桃", 6)
    player2.judgment_area = [judgment_card]
    
    print(f"目标玩家 {player2.character.name} 的牌：")
    print(f"手牌: {len(player2.hand_cards)}张")
    print(f"装备区: {[card.name for card in player2.equipped]}")
    print(f"判定区: {[card.name for card in player2.judgment_area]}")
    
    # 创建过河拆桥动作
    action = GuoHeChaiQiaoAction()
    
    # 交互式选择
    try:
        selected_card, area_type = action._select_card_from_opponent(
            player2, game, player1, test_mode=False
        )
        print(f"你选择了: {selected_card.name} (来自{area_type})")
    except KeyboardInterrupt:
        print("\n用户取消了选择")
        return False
    except Exception as e:
        print(f"选择过程中出现错误: {e}")
        return False
    
    return True

if __name__ == "__main__":
    # 运行自动测试
    test_guohe_chaiqi_selection()
    
    # 询问是否运行交互式测试
    print("\n" + "="*50)
    choice = input("是否运行交互式测试？(y/n): ").strip().lower()
    if choice == 'y':
        test_guohe_chaiqi_interactive()
    
    print("\n测试完成！")