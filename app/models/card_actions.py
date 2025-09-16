"""卡牌动作模块 - 包含所有卡牌的动作实现"""

from app.models.action import CardAction


class ShaAction(CardAction):
    def __init__(self):
        super().__init__("杀", "basic", "对目标角色造成1点伤害")
    
    def get_response_cards(self, player):
        return ["闪"]
    
    def process_response(self, game, player, opponent, response_card):
        print(f"{opponent.character.name} 使用了 {response_card} 闪避了杀。")
        # 移除使用的闪
        for i, c in enumerate(opponent.hand_cards):
            if c.name == response_card:
                opponent.hand_cards.pop(i)
                break
        return False  # 响应成功，不受到伤害
    
    def apply_default_effect(self, game, player, target=None):
        opponent = game.get_opponent(player)
        print(f"{opponent.character.name} 没有闪可以响应，受到1点伤害。")
        opponent.character.hp -= 1
        return True
    
    def apply_effect(self, game, player, target=None):
        # 杀的效果在handle_response中处理
        return True


class TaoAction(CardAction):
    def __init__(self):
        super().__init__("桃", "basic", "回复1点体力")
    
    def apply_effect(self, game, player, target=None):
        if player.character.hp < player.character.max_hp:
            player.character.hp += 1
            print(f"{player.character.name} 使用桃回复了1点体力，当前体力: {player.character.hp}")
        else:
            print(f"{player.character.name} 体力已满，无法使用桃。")
        return True


class ShanAction(CardAction):
    def __init__(self):
        super().__init__("闪", "basic", "闪避攻击")
    
    def apply_effect(self, game, player, target=None):
        print(f"{player.character.name} 使用了闪。")
        return True


class WuXieKeJiAction(CardAction):
    def __init__(self):
        super().__init__("无懈可击", "trick", "抵消锦囊牌的效果")
    
    def apply_effect(self, game, player, target=None):
        print(f"{player.character.name} 使用了无懈可击。")
        return True


class GuoHeChaiQiaoAction(CardAction):
    def __init__(self):
        super().__init__("过河拆桥", "trick", "弃置目标角色的一张牌")
    
    def apply_effect(self, game, player, target=None):
        opponent = game.get_opponent(player)
        if opponent.hand_cards:
            discarded_card = opponent.hand_cards.pop(0)
            print(f"{player.character.name} 使用过河拆桥，弃置了 {opponent.character.name} 的 {discarded_card}")
        else:
            print(f"{opponent.character.name} 没有手牌可以弃置。")
        return True


class ShunShouQianYangAction(CardAction):
    def __init__(self):
        super().__init__("顺手牵羊", "trick", "获得目标角色的一张牌")
    
    def apply_effect(self, game, player, target=None):
        opponent = game.get_opponent(player)
        if opponent.hand_cards:
            stolen_card = opponent.hand_cards.pop(0)
            player.hand_cards.append(stolen_card)
            print(f"{player.character.name} 使用顺手牵羊，获得了 {opponent.character.name} 的 {stolen_card}")
        else:
            print(f"{opponent.character.name} 没有手牌可以获得。")
        return True


class WuZhongShengYouAction(CardAction):
    def __init__(self):
        super().__init__("无中生有", "trick", "摸两张牌")
    
    def apply_effect(self, game, player, target=None):
        for _ in range(2):
            if game.deck.cards:
                card = game.deck.draw_card()
                player.hand_cards.append(card)
                print(f"{player.character.name} 使用无中生有摸了一张 {card}")
        return True


