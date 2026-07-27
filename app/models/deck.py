import json
import random
from pathlib import Path
from typing import List, Dict, Optional, Any
from .card import Card

class EnhancedDeck:
    """增强的牌堆管理系统"""
    
    def __init__(self, cards_file: str | None = None):
        self.cards_file = cards_file or str(Path(__file__).resolve().parents[1] / "data" / "cards.json")
        self.draw_pile: List[Card] = []  # 摸牌堆
        self.discard_pile: List[Card] = []  # 弃牌堆
        self.removed_cards: List[Card] = []  # 移出游戏的卡牌
        self._load_cards()
        self.shuffle_draw_pile()
        
    def _load_cards(self):
        """从JSON文件加载卡牌数据"""
        try:
            with open(self.cards_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
            for card_data in data.get('cards', []):
                card = Card(
                    name=card_data['name'],
                    suit=card_data['suit'],
                    rank=card_data['rank'],
                    card_type=card_data['type'],
                    effect=card_data['effect'],
                    category=card_data.get('category', 'basic'),
                    subtype=card_data.get('subtype')
                )
                self.draw_pile.append(card)
                
        except FileNotFoundError:
            print(f"警告：找不到卡牌文件 {self.cards_file}")
        except json.JSONDecodeError:
            print(f"错误：卡牌文件 {self.cards_file} 格式不正确")
    
    def shuffle_draw_pile(self):
        """洗摸牌堆"""
        random.shuffle(self.draw_pile)
        print(f"摸牌堆已洗牌，当前有 {len(self.draw_pile)} 张牌")
    
    def draw_card(self) -> Optional[Card]:
        """从摸牌堆摸一张牌"""
        if not self.draw_pile:
            self._reshuffle_discard_pile()
            
        if self.draw_pile:
            card = self.draw_pile.pop()
            print(f"摸到卡牌：{card}")
            return card
        else:
            print("警告：摸牌堆和弃牌堆都为空！")
            return None
    
    def draw_cards(self, count: int) -> List[Card]:
        """摸多张牌"""
        cards = []
        for _ in range(count):
            card = self.draw_card()
            if card:
                cards.append(card)
            else:
                break
        return cards
    
    def discard_card(self, card: Card):
        """将卡牌放入弃牌堆"""
        self.discard_pile.append(card)
        print(f"弃置卡牌：{card}")
    
    def discard_cards(self, cards: List[Card]):
        """将多张卡牌放入弃牌堆"""
        for card in cards:
            self.discard_card(card)
    
    def remove_card(self, card: Card):
        """将卡牌移出游戏"""
        self.removed_cards.append(card)
        print(f"移出游戏：{card}")
    
    def remove_from_game(self, card: Card) -> bool:
        """将卡牌移出游戏"""
        try:
            if card in self.draw_pile:
                self.draw_pile.remove(card)
                self.removed_cards.append(card)
                return True
            elif card in self.discard_pile:
                self.discard_pile.remove(card)
                self.removed_cards.append(card)
                return True
            else:
                return False
        except ValueError:
            return False
    
    def remove_multiple_from_game(self, cards: List[Card]) -> bool:
        """将多张卡牌移出游戏"""
        try:
            for card in cards:
                if not self.remove_from_game(card):
                    return False
            return True
        except Exception:
            return False
    
    def _reshuffle_discard_pile(self):
        """将弃牌堆重新洗入摸牌堆"""
        if self.discard_pile:
            print(f"弃牌堆有 {len(self.discard_pile)} 张牌，重新洗入摸牌堆")
            self.draw_pile.extend(self.discard_pile)
            self.discard_pile.clear()
            self.shuffle_draw_pile()
        else:
            print("弃牌堆为空，无法重新洗牌")
    
    def peek_top_card(self) -> Optional[Card]:
        """查看摸牌堆顶的卡牌（不移除）"""
        if self.draw_pile:
            return self.draw_pile[-1]
        return None
    
    def peek_top_cards(self, count: int) -> List[Card]:
        """查看摸牌堆顶的多张卡牌（不移除）"""
        if count <= 0:
            return []
        return self.draw_pile[-count:] if len(self.draw_pile) >= count else self.draw_pile[:]
    
    def get_draw_pile_count(self) -> int:
        """获取摸牌堆数量"""
        return len(self.draw_pile)
    
    def get_discard_pile_count(self) -> int:
        """获取弃牌堆数量"""
        return len(self.discard_pile)
    
    def get_removed_cards_count(self) -> int:
        """获取移出游戏的卡牌数量"""
        return len(self.removed_cards)
    
    def get_total_cards_count(self) -> int:
        """获取总卡牌数量"""
        return len(self.draw_pile) + len(self.discard_pile) + len(self.removed_cards)
    
    def get_deck_status(self) -> Dict[str, Any]:
        """获取牌堆状态信息"""
        return {
            'draw_pile': len(self.draw_pile),
            'discard_pile': len(self.discard_pile),
            'removed_cards': len(self.removed_cards),
            'total_cards': self.get_total_cards_count(),
            'draw_pile_empty': len(self.draw_pile) == 0,
            'discard_pile_empty': len(self.discard_pile) == 0
        }
    
    def is_draw_pile_empty(self) -> bool:
        """检查摸牌堆是否为空"""
        return len(self.draw_pile) == 0
    
    def is_discard_pile_empty(self) -> bool:
        """检查弃牌堆是否为空"""
        return len(self.discard_pile) == 0
    
    def get_deck_status(self) -> Dict[str, int]:
        """获取牌堆状态信息"""
        return {
            "draw_pile": self.get_draw_pile_count(),
            "discard_pile": self.get_discard_pile_count(),
            "removed_cards": self.get_removed_cards_count(),
            "total_cards": self.get_total_cards_count()
        }
    
    def display_deck_info(self):
        """显示牌堆详细信息"""
        status = self.get_deck_status()
        print("\n=== 牌堆状态 ===")
        print(f"摸牌堆：{status['draw_pile']} 张")
        print(f"弃牌堆：{status['discard_pile']} 张")
        print(f"移出游戏：{status['removed_cards']} 张")
        print(f"总计：{status['total_cards']} 张")
        
        if self.draw_pile:
            top_card = self.peek_top_card()
            print(f"摸牌堆顶：{top_card}")
        
        if self.discard_pile:
            print(f"弃牌堆顶：{self.discard_pile[-1]}")
    
    def reset_deck(self):
        """重置牌堆（将所有卡牌重新放入摸牌堆）"""
        print("重置牌堆...")
        self.draw_pile.extend(self.discard_pile)
        self.draw_pile.extend(self.removed_cards)
        self.discard_pile.clear()
        self.removed_cards.clear()
        self.shuffle_draw_pile()
    
    def get_cards_by_type(self, card_type: str) -> List[Card]:
        """获取指定类型的所有卡牌"""
        all_cards = self.draw_pile + self.discard_pile + self.removed_cards
        return [card for card in all_cards if card.card_type == card_type]
    
    def get_cards_by_name(self, name: str) -> List[Card]:
        """获取指定名称的所有卡牌"""
        all_cards = self.draw_pile + self.discard_pile + self.removed_cards
        return [card for card in all_cards if card.name == name]
    
    def __len__(self):
        """返回总卡牌数量"""
        return self.get_total_cards_count()
    
    def __str__(self):
        """返回牌堆状态的字符串表示"""
        status = self.get_deck_status()
        return f"Deck(摸牌堆:{status['draw_pile']}, 弃牌堆:{status['discard_pile']}, 移出:{status['removed_cards']})"

# 保持向后兼容性的别名
Deck = EnhancedDeck

# 演示函数
def demo_enhanced_deck():
    """演示增强牌堆系统的功能"""
    print("=== 增强牌堆系统演示 ===")
    
    # 创建牌堆
    deck = EnhancedDeck()
    
    # 显示初始状态
    deck.display_deck_info()
    
    # 摸牌测试
    print("\n--- 摸牌测试 ---")
    hand = deck.draw_cards(5)
    print(f"摸到手牌：{[str(card) for card in hand]}")
    
    # 弃牌测试
    print("\n--- 弃牌测试 ---")
    if hand:
        deck.discard_cards(hand[:2])
    
    # 查看牌堆顶
    print("\n--- 查看牌堆顶 ---")
    top_cards = deck.peek_top_cards(3)
    print(f"牌堆顶3张：{[str(card) for card in top_cards]}")
    
    # 显示最终状态
    print("\n--- 最终状态 ---")
    deck.display_deck_info()
    
    return deck

if __name__ == "__main__":
    demo_enhanced_deck()
