#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
三国杀通用交互模型
实现"判断-修正-裁决"三阶段交互机制
"""

from abc import ABC, abstractmethod
from enum import Enum
from typing import List, Dict, Any, Optional, Callable
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


class InteractionType(Enum):
    """交互类型"""
    CARD_USE = "card_use"           # 使用卡牌
    CARD_PLAY = "card_play"         # 打出卡牌
    SKILL_TRIGGER = "skill_trigger" # 技能触发
    SKILL_USE = "skill_use"         # 主动使用技能
    DAMAGE = "damage"               # 造成伤害
    HEAL = "heal"                   # 回复体力
    DRAW_CARD = "draw_card"         # 摸牌
    DISCARD_CARD = "discard_card"   # 弃牌


class InteractionResult(Enum):
    """交互结果"""
    SUCCESS = "success"             # 成功执行
    FAILED = "failed"               # 执行失败
    CANCELLED = "cancelled"         # 被取消
    MODIFIED = "modified"           # 被修正


class ResponseType(Enum):
    """响应类型"""
    DODGE = "dodge"                 # 闪避
    COUNTER = "counter"             # 反击
    NULLIFY = "nullify"             # 无效化
    ENHANCE = "enhance"             # 增强
    REDUCE = "reduce"               # 减少
    REDIRECT = "redirect"           # 重定向
    SKILL_RESPONSE = "skill_response"  # 技能响应


@dataclass
class InteractionContext:
    """交互上下文"""
    interaction_type: InteractionType
    source_player: Any  # 发起者
    target_player: Optional[Any] = None  # 目标玩家
    card: Optional[Any] = None  # 相关卡牌
    skill: Optional[Any] = None  # 相关技能
    amount: int = 0  # 数值（如伤害值、摸牌数等）
    additional_data: Dict[str, Any] = None  # 额外数据
    
    def __post_init__(self):
        if self.additional_data is None:
            self.additional_data = {}


@dataclass
class InteractionResponse:
    """交互响应"""
    responder: Any  # 响应者
    response_type: str  # 响应类型
    card: Optional[Any] = None  # 响应卡牌
    skill: Optional[Any] = None  # 响应技能
    data: Dict[str, Any] = None  # 响应数据
    
    def __post_init__(self):
        if self.data is None:
            self.data = {}


class InteractionPhase(ABC):
    """交互阶段抽象基类"""
    
    @abstractmethod
    def execute(self, context: InteractionContext) -> bool:
        """执行阶段逻辑"""
        pass


class JudgmentPhase(InteractionPhase):
    """判断阶段：检查是否可以执行"""
    
    def __init__(self):
        self.conditions: List[Callable[[InteractionContext], bool]] = []
    
    def add_condition(self, condition: Callable[[InteractionContext], bool]):
        """添加判断条件"""
        self.conditions.append(condition)
    
    def execute(self, context: InteractionContext) -> bool:
        """执行判断阶段"""
        logger.debug(f"执行判断阶段: {context.interaction_type}")
        
        # 检查所有条件
        for condition in self.conditions:
            if not condition(context):
                logger.debug(f"判断条件失败: {condition.__name__}")
                return False
        
        logger.debug("所有判断条件通过")
        return True


class ModificationPhase(InteractionPhase):
    """修正阶段：处理响应和修正"""
    
    def __init__(self):
        self.response_handlers: Dict[str, Callable[[InteractionContext, InteractionResponse], InteractionContext]] = {}
    
    def add_response_handler(self, response_type: str, handler: Callable[[InteractionContext, InteractionResponse], InteractionContext]):
        """添加响应处理器"""
        self.response_handlers[response_type] = handler
    
    def execute(self, context: InteractionContext) -> bool:
        """执行修正阶段"""
        logger.debug(f"执行修正阶段: {context.interaction_type}")
        
        # 收集所有可能的响应
        responses = self._collect_responses(context)
        
        # 处理每个响应
        for response in responses:
            if response.response_type in self.response_handlers:
                handler = self.response_handlers[response.response_type]
                context = handler(context, response)
                logger.debug(f"处理响应: {response.response_type}")
        
        return True
    
    def _collect_responses(self, context: InteractionContext) -> List[InteractionResponse]:
        """收集响应（这里需要根据具体游戏逻辑实现）"""
        responses = []
        
        # 示例：如果是使用杀，检查目标是否有闪
        if context.interaction_type == InteractionType.CARD_USE and context.card and context.card.name == "杀":
            if context.target_player and hasattr(context.target_player, 'has_card_type'):
                if context.target_player.has_card_type("闪"):
                    # 这里应该询问玩家是否使用闪
                    # 简化处理，假设玩家选择使用
                    flash_card = context.target_player.get_card_by_name("闪")
                    if flash_card:
                        responses.append(InteractionResponse(
                            responder=context.target_player,
                            response_type="dodge",
                            card=flash_card
                        ))
        
        return responses


class ResolutionPhase(InteractionPhase):
    """裁决阶段：计算最终结果"""
    
    def __init__(self):
        self.resolution_handlers: Dict[InteractionType, Callable[[InteractionContext], InteractionResult]] = {}
    
    def add_resolution_handler(self, interaction_type: InteractionType, handler: Callable[[InteractionContext], InteractionResult]):
        """添加裁决处理器"""
        self.resolution_handlers[interaction_type] = handler
    
    def execute(self, context: InteractionContext) -> bool:
        """执行裁决阶段"""
        logger.debug(f"执行裁决阶段: {context.interaction_type}")
        
        if context.interaction_type in self.resolution_handlers:
            handler = self.resolution_handlers[context.interaction_type]
            result = handler(context)
            context.additional_data['result'] = result
            logger.debug(f"裁决结果: {result}")
            return result == InteractionResult.SUCCESS
        
        logger.warning(f"未找到裁决处理器: {context.interaction_type}")
        return False


class InteractionEngine:
    """交互引擎：管理整个交互流程"""
    
    def __init__(self):
        self.judgment_phase = JudgmentPhase()
        self.modification_phase = ModificationPhase()
        self.resolution_phase = ResolutionPhase()
        self.event_listeners: Dict[str, List[Callable]] = {}
    
    def add_event_listener(self, event_name: str, listener: Callable):
        """添加事件监听器"""
        if event_name not in self.event_listeners:
            self.event_listeners[event_name] = []
        self.event_listeners[event_name].append(listener)
    
    def trigger_event(self, event_name: str, data: Any = None):
        """触发事件"""
        if event_name in self.event_listeners:
            for listener in self.event_listeners[event_name]:
                listener(data)
    
    def process_interaction(self, context: InteractionContext) -> InteractionResult:
        """处理交互流程"""
        logger.info(f"开始处理交互: {context.interaction_type}")
        
        try:
            # 阶段1: 判断
            self.trigger_event("before_judgment", context)
            if not self.judgment_phase.execute(context):
                logger.info("判断阶段失败")
                return InteractionResult.FAILED
            self.trigger_event("after_judgment", context)
            
            # 阶段2: 修正
            self.trigger_event("before_modification", context)
            if not self.modification_phase.execute(context):
                logger.info("修正阶段失败")
                return InteractionResult.FAILED
            self.trigger_event("after_modification", context)
            
            # 阶段3: 裁决
            self.trigger_event("before_resolution", context)
            if not self.resolution_phase.execute(context):
                logger.info("裁决阶段失败")
                return InteractionResult.FAILED
            self.trigger_event("after_resolution", context)
            
            result = context.additional_data.get('result', InteractionResult.SUCCESS)
            logger.info(f"交互处理完成: {result}")
            return result
            
        except Exception as e:
            logger.error(f"交互处理异常: {e}")
            return InteractionResult.FAILED


# 预定义的常用判断条件
class CommonConditions:
    """常用判断条件"""
    
    @staticmethod
    def has_card(context: InteractionContext) -> bool:
        """检查是否有指定卡牌"""
        if context.card and context.source_player:
            return hasattr(context.source_player, 'has_card') and context.source_player.has_card(context.card)
        return True
    
    @staticmethod
    def in_range(context: InteractionContext) -> bool:
        """检查是否在攻击范围内"""
        if context.target_player and context.source_player:
            return hasattr(context.source_player, 'can_attack') and context.source_player.can_attack(context.target_player)
        return True
    
    @staticmethod
    def not_self_target(context: InteractionContext) -> bool:
        """检查目标不是自己"""
        if context.target_player and context.source_player:
            return context.target_player != context.source_player
        return True
    
    @staticmethod
    def alive_target(context: InteractionContext) -> bool:
        """检查目标是否存活"""
        if context.target_player:
            return hasattr(context.target_player, 'is_alive') and context.target_player.is_alive()
        return True


# 预定义的常用裁决处理器
class CommonResolutions:
    """常用裁决处理器"""
    
    @staticmethod
    def card_use_resolution(context: InteractionContext) -> InteractionResult:
        """卡牌使用裁决"""
        if context.card and context.source_player:
            # 从手牌中移除卡牌
            if hasattr(context.source_player, 'remove_card'):
                context.source_player.remove_card(context.card)
            
            # 执行卡牌效果
            if hasattr(context.card, 'execute_effect'):
                context.card.execute_effect(context)
            
            return InteractionResult.SUCCESS
        return InteractionResult.FAILED
    
    @staticmethod
    def damage_resolution(context: InteractionContext) -> InteractionResult:
        """伤害裁决"""
        if context.target_player and context.amount > 0:
            if hasattr(context.target_player, 'take_damage'):
                context.target_player.take_damage(context.amount)
                return InteractionResult.SUCCESS
        return InteractionResult.FAILED
    
    @staticmethod
    def heal_resolution(context: InteractionContext) -> InteractionResult:
        """回复裁决"""
        if context.target_player and context.amount > 0:
            if hasattr(context.target_player, 'heal'):
                context.target_player.heal(context.amount)
                return InteractionResult.SUCCESS
        return InteractionResult.FAILED