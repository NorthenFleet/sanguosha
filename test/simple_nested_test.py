#!/usr/bin/env python3
"""
简化的嵌套裁决系统测试
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.nested_adjudication_stack import (
    NestedAdjudicationStack, AdjudicationProcess, TriggerType, 
    AdjudicationStatus, get_stack_manager, reset_stack_manager
)
from app.core.interaction_model import InteractionContext, InteractionType

class MockPlayer:
    def __init__(self, player_id: str, name: str):
        self.player_id = player_id
        self.name = name
        self.hp = 4
        self.max_hp = 4
        self.hand_cards = []
        
    def __str__(self):
        return f"{self.name}({self.player_id})"

class MockCard:
    def __init__(self, name: str, card_type: str = "basic"):
        self.name = name
        self.card_type = card_type
        
    def __str__(self):
        return f"{self.name}({self.card_type})"

def test_basic_stack():
    """测试基本堆栈功能"""
    print("=== 测试基本堆栈功能 ===")
    
    # 重置堆栈管理器
    reset_stack_manager()
    stack = get_stack_manager()
    
    # 创建测试上下文
    caocao = MockPlayer("player_1", "曹操")
    liubei = MockPlayer("player_2", "刘备")
    sha_card = MockCard("杀", "basic")
    
    context = InteractionContext(
        interaction_type=InteractionType.CARD_USE,
        source_player=caocao,
        target_player=liubei,
        card=sha_card,
        additional_data={'interaction_id': 'test_001'}
    )
    
    # 创建裁决过程
    process_id = stack.create_process(
        trigger_type=TriggerType.CARD_EFFECT,
        source_player_id=caocao.player_id,
        target_player_ids=[liubei.player_id],
        context=context,
        description="曹操对刘备使用杀"
    )
    
    print(f"1. 创建裁决过程: {process_id}")
    
    # 推入堆栈
    success = stack.push_process(process_id)
    print(f"2. 推入堆栈: {'成功' if success else '失败'}")
    
    # 检查堆栈状态
    status = stack.get_execution_summary()
    print(f"3. 堆栈状态: 深度={status['current_depth']}, 活跃进程={status['active_processes']}")
    
    # 完成进程
    stack.complete_process(process_id, "杀成功命中")
    print(f"4. 完成进程: {process_id}")
    
    # 弹出堆栈
    popped = stack.pop_process()
    print(f"5. 弹出堆栈: {'成功' if popped else '失败'}")
    
    # 最终状态
    final_status = stack.get_execution_summary()
    print(f"6. 最终状态: 深度={final_status['current_depth']}, 活跃进程={final_status['active_processes']}")
    
    print("✓ 基本堆栈功能测试完成\n")

def test_nested_process():
    """测试嵌套进程"""
    print("=== 测试嵌套进程 ===")
    
    # 重置堆栈管理器
    reset_stack_manager()
    stack = get_stack_manager()
    
    # 创建主进程
    caocao = MockPlayer("player_1", "曹操")
    liubei = MockPlayer("player_2", "刘备")
    sha_card = MockCard("杀", "basic")
    
    main_context = InteractionContext(
        interaction_type=InteractionType.CARD_USE,
        source_player=caocao,
        target_player=liubei,
        card=sha_card,
        additional_data={'interaction_id': 'main_001'}
    )
    
    main_process_id = stack.create_process(
        trigger_type=TriggerType.CARD_EFFECT,
        source_player_id=caocao.player_id,
        target_player_ids=[liubei.player_id],
        context=main_context,
        description="曹操对刘备使用杀"
    )
    
    stack.push_process(main_process_id)
    print(f"1. 创建并推入主进程: {main_process_id}")
    
    # 创建嵌套进程（八卦阵判定）
    nested_context = InteractionContext(
        interaction_type=InteractionType.SKILL_USE,
        source_player=liubei,
        additional_data={'interaction_id': 'nested_001', 'equipment': '八卦阵', 'judgment': True}
    )
    
    nested_process_id = stack.trigger_nested_process(
        trigger_type=TriggerType.EQUIPMENT_EFFECT,
        source_player_id=liubei.player_id,
        target_player_ids=[],
        context=nested_context,
        priority=1,
        description="刘备的八卦阵判定"
    )
    
    print(f"2. 触发嵌套进程: {nested_process_id}")
    
    # 检查堆栈状态
    status = stack.get_execution_summary()
    print(f"3. 嵌套后状态: 深度={status['current_depth']}, 活跃进程={status['active_processes']}")
    
    # 完成嵌套进程
    stack.complete_process(nested_process_id, "八卦阵判定成功，闪避杀")
    stack.pop_process()
    print("4. 完成嵌套进程")
    
    # 完成主进程
    stack.complete_process(main_process_id, "杀被闪避")
    stack.pop_process()
    print("5. 完成主进程")
    
    # 最终状态
    final_status = stack.get_execution_summary()
    print(f"6. 最终状态: 深度={final_status['current_depth']}, 活跃进程={final_status['active_processes']}")
    
    print("✓ 嵌套进程测试完成\n")

def main():
    """主测试函数"""
    print("开始嵌套裁决系统简化测试\n")
    
    try:
        test_basic_stack()
        test_nested_process()
        print("🎉 所有测试通过！")
        return True
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)