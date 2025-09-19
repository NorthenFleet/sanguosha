#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
三国杀交互模型演示
展示"判断-修正-裁决"三阶段交互机制的使用方法
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.interaction.interaction_model import (
    InteractionEngine, InteractionContext, InteractionType, 
    JudgmentPhase, ModificationPhase, ResolutionPhase,
    CommonConditions, CommonResolutions
)
from app.core.adjudication.judgment_conditions import JudgmentConditions, default_judgment_registry
from app.core.adjudication.modification_handlers import ModificationEngine
from app.core.adjudication.adjudication_engine import AdjudicationEngine
from app.models.card import Card
from app.models.character import CharacterFactory
import logging

# 设置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class InteractionModelDemo:
    """交互模型演示类"""
    
    def __init__(self):
        self.interaction_engine = InteractionEngine()
        self.judgment_registry = default_judgment_registry
        self.modification_engine = ModificationEngine()
        self.adjudication_engine = AdjudicationEngine()
        
        # 设置基本的交互处理器
        self._setup_basic_handlers()
    
    def _setup_basic_handlers(self):
        """设置基本的交互处理器"""
        # 添加判断阶段的条件
        self.interaction_engine.judgment_phase.add_condition(CommonConditions.has_card)
        self.interaction_engine.judgment_phase.add_condition(CommonConditions.not_self_target)
        
        # 添加裁决阶段的处理器
        self.interaction_engine.resolution_phase.add_resolution_handler(
            InteractionType.CARD_USE, CommonResolutions.card_use_resolution
        )
        self.interaction_engine.resolution_phase.add_resolution_handler(
            InteractionType.DAMAGE, CommonResolutions.damage_resolution
        )
    
    def create_test_card(self, name: str, category: str = "basic"):
        """创建测试卡牌"""
        card = Card()
        card.name = name
        card.category = category
        card.suit = "♠"
        card.rank = 1
        return card
    
    def create_test_player(self, character_name: str):
        """创建测试玩家"""
        character = CharacterFactory.create_character(character_name)
        # 简化的玩家对象
        player = type('Player', (), {
            'character': character,
            'hand_cards': [],
            'equipment_area': {},
            'is_alive': lambda self: True
        })()
        return player
    
    def demo_basic_card_interaction(self):
        """演示基本卡牌交互"""
        print("=== 基本卡牌交互演示 ===")
        
        # 创建测试数据
        source_player = self.create_test_player("曹操")
        target_player = self.create_test_player("刘备")
        sha_card = self.create_test_card("杀")
        
        # 给玩家添加卡牌
        source_player.hand_cards.append(sha_card)
        
        # 创建交互上下文
        context = InteractionContext(
            interaction_type=InteractionType.CARD_USE,
            source_player=source_player,
            target_player=target_player,
            card=sha_card
        )
        
        print(f"玩家 {source_player.character.name} 对 {target_player.character.name} 使用 {sha_card.name}")
        
        # 处理交互
        result = self.interaction_engine.process_interaction(context)
        print(f"交互结果: {result}")
        
        return result
    
    def demo_skill_interaction(self):
        """演示技能交互"""
        print("\n=== 技能交互演示 ===")
        
        # 创建测试数据
        source_player = self.create_test_player("曹操")  # 曹操有奸雄技能
        
        # 创建交互上下文
        context = InteractionContext(
            interaction_type=InteractionType.SKILL_USE,
            source_player=source_player,
            skill="奸雄"
        )
        
        print(f"玩家 {source_player.character.name} 使用技能 奸雄")
        
        # 处理交互
        result = self.interaction_engine.process_interaction(context)
        print(f"交互结果: {result}")
        
        return result
    
    def demo_damage_interaction(self):
        """演示伤害交互"""
        print("\n=== 伤害交互演示 ===")
        
        # 创建测试数据
        source_player = self.create_test_player("张飞")
        target_player = self.create_test_player("赵云")
        
        print(f"初始体力 - {source_player.character.name}: {source_player.character.hp}, "
              f"{target_player.character.name}: {target_player.character.hp}")
        
        # 创建交互上下文
        context = InteractionContext(
            interaction_type=InteractionType.DAMAGE,
            source_player=source_player,
            target_player=target_player,
            amount=2
        )
        
        print(f"玩家 {source_player.character.name} 对 {target_player.character.name} 造成 2 点伤害")
        
        # 处理交互
        result = self.interaction_engine.process_interaction(context)
        print(f"交互结果: {result}")
        
        return result
    
    def demo_judgment_conditions(self):
        """演示判断条件"""
        print("\n=== 判断条件演示 ===")
        
        # 创建测试数据
        source_player = self.create_test_player("曹操")
        target_player = self.create_test_player("刘备")
        sha_card = self.create_test_card("杀")
        
        source_player.hand_cards.append(sha_card)
        
        context = InteractionContext(
            interaction_type=InteractionType.CARD_USE,
            source_player=source_player,
            target_player=target_player,
            card=sha_card
        )
        
        # 测试各种判断条件
        conditions_to_test = [
            ("can_use_sha", JudgmentConditions.can_use_sha),
            ("has_card", CommonConditions.has_card),
            ("not_self_target", CommonConditions.not_self_target),
            ("alive_target", CommonConditions.alive_target)
        ]
        
        for condition_name, condition_func in conditions_to_test:
            result = condition_func(context)
            print(f"判断条件 {condition_name}: {'通过' if result else '失败'}")
    
    def demo_modification_system(self):
        """演示修正系统"""
        print("\n=== 修正系统演示 ===")
        
        # 创建测试数据
        source_player = self.create_test_player("张飞")
        target_player = self.create_test_player("赵云")
        sha_card = self.create_test_card("杀")
        shan_card = self.create_test_card("闪")
        
        source_player.hand_cards.append(sha_card)
        target_player.hand_cards.append(shan_card)
        
        context = InteractionContext(
            interaction_type=InteractionType.CARD_USE,
            source_player=source_player,
            target_player=target_player,
            card=sha_card
        )
        
        print(f"原始交互: {source_player.character.name} 对 {target_player.character.name} 使用 {sha_card.name}")
        
        # 模拟修正过程
        modifications = self.modification_engine.process_modifications(context)
        print(f"修正结果数量: {len(modifications)}")
        
        for i, mod in enumerate(modifications):
            print(f"修正 {i+1}: {mod.description}")
    
    def demo_adjudication_engine(self):
        """演示裁决引擎"""
        print("\n=== 裁决引擎演示 ===")
        
        # 创建测试数据
        source_player = self.create_test_player("曹操")
        target_player = self.create_test_player("刘备")
        sha_card = self.create_test_card("杀")
        
        context = InteractionContext(
            interaction_type=InteractionType.CARD_USE,
            source_player=source_player,
            target_player=target_player,
            card=sha_card
        )
        
        # 模拟修正结果
        modifications = []
        
        # 执行裁决
        final_result = self.adjudication_engine.adjudicate(context, modifications)
        
        print(f"裁决结果: {final_result.success}")
        print(f"结果类型: {final_result.result_type}")
        print(f"结果摘要: {self.adjudication_engine.create_summary(final_result)}")
    
    def run_all_demos(self):
        """运行所有演示"""
        print("开始三国杀交互模型演示")
        print("=" * 60)
        
        try:
            self.demo_basic_card_interaction()
            self.demo_skill_interaction()
            self.demo_damage_interaction()
            self.demo_judgment_conditions()
            self.demo_modification_system()
            self.demo_adjudication_engine()
            
            print("\n" + "=" * 60)
            print("所有演示完成！")
            print("\n交互模型特点:")
            print("1. 三阶段处理: 判断 -> 修正 -> 裁决")
            print("2. 可扩展的条件系统")
            print("3. 灵活的修正机制")
            print("4. 详细的结果反馈")
            print("5. 事件驱动的架构")
            
        except Exception as e:
            print(f"演示过程中出现错误: {e}")
            import traceback
            traceback.print_exc()


def main():
    """主函数"""
    demo = InteractionModelDemo()
    demo.run_all_demos()


if __name__ == "__main__":
    main()