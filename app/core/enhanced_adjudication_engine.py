#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
增强版裁决引擎
集成嵌套裁决堆栈系统，支持复杂的卡牌和技能嵌套触发
"""

from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass
import logging
from .adjudication_engine import AdjudicationEngine, FinalResult, AdjudicationResult
from .nested_adjudication_stack import (
    NestedAdjudicationStack, AdjudicationProcess, TriggerType, 
    AdjudicationStatus, get_stack_manager
)
from .interaction_model import InteractionContext, InteractionType
from .modification_handlers import ModificationResult

logger = logging.getLogger(__name__)


@dataclass
class TriggerCondition:
    """触发条件"""
    event_type: str
    condition_func: Callable[[InteractionContext], bool]
    priority: int = 0
    description: str = ""


class EnhancedAdjudicationEngine(AdjudicationEngine):
    """增强版裁决引擎，支持嵌套触发"""
    
    def __init__(self, stack_manager: Optional[NestedAdjudicationStack] = None):
        super().__init__()
        self.stack_manager = stack_manager or get_stack_manager()
        
        # 触发条件注册表
        self.trigger_conditions: Dict[str, List[TriggerCondition]] = {}
        
        # 响应处理器
        self.response_handlers: Dict[str, Callable] = {}
        
        # 初始化默认触发条件
        self._register_default_triggers()
        
        logger.info("初始化增强版裁决引擎")
    
    def register_trigger_condition(self, 
                                 player_id: str,
                                 condition: TriggerCondition):
        """注册触发条件"""
        if player_id not in self.trigger_conditions:
            self.trigger_conditions[player_id] = []
        
        self.trigger_conditions[player_id].append(condition)
        logger.info(f"为玩家 {player_id} 注册触发条件: {condition.description}")
    
    def unregister_trigger_condition(self, 
                                   player_id: str, 
                                   condition: TriggerCondition):
        """注销触发条件"""
        if player_id in self.trigger_conditions:
            if condition in self.trigger_conditions[player_id]:
                self.trigger_conditions[player_id].remove(condition)
                logger.info(f"为玩家 {player_id} 注销触发条件: {condition.description}")
    
    def adjudicate_with_stack(self, 
                            context: InteractionContext,
                            trigger_type: TriggerType = TriggerType.CARD_EFFECT,
                            description: str = "") -> FinalResult:
        """使用堆栈系统进行裁决"""
        
        # 创建裁决过程
        process_id = self.stack_manager.create_process(
            trigger_type=trigger_type,
            source_player_id=getattr(context.source_player, 'player_id', str(context.source_player)),
            target_player_ids=[getattr(context.target_player, 'player_id', str(context.target_player))] if context.target_player else [],
            context=context,
            description=description
        )
        
        # 推入堆栈
        if not self.stack_manager.push_process(process_id):
            logger.error(f"无法推入裁决过程: {process_id}")
            return self._create_failed_result(context, "无法推入裁决堆栈")
        
        try:
            # 检查嵌套触发
            nested_triggers = self._check_nested_triggers(context)
            
            # 处理嵌套触发
            for trigger_context, trigger_desc in nested_triggers:
                self._handle_nested_trigger(trigger_context, trigger_desc)
            
            # 执行原始裁决
            modifications = self._collect_modifications(context)
            result = self.adjudicate(context, modifications)
            
            # 完成裁决过程
            self.stack_manager.complete_process(process_id, result)
            
            return result
            
        except Exception as e:
            logger.error(f"裁决过程异常: {e}")
            self.stack_manager.cancel_process(process_id, f"异常: {str(e)}")
            return self._create_failed_result(context, f"裁决异常: {str(e)}")
    
    def _check_nested_triggers(self, context: InteractionContext) -> List[tuple]:
        """检查是否有嵌套触发"""
        nested_triggers = []
        
        # 检查所有玩家的触发条件
        for player_id, conditions in self.trigger_conditions.items():
            for condition in conditions:
                if condition.condition_func(context):
                    # 创建嵌套触发上下文
                    nested_context = self._create_nested_context(context, player_id, condition)
                    nested_triggers.append((nested_context, condition.description))
        
        # 按优先级排序
        nested_triggers.sort(key=lambda x: x[0].additional_data.get('priority', 0), reverse=True)
        
        return nested_triggers
    
    def _create_nested_context(self, 
                             original_context: InteractionContext,
                             player_id: str,
                             condition: TriggerCondition) -> InteractionContext:
        """创建嵌套触发上下文"""
        return InteractionContext(
            interaction_id=f"nested_{original_context.interaction_id}",
            source_player=player_id,
            target_player=original_context.target_player,
            interaction_type=InteractionType.SKILL_USE,  # 假设是技能触发
            additional_data={
                'original_context': original_context,
                'trigger_condition': condition,
                'priority': condition.priority,
                'nested_trigger': True
            }
        )
    
    def _handle_nested_trigger(self, context: InteractionContext, description: str):
        """处理嵌套触发"""
        if not self.stack_manager.can_trigger_nested(TriggerType.SKILL_TRIGGER):
            logger.warning(f"无法触发嵌套: {description}")
            return
        
        # 触发嵌套过程
        nested_process_id = self.stack_manager.trigger_nested_process(
            trigger_type=TriggerType.SKILL_TRIGGER,
            source_player_id=getattr(context.source_player, 'player_id', str(context.source_player)),
            target_player_ids=[getattr(context.target_player, 'player_id', str(context.target_player))] if context.target_player else [],
            context=context,
            priority=context.additional_data.get('priority', 0),
            description=description
        )
        
        if nested_process_id:
            # 执行嵌套裁决
            try:
                modifications = self._collect_modifications(context)
                result = self.adjudicate(context, modifications)
                self.stack_manager.complete_process(nested_process_id, result)
                
            except Exception as e:
                logger.error(f"嵌套触发异常: {e}")
                self.stack_manager.cancel_process(nested_process_id, f"异常: {str(e)}")
    
    def _collect_modifications(self, context: InteractionContext) -> List[ModificationResult]:
        """收集修正结果（简化实现）"""
        # 这里应该调用修正处理器来收集所有相关的修正
        # 暂时返回空列表
        return []
    
    def _create_failed_result(self, context: InteractionContext, reason: str) -> FinalResult:
        """创建失败结果"""
        return FinalResult(
            result_type=AdjudicationResult.FAILED,
            success=False,
            original_context=context,
            final_context=context,
            executed_effects=[],
            blocked_effects=[],
            additional_info={'failure_reason': reason}
        )
    
    def _register_default_triggers(self):
        """注册默认的触发条件"""
        
        # 示例：奸雄技能触发条件
        def jianxiong_condition(context: InteractionContext) -> bool:
            """奸雄技能触发条件：受到伤害时"""
            return (context.interaction_type == InteractionType.DAMAGE and
                    context.additional_data.get('damage_amount', 0) > 0)
        
        jianxiong_trigger = TriggerCondition(
            event_type="take_damage",
            condition_func=jianxiong_condition,
            priority=5,
            description="奸雄技能触发"
        )
        
        # 示例：八卦阵触发条件
        def bagua_condition(context: InteractionContext) -> bool:
            """八卦阵触发条件：需要闪时"""
            return (context.interaction_type == InteractionType.CARD_USE and
                    context.card and 
                    getattr(context.card, 'name', '') == '杀')
        
        bagua_trigger = TriggerCondition(
            event_type="need_dodge",
            condition_func=bagua_condition,
            priority=3,
            description="八卦阵判定"
        )
        
        # 这些触发条件会在实际游戏中根据玩家的武将和装备动态注册
        logger.info("注册了默认触发条件")
    
    def get_stack_status(self) -> Dict[str, Any]:
        """获取堆栈状态"""
        return self.stack_manager.get_execution_summary()
    
    def get_current_process_tree(self) -> Optional[Dict[str, Any]]:
        """获取当前进程树"""
        current_process = self.stack_manager.get_current_process()
        if not current_process:
            return None
        
        # 找到根进程
        root_process = current_process
        while root_process.parent_process_id:
            parent = self.stack_manager.processes.get(root_process.parent_process_id)
            if parent:
                root_process = parent
            else:
                break
        
        return self.stack_manager.get_process_tree(root_process.process_id)
    
    def force_clear_stack(self, reason: str = "强制清理"):
        """强制清理堆栈（紧急情况使用）"""
        logger.warning(f"强制清理裁决堆栈: {reason}")
        
        # 取消所有进行中的进程
        for process_id, process in self.stack_manager.processes.items():
            if process.status in [AdjudicationStatus.PROCESSING, AdjudicationStatus.WAITING_RESPONSE]:
                self.stack_manager.cancel_process(process_id, reason)
        
        # 清空执行堆栈
        self.stack_manager.execution_stack.clear()
        self.stack_manager.current_depth = 0
        self.stack_manager.is_processing = False


# 便利函数
def create_enhanced_engine() -> EnhancedAdjudicationEngine:
    """创建增强版裁决引擎实例"""
    return EnhancedAdjudicationEngine()

def adjudicate_with_nesting(context: InteractionContext, 
                          trigger_type: TriggerType = TriggerType.CARD_EFFECT,
                          description: str = "") -> FinalResult:
    """使用全局引擎进行嵌套裁决"""
    engine = create_enhanced_engine()
    return engine.adjudicate_with_stack(context, trigger_type, description)