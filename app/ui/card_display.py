from typing import Dict, List, Optional
from datetime import datetime
from ...models.deck import EnhancedDeck
from ...models.card import Card

class CardDisplayManager:
    """卡牌显示管理器 - 实时显示卡牌数量和状态"""
    
    def __init__(self, deck: EnhancedDeck):
        self.deck = deck
        self.display_config = {
            "show_draw_pile": True,
            "show_discard_pile": True,
            "show_removed_cards": True,
            "show_total_cards": True,
            "show_top_card": True,
            "show_card_types": True
        }
    
    def get_real_time_status(self) -> Dict[str, any]:
        """获取实时卡牌状态"""
        status = self.deck.get_deck_status()
        
        # 添加额外信息
        status.update({
            "top_card": str(self.deck.peek_top_card()) if not self.deck.is_draw_pile_empty() else None,
            "discard_top": str(self.deck.discard_pile[-1]) if not self.deck.is_discard_pile_empty() else None,
            "card_types_count": self._get_card_types_count(),
            "low_cards_warning": self.deck.get_draw_pile_count() < 5
        })
        
        return status
    
    def _get_card_types_count(self) -> Dict[str, int]:
        """统计各类型卡牌数量"""
        all_cards = self.deck.draw_pile + self.deck.discard_pile + self.deck.removed_cards
        
        type_count = {
            "基本牌": 0,
            "锦囊牌": 0,
            "装备牌": 0
        }
        
        for card in all_cards:
            if card.is_basic_card():
                type_count["基本牌"] += 1
            elif card.is_trick_card():
                type_count["锦囊牌"] += 1
            elif card.is_equipment_card():
                type_count["装备牌"] += 1
        
        return type_count
    
    def get_compact_display(self) -> str:
        """获取紧凑显示信息"""
        status = self.get_real_time_status()
        return f"📚{status['draw_pile']} 🗑️{status['discard_pile']} ❌{status['removed_cards']} 📊{status['total_cards']}"
    
    def get_detailed_display(self) -> str:
        """获取详细显示信息"""
        status = self.get_real_time_status()
        
        display_lines = [
            "=== 卡牌系统详细状态 ===",
            f"时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "",
            "📊 牌堆统计:",
            f"  摸牌堆: {status['draw_pile']} 张",
            f"  弃牌堆: {status['discard_pile']} 张",
            f"  移出游戏: {status['removed_cards']} 张",
            f"  总计: {status['total_cards']} 张",
            ""
        ]
        
        # 添加当前卡牌信息
        if status.get('top_card'):
            display_lines.extend([
                "🔝 当前卡牌:",
                f"  摸牌堆顶: {status['top_card']}",
            ])
        
        if status.get('discard_top'):
            display_lines.append(f"  弃牌堆顶: {status['discard_top']}")
        
        # 添加警告信息
        warnings = self.get_warning_messages()
        if warnings:
            display_lines.extend(["", "⚠️ 系统警告:"])
            for warning in warnings:
                display_lines.append(f"  {warning}")
        
        return "\n".join(display_lines)
    
    def get_ascii_visualization(self) -> str:
        """获取ASCII可视化显示"""
        status = self.get_real_time_status()
        
        # 创建ASCII艺术风格的牌堆可视化
        ascii_art = [
            "┌─────────────────────────────────────┐",
            "│          三国杀卡牌系统             │",
            "├─────────────────────────────────────┤",
            f"│ 摸牌堆: {status['draw_pile']:>3} 张 {'█' * min(status['draw_pile'] // 5, 20):20} │",
            f"│ 弃牌堆: {status['discard_pile']:>3} 张 {'▓' * min(status['discard_pile'] // 5, 20):20} │",
            f"│ 移出游戏: {status['removed_cards']:>1} 张 {'░' * min(status['removed_cards'] // 5, 20):20} │",
            "├─────────────────────────────────────┤",
            f"│ 总计: {status['total_cards']:>3} 张                        │",
            "└─────────────────────────────────────┘"
        ]
        
        return "\n".join(ascii_art)
     
    def display_compact_status(self) -> str:
        """显示紧凑的状态信息"""
        status = self.get_real_time_status()
        
        parts = []
        if self.display_config["show_draw_pile"]:
            warning = " ⚠️" if status["low_cards_warning"] else ""
            parts.append(f"摸牌堆: {status['draw_pile']}{warning}")
        
        if self.display_config["show_discard_pile"]:
            parts.append(f"弃牌堆: {status['discard_pile']}")
        
        if self.display_config["show_removed_cards"] and status['removed_cards'] > 0:
            parts.append(f"移出: {status['removed_cards']}")
        
        return " | ".join(parts)
    
    def display_detailed_status(self) -> str:
        """显示详细的状态信息"""
        status = self.get_real_time_status()
        
        lines = ["\n=== 卡牌状态详情 ==="]
        
        # 基本信息
        lines.append(f"📚 摸牌堆: {status['draw_pile']} 张")
        if status['low_cards_warning']:
            lines.append("   ⚠️  警告: 摸牌堆卡牌不足！")
        
        lines.append(f"🗑️  弃牌堆: {status['discard_pile']} 张")
        
        if status['removed_cards'] > 0:
            lines.append(f"❌ 移出游戏: {status['removed_cards']} 张")
        
        lines.append(f"📊 总计: {status['total_cards']} 张")
        
        # 牌堆顶信息
        if self.display_config["show_top_card"]:
            if status['top_card']:
                lines.append(f"🔝 摸牌堆顶: {status['top_card']}")
            if status['discard_top']:
                lines.append(f"🔝 弃牌堆顶: {status['discard_top']}")
        
        # 卡牌类型统计
        if self.display_config["show_card_types"]:
            lines.append("\n--- 卡牌类型统计 ---")
            for card_type, count in status['card_types_count'].items():
                lines.append(f"  {card_type}: {count} 张")
        
        return "\n".join(lines)
    
    def display_ascii_visual(self) -> str:
        """显示ASCII艺术风格的牌堆可视化"""
        status = self.get_real_time_status()
        
        # 摸牌堆可视化
        draw_height = min(status['draw_pile'] // 5, 8)  # 最多8层
        discard_height = min(status['discard_pile'] // 5, 8)
        
        lines = ["\n=== 牌堆可视化 ==="]
        lines.append("")
        
        # 绘制牌堆
        max_height = max(draw_height, discard_height, 1)
        
        for i in range(max_height, 0, -1):
            line_parts = []
            
            # 摸牌堆
            if i <= draw_height:
                line_parts.append("[████]")
            else:
                line_parts.append("     ")
            
            line_parts.append("    ")
            
            # 弃牌堆
            if i <= discard_height:
                line_parts.append("[░░░░]")
            else:
                line_parts.append("     ")
            
            lines.append("".join(line_parts))
        
        # 标签
        lines.append(f"摸牌堆    弃牌堆")
        lines.append(f"({status['draw_pile']:3d})     ({status['discard_pile']:3d})")
        
        if status['top_card']:
            lines.append(f"\n🔝 {status['top_card']}")
        
        return "\n".join(lines)
    
    def get_hand_display(self, hand_cards: List[Card]) -> str:
        """显示手牌信息"""
        if not hand_cards:
            return "手牌: 无"
        
        lines = [f"\n=== 手牌 ({len(hand_cards)} 张) ==="]
        
        # 按类型分组显示
        basic_cards = [card for card in hand_cards if card.is_basic_card()]
        trick_cards = [card for card in hand_cards if card.is_trick_card()]
        equipment_cards = [card for card in hand_cards if card.is_equipment_card()]
        
        if basic_cards:
            lines.append("基本牌:")
            for card in basic_cards:
                lines.append(f"  {card.get_full_display()}")
        
        if trick_cards:
            lines.append("锦囊牌:")
            for card in trick_cards:
                lines.append(f"  {card.get_full_display()}")
        
        if equipment_cards:
            lines.append("装备牌:")
            for card in equipment_cards:
                lines.append(f"  {card.get_full_display()}")
        
        return "\n".join(lines)
    
    def update_display_config(self, **kwargs):
        """更新显示配置"""
        for key, value in kwargs.items():
            if key in self.display_config:
                self.display_config[key] = value
    
    def get_warning_messages(self) -> List[str]:
        """获取警告信息"""
        warnings = []
        status = self.get_real_time_status()
        
        if status['low_cards_warning']:
            warnings.append("⚠️  摸牌堆卡牌不足，建议准备洗牌")
        
        if status['draw_pile'] == 0 and status['discard_pile'] == 0:
            warnings.append("❌ 所有卡牌已用完！")
        
        if status['total_cards'] < 20:
            warnings.append("⚠️  游戏卡牌总数较少，可能影响游戏体验")
        
        return warnings

class GameDisplayInterface:
    """游戏显示界面 - 整合所有显示功能"""
    
    def __init__(self, deck: EnhancedDeck):
        self.card_display = CardDisplayManager(deck)
        self.player_hands = {}  # 存储玩家手牌
    
    def display_hand_cards(self, hand_cards: List[Card]) -> str:
        """显示手牌"""
        if not hand_cards:
            return "🃏 手牌: 无"
        
        hand_display = ["🃏 手牌:"]
        for i, card in enumerate(hand_cards, 1):
            hand_display.append(f"  {i}. {card}")
        
        return "\n".join(hand_display)
    
    def update_player_hand(self, player_id: str, hand_cards: List[Card]):
        """更新玩家手牌"""
        self.player_hands[player_id] = hand_cards
    
    def display_game_status(self, mode: str = "compact") -> str:
        """显示游戏状态"""
        if mode == "compact":
            return self.card_display.display_compact_status()
        elif mode == "detailed":
            return self.card_display.display_detailed_status()
        elif mode == "visual":
            return self.card_display.display_ascii_visual()
        else:
            return self.card_display.display_compact_status()
    
    def display_full_game_info(self) -> str:
        """显示完整游戏信息"""
        lines = []
        
        # 牌堆状态
        lines.append(self.card_display.display_detailed_status())
        
        # 玩家手牌
        for player_id, hand_cards in self.player_hands.items():
            lines.append(f"\n=== {player_id} 手牌 ===")
            lines.append(self.card_display.get_hand_display(hand_cards))
        
        # 警告信息
        warnings = self.card_display.get_warning_messages()
        if warnings:
            lines.append("\n=== 系统提醒 ===")
            lines.extend(warnings)
        
        return "\n".join(lines)

# 演示函数
def demo_card_display():
    """演示卡牌显示系统"""
    print("=== 卡牌显示系统演示 ===")
    
    # 创建牌堆和显示管理器
    from ...models.deck import EnhancedDeck
    deck = EnhancedDeck()
    display_manager = CardDisplayManager(deck)
    game_interface = GameDisplayInterface(deck)
    
    # 显示初始状态
    print("\n--- 初始状态 ---")
    print(game_interface.display_game_status("detailed"))
    
    # 模拟摸牌
    print("\n--- 摸牌后 ---")
    hand1 = deck.draw_cards(5)
    hand2 = deck.draw_cards(5)
    
    game_interface.update_player_hand("玩家1", hand1)
    game_interface.update_player_hand("玩家2", hand2)
    
    # 显示ASCII可视化
    print(game_interface.display_game_status("visual"))
    
    # 显示完整信息
    print(game_interface.display_full_game_info())
    
    return game_interface

if __name__ == "__main__":
    demo_card_display()