"""
三国杀1v1牌堆模型
管理摸牌堆和弃牌堆，支持自动洗牌循环
"""
import random
from typing import List, Optional
from enum import Enum

class Deck:
    """牌堆类，管理摸牌堆和弃牌堆"""
    
    def __init__(self):
        self.draw_pile: List[Card] = []  # 摸牌堆
        self.discard_pile: List[Card] = []  # 弃牌堆
        self._initialize_draw_pile()
        self.shuffle()
    
    def _initialize_draw_pile(self):
        """初始化摸牌堆"""
        # 导入Card和CardType
        from .game import Card, CardType
        
        # 基本牌
        for _ in range(30):
            self.draw_pile.append(Card("杀", CardType.BASIC, random.choice(["♥", "♦", "♠", "♣"]), random.randint(1, 13)))
        for _ in range(15):
            self.draw_pile.append(Card("闪", CardType.BASIC, random.choice(["♥", "♦"]), random.randint(1, 13)))
        for _ in range(8):
            self.draw_pile.append(Card("桃", CardType.BASIC, random.choice(["♥", "♦"]), random.randint(1, 13)))
        
        # 锦囊牌
        trick_cards = ["过河拆桥", "顺手牵羊", "无中生有", "决斗", "南蛮入侵", "万箭齐发"]
        for card_name in trick_cards:
            for _ in range(4):
                self.draw_pile.append(Card(card_name, CardType.TRICK, random.choice(["♥", "♦", "♠", "♣"]), random.randint(1, 13)))
    
    def shuffle(self):
        """洗牌"""
        random.shuffle(self.draw_pile)
    
    def draw_card(self) -> Optional['Card']:
        """摸一张牌，如果没有牌则自动洗牌"""
        # 如果摸牌堆没有牌，将弃牌堆洗牌后放入摸牌堆
        if not self.draw_pile:
            if not self.discard_pile:
                # 如果弃牌堆也没有牌，返回None
                return None
            # 将弃牌堆洗牌后放入摸牌堆
            self.draw_pile = self.discard_pile[:]
            self.discard_pile.clear()
            self.shuffle()
        
        # 从摸牌堆摸一张牌
        return self.draw_pile.pop()
    
    def discard_card(self, card: 'Card'):
        """弃一张牌到弃牌堆"""
        self.discard_pile.append(card)
    
    def get_draw_pile_count(self) -> int:
        """获取摸牌堆剩余牌数"""
        return len(self.draw_pile)
    
    def get_discard_pile_count(self) -> int:
        """获取弃牌堆剩余牌数"""
        return len(self.discard_pile)
    
    def get_total_card_count(self) -> int:
        """获取总牌数"""
        return len(self.draw_pile) + len(self.discard_pile)
    
    def is_empty(self) -> bool:
        """检查牌堆是否为空"""
        return self.get_total_card_count() == 0