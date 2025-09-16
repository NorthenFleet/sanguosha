import json
from random import shuffle

from app.models.enums import CardType

class Card:
    def __init__(self, name=None, category=None, suit=None, point=None, type=None, effect=None, rank=None):
        self.name = name or "unknown"
        self.category = category or "unknown"
        self.suit = suit or "unknown"
        self.rank = point or rank or 0  # 使用 point 或 rank 作为点数
        self.type = type
        self.effect = effect

    def __str__(self):
        return f"{self.name}({self.type.value if self.type else 'unknown'}) - {self.suit}[{self.rank}]"

    def __repr__(self):
        return f"{self.suit}[{self.rank}] {self.name}"

    def __eq__(self, other):
        if isinstance(other, Card):
            return (
                self.name == other.name and
                self.category == other.category and
                self.suit == other.suit and
                self.rank == other.rank and
                self.type == other.type
            )
        return False

def display_deck_info(deck):
    print("当前牌堆数量:", len(deck.cards))
    print("弃牌堆数量:", len(deck.discard_pile))
    print("牌堆中的卡牌:")
    for card in deck.cards:
        print(f"{card.name} - {card.suit}[{card.rank}]")

    print("弃牌堆中的卡牌:")
    for card in deck.discard_pile:
        print(f"{card.name} - {card.suit}[{card.rank}]")

class Deck:
    def __init__(self, card_data_file=None):
        self.cards = self.load_cards(card_data_file) if card_data_file else []
        self.draw_pile = self.cards  # 添加 draw_pile 属性以兼容现有逻辑
        self.discard_pile = []  # 初始化弃牌堆

    def load_cards(self, card_data_file):
        try:
            # 延迟导入避免循环导入
            from app.core.game import Card as GameCard, CardType as GameCardType
            
            with open(card_data_file, "r", encoding="utf-8") as f:
                card_data = json.load(f)

            cards = []
            for category, details in card_data.items():
                if isinstance(details, list):
                    for card in details:
                        if isinstance(card.get("rank"), list):
                            for rank in card["rank"]:
                                cards.append(GameCard(name=card.get("name", category), card_type=GameCardType(card["type"]), suit=card["suit"], rank=rank))
                        else:
                            cards.append(GameCard(name=card.get("name", category), card_type=GameCardType(card["type"]), suit=card["suit"], rank=card["rank"]))
                elif isinstance(details, dict):
                    for suit, ranks in details.get("cards", {}).items():
                        for rank in ranks:
                            cards.append(GameCard(name=category, card_type=GameCardType(category), suit=suit, rank=rank))

            if not cards:
                raise ValueError("卡牌数据加载失败，未找到任何卡牌信息！")

            return cards
        except (FileNotFoundError, json.JSONDecodeError, ValueError) as e:
            print(f"加载卡牌数据时出错: {e}")
            return []

    def shuffle(self):
        import random
        random.shuffle(self.cards)

    def draw(self, num=1):
        drawn_cards = self.cards[:num]
        self.cards = self.cards[num:]
        return drawn_cards

    def discard(self, card):
        self.discard_pile.append(card)
        display_deck_info(self)  # 实时显示弃牌堆数量

    def draw_card(self):
        if not self.cards:  # 如果摸牌堆为空
            if self.discard_pile:  # 如果弃牌堆有牌
                self.cards = self.discard_pile[:]
                self.discard_pile.clear()
                self.shuffle()
                print("摸牌堆已重新洗牌！")
            else:
                print("没有牌可供摸取！")
                return None
        return self.cards.pop()

    def is_empty(self):
        """检查牌堆是否为空"""
        return not self.draw_pile and not self.discard_pile
# 示例：加载卡牌数据并摸牌
# deck = Deck("app/data/cards.json")
# print(deck.draw_card())