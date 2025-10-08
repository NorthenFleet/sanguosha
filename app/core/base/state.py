try:
    from pydantic import BaseModel, ConfigDict
    _HAS_CONFIGDICT = True
except ImportError:
    # 兼容pydantic v1：没有ConfigDict
    from pydantic import BaseModel
    ConfigDict = None
    _HAS_CONFIGDICT = False
from typing import Dict, List, Any
from ...models.player import Player
from ...models.card import Card
from .enums import Phase


class GameState(BaseModel):
    # pydantic v2 使用 model_config / ConfigDict；pydantic v1 使用内部 Config 类
    if _HAS_CONFIGDICT:
        model_config = ConfigDict(arbitrary_types_allowed=True)
    else:
        class Config:
            arbitrary_types_allowed = True

    players: Dict[str, Player]
    turn_order: List[str]
    active: str
    phase: Phase
    deck: List[Card]
    discard_pile: List[Card]
    log: List[str] = []
    version: int = 0  # 递增版本号，生成增量补丁

    def snapshot(self) -> Dict[str, Any]:
        md = getattr(self, "model_dump", None)
        if callable(md):
            return md()
        # pydantic v1 兼容
        return self.dict()

    def append_log(self, s: str):
        self.log.append(s)
        self.version += 1

    def next_player(self) -> str:
        idx = self.turn_order.index(self.active)
        self.active = self.turn_order[(idx + 1) % len(self.turn_order)]
        return self.active
