#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
基础裁决模型测试
测试新的基础裁决流程模型和集成系统
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 直接导入基础模块，避免循环导入
from app.core.adjudication.base_adjudication_model import (
    BaseAdjudicationModel, AdjudicationData, AdjudicationPhase,
    JudgmentStep, ModificationStep, CalculationStep
)
from app.core.adjudication.integrated_adjudication_system import (
    IntegratedAdjudicationSystem, initialize_adjudication_system,
    execute_adjudication, get_system_status
)
from app.models.player import Player
from app.models.card import Card


def create_test_context():
    """创建测试上下文"""
    # 创建测试玩家
    source_player = Player("张三", "魏", "曹操")
    target_player = Player("李四", "蜀", "刘备")
    
    # 创建测试卡牌
    sha_card = Card("杀", "基本", "红桃", 7)
    
    # 创建简单的上下文字典，避免导入InteractionContext
    context = {
        'source_player': source_player,
        'target_player': target_player,
        'card': sha_card,
        'interaction_type': 'USE_CARD'
    }
    
    return context


def test_basic_adjudication_model():
    """测试基础裁决模型"""
    print("=== 测试基础裁决模型 ===")
    
    # 创建模型
    model = BaseAdjudicationModel("test_sha_model")
    
    # 添加判断步骤
    def check_has_card(context):
        print(f"检查 {context['source_player'].name} 是否有杀卡牌")
        return True  # 简化测试
    
    def check_target_valid(context):
        print(f"检查目标 {context['target_player'].name} 是否有效")
        return True
    
    judgment1 = JudgmentStep("has_card", check_has_card, priority=100, required=True)
    judgment2 = JudgmentStep("target_valid", check_target_valid, priority=90, required=True)
    
    model.add_judgment_step(judgment1)
    model.add_judgment_step(judgment2)
    
    # 添加修正步骤
    def apply_weapon_bonus(context, data):
        print("应用武器伤害加成")
        return {"type": "damage_bonus", "value": 1}
    
    def check_defense(context, data):
        print("检查目标防御")
        return {"type": "defense_check", "can_defend": True}
    
    modification1 = ModificationStep("weapon_bonus", apply_weapon_bonus, priority=100)
    modification2 = ModificationStep("defense_check", check_defense, priority=90)
    
    model.add_modification_step(modification1)
    model.add_modification_step(modification2)
    
    # 添加计算步骤
    def calculate_damage(context, data):
        base_damage = 1
        bonus = 0
        for mod in data.modification_results:
            if isinstance(mod, dict) and mod.get("type") == "damage_bonus":
                bonus += mod.get("value", 0)
        final_damage = base_damage + bonus
        print(f"计算最终伤害: {base_damage} + {bonus} = {final_damage}")
        return {"final_damage": final_damage}
    
    calculation1 = CalculationStep("damage_calculation", calculate_damage, priority=100)
    model.add_calculation_step(calculation1)
    
    # 执行裁决
    context = create_test_context()
    result = model.execute(context)
    
    print(f"裁决结果:")
    print(f"  判断结果: {result.judgment_results}")
    print(f"  修正结果: {result.modification_results}")
    print(f"  计算结果: {result.calculation_outputs}")
    
    return result


def test_integrated_system():
    """测试集成裁决系统"""
    print("\n=== 测试集成裁决系统 ===")
    
    # 初始化系统
    config_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 
                             "app", "data", "adjudication_configs")
    initialize_adjudication_system(config_dir)
    
    # 获取系统状态
    status = get_system_status()
    print(f"系统状态: {status}")
    
    # 创建测试上下文
    context = create_test_context()
    
    # 尝试执行裁决（如果有配置文件）
    try:
        result = execute_adjudication("sha_card_adjudication", context, use_nested=False)
        if result:
            print(f"裁决执行成功:")
            print(f"  计算输出: {result.calculation_outputs}")
        else:
            print("未找到对应的裁决模型，这是正常的（需要配置文件）")
    except Exception as e:
        print(f"裁决执行异常: {e}")


def test_custom_rule_registration():
    """测试自定义规则注册"""
    print("\n=== 测试自定义规则注册 ===")
    
    from app.core.adjudication.integrated_adjudication_system import get_integrated_system
    
    system = get_integrated_system()
    
    # 注册自定义判断规则
    def custom_judgment(context):
        print("执行自定义判断规则")
        return True
    
    system.register_custom_judgment_rule("custom_judgment", custom_judgment)
    
    # 注册自定义修正规则
    def custom_modification(context, data):
        print("执行自定义修正规则")
        return {"type": "custom_mod", "value": 42}
    
    system.register_custom_modification_rule("custom_modification", custom_modification)
    
    # 注册自定义计算规则
    def custom_calculation(context, data):
        print("执行自定义计算规则")
        return {"custom_result": "success"}
    
    system.register_custom_calculation_rule("custom_calculation", custom_calculation)
    
    print("自定义规则注册完成")


def test_config_loading():
    """测试配置加载"""
    print("\n=== 测试配置加载 ===")
    
    from app.core.adjudication.integrated_adjudication_system import get_integrated_system
    
    system = get_integrated_system()
    
    # 创建测试配置
    test_config = {
        "model_name": "test_dynamic_model",
        "description": "动态创建的测试模型",
        "judgment_rules": [
            {
                "name": "test_judgment",
                "function": "check_has_sha_card",
                "priority": 100,
                "required": True
            }
        ],
        "modification_rules": [
            {
                "name": "test_modification",
                "function": "apply_weapon_damage_bonus",
                "priority": 100,
                "can_trigger_nested": False
            }
        ],
        "calculation_rules": [
            {
                "name": "test_calculation",
                "function": "calculate_final_damage",
                "priority": 100
            }
        ],
        "metadata": {
            "test": True
        }
    }
    
    # 加载配置
    model_name = system.load_model_from_config(test_config)
    print(f"动态加载模型: {model_name}")
    
    # 测试执行
    context = create_test_context()
    result = system.execute_simple_adjudication(model_name, context)
    
    if result:
        print(f"动态模型执行成功:")
        print(f"  判断结果: {result.judgment_results}")
        print(f"  修正结果: {result.modification_results}")
        print(f"  计算结果: {result.calculation_outputs}")
    else:
        print("动态模型执行失败")


def main():
    """主测试函数"""
    print("开始测试基础裁决模型系统")
    
    try:
        # 测试基础模型
        test_basic_adjudication_model()
        
        # 测试集成系统
        test_integrated_system()
        
        # 测试自定义规则注册
        test_custom_rule_registration()
        
        # 测试配置加载
        test_config_loading()
        
        print("\n=== 所有测试完成 ===")
        
    except Exception as e:
        print(f"测试过程中发生异常: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()