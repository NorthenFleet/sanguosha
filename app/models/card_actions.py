"""卡牌动作模块 - 包含所有卡牌的动作实现"""

from app.models.action import CardAction


class ShaAction(CardAction):
    def __init__(self):
        super().__init__("杀", "basic", "对目标角色造成1点伤害")
    
    def get_response_cards(self, player):
        response_cards = ["闪"]
        # 八卦阵可以提供额外的闪避机会
        if player.has_defense_equipment("八卦阵"):
            response_cards.append("八卦阵判定")
        return response_cards
    
    def process_response(self, game, player, opponent, response_card):
        if response_card == "八卦阵判定":
            # 八卦阵判定
            if opponent.can_dodge_with_bagua():
                print(f"{opponent.character.name} 通过八卦阵判定闪避了杀。")
            else:
                print(f"{opponent.character.name} 八卦阵判定失败，无法闪避。")
                return True  # 判定失败，受到伤害
        else:
            print(f"{opponent.character.name} 使用了 {response_card} 闪避了杀。")
            # 移除使用的闪并放入弃牌堆
            for i, c in enumerate(opponent.hand_cards):
                if c.name == response_card:
                    used_card = opponent.hand_cards.pop(i)
                    game.deck.discard(used_card)
                    print(f"响应卡牌 {response_card} 进入弃牌堆")
                    break
        
        # 青龙偃月刀效果：对方使用闪后，可以继续出杀
        if player.has_weapon_effect("青龙偃月刀"):
            print(f"{player.character.name} 装备了青龙偃月刀，可以继续出杀！")
            # 检查是否还有杀可以使用
            sha_cards = [c for c in player.hand_cards if c.name == "杀"]
            if sha_cards:
                print(f"请选择是否继续出杀：")
                for i, card in enumerate(sha_cards):
                    print(f"{i+1}. {card}")
                print(f"{len(sha_cards)+1}. 不出杀")
                
                try:
                    choice = input("请选择: ")
                    choice_idx = int(choice) - 1
                    if 0 <= choice_idx < len(sha_cards):
                        # 继续出杀
                        selected_card = sha_cards[choice_idx]
                        player.hand_cards.remove(selected_card)
                        print(f"{player.character.name} 继续出杀！")
                        # 递归处理新的杀
                        return game.handle_response(player, opponent, self)
                    else:
                        print(f"{player.character.name} 选择不继续出杀。")
                except (ValueError, EOFError):
                    print(f"{player.character.name} 选择不继续出杀。")
            else:
                print(f"{player.character.name} 没有更多的杀可以使用。")
        
        return False  # 响应成功，不受到伤害
    
    def apply_default_effect(self, game, player, target=None):
        opponent = game.get_opponent(player)
        print(f"{opponent.character.name} 没有闪可以响应，受到1点伤害。")
        opponent.character.hp -= 1
        return True
    
    def apply_effect(self, game, player, target=None):
        # 检查攻击范围
        opponent = game.get_opponent(player)
        if not player.can_attack(opponent):
            print(f"{opponent.character.name} 不在攻击范围内！")
            return False
        
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
    
    def _select_card_from_opponent(self, opponent):
        """从对手的手牌、装备区、判定区中选择一张牌"""
        all_cards = opponent.get_all_cards()
        available_areas = []
        
        # 检查各个区域是否有牌
        if all_cards['hand']:
            available_areas.append(('hand', '手牌', all_cards['hand']))
        if all_cards['equipment']:
            available_areas.append(('equipment', '装备区', all_cards['equipment']))
        if all_cards['judgment']:
            available_areas.append(('judgment', '判定区', all_cards['judgment']))
        
        if not available_areas:
            return None, None
        
        # 简化选择逻辑：优先选择手牌，然后装备区，最后判定区
        area_type, area_name, cards = available_areas[0]
        selected_card = cards[0]  # 选择第一张牌
        
        return selected_card, area_type
    
    def apply_effect(self, game, player, target=None):
        opponent = game.get_opponent(player)
        selected_card, area_type = self._select_card_from_opponent(opponent)
        
        if selected_card:
            # 从对手区域移除牌
            opponent.remove_card_from_area(selected_card, area_type)
            # 将牌放入弃牌堆
            game.discard_pile.append(selected_card)
            
            area_names = {'hand': '手牌', 'equipment': '装备区', 'judgment': '判定区'}
            print(f"{player.character.name} 使用过河拆桥，弃置了 {opponent.character.name} {area_names[area_type]}的 {selected_card.name}")
        else:
            print(f"{opponent.character.name} 没有可以弃置的牌。")
        return True


