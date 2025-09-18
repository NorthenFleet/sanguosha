import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app.core.path_utils import setup_paths
setup_paths()

from app.core.event_system import EventManager
from app.core.game import Game
from app.models.character import Character
from app.models.card import Deck, display_deck_info


def main():
    # 初始化事件管理器和游戏实例
    event_manager = EventManager()
    game = Game(event_manager)

    # 可选武将列表
    available_characters = [
        Character("曹操", "魏", 4, ["奸雄"]),
        Character("刘备", "蜀", 4, ["仁德"]),
        Character("孙权", "吴", 4, ["制衡"]),
    ]

    # 玩家选择武将
    print("请选择你的武将:")
    for idx, character in enumerate(available_characters, start=1):
        print(f"{idx}. {character.name} ({character.kingdom}) - 血量: {character.max_hp}, 技能: {', '.join(character.skills)}")

    while True:
        try:
            user_input = input("输入武将编号: ")
            if not user_input.strip():
                print("输入不能为空，请重新选择。")
                continue
            choice = int(user_input) - 1
            if 0 <= choice < len(available_characters):
                player_character = available_characters.pop(choice)
                break
            else:
                print("无效的选择，请重新选择。")
        except (ValueError, EOFError, KeyboardInterrupt):
            print("游戏被中断或输入无效，请重新选择。")
            continue

    # 为人机选择武将
    ai_character = available_characters[0]

    # 添加玩家和人机到游戏
    game.add_player(player_character)
    game.add_player(ai_character)

    print(f"你选择了 {player_character.name} ({player_character.kingdom})")
    print(f"人机选择了 {ai_character.name} ({ai_character.kingdom})")

    # 启动游戏
    game.start_game()

    # 初始化牌堆
    deck = Deck("app/data/cards.json")
    if not deck.cards:
        print("错误: 卡牌数据加载失败，请检查 cards.json 文件内容。")
        return

    deck.shuffle()

    # 显示牌堆信息
    display_deck_info(deck)

    # 测试摸牌功能
    card = deck.draw_card()
    print(f"摸到的牌是：{card}")

    # 将摸到的牌放入弃牌堆
    deck.discard(card)

    # 再次显示牌堆信息
    display_deck_info(deck)

if __name__ == "__main__":
    main()