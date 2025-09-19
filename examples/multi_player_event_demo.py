#!/usr/bin/env python3
"""
多玩家事件系统演示
展示事件驱动的多玩家交互响应模型
"""
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from app.core.events.multi_player_event_system import (
    MultiPlayerEventSystem, GameEvent, EventResponse
)
from app.core.events.event_dispatcher import GameEventDispatcher
from app.core.interaction.player_response_manager import PlayerResponseManager
from app.core.events.skill_event_handlers import CharacterSkillManager, SkillResponseHandler
from app.models.card import Card
from app.models.player import Player
from app.models.character import Character
import uuid
from datetime import datetime

def create_test_players():
    """创建测试玩家"""
    players = []
    characters = ["曹操", "刘备", "孙权", "关羽", "张飞"]
    
    for i, character_name in enumerate(characters):
        character = Character(character_name, "魏" if i == 0 else "蜀", 4, [])
        player = Player(character)
        player.player_id = f"player_{i+1}"
        player.name = f"玩家{i+1}"
        player.position = i
        players.append(player)
    
    return players

def create_test_card(name: str, suit: str = "红桃", rank: str = "A"):
    """创建测试卡牌"""
    return Card(
        name=name,
        suit=suit,
        rank=rank,
        category="basic" if name in ["杀", "闪", "桃"] else "trick"
    )

def demo_basic_event_flow():
    """演示基本事件流程"""
    print("=== 基本事件流程演示 ===")
    
    # 创建玩家
    players = create_test_players()
    player_ids = [player.player_id for player in players]
    
    # 创建事件系统
    event_system = MultiPlayerEventSystem(player_ids)
    
    # 注册玩家处理器
    for player in players:
        handler = BasicCardResponseHandler(player.player_id, player.hand_cards)
        event_system.register_player_handler(player.player_id, handler)
    
    # 创建测试事件：玩家1使用杀攻击玩家2
    sha_card = create_test_card("杀")
    play_card_event = GameEvent(
        event_id=str(uuid.uuid4()),
        event_type="play_card",
        source_player_id="player_1",
        target_player_ids=["player_2"],
        data={
            "card": sha_card,
            "action": "attack",
            "timestamp": datetime.now()
        },
        timestamp=datetime.now().timestamp()
    )
    
    print(f"事件创建: {play_card_event.event_type}")
    print(f"源玩家: {play_card_event.source_player_id}")
    print(f"目标玩家: {play_card_event.target_player_ids}")
    print(f"卡牌: {sha_card.name}")
    
    # 发布事件
    responses = event_system.publish_event(play_card_event)
    
    print(f"\n收到 {len(responses)} 个响应:")
    for response in responses:
        print(f"  - 玩家 {response.player_id}: {response.response_type.value}")
        print(f"    动作: {response.action_data.get('action_type')}")
        if 'card' in response.action_data:
            card = response.action_data['card']
            print(f"    卡牌: {card.name}")
    
    print("基本事件流程演示完成\n")

