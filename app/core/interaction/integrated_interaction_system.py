#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
集成的交互系统
将新的交互模型与现有游戏引擎整合
"""

from typing import Dict, List, Optional, Any
from .interaction_model import InteractionEngine, InteractionContext, InteractionType
from ..adjudication.judgment_conditions import default_judgment_registry
from ..adjudication.modification_handlers import ModificationEngine
from ..adjudication.adjudication_engine import AdjudicationEngine, FinalResult
from ..base.game_engine import GameEngine
from ..base.game import Game
from ...models.player import Player
import logging

logger = logging.getLogger(__name__)


class IntegratedInteractionSystem:
    """集成的交互系统"""
    
    def __init__(self, game_engine: GameEngine):
        self.game_engine = game_engine
        self.interaction_engine = InteractionEngine()
        self.judgment_registry = default_judgment_registry
        self.modification_engine = ModificationEngine()
        self.adjudication_engine = AdjudicationEngine()
    
    def process_card_play(self, game_id: str, player_id: int, card_name: str, target_player_id: Optional[int] = None) -> FinalResult:
        """处理卡牌使用"""
        game = self.game_engine.get_game(game_id)
        if not game:
            raise ValueError(f"游戏不存在: {game_id}")
        
        # 获取玩家和目标
        source_player = game.players[player_id]
        target_player = game.players[target_player_id] if target_player_id is not None else None
        
        # 查找卡牌
        card = self._find_card_in_hand(source_player, card_name)
        if not card:
            raise ValueError(f"玩家没有卡牌: {card_name}")
        
        # 创建交互上下文
        context = InteractionContext(
            interaction_type=InteractionType.CARD_PLAY,
            source_player=source_player,
            target_player=target_player,
            card=card,
            additional_data={'game': game}
        )
        
        # 执行完整的交互流程
        return self._execute_interaction(context)
    
    def process_skill_use(self, game_id: str, player_id: int, skill_name: str, target_player_id: Optional[int] = None, **kwargs) -> FinalResult:
        """处理技能使用"""
        game = self.game_engine.get_game(game_id)
        if not game:
            raise ValueError(f"游戏不存在: {game_id}")
        
        source_player = game.players[player_id]
        target_player = game.players[target_player_id] if target_player_id is not None else None
        
        # 检查技能是否存在
        if not hasattr(source_player.character, 'has_skill') or not source_player.character.has_skill(skill_name):
            raise ValueError(f"玩家没有技能: {skill_name}")
        
        # 创建交互上下文
        context = InteractionContext(
            interaction_type=InteractionType.SKILL_USE,
            source_player=source_player,
            target_player=target_player,
            additional_data={
                'skill_name': skill_name,
                'game': game,
                **kwargs
            }
        )
        
        return self._execute_interaction(context)
    
    def process_damage(self, game_id: str, source_player_id: int, target_player_id: int, damage_amount: int = 1, damage_card=None) -> FinalResult:
        """处理伤害"""
        game = self.game_engine.get_game(game_id)
        if not game:
            raise ValueError(f"游戏不存在: {game_id}")
        
        source_player = game.players[source_player_id]
        target_player = game.players[target_player_id]
        
        # 创建交互上下文
        context = InteractionContext(
            interaction_type=InteractionType.DAMAGE,
            source_player=source_player,
            target_player=target_player,
            additional_data={
                'damage_amount': damage_amount,
                'damage_card': damage_card,
                'game': game
            }
        )
        
        return self._execute_interaction(context)
    
    def process_response(self, game_id: str, player_id: int, response_card_name: str, responding_to_context: InteractionContext) -> FinalResult:
        """处理响应"""
        game = self.game_engine.get_game(game_id)
        if not game:
            raise ValueError(f"游戏不存在: {game_id}")
        
        source_player = game.players[player_id]
        response_card = self._find_card_in_hand(source_player, response_card_name)
        
        if not response_card:
            raise ValueError(f"玩家没有响应卡牌: {response_card_name}")
        
        # 创建响应上下文
        context = InteractionContext(
            interaction_type=InteractionType.CARD_PLAY,
            source_player=source_player,
            card=response_card,
            additional_data={
                'responding_to': responding_to_context.card,
                'original_context': responding_to_context,
                'game': game
            }
        )
        
        return self._execute_interaction(context)
    
    def _execute_interaction(self, context: InteractionContext) -> FinalResult:
        """执行完整的交互流程"""
        logger.info(f"开始处理交互: {context.interaction_type}")
        
        try:
            # 阶段1: 判断
            if not self._check_conditions(context):
                return FinalResult(
                    result_type="failed",
                    success=False,
                    original_context=context,
                    final_context=context,
                    executed_effects=[],
                    blocked_effects=[{'type': 'original_action', 'reason': 'conditions_not_met'}]
                )
            
            # 阶段2: 修正
            modifications = self.modification_engine.process_modifications(context)
            
            # 阶段3: 裁决
            final_result = self.adjudication_engine.adjudicate(context, modifications)
            
            # 应用结果到游戏状态
            self._apply_result_to_game(final_result)
            
            logger.info(f"交互处理完成: {self.adjudication_engine.create_summary(final_result)}")
            return final_result
            
        except Exception as e:
            logger.error(f"交互处理失败: {e}")
            return FinalResult(
                result_type="failed",
                success=False,
                original_context=context,
                final_context=context,
                executed_effects=[],
                blocked_effects=[{'type': 'error', 'reason': str(e)}]
            )
    
    def _check_conditions(self, context: InteractionContext) -> bool:
        """检查条件"""
        # 根据交互类型和卡牌/技能名称确定判断键
        judgment_key = self._get_judgment_key(context)
        
        if judgment_key:
            return self.judgment_registry.check_all_conditions(judgment_key, context)
        
        # 如果没有特定的判断条件，返回True
        return True
    
    def _get_judgment_key(self, context: InteractionContext) -> Optional[str]:
        """获取判断键"""
        if context.interaction_type == InteractionType.CARD_PLAY:
            if context.card and hasattr(context.card, 'name'):
                card_name = context.card.name
                if card_name == "杀":
                    return "use_sha"
                elif card_name == "闪":
                    return "use_shan"
                elif card_name == "桃":
                    return "use_tao"
                elif card_name == "无懈可击":
                    return "use_wuxiekeji"
                elif card_name == "过河拆桥":
                    return "use_guohechaiqiao"
        
        elif context.interaction_type == InteractionType.SKILL_USE:
            skill_name = context.additional_data.get('skill_name')
            if skill_name:
                return f"use_{skill_name.lower()}"
        
        elif context.interaction_type == InteractionType.EQUIPMENT:
            if context.card and hasattr(context.card, 'equipment_type'):
                equipment_type = context.card.equipment_type
                return f"equip_{equipment_type}"
        
        return None
    
    def _find_card_in_hand(self, player: Player, card_name: str):
        """在玩家手牌中查找卡牌"""
        for card in player.hand_cards:
            if hasattr(card, 'name') and card.name == card_name:
                return card
        return None
    
    def _apply_result_to_game(self, result: FinalResult):
        """将结果应用到游戏状态"""
        game = result.original_context.additional_data.get('game')
        if not game:
            return
        
        # 应用执行的效果
        for effect in result.executed_effects:
            self._apply_single_effect(effect, game)
    
    def _apply_single_effect(self, effect: Dict[str, Any], game: Game):
        """应用单个效果到游戏状态"""
        effect_type = effect['type']
        
        try:
            if effect_type == 'card_play':
                # 卡牌使用效果
                player = effect['player']
                card = effect['card']
                if card in player.hand_cards:
                    player.hand_cards.remove(card)
                    game.discard_pile.append(card)
                    logger.info(f"{player.character.name}使用了{card.name}")
            
            elif effect_type == 'gain_card':
                # 获得卡牌效果
                player = effect['player']
                card = effect['card']
                player.hand_cards.append(card)
                logger.info(f"{player.character.name}获得了{card.name}")
            
            elif effect_type == 'lose_card' or effect_type == 'card_discarded':
                # 失去卡牌效果
                player = effect['player']
                card = effect['card']
                if card in player.hand_cards:
                    player.hand_cards.remove(card)
                    game.discard_pile.append(card)
                    logger.info(f"{player.character.name}失去了{card.name}")
            
            elif effect_type == 'damage':
                # 伤害效果
                target = effect['target']
                amount = effect.get('amount', 1)
                if hasattr(target, 'character') and hasattr(target.character, 'hp'):
                    target.character.hp = max(0, target.character.hp - amount)
                    logger.info(f"{target.character.name}受到{amount}点伤害，剩余体力{target.character.hp}")
            
            elif effect_type == 'recover_hp':
                # 回复体力效果
                player = effect['player']
                amount = effect.get('amount', 1)
                if hasattr(player, 'character') and hasattr(player.character, 'hp'):
                    max_hp = getattr(player.character, 'max_hp', 4)
                    player.character.hp = min(max_hp, player.character.hp + amount)
                    logger.info(f"{player.character.name}回复{amount}点体力，当前体力{player.character.hp}")
            
            elif effect_type == 'lose_hp':
                # 失去体力效果
                player = effect['player']
                amount = effect.get('amount', 1)
                if hasattr(player, 'character') and hasattr(player.character, 'hp'):
                    player.character.hp = max(0, player.character.hp - amount)
                    logger.info(f"{player.character.name}失去{amount}点体力，剩余体力{player.character.hp}")
        
        except Exception as e:
            logger.error(f"应用效果失败: {effect}, 错误: {e}")


class EnhancedGameEngine(GameEngine):
    """增强的游戏引擎，集成了新的交互系统"""
    
    def __init__(self):
        super().__init__()
        self.interaction_system = IntegratedInteractionSystem(self)
    
    def use_card(self, game_id: str, player_id: int, card_name: str, target_player_id: Optional[int] = None) -> Dict[str, Any]:
        """使用卡牌"""
        try:
            result = self.interaction_system.process_card_play(game_id, player_id, card_name, target_player_id)
            return {
                'success': result.success,
                'result_type': result.result_type.value if hasattr(result.result_type, 'value') else str(result.result_type),
                'summary': self.interaction_system.adjudication_engine.create_summary(result),
                'damage_dealt': result.damage_dealt,
                'cards_gained': len(result.cards_gained),
                'cards_lost': len(result.cards_lost),
                'hp_changed': result.hp_changed
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def use_skill(self, game_id: str, player_id: int, skill_name: str, target_player_id: Optional[int] = None, **kwargs) -> Dict[str, Any]:
        """使用技能"""
        try:
            result = self.interaction_system.process_skill_use(game_id, player_id, skill_name, target_player_id, **kwargs)
            return {
                'success': result.success,
                'result_type': result.result_type.value if hasattr(result.result_type, 'value') else str(result.result_type),
                'summary': self.interaction_system.adjudication_engine.create_summary(result),
                'damage_dealt': result.damage_dealt,
                'cards_gained': len(result.cards_gained),
                'cards_lost': len(result.cards_lost),
                'hp_changed': result.hp_changed
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def respond_with_card(self, game_id: str, player_id: int, response_card_name: str, original_context: InteractionContext) -> Dict[str, Any]:
        """使用卡牌响应"""
        try:
            result = self.interaction_system.process_response(game_id, player_id, response_card_name, original_context)
            return {
                'success': result.success,
                'result_type': result.result_type.value if hasattr(result.result_type, 'value') else str(result.result_type),
                'summary': self.interaction_system.adjudication_engine.create_summary(result),
                'blocked_original': any(effect.get('type') == 'original_action' for effect in result.blocked_effects)
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }