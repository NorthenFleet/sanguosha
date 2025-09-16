import unittest
from app.models.card import Deck

class TestDeck(unittest.TestCase):
    def test_load_cards(self):
        deck = Deck("app/data/cards.json")
        self.assertGreater(len(deck.cards), 0, "卡牌加载失败，未找到任何卡牌信息！")
        for card in deck.cards:
            self.assertIsNotNone(card.point, f"卡牌点数未正确加载: {card}")

if __name__ == "__main__":
    unittest.main()