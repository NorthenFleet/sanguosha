from abc import ABC, abstractmethod


class Skill(ABC):
    def __init__(self, name, description, skill_type):
        self.name = name
        self.description = description
        self.skill_type = skill_type

    @abstractmethod
    def can_activate(self, game_state, player, **kwargs):
        """
        判断技能是否满足激活条件
        :param game_state: 当前游戏状态
        :param player: 触发技能的玩家
        :return: 布尔值，表示技能是否可以激活
        """
        pass

    @abstractmethod
    def trigger(self, game_state, player, target=None, **kwargs):
        """
        发起技能的效果
        :param game_state: 当前游戏状态
        :param player: 触发技能的玩家
        :param target: 受技能影响的目标
        """
        pass

    @abstractmethod
    def respond(self, game_state, player, source, **kwargs):
        """
        响应技能的效果
        :param game_state: 当前游戏状态
        :param player: 响应技能的玩家
        :param source: 发起技能的玩家
        """
        pass

# 杀


class Slash(Skill):
    def __init__(self):
        super().__init__(name="杀", description="对目标造成1点伤害。", skill_type="主动技能")

    def can_activate(self, game_state, player, target):
        if target == player:
            return False
        if not target.is_alive():
            return False
        return True

    def trigger(self, game_state, player, target=None, **kwargs):
        """发起技能"""
        print(f"{player.name} 对 {target.name} 使用了【杀】")
        game_state.create_event("slash", source=player, target=target)

    def respond(self, game_state, player, source, **kwargs):
        """响应技能"""
        if player.can_respond_with_dodge():
            if player.choose_to_dodge():
                print(f"{player.name} 打出了【闪】，躲避了【杀】的攻击")
                return True
        player.take_damage(1)
        print(f"{player.name} 受到1点伤害，当前体力为 {player.health}")
        return False


# 闪
class Dodge(Skill):
    def __init__(self):
        super().__init__(name="闪", description="抵消一次杀的伤害。", skill_type="响应技能")

    def can_activate(self, game_state, player, **kwargs):
        return '闪' in player.hand_cards

    def trigger(self, game_state, player, **kwargs):
        """闪没有触发效果，直接响应"""
        pass

    def respond(self, game_state, player, source, **kwargs):
        """响应技能，抵消杀的效果"""
        player.discard_card('闪')
        print(f"{player.name} 打出了【闪】，成功躲避了攻击")
        return True


# 桃
class Peach(Skill):
    def __init__(self):
        super().__init__(name="桃", description="回复自己或其他角色1点体力。", skill_type="主动技能")

    def can_activate(self, game_state, player, target=None):
        if '桃' not in player.hand_cards:
            return False
        if target:
            return target.is_alive() and target.health < target.max_health
        else:
            return player.health < player.max_health

    def trigger(self, game_state, player, target=None, **kwargs):
        print(f"{player.name} 使用了【桃】")
        if not target:
            target = player
        game_state.create_event("peach", source=player, target=target)

    def respond(self, game_state, player, source, **kwargs):
        """响应桃的效果，恢复体力"""
        player.heal(1)
        print(f"{player.name} 恢复了1点体力，当前体力为 {player.health}")

# 酒


class Wine(Skill):
    def __init__(self):
        super().__init__(name="酒", description="本回合内下一张杀的伤害+1，或在濒死状态下回复1点体力。", skill_type="主动技能")

    def can_activate(self, game_state, player, **kwargs):
        if '酒' not in player.hand_cards:
            return False
        if player.health == 0:
            return True
        else:
            return True

    def trigger(self, game_state, player, **kwargs):
        player.discard_card('酒')
        if player.health == 0:
            game_state.create_event("peach", source=player, target=player)
        else:
            player.has_used_wine = True
            print(f"{player.name} 使用了【酒】，本回合内下一张【杀】的伤害+1")

    def respond(self, game_state, player, source, **kwargs):
        """响应酒的效果，处理濒死恢复体力"""
        player.heal(1)
        print(f"{player.name} 恢复了1点体力，当前体力为 {player.health}")


# 决斗
class Duel(Skill):
    def __init__(self):
        super().__init__(
            name="决斗", description="与目标角色进行决斗，轮流打出【杀】，直到一方无法出杀并受到1点伤害。", skill_type="主动技能")

    def can_activate(self, game_state, player, target):
        """
        判断是否可以发起决斗
        :param game_state: 当前游戏状态
        :param player: 发起决斗的玩家
        :param target: 决斗的目标玩家
        :return: 布尔值
        """
        if target == player:
            return False
        if not target.is_alive():
            return False
        return True

    def trigger(self, game_state, player, target=None, **kwargs):
        """发起决斗"""
        print(f"{player.name} 向 {target.name} 发起了【决斗】")
        game_state.create_event("duel", source=player, target=target)

    def respond(self, game_state, player, source, **kwargs):
        """响应决斗"""
        if player.can_respond_with_slash():
            if player.choose_to_slash():
                print(f"{player.name} 打出了【杀】来响应决斗")
                game_state.create_event("duel", source=player, target=source)
            else:
                print(f"{player.name} 放弃了出杀，受到1点伤害")
                player.take_damage(1)
        else:
            print(f"{player.name} 无法出杀，受到1点伤害")
            player.take_damage(1)
