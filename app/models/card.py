import json
from random import shuffle

class Card:
    def __init__(self, name=None, category=None, suit=None, point=None, type=None, effect=None, rank=None):
        self.name = name or "unknown"
        self.category = category or "unknown"
        self.suit = suit or "unknown"
        self.point = point or 0
        self.type = type
        self.effect = effect
        self.rank = rank

    def __repr__(self):
        return f"{self.suit}{self.rank} {self.name}"

class Deck:
    def __init__(self, card_data_file):
        self.cards = self.load_cards(card_data_file)

    def load_cards(self, card_data_file):
        import json
        with open(card_data_file, "r", encoding="utf-8") as f:
            card_data = json.load(f)

        cards = []
        for category, details in card_data.items():
            if isinstance(details, dict):
                for suit, points in details.get("cards", {}).items():
                    for point in points:
                        cards.append(Card(category=category, suit=suit, point=point))
            elif isinstance(details, list):
                for card in details:
                    cards.append(Card(**card))
        return cards

    def shuffle(self):
        import random
        random.shuffle(self.cards)

    def draw(self, num=1):
        drawn_cards = self.cards[:num]
        self.cards = self.cards[num:]
        return drawn_cards

    def draw_card(self):
        return self.cards.pop() if self.cards else None

# 示例：加载卡牌数据并摸牌
deck = Deck("app/data/cards.json")
print(deck.draw_card())