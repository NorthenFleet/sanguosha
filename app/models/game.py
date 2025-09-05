"""
三国杀1v1游戏核心框架
"""
from enum import Enum
from typing import List, Dict, Optional
import random
from app.models.skills import SkillManager, PaoXiao, KeJi, YingZi
from app.models.deck import Deck
from .action import CardAction, SkillAction

class CardType(Enum):
    """牌的类型"""
    BASIC = "基本牌"
    TRICK = "锦囊牌"
    EQUIP = "装备牌"

class Card:
    """牌的基类"""
    def __init__(self, name: str, card_type: CardType, suit: str, rank: int):
        self.name = name
        self.type = card_type
        self.suit = suit  # 花色
        self.rank = rank  # 点数

    def __str__(self):
        return f"{self.name}({self.type.value})"

class Character:
    """武将基类"""
    def __init__(self, name: str, kingdom: str, max_hp: int, skills: List[str]):
        self.name = name
        self.kingdom = kingdom  # 势力: 魏/蜀/吴
        self.max_hp = max_hp
        self.hp = max_hp
        self.skills = skills

    def use_skill(self, skill_name: str, target=None):
        """使用技能"""
        if skill_name in self.skills:
            print(f"{self.name} 使用了技能 {skill_name}")
            # 技能效果实现
            return True
        return False
    
    def has_skill(self, skill_name: str) -> bool:
        """检查角色是否拥有指定技能"""
        return skill_name in self.skills
    
    def get_skill(self, skill_name: str):
        """获取技能实例"""
        # 在实际实现中，这里应该返回具体的技能实例
        # 目前我们简化处理，只返回技能名称
        if self.has_skill(skill_name):
            return skill_name
        return None

class Player:
    """玩家类"""
    def __init__(self, character):
        self.character = character
        self.hand_cards = []
        self.weapon = None  # 添加武器属性，默认为 None
        self.chained = False  # 添加铁锁连环状态，默认为 False
        self.has_used_sha = False  # 添加是否使用过杀的标记，默认为 False

    def draw_card(self, deck: Deck, num: int = 1):
        """摸牌"""
        for _ in range(num):
            card = deck.draw_card()
            if card:
                self.hand_cards.append(card)

    def play_card(self, card_index: int, target=None):
        """出牌"""
        if 0 <= card_index < len(self.hand_cards):
            card = self.hand_cards.pop(card_index)
            print(f"{self.character.name} 使用了 {card}")
            return card
        return None

