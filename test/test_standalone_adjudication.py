#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
独立的基础裁决模型测试
完全独立实现，不依赖包导入
"""

from typing import Dict, List, Optional, Any, Callable, Union
from dataclasses import dataclass, field
from enum import Enum
from abc import ABC, abstractmethod
import logging

logger = logging.getLogger(__name__)

# 定义裁决阶段
class AdjudicationPhase(Enum):
    """裁决阶段"""
    JUDGMENT = "judgment"        # 判断条件阶段
    MODIFICATION = "modification"  # 查看修正阶段
    CALCULATION = "calculation"   # 裁决计算阶段

# 定义步骤结果
class AdjudicationStepResult(Enum):
    """裁决步骤结果"""
    CONTINUE = "continue"        # 继续下一步
    BLOCK = "block"             # 阻止执行
    TRIGGER_NESTED = "trigger_nested"  # 触发嵌套裁决
    COMPLETE = "complete"       # 直接完成

# 裁决数据容器
@dataclass
class AdjudicationData:
    """裁决数据容器，存储整个裁决过程的数据"""
    model_name: str
    context: Any  # 使用Any代替InteractionContext
    phase: AdjudicationPhase
    step_results: Dict[AdjudicationPhase, Any] = field(default_factory=dict)
    
    # 判断阶段数据
    judgment_conditions: List[str] = field(default_factory=list)
    judgment_results: Dict[str, bool] = field(default_factory=dict)
    
    # 修正阶段数据
    modifications: List[Dict[str, Any]] = field(default_factory=list)
    modification_results: List[Any] = field(default_factory=list)
    
    # 计算阶段数据
    calculation_inputs: Dict[str, Any] = field(default_factory=dict)
    calculation_outputs: Dict[str, Any] = field(default_factory=dict)
    
    # 嵌套裁决数据
    nested_triggers: List[Dict[str, Any]] = field(default_factory=list)
    nested_results: List[Any] = field(default_factory=list)
    
    # 元数据
    metadata: Dict[str, Any] = field(default_factory=dict)

# 基础裁决步骤
class BaseAdjudicationStep(ABC):
    """基础裁决步骤抽象类"""
    
    def __init__(self, step_name: str, priority: int = 0):
        self.name = step_name
        self.priority = priority
    
    @abstractmethod
    def execute(self, data: AdjudicationData) -> AdjudicationStepResult:
        """执行步骤"""
        pass
    
    def can_execute(self, data: AdjudicationData) -> bool:
        """检查是否可以执行"""
        return True
    
    def get_dependencies(self) -> List[str]:
        """获取依赖的步骤"""
        return []

# 判断步骤
class JudgmentStep(BaseAdjudicationStep):
    """判断条件步骤"""
    
    def __init__(self, condition_name: str, condition_func: Callable[[Any], bool], 
                 priority: int = 0, required: bool = True):
        super().__init__(condition_name, priority)
        self.condition_func = condition_func
        self.required = required
    
    def execute(self, data: AdjudicationData) -> AdjudicationStepResult:
        """执行判断条件"""
        try:
            result = self.condition_func(data.context)
            data.judgment_results[self.name] = result
            data.judgment_conditions.append(self.name)
            
            if not result and self.required:
                logger.info(f"必需判断条件 {self.name} 失败，阻止执行")
                return AdjudicationStepResult.BLOCK
            
            return AdjudicationStepResult.CONTINUE
            
        except Exception as e:
            logger.error(f"判断条件 {self.name} 执行异常: {e}")
            if self.required:
                return AdjudicationStepResult.BLOCK
            return AdjudicationStepResult.CONTINUE

# 修正步骤
class ModificationStep(BaseAdjudicationStep):
    """修正处理步骤"""
    
    def __init__(self, modification_name: str, modification_func: Callable[[Any, AdjudicationData], Any],
                 priority: int = 0, can_trigger_nested: bool = False):
        super().__init__(modification_name, priority)
        self.modification_func = modification_func
        self.can_trigger_nested = can_trigger_nested
    
    def execute(self, data: AdjudicationData) -> AdjudicationStepResult:
        """执行修正处理"""
        try:
            result = self.modification_func(data.context, data)
            data.modification_results.append(result)
            
            # 记录修正信息
            modification_info = {
                "name": self.name,
                "result": result,
                "priority": self.priority
            }
            data.modifications.append(modification_info)
            
            # 检查是否需要触发嵌套裁决
            if self.can_trigger_nested and self._should_trigger_nested(result):
                return AdjudicationStepResult.TRIGGER_NESTED
            
            return AdjudicationStepResult.CONTINUE
            
        except Exception as e:
            logger.error(f"修正处理 {self.name} 执行异常: {e}")
            return AdjudicationStepResult.CONTINUE
    
    def _should_trigger_nested(self, result: Any) -> bool:
        """判断是否应该触发嵌套裁决"""
        return isinstance(result, dict) and result.get("trigger_nested", False)

# 计算步骤
class CalculationStep(BaseAdjudicationStep):
    """裁决计算步骤"""
    
    def __init__(self, calculation_name: str, calculation_func: Callable[[Any, AdjudicationData], Any],
                 priority: int = 0):
        super().__init__(calculation_name, priority)
        self.calculation_func = calculation_func
    
    def execute(self, data: AdjudicationData) -> AdjudicationStepResult:
        """执行裁决计算"""
        try:
            result = self.calculation_func(data.context, data)
            data.calculation_outputs[self.name] = result
            
            return AdjudicationStepResult.CONTINUE
            
        except Exception as e:
            logger.error(f"裁决计算 {self.name} 执行异常: {e}")
            return AdjudicationStepResult.CONTINUE

# 基础裁决模型
class BaseAdjudicationModel:
    """基础裁决模型，实现三步裁决流程"""
    
    def __init__(self, model_name: str):
        self.name = model_name
        self.judgment_steps: List[JudgmentStep] = []
        self.modification_steps: List[ModificationStep] = []
        self.calculation_steps: List[CalculationStep] = []
        self.nested_handler: Optional[Callable] = None
        
        # 配置日志
        self.logger = logging.getLogger(f"{__name__}.{model_name}")
    
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
    
    def execute(self, context: Any) -> AdjudicationData:
        """执行完整的裁决流程"""
        # 创建裁决数据容器
        data = AdjudicationData(
            model_name=self.name,
            context=context,
            phase=AdjudicationPhase.JUDGMENT
        )
        
        self.logger.info(f"开始执行裁决模型: {self.name}")
        
        # 执行判断阶段
        if not self._execute_judgment_phase(data):
            self.logger.info("判断阶段失败，裁决终止")
            return data
        
        # 执行修正阶段
        data.phase = AdjudicationPhase.MODIFICATION
        nested_triggers = self._execute_modification_phase(data)
        
        # 处理嵌套裁决触发
        if nested_triggers and self.nested_handler:
            for trigger in nested_triggers:
                nested_result = self.nested_handler(trigger)
                data.nested_results.append(nested_result)
        
        # 执行计算阶段
        data.phase = AdjudicationPhase.CALCULATION
        self._execute_calculation_phase(data)
        
        self.logger.info(f"裁决模型 {self.name} 执行完成")
        return data
    
    def _execute_judgment_phase(self, data: AdjudicationData) -> bool:
        """执行判断阶段"""
        self.logger.info("执行判断阶段")
        
        for step in self.judgment_steps:
            if not step.can_execute(data):
                continue
            
            result = step.execute(data)
            if result == AdjudicationStepResult.BLOCK:
                return False
        
        return True
    
    def _execute_modification_phase(self, data: AdjudicationData) -> List[Dict[str, Any]]:
        """执行修正阶段"""
        self.logger.info("执行修正阶段")
        nested_triggers = []
        
        for step in self.modification_steps:
            if not step.can_execute(data):
                continue
            
            result = step.execute(data)
            if result == AdjudicationStepResult.TRIGGER_NESTED:
                nested_triggers.append({
                    "step_name": step.name,
                    "context": data.context,
                    "trigger_data": data.modification_results[-1]
                })
        
        return nested_triggers
    
    def _execute_calculation_phase(self, data: AdjudicationData):
        """执行计算阶段"""
        self.logger.info("执行计算阶段")
        
        for step in self.calculation_steps:
            if not step.can_execute(data):
                continue
            
            step.execute(data)


def test_basic_model():
    """测试基础裁决模型"""
    print("=== 测试基础裁决模型 ===")
    
    # 创建模型
    model = BaseAdjudicationModel("test_sha_model")
    print(f"创建模型: {model.name}")
    
    # 定义判断函数
    def check_has_card(context):
        player_name = context.get('source_player', {}).get('name', '未知玩家')
        print(f"  判断: {player_name} 是否有杀卡牌")
        return True
    
    def check_target_valid(context):
        target_name = context.get('target_player', {}).get('name', '未知目标')
        print(f"  判断: 目标 {target_name} 是否有效")
        return True
    
    # 添加判断步骤
    judgment1 = JudgmentStep("has_card", check_has_card, priority=100, required=True)
    judgment2 = JudgmentStep("target_valid", check_target_valid, priority=90, required=True)
    
    model.add_judgment_step(judgment1)
    model.add_judgment_step(judgment2)
    print(f"添加了 {len(model.judgment_steps)} 个判断步骤")
    
    # 定义修正函数
    def apply_weapon_bonus(context, data):
        print(f"  修正: 应用武器伤害加成")
        return {"type": "damage_bonus", "value": 1}
    
    def check_defense(context, data):
        print(f"  修正: 检查目标防御")
        return {"type": "defense_check", "can_defend": True}
    
    # 添加修正步骤
    modification1 = ModificationStep("weapon_bonus", apply_weapon_bonus, priority=100)
    modification2 = ModificationStep("defense_check", check_defense, priority=90)
    
    model.add_modification_step(modification1)
    model.add_modification_step(modification2)
    print(f"添加了 {len(model.modification_steps)} 个修正步骤")
    
    # 定义计算函数
    def calculate_damage(context, data):
        base_damage = 1
        bonus = 0
        
        # 计算加成
        for mod in data.modification_results:
            if isinstance(mod, dict) and mod.get("type") == "damage_bonus":
                bonus += mod.get("value", 0)
        
        final_damage = base_damage + bonus
        print(f"  计算: 基础伤害 {base_damage} + 加成 {bonus} = 最终伤害 {final_damage}")
        return {"final_damage": final_damage}
    
    # 添加计算步骤
    calculation1 = CalculationStep("damage_calculation", calculate_damage, priority=100)
    model.add_calculation_step(calculation1)
    print(f"添加了 {len(model.calculation_steps)} 个计算步骤")
    
    # 创建测试上下文
    context = {
        'source_player': {'name': '张三'},
        'target_player': {'name': '李四'},
        'card': {'name': '杀'},
        'interaction_type': 'USE_CARD'
    }
    
    # 执行裁决
    print("\n开始执行裁决:")
    result = model.execute(context)
    
    # 输出结果
    print(f"\n裁决执行完成:")
    print(f"  模型名称: {result.model_name}")
    print(f"  执行阶段: {result.phase}")
    print(f"  判断结果: {result.judgment_results}")
    print(f"  修正结果: {result.modification_results}")
    print(f"  计算输出: {result.calculation_outputs}")
    
    return result


def test_step_priorities():
    """测试步骤优先级"""
    print("\n=== 测试步骤优先级 ===")
    
    model = BaseAdjudicationModel("priority_test_model")
    
    # 添加不同优先级的判断步骤
    def judgment_high(context):
        print("  执行高优先级判断 (priority=200)")
        return True
    
    def judgment_low(context):
        print("  执行低优先级判断 (priority=50)")
        return True
    
    def judgment_medium(context):
        print("  执行中优先级判断 (priority=100)")
        return True
    
    # 故意以错误的顺序添加
    model.add_judgment_step(JudgmentStep("low", judgment_low, priority=50))
    model.add_judgment_step(JudgmentStep("high", judgment_high, priority=200))
    model.add_judgment_step(JudgmentStep("medium", judgment_medium, priority=100))
    
    print("按优先级执行判断步骤:")
    context = {'test': 'data'}
    result = model.execute(context)
    
    print(f"执行顺序验证完成")


def test_required_judgment():
    """测试必需判断失败的情况"""
    print("\n=== 测试必需判断失败 ===")
    
    model = BaseAdjudicationModel("required_test_model")
    
    def failing_judgment(context):
        print("  执行必需判断 - 返回失败")
        return False
    
    def normal_judgment(context):
        print("  执行普通判断 - 返回成功")
        return True
    
    # 添加一个必需的失败判断和一个普通判断
    model.add_judgment_step(JudgmentStep("failing", failing_judgment, required=True))
    model.add_judgment_step(JudgmentStep("normal", normal_judgment, required=False))
    
    context = {'test': 'data'}
    result = model.execute(context)
    
    print(f"必需判断失败时的结果:")
    print(f"  当前阶段: {result.phase}")
    print(f"  判断结果: {result.judgment_results}")


def main():
    """主测试函数"""
    print("开始测试基础裁决模型")
    
    try:
        # 测试基础模型功能
        test_basic_model()
        
        # 测试步骤优先级
        test_step_priorities()
        
        # 测试必需判断失败
        test_required_judgment()
        
        print("\n=== 所有测试完成 ===")
        print("基础裁决模型测试成功！")
        
    except Exception as e:
        print(f"测试过程中发生异常: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()