"""
三国杀1v1出牌和技能使用的基本模型
"""
from abc import ABC, abstractmethod
from typing import List, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from .game import Game, Player
    from .character import Character


class Action(ABC):
    """出牌或技能使用的基类"""
    
    def __init__(self, name: str, description: str = ""):
        self.name = name
        self.description = description
    
    @abstractmethod
    def can_execute(self, game: 'Game', player: 'Player', target: Optional['Player'] = None) -> bool:
        """检查是否可以执行该动作"""
        pass
    
    @abstractmethod
    def execute(self, game: 'Game', player: 'Player', target: Optional['Player'] = None) -> bool:
        """执行动作"""
        pass
    
    def handle_response(self, game: 'Game', player: 'Player', target: Optional['Player'] = None) -> bool:
        """处理对手的响应"""
        # 默认实现不处理响应
        return True


class CardAction(Action):
    """卡牌动作基类"""
    
    def __init__(self, name: str, card_type: str, description: str = ""):
        super().__init__(name, description)
        self.card_type = card_type
    
    def can_execute(self, game: 'Game', player: 'Player', target: Optional['Player'] = None) -> bool:
        """检查是否可以执行该卡牌动作"""
        # 默认实现，子类可以重写
        return True
    
    def execute(self, game: 'Game', player: 'Player', target: Optional['Player'] = None) -> bool:
        """执行卡牌动作"""
        print(f"{player.character.name} 使用了 {self.name}")
        # 执行卡牌效果
        return self.apply_effect(game, player, target)
    
    @abstractmethod
    def apply_effect(self, game: 'Game', player: 'Player', target: Optional['Player'] = None) -> bool:
        """应用卡牌效果"""
        pass
    
    def handle_response(self, game: 'Game', player: 'Player', target: Optional['Player'] = None, test_mode: bool = False) -> bool:
        """处理对手的响应"""
        opponent = game.get_opponent(player)
        print(f"{opponent.character.name} 需要响应 {self.name}...")
        
        # 检查是否有响应卡牌
        response_cards = self.get_response_cards(opponent)
        
        if response_cards:
            # 让对手选择是否响应
            use_response = self.ask_for_response(game, opponent, response_cards, test_mode)
            if use_response:
                # 处理响应卡牌
                return self.process_response(game, player, opponent, use_response)
        
        # 没有响应或不响应，执行默认效果
        return self.apply_default_effect(game, player, target)
    
    def get_response_cards(self, player: 'Player') -> List[str]:
        """获取可以响应的卡牌类型"""
        # 默认实现，子类可以重写
        return []
    
    def ask_for_response(self, game: 'Game', player: 'Player', response_cards: List[str], test_mode: bool = False) -> Optional[str]:
        """询问玩家是否使用响应卡牌"""
        # 在实际实现中，这会与用户界面交互
        # 在测试模式下，可以自动选择
        if test_mode:
            # 测试模式下自动选择第一张响应卡牌，但只选择玩家实际拥有的卡牌
            for card_name in response_cards:
                if any(c.name == card_name for c in player.hand_cards):
                    return card_name
            return None
        
        # 实际实现中需要与用户交互
        print(f"\n{player.character.name} 的回合 - 需要响应 {self.name}")
        print(f"当前手牌:")
        for idx, card in enumerate(player.hand_cards, start=1):
            print(f"{idx}. {card}")
        
        print(f"\n可以使用的响应卡牌: {', '.join(response_cards)}")
        print("0. 结束响应")
        
        try:
            choice = input("选择要使用的响应卡牌编号 (输入0结束响应): ")
            if choice == "0":
                return None
            
            choice = int(choice) - 1
            if 0 <= choice < len(player.hand_cards):
                selected_card = player.hand_cards[choice]
                if selected_card.name in response_cards:
                    return selected_card.name
                else:
                    print("选择的卡牌不能用于响应，请重新选择。")
                    return self.ask_for_response(game, player, response_cards, test_mode)
            else:
                print("选择无效，请重新选择。")
                return self.ask_for_response(game, player, response_cards, test_mode)
        except ValueError:
            print("输入无效，请重新选择。")
            return self.ask_for_response(game, player, response_cards, test_mode)
    
    def process_response(self, game: 'Game', player: 'Player', opponent: 'Player', response_card: str) -> bool:
        """处理响应卡牌"""
        print(f"{opponent.character.name} 使用了 {response_card}")
        # 移除响应卡牌
        # 这里需要具体实现
        
        # 可能需要进一步的响应
        return self.handle_further_response(game, player, opponent, response_card)
    
    def handle_further_response(self, game: 'Game', player: 'Player', opponent: 'Player', response_card: str) -> bool:
        """处理进一步的响应"""
        # 默认实现不处理进一步的响应
        return True
    
    def apply_default_effect(self, game: 'Game', player: 'Player', target: Optional['Player'] = None) -> bool:
        """应用默认效果（当没有响应或响应失败时）"""
        # 默认实现，子类可以重写
        return True


class SkillAction(Action):
    """技能动作基类"""
    
    def can_execute(self, game: 'Game', player: 'Player', target: Optional['Player'] = None) -> bool:
        """检查是否可以执行该技能动作"""
        # 默认实现，子类可以重写
        return True
    
    def execute(self, game: 'Game', player: 'Player', target: Optional['Player'] = None) -> bool:
        """执行技能动作"""
        print(f"{player.character.name} 使用了技能 {self.name}")
        # 执行技能效果
        return self.apply_effect(game, player, target)
    
    @abstractmethod
    def apply_effect(self, game: 'Game', player: 'Player', target: Optional['Player'] = None) -> bool:
        """应用技能效果"""
        pass