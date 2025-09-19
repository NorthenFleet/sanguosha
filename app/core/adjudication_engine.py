#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
三国杀裁决引擎实现
负责计算所有修正后的最终结果
"""

from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from enum import Enum
from .interaction_model import InteractionContext, InteractionType
from .modification_handlers import ModificationResult
import logging

logger = logging.getLogger(__name__)


class AdjudicationResult(Enum):
    """裁决结果类型"""
    SUCCESS = "success"           # 成功执行
    BLOCKED = "blocked"           # 被阻止
    MODIFIED = "modified"         # 被修正
    FAILED = "failed"             # 执行失败
    PARTIAL = "partial"           # 部分执行


@dataclass
class FinalResult:
    """最终裁决结果"""
    result_type: AdjudicationResult
    success: bool
    original_context: InteractionContext
    final_context: InteractionContext
    executed_effects: List[Dict[str, Any]]
    blocked_effects: List[Dict[str, Any]]
    damage_dealt: int = 0
    cards_gained: List[Any] = None
    cards_lost: List[Any] = None
    hp_changed: int = 0
    additional_info: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.cards_gained is None:
            self.cards_gained = []
        if self.cards_lost is None:
            self.cards_lost = []
        if self.additional_info is None:
            self.additional_info = {}


class EffectCalculator:
    """效果计算器"""
    
    @staticmethod
    def calculate_damage(context: InteractionContext, modifications: List[ModificationResult]) -> int:
        """计算最终伤害"""
        base_damage = context.additional_data.get('damage_amount', 1)
        
        # 应用所有伤害修正
        for mod in modifications:
            if mod.success and 'damage_amount' in mod.modified_context.additional_data:
                base_damage = mod.modified_context.additional_data['damage_amount']
        
        # 检查是否被完全阻止
        for mod in modifications:
            if mod.block_original:
                logger.info("伤害被完全阻止")
                return 0
        
        return max(0, base_damage)
    
    @staticmethod
    def calculate_card_changes(context: InteractionContext, modifications: List[ModificationResult]) -> Tuple[List[Any], List[Any]]:
        """计算卡牌变化"""
        cards_gained = []
        cards_lost = []
        
        # 处理原始卡牌使用
        if context.card:
            cards_lost.append(context.card)
        
        # 处理修正产生的卡牌变化
        for mod in modifications:
            if mod.additional_effects:
                for effect in mod.additional_effects:
                    if effect['type'] == 'gain_card':
                        cards_gained.append(effect['card'])
                    elif effect['type'] == 'lose_card' or effect['type'] == 'card_discarded':
                        cards_lost.append(effect['card'])
        
        return cards_gained, cards_lost
    
    @staticmethod
    def calculate_hp_change(context: InteractionContext, modifications: List[ModificationResult]) -> int:
        """计算体力变化"""
        hp_change = 0
        
        # 计算伤害造成的体力减少
        damage = EffectCalculator.calculate_damage(context, modifications)
        if damage > 0:
            hp_change -= damage
        
        # 处理修正产生的体力变化
        for mod in modifications:
            if mod.additional_effects:
                for effect in mod.additional_effects:
                    if effect['type'] == 'recover_hp':
                        hp_change += effect.get('amount', 1)
                    elif effect['type'] == 'lose_hp':
                        hp_change -= effect.get('amount', 1)
        
        return hp_change


class AdjudicationEngine:
    """裁决引擎"""
    
    def __init__(self):
        self.effect_calculator = EffectCalculator()
    
    def adjudicate(self, original_context: InteractionContext, modifications: List[ModificationResult]) -> FinalResult:
        """执行最终裁决"""
        logger.info(f"开始裁决交互: {original_context.interaction_type}")
        
        # 确定最终上下文
        final_context = self._get_final_context(original_context, modifications)
        
        # 检查是否被阻止
        if self._is_blocked(modifications):
            return self._create_blocked_result(original_context, final_context, modifications)
        
        # 计算各种效果
        damage_dealt = self.effect_calculator.calculate_damage(final_context, modifications)
        cards_gained, cards_lost = self.effect_calculator.calculate_card_changes(final_context, modifications)
        hp_changed = self.effect_calculator.calculate_hp_change(final_context, modifications)
        
        # 执行效果
        executed_effects, blocked_effects = self._execute_effects(final_context, modifications)
        
        # 确定结果类型
        result_type = self._determine_result_type(original_context, final_context, modifications)
        
        return FinalResult(
            result_type=result_type,
            success=True,
            original_context=original_context,
            final_context=final_context,
            executed_effects=executed_effects,
            blocked_effects=blocked_effects,
            damage_dealt=damage_dealt,
            cards_gained=cards_gained,
            cards_lost=cards_lost,
            hp_changed=hp_changed,
            additional_info=self._collect_additional_info(final_context, modifications)
        )
    
    def _get_final_context(self, original_context: InteractionContext, modifications: List[ModificationResult]) -> InteractionContext:
        """获取最终上下文"""
        final_context = original_context
        
        for mod in modifications:
            if mod.success:
                final_context = mod.modified_context
        
        return final_context
    
    def _is_blocked(self, modifications: List[ModificationResult]) -> bool:
        """检查是否被阻止"""
        return any(mod.block_original for mod in modifications if mod.success)
    
    def _create_blocked_result(self, original_context: InteractionContext, final_context: InteractionContext, modifications: List[ModificationResult]) -> FinalResult:
        """创建被阻止的结果"""
        logger.info("交互被阻止")
        
        # 即使被阻止，某些效果仍可能执行（如卡牌弃置）
        executed_effects = []
        for mod in modifications:
            if mod.additional_effects:
                for effect in mod.additional_effects:
                    if effect['type'] in ['card_discarded', 'lose_card']:
                        executed_effects.append(effect)
        
        return FinalResult(
            result_type=AdjudicationResult.BLOCKED,
            success=False,
            original_context=original_context,
            final_context=final_context,
            executed_effects=executed_effects,
            blocked_effects=[{'type': 'original_action', 'reason': 'blocked_by_modification'}]
        )
    
    def _execute_effects(self, context: InteractionContext, modifications: List[ModificationResult]) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """执行效果"""
        executed_effects = []
        blocked_effects = []
        
        # 执行原始效果（如果没有被阻止）
        if not self._is_blocked(modifications):
            original_effect = self._create_original_effect(context)
            if original_effect:
                executed_effects.append(original_effect)
        else:
            original_effect = self._create_original_effect(context)
            if original_effect:
                blocked_effects.append(original_effect)
        
        # 执行修正产生的效果
        for mod in modifications:
            if mod.success and mod.additional_effects:
                for effect in mod.additional_effects:
                    try:
                        self._execute_single_effect(effect)
                        executed_effects.append(effect)
                    except Exception as e:
                        logger.error(f"执行效果失败: {effect}, 错误: {e}")
                        blocked_effects.append(effect)
        
        return executed_effects, blocked_effects
    
    def _create_original_effect(self, context: InteractionContext) -> Optional[Dict[str, Any]]:
        """创建原始效果"""
        if context.interaction_type == InteractionType.CARD_PLAY:
            return {
                'type': 'card_play',
                'player': context.source_player,
                'card': context.card,
                'target': context.target_player
            }
        elif context.interaction_type == InteractionType.SKILL_USE:
            return {
                'type': 'skill_use',
                'player': context.source_player,
                'skill': context.additional_data.get('skill_name'),
                'target': context.target_player
            }
        elif context.interaction_type == InteractionType.DAMAGE:
            return {
                'type': 'damage',
                'source': context.source_player,
                'target': context.target_player,
                'amount': context.additional_data.get('damage_amount', 1)
            }
        
        return None
    
    def _execute_single_effect(self, effect: Dict[str, Any]):
        """执行单个效果"""
        effect_type = effect['type']
        
        if effect_type == 'gain_card':
            player = effect['player']
            card = effect['card']
            if hasattr(player, 'gain_card'):
                player.gain_card(card)
                logger.info(f"{player}获得卡牌{card}")
        
        elif effect_type == 'lose_card' or effect_type == 'card_discarded':
            player = effect['player']
            card = effect['card']
            if hasattr(player, 'lose_card'):
                player.lose_card(card)
                logger.info(f"{player}失去卡牌{card}")
        
        elif effect_type == 'recover_hp':
            player = effect['player']
            amount = effect.get('amount', 1)
            if hasattr(player, 'recover_hp'):
                player.recover_hp(amount)
                logger.info(f"{player}回复{amount}点体力")
        
        elif effect_type == 'lose_hp':
            player = effect['player']
            amount = effect.get('amount', 1)
            if hasattr(player, 'lose_hp'):
                player.lose_hp(amount)
                logger.info(f"{player}失去{amount}点体力")
        
        elif effect_type == 'damage':
            source = effect.get('source')
            target = effect['target']
            amount = effect.get('amount', 1)
            if hasattr(target, 'take_damage'):
                target.take_damage(amount, source)
                logger.info(f"{target}受到{amount}点伤害")
    
    def _determine_result_type(self, original_context: InteractionContext, final_context: InteractionContext, modifications: List[ModificationResult]) -> AdjudicationResult:
        """确定结果类型"""
        if self._is_blocked(modifications):
            return AdjudicationResult.BLOCKED
        
        # 检查是否有修正
        has_modifications = any(mod.success for mod in modifications)
        if has_modifications:
            # 检查是否完全成功
            if self._is_fully_successful(final_context, modifications):
                return AdjudicationResult.MODIFIED
            else:
                return AdjudicationResult.PARTIAL
        
        # 检查原始行为是否成功
        if self._is_original_successful(original_context):
            return AdjudicationResult.SUCCESS
        else:
            return AdjudicationResult.FAILED
    
    def _is_fully_successful(self, context: InteractionContext, modifications: List[ModificationResult]) -> bool:
        """检查是否完全成功"""
        # 这里可以根据具体的成功条件来判断
        # 暂时简单返回True
        return True
    
    def _is_original_successful(self, context: InteractionContext) -> bool:
        """检查原始行为是否成功"""
        # 这里可以根据具体的成功条件来判断
        # 暂时简单返回True
        return True
    
    def _collect_additional_info(self, context: InteractionContext, modifications: List[ModificationResult]) -> Dict[str, Any]:
        """收集额外信息"""
        info = {}
        
        # 收集触发的技能
        triggered_skills = []
        for mod in modifications:
            if mod.success and hasattr(mod, 'skill_name'):
                triggered_skills.append(mod.skill_name)
        
        if triggered_skills:
            info['triggered_skills'] = triggered_skills
        
        # 收集特殊效果
        special_effects = []
        for mod in modifications:
            if mod.additional_effects:
                for effect in mod.additional_effects:
                    if effect['type'] not in ['gain_card', 'lose_card', 'card_discarded', 'recover_hp', 'lose_hp', 'damage']:
                        special_effects.append(effect)
        
        if special_effects:
            info['special_effects'] = special_effects
        
        return info
    
    def create_summary(self, result: FinalResult) -> str:
        """创建结果摘要"""
        summary_parts = []
        
        # 基本结果
        if result.success:
            result_value = result.result_type.value if hasattr(result.result_type, 'value') else str(result.result_type)
            summary_parts.append(f"交互成功执行 ({result_value})")
        else:
            result_value = result.result_type.value if hasattr(result.result_type, 'value') else str(result.result_type)
            summary_parts.append(f"交互被阻止 ({result_value})")
        
        # 伤害信息
        if result.damage_dealt > 0:
            summary_parts.append(f"造成{result.damage_dealt}点伤害")
        
        # 体力变化
        if result.hp_changed != 0:
            if result.hp_changed > 0:
                summary_parts.append(f"回复{result.hp_changed}点体力")
            else:
                summary_parts.append(f"失去{abs(result.hp_changed)}点体力")
        
        # 卡牌变化
        if result.cards_gained:
            summary_parts.append(f"获得{len(result.cards_gained)}张卡牌")
        if result.cards_lost:
            summary_parts.append(f"失去{len(result.cards_lost)}张卡牌")
        
        # 执行的效果数量
        if result.executed_effects:
            summary_parts.append(f"执行了{len(result.executed_effects)}个效果")
        
        return "；".join(summary_parts)