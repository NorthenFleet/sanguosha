#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
嵌套裁决堆栈系统
处理卡牌和技能的嵌套触发，确保正确的执行顺序和上下文保持
"""

from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, field
from enum import Enum
from uuid import uuid4
import time
import logging
from .interaction_model import InteractionContext
from .adjudication_engine import FinalResult, AdjudicationResult

logger = logging.getLogger(__name__)


class AdjudicationStatus(Enum):
    """裁决状态"""
    PENDING = "pending"           # 等待处理
    PROCESSING = "processing"     # 正在处理
    WAITING_RESPONSE = "waiting_response"  # 等待响应
    COMPLETED = "completed"       # 已完成
    CANCELLED = "cancelled"       # 已取消
    BLOCKED = "blocked"          # 被阻止


class TriggerType(Enum):
    """触发类型"""
    CARD_EFFECT = "card_effect"           # 卡牌效果
    SKILL_TRIGGER = "skill_trigger"       # 技能触发
    EQUIPMENT_EFFECT = "equipment_effect" # 装备效果
    PASSIVE_SKILL = "passive_skill"       # 被动技能
    COUNTER_EFFECT = "counter_effect"     # 反制效果
    CHAIN_REACTION = "chain_reaction"     # 连锁反应


@dataclass
class AdjudicationProcess:
    """单个裁决过程记录"""
    process_id: str = field(default_factory=lambda: str(uuid4()))
    trigger_type: TriggerType = TriggerType.CARD_EFFECT
    source_player_id: str = ""
    target_player_ids: List[str] = field(default_factory=list)
    
    # 核心数据
    original_context: Optional[InteractionContext] = None
    current_context: Optional[InteractionContext] = None
    final_result: Optional[FinalResult] = None
    
    # 状态管理
    status: AdjudicationStatus = AdjudicationStatus.PENDING
    priority: int = 0  # 优先级，数值越大优先级越高
    
    # 嵌套关系
    parent_process_id: Optional[str] = None
    child_process_ids: List[str] = field(default_factory=list)
    
    # 时间戳
    created_at: float = field(default_factory=time.time)
    started_at: Optional[float] = None
    completed_at: Optional[float] = None
    
    # 附加信息
    description: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        if not self.process_id:
            self.process_id = str(uuid4())


@dataclass
class StackFrame:
    """堆栈帧 - 表示当前正在处理的裁决层级"""
    process_id: str
    depth: int  # 嵌套深度
    waiting_for: List[str] = field(default_factory=list)  # 等待的子进程ID
    can_interrupt: bool = True  # 是否可以被中断


class NestedAdjudicationStack:
    """嵌套裁决堆栈管理器"""
    
    def __init__(self, max_depth: int = 10):
        # 核心数据结构
        self.processes: Dict[str, AdjudicationProcess] = {}  # 所有裁决过程
        self.execution_stack: List[StackFrame] = []  # 执行堆栈
        
        # 配置
        self.max_depth = max_depth
        self.current_depth = 0
        
        # 状态管理
        self.is_processing = False
        self.processing_queue: List[str] = []  # 待处理队列
        
        logger.info(f"初始化嵌套裁决堆栈，最大深度: {max_depth}")
    
    def create_process(self, 
                      trigger_type: TriggerType,
                      source_player_id: str,
                      target_player_ids: List[str],
                      context: InteractionContext,
                      priority: int = 0,
                      parent_process_id: Optional[str] = None,
                      description: str = "") -> str:
        """创建新的裁决过程"""
        
        process = AdjudicationProcess(
            trigger_type=trigger_type,
            source_player_id=source_player_id,
            target_player_ids=target_player_ids,
            original_context=context,
            current_context=context,
            priority=priority,
            parent_process_id=parent_process_id,
            description=description
        )
        
        # 存储过程
        self.processes[process.process_id] = process
        
        # 建立父子关系
        if parent_process_id and parent_process_id in self.processes:
            self.processes[parent_process_id].child_process_ids.append(process.process_id)
        
        logger.info(f"创建裁决过程: {process.process_id} - {description}")
        return process.process_id
    
    def push_process(self, process_id: str) -> bool:
        """将裁决过程推入执行堆栈"""
        if process_id not in self.processes:
            logger.error(f"裁决过程不存在: {process_id}")
            return False
        
        if self.current_depth >= self.max_depth:
            logger.error(f"达到最大嵌套深度: {self.max_depth}")
            return False
        
        process = self.processes[process_id]
        
        # 创建堆栈帧
        frame = StackFrame(
            process_id=process_id,
            depth=self.current_depth
        )
        
        self.execution_stack.append(frame)
        self.current_depth += 1
        
        # 更新进程状态
        process.status = AdjudicationStatus.PROCESSING
        process.started_at = time.time()
        
        logger.info(f"推入堆栈: {process_id}, 深度: {self.current_depth}")
        return True
    
    def pop_process(self) -> Optional[str]:
        """从执行堆栈弹出裁决过程"""
        if not self.execution_stack:
            return None
        
        frame = self.execution_stack.pop()
        self.current_depth -= 1
        
        process = self.processes[frame.process_id]
        process.status = AdjudicationStatus.COMPLETED
        process.completed_at = time.time()
        
        logger.info(f"弹出堆栈: {frame.process_id}, 深度: {self.current_depth}")
        return frame.process_id
    
    def get_current_process(self) -> Optional[AdjudicationProcess]:
        """获取当前正在处理的裁决过程"""
        if not self.execution_stack:
            return None
        
        current_frame = self.execution_stack[-1]
        return self.processes.get(current_frame.process_id)
    
    def can_trigger_nested(self, trigger_type: TriggerType, priority: int = 0) -> bool:
        """检查是否可以触发嵌套裁决"""
        # 检查深度限制
        if self.current_depth >= self.max_depth:
            return False
        
        # 检查当前进程是否允许中断
        current_process = self.get_current_process()
        if current_process:
            current_frame = self.execution_stack[-1]
            if not current_frame.can_interrupt:
                return False
        
        return True
    
    def trigger_nested_process(self,
                             trigger_type: TriggerType,
                             source_player_id: str,
                             target_player_ids: List[str],
                             context: InteractionContext,
                             priority: int = 0,
                             description: str = "") -> Optional[str]:
        """触发嵌套裁决过程"""
        
        if not self.can_trigger_nested(trigger_type, priority):
            logger.warning(f"无法触发嵌套裁决: {description}")
            return None
        
        # 获取父进程ID
        parent_process_id = None
        if self.execution_stack:
            parent_process_id = self.execution_stack[-1].process_id
        
        # 创建新进程
        process_id = self.create_process(
            trigger_type=trigger_type,
            source_player_id=source_player_id,
            target_player_ids=target_player_ids,
            context=context,
            priority=priority,
            parent_process_id=parent_process_id,
            description=description
        )
        
        # 推入堆栈
        if self.push_process(process_id):
            return process_id
        
        return None
    
    def complete_process(self, process_id: str, result: FinalResult):
        """完成裁决过程"""
        if process_id not in self.processes:
            logger.error(f"裁决过程不存在: {process_id}")
            return
        
        process = self.processes[process_id]
        process.final_result = result
        process.status = AdjudicationStatus.COMPLETED
        process.completed_at = time.time()
        
        # 如果是当前栈顶进程，弹出堆栈
        if self.execution_stack and self.execution_stack[-1].process_id == process_id:
            self.pop_process()
        
        logger.info(f"完成裁决过程: {process_id}")
    
    def cancel_process(self, process_id: str, reason: str = ""):
        """取消裁决过程"""
        if process_id not in self.processes:
            return
        
        process = self.processes[process_id]
        process.status = AdjudicationStatus.CANCELLED
        process.metadata['cancel_reason'] = reason
        
        # 递归取消所有子进程
        for child_id in process.child_process_ids:
            self.cancel_process(child_id, f"父进程取消: {reason}")
        
        logger.info(f"取消裁决过程: {process_id} - {reason}")
    
    def get_process_tree(self, root_process_id: str) -> Dict[str, Any]:
        """获取进程树结构"""
        if root_process_id not in self.processes:
            return {}
        
        root_process = self.processes[root_process_id]
        
        tree = {
            'process_id': root_process_id,
            'description': root_process.description,
            'status': root_process.status.value,
            'trigger_type': root_process.trigger_type.value,
            'children': []
        }
        
        for child_id in root_process.child_process_ids:
            child_tree = self.get_process_tree(child_id)
            if child_tree:
                tree['children'].append(child_tree)
        
        return tree
    
    def get_execution_summary(self) -> Dict[str, Any]:
        """获取执行摘要"""
        return {
            'current_depth': self.current_depth,
            'max_depth': self.max_depth,
            'total_processes': len(self.processes),
            'active_processes': len([p for p in self.processes.values() 
                                   if p.status in [AdjudicationStatus.PROCESSING, AdjudicationStatus.WAITING_RESPONSE]]),
            'execution_stack': [frame.process_id for frame in self.execution_stack],
            'is_processing': self.is_processing
        }
    
    def clear_completed_processes(self, keep_recent: int = 100):
        """清理已完成的进程（保留最近的一些记录）"""
        completed_processes = [
            (pid, p) for pid, p in self.processes.items()
            if p.status in [AdjudicationStatus.COMPLETED, AdjudicationStatus.CANCELLED]
        ]
        
        # 按完成时间排序，保留最近的
        completed_processes.sort(key=lambda x: x[1].completed_at or 0, reverse=True)
        
        to_remove = completed_processes[keep_recent:]
        for pid, _ in to_remove:
            del self.processes[pid]
        
        logger.info(f"清理了 {len(to_remove)} 个已完成的进程")


# 全局堆栈管理器实例
_global_stack_manager: Optional[NestedAdjudicationStack] = None

def get_stack_manager() -> NestedAdjudicationStack:
    """获取全局堆栈管理器"""
    global _global_stack_manager
    if _global_stack_manager is None:
        _global_stack_manager = NestedAdjudicationStack()
    return _global_stack_manager

def reset_stack_manager():
    """重置全局堆栈管理器"""
    global _global_stack_manager
    _global_stack_manager = None