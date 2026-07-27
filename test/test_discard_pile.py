from app.models.card import Card
from app.models.deck import Deck


def _empty_deck(tmp_path):
    deck = Deck(cards_file=str(tmp_path / "missing-cards.json"))
    deck.draw_pile.clear()
    deck.discard_pile.clear()
    return deck


def test_discard_pile_count(tmp_path):
    deck = _empty_deck(tmp_path)
    cards = [
        Card(name="杀", category="basic", suit="黑桃", rank=7),
        Card(name="闪", category="basic", suit="红桃", rank=2),
    ]

    deck.discard_cards(cards)

    assert deck.get_discard_pile_count() == 2
    assert deck.get_total_cards_count() == 2
    assert deck.get_deck_status()["discard_pile"] == 2


def test_draw_reshuffles_discard_pile(tmp_path):
    deck = _empty_deck(tmp_path)
    card = Card(name="桃", category="basic", suit="红桃", rank=9)
    deck.discard_card(card)

    drawn = deck.draw_card()

    assert drawn is card
    assert deck.get_draw_pile_count() == 0
    assert deck.get_discard_pile_count() == 0
    assert deck.get_total_cards_count() == 0
