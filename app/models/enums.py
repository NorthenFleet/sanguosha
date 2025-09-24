from enum import Enum

class CardType(Enum):
    """牌的类型"""
    BASIC = "基本牌"
    TRICK = "锦囊牌"
    EQUIP = "装备牌"

class Suit(Enum):
    """花色"""
    SPADES = "黑桃"    # 黑色
    HEARTS = "红桃"    # 红色
    CLUBS = "梅花"     # 黑色
    DIAMONDS = "方片"  # 红色