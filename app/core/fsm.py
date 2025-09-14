from .enums import Phase
from .state import GameState
from .rules import draw_cards, must_discard


class TurnFSM:
    def __init__(self, gs: GameState):
        self.gs = gs


    def start_turn(self):
        self.gs.phase = Phase.DRAW
        self.gs.append_log(f"[PHASE] {self.gs.active} → DRAW")
        draw_cards(self.gs.players[self.gs.active], self.gs.deck, 2)
        self.to_play()


    def to_play(self):
        self.gs.phase = Phase.PLAY
        self.gs.append_log(f"[PHASE] {self.gs.active} → PLAY")
        # 等待客户端通过 WS 发送动作（出牌/结束）


    def end_play(self):
        self.gs.phase = Phase.DISCARD
        p = self.gs.players[self.gs.active]
        need = must_discard(p)
        self.gs.append_log(f"[PHASE] DISCARD, need={need}")
        # 简化：若需弃牌，由客户端发 RESPOND 丢弃；否则直接结束
        if need == 0:
            self.to_end()


    def to_end(self):
        self.gs.phase = Phase.END
        self.gs.append_log(f"[PHASE] {self.gs.active} → END")
        self.gs.next_player()
        self.start_turn()