def demo_skill_event_integration():
    """演示技能事件集成"""
    print("=== 技能事件集成演示 ===")
    
    # 创建事件分发器
    dispatcher = GameEventDispatcher()
    
    # 创建玩家响应管理器
    response_manager = PlayerResponseManager()
    
    # 创建玩家和技能管理器
    players = create_test_players()
    skill_managers = {}
    
    for player in players:
        skill_manager = CharacterSkillManager(player.player_id, player.character)
        skill_managers[player.player_id] = skill_manager
        
        # 注册技能响应处理器
        skill_handler = SkillResponseHandler(player.player_id, skill_manager)
        dispatcher.register_handler(player.player_id, skill_handler)
        
        print(f"玩家 {player.name} ({player.character}) 技能已注册")
    
    # 创建伤害事件，触发曹操的奸雄技能
    damage_card = create_test_card("杀")
    damage_event = GameEvent(
        event_id=str(uuid.uuid4()),
        event_type="take_damage",
        source_player_id="player_2",
        target_player_ids=["player_1"],  # 曹操
        data={
            "damage_amount": 1,
            "damage_card": damage_card,
            "damage_source": "card_effect"
        },
        priority=EventPriority.NORMAL
    )
    
    print(f"\n创建伤害事件:")
    print(f"  事件类型: {damage_event.event_type}")
    print(f"  伤害来源: 玩家2")
    print(f"  伤害目标: 玩家1 (曹操)")
    print(f"  伤害牌: {damage_card.name}")
    
    # 分发事件
    responses = dispatcher.dispatch_event(damage_event)
    
    print(f"\n收到 {len(responses)} 个技能响应:")
    for response in responses:
        print(f"  - 玩家 {response.player_id}: {response.response_type.value}")
        if 'skill_name' in response.action_data:
            print(f"    技能: {response.action_data['skill_name']}")
        if 'effect_result' in response.action_data:
            effect = response.action_data['effect_result']
            print(f"    效果: {effect.get('message', '无描述')}")
    
    print("技能事件集成演示完成\n")

def demo_multi_player_response_order():
    """演示多玩家响应顺序"""
    print("=== 多玩家响应顺序演示 ===")
    
    # 创建事件系统和响应管理器
    event_system = MultiPlayerEventSystem()
    response_manager = PlayerResponseManager()
    
    # 创建玩家
    players = create_test_players()
    
    # 注册玩家
    for player in players:
        event_system.register_player(player.player_id)
        response_manager.register_player(player.player_id, player.position)
    
    # 创建全局事件：有人使用无懈可击
    wuxie_card = create_test_card("无懈可击")
    wuxie_event = GameEvent(
        event_id=str(uuid.uuid4()),
        event_type="play_card",
        source_player_id="player_3",
        target_player_ids=["player_1"],  # 针对玩家1的锦囊
        data={
            "card": wuxie_card,
            "action": "counter_spell",
            "original_target": "player_1"
        },
        priority=EventPriority.HIGH
    )
    
    print(f"创建无懈可击事件:")
    print(f"  使用者: 玩家3")
    print(f"  目标: 玩家1")
    
    # 开启响应窗口
    window = response_manager.open_response_window(
        event=wuxie_event,
        eligible_players=["player_1", "player_2", "player_4", "player_5"],  # 除了使用者
        timeout_seconds=30
    )
    
    print(f"\n响应窗口已开启，窗口ID: {window.window_id}")
    print(f"符合条件的玩家: {window.eligible_players}")
    
    # 模拟玩家按顺序响应
    player_responses = [
        ("player_4", "也使用无懈可击"),
        ("player_5", "不响应"),
        ("player_1", "使用无懈可击"),
        ("player_2", "不响应")
    ]
    
    for player_id, action in player_responses:
        if action != "不响应":
            response = EventResponse(
                response_id=str(uuid.uuid4()),
                event_id=wuxie_event.event_id,
                player_id=player_id,
                response_type=ResponseType.COUNTER,
                priority=EventPriority.HIGH,
                action_data={
                    "action_type": "play_card",
                    "card": create_test_card("无懈可击"),
                    "counter_target": wuxie_event.event_id
                },
                conditions_met=True
            )
            response_manager.submit_response(window.window_id, response)
            print(f"  玩家 {player_id}: {action}")
        else:
            print(f"  玩家 {player_id}: {action}")
    
    # 获取最终响应顺序
    final_responses = response_manager.get_responses_in_order(window.window_id)
    
    print(f"\n最终响应顺序 ({len(final_responses)} 个响应):")
    for i, response in enumerate(final_responses, 1):
        print(f"  {i}. 玩家 {response.player_id}: {response.action_data.get('action_type')}")
    
    # 关闭响应窗口
    response_manager.close_response_window(window.window_id)
    
    print("多玩家响应顺序演示完成\n")

