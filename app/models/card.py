import json
from random import shuffle

class Card:
    def __init__(self, name, suit, rank, card_type, effect):
        self.name = name
        self.suit = suit
        self.rank = rank
        self.card_type = card_type
        self.effect = effect

    def __repr__(self):
        return f"{self.suit}{self.rank} {self.name}"

class Deck:
    def __init__(self, card_data_file):
        self.cards = self.load_cards(card_data_file)
        shuffle(self.cards)

    def load_cards(self, card_data_file):
        with open(card_data_file, 'r', encoding='utf-8') as file:
            card_data = json.load(file)
        return [Card(**card) for card in card_data]

    def draw_card(self):
        return self.cards.pop() if self.cards else None

# 示例：加载卡牌数据并摸牌
deck = Deck("app/data/cards.json")
print(deck.draw_card())