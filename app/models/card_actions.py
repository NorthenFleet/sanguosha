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
        if target is None:
            target = game.get_opponent(player)
        print(f"{target.character.name} 没有闪可以响应，受到1点伤害。")
        # 使用游戏的handle_damage方法来处理伤害，这样可以触发相关的装备效果和技能
        game.handle_damage(target, 1, damage_card=None)
        return True
    
    def apply_effect(self, game, player, target=None):
        # 如果没有指定目标，则选择目标
        if target is None:
            target = game.select_target(player, "选择【杀】的目标", test_mode=(game.current_phase == "test"))
        
        # 检查攻击范围
        if not player.can_attack(target):
            print(f"{target.character.name} 不在攻击范围内！")
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
        super().__init__("无懈可击", "trick", "抵消一张锦囊牌的效果")
    
    def apply_effect(self, game, player, target=None, target_action=None):
        # target_action是被抵消的锦囊牌动作
        if target_action:
            print(f"{player.character.name} 使用了无懈可击，抵消了{target_action.name}的效果。")
        else:
            print(f"{player.character.name} 使用了无懈可击，抵消了锦囊牌的效果。")
        return True
    
    def can_be_used_against(self, action):
        # 判断无懈可击是否可以对抗指定的动作
        # 只能对抗锦囊牌
        return action.card_type == "trick" and action.name != "无懈可击"


class GuoHeChaiQiaoAction(CardAction):
    def __init__(self):
        super().__init__("过河拆桥", "trick", "弃置目标角色的一张牌")
    
    def _select_card_from_opponent(self, opponent, game=None, player=None, test_mode=False):
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
        
        # 如果是测试模式，使用简化逻辑
        if test_mode:
            area_type, area_name, cards = available_areas[0]
            selected_card = cards[0]
            return selected_card, area_type
        
        # 正常模式：让玩家选择区域
        print(f"\n{player.character.name} 使用过河拆桥，选择要弃置 {opponent.character.name} 的牌：")
        print("可选择的区域：")
        for i, (area_type, area_name, cards) in enumerate(available_areas):
            print(f"{i + 1}. {area_name} ({len(cards)}张牌)")
        
        # 获取玩家选择的区域
        while True:
            try:
                choice = input(f"请选择区域 (1-{len(available_areas)}): ").strip()
                if not choice:  # 处理空输入
                    continue
                area_index = int(choice) - 1
                if 0 <= area_index < len(available_areas):
                    break
                else:
                    print("无效选择，请重新输入")
            except (ValueError, EOFError, KeyboardInterrupt):
                print("输入无效或被中断，请重新输入")
                continue
        
        selected_area_type, selected_area_name, selected_area_cards = available_areas[area_index]
        
        # 如果选择的是手牌区域，随机选择一张（因为看不到对手手牌）
        if selected_area_type == 'hand':
            import random
            selected_card = random.choice(selected_area_cards)
            print(f"从 {opponent.character.name} 的手牌中随机弃置了一张牌")
        else:
            # 装备区和判定区的牌是公开的，让玩家选择具体的牌
            print(f"\n{selected_area_name}中的牌：")
            for i, card in enumerate(selected_area_cards):
                print(f"{i + 1}. {card.name}")
            
            # 获取玩家选择的具体牌
            while True:
                try:
                    choice = input(f"请选择要弃置的牌 (1-{len(selected_area_cards)}): ").strip()
                    if not choice:  # 处理空输入
                        continue
                    card_index = int(choice) - 1
                    if 0 <= card_index < len(selected_area_cards):
                        selected_card = selected_area_cards[card_index]
                        break
                    else:
                        print("无效选择，请重新输入")
                except (ValueError, EOFError, KeyboardInterrupt):
                    print("输入无效或被中断，请重新输入")
                    continue
        
        return selected_card, selected_area_type
    
    def apply_effect(self, game, player, target=None):
        # 如果没有指定目标，则选择目标
        if target is None:
            target = game.select_target(player, "选择【过河拆桥】的目标", test_mode=(game.current_phase == "test"))
        
        # 先询问所有玩家是否使用无懈可击
        if not self.handle_response(game, player, target, test_mode=(game.current_phase == "test")):
            # 如果被无懈可击抵消，则不生效
            return False
        
        # 判断是否为测试模式
        test_mode = (game.current_phase == "test")
        selected_card, area_type = self._select_card_from_opponent(target, game, player, test_mode)
        
        if selected_card:
            # 从对手区域移除牌
            target.remove_card_from_area(selected_card, area_type)
            # 将牌放入弃牌堆
            game.discard_pile.append(selected_card)
            
            area_names = {'hand': '手牌', 'equipment': '装备区', 'judgment': '判定区'}
            print(f"{player.character.name} 使用过河拆桥，弃置了 {target.character.name} {area_names[area_type]}的 {selected_card.name}")
        else:
            print(f"{target.character.name} 没有可以弃置的牌。")
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
        # 如果没有指定目标，则选择目标
        if target is None:
            target = game.select_target(player, "选择【顺手牵羊】的目标", test_mode=(game.current_phase == "test"))
        
        # 检查距离限制（顺手牵羊要求距离为1）
        distance = player.get_distance_to(target)
        if distance > 1:
            print(f"{player.character.name} 使用顺手牵羊失败，{target.character.name} 距离过远（距离：{distance}）")
            return False
        
        # 先询问所有玩家是否使用无懈可击
        if not self.handle_response(game, player, target, test_mode=(game.current_phase == "test")):
            # 如果被无懈可击抵消，则不生效
            return False
        
        selected_card, area_type = self._select_card_from_opponent(target)
        
        if selected_card:
            # 从对手区域移除牌
            target.remove_card_from_area(selected_card, area_type)
            # 将牌加入自己手牌
            player.hand_cards.append(selected_card)
            
            area_names = {'hand': '手牌', 'equipment': '装备区', 'judgment': '判定区'}
            print(f"{player.character.name} 使用顺手牵羊，从 {target.character.name} {area_names[area_type]}获得了 {selected_card.name}")
        else:
            print(f"{target.character.name} 没有可以获得的牌。")
        return True


class WuZhongShengYouAction(CardAction):
    def __init__(self):
        super().__init__("无中生有", "trick", "摸两张牌")
    
    def apply_effect(self, game, player, target=None):
        # 先询问所有玩家是否使用无懈可击
        if not self.handle_response(game, player, None, test_mode=(game.current_phase == "test")):
            # 如果被无懈可击抵消，则不生效
            return False
            
        for _ in range(2):
            if game.deck.draw_pile:  # 使用draw_pile而不是cards
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
        if target is None:
            target = game.get_opponent(player)
        print(f"{target.character.name} 没有杀可以响应决斗，受到1点伤害。")
        target.character.hp -= 1
        return True
    
    def apply_effect(self, game, player, target=None):
        # 如果没有指定目标，则选择目标
        if target is None:
            target = game.select_target(player, "选择【决斗】的目标", test_mode=(game.current_phase == "test"))
        
        # 先询问所有玩家是否使用无懈可击
        if not self.handle_response(game, player, target, test_mode=(game.current_phase == "test")):
            # 如果被无懈可击抵消，则不生效
            return False
        
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
        if target is None:
            target = game.get_opponent(player)
        print(f"{target.character.name} 没有杀可以响应南蛮入侵，受到1点伤害。")
        target.character.hp -= 1
        return True
    
    def apply_effect(self, game, player, target=None):
        # 南蛮入侵是群体锦囊牌，对除了使用者以外的所有角色生效
        print(f"{player.character.name} 使用了南蛮入侵，所有其他角色需要打出一张杀，否则受到1点伤害。")
        
        # 先询问所有玩家是否使用无懈可击
        if not self.handle_response(game, player, None, test_mode=(game.current_phase == "test")):
            # 如果被无懈可击抵消，则不生效
            return False
        
        # 对每个其他玩家进行处理
        for p in game.players:
            if p != player:  # 不包括使用者自己
                print(f"处理 {p.character.name} 对南蛮入侵的响应...")
                # 检查是否有杀
                has_sha = any(c.name == "杀" for c in p.hand_cards)
                if has_sha:
                    # 让玩家选择是否使用杀
                    use_sha = self.ask_for_response(game, p, ["杀"], test_mode=(game.current_phase == "test"))
                    if use_sha:
                        # 处理响应
                        self.process_response(game, player, p, use_sha)
                    else:
                        # 不使用杀，受到伤害
                        self.apply_default_effect(game, player, p)
                else:
                    # 没有杀，受到伤害
                    self.apply_default_effect(game, player, p)
        
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
        if target is None:
            target = game.get_opponent(player)
        print(f"{target.character.name} 没有闪可以响应万箭齐发，受到1点伤害。")
        target.character.hp -= 1
        return True
    
    def apply_effect(self, game, player, target=None):
        # 万箭齐发是群体锦囊牌，对除了使用者以外的所有角色生效
        print(f"{player.character.name} 使用了万箭齐发，所有其他角色需要打出一张闪，否则受到1点伤害。")
        
        # 先询问所有玩家是否使用无懈可击
        if not self.handle_response(game, player, None, test_mode=(game.current_phase == "test")):
            # 如果被无懈可击抵消，则不生效
            return False
        
        # 对每个其他玩家进行处理
        for p in game.players:
            if p != player:  # 不包括使用者自己
                print(f"处理 {p.character.name} 对万箭齐发的响应...")
                # 检查是否有闪
                has_shan = any(c.name == "闪" for c in p.hand_cards)
                if has_shan:
                    # 让玩家选择是否使用闪
                    use_shan = self.ask_for_response(game, p, ["闪"], test_mode=(game.current_phase == "test"))
                    if use_shan:
                        # 处理响应
                        self.process_response(game, player, p, use_shan)
                    else:
                        # 不使用闪，受到伤害
                        self.apply_default_effect(game, player, p)
                else:
                    # 没有闪，受到伤害
                    self.apply_default_effect(game, player, p)
        
        return True
    
    def apply_effect(self, game, player, target=None):
        # 万箭齐发的效果在handle_response中处理
        return True


