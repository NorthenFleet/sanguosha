"""
三国杀1v1游戏核心框架
"""
from enum import Enum
from typing import List, Dict, Optional
import random
from app.models.skills import SkillManager, PaoXiao, KeJi, YingZi

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

class Player:
    """玩家类"""
    def __init__(self, character):
        self.character = character
        self.hand_cards = []
        self.weapon = None  # 添加武器属性，默认为 None
        self.chained = False  # 添加铁锁连环状态，默认为 False
        self.has_used_sha = False  # 添加是否使用过杀的标记，默认为 False

    def draw_card(self, deck, num: int = 1):
        """摸牌"""
        for _ in range(num):
            if deck:
                self.hand_cards.append(deck.pop())

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
        self.deck: List[Card] = []
        self.current_player_index = 0
        self.current_phase = "准备阶段"
        self.phase = "准备阶段"

    def initialize_deck(self):
        """初始化牌堆"""
        # 基本牌
        for _ in range(30):
            self.deck.append(Card("杀", CardType.BASIC, random.choice(["♥", "♦", "♠", "♣"]), random.randint(1, 13)))
        for _ in range(15):
            self.deck.append(Card("闪", CardType.BASIC, random.choice(["♥", "♦"]), random.randint(1, 13)))
        for _ in range(8):
            self.deck.append(Card("桃", CardType.BASIC, random.choice(["♥", "♦"]), random.randint(1, 13)))
        
        # 锦囊牌
        trick_cards = ["过河拆桥", "顺手牵羊", "无中生有", "决斗", "南蛮入侵", "万箭齐发"]
        for card_name in trick_cards:
            for _ in range(4):
                self.deck.append(Card(card_name, CardType.TRICK, random.choice(["♥", "♦", "♠", "♣"]), random.randint(1, 13)))
        
        # 洗牌
        random.shuffle(self.deck)

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
                
                card = player.hand_cards.pop(0)
                print(f"\n{player.character.name} 使用了手牌: {card}")
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
                            
                            card = player.hand_cards.pop(choice)
                            print(f"\n{player.character.name} 使用了手牌: {card}")
                            self.handle_response(player, card)
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
        opponent = self.get_opponent(player)
        print(f"{opponent.character.name} 需要响应 {card}...")
        
        if card.name == "杀":
            shan_card_index = -1
            for i, c in enumerate(opponent.hand_cards):
                if c.name == "闪":
                    shan_card_index = i
                    break
            
            if shan_card_index != -1:
                # 在测试模式下自动使用闪
                use_shan = 'y' if test_mode else input(f"{opponent.character.name} 是否使用闪? (y/n): ")
                if use_shan.lower() == 'y':
                    shan_card = opponent.hand_cards.pop(shan_card_index)
                    print(f"{opponent.character.name} 使用了 {shan_card}，成功闪避攻击。")
                else:
                    opponent.character.hp -= 1
                    print(f"{opponent.character.name} 未能闪避，失去1点血量。")
                    if opponent.character.hp <= 0:
                        print(f"{opponent.character.name} 已死亡！")
            else:
                opponent.character.hp -= 1
                print(f"{opponent.character.name} 未能闪避，失去1点血量。")
                if opponent.character.hp <= 0:
                    print(f"{opponent.character.name} 已死亡！")
        elif card.name == "桃":
            # 使用桃回复体力
            if player.character.hp < player.character.max_hp:
                player.character.hp += 1
                print(f"{player.character.name} 使用了 {card}，回复1点血量。")
            else:
                print(f"{player.character.name} 体力已满，无法使用 {card}。")
        else:
            print(f"{card} 无需响应。")

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
            if self.deck:
                card = self.deck.pop()
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
        return any(player.character.hp <= 0 for player in self.players) or not self.deck

    def get_opponent(self, player):
        """获取对手玩家。"""
        return self.players[1] if self.players[0] == player else self.players[0]

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