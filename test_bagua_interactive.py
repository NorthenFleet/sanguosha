#!/usr/bin/env python3
"""
八卦阵交互测试 - 验证用户选择是否使用八卦阵的完整流程
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.models.player import Player
from app.models.character import Character, Kingdom
from app.models.card import Card
from app.models.deck import EnhancedDeck
from app.models.card_actions import ShaAction
from app.core.judgment_system import JudgmentSystem, JudgmentType
from app.core.events.event_system import EventManager
from app.core.base.game import Game

def test_interactive_bagua():
    """测试八卦阵的交互式选择"""
    print("=== 八卦阵交互测试 ===")
    print("这个测试将模拟真实的游戏场景，让你选择是否使用八卦阵")
    
    # 创建游戏环境
    event_manager = EventManager()
    game = Game(event_manager)
    
    # 创建攻击者和防御者
    attacker = Player(Character("曹操", Kingdom.WEI, 4, ["奸雄"]))
    defender = Player(Character("刘备", Kingdom.SHU, 4, ["仁德"]))
    
    # 给防御者装备八卦阵
    bagua_card = Card("八卦阵", "equipment", "defense")
    defender._equip_card(bagua_card)
    print(f"\n{defender.character.name} 装备了八卦阵")
    
    # 给防御者一张闪
    shan_card = Card("闪", "basic")
    defender.hand_cards.append(shan_card)
    print(f"{defender.character.name} 手牌中有闪")
    
    # 给攻击者一张杀
    sha_card = Card("杀", "basic")
    attacker.hand_cards.append(sha_card)
    
    print(f"\n--- 游戏场景 ---")
    print(f"{attacker.character.name} 对 {defender.character.name} 使用了杀")
    print(f"{defender.character.name} 需要响应这张杀")
    
    # 创建杀的动作
    sha_action = ShaAction()
    
    # 获取响应卡牌
    response_cards = sha_action.get_response_cards(defender)
    print(f"\n可用的响应卡牌: {response_cards}")
    
    # 询问响应（非测试模式，需要用户输入）
    print("\n现在将询问你是否使用八卦阵...")
    response = sha_action.ask_for_response(game, defender, response_cards, test_mode=False)
    
    # 处理响应结果
    if response == "八卦阵判定成功":
        print(f"\n✓ {defender.character.name} 通过八卦阵成功防御了杀！")
        damage_taken = sha_action.process_response(game, attacker, defender, response)
        print(f"是否受到伤害: {damage_taken}")
    elif response == "闪":
        print(f"\n✓ {defender.character.name} 使用闪成功防御了杀！")
        damage_taken = sha_action.process_response(game, attacker, defender, response)
        print(f"是否受到伤害: {damage_taken}")
    elif response is None:
        print(f"\n✗ {defender.character.name} 没有有效防御，将受到1点伤害")
        damage_taken = True
        print(f"是否受到伤害: {damage_taken}")
    
    print("\n=== 测试完成 ===")

if __name__ == "__main__":
    test_interactive_bagua()