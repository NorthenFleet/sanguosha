#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
sys.path.append('.')

from app.models.player import Player
from app.models.character import Character, Kingdom
from app.models.card import Card
from app.models.card_actions import ShunShouQianYangAction
from app.core.base.game import Game
from app.core.events.event_system import EventManager

def create_test_game():
    """创建测试游戏环境"""
    event_manager = EventManager()
    game = Game(event_manager)
    
    # 创建角色
    attacker_char = Character("曹操", Kingdom.WEI, 4, ["奸雄"])
    defender_char = Character("刘备", Kingdom.SHU, 4, ["仁德"])
    
    # 创建玩家
    attacker = Player(attacker_char)
    defender = Player(defender_char)
    
    # 添加到游戏
    game.players = [attacker, defender]
    game.current_player_index = 0
    
    return game, attacker, defender

def main():
    print("=== 顺手牵羊交互测试 ===")
    print("这个测试将模拟真实的游戏场景，让你选择从对手的哪个区域获得牌")
    
    # 创建游戏环境
    game, attacker, defender = create_test_game()
    
    # 给攻击者顺手牵羊
    shunshou_card = Card("顺手牵羊", "trick", "黑桃", 3)
    attacker.hand_cards.append(shunshou_card)
    
    # 给防御者各种牌
    # 手牌
    shan_card = Card("闪", "basic", "红桃", 2)
    sha_card = Card("杀", "basic", "黑桃", 7)
    defender.hand_cards.extend([shan_card, sha_card])
    
    # 装备牌
    weapon_card = Card("青龙偃月刀", "equipment", "黑桃", 5)
    armor_card = Card("八卦阵", "equipment", "梅花", 2)
    defender._equip_card(weapon_card)
    defender._equip_card(armor_card)
    
    # 判定牌（模拟延时锦囊）
    judgment_card = Card("乐不思蜀", "trick", "红桃", 6)
    defender.judgment_area.append(judgment_card)
    
    print(f"\n{attacker.character.name} 手牌中有顺手牵羊")
    print(f"{defender.character.name} 的状态：")
    print(f"  手牌: {len(defender.hand_cards)}张")
    print(f"  装备: {[card.name for card in defender.equipped]}")
    print(f"  判定区: {[card.name for card in defender.judgment_area]}")
    
    print(f"\n--- 游戏场景 ---")
    print(f"{attacker.character.name} 对 {defender.character.name} 使用了顺手牵羊")
    print(f"现在需要选择从哪个区域获得牌...")
    
    # 创建顺手牵羊动作
    shunshou_action = ShunShouQianYangAction()
    
    # 执行顺手牵羊（非测试模式，会有交互）
    print(f"\n现在将询问你要从哪个区域获得牌...")
    result = shunshou_action.apply_effect(game, attacker, defender)
    
    print(f"\n=== 结果 ===")
    print(f"顺手牵羊结果: {'成功' if result else '失败'}")
    print(f"{attacker.character.name} 当前手牌: {[card.name for card in attacker.hand_cards]}")
    print(f"{defender.character.name} 剩余状态：")
    print(f"  手牌: {len(defender.hand_cards)}张")
    print(f"  装备: {[card.name for card in defender.equipped]}")
    print(f"  判定区: {[card.name for card in defender.judgment_area]}")
    
    print("\n=== 测试完成 ===")

if __name__ == "__main__":
    main()