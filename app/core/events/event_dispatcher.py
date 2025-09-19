"""
事件分发器
集成多玩家事件系统与现有的交互模型
"""
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass
import time
import uuid
from .multi_player_event_system import (
    MultiPlayerEventSystem, GameEvent, EventResponse, 
    PlayerResponseHandler, EventSubscription, EventPriority, ResponseType
)
from ..interaction.interaction_model import InteractionContext, InteractionResult
from ..adjudication.adjudication_engine import AdjudicationEngine, AdjudicationResult

@dataclass
class EventContext:
    """事件上下文"""
    game_id: str
    current_player_id: str
    phase: str
    turn_number: int
    additional_data: Dict[str, Any]

class GameEventDispatcher:
    """游戏事件分发器"""
    
    def __init__(self, players: List[str], adjudication_engine: Optional[AdjudicationEngine] = None):
        self.event_system = MultiPlayerEventSystem(players)
        self.adjudication_engine = adjudication_engine or AdjudicationEngine()
        self.event_context = None
        self.event_queue = []
        self.processing_event = False
        
        # 事件类型映射
        self.event_type_mapping = {
            'card_play': 'play_card',
            'card_use': 'use_card', 
            'skill_use': 'use_skill',
            'damage_deal': 'deal_damage',
            'damage_take': 'take_damage',
            'card_draw': 'draw_card',
            'card_discard': 'discard_card',
            'phase_change': 'phase_change',
            'equipment_equip': 'equip_equipment',
            'equipment_unequip': 'unequip_equipment'
        }
    
    def set_context(self, context: EventContext):
        """设置事件上下文"""
        self.event_context = context
    
    def register_player_handler(self, player_id: str, handler: PlayerResponseHandler):
        """注册玩家响应处理器"""
        self.event_system.register_player_handler(player_id, handler)
    
    def subscribe_to_events(self, subscription: EventSubscription):
        """订阅事件"""
        self.event_system.subscribe_to_event(subscription)
    
    def dispatch_card_event(self, 
                          source_player_id: str,
                          target_player_ids: List[str],
                          card: Any,
                          action_type: str = 'play') -> List[EventResponse]:
        """分发卡牌事件"""
        event_type = f'card_{action_type}'
        
        event_data = {
            'card': card,
            'card_name': getattr(card, 'name', ''),
            'card_category': getattr(card, 'category', ''),
            'card_rank': getattr(card, 'rank', ''),
            'card_suit': getattr(card, 'suit', ''),
            'action_type': action_type,
            'context': self.event_context.__dict__ if self.event_context else {}
        }
        
        return self._dispatch_event(event_type, source_player_id, target_player_ids, event_data)
    
    def dispatch_skill_event(self,
                           source_player_id: str,
                           target_player_ids: List[str],
                           skill: Any,
                           trigger_condition: str = '') -> List[EventResponse]:
        """分发技能事件"""
        event_data = {
            'skill': skill,
            'skill_name': getattr(skill, 'name', ''),
            'skill_type': getattr(skill, 'skill_type', ''),
            'trigger_condition': trigger_condition,
            'context': self.event_context.__dict__ if self.event_context else {}
        }
        
        return self._dispatch_event('skill_use', source_player_id, target_player_ids, event_data)
    
    def dispatch_damage_event(self,
                            source_player_id: str,
                            target_player_id: str,
                            damage_amount: int,
                            damage_type: str = 'normal') -> List[EventResponse]:
        """分发伤害事件"""
        event_data = {
            'damage_amount': damage_amount,
            'damage_type': damage_type,
            'source': source_player_id,
            'context': self.event_context.__dict__ if self.event_context else {}
        }
        
        return self._dispatch_event('damage_deal', source_player_id, [target_player_id], event_data)
    
    def dispatch_phase_change_event(self,
                                  player_id: str,
                                  old_phase: str,
                                  new_phase: str) -> List[EventResponse]:
        """分发阶段变化事件"""
        event_data = {
            'old_phase': old_phase,
            'new_phase': new_phase,
            'player': player_id,
            'context': self.event_context.__dict__ if self.event_context else {}
        }
        
        # 阶段变化事件通知所有玩家
        all_players = self.event_system.players.copy()
        return self._dispatch_event('phase_change', player_id, all_players, event_data)
    
    def _dispatch_event(self,
                       event_type: str,
                       source_player_id: str,
                       target_player_ids: List[str],
                       event_data: Dict[str, Any]) -> List[EventResponse]:
        """内部事件分发方法"""
        
        # 防止事件循环
        if self.processing_event:
            self.event_queue.append((event_type, source_player_id, target_player_ids, event_data))
            return []
        
        self.processing_event = True
        
        try:
            # 创建游戏事件
            game_event = GameEvent(
                event_id=str(uuid.uuid4()),
                event_type=self.event_type_mapping.get(event_type, event_type),
                source_player_id=source_player_id,
                target_player_ids=target_player_ids,
                data=event_data,
                timestamp=time.time(),
                can_be_responded=True,
                response_window_open=True
            )
            
            # 发布事件并收集响应
            responses = self.event_system.publish_event(game_event)
            
            # 处理队列中的事件
            while self.event_queue:
                queued_event = self.event_queue.pop(0)
                queued_responses = self._dispatch_event(*queued_event)
                responses.extend(queued_responses)
            
            return responses
            
        finally:
            self.processing_event = False
    
    def create_interaction_context_from_event(self, event: GameEvent) -> InteractionContext:
        """从事件创建交互上下文"""
        return InteractionContext(
            interaction_id=event.event_id,
            source_player_id=event.source_player_id,
            target_player_ids=event.target_player_ids,
            interaction_type=event.event_type,
            card=event.data.get('card'),
            skill=event.data.get('skill'),
            additional_data=event.data
        )
    
    def process_with_adjudication(self, event: GameEvent) -> InteractionResult:
        """使用裁决引擎处理事件"""
        context = self.create_interaction_context_from_event(event)
        return self.adjudication_engine.adjudicate_interaction(context)

