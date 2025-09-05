"""
三国杀技能模块
"""
from abc import ABC, abstractmethod
from typing import Optional, List
# 注意：避免循环导入，不要直接导入Game, Player, Card类
# 可以使用字符串类型注解或在函数内部导入


class Skill(ABC):
    """技能基类"""
    def __init__(self, name: str, description: str = ""):
        self.name = name
        self.description = description
    
    @abstractmethod
    def can_trigger(self, game: 'Game', player: 'Player', target: Optional['Player'] = None) -> bool:
        """检查技能是否可以触发"""
        pass
    
    @abstractmethod
    def execute(self, game: 'Game', player: 'Player', target: Optional['Player'] = None) -> bool:
        """执行技能效果"""
        pass


class SkillManager:
    """技能管理器"""
    def __init__(self):
        self.skills = {}
    
    def register_skill(self, skill: Skill):
        """注册技能"""
        self.skills[skill.name] = skill
    
    def get_skill(self, name: str) -> Optional[Skill]:
        """获取技能"""
        return self.skills.get(name)
    
    def trigger_skill(self, skill_name: str, game: 'Game', player: 'Player', target: Optional['Player'] = None) -> bool:
        """触发技能"""
        skill = self.get_skill(skill_name)
        if skill and skill.can_trigger(game, player, target):
            print(f"{player.character.name} 发动了技能【{skill_name}】")
            return skill.execute(game, player, target)
        return False


# ========== 具体技能实现 ==========

class JianXiong(Skill):
    """奸雄技能"""
    def __init__(self):
        super().__init__("奸雄", "当你受到伤害后，你可以获得对你造成伤害的牌。")
    
    def can_trigger(self, game: 'Game', player: 'Player', target: Optional['Player'] = None) -> bool:
        # 简化实现，实际需要检查是否受到伤害
        return target is not None and len(target.hand_cards) > 0
    
    def execute(self, game: 'Game', player: 'Player', target: Optional['Player'] = None) -> bool:
        if target and target.hand_cards:
            card = target.hand_cards.pop()
            player.hand_cards.append(card)
            print(f"{player.character.name} 发动技能【奸雄】，获得了 {card}")
            return True
        return False


class FanKui(Skill):
    """反馈技能"""
    def __init__(self):
        super().__init__("反馈", "当你受到伤害后，你可以获得伤害来源的一张手牌或装备牌。")
    
    def can_trigger(self, game: 'Game', player: 'Player', target: Optional['Player'] = None) -> bool:
        # 简化实现，实际需要检查是否受到伤害
        return target is not None and (len(target.hand_cards) > 0 or target.weapon is not None)
    
    def execute(self, game: 'Game', player: 'Player', target: Optional['Player'] = None) -> bool:
        if target:
            # 简化实现，实际需要让玩家选择获得手牌还是装备牌
            if target.hand_cards:
                card = target.hand_cards.pop()
                player.hand_cards.append(card)
                print(f"{player.character.name} 发动技能【反馈】，获得了 {card}")
                return True
            elif target.weapon:
                weapon = target.weapon
                target.weapon = None
                player.weapon = weapon
                print(f"{player.character.name} 发动技能【反馈】，获得了武器 {weapon}")
                return True
        return False


class GangLie(Skill):
    """刚烈技能"""
    def __init__(self):
        super().__init__("刚烈", "当你受到1点伤害后，你可以判定，若结果不为红桃，则伤害来源选择弃置2张手牌或受到1点伤害。")
    
    def can_trigger(self, game: 'Game', player: 'Player', target: Optional['Player'] = None) -> bool:
        # 简化实现，实际需要检查是否受到伤害
        return target is not None
    
    def execute(self, game: 'Game', player: 'Player', target: Optional['Player'] = None) -> bool:
        if target:
            # 简化实现，实际需要进行判定
            print(f"{player.character.name} 发动技能【刚烈】")
            # 简化实现，实际需要让伤害来源选择弃置手牌或受到伤害
            target.hand_cards = target.hand_cards[:-2] if len(target.hand_cards) >= 2 else []
            print(f"{target.character.name} 弃置了2张手牌")
            return True
        return False