class JueDouAction(CardAction):
    def __init__(self):
        super().__init__("决斗", "trick", "与目标角色决斗")
    
    def get_response_cards(self, player):
        return ["杀"]
    
    def process_response(self, game, player, opponent, response_card):
        print(f"{opponent.character.name} 使用了 {response_card} 响应决斗。")
        # 移除使用的杀
        for i, c in enumerate(opponent.hand_cards):
            if c.name == response_card:
                opponent.hand_cards.pop(i)
                break
        
        # 现在轮到发起决斗的玩家响应
        sha_cards = [c for c in player.hand_cards if c.name == "杀"]
        if sha_cards:
            # 自动使用第一张杀
            player.hand_cards.remove(sha_cards[0])
            print(f"{player.character.name} 使用了杀继续决斗。")
            # 继续决斗循环...
            return self.process_response(game, opponent, player, "杀")
        else:
            print(f"{player.character.name} 没有杀可以响应，受到1点伤害。")
            player.character.hp -= 1
            return False
    
    def apply_default_effect(self, game, player, target=None):
        opponent = game.get_opponent(player)
        print(f"{opponent.character.name} 没有杀可以响应决斗，受到1点伤害。")
        opponent.character.hp -= 1
        return True
    
    def apply_effect(self, game, player, target=None):
        # 决斗的效果在handle_response中处理
        return True


class NanManRuQinAction(CardAction):
    def __init__(self):
        super().__init__("南蛮入侵", "trick", "所有角色需要打出一张杀，否则受到1点伤害")
    
    def get_response_cards(self, player):
        return ["杀"]
    
    def process_response(self, game, player, opponent, response_card):
        print(f"{opponent.character.name} 使用了 {response_card} 响应南蛮入侵。")
        # 移除使用的杀
        for i, c in enumerate(opponent.hand_cards):
            if c.name == response_card:
                opponent.hand_cards.pop(i)
                break
        return False  # 响应成功，不受到伤害
    
    def apply_default_effect(self, game, player, target=None):
        opponent = game.get_opponent(player)
        print(f"{opponent.character.name} 没有杀可以响应南蛮入侵，受到1点伤害。")
        opponent.character.hp -= 1
        return True
    
    def apply_effect(self, game, player, target=None):
        # 南蛮入侵的效果在handle_response中处理
        return True


class WanJianQiFaAction(CardAction):
    def __init__(self):
        super().__init__("万箭齐发", "trick", "所有角色需要打出一张闪，否则受到1点伤害")
    
    def get_response_cards(self, player):
        return ["闪"]
    
    def process_response(self, game, player, opponent, response_card):
        print(f"{opponent.character.name} 使用了 {response_card} 响应万箭齐发。")
        # 移除使用的闪
        for i, c in enumerate(opponent.hand_cards):
            if c.name == response_card:
                opponent.hand_cards.pop(i)
                break
        return False  # 响应成功，不受到伤害
    
    def apply_default_effect(self, game, player, target=None):
        opponent = game.get_opponent(player)
        print(f"{opponent.character.name} 没有闪可以响应万箭齐发，受到1点伤害。")
        opponent.character.hp -= 1
        return True
    
    def apply_effect(self, game, player, target=None):
        # 万箭齐发的效果在handle_response中处理
        return True


class DefaultAction(CardAction):
    def __init__(self, card_name):
        super().__init__(card_name, "basic", "默认卡牌效果")
    
    def apply_effect(self, game, player, target=None):
        print(f"{self.name} 无需响应。")
        return True


# 卡牌动作工厂函数
def create_card_action(card):
    """根据卡牌创建对应的动作实例"""
    action_map = {
        "杀": ShaAction,
        "桃": TaoAction,
        "闪": ShanAction,
        "无懈可击": WuXieKeJiAction,
        "过河拆桥": GuoHeChaiQiaoAction,
        "顺手牵羊": ShunShouQianYangAction,
        "无中生有": WuZhongShengYouAction,
        "决斗": JueDouAction,
        "南蛮入侵": NanManRuQinAction,
        "万箭齐发": WanJianQiFaAction,
    }
    
    action_class = action_map.get(card.name)
    if action_class:
        return action_class()
    else:
        return DefaultAction(card.name)