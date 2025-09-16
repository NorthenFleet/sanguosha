"""
三国杀1v1玩家模块
"""
from typing import List
from .character import Character
from .card import Card

class Player:
    """玩家类"""
    def __init__(self, character: Character):
        self.character = character
        self.hp = character.hp
        self.hand_cards: List[Card] = []
        self.weapon = None  # 武器牌
        self.defense = None  # 防御牌
        self.attack_horse = None  # 进攻马
        self.defense_horse = None  # 防御马
        self.equipped = []  # 初始化 equipped 属性为空列表
        self.chained = False

    def draw_card(self, deck: List[Card], count: int):
        """从牌堆摸牌"""
        for _ in range(count):
            if deck:
                self.hand_cards.append(deck.pop())

    def discard_card(self, card: str):
        """弃牌"""
        if card in self.hand_cards:
            self.hand_cards.remove(card)

    def use_card(self, card):
        """使用牌"""
        original_card_str = None
        target_card = None
        
        if isinstance(card, str):
            original_card_str = card
            # 将字符串解析为 Card 对象
            target_card = next((c for c in self.hand_cards if str(c) == card), None)
            if not target_card:
                print(f"错误: 未找到匹配的卡牌 {original_card_str}")
                return False
        else:
            target_card = card

        print(f"[DEBUG] 当前手牌: {self.hand_cards}")
        print(f"[DEBUG] 使用的卡牌: {target_card}")
        
        # 直接从手牌中移除找到的卡牌
        if target_card in self.hand_cards:
            self.hand_cards.remove(target_card)
            print(f"[DEBUG] 卡牌 {target_card} 已从手牌移除")
            
            # 处理装备牌逻辑
            if hasattr(target_card, 'type') and target_card.type and hasattr(target_card.type, 'value') and target_card.type.value == "装备牌":
                if target_card.name == "青龙偃月刀":
                    self.weapon = target_card
                elif target_card.name == "赤兔":
                    self.attack_horse = target_card
                # 添加到装备列表
                self.equipped.append(target_card)
            return True
        else:
            print(f"[ERROR] 卡牌 {target_card} 不在手牌中")
            return False