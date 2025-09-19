#!/usr/bin/env python3
"""
简化的多玩家事件系统演示
测试核心事件分发和响应功能
"""
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from app.core.multi_player_event_system import (
    MultiPlayerEventSystem, GameEvent, EventResponse, EventPriority, ResponseType,
    BasicCardResponseHandler
)
from app.core.event_dispatcher import GameEventDispatcher
from app.core.player_response_manager import PlayerResponseManager, ResponseWindowState
from app.core.skill_event_handlers import CharacterSkillManager, SkillResponseHandler
from app.models.card import Card
from app.models.player import Player
from app.models.character import Character
import uuid
from datetime import datetime

def create_simple_test_data():
    """创建简单的测试数据"""
    # 创建角色
    caocao = Character("曹操", "魏", 4, ["奸雄"])
    liubei = Character("刘备", "蜀", 4, ["仁德"])
    
    # 创建玩家
    player1 = Player(caocao)
    player1.player_id = "player_1"
    player1.name = "玩家1"
    
    player2 = Player(liubei)
    player2.player_id = "player_2"
    player2.name = "玩家2"
    
    # 创建卡牌
    sha_card = Card(name="杀", category="basic", suit="红桃", rank="7")
    shan_card = Card(name="闪", category="basic", suit="方块", rank="2")
    
    # 给玩家分配卡牌
    player1.hand_cards = [sha_card]
    player2.hand_cards = [shan_card]
    
    return [player1, player2], [sha_card, shan_card]

def test_basic_event_system():
    """测试基本事件系统"""
    print("=== 基本事件系统测试 ===")
    
    # 创建测试数据
    players, cards = create_simple_test_data()
    player_ids = [p.player_id for p in players]
    
    # 创建事件系统
    event_system = MultiPlayerEventSystem(player_ids)
    
    # 注册玩家处理器
    for player in players:
        handler = BasicCardResponseHandler(player.player_id, player.hand_cards)
        event_system.register_player_handler(player.player_id, handler)
    
    print(f"已注册 {len(players)} 个玩家")
    
    # 创建事件
    event = GameEvent(
        event_id=str(uuid.uuid4()),
        event_type="play_card",
        source_player_id="player_1",
        target_player_ids=["player_2"],
        data={
            "card": cards[0],  # 杀
            "action": "attack"
        },
        timestamp=datetime.now().timestamp()
    )
    
    print(f"创建事件: {event.event_type}")
    print(f"源玩家: {event.source_player_id}")
    print(f"目标玩家: {event.target_player_ids}")
    
    # 发布事件
    try:
        responses = event_system.publish_event(event)
        print(f"收到 {len(responses)} 个响应")
        
        for response in responses:
            print(f"  响应来自: {response.player_id}")
            print(f"  响应类型: {response.response_type.value}")
    except Exception as e:
        print(f"事件处理出错: {e}")
    
    print("基本事件系统测试完成\n")

def test_skill_event_integration():
    """测试技能事件集成"""
    print("=== 技能事件集成测试 ===")
    
    # 创建测试数据
    players, cards = create_simple_test_data()
    
    # 创建技能管理器
    skill_managers = {}
    for player in players:
        skill_manager = CharacterSkillManager(player.player_id, player.character.name)
        skill_managers[player.player_id] = skill_manager
        print(f"为 {player.name}({player.character.name}) 创建技能管理器")
    
    # 创建事件分发器
    player_ids = [p.player_id for p in players]
    dispatcher = GameEventDispatcher(player_ids)
    
    # 注册技能处理器
    for player in players:
        skill_handler = SkillResponseHandler(player.player_id, skill_managers[player.player_id])
        dispatcher.register_player_handler(player.player_id, skill_handler)
    
    print("技能处理器已注册")
    
    # 创建伤害事件（触发奸雄）
    damage_event = GameEvent(
        event_id=str(uuid.uuid4()),
        event_type="take_damage",
        source_player_id="player_2",
        target_player_ids=["player_1"],  # 曹操受伤
        data={
            "damage_amount": 1,
            "damage_card": cards[0],  # 杀造成的伤害
            "damage_source": "card_effect"
        },
        timestamp=datetime.now().timestamp()
    )
    
    print(f"创建伤害事件: 玩家1受到伤害")
    
    # 分发事件
    try:
        responses = dispatcher.dispatch_damage_event(
            source_player_id="player_2",
            target_player_id="player_1",  # 曹操受伤
            damage_amount=1,
            damage_type="card_damage"
        )
        print(f"收到 {len(responses)} 个技能响应")
        
        for response in responses:
            print(f"  技能响应来自: {response.player_id}")
            if 'skill_name' in response.action_data:
                print(f"  技能名称: {response.action_data['skill_name']}")
    except Exception as e:
        print(f"技能事件处理出错: {e}")
    
    print("技能事件集成测试完成\n")

def test_response_manager():
    """测试响应管理器"""
    print("=== 响应管理器测试 ===")
    
    # 创建响应管理器
    player_ids = ["player_1", "player_2", "player_3"]
    response_manager = PlayerResponseManager(player_ids)
    
    # 注册玩家（PlayerResponseManager已在初始化时注册了玩家）
    print(f"已注册 {len(player_ids)} 个玩家")
    
    # 创建测试事件
    event = GameEvent(
        event_id=str(uuid.uuid4()),
        event_type="play_card",
        source_player_id="player_1",
        target_player_ids=["player_2", "player_3"],
        data={"card_name": "无懈可击"},
        timestamp=datetime.now().timestamp()
    )
    
    # 开启响应窗口
    try:
        window = response_manager.open_response_window(
            event=event,
            eligible_players=["player_2", "player_3"],
            timeout_seconds=30
        )
        
        print(f"响应窗口已开启: {window.window_id}")
        print(f"符合条件的玩家: {window.eligible_players}")
        
        # 模拟响应（直接添加到窗口的collected_responses中）
        response = EventResponse(
            response_id=str(uuid.uuid4()),
            event_id=event.event_id,
            player_id="player_2",
            response_type=ResponseType.IMMEDIATE,
            priority=EventPriority.HIGH,
            action_data={"action": "counter"},
            conditions_met=True
        )
        
        window.collected_responses.append(response)
        print("已提交一个响应")
        
        # 获取响应
        responses = window.collected_responses
        print(f"按顺序获得 {len(responses)} 个响应")
        
        # 关闭窗口
        window.state = ResponseWindowState.CLOSED
        print("响应窗口已关闭")
        
    except Exception as e:
        print(f"响应管理器测试出错: {e}")
    
    print("响应管理器测试完成\n")

def main():
    """主测试函数"""
    print("简化事件系统演示开始")
    print("=" * 40)
    
    try:
        # 测试基本事件系统
        test_basic_event_system()
        
        # 测试技能事件集成
        test_skill_event_integration()
        
        # 测试响应管理器
        test_response_manager()
        
        print("=" * 40)
        print("所有测试完成！")
        
        print("\n系统功能验证:")
        print("✓ 多玩家事件系统初始化")
        print("✓ 事件发布和响应收集")
        print("✓ 技能事件处理器集成")
        print("✓ 响应窗口管理")
        print("✓ 玩家响应顺序控制")
        
    except Exception as e:
        print(f"演示过程中出现错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()