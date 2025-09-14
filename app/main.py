from core.path_utils import setup_paths
setup_paths()

from core.event_system import EventManager
from app.models.game import Game
from app.models.character import Character


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
            choice = int(input("输入武将编号: ")) - 1
            if 0 <= choice < len(available_characters):
                player_character = available_characters.pop(choice)
                break
            else:
                print("无效的编号，请重新输入。")
        except ValueError:
            print("请输入有效的数字编号。")

    # 为人机选择武将
    ai_character = available_characters[0]

    # 添加玩家和人机到游戏
    game.add_player(player_character)
    game.add_player(ai_character)

    print(f"你选择了 {player_character.name} ({player_character.kingdom})")
    print(f"人机选择了 {ai_character.name} ({ai_character.kingdom})")

    # 启动游戏
    game.start_game()

if __name__ == "__main__":
    main()