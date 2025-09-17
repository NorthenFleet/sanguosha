"""
三国杀技能模块
"""
from abc import ABC, abstractmethod
from typing import Optional, List
# 注意：避免循环导入，不要直接导入Game, Player, Card类
# 可以使用字符串类型注解或在函数内部导入

# 在文件开头添加导入
from .action import SkillAction

class Skill(ABC):
    """技能基类"""
    def __init__(self, name: str, description: str = ""):
        self.name = name
        self.description = description
    
    @abstractmethod
    def can_trigger(self, game: 'Game', player: 'Player', event_type: str, **kwargs) -> bool:
        """检查技能是否可以触发"""
        pass
    
    @abstractmethod
    def execute(self, game: 'Game', player: 'Player', **kwargs) -> bool:
        """执行技能效果"""
        pass
    
    def create_skill_action(self):
        """创建技能动作实例"""
        # 默认实现，子类可以重写
        class DefaultSkillAction(SkillAction):
            def __init__(self, skill):
                super().__init__(skill.name, skill.description)
                self.skill = skill
            
            def apply_effect(self, game, player, **kwargs):
                # 调用原始的execute方法
                return self.skill.__class__.execute(self.skill, game, player, **kwargs)
        
        return DefaultSkillAction(self)


class SkillManager:
    """技能管理器"""
    def __init__(self):
        self.skills = {}
        self._register_default_skills()
    
    def _register_default_skills(self):
        """注册默认技能"""
        # 注册所有技能
        self.register_skill(JianXiong())
        self.register_skill(FanKui())
        self.register_skill(GangLie())
        self.register_skill(PaoXiao())
        self.register_skill(GuanXing())
        self.register_skill(KongCheng())
        self.register_skill(QiXi())
        self.register_skill(KeJi())
        self.register_skill(YingZi())
        self.register_skill(WuSheng())
        self.register_skill(ZhiHeng())
    
    def register_skill(self, skill: Skill):
        """注册技能"""
        self.skills[skill.name] = skill
    
    def get_skill(self, name: str) -> Optional[Skill]:
        """获取技能"""
        return self.skills.get(name)
    
    def trigger_skill(self, skill_name: str, game: 'Game', player: 'Player', event_type: str, **kwargs) -> bool:
        """触发技能"""
        skill = self.get_skill(skill_name)
        if skill and skill.can_trigger(game, player, event_type, **kwargs):
            print(f"{player.character.name} 发动了技能【{skill_name}】")
            # 使用新的技能动作模型
            skill_action = skill.create_skill_action()
            return skill_action.apply_effect(game, player, **kwargs)
        return False


# ========== 具体技能实现 ==========

class JianXiong(Skill):
    def __init__(self):
        super().__init__("奸雄", "当曹操受到1点伤害后，可以立即获得造成此伤害的牌")
    
    def can_trigger(self, game, player, event_type, **kwargs):
        return event_type == "take_damage" and player.character.name == "曹操"
    
    def execute(self, game, player, **kwargs):
        # 创建技能动作实例并执行
        skill_action = self.create_skill_action()
        return skill_action.apply_effect(game, player, **kwargs)
    
    def create_skill_action(self):
        """创建奸雄技能动作实例"""
        class JianXiongAction(SkillAction):
            def __init__(self):
                super().__init__("奸雄", "当曹操受到1点伤害后，可以立即获得造成此伤害的牌")
            
            def apply_effect(self, game, player, **kwargs):
                # 获取造成伤害的牌
                damage_card = kwargs.get('damage_card')
                if damage_card:
                    player.hand_cards.append(damage_card)
                    print(f"{player.character.name} 触发了 奸雄 技能，获得了 {damage_card}")
                    return True
                return False
        
        return JianXiongAction()


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
    def __init__(self):
        super().__init__("咆哮", "锁定技，出牌阶段，孙权使用【杀】无次数限制")
    
    def can_trigger(self, game, player, event_type, **kwargs):
        return event_type == "play_card" and player.character.name == "孙权" and kwargs.get('card').name == "杀"
    
    def execute(self, game, player, **kwargs):
        # 创建技能动作实例并执行
        skill_action = self.create_skill_action()
        return skill_action.apply_effect(game, player, **kwargs)
    
    def create_skill_action(self):
        """创建咆哮技能动作实例"""
        class PaoXiaoAction(SkillAction):
            def __init__(self):
                super().__init__("咆哮", "锁定技，出牌阶段，孙权使用【杀】无次数限制")
            
            def apply_effect(self, game, player, **kwargs):
                # 咆哮技能不需要额外执行效果，它只是一个标记
                print(f"{player.character.name} 使用了 咆哮 技能")
                return True
        
        return PaoXiaoAction()


