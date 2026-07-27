"""Deterministic game-state smoke coverage."""

from app.core.base.game import Game
from app.core.events.event_system import EventManager
from app.models.card import Card
from app.models.character import Character, Kingdom
from app.models.player import Player


def test_game_tracks_players_and_current_turn_without_console_input():
    game = Game(EventManager())
    first = Player(Character("曹操", Kingdom.WEI, 4, ["奸雄"]))
    second = Player(Character("刘备", Kingdom.SHU, 4, ["仁德"]))

    game.add_player(first)
    game.add_player(second)

    assert game.players == [first, second]
    assert game.current_player_index == 0
    assert game.current_player is None

    game.current_player = first

    assert game.current_player is first


def test_discard_phase_is_bounded_in_test_mode():
    game = Game(EventManager())
    player = Player(Character("曹操", Kingdom.WEI, 4, ["奸雄"]))
    game.add_player(player)
    player.hand_cards = [
        Card(name=f"测试牌-{index}", category="basic", point=index)
        for index in range(1, 7)
    ]

    game.discard_phase(player, test_mode=True)

    assert len(player.hand_cards) == player.character.hp
