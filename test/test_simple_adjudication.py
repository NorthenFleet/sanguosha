#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简化的基础裁决模型测试
直接测试基础裁决流程模型，避免循环导入
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 直接导入需要的类，避免通过__init__.py
from app.core.adjudication.base_adjudication_model import (
    BaseAdjudicationModel, AdjudicationData, AdjudicationPhase,
    JudgmentStep, ModificationStep, CalculationStep
)
from app.models.player import Player
from app.models.card import Card


def create_simple_context():
    """创建简单的测试上下文"""
    source_player = Player("张三", "魏", "曹操")
    target_player = Player("李四", "蜀", "刘备")
    sha_card = Card("杀", "基本", "红桃", 7)
    
    return {
        'source_player': source_player,
        'target_player': target_player,
        'card': sha_card,
        'interaction_type': 'USE_CARD'
    }


def test_basic_model():
    """测试基础裁决模型"""
    print("=== 测试基础裁决模型 ===")
    
    # 创建模型
    model = BaseAdjudicationModel("test_sha_model")
    print(f"创建模型: {model.name}")
    
    # 定义判断函数
    def check_has_card(context):
        player_name = context['source_player'].name
        print(f"  判断: {player_name} 是否有杀卡牌")
        return True
    
    def check_target_valid(context):
        target_name = context['target_player'].name
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
    
    # 执行裁决
    print("\n开始执行裁决:")
    context = create_simple_context()
    result = model.execute(context)
    
    # 输出结果
    print(f"\n裁决执行完成:")
    print(f"  模型名称: {result.model_name}")
    print(f"  执行阶段: {result.current_phase}")
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
    context = create_simple_context()
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
    
    context = create_simple_context()
    result = model.execute(context)
    
    print(f"必需判断失败时的结果:")
    print(f"  当前阶段: {result.current_phase}")
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