class GuanXing(Skill):
    """观星技能"""
    def __init__(self):
        super().__init__("观星", "准备阶段，你可以观看牌堆顶的X张牌，然后将之以任意顺序置于牌堆顶或牌堆底。")
    
    def can_trigger(self, game, player, event_type, **kwargs):
        # 检查是否在准备阶段
        return event_type == "phase_change" and kwargs.get('phase') == "judgment" and player.character.name == "诸葛亮"
    
    def execute(self, game, player, **kwargs):
        # 创建技能动作实例并执行
        skill_action = self.create_skill_action()
        return skill_action.apply_effect(game, player, **kwargs)
    
    def create_skill_action(self):
        """创建观星技能动作实例"""
        class GuanXingAction(SkillAction):
            def __init__(self):
                super().__init__("观星", "准备阶段，你可以观看牌堆顶的X张牌，然后将之以任意顺序置于牌堆顶或牌堆底。")
            
            def apply_effect(self, game, player, **kwargs):
                # 获取牌堆顶的牌数量（根据玩家数量确定）
                num_cards = min(len(game.players), len(game.deck.cards))
                if num_cards > 0:
                    print(f"{player.character.name} 发动了【观星】技能，观看了牌堆顶的 {num_cards} 张牌")
                    
                    # 从牌堆顶获取牌
                    cards = []
                    for _ in range(num_cards):
                        card = game.deck.draw_card()
                        if card:
                            cards.append(card)
                    
                    # 显示这些牌
                    print("观看的牌:")
                    for i, card in enumerate(cards):
                        print(f"{i+1}. {card}")
                    
                    # 简化实现：将所有牌放回牌堆顶部
                    # 实际游戏中应该让玩家决定每张牌放在牌堆顶部还是底部
                    for card in cards:
                        game.deck.cards.insert(0, card)
                    
                    print(f"{player.character.name} 将牌放回了牌堆")
                    return True
                return False
        
        return GuanXingAction()


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
    
    def can_trigger(self, game, player, event_type, **kwargs):
        # 检查是否在摸牌阶段
        return event_type == "phase_change" and kwargs.get('phase') == "draw" and player.character.has_skill("英姿")
    
    def execute(self, game, player, **kwargs):
        # 创建技能动作实例并执行
        skill_action = self.create_skill_action()
        return skill_action.apply_effect(game, player, **kwargs)
    
    def create_skill_action(self):
        """创建英姿技能动作实例"""
        class YingZiAction(SkillAction):
            def __init__(self):
                super().__init__("英姿", "摸牌阶段，你可以多摸一张牌。")
            
            def apply_effect(self, game, player, **kwargs):
                print(f"{player.character.name} 发动了【英姿】技能，额外摸一张牌")
                card = game.deck.draw_card()
                if card:
                    player.hand_cards.append(card)
                    print(f"{player.character.name} 摸到了 {card}")
                    return True
                return False
        
        return YingZiAction()


class KongCheng(Skill):
    """空城技能"""
    def __init__(self):
        super().__init__("空城", "锁定技，当你没有手牌时，你不能成为【杀】或【决斗】的目标。")
    
    def can_trigger(self, game, player, event_type, **kwargs):
        # 检查是否是诸葛亮，且没有手牌，且是杀或决斗的目标
        target = kwargs.get('target')
        card = kwargs.get('card')
        return (event_type == "play_card" and 
                player.character.name == "诸葛亮" and 
                len(player.hand_cards) == 0 and 
                target == player and 
                card and card.name in ["杀", "决斗"])
    
    def execute(self, game, player, **kwargs):
        # 创建技能动作实例并执行
        skill_action = self.create_skill_action()
        return skill_action.apply_effect(game, player, **kwargs)
    
    def create_skill_action(self):
        """创建空城技能动作实例"""
        class KongChengAction(SkillAction):
            def __init__(self):
                super().__init__("空城", "锁定技，当你没有手牌时，你不能成为【杀】或【决斗】的目标。")
            
            def apply_effect(self, game, player, **kwargs):
                source = kwargs.get('player')  # 使用卡牌的玩家
                card = kwargs.get('card')      # 使用的卡牌
                
                print(f"{player.character.name} 触发了【空城】技能，不能成为 {card.name} 的目标")
                # 返回True表示技能生效，阻止了卡牌效果
                return True
        
        return KongChengAction()


