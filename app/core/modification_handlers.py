#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
三国杀修正阶段实现
处理各种响应、技能触发、卡牌效果修正
"""

from typing import Dict, List, Optional, Callable, Any
from dataclasses import dataclass
from enum import Enum
from .interaction_model import InteractionContext, InteractionType, ResponseType
import logging

logger = logging.getLogger(__name__)


class ModificationPriority(Enum):
    """修正优先级"""
    HIGHEST = 1      # 最高优先级（如锁定技）
    HIGH = 2         # 高优先级（如主动技能）
    NORMAL = 3       # 普通优先级（如装备效果）
    LOW = 4          # 低优先级（如被动效果）
    LOWEST = 5       # 最低优先级（如默认规则）


@dataclass
class ModificationResult:
    """修正结果"""
    success: bool                           # 修正是否成功
    modified_context: InteractionContext    # 修正后的上下文
    additional_effects: List[Dict[str, Any]] = None  # 额外效果
    block_original: bool = False            # 是否阻止原始行为
    trigger_new_interaction: Optional[InteractionContext] = None  # 是否触发新的交互


class ModificationHandler:
    """修正处理器基类"""
    
    def __init__(self, priority: ModificationPriority = ModificationPriority.NORMAL):
        self.priority = priority
    
    def can_handle(self, context: InteractionContext) -> bool:
        """判断是否可以处理此修正"""
        raise NotImplementedError
    
    def handle(self, context: InteractionContext) -> ModificationResult:
        """处理修正"""
        raise NotImplementedError


class ShanResponseHandler(ModificationHandler):
    """闪的响应处理器"""
    
    def __init__(self):
        super().__init__(ModificationPriority.HIGH)
    
    def can_handle(self, context: InteractionContext) -> bool:
        """判断是否可以处理闪的响应"""
        if context.interaction_type != InteractionType.CARD_PLAY:
            return False
        
        # 检查是否是对杀的响应
        if 'responding_to' in context.additional_data:
            responding_card = context.additional_data['responding_to']
            if hasattr(responding_card, 'name') and responding_card.name == "杀":
                return True
        
        return False
    
    def handle(self, context: InteractionContext) -> ModificationResult:
        """处理闪的响应"""
        logger.info(f"{context.source_player}使用闪响应杀")
        
        # 创建修正后的上下文
        modified_context = context
        modified_context.additional_data['shan_used'] = True
        
        # 阻止杀的伤害
        return ModificationResult(
            success=True,
            modified_context=modified_context,
            block_original=True,  # 阻止杀造成伤害
            additional_effects=[{
                'type': 'card_discarded',
                'player': context.source_player,
                'card': context.card
            }]
        )


class WuxiekejiHandler(ModificationHandler):
    """无懈可击处理器"""
    
    def __init__(self):
        super().__init__(ModificationPriority.HIGHEST)
    
    def can_handle(self, context: InteractionContext) -> bool:
        """判断是否可以处理无懈可击"""
        if context.interaction_type != InteractionType.CARD_PLAY:
            return False
        
        # 检查是否是对锦囊的响应
        if 'responding_to' in context.additional_data:
            responding_card = context.additional_data['responding_to']
            if hasattr(responding_card, 'category') and responding_card.category == 'trick':
                return True
        
        return False
    
    def handle(self, context: InteractionContext) -> ModificationResult:
        """处理无懈可击"""
        logger.info(f"{context.source_player}使用无懈可击")
        
        modified_context = context
        modified_context.additional_data['wuxiekeji_used'] = True
        
        return ModificationResult(
            success=True,
            modified_context=modified_context,
            block_original=True,  # 阻止锦囊效果
            additional_effects=[{
                'type': 'card_discarded',
                'player': context.source_player,
                'card': context.card
            }]
        )


class JianxiongSkillHandler(ModificationHandler):
    """奸雄技能处理器"""
    
    def __init__(self):
        super().__init__(ModificationPriority.HIGH)
    
    def can_handle(self, context: InteractionContext) -> bool:
        """判断是否可以触发奸雄"""
        if context.interaction_type != InteractionType.DAMAGE:
            return False
        
        # 检查是否有奸雄技能
        if hasattr(context.target_player, 'has_skill') and context.target_player.has_skill("奸雄"):
            return True
        
        return False
    
    def handle(self, context: InteractionContext) -> ModificationResult:
        """处理奸雄技能"""
        logger.info(f"{context.target_player}触发奸雄技能")
        
        modified_context = context
        damage_card = context.additional_data.get('damage_card')
        
        additional_effects = []
        if damage_card:
            additional_effects.append({
                'type': 'gain_card',
                'player': context.target_player,
                'card': damage_card,
                'reason': '奸雄'
            })
        
        return ModificationResult(
            success=True,
            modified_context=modified_context,
            additional_effects=additional_effects
        )


class RendeSkillHandler(ModificationHandler):
    """仁德技能处理器"""
    
    def __init__(self):
        super().__init__(ModificationPriority.NORMAL)
    
    def can_handle(self, context: InteractionContext) -> bool:
        """判断是否可以使用仁德"""
        if context.interaction_type != InteractionType.SKILL_USE:
            return False
        
        if hasattr(context.source_player, 'has_skill') and context.source_player.has_skill("仁德"):
            return True
        
        return False
    
    def handle(self, context: InteractionContext) -> ModificationResult:
        """处理仁德技能"""
        logger.info(f"{context.source_player}使用仁德技能")
        
        cards_to_give = context.additional_data.get('cards_to_give', [])
        target_player = context.target_player
        
        additional_effects = []
        for card in cards_to_give:
            additional_effects.extend([
                {
                    'type': 'lose_card',
                    'player': context.source_player,
                    'card': card,
                    'reason': '仁德'
                },
                {
                    'type': 'gain_card',
                    'player': target_player,
                    'card': card,
                    'reason': '仁德'
                }
            ])
        
        # 仁德的额外效果：如果给出的牌数达到2张或更多，可以回复1点体力
        if len(cards_to_give) >= 2:
            additional_effects.append({
                'type': 'recover_hp',
                'player': context.source_player,
                'amount': 1,
                'reason': '仁德'
            })
        
        return ModificationResult(
            success=True,
            modified_context=context,
            additional_effects=additional_effects
        )


class PaoxiaoSkillHandler(ModificationHandler):
    """咆哮技能处理器"""
    
    def __init__(self):
        super().__init__(ModificationPriority.HIGHEST)  # 锁定技，最高优先级
    
    def can_handle(self, context: InteractionContext) -> bool:
        """判断是否触发咆哮"""
        if context.interaction_type != InteractionType.CARD_PLAY:
            return False
        
        if not context.card or not hasattr(context.card, 'name') or context.card.name != "杀":
            return False
        
        if hasattr(context.source_player, 'has_skill') and context.source_player.has_skill("咆哮"):
            return True
        
        return False
    
    def handle(self, context: InteractionContext) -> ModificationResult:
        """处理咆哮技能"""
        logger.info(f"{context.source_player}的咆哮技能生效，无出杀次数限制")
        
        modified_context = context
        # 移除出杀次数限制
        modified_context.additional_data['ignore_sha_limit'] = True
        
        return ModificationResult(
            success=True,
            modified_context=modified_context
        )


class WeaponEffectHandler(ModificationHandler):
    """武器效果处理器"""
    
    def __init__(self):
        super().__init__(ModificationPriority.NORMAL)
    
    def can_handle(self, context: InteractionContext) -> bool:
        """判断是否有武器效果"""
        if context.interaction_type != InteractionType.CARD_PLAY:
            return False
        
        if not context.card or not hasattr(context.card, 'name') or context.card.name != "杀":
            return False
        
        # 检查是否装备了武器
        if hasattr(context.source_player, 'equipment_area') and 'weapon' in context.source_player.equipment_area:
            weapon = context.source_player.equipment_area['weapon']
            if weapon is not None:
                return True
        
        return False
    
    def handle(self, context: InteractionContext) -> ModificationResult:
        """处理武器效果"""
        weapon = context.source_player.equipment_area['weapon']
        weapon_name = weapon.name if hasattr(weapon, 'name') else "未知武器"
        
        logger.info(f"{context.source_player}的{weapon_name}效果触发")
        
        modified_context = context
        additional_effects = []
        
        # 根据不同武器添加不同效果
        if hasattr(weapon, 'name'):
            if weapon.name == "青龙偃月刀":
                # 青龙偃月刀：杀被闪避后可以再出一张杀
                modified_context.additional_data['qinglong_effect'] = True
            elif weapon.name == "丈八蛇矛":
                # 丈八蛇矛：可以将两张手牌当杀使用
                modified_context.additional_data['zhangba_effect'] = True
            elif weapon.name == "贯石斧":
                # 贯石斧：杀被闪避后可以弃置两张牌令杀依然造成伤害
                modified_context.additional_data['guanshi_effect'] = True
        
        return ModificationResult(
            success=True,
            modified_context=modified_context,
            additional_effects=additional_effects
        )


class ArmorEffectHandler(ModificationHandler):
    """防具效果处理器"""
    
    def __init__(self):
        super().__init__(ModificationPriority.HIGH)
    
    def can_handle(self, context: InteractionContext) -> bool:
        """判断是否有防具效果"""
        if context.interaction_type != InteractionType.DAMAGE:
            return False
        
        # 检查目标是否装备了防具
        if hasattr(context.target_player, 'equipment_area') and 'armor' in context.target_player.equipment_area:
            armor = context.target_player.equipment_area['armor']
            if armor is not None:
                return True
        
        return False
    
    def handle(self, context: InteractionContext) -> ModificationResult:
        """处理防具效果"""
        armor = context.target_player.equipment_area['armor']
        armor_name = armor.name if hasattr(armor, 'name') else "未知防具"
        
        logger.info(f"{context.target_player}的{armor_name}效果触发")
        
        modified_context = context
        additional_effects = []
        block_original = False
        
        # 根据不同防具添加不同效果
        if hasattr(armor, 'name'):
            if armor.name == "八卦阵":
                # 八卦阵：可以进行判定，红色则视为使用了闪
                modified_context.additional_data['bagua_judgment'] = True
            elif armor.name == "仁王盾":
                # 仁王盾：黑色杀对你无效
                damage_card = context.additional_data.get('damage_card')
                if damage_card and hasattr(damage_card, 'suit') and damage_card.suit in ['♠', '♣']:
                    block_original = True
                    logger.info("仁王盾效果：黑色杀无效")
            elif armor.name == "白银狮子":
                # 白银狮子：受到的伤害最多为1点
                if 'damage_amount' in context.additional_data and context.additional_data['damage_amount'] > 1:
                    modified_context.additional_data['damage_amount'] = 1
                    logger.info("白银狮子效果：伤害减少至1点")
        
        return ModificationResult(
            success=True,
            modified_context=modified_context,
            additional_effects=additional_effects,
            block_original=block_original
        )


class ModificationEngine:
    """修正引擎"""
    
    def __init__(self):
        self.handlers: List[ModificationHandler] = []
        self._register_default_handlers()
    
    def _register_default_handlers(self):
        """注册默认的修正处理器"""
        self.handlers.extend([
            ShanResponseHandler(),
            WuxiekejiHandler(),
            JianxiongSkillHandler(),
            RendeSkillHandler(),
            PaoxiaoSkillHandler(),
            WeaponEffectHandler(),
            ArmorEffectHandler()
        ])
        
        # 按优先级排序
        self.handlers.sort(key=lambda h: h.priority.value)
    
    def register_handler(self, handler: ModificationHandler):
        """注册修正处理器"""
        self.handlers.append(handler)
        self.handlers.sort(key=lambda h: h.priority.value)
    
    def process_modifications(self, context: InteractionContext) -> List[ModificationResult]:
        """处理所有修正"""
        results = []
        current_context = context
        
        for handler in self.handlers:
            if handler.can_handle(current_context):
                try:
                    result = handler.handle(current_context)
                    results.append(result)
                    
                    # 如果修正成功，更新当前上下文
                    if result.success:
                        current_context = result.modified_context
                        
                        # 如果阻止原始行为，停止后续处理
                        if result.block_original:
                            logger.info("修正阻止了原始行为，停止后续处理")
                            break
                            
                except Exception as e:
                    logger.error(f"修正处理器 {handler.__class__.__name__} 处理失败: {e}")
        
        return results
    
    def has_blocking_modification(self, results: List[ModificationResult]) -> bool:
        """检查是否有阻止原始行为的修正"""
        return any(result.block_original for result in results)
    
    def get_all_additional_effects(self, results: List[ModificationResult]) -> List[Dict[str, Any]]:
        """获取所有额外效果"""
        all_effects = []
        for result in results:
            if result.additional_effects:
                all_effects.extend(result.additional_effects)
        return all_effects