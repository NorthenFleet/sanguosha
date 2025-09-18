import sys
sys.path.append('.')

from app.models.player import Player
from app.models.character import Character
from app.models.card import Card
from app.models.enums import CardType

print("=== 测试卡牌使用后的状态更新 ===")

# 创建玩家
character = Character("关羽", "蜀", 4, ["武圣"])
player = Player(character)

# 创建各种类型的卡牌
sha_card = Card(name="杀", type=CardType.BASIC, category="basic", suit="红桃", rank=7)
tao_card = Card(name="桃", type=CardType.BASIC, category="basic", suit="红桃", rank=3)
weapon_card = Card(name="青龙偃月刀", type=CardType.EQUIP, category="equipment", suit="黑桃", rank=5)
wuzhong_card = Card(name="无中生有", type=CardType.TRICK, category="trick", suit="红桃", rank=7)

print(f"初始状态:")
print(f"玩家血量: {player.hp}/{player.character.max_hp}")
print(f"手牌数量: {len(player.hand_cards)}")
print(f"装备区: 武器={player.weapon}, 防具={player.defense}")
print(f"装备列表: {player.equipped}")

# 测试1: 使用桃回血的状态更新
print(f"\n=== 测试桃的状态更新 ===")
player.hp = 2  # 模拟受伤
player.hand_cards = [tao_card]
print(f"受伤后血量: {player.hp}/{player.character.max_hp}")
print(f"使用桃前手牌: {len(player.hand_cards)}")

player.use_card(tao_card)
print(f"使用桃后血量: {player.hp}/{player.character.max_hp}")
print(f"使用桃后手牌: {len(player.hand_cards)}")

# 测试2: 装备武器的状态更新
print(f"\n=== 测试装备武器的状态更新 ===")
player.hand_cards = [weapon_card]
print(f"装备前武器: {player.weapon}")
print(f"装备前手牌: {len(player.hand_cards)}")
print(f"装备前装备列表: {player.equipped}")

player.use_card(weapon_card)
print(f"装备后武器: {player.weapon}")
print(f"装备后手牌: {len(player.hand_cards)}")
print(f"装备后装备列表: {player.equipped}")

# 测试3: 使用杀的状态更新
print(f"\n=== 测试使用杀的状态更新 ===")
player.hand_cards = [sha_card]
print(f"使用杀前手牌: {len(player.hand_cards)}")

player.use_card(sha_card)
print(f"使用杀后手牌: {len(player.hand_cards)}")

# 测试4: 使用锦囊牌的状态更新
print(f"\n=== 测试使用锦囊牌的状态更新 ===")
player.hand_cards = [wuzhong_card]
print(f"使用无中生有前手牌: {len(player.hand_cards)}")

player.use_card(wuzhong_card)
print(f"使用无中生有后手牌: {len(player.hand_cards)}")

# 测试5: 连续使用多张牌的状态更新
print(f"\n=== 测试连续使用多张牌的状态更新 ===")
sha_card2 = Card(name="杀", type=CardType.BASIC, category="basic", suit="黑桃", rank=5)
tao_card2 = Card(name="桃", type=CardType.BASIC, category="basic", suit="方片", rank=4)
player.hand_cards = [sha_card2, tao_card2]
player.hp = 3  # 模拟受伤状态

print(f"初始状态: 血量={player.hp}, 手牌={len(player.hand_cards)}")

# 使用杀
player.use_card(sha_card2)
print(f"使用杀后: 血量={player.hp}, 手牌={len(player.hand_cards)}")

# 使用桃
player.use_card(tao_card2)
print(f"使用桃后: 血量={player.hp}, 手牌={len(player.hand_cards)}")

# 测试6: 验证卡牌确实从手牌中移除
print(f"\n=== 验证卡牌移除 ===")
test_card = Card(name="闪", type=CardType.BASIC, category="basic", suit="方片", rank=2)
player.hand_cards = [test_card]
print(f"添加闪牌前手牌内容: {[str(card) for card in player.hand_cards]}")

player.use_card(test_card)
print(f"使用闪牌后手牌内容: {[str(card) for card in player.hand_cards]}")
print(f"闪牌是否还在手牌中: {test_card in player.hand_cards}")

print(f"\n卡牌状态更新测试完成!")