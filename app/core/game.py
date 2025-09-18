"""
三国杀1v1游戏核心框架
"""
from enum import Enum
from typing import List, Dict, Optional
import random
from app.models.skills import SkillManager, PaoXiao, KeJi, YingZi, JianXiong
from app.models.card import Deck, Card
from app.models.action import CardAction, SkillAction
from app.models.player import Player
from app.models.enums import CardType
from app.models.card_actions import create_card_action
from app.models.character import Character

class Game:
    """三国杀1v1游戏逻辑模块"""
    def __init__(self, event_manager):
        self.players: List[Player] = []
        self.deck: Deck = Deck()
        self.discard_pile: List = []  # 弃牌堆
        self.current_player_index = 0
        self.current_phase = "准备阶段"
        self.phase = "准备阶段"
        self.current_player = None  # 添加当前玩家属性
        self.skill_manager = SkillManager()
        self.event_manager = event_manager
        # 注册技能
        self.skill_manager.register_skill(JianXiong())
        self.skill_manager.register_skill(PaoXiao())
        self.skill_manager.register_skill(KeJi())
        self.skill_manager.register_skill(YingZi())

    def initialize_deck(self):
        """初始化牌堆"""
        # 重新初始化牌堆
        self.deck = Deck("app/data/cards.json")
        if not self.deck.cards:
            print("错误: 卡牌数据加载失败，请检查 cards.json 文件内容。")
            return

    def add_player(self, player_or_character):
        """添加玩家"""
        if len(self.players) < 2:
            if isinstance(player_or_character, Player):
                self.players.append(player_or_character)
            else:
                # 兼容旧的 Character 参数
                self.players.append(Player(player_or_character))
            return True
        return False

    def start_game(self):
        """开始游戏"""
        if len(self.players) != 2:
            print("需要2名玩家才能开始游戏")
            return
        
        # 触发游戏开始事件
        self.event_manager.trigger("game_start", {"players": self.players})
        
        self.initialize_deck()
        
        # 初始摸牌
        for player in self.players:
            drawn_cards = self.deck.draw(4)
            player.hand_cards.extend(drawn_cards)
            # 触发摸牌事件
            self.event_manager.trigger("draw_card", {"player": player, "count": 4})
        
        print("游戏开始!")
        self.game_loop()

    def game_loop(self):
        """游戏主循环"""
        print("游戏主循环开始...")
        # 设置当前玩家
        self.current_player = self.players[self.current_player_index]

    def judgment_phase(self):
        """判定阶段: 检查是否有负面效果并处理。"""
        self.current_phase = "judgment"
        # 触发阶段变化事件
        self.event_manager.trigger("phase_change", {"phase": "judgment", "player": self.current_player})
        
        print("判定阶段: 检查负面效果...")
        # 示例逻辑: 随机决定是否有负面效果
        if random.choice([True, False]):
            print("负面效果触发!")
        else:
            print("无负面效果。")

    def show_player_status(self, player):
        print(f"  - {player.character.name}: 血量: {player.hp}, 手牌数: {len(player.hand_cards)}, 武器: {player.weapon if player.weapon else '无'}, 铁索连环: {'是' if player.chained else '否'}")
        print("    装备:")
        print(f"      武器牌: {player.weapon if player.weapon else '无'}")
        print(f"      防御牌: {player.defense if player.defense else '无'}")
        print(f"      进攻马: {player.attack_horse if player.attack_horse else '无'}")
        print(f"      防御马: {player.defense_horse if player.defense_horse else '无'}")
        if player.equipped:
            print("    装备:")
            for equip in player.equipped:
                print(f"      - {equip}")
        else:
            print("    装备: 无")

    def play_phase(self, player, test_mode=False):
        """出牌阶段: 玩家选择使用手牌，并处理响应逻辑。"""
        self.current_phase = "play"
        self.current_player = player
        # 触发阶段变化事件
        self.event_manager.trigger("phase_change", {"phase": "play", "player": player})
        
        print(f"\n{player.character.name} 的出牌阶段...")
        has_used_kill = False  # 标记是否已使用过"杀"
        # 检查是否有咆哮技能，允许多次使用杀
        if player.character.has_skill("咆哮"):
            print(f"{player.character.name} 有技能【咆哮】，可以多次使用杀")
            # 触发咆哮技能
            if hasattr(player.character, 'use_skill'):
                player.character.use_skill("咆哮", self, player)
                # 触发使用技能事件
                self.event_manager.trigger("use_skill", {"player": player, "skill": "咆哮"})
        
        # 在测试模式下自动选择手牌
        if test_mode:
            # 自动使用第一张手牌
            if player.hand_cards:
                card = player.hand_cards[0]
                
                # 检查是否有咆哮技能
                has_paoxiao = player.character.has_skill("咆哮")
                
                # 检查是否可以使用"杀"
                if card.name == "杀":
                    if has_used_kill and not has_paoxiao:
                        print("本回合已使用过\"杀\"，无法再次使用。")
                    else:
                        has_used_kill = True
                        player.has_used_sha = True
                
                # 触发咆哮技能
                if has_paoxiao:
                    player.character.use_skill("咆哮", self, player)
                
                card = player.hand_cards.pop(0)
                print(f"\n{player.character.name} 使用了手牌: {card}")
                # 处理响应
                card_action = self.create_card_action(card)
                card_action.handle_response(self, player, test_mode=True)
                
                # 卡牌使用完成后，如果不是装备牌且没有停留在场上，则进入弃牌堆
                if card.type and card.type.value != "装备牌":
                    self.deck.discard(card)
                    print(f"卡牌 {card.name} 进入弃牌堆")
        else:
            while True:
                print("\n当前场上状态:")
                for p in self.players:
                    self.show_player_status(p)

                if player.hand_cards:
                    print("\n你的手牌:")
                    for idx, card in enumerate(player.hand_cards, start=1):
                        type_display = card.type.value if card.type else "unknown"
                        print(f"{idx}. {card.name}({type_display}) - {card.suit}[{card.rank}]")

                    print("\n当前牌堆信息:")
                    print(f"摸牌堆卡牌数量: {len(self.deck.cards)}")
                    print(f"弃牌堆卡牌数量: {len(self.deck.discard_pile)}")
                    try:
                        user_input = input("选择要使用的手牌编号 (输入0结束出牌阶段): ")
                        if not user_input.strip():
                            print("输入不能为空，请重新选择。")
                            continue
                        choice = user_input
                        if choice == "0":
                            break
                        choice = int(choice) - 1
                        if 0 <= choice < len(player.hand_cards):
                            card = player.hand_cards[choice]
                            
                            # 检查是否可以使用"杀"
                            has_paoxiao = False
                            if card.name == "杀":
                                # 检查是否有咆哮技能
                                has_paoxiao = player.character.has_skill("咆哮")
                                if has_used_kill and not has_paoxiao:
                                    print("本回合已使用过\"杀\"，无法再次使用。")
                                    continue
                                has_used_kill = True
                                player.has_used_sha = True
                            
                            # 触发咆哮技能
                            if has_paoxiao:
                                player.character.use_skill("咆哮", self, player)
                            
                            card = player.hand_cards[choice]
                            print(f"\n{player.character.name} 使用了手牌: {card}")
                            # 如果是装备牌，更新装备状态
                            if card.type and card.type.value == "装备牌":
                                player.use_card(card)
                            else:
                                # 对于非装备牌，直接从手牌中移除
                                player.hand_cards.pop(choice)
                            # 触发使用卡牌事件
                            self.event_manager.trigger("play_card", {"player": player, "card": card, "target": self.get_opponent(player)})
                            # 处理响应 - 这会自动切换到对手的回合进行响应
                            card_action = self.create_card_action(card)
                            response_result = card_action.handle_response(self, player, test_mode=False)
                            
                            # 卡牌使用完成后，如果不是装备牌且没有停留在场上，则进入弃牌堆
                            if card.type and card.type.value != "装备牌":
                                self.deck.discard(card)
                                print(f"卡牌 {card.name} 进入弃牌堆")
                            
                            # 如果是无中生有被无懈可击响应，继续出牌阶段
                            if response_result == "continue_play_phase":
                                card_action = self.create_card_action(card)
                                card_action.handle_response(self, player, test_mode=False)
                        else:
                            print("选择无效，请重新选择。")
                    except ValueError:
                        print("输入无效，请重新选择。")
                    except (EOFError, KeyboardInterrupt):
                        print("\n游戏被中断。")
                        return
                else:
                    print("没有手牌可用。")
                    break

    def handle_response(self, player, card, test_mode=False):
        """处理出牌响应逻辑。"""
        # 创建卡牌动作实例
        card_action = self.create_card_action(card)
        
        # 如果是桃，直接应用效果，不需要响应
        if card.name == "桃":
            return card_action.apply_effect(self, player)
        
        # 处理响应
        result = card_action.handle_response(self, player, test_mode=test_mode)
        
        # 杀牌的伤害已经在apply_default_effect中处理，这里不需要重复处理
        
        # 如果是无中生有、过河拆桥或顺手牵羊且被无懈可击响应，返回特殊标志让出牌阶段继续
        if (card.name == "无中生有" or card.name == "过河拆桥" or card.name == "顺手牵羊") and result == False:
            return "continue_play_phase"
        
        return result
    
    def create_card_action(self, card):
        """根据卡牌创建对应的动作实例"""
        return create_card_action(card)

    def discard_phase(self, player, test_mode=False):
        """弃牌阶段: 玩家弃置多余手牌。"""
        self.current_phase = "discard"
        self.current_player = player
        # 触发阶段变化事件
        self.event_manager.trigger("phase_change", {"phase": "discard", "player": player})
        
        print(f"{player.character.name} 的弃牌阶段...")
        # 检查是否有克己技能
        if player.character.has_skill("克己") and player.has_used_sha:
            print(f"{player.character.name} 有技能【克己】，且本回合使用过杀，跳过弃牌阶段")
            # 触发克己技能
            if hasattr(player.character, 'use_skill'):
                player.character.use_skill("克己", self, player)
                # 触发使用技能事件
                self.event_manager.trigger("use_skill", {"player": player, "skill": "克己"})
            return
        else:
            # 在测试模式下自动弃牌
            if test_mode:
                while len(player.hand_cards) > player.character.hp:
                    if player.hand_cards:
                        discarded_card = player.hand_cards.pop()
                        self.deck.discard(discarded_card)
                        print(f"{player.character.name} 弃置了 {discarded_card.name}，进入弃牌堆")
                        # 触发弃牌事件
                        self.event_manager.trigger("discard_card", {"player": player, "card": discarded_card})
            else:
                # 弃牌直到手牌数等于血量
                while len(player.hand_cards) > player.character.hp:
                    print(f"\n{player.character.name} 的手牌:")
                    for i, card in enumerate(player.hand_cards):
                        type_display = card.type.value if card.type else "unknown"
                        print(f"{i+1}. {card.name}({type_display})")
                    try:
                        user_input = input("选择要弃置的手牌编号: ")
                        if not user_input.strip():
                            print("输入不能为空，请重新选择。")
                            continue
                        choice = int(user_input) - 1
                        if 0 <= choice < len(player.hand_cards):
                            discarded_card = player.hand_cards.pop(choice)
                            self.deck.discard(discarded_card)
                            print(f"{player.character.name} 弃置了 {discarded_card.name}，进入弃牌堆")
                            # 触发弃牌事件
                            self.event_manager.trigger("discard_card", {"player": player, "card": discarded_card})
                        else:
                            print("无效的选择，请重新选择。")
                    except (ValueError, EOFError, KeyboardInterrupt):
                        print("请输入有效的数字。")

    def draw_phase(self, player):
        """摸牌阶段: 玩家从牌堆中摸牌。"""
        self.current_phase = "draw"
        self.current_player = player
        # 触发阶段变化事件
        self.event_manager.trigger("phase_change", {"phase": "draw", "player": player})
        
        # 重置玩家使用杀的标记
        player.has_used_sha = False
        print(f"{player.character.name} 的摸牌阶段...")
        # 检查是否有英姿技能
        if player.character.has_skill("英姿"):
            print(f"{player.character.name} 有技能【英姿】，可以多摸一张牌")
            # 触发英姿技能
            if hasattr(player.character, 'use_skill'):
                player.character.use_skill("英姿", self, player)
                # 触发使用技能事件
                self.event_manager.trigger("use_skill", {"player": player, "skill": "英姿"})
        
        # 正常摸牌逻辑
        draw_count = 2
        for _ in range(draw_count):
            card = self.deck.draw_card()
            if card:
                player.hand_cards.append(card)
                print(f"摸到手牌: {card}")
            else:
                print("牌堆已空")
        
        # 触发摸牌事件
        self.event_manager.trigger("draw_card", {"player": player, "count": draw_count})

    def game_loop(self, test_mode=False):
        """游戏主循环: 包括判定、摸牌、出牌、弃牌阶段。"""
        # 设置当前玩家
        self.current_player = self.players[self.current_player_index]
        
        while not self.is_game_over():
            for i, player in enumerate(self.players):
                # 更新当前玩家
                self.current_player_index = i
                self.current_player = player
                
                print(f"\n=== {player.character.name} 的回合 ===")
                self.judgment_phase()
                self.draw_phase(player)
                self.play_phase(player, test_mode=test_mode)
                self.discard_phase(player, test_mode=test_mode)
                
                # 检查游戏是否结束
                if self.is_game_over():
                    self.end_game()
                    break
                    
    def end_game(self):
        """处理游戏结束逻辑"""
        print("\n=== 游戏结束 ===")
        winner = self.get_winner()
        
        if winner:
            print(f"胜利者: {winner.character.name}")
            print(f"剩余血量: {winner.character.hp}")
        else:
            print("游戏平局！")
            
        # 显示游戏统计信息
        print("\n游戏统计:")
        for player in self.players:
            print(f"{player.character.name}: 剩余血量 {player.character.hp}, 剩余手牌 {len(player.hand_cards)}")
            
        # 触发游戏结束事件
        self.event_manager.trigger("game_end", {"winner": winner, "players": self.players})

    def is_game_over(self):
        """检查游戏是否结束。"""
        # 如果任意玩家的角色血量为0或牌堆为空，则游戏结束
        return any(player.character.hp <= 0 for player in self.players) or self.deck.is_empty()
        
    def get_winner(self):
        """获取游戏胜利者。"""
        if not self.is_game_over():
            return None
            
        # 如果有玩家血量为0，另一个玩家获胜
        for i, player in enumerate(self.players):
            if player.character.hp <= 0:
                return self.players[1-i]  # 返回另一个玩家
                
        # 如果牌堆为空，血量较高的玩家获胜
        if self.deck.is_empty():
            if self.players[0].character.hp > self.players[1].character.hp:
                return self.players[0]
            elif self.players[1].character.hp > self.players[0].character.hp:
                return self.players[1]
            else:
                return None  # 平局
                
        return None  # 未知情况

    def get_opponent(self, player):
        """获取对手玩家。"""
        return self.players[1] if self.players[0] == player else self.players[0]
        
    def select_target(self, player, prompt="选择目标玩家", test_mode=False):
        """选择目标玩家"""
        if len(self.players) <= 2:
            # 在1v1模式下，直接返回对手
            return self.get_opponent(player)
        
        # 在多人模式下，让玩家选择目标
        if test_mode:
            # 测试模式下自动选择第一个不是自己的玩家
            for p in self.players:
                if p != player:
                    return p
        else:
            print(prompt)
            for i, p in enumerate(self.players):
                if p != player:  # 不能选择自己
                    print(f"{i+1}. {p.character.name}")
            
            try:
                user_input = input("请选择目标玩家编号: ")
                if not user_input.strip():
                    print("输入不能为空，请重新选择。")
                    return self.select_target(player, prompt, test_mode)
                choice = int(user_input) - 1
                if 0 <= choice < len(self.players) and self.players[choice] != player:
                    return self.players[choice]
                else:
                    print("无效的选择，请重新选择。")
                    return self.select_target(player, prompt, test_mode)
            except (ValueError, EOFError, KeyboardInterrupt):
                print("输入无效或游戏被中断。")
                return self.select_target(player, prompt, test_mode)
        
        return None
    
    def handle_damage(self, player, damage, damage_card=None):
        """处理玩家受到的伤害。"""
        # 触发伤害事件
        self.event_manager.trigger("take_damage", {"player": player, "damage": damage, "damage_card": damage_card})
        
        player.character.hp -= damage
        print(f"{player.character.name} 受到 {damage} 点伤害，剩余血量: {player.character.hp}")
        
        # 检查是否有奸雄技能
        if player.character.has_skill("奸雄") and damage_card:
            # 触发奸雄技能
            self.skill_manager.trigger_skill("奸雄", self, player, damage_card=damage_card)
        
        # 检查角色是否死亡
        if player.character.hp <= 0:
            print(f"{player.character.name} 已死亡！")
            # 触发角色死亡事件
            self.event_manager.trigger("player_death", {"player": player})
            # 检查游戏是否结束
            if self.is_game_over():
                self.end_game()
            return True
        return False

# 示例用法
if __name__ == "__main__":
    # 创建武将
    caocao = Character("曹操", "魏", 4, ["奸雄"])
    liubei = Character("刘备", "蜀", 4, ["仁德"])

    # 初始化游戏
    game = Game()
    game.add_player(caocao)
    game.add_player(liubei)

    # 开始游戏
    game.start_game()