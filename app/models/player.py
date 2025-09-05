"""
三国杀1v1玩家模块
"""
from typing import List
from .character import Character

class Player:
    """玩家类"""
    def __init__(self, character: Character):
        self.character = character
        self.hand_cards: List[str] = []
        self.weapon = None
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
            return True
        return False