#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据驱动的裁决配置系统
支持通过JSON配置文件定义裁决规则，实现灵活的规则配置和动态加载
"""

from typing import Dict, List, Optional, Any, Callable
import json
import os
import logging
from dataclasses import dataclass
from .base_adjudication_model import (
    BaseAdjudicationModel, JudgmentStep, ModificationStep, CalculationStep,
    AdjudicationData, AdjudicationStepResult
)
from ..interaction.interaction_model import InteractionContext

logger = logging.getLogger(__name__)


@dataclass
class AdjudicationConfig:
    """裁决配置数据结构"""
    model_name: str
    description: str
    judgment_rules: List[Dict[str, Any]]
    modification_rules: List[Dict[str, Any]]
    calculation_rules: List[Dict[str, Any]]
    metadata: Dict[str, Any]


class RuleRegistry:
    """规则注册器 - 管理所有可用的判断、修正和计算函数"""
    
    def __init__(self):
        self.judgment_functions: Dict[str, Callable[[InteractionContext], bool]] = {}
        self.modification_functions: Dict[str, Callable[[InteractionContext, AdjudicationData], Any]] = {}
        self.calculation_functions: Dict[str, Callable[[InteractionContext, AdjudicationData], Any]] = {}
    
    def register_judgment_function(self, name: str, func: Callable[[InteractionContext], bool]):
        """注册判断函数"""
        self.judgment_functions[name] = func
        logger.debug(f"注册判断函数: {name}")
    
    def register_modification_function(self, name: str, func: Callable[[InteractionContext, AdjudicationData], Any]):
        """注册修正函数"""
        self.modification_functions[name] = func
        logger.debug(f"注册修正函数: {name}")
    
    def register_calculation_function(self, name: str, func: Callable[[InteractionContext, AdjudicationData], Any]):
        """注册计算函数"""
        self.calculation_functions[name] = func
        logger.debug(f"注册计算函数: {name}")
    
    def get_judgment_function(self, name: str) -> Optional[Callable]:
        """获取判断函数"""
        return self.judgment_functions.get(name)
    
    def get_modification_function(self, name: str) -> Optional[Callable]:
        """获取修正函数"""
        return self.modification_functions.get(name)
    
    def get_calculation_function(self, name: str) -> Optional[Callable]:
        """获取计算函数"""
        return self.calculation_functions.get(name)


class DataDrivenAdjudicationFactory:
    """数据驱动的裁决工厂"""
    
    def __init__(self, rule_registry: RuleRegistry):
        self.rule_registry = rule_registry
        self.config_cache: Dict[str, AdjudicationConfig] = {}
    
    def load_config_from_file(self, config_path: str) -> AdjudicationConfig:
        """从文件加载配置"""
        if not os.path.exists(config_path):
            raise FileNotFoundError(f"配置文件不存在: {config_path}")
        
        with open(config_path, 'r', encoding='utf-8') as f:
            config_data = json.load(f)
        
        return self._parse_config(config_data)
    
    def load_config_from_dict(self, config_data: Dict[str, Any]) -> AdjudicationConfig:
        """从字典加载配置"""
        return self._parse_config(config_data)
    
    def _parse_config(self, config_data: Dict[str, Any]) -> AdjudicationConfig:
        """解析配置数据"""
        return AdjudicationConfig(
            model_name=config_data.get('model_name', ''),
            description=config_data.get('description', ''),
            judgment_rules=config_data.get('judgment_rules', []),
            modification_rules=config_data.get('modification_rules', []),
            calculation_rules=config_data.get('calculation_rules', []),
            metadata=config_data.get('metadata', {})
        )
    
    def create_model_from_config(self, config: AdjudicationConfig) -> BaseAdjudicationModel:
        """根据配置创建裁决模型"""
        model = BaseAdjudicationModel(config.model_name)
        
        # 创建判断步骤
        for rule in config.judgment_rules:
            step = self._create_judgment_step(rule)
            if step:
                model.add_judgment_step(step)
        
        # 创建修正步骤
        for rule in config.modification_rules:
            step = self._create_modification_step(rule)
            if step:
                model.add_modification_step(step)
        
        # 创建计算步骤
        for rule in config.calculation_rules:
            step = self._create_calculation_step(rule)
            if step:
                model.add_calculation_step(step)
        
        logger.info(f"从配置创建裁决模型: {config.model_name}")
        return model
    
    def _create_judgment_step(self, rule: Dict[str, Any]) -> Optional[JudgmentStep]:
        """创建判断步骤"""
        function_name = rule.get('function')
        if not function_name:
            logger.warning("判断规则缺少function字段")
            return None
        
        func = self.rule_registry.get_judgment_function(function_name)
        if not func:
            logger.warning(f"未找到判断函数: {function_name}")
            return None
        
        return JudgmentStep(
            condition_name=rule.get('name', function_name),
            condition_func=func,
            priority=rule.get('priority', 0),
            required=rule.get('required', True)
        )
    
    def _create_modification_step(self, rule: Dict[str, Any]) -> Optional[ModificationStep]:
        """创建修正步骤"""
        function_name = rule.get('function')
        if not function_name:
            logger.warning("修正规则缺少function字段")
            return None
        
        func = self.rule_registry.get_modification_function(function_name)
        if not func:
            logger.warning(f"未找到修正函数: {function_name}")
            return None
        
        return ModificationStep(
            modification_name=rule.get('name', function_name),
            modification_func=func,
            priority=rule.get('priority', 0),
            can_trigger_nested=rule.get('can_trigger_nested', False)
        )
    
    def _create_calculation_step(self, rule: Dict[str, Any]) -> Optional[CalculationStep]:
        """创建计算步骤"""
        function_name = rule.get('function')
        if not function_name:
            logger.warning("计算规则缺少function字段")
            return None
        
        func = self.rule_registry.get_calculation_function(function_name)
        if not func:
            logger.warning(f"未找到计算函数: {function_name}")
            return None
        
        return CalculationStep(
            calculation_name=rule.get('name', function_name),
            calculation_func=func,
            priority=rule.get('priority', 0)
        )


class AdjudicationModelManager:
    """裁决模型管理器"""
    
    def __init__(self):
        self.rule_registry = RuleRegistry()
        self.factory = DataDrivenAdjudicationFactory(self.rule_registry)
        self.models: Dict[str, BaseAdjudicationModel] = {}
        self.config_directory = ""
    
    def set_config_directory(self, directory: str):
        """设置配置文件目录"""
        self.config_directory = directory
    
    def register_judgment_function(self, name: str, func: Callable[[InteractionContext], bool]):
        """注册判断函数"""
        self.rule_registry.register_judgment_function(name, func)
    
    def register_modification_function(self, name: str, func: Callable[[InteractionContext, AdjudicationData], Any]):
        """注册修正函数"""
        self.rule_registry.register_modification_function(name, func)
    
    def register_calculation_function(self, name: str, func: Callable[[InteractionContext, AdjudicationData], Any]):
        """注册计算函数"""
        self.rule_registry.register_calculation_function(name, func)
    
    def load_model_from_file(self, config_filename: str) -> str:
        """从文件加载模型"""
        config_path = os.path.join(self.config_directory, config_filename)
        config = self.factory.load_config_from_file(config_path)
        model = self.factory.create_model_from_config(config)
        
        self.models[config.model_name] = model
        logger.info(f"加载裁决模型: {config.model_name}")
        return config.model_name
    
    def load_model_from_dict(self, config_data: Dict[str, Any]) -> str:
        """从字典加载模型"""
        config = self.factory.load_config_from_dict(config_data)
        model = self.factory.create_model_from_config(config)
        
        self.models[config.model_name] = model
        logger.info(f"加载裁决模型: {config.model_name}")
        return config.model_name
    
    def get_model(self, model_name: str) -> Optional[BaseAdjudicationModel]:
        """获取裁决模型"""
        return self.models.get(model_name)
    
    def execute_model(self, model_name: str, context: InteractionContext) -> Optional[AdjudicationData]:
        """执行指定的裁决模型"""
        model = self.get_model(model_name)
        if not model:
            logger.error(f"未找到裁决模型: {model_name}")
            return None
        
        return model.execute(context)
    
    def list_models(self) -> List[str]:
        """列出所有已加载的模型"""
        return list(self.models.keys())
    
    def reload_all_models(self):
        """重新加载所有模型"""
        if not self.config_directory:
            logger.warning("未设置配置目录")
            return
        
        self.models.clear()
        
        for filename in os.listdir(self.config_directory):
            if filename.endswith('.json'):
                try:
                    self.load_model_from_file(filename)
                except Exception as e:
                    logger.error(f"加载配置文件 {filename} 失败: {e}")


# 全局管理器实例
global_adjudication_manager = AdjudicationModelManager()


# 便利函数
def get_adjudication_manager() -> AdjudicationModelManager:
    """获取全局裁决管理器"""
    return global_adjudication_manager


def register_judgment_rule(name: str, func: Callable[[InteractionContext], bool]):
    """注册判断规则"""
    global_adjudication_manager.register_judgment_function(name, func)


def register_modification_rule(name: str, func: Callable[[InteractionContext, AdjudicationData], Any]):
    """注册修正规则"""
    global_adjudication_manager.register_modification_function(name, func)


def register_calculation_rule(name: str, func: Callable[[InteractionContext, AdjudicationData], Any]):
    """注册计算规则"""
    global_adjudication_manager.register_calculation_function(name, func)


def execute_adjudication(model_name: str, context: InteractionContext) -> Optional[AdjudicationData]:
    """执行裁决"""
    return global_adjudication_manager.execute_model(model_name, context)