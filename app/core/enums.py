# 阶段、动作、事件、阵营等枚举

from enum import Enum, auto


class Phase(Enum):
    DRAW = auto() # 摸牌阶段
    PLAY = auto() # 出牌阶段
    DISCARD = auto() # 弃牌阶段
    END = auto() # 回合结束


class ActionType(Enum):
    USE_CARD = auto() # 使用牌（如“杀”）
    RESPOND_CARD = auto() # 响应（如“闪”）
    END_PLAY = auto() # 结束出牌阶段


class EventType(Enum):
    CARD_USED = auto()
    CARD_TARGETED = auto()
    CARD_RESOLVED = auto()
    DAMAGE = auto()
    HEAL = auto()
    PHASE_CHANGE = auto()   


class Suit(Enum):
    SPADE = auto(); HEART = auto(); CLUB = auto(); DIAMOND = auto()