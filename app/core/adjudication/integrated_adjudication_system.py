#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
集成裁决系统
整合基础裁决模型、数据驱动配置、嵌套裁决功能，提供统一的裁决接口
"""

from typing import Dict, List, Optional, Any, Callable
import logging
import os
from .base_adjudication_model import BaseAdjudicationModel, AdjudicationData
from .data_driven_adjudication import (
    AdjudicationModelManager, get_adjudication_manager,
    register_judgment_rule, register_modification_rule, register_calculation_rule
)
from .nested_adjudication_stack import NestedAdjudicationStack, TriggerType, get_stack_manager
from .enhanced_adjudication_engine import EnhancedAdjudicationEngine
from .standard_rule_functions import *
from ..interaction.interaction_model import InteractionContext

logger = logging.getLogger(__name__)


class IntegratedAdjudicationSystem:
    """集成裁决系统"""
    
    def __init__(self, config_directory: str = ""):
        # 核心组件
        self.model_manager = get_adjudication_manager()
        self.stack_manager = get_stack_manager()
        self.enhanced_engine = EnhancedAdjudicationEngine(self.stack_manager)
        
        # 配置
        if config_directory:
            self.model_manager.set_config_directory(config_directory)
        
        # 初始化标准规则
        self._register_standard_rules()
        
        # 加载配置文件
        if config_directory and os.path.exists(config_directory):
            self._load_all_configs()
        
        logger.info("集成裁决系统初始化完成")
    
    def _register_standard_rules(self):
        """注册标准规则函数"""
        # 判断条件函数
        judgment_functions = {
            'check_has_sha_card': check_has_sha_card,
            'check_target_alive': check_target_alive,
            'check_attack_range': check_attack_range,
            'check_sha_count_limit': check_sha_count_limit,
            'check_has_tao_card': check_has_tao_card,
            'check_target_needs_healing': check_target_needs_healing,
            'check_can_equip_weapon': check_can_equip_weapon,
        }
        
        for name, func in judgment_functions.items():
            register_judgment_rule(name, func)
        
        # 修正函数
        modification_functions = {
            'apply_weapon_damage_bonus': apply_weapon_damage_bonus,
            'apply_skill_damage_modification': apply_skill_damage_modification,
            'check_target_defense': check_target_defense,
            'apply_distance_modification': apply_distance_modification,
        }
        
        for name, func in modification_functions.items():
            register_modification_rule(name, func)
        
        # 计算函数
        calculation_functions = {
            'calculate_final_damage': calculate_final_damage,
            'calculate_card_consumption': calculate_card_consumption,
            'apply_final_effects': apply_final_effects,
            'calculate_healing_amount': calculate_healing_amount,
            'apply_healing_effects': apply_healing_effects,
            'apply_equipment_effects': apply_equipment_effects,
        }
        
        for name, func in calculation_functions.items():
            register_calculation_rule(name, func)
        
        logger.info("标准规则函数注册完成")
    
    def _load_all_configs(self):
        """加载所有配置文件"""
        try:
            self.model_manager.reload_all_models()
            logger.info("配置文件加载完成")
        except Exception as e:
            logger.error(f"加载配置文件失败: {e}")
    
    def execute_simple_adjudication(self, model_name: str, context: InteractionContext) -> Optional[AdjudicationData]:
        """执行简单裁决（不使用嵌套堆栈）"""
        return self.model_manager.execute_model(model_name, context)
    
    def execute_nested_adjudication(self, model_name: str, context: InteractionContext, 
                                  trigger_type: TriggerType = TriggerType.CARD_EFFECT,
                                  description: str = "") -> Optional[AdjudicationData]:
        """执行嵌套裁决（使用堆栈系统）"""
        # 获取模型
        model = self.model_manager.get_model(model_name)
        if not model:
            logger.error(f"未找到裁决模型: {model_name}")
            return None
        
        # 设置嵌套处理器
        model.set_nested_handler(self._handle_nested_trigger)
        
        # 使用增强引擎执行
        result = self.enhanced_engine.adjudicate_with_stack(context, trigger_type, description)
        
        # 转换结果格式
        return self._convert_final_result_to_adjudication_data(result, context)
    
    def _handle_nested_trigger(self, nested_context: InteractionContext) -> Any:
        """处理嵌套触发"""
        # 根据上下文确定使用哪个模型
        model_name = self._determine_nested_model(nested_context)
        
        if model_name:
            return self.execute_nested_adjudication(
                model_name, 
                nested_context, 
                TriggerType.NESTED_TRIGGER,
                f"嵌套触发: {nested_context.interaction_type}"
            )
        
        return None
    
    def _determine_nested_model(self, context: InteractionContext) -> Optional[str]:
        """确定嵌套裁决使用的模型"""
        # 根据交互类型确定模型
        interaction_type = context.interaction_type
        
        model_mapping = {
            'use_sha': 'sha_card_adjudication',
            'use_shan': 'shan_card_adjudication',
            'use_tao': 'tao_card_adjudication',
            'use_wuxiekeji': 'wuxiekeji_adjudication',
            'equip_weapon': 'weapon_equipment_adjudication',
        }
        
        return model_mapping.get(str(interaction_type))
    
    def _convert_final_result_to_adjudication_data(self, final_result, context: InteractionContext) -> AdjudicationData:
        """将FinalResult转换为AdjudicationData"""
        data = AdjudicationData(context=context, phase=None)
        
        # 填充计算输出
        data.calculation_outputs['final_result'] = {
            'success': final_result.success,
            'result_type': final_result.result_type.value,
            'damage_dealt': final_result.damage_dealt,
            'hp_changed': final_result.hp_changed,
            'cards_gained': final_result.cards_gained,
            'cards_lost': final_result.cards_lost,
            'executed_effects': final_result.executed_effects,
            'blocked_effects': final_result.blocked_effects,
            'additional_info': final_result.additional_info
        }
        
        return data
    
    def register_custom_judgment_rule(self, name: str, func: Callable[[InteractionContext], bool]):
        """注册自定义判断规则"""
        register_judgment_rule(name, func)
        logger.info(f"注册自定义判断规则: {name}")
    
    def register_custom_modification_rule(self, name: str, func: Callable[[InteractionContext, AdjudicationData], Any]):
        """注册自定义修正规则"""
        register_modification_rule(name, func)
        logger.info(f"注册自定义修正规则: {name}")
    
    def register_custom_calculation_rule(self, name: str, func: Callable[[InteractionContext, AdjudicationData], Any]):
        """注册自定义计算规则"""
        register_calculation_rule(name, func)
        logger.info(f"注册自定义计算规则: {name}")
    
    def load_model_from_config(self, config_data: Dict[str, Any]) -> str:
        """从配置数据加载模型"""
        return self.model_manager.load_model_from_dict(config_data)
    
    def get_available_models(self) -> List[str]:
        """获取可用的模型列表"""
        return self.model_manager.list_models()
    
    def get_stack_status(self) -> Dict[str, Any]:
        """获取堆栈状态"""
        return {
            'current_depth': self.stack_manager.current_depth,
            'max_depth': self.stack_manager.max_depth,
            'is_processing': self.stack_manager.is_processing,
            'active_processes': len(self.stack_manager.processes),
            'execution_stack_size': len(self.stack_manager.execution_stack)
        }
    
    def clear_stack(self):
        """清空堆栈"""
        self.stack_manager.clear_stack()
        logger.info("裁决堆栈已清空")


# 全局集成系统实例
_global_system: Optional[IntegratedAdjudicationSystem] = None


def get_integrated_system(config_directory: str = "") -> IntegratedAdjudicationSystem:
    """获取全局集成裁决系统"""
    global _global_system
    if _global_system is None:
        _global_system = IntegratedAdjudicationSystem(config_directory)
    return _global_system


def initialize_adjudication_system(config_directory: str = ""):
    """初始化裁决系统"""
    global _global_system
    _global_system = IntegratedAdjudicationSystem(config_directory)
    logger.info("全局裁决系统初始化完成")


# 便利函数
def execute_adjudication(model_name: str, context: InteractionContext, 
                        use_nested: bool = True) -> Optional[AdjudicationData]:
    """执行裁决"""
    system = get_integrated_system()
    
    if use_nested:
        return system.execute_nested_adjudication(model_name, context)
    else:
        return system.execute_simple_adjudication(model_name, context)


def register_judgment_function(name: str, func: Callable[[InteractionContext], bool]):
    """注册判断函数"""
    system = get_integrated_system()
    system.register_custom_judgment_rule(name, func)


def register_modification_function(name: str, func: Callable[[InteractionContext, AdjudicationData], Any]):
    """注册修正函数"""
    system = get_integrated_system()
    system.register_custom_modification_rule(name, func)


def register_calculation_function(name: str, func: Callable[[InteractionContext, AdjudicationData], Any]):
    """注册计算函数"""
    system = get_integrated_system()
    system.register_custom_calculation_rule(name, func)


def get_system_status() -> Dict[str, Any]:
    """获取系统状态"""
    system = get_integrated_system()
    return {
        'available_models': system.get_available_models(),
        'stack_status': system.get_stack_status()
    }