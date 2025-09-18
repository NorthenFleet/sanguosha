#!/usr/bin/env python3
"""
测试修复后的过河拆桥功能
"""

import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app.core.game import Game
from app.models.player import Player
from app.models.character import Character
from app.models.card import Card
from app.models.enums import CardType
from app.models.card_actions import GuoHeChaiQiaoAction
from app.core.event_system import EventManager

def create_test_game():
    """创建测试游戏环境"""
    # 创建事件管理器
    event_manager = EventManager()
    
    # 创建角色
    char1 = Character("曹操", "魏", 4, ["奸雄"])
    char2 = Character("刘备", "蜀", 4, ["仁德"])
    
    # 创建玩家
    player1 = Player(char1)
    player2 = Player(char2)
    
    # 创建游戏
    game = Game(event_manager)
    game.add_player(player1)
    game.add_player(player2)
    
    return game, player1, player2

def setup_test_cards(player):
    """设置测试卡牌"""
    # 手牌
    player.hand_cards = [
        Card("杀", CardType.BASIC, "♠", 7),
        Card("闪", CardType.BASIC, "♦", 2),
        Card("桃", CardType.BASIC, "♥", 3)
    ]
    
    # 装备区
    weapon = Card("青龙偃月刀", CardType.EQUIP, "♠", 5)
    defense = Card("八卦阵", CardType.EQUIP, "♠", 2)
    player.equipped = [weapon, defense]
    player.weapon = weapon
    player.defense = defense
    
    # 判定区
    judgment_card = Card("乐不思蜀", CardType.TRICK, "♥", 6)
    player.judgment_area = [judgment_card]

def test_guohe_interactive():
    """测试修复后的过河拆桥交互功能"""
    print("修复后的过河拆桥功能测试")
    print("========================================")
    
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
    
    print("\n=== 交互式测试 ===")
    print("现在将测试修复后的过河拆桥选择机制")
    print("请按照提示进行选择...")
    
    try:
        # 测试交互式选择
        selected_card, area_type = action._select_card_from_opponent(
            player2, game, player1, test_mode=False
        )
        
        if selected_card:
            print(f"\n选择成功！")
            print(f"选择的牌: {selected_card.name}")
            print(f"来自区域: {area_type}")
            
            # 测试完整的apply_effect方法
            print("\n--- 测试完整效果 ---")
            original_counts = {
                'hand': len(player2.hand_cards),
                'equipment': len(player2.equipped),
                'judgment': len(player2.judgment_area)
            }
            
            # 执行过河拆桥
            result = action.apply_effect(game, player1, player2)
            
            print(f"执行结果: {result}")
            print(f"手牌变化: {original_counts['hand']} -> {len(player2.hand_cards)}")
            print(f"装备变化: {original_counts['equipment']} -> {len(player2.equipped)}")
            print(f"判定区变化: {original_counts['judgment']} -> {len(player2.judgment_area)}")
        else:
            print("没有选择到任何牌")
            
    except KeyboardInterrupt:
        print("\n\n测试被用户中断")
    except Exception as e:
        print(f"\n测试过程中出现错误: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n========================================")
    print("测试完成！")

if __name__ == "__main__":
    test_guohe_interactive()