class Game:
    """游戏主逻辑"""
    def __init__(self):
        self.players: List[Player] = []
        self.deck: Deck = Deck()
        self.current_player_index = 0
        self.current_phase = "准备阶段"
        self.phase = "准备阶段"
        self.skill_manager = SkillManager()
        # 注册技能
        self.skill_manager.register_skill(JianXiong())
        self.skill_manager.register_skill(PaoXiao())
        self.skill_manager.register_skill(KeJi())
        self.skill_manager.register_skill(YingZi())

    def initialize_deck(self):
        """初始化牌堆"""
        # 重新初始化牌堆
        self.deck = Deck()

    def add_player(self, character: Character):
        """添加玩家"""
        if len(self.players) < 2:
            self.players.append(Player(character))
            return True
        return False

    def start_game(self):
        """开始游戏"""
        if len(self.players) != 2:
            print("需要2名玩家才能开始游戏")
            return
        
        self.initialize_deck()
        
        # 初始摸牌
        for player in self.players:
            player.draw_card(self.deck, 4)
        
        print("游戏开始!")
        self.game_loop()

    def judgment_phase(self):
        """判定阶段: 检查是否有负面效果并处理。"""
        self.current_phase = "judgment"
        print("判定阶段: 检查负面效果...")
        # 示例逻辑: 随机决定是否有负面效果
        if random.choice([True, False]):
            print("负面效果触发!")
        else:
            print("无负面效果。")

    def show_player_status(self, player):
        """显示玩家当前状态。"""
        print(f"  - {player.character.name}: 血量: {player.character.hp}, 手牌数: {len(player.hand_cards)}, 武器: {player.weapon if player.weapon else '无'}, 铁索连环: {'是' if player.chained else '否'}")

    def play_phase(self, player, test_mode=False):
        """出牌阶段: 玩家选择使用手牌，并处理响应逻辑。"""
        self.current_phase = "play"
        self.current_player = player
        print(f"\n{player.character.name} 的出牌阶段...")
        has_used_kill = False  # 标记是否已使用过"杀"
        # 检查是否有咆哮技能，允许多次使用杀
        if player.character.has_skill("咆哮"):
            print(f"{player.character.name} 有技能【咆哮】，可以多次使用杀")
            # 触发咆哮技能
            if hasattr(player.character, 'use_skill'):
                player.character.use_skill("咆哮", self, player)
        
        # 在测试模式下自动选择手牌
        if test_mode:
            # 自动使用第一张手牌
            if player.hand_cards:
                card = player.hand_cards[0]
                
                # 检查是否可以使用"杀"
                if card.name == "杀":
                    # 检查是否有咆哮技能
                    has_paoxiao = player.character.has_skill("咆哮")
                    if has_used_kill and not has_paoxiao:
                        print("本回合已使用过\"杀\"，无法再次使用。")
                    else:
                        has_used_kill = True
                        player.has_used_sha = True
                
                # 触发咆哮技能
                if has_paoxiao:
                    paoxiao_skill = player.character.get_skill("咆哮")
                    if paoxiao_skill:
                        paoxiao_skill.execute(self, player, card=card)
                
                card = player.hand_cards.pop(0)
                print(f"\n{player.character.name} 使用了手牌: {card}")
                # 处理响应
                self.handle_response(player, card, test_mode=True)
        else:
            while True:
                print("\n当前场上状态:")
                for p in self.players:
                    self.show_player_status(p)

                if player.hand_cards:
                    print("\n你的手牌:")
                    for idx, card in enumerate(player.hand_cards, start=1):
                        print(f"{idx}. {card}")
                    try:
                        choice = input("选择要使用的手牌编号 (输入0结束出牌阶段): ")
                        if choice == "0":
                            break
                        choice = int(choice) - 1
                        if 0 <= choice < len(player.hand_cards):
                            card = player.hand_cards[choice]
                            
                            # 检查是否可以使用"杀"
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
                            paoxiao_skill = player.character.get_skill("咆哮")
                            if paoxiao_skill:
                                paoxiao_skill.execute(self, player, card=card)
                            
                            card = player.hand_cards.pop(choice)
                            print(f"\n{player.character.name} 使用了手牌: {card}")
                            # 处理响应
                            self.handle_response(player, card, test_mode=False)
                        else:
                            print("选择无效，请重新选择。")
                    except ValueError:
                        print("输入无效，请重新选择。")
                    except KeyboardInterrupt:
                        print("\n游戏被中断。")
                        return
                else:
                    print("没有手牌可用。")
                    break

    def handle_response(self, player, card, test_mode=False):
        """处理出牌响应逻辑。"""
        # 创建卡牌动作实例
        card_action = self.create_card_action(card)
        
        # 处理响应
        result = card_action.handle_response(self, player)
        
        # 如果是杀牌且未被闪避，则处理伤害
        if card.name == "杀" and result:
            opponent = self.get_opponent(player)
            self.handle_damage(opponent, 1, card)
        
        return result
    
    def create_card_action(self, card):
        """根据卡牌创建对应的动作实例"""
        class ShaAction(CardAction):
            def __init__(self):
                super().__init__("杀", "basic", "对目标造成1点伤害，目标可以使用闪来抵消")
            
            def get_response_cards(self, player):
                return [c.name for c in player.hand_cards if c.name == "闪"]
            
            def process_response(self, game, player, opponent, response_card):
                print(f"{opponent.character.name} 使用了 {response_card}，成功闪避攻击。")
                # 移除使用的闪
                for i, c in enumerate(opponent.hand_cards):
                    if c.name == response_card:
                        opponent.hand_cards.pop(i)
                        break
                return False  # 攻击被抵消
            
            def apply_default_effect(self, game, player, target):
                opponent = game.get_opponent(player)
                opponent.character.hp -= 1
                print(f"{opponent.character.name} 未能闪避，失去1点血量。")
                if opponent.character.hp <= 0:
                    print(f"{opponent.character.name} 已死亡！")
                return True
        
        class TaoAction(CardAction):
            def __init__(self):
                super().__init__("桃", "basic", "回复1点体力")
            
            def apply_effect(self, game, player, target=None):
                if player.character.hp < player.character.max_hp:
                    player.character.hp += 1
                    print(f"{player.character.name} 使用了 桃，回复1点血量。")
                    return True
                else:
                    print(f"{player.character.name} 体力已满，无法使用 桃。")
                    return False
        
        class ShanAction(CardAction):
            def __init__(self):
                super().__init__("闪", "basic", "用于闪避杀")
            
            def apply_effect(self, game, player, target=None):
                print(f"{player.character.name} 使用了 闪 来闪避攻击。")
                return True
        
        class WuXieKeJiAction(CardAction):
            def __init__(self):
                super().__init__("无懈可击", "trick", "抵消一张锦囊牌的效果")
            
            def apply_effect(self, game, player, target=None):
                print(f"{player.character.name} 使用了 无懈可击 来抵消锦囊牌效果。")
                return True
        
        # 根据卡牌类型创建对应的动作实例
        if card.name == "杀":
            return ShaAction()
        elif card.name == "桃":
            return TaoAction()
        elif card.name == "闪":
            return ShanAction()
        elif card.name == "无懈可击":
            return WuXieKeJiAction()
        else:
            # 对于其他卡牌，创建一个默认的动作实例
            class DefaultAction(CardAction):
                def __init__(self, card_name):
                    super().__init__(card_name, "basic", "默认卡牌效果")
                
                def apply_effect(self, game, player, target=None):
                    print(f"{card_name} 无需响应。")
                    return True
            
            return DefaultAction(card.name)

    def discard_phase(self, player, test_mode=False):
        """弃牌阶段: 玩家弃置多余手牌。"""
        self.current_phase = "discard"
        print(f"{player.character.name} 的弃牌阶段...")
        # 检查是否有克己技能
        if player.character.has_skill("克己"):
            print(f"{player.character.name} 有技能【克己】，可以跳过弃牌阶段")
            # 触发克己技能
            if hasattr(player.character, 'use_skill'):
                player.character.use_skill("克己", self, player)
        else:
            # 在测试模式下自动弃牌
            if test_mode:
                while len(player.hand_cards) > player.character.hp:
                    if player.hand_cards:
                        discarded_card = player.hand_cards.pop()
                        print(f"{player.character.name} 弃置了 {discarded_card.name}")
            else:
                # 弃牌直到手牌数等于血量
                while len(player.hand_cards) > player.character.hp:
                    print(f"你的手牌({len(player.hand_cards)}张):")
                    for i, card in enumerate(player.hand_cards):
                        print(f"{i+1}. {card.name}({card.type.value})")
                    try:
                        choice = int(input("选择要弃置的手牌编号: ")) - 1
                        if 0 <= choice < len(player.hand_cards):
                            discarded_card = player.hand_cards.pop(choice)
                            print(f"{player.character.name} 弃置了 {discarded_card.name}")
                        else:
                            print("无效的选择，请重新选择。")
                    except ValueError:
                        print("请输入有效的数字。")

    def draw_phase(self, player):
        """摸牌阶段: 玩家从牌堆中摸牌。"""
        self.current_phase = "draw"
        self.current_player = player
        # 重置玩家使用杀的标记
        player.has_used_sha = False
        print(f"{player.character.name} 的摸牌阶段...")
        # 检查是否有英姿技能
        if player.character.has_skill("英姿"):
            print(f"{player.character.name} 有技能【英姿】，可以多摸一张牌")
            # 触发英姿技能
            if hasattr(player.character, 'use_skill'):
                player.character.use_skill("英姿", self, player)
        
        # 正常摸牌逻辑
        for _ in range(2):
            card = self.deck.draw_card()
            if card:
                player.hand_cards.append(card)
                print(f"摸到手牌: {card}")
            else:
                print("牌堆已空")

    def game_loop(self, test_mode=False):
        """游戏主循环: 包括判定、摸牌、出牌、弃牌阶段。"""
        while not self.is_game_over():
            for player in self.players:
                self.judgment_phase()
                self.draw_phase(player)
                self.play_phase(player, test_mode=test_mode)
                self.discard_phase(player, test_mode=test_mode)

    def is_game_over(self):
        """检查游戏是否结束。"""
        # 如果任意玩家的角色血量为0或牌堆为空，则游戏结束
        return any(player.character.hp <= 0 for player in self.players) or self.deck.is_empty()

    def get_opponent(self, player):
        """获取对手玩家。"""
        return self.players[1] if self.players[0] == player else self.players[0]
    
    def handle_damage(self, player, damage, damage_card=None):
        """处理玩家受到的伤害。"""
        player.character.hp -= damage
        print(f"{player.character.name} 受到 {damage} 点伤害，剩余血量: {player.character.hp}")
        
        # 检查是否有奸雄技能
        if player.character.has_skill("奸雄") and damage_card:
            # 触发奸雄技能
            self.skill_manager.trigger_skill("奸雄", self, player, damage_card=damage_card)
        
        # 检查角色是否死亡
        if player.character.hp <= 0:
            print(f"{player.character.name} 已死亡！")
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