class JieDaoShaRenAction(CardAction):
    def __init__(self):
        super().__init__("借刀杀人", "trick", "令一名装备武器的角色对其攻击范围内的另一名角色使用一张杀")
    
    def apply_effect(self, game, player, target=None):
        """借刀杀人的效果：选择一名装备武器的角色，令其对攻击范围内的另一名角色使用杀"""
        
        # 先询问所有玩家是否使用无懈可击
        if not self.handle_response(game, player, target, test_mode=(game.current_phase == "test")):
            # 如果被无懈可击抵消，则不生效
            return False
        
        # 选择装备武器的目标角色
        weapon_players = []
        for p in game.players:
            if p != player and p.weapon:  # 不能选择自己，且必须装备武器
                weapon_players.append(p)
        
        if not weapon_players:
            print("场上没有装备武器的其他角色，借刀杀人无效。")
            return False
        
        # 选择装备武器的角色
        if target is None:
            if len(weapon_players) == 1:
                weapon_holder = weapon_players[0]
            else:
                print("选择一名装备武器的角色：")
                for i, p in enumerate(weapon_players):
                    print(f"{i+1}. {p.character.name} (武器: {p.weapon.name})")
                
                test_mode = (game.current_phase == "test")
                if test_mode:
                    # 测试模式下自动选择第一个
                    weapon_holder = weapon_players[0]
                else:
                    try:
                        choice = input("请选择: ")
                        choice_idx = int(choice) - 1
                        if 0 <= choice_idx < len(weapon_players):
                            weapon_holder = weapon_players[choice_idx]
                        else:
                            print("无效选择，借刀杀人失败。")
                            return False
                    except (ValueError, EOFError):
                        print("输入无效，借刀杀人失败。")
                        return False
        else:
            weapon_holder = target
        
        # 检查武器持有者是否真的装备了武器
        if not weapon_holder.weapon:
            print(f"{weapon_holder.character.name} 没有装备武器，借刀杀人无效。")
            return False
        
        # 找到武器持有者攻击范围内的其他角色
        attack_targets = []
        for p in game.players:
            if p != weapon_holder and p != player:  # 不能攻击自己和借刀杀人的使用者
                if weapon_holder.can_attack(p, game.players):  # 传入all_players参数
                    attack_targets.append(p)
        
        if not attack_targets:
            print(f"{weapon_holder.character.name} 的攻击范围内没有其他角色，借刀杀人无效。")
            return False
        
        # 选择攻击目标
        if len(attack_targets) == 1:
            attack_target = attack_targets[0]
        else:
            print(f"选择 {weapon_holder.character.name} 要攻击的目标：")
            for i, p in enumerate(attack_targets):
                print(f"{i+1}. {p.character.name}")
            
            test_mode = (game.current_phase == "test")
            if test_mode:
                # 测试模式下自动选择第一个
                attack_target = attack_targets[0]
            else:
                try:
                    choice = input("请选择攻击目标: ")
                    choice_idx = int(choice) - 1
                    if 0 <= choice_idx < len(attack_targets):
                        attack_target = attack_targets[choice_idx]
                    else:
                        print("无效选择，借刀杀人失败。")
                        return False
                except (ValueError, EOFError):
                    print("输入无效，借刀杀人失败。")
                    return False
        
        print(f"{player.character.name} 使用借刀杀人，令 {weapon_holder.character.name} 对 {attack_target.character.name} 使用杀。")
        
        # 检查武器持有者是否有杀
        sha_cards = [c for c in weapon_holder.hand_cards if c.name == "杀"]
        if sha_cards:
            # 武器持有者必须使用杀
            sha_card = sha_cards[0]  # 使用第一张杀
            weapon_holder.hand_cards.remove(sha_card)
            
            print(f"{weapon_holder.character.name} 被迫使用杀对 {attack_target.character.name}。")
            
            # 创建杀的动作并执行
            sha_action = ShaAction()
            # 直接调用apply_default_effect来造成伤害，跳过响应阶段
            result = sha_action.apply_default_effect(game, weapon_holder, attack_target)
            
            # 将使用的杀放入弃牌堆
            game.discard_pile.append(sha_card)
            print(f"卡牌 {sha_card.name} 进入弃牌堆")
            
            return result
        else:
            # 武器持有者没有杀，需要交出武器给借刀杀人的使用者
            print(f"{weapon_holder.character.name} 没有杀，必须将武器 {weapon_holder.weapon.name} 交给 {player.character.name}。")
            
            # 移除武器持有者的武器
            weapon = weapon_holder.weapon
            weapon_holder.equipped.remove(weapon)
            weapon_holder.weapon = None
            
            # 将武器给借刀杀人的使用者
            player.equipped.append(weapon)
            player.weapon = weapon
            
            print(f"{player.character.name} 获得了 {weapon.name}。")
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
        "借刀杀人": JieDaoShaRenAction,
    }
    
    action_class = action_map.get(card.name)
    if action_class:
        return action_class()
    else:
        return DefaultAction(card.name)