class PaoXiao(Skill):
    """咆哮技能"""
    def __init__(self):
        super().__init__("咆哮", "出牌阶段，你可以使用任意数量的【杀】。")
    
    def can_trigger(self, game: 'Game', player: 'Player', target: Optional['Player'] = None) -> bool:
        # 检查是否在出牌阶段
        return game.current_phase == 'play' and player == game.current_player
    
    def execute(self, game: 'Game', player: 'Player', target: Optional['Player'] = None) -> bool:
        print(f"{player.character.name} 发动技能【咆哮】，本回合可以使用任意数量的【杀】")
        # 实际实现需要修改游戏逻辑，允许使用任意数量的杀
        return True


class GuanXing(Skill):
    """观星技能"""
    def __init__(self):
        super().__init__("观星", "准备阶段，你可以观看牌堆顶的X张牌，然后将之以任意顺序置于牌堆顶或牌堆底。")
    
    def can_trigger(self, game: 'Game', player: 'Player', target: Optional['Player'] = None) -> bool:
        # 简化实现，实际需要检查是否在准备阶段
        return len(game.deck) >= 2
    
    def execute(self, game: 'Game', player: 'Player', target: Optional['Player'] = None) -> bool:
        if len(game.deck) >= 2:
            # 简化实现，实际需要让玩家选择如何排列牌
            cards = [game.deck.pop(), game.deck.pop()]
            game.deck.extend(cards)
            print(f"{player.character.name} 发动技能【观星】")
            return True
        return False


class QiXi(Skill):
    """奇袭技能"""
    def __init__(self):
        super().__init__("奇袭", "出牌阶段，你可以将一张黑色牌当【过河拆桥】使用。")
    
    def can_trigger(self, game: 'Game', player: 'Player', target: Optional['Player'] = None) -> bool:
        # 简化实现，实际需要检查是否有黑色牌
        return any(card.suit in ['♠', '♣'] for card in player.hand_cards)
    
    def execute(self, game: 'Game', player: 'Player', target: Optional['Player'] = None) -> bool:
        # 简化实现，实际需要让玩家选择一张黑色牌
        for i, card in enumerate(player.hand_cards):
            if card.suit in ['♠', '♣']:
                player.hand_cards.pop(i)
                print(f"{player.character.name} 发动技能【奇袭】，将 {card} 当【过河拆桥】使用")
                return True
        return False


class KeJi(Skill):
    """克己技能"""
    def __init__(self):
        super().__init__("克己", "若你没有使用或打出过【杀】，你可以跳过弃牌阶段。")
    
    def can_trigger(self, game: 'Game', player: 'Player', target: Optional['Player'] = None) -> bool:
        # 检查玩家是否使用过杀
        return not player.has_used_sha
    
    def execute(self, game: 'Game', player: 'Player', target: Optional['Player'] = None) -> bool:
        print(f"{player.character.name} 发动技能【克己】，跳过弃牌阶段")
        # 实际实现需要修改游戏逻辑，跳过弃牌阶段
        return True


class YingZi(Skill):
    """英姿技能"""
    def __init__(self):
        super().__init__("英姿", "摸牌阶段，你可以多摸一张牌。")
    
    def can_trigger(self, game: 'Game', player: 'Player', target: Optional['Player'] = None) -> bool:
        # 检查是否在摸牌阶段
        return game.current_phase == 'draw' and player == game.current_player
    
    def execute(self, game: 'Game', player: 'Player', target: Optional['Player'] = None) -> bool:
        print(f"{player.character.name} 发动技能【英姿】，多摸一张牌")
        # 实际实现需要修改游戏逻辑，多摸一张牌
        if game.deck:
            card = game.deck.pop()
            player.hand_cards.append(card)
        return True