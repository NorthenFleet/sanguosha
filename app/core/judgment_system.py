#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
判定系统
实现三国杀中的判定机制，包括从牌堆摸牌进行判定，根据花色、点数或类别决定结果
"""

from typing import Optional, Dict, Any, Callable
from enum import Enum
from ..models.card import Card
from ..models.enums import Suit, CardType
import logging

logger = logging.getLogger(__name__)


class JudgmentType(Enum):
    """判定类型"""
    BAGUA_ZHEN = "八卦阵"  # 八卦阵判定：红色成功
    LIGHTNING = "闪电"    # 闪电判定：黑桃2-9
    LEBUSISHU = "乐不思蜀"  # 乐不思蜀判定：红桃跳过出牌阶段
    BINGLIANG = "兵粮寸断"  # 兵粮寸断判定：梅花跳过摸牌阶段
    CUSTOM = "自定义"      # 自定义判定


class JudgmentResult:
    """判定结果"""
    
    def __init__(self, judgment_card: Card, success: bool, description: str = ""):
        self.judgment_card = judgment_card
        self.success = success
        self.description = description
        
    def __str__(self):
        return f"判定牌：{self.judgment_card} - {'成功' if self.success else '失败'} - {self.description}"


class JudgmentSystem:
    """判定系统"""
    
    def __init__(self, deck=None):
        self.deck = deck
        self.judgment_rules: Dict[JudgmentType, Callable[[Card], bool]] = {
            JudgmentType.BAGUA_ZHEN: self._bagua_judgment,
            JudgmentType.LIGHTNING: self._lightning_judgment,
            JudgmentType.LEBUSISHU: self._lebusishu_judgment,
            JudgmentType.BINGLIANG: self._bingliang_judgment,
        }
        
    def set_deck(self, deck):
        """设置牌堆"""
        self.deck = deck
        
    def perform_judgment(self, judgment_type: JudgmentType, player_name: str = "玩家") -> Optional[JudgmentResult]:
        """执行判定"""
        if not self.deck:
            logger.error("判定系统未设置牌堆")
            return None
            
        # 从牌堆顶摸一张牌作为判定牌
        judgment_card = self.deck.draw_card()
        if not judgment_card:
            logger.error("牌堆为空，无法进行判定")
            return None
            
        print(f"\n{player_name} 进行{judgment_type.value}判定...")
        print(f"判定牌：{judgment_card}")
        
        # 根据判定类型执行相应的判定规则
        if judgment_type in self.judgment_rules:
            success = self.judgment_rules[judgment_type](judgment_card)
            description = self._get_judgment_description(judgment_type, judgment_card, success)
        else:
            logger.error(f"未知的判定类型：{judgment_type}")
            success = False
            description = "未知判定类型"
            
        result = JudgmentResult(judgment_card, success, description)
        print(f"判定结果：{result}")
        
        # 判定牌进入弃牌堆
        self.deck.discard_card(judgment_card)
        
        return result
        
    def perform_custom_judgment(self, judgment_rule: Callable[[Card], bool], 
                              description: str = "自定义判定", 
                              player_name: str = "玩家") -> Optional[JudgmentResult]:
        """执行自定义判定"""
        if not self.deck:
            logger.error("判定系统未设置牌堆")
            return None
            
        # 从牌堆顶摸一张牌作为判定牌
        judgment_card = self.deck.draw_card()
        if not judgment_card:
            logger.error("牌堆为空，无法进行判定")
            return None
            
        print(f"\n{player_name} 进行{description}...")
        print(f"判定牌：{judgment_card}")
        
        # 执行自定义判定规则
        success = judgment_rule(judgment_card)
        
        result = JudgmentResult(judgment_card, success, description)
        print(f"判定结果：{result}")
        
        # 判定牌进入弃牌堆
        self.deck.discard_card(judgment_card)
        
        return result
        
    def _bagua_judgment(self, card: Card) -> bool:
        """八卦阵判定：红色牌成功"""
        return card.is_red()
        
    def _lightning_judgment(self, card: Card) -> bool:
        """闪电判定：黑桃2-9成功（造成伤害）"""
        return card.suit == Suit.SPADE and 2 <= card.rank <= 9
        
    def _lebusishu_judgment(self, card: Card) -> bool:
        """乐不思蜀判定：红桃成功（跳过出牌阶段）"""
        return card.suit == Suit.HEART
        
    def _bingliang_judgment(self, card: Card) -> bool:
        """兵粮寸断判定：梅花成功（跳过摸牌阶段）"""
        return card.suit == Suit.CLUB
        
    def _get_judgment_description(self, judgment_type: JudgmentType, card: Card, success: bool) -> str:
        """获取判定描述"""
        descriptions = {
            JudgmentType.BAGUA_ZHEN: {
                True: f"{card.suit}为红色，视为使用了一张闪",
                False: f"{card.suit}为黑色，判定失败"
            },
            JudgmentType.LIGHTNING: {
                True: f"{card.suit}{card.rank}在黑桃2-9范围内，闪电生效",
                False: f"{card.suit}{card.rank}不在黑桃2-9范围内，闪电不生效"
            },
            JudgmentType.LEBUSISHU: {
                True: f"{card.suit}为红桃，跳过出牌阶段",
                False: f"{card.suit}不是红桃，正常进行出牌阶段"
            },
            JudgmentType.BINGLIANG: {
                True: f"{card.suit}为梅花，跳过摸牌阶段",
                False: f"{card.suit}不是梅花，正常进行摸牌阶段"
            }
        }
        
        return descriptions.get(judgment_type, {}).get(success, "未知判定结果")


# 便捷函数
def create_bagua_judgment_rule() -> Callable[[Card], bool]:
    """创建八卦阵判定规则"""
    def bagua_rule(card: Card) -> bool:
        return card.suit in [Suit.HEART, Suit.DIAMOND]
    return bagua_rule


def create_color_judgment_rule(red_success: bool = True) -> Callable[[Card], bool]:
    """创建颜色判定规则"""
    def color_rule(card: Card) -> bool:
        is_red = card.suit in [Suit.HEART, Suit.DIAMOND]
        return is_red if red_success else not is_red
    return color_rule


def create_suit_judgment_rule(target_suit: Suit) -> Callable[[Card], bool]:
    """创建花色判定规则"""
    def suit_rule(card: Card) -> bool:
        return card.suit == target_suit
    return suit_rule


def create_rank_range_judgment_rule(min_rank: int, max_rank: int, target_suit: Suit = None) -> Callable[[Card], bool]:
    """创建点数范围判定规则"""
    def rank_range_rule(card: Card) -> bool:
        rank_match = min_rank <= card.rank <= max_rank
        if target_suit:
            return rank_match and card.suit == target_suit
        return rank_match
    return rank_range_rule


def create_card_type_judgment_rule(target_type: CardType) -> Callable[[Card], bool]:
    """创建卡牌类型判定规则"""
    def card_type_rule(card: Card) -> bool:
        return card.card_type == target_type
    return card_type_rule


# 演示函数
def demo_judgment_system():
    """演示判定系统功能"""
    from ..models.deck import EnhancedDeck
    
    print("=== 判定系统演示 ===")
    
    # 创建牌堆和判定系统
    deck = EnhancedDeck()
    judgment_system = JudgmentSystem(deck)
    
    # 演示八卦阵判定
    print("\n--- 八卦阵判定演示 ---")
    for i in range(3):
        result = judgment_system.perform_judgment(JudgmentType.BAGUA_ZHEN, f"玩家{i+1}")
        if result:
            print(f"第{i+1}次判定：{'成功' if result.success else '失败'}")
    
    # 演示自定义判定
    print("\n--- 自定义判定演示 ---")
    custom_rule = create_rank_range_judgment_rule(10, 13)  # J、Q、K、A
    result = judgment_system.perform_custom_judgment(
        custom_rule, 
        "大牌判定（J、Q、K、A成功）", 
        "测试玩家"
    )
    
    return judgment_system


if __name__ == "__main__":
    demo_judgment_system()