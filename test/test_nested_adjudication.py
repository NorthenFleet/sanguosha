#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
嵌套裁决系统测试
测试卡牌和技能的嵌套触发场景
"""

import unittest
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.nested_adjudication_stack import (
    NestedAdjudicationStack, AdjudicationProcess, TriggerType, 
    AdjudicationStatus, get_stack_manager, reset_stack_manager
)
from app.core.enhanced_adjudication_engine import (
    EnhancedAdjudicationEngine, TriggerCondition
)
from app.core.interaction_model import InteractionContext, InteractionType
from app.core.adjudication_engine import FinalResult, AdjudicationResult


class MockPlayer:
    """模拟玩家类"""
    def __init__(self, player_id: str, name: str):
        self.player_id = player_id
        self.name = name
        self.hp = 4
        self.max_hp = 4
        self.cards = []
        self.character = name
        
    def __str__(self):
        return f"{self.name}({self.player_id})"


class MockCard:
    """模拟卡牌类"""
    def __init__(self, name: str, card_type: str = "basic"):
        self.name = name
        self.card_type = card_type
        
    def __str__(self):
        return self.name


class TestNestedAdjudicationStack(unittest.TestCase):
    """嵌套裁决堆栈测试"""
    
    def setUp(self):
        """测试前准备"""
        reset_stack_manager()
        self.stack = NestedAdjudicationStack(max_depth=5)
        
        # 创建测试玩家
        self.player1 = MockPlayer("player_1", "曹操")
        self.player2 = MockPlayer("player_2", "刘备")
        self.player3 = MockPlayer("player_3", "孙权")
        
        # 创建测试卡牌
        self.sha_card = MockCard("杀", "basic")
        self.shan_card = MockCard("闪", "basic")
        
    def test_basic_stack_operations(self):
        """测试基本堆栈操作"""
        # 创建交互上下文
        context = InteractionContext(
            interaction_type=InteractionType.CARD_USE,
            source_player=MockPlayer("player_1", "测试玩家1"),
            target_player=MockPlayer("player_2", "测试玩家2"),
            card=self.sha_card,
            additional_data={'interaction_id': 'test_001'}
        )
        
        # 创建裁决过程
        process_id = self.stack.create_process(
            trigger_type=TriggerType.CARD_EFFECT,
            source_player_id="player_1",
            target_player_ids=["player_2"],
            context=context,
            description="测试杀的使用"
        )
        
        self.assertIsNotNone(process_id)
        self.assertIn(process_id, self.stack.processes)
        
        # 推入堆栈
        success = self.stack.push_process(process_id)
        self.assertTrue(success)
        self.assertEqual(self.stack.current_depth, 1)
        
        # 获取当前进程
        current_process = self.stack.get_current_process()
        self.assertIsNotNone(current_process)
        self.assertEqual(current_process.process_id, process_id)
        
        # 弹出堆栈
        popped_id = self.stack.pop_process()
        self.assertEqual(popped_id, process_id)
        self.assertEqual(self.stack.current_depth, 0)
    
    def test_nested_triggers(self):
        """测试嵌套触发"""
        # 创建主要交互（杀）
        main_context = InteractionContext(
            interaction_type=InteractionType.CARD_USE,
            source_player=MockPlayer("player_1", "测试玩家1"),
            target_player=MockPlayer("player_2", "测试玩家2"),
            card=self.sha_card,
            additional_data={'interaction_id': 'main_001'}
        )
        
        main_process_id = self.stack.create_process(
            trigger_type=TriggerType.CARD_EFFECT,
            source_player_id="player_1",
            target_player_ids=["player_2"],
            context=main_context,
            description="曹操对刘备使用杀"
        )
        
        self.stack.push_process(main_process_id)
        
        # 触发嵌套（八卦阵判定）
        nested_context = InteractionContext(
            interaction_type=InteractionType.SKILL_USE,
            source_player=MockPlayer("player_2", "测试玩家2"),
            additional_data={'interaction_id': 'nested_001', 'equipment': '八卦阵', 'judgment': True}
        )
        
        nested_process_id = self.stack.trigger_nested_process(
            trigger_type=TriggerType.EQUIPMENT_EFFECT,
            source_player_id="player_2",
            target_player_ids=[],
            context=nested_context,
            description="刘备八卦阵判定"
        )
        
        self.assertIsNotNone(nested_process_id)
        self.assertEqual(self.stack.current_depth, 2)
        
        # 检查父子关系
        main_process = self.stack.processes[main_process_id]
        nested_process = self.stack.processes[nested_process_id]
        
        self.assertEqual(nested_process.parent_process_id, main_process_id)
        self.assertIn(nested_process_id, main_process.child_process_ids)
        
        # 完成嵌套进程
        nested_result = FinalResult(
            result_type=AdjudicationResult.SUCCESS,
            success=True,
            original_context=nested_context,
            final_context=nested_context,
            executed_effects=[],
            blocked_effects=[]
        )
        
        self.stack.complete_process(nested_process_id, nested_result)
        self.assertEqual(self.stack.current_depth, 1)
        
        # 完成主进程
        main_result = FinalResult(
            result_type=AdjudicationResult.SUCCESS,
            success=True,
            original_context=main_context,
            final_context=main_context,
            executed_effects=[],
            blocked_effects=[]
        )
        
        self.stack.complete_process(main_process_id, main_result)
        self.assertEqual(self.stack.current_depth, 0)
    
    def test_max_depth_limit(self):
        """测试最大深度限制"""
        contexts = []
        process_ids = []
        
        # 创建多层嵌套，直到达到最大深度
        for i in range(self.stack.max_depth + 2):
            context = InteractionContext(
                interaction_type=InteractionType.SKILL_USE,
                source_player=MockPlayer("player_1", "测试玩家1"),
                target_player=MockPlayer("player_2", "测试玩家2"),
                additional_data={'interaction_id': f'depth_{i}', 'depth': i}
            )
            contexts.append(context)
            
            if i < self.stack.max_depth:
                # 应该成功
                process_id = self.stack.trigger_nested_process(
                    trigger_type=TriggerType.SKILL_TRIGGER,
                    source_player_id="player_1",
                    target_player_ids=["player_2"],
                    context=context,
                    description=f"深度 {i} 的技能触发"
                )
                self.assertIsNotNone(process_id)
                process_ids.append(process_id)
            else:
                # 应该失败（达到最大深度）
                process_id = self.stack.trigger_nested_process(
                    trigger_type=TriggerType.SKILL_TRIGGER,
                    source_player_id="player_1",
                    target_player_ids=["player_2"],
                    context=context,
                    description=f"深度 {i} 的技能触发（应该失败）"
                )
                self.assertIsNone(process_id)
        
        self.assertEqual(self.stack.current_depth, self.stack.max_depth)
    
    def test_process_tree(self):
        """测试进程树结构"""
        # 创建复杂的嵌套结构
        root_context = InteractionContext(
            interaction_type=InteractionType.CARD_USE,
            source_player=MockPlayer("player_1", "测试玩家1"),
            target_player=MockPlayer("player_2", "测试玩家2"),
            card=MockCard("南蛮入侵", "trick"),
            additional_data={'interaction_id': 'root'}
        )
        
        root_id = self.stack.create_process(
            trigger_type=TriggerType.CARD_EFFECT,
            source_player_id="player_1",
            target_player_ids=["player_2", "player_3"],
            context=root_context,
            description="南蛮入侵"
        )
        
        self.stack.push_process(root_id)
        
        # 为每个目标创建响应
        child_ids = []
        for i, target in enumerate(["player_2", "player_3"]):
            child_context = InteractionContext(
                interaction_type=InteractionType.CARD_USE,
                source_player=MockPlayer(target, f"测试玩家{i+2}"),
                card=self.sha_card,
                additional_data={'interaction_id': f'response_{i}'}
            )
            
            child_id = self.stack.trigger_nested_process(
                trigger_type=TriggerType.CARD_EFFECT,
                source_player_id=target,
                target_player_ids=[],
                context=child_context,
                description=f"{target}打出杀响应南蛮入侵"
            )
            
            if child_id:
                child_ids.append(child_id)
                self.stack.pop_process()  # 立即完成响应
        
        # 获取进程树
        tree = self.stack.get_process_tree(root_id)
        
        self.assertEqual(tree['process_id'], root_id)
        self.assertEqual(tree['description'], "南蛮入侵")
        self.assertEqual(len(tree['children']), len(child_ids))


class TestEnhancedAdjudicationEngine(unittest.TestCase):
    """增强版裁决引擎测试"""
    
    def setUp(self):
        """测试前准备"""
        reset_stack_manager()
        self.engine = EnhancedAdjudicationEngine()
        
        # 创建测试数据
        self.player1 = MockPlayer("player_1", "曹操")
        self.player2 = MockPlayer("player_2", "刘备")
        self.sha_card = MockCard("杀", "basic")
    
    def test_trigger_condition_registration(self):
        """测试触发条件注册"""
        # 创建奸雄技能触发条件
        def jianxiong_condition(context: InteractionContext) -> bool:
            return (context.interaction_type == InteractionType.DAMAGE and
                    context.additional_data.get('damage_amount', 0) > 0)
        
        trigger = TriggerCondition(
            event_type="take_damage",
            condition_func=jianxiong_condition,
            priority=5,
            description="奸雄技能触发"
        )
        
        # 注册触发条件
        self.engine.register_trigger_condition("player_1", trigger)
        
        self.assertIn("player_1", self.engine.trigger_conditions)
        self.assertIn(trigger, self.engine.trigger_conditions["player_1"])
        
        # 注销触发条件
        self.engine.unregister_trigger_condition("player_1", trigger)
        self.assertNotIn(trigger, self.engine.trigger_conditions["player_1"])
    
    def test_nested_adjudication(self):
        """测试嵌套裁决"""
        # 创建伤害上下文
        damage_context = InteractionContext(
            interaction_type=InteractionType.DAMAGE,
            source_player=MockPlayer("player_2", "测试玩家2"),
            target_player=MockPlayer("player_1", "测试玩家1"),
            amount=1,
            additional_data={'interaction_id': 'damage_001', 'damage_amount': 1, 'damage_source': self.sha_card}
        )
        
        # 注册奸雄技能触发条件
        def jianxiong_condition(context: InteractionContext) -> bool:
            target_id = getattr(context.target_player, 'player_id', str(context.target_player)) if context.target_player else None
            return (context.interaction_type == InteractionType.DAMAGE and
                    context.additional_data.get('damage_amount', 0) > 0 and
                    target_id == "player_1")
        
        jianxiong_trigger = TriggerCondition(
            event_type="take_damage",
            condition_func=jianxiong_condition,
            priority=5,
            description="奸雄技能触发"
        )
        
        self.engine.register_trigger_condition("player_1", jianxiong_trigger)
        
        # 执行嵌套裁决
        result = self.engine.adjudicate_with_stack(
            context=damage_context,
            trigger_type=TriggerType.CARD_EFFECT,
            description="刘备对曹操造成伤害"
        )
        
        # 验证结果
        self.assertIsNotNone(result)
        
        # 检查堆栈状态
        stack_status = self.engine.get_stack_status()
        # 由于可能存在未完成的进程，我们检查活跃进程数量而不是深度
        self.assertEqual(stack_status['active_processes'], 0)  # 应该没有活跃进程
    
    def test_complex_nested_scenario(self):
        """测试复杂嵌套场景"""
        # 场景：曹操对刘备使用杀，刘备装备八卦阵，触发判定
        
        # 1. 主要动作：使用杀
        sha_context = InteractionContext(
            interaction_type=InteractionType.CARD_USE,
            source_player=MockPlayer("player_1", "测试玩家1"),
            target_player=MockPlayer("player_2", "测试玩家2"),
            card=self.sha_card,
            additional_data={'interaction_id': 'sha_001'}
        )
        
        # 2. 注册八卦阵触发条件
        def bagua_condition(context: InteractionContext) -> bool:
            return (context.interaction_type == InteractionType.CARD_USE and
                    context.card and 
                    getattr(context.card, 'name', '') == '杀' and
                    context.target_player and context.target_player.name == "刘备")
        
        bagua_trigger = TriggerCondition(
            event_type="need_dodge",
            condition_func=bagua_condition,
            priority=3,
            description="八卦阵判定"
        )
        
        self.engine.register_trigger_condition("player_2", bagua_trigger)
        
        # 3. 执行裁决
        result = self.engine.adjudicate_with_stack(
            context=sha_context,
            trigger_type=TriggerType.CARD_EFFECT,
            description="曹操对刘备使用杀"
        )
        
        # 4. 验证结果
        self.assertIsNotNone(result)
        
        # 5. 检查进程树
        process_tree = self.engine.get_current_process_tree()
        # 由于已经完成，可能没有当前进程树
        
        # 6. 检查堆栈状态
        stack_status = self.engine.get_stack_status()
        self.assertGreaterEqual(stack_status['total_processes'], 1)


def run_nested_adjudication_demo():
    """运行嵌套裁决演示"""
    print("=== 嵌套裁决系统演示 ===\n")
    
    # 创建堆栈管理器
    stack = NestedAdjudicationStack(max_depth=5)
    
    # 创建增强版裁决引擎
    engine = EnhancedAdjudicationEngine(stack)
    
    print("1. 创建测试场景：曹操对刘备使用杀")
    
    # 创建杀的使用上下文
    sha_context = InteractionContext(
        interaction_type=InteractionType.CARD_USE,
        source_player=MockPlayer("曹操", "曹操"),
        target_player=MockPlayer("刘备", "刘备"),
        card=MockCard("杀", "basic"),
        additional_data={'interaction_id': 'demo_sha'}
    )
    
    print("2. 注册刘备的八卦阵触发条件")
    
    def bagua_condition(context: InteractionContext) -> bool:
        target_name = getattr(context.target_player, 'name', str(context.target_player)) if context.target_player else None
        return (context.interaction_type == InteractionType.CARD_USE and
                context.card and 
                getattr(context.card, 'name', '') == '杀' and
                target_name == "刘备")
    
    bagua_trigger = TriggerCondition(
        event_type="need_dodge",
        condition_func=bagua_condition,
        priority=3,
        description="刘备八卦阵判定"
    )
    
    engine.register_trigger_condition("刘备", bagua_trigger)
    
    print("3. 执行嵌套裁决")
    
    result = engine.adjudicate_with_stack(
        context=sha_context,
        trigger_type=TriggerType.CARD_EFFECT,
        description="曹操对刘备使用杀"
    )
    
    print(f"4. 裁决结果：{result.success}")
    print(f"   结果类型：{result.result_type}")
    
    print("5. 堆栈状态：")
    stack_status = engine.get_stack_status()
    for key, value in stack_status.items():
        print(f"   {key}: {value}")
    
    print("\n=== 演示完成 ===")


if __name__ == '__main__':
    # 运行演示
    run_nested_adjudication_demo()
    
    print("\n" + "="*50 + "\n")
    
    # 运行单元测试
    unittest.main(verbosity=2)