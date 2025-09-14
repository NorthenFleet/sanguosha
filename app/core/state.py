from pydantic import BaseModel
from typing import Dict, List, Any
from .models import Player, Card
from .enums import Phase


class GameState(BaseModel):
    players: Dict[str, Player]
    turn_order: List[str]
    active: str
    phase: Phase
    deck: List[Card]
    discard_pile: List[Card]
    log: List[str] = []
    version: int = 0 # 递增版本号，生成增量补丁


    def snapshot(self) -> Dict[str, Any]:
        return self.model_dump()


def append_log(self, s: str):
    self.log.append(s)
    self.version += 1


def next_player(self) -> str:
    idx = self.turn_order.index(self.active)
    self.active = self.turn_order[(idx+1) % len(self.turn_order)]
    return self.active
