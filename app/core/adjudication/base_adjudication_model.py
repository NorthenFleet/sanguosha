#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
基础裁决流程模型
定义标准的三步裁决流程：判断条件 -> 查看修正 -> 裁决计算
支持数据驱动的配置和嵌套裁决
"""

from typing import Dict, List, Optional, Any, Callable, Union
from dataclasses import dataclass, field
from enum import Enum
from abc import ABC, abstractmethod
import logging

# 暂时使用Any类型代替InteractionContext，避免循环导入
InteractionContext = Any

logger = logging.getLogger(__name__)


class AdjudicationPhase(Enum):
    """裁决阶段"""
    JUDGMENT = "judgment"        # 判断条件阶段
    MODIFICATION = "modification"  # 查看修正阶段
    CALCULATION = "calculation"   # 裁决计算阶段


class AdjudicationStepResult(Enum):
    """裁决步骤结果"""
    CONTINUE = "continue"        # 继续下一步
    BLOCK = "block"             # 阻止执行
    TRIGGER_NESTED = "trigger_nested"  # 触发嵌套裁决
    COMPLETE = "complete"       # 直接完成


@dataclass
class AdjudicationData:
    """裁决数据容器"""
    # 基础数据
    context: InteractionContext
    phase: AdjudicationPhase
    step_results: Dict[AdjudicationPhase, Any] = field(default_factory=dict)
    
    # 判断条件数据
    judgment_conditions: List[str] = field(default_factory=list)
    judgment_results: Dict[str, bool] = field(default_factory=dict)
    
    # 修正数据
    modifications: List[Dict[str, Any]] = field(default_factory=list)
    modification_results: List[Any] = field(default_factory=list)
    
    # 计算数据
    calculation_inputs: Dict[str, Any] = field(default_factory=dict)
    calculation_outputs: Dict[str, Any] = field(default_factory=dict)
    
    # 嵌套裁决数据
    nested_triggers: List[Dict[str, Any]] = field(default_factory=list)
    nested_results: List[Any] = field(default_factory=list)
    
    # 元数据
    metadata: Dict[str, Any] = field(default_factory=dict)


class BaseAdjudicationStep(ABC):
    """基础裁决步骤抽象类"""
    
    def __init__(self, step_name: str, priority: int = 0):
        self.step_name = step_name
        self.priority = priority
    
    @abstractmethod
    def execute(self, data: AdjudicationData) -> AdjudicationStepResult:
        """执行裁决步骤"""
        pass
    
    def can_execute(self, data: AdjudicationData) -> bool:
        """检查是否可以执行"""
        return True
    
    def get_dependencies(self) -> List[str]:
        """获取依赖的步骤"""
        return []


class JudgmentStep(BaseAdjudicationStep):
    """判断条件步骤"""
    
    def __init__(self, condition_name: str, condition_func: Callable[[InteractionContext], bool], 
                 priority: int = 0, required: bool = True):
        super().__init__(f"judgment_{condition_name}", priority)
        self.condition_name = condition_name
        self.condition_func = condition_func
        self.required = required
    
    def execute(self, data: AdjudicationData) -> AdjudicationStepResult:
        """执行判断条件"""
        try:
            result = self.condition_func(data.context)
            data.judgment_results[self.condition_name] = result
            
            logger.debug(f"判断条件 {self.condition_name}: {result}")
            
            # 如果是必需条件且失败，则阻止执行
            if self.required and not result:
                logger.info(f"必需条件 {self.condition_name} 失败，阻止执行")
                return AdjudicationStepResult.BLOCK
            
            return AdjudicationStepResult.CONTINUE
            
        except Exception as e:
            logger.error(f"判断条件 {self.condition_name} 执行异常: {e}")
            if self.required:
                return AdjudicationStepResult.BLOCK
            return AdjudicationStepResult.CONTINUE


class ModificationStep(BaseAdjudicationStep):
    """修正步骤"""
    
    def __init__(self, modification_name: str, modification_func: Callable[[InteractionContext, AdjudicationData], Any],
                 priority: int = 0, can_trigger_nested: bool = False):
        super().__init__(f"modification_{modification_name}", priority)
        self.modification_name = modification_name
        self.modification_func = modification_func
        self.can_trigger_nested = can_trigger_nested
    
    def execute(self, data: AdjudicationData) -> AdjudicationStepResult:
        """执行修正"""
        try:
            result = self.modification_func(data.context, data)
            data.modification_results.append(result)
            
            logger.debug(f"修正 {self.modification_name} 执行完成")
            
            # 检查是否触发嵌套裁决
            if self.can_trigger_nested and self._should_trigger_nested(result):
                nested_context = self._create_nested_context(data.context, result)
                data.nested_triggers.append({
                    'source': self.modification_name,
                    'context': nested_context,
                    'trigger_data': result
                })
                return AdjudicationStepResult.TRIGGER_NESTED
            
            return AdjudicationStepResult.CONTINUE
            
        except Exception as e:
            logger.error(f"修正 {self.modification_name} 执行异常: {e}")
            return AdjudicationStepResult.CONTINUE
    
    def _should_trigger_nested(self, result: Any) -> bool:
        """检查是否应该触发嵌套裁决"""
        # 可以根据具体需求实现
        return hasattr(result, 'trigger_nested') and result.trigger_nested
    
    def _create_nested_context(self, original_context: InteractionContext, result: Any) -> InteractionContext:
        """创建嵌套上下文"""
        # 可以根据具体需求实现
        return original_context


class CalculationStep(BaseAdjudicationStep):
    """计算步骤"""
    
    def __init__(self, calculation_name: str, calculation_func: Callable[[InteractionContext, AdjudicationData], Any],
                 priority: int = 0):
        super().__init__(f"calculation_{calculation_name}", priority)
        self.calculation_name = calculation_name
        self.calculation_func = calculation_func
    
    def execute(self, data: AdjudicationData) -> AdjudicationStepResult:
        """执行计算"""
        try:
            result = self.calculation_func(data.context, data)
            data.calculation_outputs[self.calculation_name] = result
            
            logger.debug(f"计算 {self.calculation_name} 完成: {result}")
            return AdjudicationStepResult.CONTINUE
            
        except Exception as e:
            logger.error(f"计算 {self.calculation_name} 执行异常: {e}")
            return AdjudicationStepResult.CONTINUE


class BaseAdjudicationModel:
    """基础裁决流程模型"""
    
    def __init__(self, model_name: str):
        self.model_name = model_name
        
        # 三个阶段的步骤
        self.judgment_steps: List[JudgmentStep] = []
        self.modification_steps: List[ModificationStep] = []
        self.calculation_steps: List[CalculationStep] = []
        
        # 嵌套裁决处理器
        self.nested_handler: Optional[Callable] = None
        
        logger.info(f"初始化基础裁决模型: {model_name}")
    
    def add_judgment_step(self, step: JudgmentStep):
        """添加判断步骤"""
        self.judgment_steps.append(step)
        self.judgment_steps.sort(key=lambda x: x.priority, reverse=True)
    
    def add_modification_step(self, step: ModificationStep):
        """添加修正步骤"""
        self.modification_steps.append(step)
        self.modification_steps.sort(key=lambda x: x.priority, reverse=True)
    
    def add_calculation_step(self, step: CalculationStep):
        """添加计算步骤"""
        self.calculation_steps.append(step)
        self.calculation_steps.sort(key=lambda x: x.priority, reverse=True)
    
    def set_nested_handler(self, handler: Callable):
        """设置嵌套裁决处理器"""
        self.nested_handler = handler
    
    def execute(self, context: InteractionContext) -> AdjudicationData:
        """执行完整的裁决流程"""
        data = AdjudicationData(context=context, phase=AdjudicationPhase.JUDGMENT)
        
        logger.info(f"开始执行裁决模型: {self.model_name}")
        
        # 阶段1: 判断条件
        if not self._execute_judgment_phase(data):
            logger.info("判断条件阶段失败，裁决被阻止")
            return data
        
        # 阶段2: 查看修正
        data.phase = AdjudicationPhase.MODIFICATION
        nested_triggers = self._execute_modification_phase(data)
        
        # 处理嵌套触发
        if nested_triggers and self.nested_handler:
            for trigger in nested_triggers:
                nested_result = self.nested_handler(trigger['context'])
                data.nested_results.append(nested_result)
        
        # 阶段3: 裁决计算
        data.phase = AdjudicationPhase.CALCULATION
        self._execute_calculation_phase(data)
        
        logger.info(f"裁决模型 {self.model_name} 执行完成")
        return data
    
    def _execute_judgment_phase(self, data: AdjudicationData) -> bool:
        """执行判断条件阶段"""
        logger.debug("执行判断条件阶段")
        
        for step in self.judgment_steps:
            if not step.can_execute(data):
                continue
            
            result = step.execute(data)
            data.step_results[AdjudicationPhase.JUDGMENT] = result
            
            if result == AdjudicationStepResult.BLOCK:
                return False
        
        return True
    
    def _execute_modification_phase(self, data: AdjudicationData) -> List[Dict[str, Any]]:
        """执行修正阶段"""
        logger.debug("执行修正阶段")
        nested_triggers = []
        
        for step in self.modification_steps:
            if not step.can_execute(data):
                continue
            
            result = step.execute(data)
            
            if result == AdjudicationStepResult.TRIGGER_NESTED:
                nested_triggers.extend(data.nested_triggers)
                data.nested_triggers.clear()  # 清空已处理的触发
        
        return nested_triggers
    
    def _execute_calculation_phase(self, data: AdjudicationData):
        """执行计算阶段"""
        logger.debug("执行计算阶段")
        
        for step in self.calculation_steps:
            if not step.can_execute(data):
                continue
            
            step.execute(data)


# 便利函数
def create_adjudication_model(model_name: str) -> BaseAdjudicationModel:
    """创建裁决模型"""
    return BaseAdjudicationModel(model_name)


def create_judgment_step(condition_name: str, condition_func: Callable[[InteractionContext], bool],
                        priority: int = 0, required: bool = True) -> JudgmentStep:
    """创建判断步骤"""
    return JudgmentStep(condition_name, condition_func, priority, required)


def create_modification_step(modification_name: str, 
                           modification_func: Callable[[InteractionContext, AdjudicationData], Any],
                           priority: int = 0, can_trigger_nested: bool = False) -> ModificationStep:
    """创建修正步骤"""
    return ModificationStep(modification_name, modification_func, priority, can_trigger_nested)


def create_calculation_step(calculation_name: str,
                          calculation_func: Callable[[InteractionContext, AdjudicationData], Any],
                          priority: int = 0) -> CalculationStep:
    """创建计算步骤"""
    return CalculationStep(calculation_name, calculation_func, priority)