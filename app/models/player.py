"""
三国杀1v1玩家模块
"""
from typing import List
from .character import Character

class Player:
    """玩家类"""
    def __init__(self, character: Character):
        self.character = character
        self.hp = character.hp
        self.hand_cards: List[str] = []
        self.weapon = None  # 武器牌
        self.defense = None  # 防御牌
        self.attack_horse = None  # 进攻马
        self.defense_horse = None  # 防御马
        self.equipped = []  # 初始化 equipped 属性为空列表
        self.chained = False

    def draw_card(self, deck: List[str], count: int):
        """从牌堆摸牌"""
        for _ in range(count):
            if deck:
                self.hand_cards.append(deck.pop())

    def discard_card(self, card: str):
        """弃牌"""
        if card in self.hand_cards:
            self.hand_cards.remove(card)

    def use_card(self, card: str):
        """使用牌"""
        if card in self.hand_cards:
            self.hand_cards.remove(card)
            # 处理装备牌逻辑
            if card.type == "装备牌":
                if "武器" in card.name:
                    self.weapon = card
                elif "防御" in card.name:
                    self.defense = card
                elif "进攻马" in card.name:
                    self.attack_horse = card
                elif "防御马" in card.name:
                    self.defense_horse = card
            return True
        return False