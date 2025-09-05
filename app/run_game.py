"""
三国杀1v1游戏运行脚本

此脚本用于在终端运行游戏并显示输出，方便调试。
"""
import sys
import os

# 将项目根目录添加到Python路径中
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from app.core.game_engine import GameEngine
from app.models.character import CharacterFactory

def main():
    """主函数"""
    print("三国杀1v1游戏")
    print("=" * 30)
    
    # 创建游戏引擎
    engine = GameEngine()
    
    # 选择武将
    print("请选择武将:")
    available_characters = ["曹操", "司马懿", "张辽", "夏侯惇", "刘备", "关羽", "张飞", "赵云", 
                         "诸葛亮", "孙权", "周瑜", "甘宁", "吕蒙"]
    
    for i, character in enumerate(available_characters, 1):
        print(f"{i}. {character}")
    
    # 获取玩家选择
    try:
        choice1 = int(input("\n玩家1请选择武将 (输入数字): "))
        choice2 = int(input("玩家2请选择武将 (输入数字): "))
        
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
        game_id = engine.create_game(player1_character, player2_character)
        print(f"\n游戏创建成功，游戏ID: {game_id}")
        
        # 显示初始游戏状态
        status = engine.get_game_status(game_id)
        print("\n初始游戏状态:")
        print(f"当前玩家: 玩家{status['current_player_id']} ({status['players'][status['current_player_id']-1]['character_name']})")
        print(f"当前阶段: {status['current_phase']}")
        
        for player_status in status['players']:
            print(f"\n玩家{player_status['player_id']} ({player_status['character_name']}):")
            print(f"  体力: {player_status['hp']}/{player_status['max_hp']}")
            print(f"  手牌数: {player_status['hand_cards_count']}")
            print(f"  武器: {player_status['weapon']}")
            print(f"  连环: {player_status['chained']}")
        
        print(f"\n牌堆剩余: {status['deck_count']}张牌")
        
        # 游戏循环
        while True:
            # 获取当前游戏状态
            status = engine.get_game_status(game_id)
            
            # 检查游戏是否结束
            game_over = False
            for player_status in status['players']:
                if player_status['hp'] <= 0:
                    print(f"\n游戏结束! 玩家{player_status['player_id']} ({player_status['character_name']}) 被击败!")
                    game_over = True
                    break
            
            if game_over:
                break
            
            # 显示当前玩家和阶段
            print(f"\n当前玩家: 玩家{status['current_player_id']} ({status['players'][status['current_player_id']-1]['character_name']})")
            print(f"当前阶段: {status['current_phase']}")
            
            # 显示玩家状态和手牌
            for player_status in status['players']:
                print(f"\n玩家{player_status['player_id']} ({player_status['character_name']}):")
                print(f"  体力: {player_status['hp']}/{player_status['max_hp']}")
                print(f"  手牌数: {player_status['hand_cards_count']}")
                print(f"  手牌: {', '.join(player_status['hand_cards'])}")
                print(f"  武器: {player_status['weapon']}")
                print(f"  连环: {player_status['chained']}")
            
            print(f"\n牌堆剩余: {status['deck_count']}张牌")
            
            # 获取玩家动作
            try:
                action = input("\n请输入动作 (输入'quit'退出游戏): ")
                if action.lower() == 'quit':
                    print("游戏退出。")
                    break
                
                # 执行动作（这里只是一个示例，实际需要根据游戏规则实现）
                # 目前只是简单地更新状态
                print(f"执行动作: {action}")
                
                # 这里应该调用engine.perform_action来执行具体动作
                # 暂时跳过实际动作执行，只更新状态
                
                # 切换到下一个玩家（简化处理）
                # 实际游戏中应该根据游戏规则和阶段来处理
                
            except KeyboardInterrupt:
                print("\n游戏被中断。")
                break
            except Exception as e:
                print(f"执行动作时出错: {e}")
        
    except Exception as e:
        print(f"创建游戏时出错: {e}")
        return
    
    print("\n游戏结束。")

if __name__ == "__main__":
    main()