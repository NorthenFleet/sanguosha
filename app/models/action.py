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
        # 如果是锦囊牌，先询问所有玩家是否使用无懈可击
        if self.card_type == "trick":
            # 询问所有玩家是否使用无懈可击
            for p in game.players:
                # 跳过使用者自己
                if p == player:
                    continue
                    
                print(f"询问 {p.character.name} 是否使用无懈可击响应 {self.name}...")
                # 检查玩家是否有无懈可击
                has_wuxie = any(c.name == "无懈可击" for c in p.hand_cards)
                
                # 无论是否有无懈可击，都询问玩家
                if has_wuxie:
                    # 让玩家选择是否使用无懈可击
                    use_wuxie = self.ask_for_response(game, p, ["无懈可击"], test_mode=(test_mode or game.current_phase == "test"))
                    if use_wuxie:
                        print(f"{p.character.name} 使用了无懈可击，抵消了 {self.name} 的效果。")
                        # 移除使用的无懈可击并放入弃牌堆
                        for i, c in enumerate(p.hand_cards):
                            if c.name == "无懈可击":
                                used_card = p.hand_cards.pop(i)
                                game.deck.discard(used_card)
                                print(f"无懈可击进入弃牌堆")
                                break
                        # 触发使用卡牌事件
                        game.event_manager.trigger("play_card", {"player": p, "card": used_card, "target": player})
                        # 获取无懈可击动作并执行
                        from .card_actions import WuXieKeJiAction
                        wuxie_action = WuXieKeJiAction()
                        wuxie_action.apply_effect(game, p, player, target_action=self)
                        return False  # 锦囊牌被无懈可击抵消
                else:
                    # 即使没有无懈可击，也询问玩家
                    print(f"{p.character.name} 没有无懈可击可以使用。")
                    # 在测试模式下，可以跳过询问
                    if not (test_mode or game.current_phase == "test"):
                        input(f"{p.character.name} 按任意键继续...")
                    else:
                        print(f"测试模式：自动跳过询问。")
        
        # 对于基本牌或者锦囊牌没有被无懈可击抵消的情况，询问目标玩家是否响应
        if target is None:
            # 如果没有指定目标，使用默认的对手
            target = game.get_opponent(player)
            
        # 对于群体锦囊牌，目标可能是多个，这种情况在具体的锦囊牌实现中处理
        # 这里只处理单一目标的情况
        if target:
            print(f"{target.character.name} 需要响应 {self.name}...")
            
            # 检查是否有响应卡牌
            response_cards = self.get_response_cards(target)
            
            if response_cards:
                # 让目标选择是否响应
                use_response = self.ask_for_response(game, target, response_cards, test_mode=(test_mode or game.current_phase == "test"))
                if use_response:
                    # 处理响应卡牌
                    return self.process_response(game, player, target, use_response)
        
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
        print(f"{opponent.character.name} 使用了 {response_card} 响应 {self.name}")
        # 移除响应卡牌并放入弃牌堆
        for i, c in enumerate(opponent.hand_cards):
            if c.name == response_card:
                used_card = opponent.hand_cards.pop(i)
                game.deck.discard(used_card)
                print(f"响应卡牌 {response_card} 进入弃牌堆")
                break
        
        # 触发使用卡牌事件
        game.event_manager.trigger("play_card", {"player": opponent, "card": used_card, "target": player})
        
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