def demo_complex_skill_chain():
    """演示复杂技能连锁"""
    print("=== 复杂技能连锁演示 ===")
    
    # 创建完整的事件处理系统
    event_system = MultiPlayerEventSystem()
    dispatcher = GameEventDispatcher()
    response_manager = PlayerResponseManager()
    
    # 创建玩家和技能管理器
    players = create_test_players()
    skill_managers = {}
    
    for player in players:
        event_system.register_player(player.player_id)
        response_manager.register_player(player.player_id, player.position)
        
        skill_manager = CharacterSkillManager(player.player_id, player.character)
        skill_managers[player.player_id] = skill_manager
        
        skill_handler = SkillResponseHandler(player.player_id, skill_manager)
        dispatcher.register_handler(player.player_id, skill_handler)
    
    print("所有玩家和技能已注册")
    
    # 场景：玩家1(曹操)使用杀攻击玩家4(关羽)
    # 关羽可能发动武圣，曹操受到反击伤害后可能发动奸雄
    
    # 第一步：关羽出牌阶段，可能发动武圣
    phase_event = GameEvent(
        event_id=str(uuid.uuid4()),
        event_type="phase_change",
        source_player_id="player_4",  # 关羽
        target_player_ids=["player_4"],
        data={
            "old_phase": "draw",
            "new_phase": "play",
            "player_character": "关羽"
        },
        priority=EventPriority.NORMAL
    )
    
    print(f"\n第一步：关羽进入出牌阶段")
    responses = dispatcher.dispatch_event(phase_event)
    
    for response in responses:
        if 'skill_name' in response.action_data:
            print(f"  技能响应: {response.action_data['skill_name']}")
    
    # 第二步：关羽使用红色牌当杀使用（武圣）
    red_card = create_test_card("桃", "红桃", "K")  # 红色牌
    wusheng_event = GameEvent(
        event_id=str(uuid.uuid4()),
        event_type="play_card",
        source_player_id="player_4",  # 关羽
        target_player_ids=["player_1"],  # 攻击曹操
        data={
            "card": red_card,
            "converted_to": "杀",
            "skill_used": "武圣",
            "original_card": red_card
        },
        priority=EventPriority.HIGH
    )
    
    print(f"\n第二步：关羽发动武圣，将{red_card.name}当杀使用攻击曹操")
    responses = dispatcher.dispatch_event(wusheng_event)
    
    # 第三步：假设攻击成功，曹操受到伤害，触发奸雄
    damage_event = GameEvent(
        event_id=str(uuid.uuid4()),
        event_type="take_damage",
        source_player_id="player_4",  # 关羽
        target_player_ids=["player_1"],  # 曹操
        data={
            "damage_amount": 1,
            "damage_card": red_card,  # 造成伤害的牌
            "damage_source": "skill_conversion",
            "original_skill": "武圣"
        },
        priority=EventPriority.NORMAL
    )
    
    print(f"\n第三步：曹操受到伤害，可能发动奸雄")
    responses = dispatcher.dispatch_event(damage_event)
    
    for response in responses:
        if 'skill_name' in response.action_data:
            skill_name = response.action_data['skill_name']
            effect = response.action_data.get('effect_result', {})
            print(f"  {skill_name}技能发动: {effect.get('message', '无描述')}")
    
    print("复杂技能连锁演示完成\n")

def main():
    """主演示函数"""
    print("多玩家事件系统演示开始")
    print("=" * 50)
    
    try:
        # 基本事件流程
        demo_basic_event_flow()
        
        # 技能事件集成
        demo_skill_event_integration()
        
        # 多玩家响应顺序
        demo_multi_player_response_order()
        
        # 复杂技能连锁
        demo_complex_skill_chain()
        
        print("=" * 50)
        print("所有演示完成！")
        
        print("\n系统特性总结:")
        print("✓ 事件驱动架构")
        print("✓ 多玩家按顺序响应")
        print("✓ 技能事件自动订阅")
        print("✓ 响应优先级管理")
        print("✓ 复杂技能连锁支持")
        print("✓ 响应窗口管理")
        
    except Exception as e:
        print(f"演示过程中出现错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()