"""
三国杀1v1游戏流程测试脚本
"""
import sys
import os
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))

from app.models.game import Game, Card, CardType
from app.models.character import CharacterFactory

def test_game_flow():
    """测试游戏流程"""
    print("开始测试游戏流程...")
    
    # 创建游戏实例
    game = Game()
    
    # 创建测试用的武将 (张飞-有咆哮技能, 诸葛亮-有观星技能)
    zhangfei = CharacterFactory.create_character("张飞")
    zhuge = CharacterFactory.create_character("诸葛亮")
    
    # 添加玩家
    game.add_player(zhangfei)
    game.add_player(zhuge)
    
    # 初始化牌堆
    game.initialize_deck()
    
    # 给玩家一些初始手牌用于测试
    # 给张飞一些杀和闪
    game.players[0].hand_cards = [
        Card("杀", CardType.BASIC, "♠", 5),
        Card("杀", CardType.BASIC, "♥", 6),
        Card("杀", CardType.BASIC, "♦", 7),
        Card("闪", CardType.BASIC, "♣", 8)
    ]
    
    # 给诸葛亮一些锦囊牌
    game.players[1].hand_cards = [
        Card("过河拆桥", CardType.TRICK, "♠", 9),
        Card("顺手牵羊", CardType.TRICK, "♥", 10),
        Card("无中生有", CardType.TRICK, "♦", 11),
        Card("桃", CardType.BASIC, "♣", 12)
    ]
    
    print("初始状态:")
    print(f"{game.players[0].character.name} 手牌: {[str(card) for card in game.players[0].hand_cards]}")
    print(f"{game.players[1].character.name} 手牌: {[str(card) for card in game.players[1].hand_cards]}")
    
    # 测试张飞的咆哮技能 - 可以使用多张杀
    print("\n测试张飞的咆哮技能:")
    print(f"{game.players[0].character.name} 是否有咆哮技能: {game.players[0].character.has_skill('咆哮')}")
    
    # 测试诸葛亮的观星技能
    print("\n测试诸葛亮的观星技能:")
    print(f"{game.players[1].character.name} 是否有观星技能: {game.players[1].character.has_skill('观星')}")
    
    # 模拟一个简单的回合
    print("\n模拟一个简单的回合:")
    
    # 判定阶段
    game.judgment_phase()
    
    # 摸牌阶段
    game.draw_phase(game.players[0])
    
    # 出牌阶段 - 测试张飞使用多张杀
    print(f"\n{game.players[0].character.name} 的出牌阶段:")
    # 检查咆哮技能
    if game.players[0].character.has_skill("咆哮"):
        print(f"{game.players[0].character.name} 有技能【咆哮】，可以多次使用杀")
        # 触发咆哮技能
        game.players[0].character.use_skill("咆哮", game, game.players[0])
    
    # 使用一张杀
    if game.players[0].hand_cards:
        card = game.players[0].hand_cards[0]
        if card.name == "杀":
            print(f"{game.players[0].character.name} 使用了 {card}")
            game.handle_response(game.players[0], card, test_mode=True)
    
    # 弃牌阶段
    game.discard_phase(game.players[0], test_mode=True)
    
    # 运行一个简单的回合用于测试
    game.judgment_phase()
    game.draw_phase(game.players[0])
    game.play_phase(game.players[0], test_mode=True)
    game.discard_phase(game.players[0], test_mode=True)
    
    print("\n测试完成。")

if __name__ == "__main__":
    test_game_flow()