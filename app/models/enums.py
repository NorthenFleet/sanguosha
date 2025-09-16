from enum import Enum

class CardType(Enum):
    """牌的类型"""
    BASIC = "基本牌"
    TRICK = "锦囊牌"
    EQUIP = "装备牌"