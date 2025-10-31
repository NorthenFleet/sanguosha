try:
    from pydantic import BaseModel, ConfigDict
    _HAS_CONFIGDICT = True
except ImportError:
    # 兼容pydantic v1：没有ConfigDict
    from pydantic import BaseModel
    ConfigDict = None
    _HAS_CONFIGDICT = False
from typing import Dict, List, Any, TYPE_CHECKING

# 使用TYPE_CHECKING避免运行时导入问题
if TYPE_CHECKING:
    from ...models.player import Player
    from ...models.card import Card
else:
    # 运行时使用Any类型，避免验证问题
    Player = Any
    Card = Any

from .enums import Phase


class GameState(BaseModel):
    # pydantic v1 配置
    class Config:
        arbitrary_types_allowed = True
        validate_assignment = True

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
