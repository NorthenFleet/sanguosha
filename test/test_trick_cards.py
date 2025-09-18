import sys
sys.path.append('.')

from app.models.player import Player
from app.models.character import Character
from app.models.card import Card
from app.models.enums import CardType

print("=== 测试锦囊牌使用功能 ===")

# 创建两个玩家进行对战测试
character1 = Character("关羽", "蜀", 4, ["武圣"])
character2 = Character("曹操", "魏", 4, ["奸雄"])
player1 = Player(character1)
player2 = Player(character2)

# 创建锦囊牌
wugu_card = Card(name="五谷丰登", type=CardType.TRICK, category="trick", suit="红桃", rank=3)
nanman_card = Card(name="南蛮入侵", type=CardType.TRICK, category="trick", suit="梅花", rank=7)
wanjian_card = Card(name="万箭齐发", type=CardType.TRICK, category="trick", suit="红桃", rank=1)
wuzhong_card = Card(name="无中生有", type=CardType.TRICK, category="trick", suit="红桃", rank=7)
shunshou_card = Card(name="顺手牵羊", type=CardType.TRICK, category="trick", suit="方片", rank=3)

print(f"创建的锦囊牌:")
print(f"五谷丰登 - type: {wugu_card.type}, category: {wugu_card.category}")
print(f"南蛮入侵 - type: {nanman_card.type}, category: {nanman_card.category}")
print(f"万箭齐发 - type: {wanjian_card.type}, category: {wanjian_card.category}")
print(f"无中生有 - type: {wuzhong_card.type}, category: {wuzhong_card.category}")
print(f"顺手牵羊 - type: {shunshou_card.type}, category: {shunshou_card.category}")

# 测试1: 无中生有的使用
print(f"\n=== 测试无中生有的使用 ===")
player1.hand_cards = [wuzhong_card]
print(f"玩家1初始手牌: {len(player1.hand_cards)}")

print(f"玩家1使用无中生有...")
player1.use_card(wuzhong_card)
print(f"使用后手牌数量: {len(player1.hand_cards)}")

# 测试2: 五谷丰登的使用
print(f"\n=== 测试五谷丰登的使用 ===")
player1.hand_cards = [wugu_card]
print(f"玩家1初始手牌: {len(player1.hand_cards)}")

print(f"玩家1使用五谷丰登...")
player1.use_card(wugu_card)
print(f"使用后手牌数量: {len(player1.hand_cards)}")

# 测试3: 南蛮入侵的使用
print(f"\n=== 测试南蛮入侵的使用 ===")
player1.hand_cards = [nanman_card]
print(f"玩家1初始手牌: {len(player1.hand_cards)}")

print(f"玩家1使用南蛮入侵...")
player1.use_card(nanman_card)
print(f"使用后手牌数量: {len(player1.hand_cards)}")

# 测试4: 万箭齐发的使用
print(f"\n=== 测试万箭齐发的使用 ===")
player1.hand_cards = [wanjian_card]
print(f"玩家1初始手牌: {len(player1.hand_cards)}")

print(f"玩家1使用万箭齐发...")
player1.use_card(wanjian_card)
print(f"使用后手牌数量: {len(player1.hand_cards)}")

# 测试5: 顺手牵羊的使用
print(f"\n=== 测试顺手牵羊的使用 ===")
player1.hand_cards = [shunshou_card]
player2.hand_cards = [Card(name="杀", type=CardType.BASIC, category="basic", suit="黑桃", rank=5)]
print(f"玩家1初始手牌: {len(player1.hand_cards)}")
print(f"玩家2初始手牌: {len(player2.hand_cards)}")

print(f"玩家1使用顺手牵羊...")
player1.use_card(shunshou_card)
print(f"使用后玩家1手牌数量: {len(player1.hand_cards)}")
print(f"使用后玩家2手牌数量: {len(player2.hand_cards)}")

# 测试6: 检查锦囊牌的判断方法
print(f"\n=== 测试锦囊牌判断方法 ===")
new_trick = Card(name="决斗", type=CardType.TRICK, category="trick", suit="黑桃", rank=1)
print(f"决斗牌是否为基本牌: {new_trick.is_basic_card()}")
print(f"决斗牌是否为装备牌: {new_trick.is_equipment_card()}")
print(f"决斗牌是否为锦囊牌: {new_trick.is_trick_card()}")

print(f"\n锦囊牌测试完成!")