class IntegratedEventHandler(PlayerResponseHandler):
    """集成事件处理器"""
    
    def __init__(self, 
                 player_id: str,
                 player_data: Dict[str, Any],
                 response_callback: Optional[Callable] = None):
        self.player_id = player_id
        self.player_data = player_data
        self.response_callback = response_callback
        
        # 玩家状态
        self.hand_cards = player_data.get('hand_cards', [])
        self.equipment_cards = player_data.get('equipment_cards', [])
        self.character_skills = player_data.get('character_skills', [])
        self.hp = player_data.get('hp', 4)
        self.max_hp = player_data.get('max_hp', 4)
        self.is_alive = player_data.get('is_alive', True)
    
    def can_respond(self, event: GameEvent) -> bool:
        """检查是否可以响应事件"""
        # 死亡玩家不能响应大部分事件
        if not self.is_alive and event.event_type not in ['player_death', 'game_end']:
            return False
        
        # 检查是否是事件目标
        if (self.player_id not in event.target_player_ids and 
            event.event_type not in ['phase_change', 'skill_use']):
            return False
        
        # 检查具体响应能力
        return self._check_specific_response_ability(event)
    
    def get_response_options(self, event: GameEvent) -> List[Dict[str, Any]]:
        """获取响应选项"""
        options = []
        
        # 基础卡牌响应
        card_options = self._get_card_response_options(event)
        options.extend(card_options)
        
        # 技能响应
        skill_options = self._get_skill_response_options(event)
        options.extend(skill_options)
        
        # 装备响应
        equipment_options = self._get_equipment_response_options(event)
        options.extend(equipment_options)
        
        return options
    
    def execute_response(self, event: GameEvent, response_data: Dict[str, Any]) -> EventResponse:
        """执行响应"""
        action_type = response_data.get('action_type', '')
        
        if action_type == 'play_card':
            return self._execute_card_response(event, response_data)
        elif action_type == 'use_skill':
            return self._execute_skill_response(event, response_data)
        elif action_type == 'use_equipment':
            return self._execute_equipment_response(event, response_data)
        else:
            return self._execute_default_response(event, response_data)
    
    def _check_specific_response_ability(self, event: GameEvent) -> bool:
        """检查具体的响应能力"""
        event_type = event.event_type
        
        if event_type == 'play_card':
            # 检查是否有闪避卡牌
            card_data = event.data.get('card', {})
            if hasattr(card_data, 'name') and card_data.name == '杀':
                return any(hasattr(card, 'name') and card.name == '闪' for card in self.hand_cards)
        
        elif event_type == 'use_card':
            # 检查是否有无懈可击
            card_data = event.data.get('card', {})
            if hasattr(card_data, 'category') and card_data.category == 'trick':
                return any(hasattr(card, 'name') and card.name == '无懈可击' for card in self.hand_cards)
        
        elif event_type == 'deal_damage':
            # 检查是否有防御技能
            return any(hasattr(skill, 'skill_type') and 'defense' in skill.skill_type 
                      for skill in self.character_skills)
        
        return True
    
    def _get_card_response_options(self, event: GameEvent) -> List[Dict[str, Any]]:
        """获取卡牌响应选项"""
        options = []
        
        for card in self.hand_cards:
            if self._card_can_respond_to_event(card, event):
                option = {
                    'type': 'immediate',
                    'priority': EventPriority.HIGH.value,
                    'data': {
                        'action_type': 'play_card',
                        'card': card,
                        'target': event.source_player_id
                    },
                    'conditions_met': True
                }
                options.append(option)
        
        return options
    
    def _get_skill_response_options(self, event: GameEvent) -> List[Dict[str, Any]]:
        """获取技能响应选项"""
        options = []
        
        for skill in self.character_skills:
            if self._skill_can_respond_to_event(skill, event):
                option = {
                    'type': 'triggered',
                    'priority': getattr(skill, 'priority', EventPriority.NORMAL.value),
                    'data': {
                        'action_type': 'use_skill',
                        'skill': skill,
                        'target': event.source_player_id
                    },
                    'conditions_met': self._check_skill_conditions(skill, event)
                }
                options.append(option)
        
        return options
    
    def _get_equipment_response_options(self, event: GameEvent) -> List[Dict[str, Any]]:
        """获取装备响应选项"""
        options = []
        
        for equipment in self.equipment_cards:
            if self._equipment_can_respond_to_event(equipment, event):
                option = {
                    'type': 'passive',
                    'priority': EventPriority.LOW.value,
                    'data': {
                        'action_type': 'use_equipment',
                        'equipment': equipment,
                        'target': event.source_player_id
                    },
                    'conditions_met': True
                }
                options.append(option)
        
        return options
    
    def _card_can_respond_to_event(self, card: Any, event: GameEvent) -> bool:
        """检查卡牌是否可以响应事件"""
        if not hasattr(card, 'name'):
            return False
        
        event_type = event.event_type
        card_name = card.name
        
        # 闪避杀
        if event_type == 'play_card' and card_name == '闪':
            event_card = event.data.get('card')
            return hasattr(event_card, 'name') and event_card.name == '杀'
        
        # 无懈可击锦囊
        if event_type == 'use_card' and card_name == '无懈可击':
            event_card = event.data.get('card')
            return hasattr(event_card, 'category') and event_card.category == 'trick'
        
        return False
    
    def _skill_can_respond_to_event(self, skill: Any, event: GameEvent) -> bool:
        """检查技能是否可以响应事件"""
        if not hasattr(skill, 'trigger_events'):
            return False
        
        return event.event_type in skill.trigger_events
    
    def _equipment_can_respond_to_event(self, equipment: Any, event: GameEvent) -> bool:
        """检查装备是否可以响应事件"""
        if not hasattr(equipment, 'passive_effects'):
            return False
        
        # 检查装备的被动效果是否适用于当前事件
        return event.event_type in getattr(equipment, 'applicable_events', [])
    
    def _check_skill_conditions(self, skill: Any, event: GameEvent) -> bool:
        """检查技能触发条件"""
        if hasattr(skill, 'check_conditions'):
            return skill.check_conditions(event, self.player_data)
        return True
    
    def _execute_card_response(self, event: GameEvent, response_data: Dict[str, Any]) -> EventResponse:
        """执行卡牌响应"""
        card = response_data.get('card')
        
        # 从手牌中移除
        if card in self.hand_cards:
            self.hand_cards.remove(card)
        
        # 调用回调函数
        if self.response_callback:
            self.response_callback('card_played', {
                'player_id': self.player_id,
                'card': card,
                'event': event
            })
        
        return EventResponse(
            response_id=str(uuid.uuid4()),
            event_id=event.event_id,
            player_id=self.player_id,
            response_type=ResponseType.IMMEDIATE,
            priority=EventPriority.HIGH,
            action_data=response_data,
            conditions_met=True
        )
    
    def _execute_skill_response(self, event: GameEvent, response_data: Dict[str, Any]) -> EventResponse:
        """执行技能响应"""
        skill = response_data.get('skill')
        
        # 执行技能效果
        if hasattr(skill, 'execute'):
            skill.execute(event, self.player_data)
        
        # 调用回调函数
        if self.response_callback:
            self.response_callback('skill_used', {
                'player_id': self.player_id,
                'skill': skill,
                'event': event
            })
        
        return EventResponse(
            response_id=str(uuid.uuid4()),
            event_id=event.event_id,
            player_id=self.player_id,
            response_type=ResponseType.TRIGGERED,
            priority=EventPriority.NORMAL,
            action_data=response_data,
            conditions_met=True
        )
    
    def _execute_equipment_response(self, event: GameEvent, response_data: Dict[str, Any]) -> EventResponse:
        """执行装备响应"""
        equipment = response_data.get('equipment')
        
        # 触发装备效果
        if hasattr(equipment, 'trigger_effect'):
            equipment.trigger_effect(event, self.player_data)
        
        return EventResponse(
            response_id=str(uuid.uuid4()),
            event_id=event.event_id,
            player_id=self.player_id,
            response_type=ResponseType.PASSIVE,
            priority=EventPriority.LOW,
            action_data=response_data,
            conditions_met=True
        )
    
    def _execute_default_response(self, event: GameEvent, response_data: Dict[str, Any]) -> EventResponse:
        """执行默认响应"""
        return EventResponse(
            response_id=str(uuid.uuid4()),
            event_id=event.event_id,
            player_id=self.player_id,
            response_type=ResponseType.OPTIONAL,
            priority=EventPriority.NORMAL,
            action_data=response_data,
            conditions_met=True
        )