import sys
sys.path.append('.')

from app.models.player import Player
from app.models.character import Character
from app.models.card import Card
from app.models.enums import CardType

print("=== 测试基本牌使用功能 ===")

# 创建两个玩家进行对战测试
character1 = Character("关羽", "蜀", 4, ["武圣"])
character2 = Character("曹操", "魏", 4, ["奸雄"])
player1 = Player(character1)
player2 = Player(character2)

# 创建基本牌
sha_card = Card(name="杀", type=CardType.BASIC, category="basic", suit="红桃", rank=7)
shan_card = Card(name="闪", type=CardType.BASIC, category="basic", suit="方片", rank=2)
tao_card = Card(name="桃", type=CardType.BASIC, category="basic", suit="红桃", rank=3)

print(f"创建的基本牌:")
print(f"杀 - type: {sha_card.type}, category: {sha_card.category}")
print(f"闪 - type: {shan_card.type}, category: {shan_card.category}")
print(f"桃 - type: {tao_card.type}, category: {tao_card.category}")

# 测试1: 杀的使用
print(f"\n=== 测试杀的使用 ===")
player1.hand_cards = [sha_card]
print(f"玩家1初始手牌: {len(player1.hand_cards)}")
print(f"玩家1初始血量: {player1.hp}")

print(f"玩家1使用杀...")
player1.use_card(sha_card)
print(f"使用后手牌数量: {len(player1.hand_cards)}")

# 测试2: 闪的使用
print(f"\n=== 测试闪的使用 ===")
player2.hand_cards = [shan_card]
print(f"玩家2初始手牌: {len(player2.hand_cards)}")

print(f"玩家2使用闪...")
player2.use_card(shan_card)
print(f"使用后手牌数量: {len(player2.hand_cards)}")

# 测试3: 桃的使用
print(f"\n=== 测试桃的使用 ===")
player1.hp = 2  # 模拟受伤状态
player1.hand_cards = [tao_card]
print(f"玩家1受伤血量: {player1.hp}")
print(f"玩家1手牌: {len(player1.hand_cards)}")

print(f"玩家1使用桃...")
player1.use_card(tao_card)
print(f"使用后血量: {player1.hp}")
print(f"使用后手牌数量: {len(player1.hand_cards)}")

# 测试4: 检查基本牌的判断方法
print(f"\n=== 测试基本牌判断方法 ===")
new_sha = Card(name="杀", type=CardType.BASIC, category="basic", suit="黑桃", rank=5)
print(f"新杀牌是否为基本牌: {new_sha.is_basic_card()}")
print(f"新杀牌是否为装备牌: {new_sha.is_equipment_card()}")
print(f"新杀牌是否为锦囊牌: {new_sha.is_trick_card()}")

print(f"\n基本牌测试完成!")