"""
三国杀1v1游戏测试脚本
"""
import sys
import os

# 将项目根目录添加到Python路径中
sys.path.append(os.path.join(os.path.dirname(__file__)))

from app.models.game import Game, Character
from app.models.character import CharacterFactory

def test_game():
    """测试游戏功能"""
    print("三国杀1v1游戏测试")
    print("=" * 30)
    
    # 创建游戏实例
    game = Game()
    
    # 创建武将实例并添加到游戏
    p1_character = CharacterFactory.create_character("曹操")
    p2_character = CharacterFactory.create_character("刘备")
    
    game.add_player(p1_character)
    game.add_player(p2_character)
    
    print("游戏创建成功")
    print(f"玩家1: {p1_character.name}")
    print(f"玩家2: {p2_character.name}")
    
    # 开始游戏
    game.start_game()

if __name__ == "__main__":
    test_game()