class WuSheng(Skill):
    """武圣技能"""
    def __init__(self):
        super().__init__("武圣", "你可以将一张红色牌当【杀】使用或打出。")
    
    def can_trigger(self, game, player, event_type, **kwargs):
        # 检查是否是关羽，且有红色牌
        if event_type == "play_card" and player.character.name == "关羽":
            # 检查是否有红色牌
            return any(card.color == "红色" for card in player.hand_cards)
        return False
    
    def execute(self, game, player, **kwargs):
        # 创建技能动作实例并执行
        skill_action = self.create_skill_action()
        return skill_action.apply_effect(game, player, **kwargs)
    
    def create_skill_action(self):
        """创建武圣技能动作实例"""
        class WuShengAction(SkillAction):
            def __init__(self):
                super().__init__("武圣", "你可以将一张红色牌当【杀】使用或打出。")
            
            def apply_effect(self, game, player, **kwargs):
                # 找出所有红色牌
                red_cards = [card for card in player.hand_cards if card.color == "红色"]
                if not red_cards:
                    return False
                
                # 简化实现：使用第一张红色牌当杀
                card = red_cards[0]
                player.hand_cards.remove(card)
                
                # 获取目标
                target = game.get_opponent(player)
                
                print(f"{player.character.name} 发动了【武圣】技能，将 {card} 当【杀】使用，目标是 {target.character.name}")
                
                # 处理杀的效果
                game.handle_damage(target, 1, player)
                game.deck.discard_pile.append(card)
                
                return True
        
        return WuShengAction()


class ZhiHeng(Skill):
    """制衡技能"""
    def __init__(self):
        super().__init__("制衡", "出牌阶段限一次，你可以弃置任意张牌，然后摸等量的牌。")
    
    def can_trigger(self, game, player, event_type, **kwargs):
        # 检查是否是孙权，且在出牌阶段
        return (event_type == "phase_change" and 
                kwargs.get('phase') == "play" and 
                player.character.name == "孙权" and 
                not getattr(player, 'used_zhiheng', False))
    
    def execute(self, game, player, **kwargs):
        # 创建技能动作实例并执行
        skill_action = self.create_skill_action()
        return skill_action.apply_effect(game, player, **kwargs)
    
    def create_skill_action(self):
        """创建制衡技能动作实例"""
        class ZhiHengAction(SkillAction):
            def __init__(self):
                super().__init__("制衡", "出牌阶段限一次，你可以弃置任意张牌，然后摸等量的牌。")
            
            def apply_effect(self, game, player, **kwargs):
                # 标记已使用制衡
                setattr(player, 'used_zhiheng', True)
                
                # 简化实现：弃置一半手牌
                discard_count = len(player.hand_cards) // 2
                if discard_count == 0:
                    print(f"{player.character.name} 没有手牌可以弃置，无法发动【制衡】")
                    return False
                
                print(f"{player.character.name} 发动了【制衡】技能，弃置 {discard_count} 张牌")
                
                # 弃置牌
                discarded_cards = []
                for _ in range(discard_count):
                    if player.hand_cards:
                        card = player.hand_cards.pop(0)
                        game.deck.discard_pile.append(card)
                        discarded_cards.append(card)
                        # 触发弃牌事件
                        game.event_manager.trigger("discard_card", {"player": player, "card": card})
                
                # 显示弃置的牌
                for card in discarded_cards:
                    print(f"弃置了 {card}")
                
                # 摸等量的牌
                for _ in range(len(discarded_cards)):
                    card = game.deck.draw_card()
                    if card:
                        player.hand_cards.append(card)
                        print(f"摸到了 {card}")
                
                # 触发摸牌事件
                game.event_manager.trigger("draw_card", {"player": player, "count": len(discarded_cards)})
                
                return True
        
        return ZhiHengAction()