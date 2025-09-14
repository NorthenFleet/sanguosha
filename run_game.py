"""
三国杀1v1游戏运行脚本

此脚本用于在终端运行游戏并显示输出，方便调试。
"""
import sys
import os

# 将项目根目录添加到Python路径中
sys.path.append(os.path.join(os.path.dirname(__file__), '.'))

from app.models.game import Game, Character
from app.models.character import CharacterFactory

def main():
    """主函数"""
    print("三国杀1v1游戏")
    print("=" * 30)
    
    # 创建游戏实例
    game = Game()
    
    # 选择武将
    print("请选择武将:")
    available_characters = ["曹操", "司马懿", "张辽", "夏侯惇", "刘备", "关羽", "张飞", "赵云", 
                         "诸葛亮", "孙权", "周瑜", "甘宁", "吕蒙"]
    
    for i, character in enumerate(available_characters, 1):
        print(f"{i}. {character}")
    
    # 获取玩家选择
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
        
        # 开始游戏
        game.start_game()
        
    except Exception as e:
        print(f"创建游戏时出错: {e}")
        return
    
    print("\n游戏结束。")

if __name__ == "__main__":
    main()