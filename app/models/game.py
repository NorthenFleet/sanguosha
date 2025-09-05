"""
三国杀1v1游戏核心框架
"""
from enum import Enum
from typing import List, Dict, Optional
import random


class CardType(Enum):
    """牌的类型"""
    BASIC = "基本牌"
    TRICK = "锦囊牌"
    EQUIP = "装备牌"


class Card:
    """牌的基类"""
    def __init__(self, name: str, card_type: CardType, suit: str, rank: int):
        self.name = name
        self.type = card_type
        self.suit = suit  # 花色
        self.rank = rank  # 点数

    def __str__(self):
        return f"{self.name}({self.type.value})"


class Player:
    """玩家类"""
    def __init__(self, character):
        self.character = character
        self.hand_cards = []
        self.weapon = None  # 添加武器属性，默认为 None
        self.chained = False  # 添加铁锁连环状态，默认为 False
        self.has_used_sha = False  # 添加是否使用过杀的标记，默认为 False

    def draw_card(self, deck, num: int = 1):
        """摸牌"""
        for _ in range(num):
            if deck:
                self.hand_cards.append(deck.pop())

    def play_card(self, card_index: int, target=None):
        """出牌"""
        if 0 <= card_index < len(self.hand_cards):
            card = self.hand_cards.pop(card_index)
            print(f"{self.character.name} 使用了 {card}")
            return card
        return None


class Game:
    """游戏主逻辑"""
    def __init__(self):
        self.players: List[Player] = []
        self.deck: List[Card] = []
        self.current_player_index = 0
        self.current_phase = "准备阶段"
        self.phase = "准备阶段"

    def initialize_deck(self):
        """初始化牌堆"""
        # 基本牌
        for _ in range(30):
            self.deck.append(Card("杀", CardType.BASIC, random.choice(["♥", "♦", "♠", "♣"]), random.randint(1, 13)))
        for _ in range(15):
            self.deck.append(Card("闪", CardType.BASIC, random.choice(["♥", "♦"]), random.randint(1, 13)))
        for _ in range(8):
            self.deck.append(Card("桃", CardType.BASIC, random.choice(["♥", "♦"]), random.randint(1, 13)))
        
        # 锦囊牌
        trick_cards = ["过河拆桥", "顺手牵羊", "无中生有", "决斗", "南蛮入侵", "万箭齐发"]
        for card_name in trick_cards:
            for _ in range(4):
                self.deck.append(Card(card_name, CardType.TRICK, random.choice(["♥", "♦", "♠", "♣"]), random.randint(1, 13)))
        
        # 洗牌
        random.shuffle(self.deck)

    def add_player(self, character):
        """添加玩家"""
        if len(self.players) < 2:
            self.players.append(Player(character))
            return True
        return False