"""
三国杀1v1游戏运行脚本

此脚本用于在终端运行游戏并显示输出，方便调试。
"""
import sys
import os
import argparse
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.core.base.path_utils import setup_paths
from app.core.base.game import Game
from app.models.character import Character
from app.core.events.event_system import EventManager

if __name__ == "__main__":
    setup_paths()
    event_manager = EventManager()
    game = Game(event_manager)

from app.models.character import CharacterFactory

def main():
    """主函数"""
    print("三国杀1v1游戏")
    print("=" * 30)

    # 创建事件管理器和游戏实例
    event_manager = EventManager()
    game = Game(event_manager)

    # 选择武将
    print("请选择武将:")
    available_characters = ["曹操", "司马懿", "张辽", "夏侯惇", "刘备", "关羽", "张飞", "赵云", 
                         "诸葛亮", "孙权", "周瑜", "甘宁", "吕蒙"]

    parser = argparse.ArgumentParser(description="在终端运行三国杀1v1")
    parser.add_argument("--p1", type=str, help="玩家1武将名称", default=None)
    parser.add_argument("--p2", type=str, help="玩家2武将名称", default=None)
    parser.add_argument("--auto", action="store_true", help="无交互自动选择默认武将")
    args = parser.parse_args()

    non_interactive = args.auto or not sys.stdin.isatty()

    if not non_interactive and args.p1 is None and args.p2 is None:
        for i, character in enumerate(available_characters, 1):
            print(f"{i}. {character}")

    # 获取玩家选择
    if non_interactive:
        # 自动或非交互模式：使用参数或默认值
        player1_character = args.p1 if args.p1 else "刘备"
        player2_character = args.p2 if args.p2 else "曹操"
        if player1_character == player2_character:
            # 若传入相同，自动调整为不同
            player2_character = "孙权" if player1_character != "孙权" else "周瑜"
        print(f"非交互模式: 玩家1={player1_character}, 玩家2={player2_character}")
    else:
        try:
            choice1 = int(input("\n玩家1请选择武将 (输入数字): ").strip())
            choice2 = int(input("玩家2请选择武将 (输入数字): ").strip())

            if choice1 < 1 or choice1 > len(available_characters) or choice2 < 1 or choice2 > len(available_characters):
                print("无效的选择")
                return

            player1_character = available_characters[choice1 - 1]
            player2_character = available_characters[choice2 - 1]

            if player1_character == player2_character:
                print("两位玩家不能选择相同的武将")
                return

        except ValueError:
            print("请输入有效的数字")
            return

    # 创建游戏
    try:
        # 创建武将实例并添加到游戏
        p1_character = CharacterFactory.create_character(player1_character)
        p2_character = CharacterFactory.create_character(player2_character)

        game.add_player(p1_character)
        game.add_player(p2_character)

        print("\n游戏创建成功")

        # 开始游戏，自动/非交互模式下启用测试模式以跳过交互输入
        game.start_game(test_mode=non_interactive)

    except Exception as e:
        print(f"创建游戏时出错: {e}")
        return

    print("\n游戏结束。")

if __name__ == "__main__":
    main()