class ShunShouQianYangAction(CardAction):
    def __init__(self):
        super().__init__("顺手牵羊", "trick", "获得目标角色的一张牌")
    
    def _select_card_from_opponent(self, opponent):
        """从对手的手牌、装备区、判定区中选择一张牌"""
        all_cards = opponent.get_all_cards()
        available_areas = []
        
        # 检查各个区域是否有牌
        if all_cards['hand']:
            available_areas.append(('hand', '手牌', all_cards['hand']))
        if all_cards['equipment']:
            available_areas.append(('equipment', '装备区', all_cards['equipment']))
        if all_cards['judgment']:
            available_areas.append(('judgment', '判定区', all_cards['judgment']))
        
        if not available_areas:
            return None, None
        
        # 简化选择逻辑：优先选择手牌，然后装备区，最后判定区
        area_type, area_name, cards = available_areas[0]
        selected_card = cards[0]  # 选择第一张牌
        
        return selected_card, area_type
    
    def apply_effect(self, game, player, target=None):
        opponent = game.get_opponent(player)
        
        # 检查距离限制（顺手牵羊要求距离为1）
        distance = player.get_distance_to(opponent)
        if distance > 1:
            print(f"{player.character.name} 使用顺手牵羊失败，{opponent.character.name} 距离过远（距离：{distance}）")
            return False
        
        selected_card, area_type = self._select_card_from_opponent(opponent)
        
        if selected_card:
            # 从对手区域移除牌
            opponent.remove_card_from_area(selected_card, area_type)
            # 将牌加入自己手牌
            player.hand_cards.append(selected_card)
            
            area_names = {'hand': '手牌', 'equipment': '装备区', 'judgment': '判定区'}
            print(f"{player.character.name} 使用顺手牵羊，从 {opponent.character.name} {area_names[area_type]}获得了 {selected_card.name}")
        else:
            print(f"{opponent.character.name} 没有可以获得的牌。")
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
        # 移除使用的杀并放入弃牌堆
        for i, c in enumerate(opponent.hand_cards):
            if c.name == response_card:
                used_card = opponent.hand_cards.pop(i)
                game.deck.discard(used_card)
                print(f"响应卡牌 {response_card} 进入弃牌堆")
                break
        
        # 现在轮到发起决斗的玩家响应
        sha_cards = [c for c in player.hand_cards if c.name == "杀"]
        if sha_cards:
            # 自动使用第一张杀
            used_sha = sha_cards[0]
            player.hand_cards.remove(used_sha)
            game.deck.discard(used_sha)
            print(f"{player.character.name} 使用了杀继续决斗，进入弃牌堆")
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
        # 移除使用的杀并放入弃牌堆
        for i, c in enumerate(opponent.hand_cards):
            if c.name == response_card:
                used_card = opponent.hand_cards.pop(i)
                game.deck.discard(used_card)
                print(f"响应卡牌 {response_card} 进入弃牌堆")
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
        # 移除使用的闪并放入弃牌堆
        for i, c in enumerate(opponent.hand_cards):
            if c.name == response_card:
                used_card = opponent.hand_cards.pop(i)
                game.deck.discard(used_card)
                print(f"响应卡牌 {response_card} 进入弃牌堆")
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