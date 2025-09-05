"""
三国杀1v1自动化测试脚本

此脚本用于测试游戏的基本功能，使用简单的决策逻辑来模拟玩家行为。
"""
import json
import random
from typing import Dict, Any, List

def load_game_state(file_path: str) -> Dict[str, Any]:
    """加载游戏状态"""
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_game_state(file_path: str, state: Dict[str, Any]):
    """保存游戏状态"""
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(state, f, ensure_ascii=False, indent=2)

def decide_action(state: Dict[str, Any]) -> str:
    """根据游戏状态决定行动"""
    # 获取当前玩家信息
    current_turn = state['current_turn']
    team_name = "冷方" if "冷方" in current_turn else "暖方"
    position = ""
    if "主帅" in current_turn:
        position = "leader"
    elif "前锋1" in current_turn:
        position = "frontline_1"
    elif "前锋2" in current_turn:
        position = "frontline_2"
    
    player_info = state['teams'][team_name][position]
    
    # 检查手牌
    hand_cards = player_info['hand_cards']
    
    # 简单决策逻辑
    # 1. 如果有桃且体力不满，优先使用桃
    if "桃" in hand_cards and player_info['hp'] < player_info['max_hp']:
        return "使用桃"
    
    # 2. 如果有杀，优先使用杀攻击对手
    if "杀" in hand_cards:
        return "使用杀"
    
    # 3. 如果有锦囊牌，考虑使用
    trick_cards = [card for card in hand_cards if card in ["过河拆桥", "顺手牵羊", "无中生有", "决斗", "南蛮入侵", "万箭齐发"]]
    if trick_cards:
        return f"使用{trick_cards[0]}"
    
    # 4. 如果有装备牌，考虑装备
    equip_cards = [card for card in hand_cards if card in ["方天画戟", "赤兔", "仁王盾", "青釭剑", "贯石斧"]]
    if equip_cards:
        return f"装备{equip_cards[0]}"
    
    # 5. 默认弃牌
    return "弃牌"

def execute_action(state: Dict[str, Any], action: str) -> Dict[str, Any]:
    """执行行动并更新游戏状态"""
    # 这里只是一个示例，实际实现需要根据游戏规则更新状态
    new_state = state.copy()
    
    # 简单示例：更新日志
    new_state['logs'].append(f"执行了动作: {action}")
    
    return new_state

def run_test(state_file: str):
    """运行测试"""
    # 加载游戏状态
    state = load_game_state(state_file)
    
    # 决定行动
    action = decide_action(state)
    print(f"决定执行的动作: {action}")
    
    # 执行行动
    new_state = execute_action(state, action)
    
    # 保存更新后的状态
    save_game_state(state_file, new_state)
    
    print("测试完成，游戏状态已更新。")

if __name__ == "__main__":
    run_test("app/data/state.json")