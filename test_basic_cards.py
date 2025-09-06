#!/usr/bin/env python3
"""
测试基本牌功能：
1. 桃可以用来恢复1点血量，但不能超过血量上限
2. 杀的伤害降低到1点
"""

from app.models.game import Game, Character, Card, CardType

def test_tao_card():
    """测试桃卡牌功能"""
    print("=== 测试桃卡牌功能 ===")
    
    # 创建武将
    caocao = Character("曹操", "魏", 4, ["奸雄"])
    
    # 初始化游戏
    game = Game()
    game.add_player(caocao)
    
    # 模拟玩家
    player = game.players[0]
    
    # 测试1: 血量不满时使用桃
    player.character.hp = 3  # 设置当前血量为3
    tao_card = Card("桃", CardType.BASIC, "♥", 1)
    player.hand_cards = [tao_card]
    
    print(f"初始血量: {player.character.hp}/{player.character.max_hp}")
    
    # 使用桃
    result = player.play_card(0)
    if result:
        # 创建桃动作实例
        tao_action = game.create_card_action(result)
        tao_action.apply_effect(game, player)
    
    print(f"使用桃后血量: {player.character.hp}/{player.character.max_hp}")
    print("✓ 血量不满时使用桃成功")
    
    # 测试2: 血量已满时使用桃
    player.character.hp = 4  # 设置当前血量为满
    tao_card2 = Card("桃", CardType.BASIC, "♥", 1)
    player.hand_cards = [tao_card2]
    
    print(f"\n初始血量: {player.character.hp}/{player.character.max_hp}")
    
    # 使用桃
    result = player.play_card(0)
    if result:
        # 创建桃动作实例
        tao_action = game.create_card_action(result)
        success = tao_action.apply_effect(game, player)
        if not success:
            print("✓ 血量已满时无法使用桃")
        else:
            print("✗ 血量已满时不应该能使用桃")
    
    print(f"使用桃后血量: {player.character.hp}/{player.character.max_hp}")

def test_sha_card_damage():
    """测试杀卡牌伤害"""
    print("\n=== 测试杀卡牌伤害 ===")
    
    # 创建武将
    caocao = Character("曹操", "魏", 4, ["奸雄"])
    liubei = Character("刘备", "蜀", 4, ["仁德"])
    
    # 初始化游戏
    game = Game()
    game.add_player(caocao)
    game.add_player(liubei)
    
    # 模拟玩家
    attacker = game.players[0]  # 曹操
    defender = game.players[1]  # 刘备
    
    # 设置初始血量
    defender.character.hp = 4
    print(f"初始血量 - {defender.character.name}: {defender.character.hp}/{defender.character.max_hp}")
    
    # 测试杀造成的伤害
    sha_card = Card("杀", CardType.BASIC, "♠", 1)
    attacker.hand_cards = [sha_card]
    
    # 使用杀
    result = attacker.play_card(0)
    if result:
        # 创建杀动作实例
        sha_action = game.create_card_action(result)
        sha_action.apply_default_effect(game, attacker, defender)
    
    print(f"使用杀后血量 - {defender.character.name}: {defender.character.hp}/{defender.character.max_hp}")
    
    # 验证伤害是否为1点
    expected_hp = 3
    if defender.character.hp == expected_hp:
        print("✓ 杀的伤害正确为1点")
    else:
        print(f"✗ 杀的伤害不正确，期望: {expected_hp}, 实际: {defender.character.hp}")

def test_multiple_sha_damage():
    """测试多次杀的伤害"""
    print("\n=== 测试多次杀的伤害 ===")
    
    # 创建武将
    caocao = Character("曹操", "魏", 4, ["奸雄"])
    liubei = Character("刘备", "蜀", 4, ["仁德"])
    
    # 初始化游戏
    game = Game()
    game.add_player(caocao)
    game.add_player(liubei)
    
    # 模拟玩家
    attacker = game.players[0]  # 曹操
    defender = game.players[1]  # 刘备
    
    # 设置初始血量
    defender.character.hp = 4
    print(f"初始血量 - {defender.character.name}: {defender.character.hp}/{defender.character.max_hp}")
    
    # 使用3次杀
    for i in range(3):
        sha_card = Card("杀", CardType.BASIC, "♠", 1)
        attacker.hand_cards = [sha_card]
        
        result = attacker.play_card(0)
        if result:
            sha_action = game.create_card_action(result)
            sha_action.apply_default_effect(game, attacker, defender)
        
        print(f"第{i+1}次杀后血量 - {defender.character.name}: {defender.character.hp}/{defender.character.max_hp}")
    
    # 验证最终血量
    expected_hp = 1
    if defender.character.hp == expected_hp:
        print("✓ 多次杀的伤害累计正确")
    else:
        print(f"✗ 多次杀的伤害累计不正确，期望: {expected_hp}, 实际: {defender.character.hp}")

if __name__ == "__main__":
    try:
        test_tao_card()
        test_sha_card_damage()
        test_multiple_sha_damage()
        print("\n=== 所有测试完成 ===")
    except Exception as e:
        print(f"测试过程中出现错误: {e}")
        import traceback
        traceback.print_exc()