"""
三国杀1v1游戏主程序

注意：此脚本用于正常游戏运行，需要用户输入。
对于自动化测试，请运行 run_tests.py 脚本。
"""
from game import Game
from characters import CharacterFactory

def main():
    """游戏主程序"""
    print("=== 三国杀1v1 ===")
    
    # 创建游戏实例
    game = Game()
    
    # 选择武将
    print("\n可选武将:")
    available_characters = ["曹操", "司马懿", "张辽", "夏侯惇", "刘备", "关羽", "张飞", "赵云", "诸葛亮", "孙权", "周瑜", "甘宁", "吕蒙"]
    for idx, character in enumerate(available_characters, start=1):
        print(f"{idx}. {character}")

    # 玩家1选择
    while True:
        try:
            p1_choice = int(input("\n玩家1选择武将(1-13): "))
            if 1 <= p1_choice <= 13:
                break
            else:
                print("选择无效，请重新选择。")
        except ValueError:
            print("输入无效，请重新选择。")
    p1 = CharacterFactory.create_character(available_characters[p1_choice-1])

    # 玩家2选择
    while True:
        try:
            p2_choice = int(input("玩家2选择武将(1-13): "))
            if 1 <= p2_choice <= 13 and p2_choice != p1_choice:
                break
            else:
                print("选择无效，请重新选择。")
        except ValueError:
            print("输入无效，请重新选择。")
    p2 = CharacterFactory.create_character(available_characters[p2_choice-1])

    # 添加玩家
    game.add_player(p1)
    game.add_player(p2)

    # 开始游戏
    game.start_game()

if __name__ == "__main__":
    main()