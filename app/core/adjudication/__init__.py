"""
裁决计算模块

包含游戏的裁决计算组件：
- adjudication_engine: 基础裁决引擎
- enhanced_adjudication_engine: 增强裁决引擎
- judgment_conditions: 判断条件
- modification_handlers: 修正处理器
- nested_adjudication_stack: 嵌套裁决栈
- equipment_judgment: 装备判定
- base_adjudication_model: 基础裁决流程模型
- data_driven_adjudication: 数据驱动裁决配置
- standard_rule_functions: 标准规则函数库
- integrated_adjudication_system: 集成裁决系统
"""

"""
裁决计算模块

包含游戏的裁决计算组件：
- judgment_conditions: 判断条件
- modification_handlers: 修正处理器
- base_adjudication_model: 基础裁决流程模型
- data_driven_adjudication: 数据驱动裁决配置
- standard_rule_functions: 标准规则函数库
- integrated_adjudication_system: 集成裁决系统
- equipment_judgment: 装备判定
- adjudication_engine: 基础裁决引擎
- enhanced_adjudication_engine: 增强裁决引擎
- nested_adjudication_stack: 嵌套裁决栈
"""

# 首先导入基础模块，避免循环导入
from .judgment_conditions import *
from .modification_handlers import *
from .base_adjudication_model import *
from .data_driven_adjudication import *
from .standard_rule_functions import *
from .integrated_adjudication_system import *
from .equipment_judgment import *

# 延迟导入可能有循环依赖的模块
try:
    from .adjudication_engine import *
    from .enhanced_adjudication_engine import *
    from .nested_adjudication_stack import *
except ImportError as e:
    # 如果有循环导入，先跳过，稍后再导入
    pass

__all__ = [
    # 基础裁决引擎
    'AdjudicationEngine', 'AdjudicationResult', 'FinalResult',
    
    # 增强裁决引擎
    'EnhancedAdjudicationEngine', 'TriggerCondition',
    
    # 嵌套裁决栈
    'NestedAdjudicationStack', 'AdjudicationProcess', 'TriggerType', 'AdjudicationStatus',
    
    # 基础裁决模型
    'BaseAdjudicationModel', 'AdjudicationData', 'AdjudicationPhase', 'AdjudicationStepResult',
    'JudgmentStep', 'ModificationStep', 'CalculationStep',
    
    # 数据驱动裁决
    'AdjudicationModelManager', 'DataDrivenAdjudicationFactory', 'RuleRegistry',
    
    # 集成裁决系统
    'IntegratedAdjudicationSystem', 'get_integrated_system', 'initialize_adjudication_system',
    'execute_adjudication', 'get_system_status',
    
    # 便利函数
    'register_judgment_function', 'register_modification_function', 'register_calculation_function',
]