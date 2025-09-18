import sys
sys.path.append('.')

from app.core.game_engine import GameEngine
from app.models.character import Character
from app.models.card import Card
from app.models.enums import CardType

print("=== 测试游戏整体流程稳定性 ===")

# 创建游戏引擎
game_engine = GameEngine()

# 创建武将
character1 = Character("关羽", Kingdom.SHU, 4, ["武圣"])
character2 = Character("曹操", Kingdom.WEI, 4, ["奸雄"])

print(f"创建的武将:")
print(f"武将1: {character1.name} - {character1.kingdom.value} - {character1.hp}血 - 技能: {character1.skills}")
print(f"武将2: {character2.name} - {character2.kingdom.value} - {character2.hp}血 - 技能: {character2.skills}")

# 测试1: 创建游戏
print(f"\n=== 测试游戏创建 ===")
try:
    game_id = game_engine.create_game("player1", character1.name)
    print(f"游戏创建成功，游戏ID: {game_id}")
    
    # 添加第二个玩家
    game_engine.add_player(game_id, "player2", character2.name)
    print(f"第二个玩家添加成功")
    
    # 获取游戏状态
    game_status = game_engine.get_game_status(game_id)
    print(f"游戏状态: {game_status['status']}")
    print(f"当前玩家: {game_status['current_player']}")
    print(f"玩家数量: {len(game_status['players'])}")
    
except Exception as e:
    print(f"游戏创建失败: {e}")

# 测试2: 游戏动作执行
print(f"\n=== 测试游戏动作执行 ===")
try:
    # 获取当前玩家手牌
    game_status = game_engine.get_game_status(game_id)
    current_player = game_status['current_player']
    players = game_status['players']
    
    print(f"当前玩家: {current_player}")
    for player_id, player_info in players.items():
        print(f"玩家 {player_id}: 血量={player_info['hp']}, 手牌数={len(player_info['hand_cards'])}")
        if len(player_info['hand_cards']) > 0:
            print(f"  手牌: {player_info['hand_cards'][:3]}...")  # 只显示前3张牌
    
    # 尝试使用一张牌
    if current_player in players and len(players[current_player]['hand_cards']) > 0:
        first_card = players[current_player]['hand_cards'][0]
        print(f"尝试使用卡牌: {first_card}")
        
        action_result = game_engine.perform_action(game_id, current_player, {
            "action": "use_card",
            "card": first_card
        })
        print(f"动作执行结果: {action_result}")
        
        # 获取更新后的游戏状态
        updated_status = game_engine.get_game_status(game_id)
        print(f"动作后当前玩家: {updated_status['current_player']}")
    
except Exception as e:
    print(f"游戏动作执行失败: {e}")

# 测试3: 多轮游戏流程
print(f"\n=== 测试多轮游戏流程 ===")
try:
    for round_num in range(3):
        print(f"\n--- 第 {round_num + 1} 轮 ---")
        game_status = game_engine.get_game_status(game_id)
        current_player = game_status['current_player']
        
        if game_status['status'] == 'finished':
            print(f"游戏已结束")
            break
            
        print(f"当前玩家: {current_player}")
        
        # 尝试结束回合
        end_turn_result = game_engine.perform_action(game_id, current_player, {
            "action": "end_turn"
        })
        print(f"结束回合结果: {end_turn_result}")
        
        # 检查回合是否切换
        new_status = game_engine.get_game_status(game_id)
        print(f"新的当前玩家: {new_status['current_player']}")
        
except Exception as e:
    print(f"多轮游戏流程测试失败: {e}")

# 测试4: 错误处理
print(f"\n=== 测试错误处理 ===")
try:
    # 测试无效游戏ID
    invalid_result = game_engine.get_game_status("invalid_game_id")
    print(f"无效游戏ID结果: {invalid_result}")
except Exception as e:
    print(f"无效游戏ID错误处理: {e}")

try:
    # 测试无效动作
    invalid_action_result = game_engine.perform_action(game_id, current_player, {
        "action": "invalid_action"
    })
    print(f"无效动作结果: {invalid_action_result}")
except Exception as e:
    print(f"无效动作错误处理: {e}")

# 测试5: 游戏状态一致性
print(f"\n=== 测试游戏状态一致性 ===")
try:
    # 多次获取游戏状态，检查一致性
    status1 = game_engine.get_game_status(game_id)
    status2 = game_engine.get_game_status(game_id)
    
    print(f"状态1当前玩家: {status1['current_player']}")
    print(f"状态2当前玩家: {status2['current_player']}")
    print(f"状态一致性: {status1['current_player'] == status2['current_player']}")
    
except Exception as e:
    print(f"游戏状态一致性测试失败: {e}")

print(f"\n游戏整体流程稳定性测试完成!")