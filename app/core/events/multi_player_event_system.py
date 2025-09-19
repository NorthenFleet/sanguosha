"""
多玩家事件响应系统
实现事件驱动的多玩家交互响应机制
"""
from enum import Enum
from typing import Dict, List, Callable, Any, Optional, Tuple
from dataclasses import dataclass
import uuid
from abc import ABC, abstractmethod

class EventPriority(Enum):
    """事件优先级"""
    HIGHEST = 0    # 最高优先级（如无懈可击）
    HIGH = 1       # 高优先级（如闪避）
    NORMAL = 2     # 普通优先级（如技能响应）
    LOW = 3        # 低优先级（如被动技能）
    LOWEST = 4     # 最低优先级

class ResponseType(Enum):
    """响应类型"""
    IMMEDIATE = "immediate"     # 立即响应（如闪避）
    TRIGGERED = "triggered"     # 触发响应（如技能）
    PASSIVE = "passive"         # 被动响应（如被动技能）
    OPTIONAL = "optional"       # 可选响应（如是否发动技能）

@dataclass
class GameEvent:
    """游戏事件"""
    event_id: str
    event_type: str
    source_player_id: str
    target_player_ids: List[str]
    data: Dict[str, Any]
    timestamp: float
    can_be_responded: bool = True
    response_window_open: bool = True

@dataclass
class EventResponse:
    """事件响应"""
    response_id: str
    event_id: str
    player_id: str
    response_type: ResponseType
    priority: EventPriority
    action_data: Dict[str, Any]
    conditions_met: bool = True

class EventSubscription:
    """事件订阅"""
    def __init__(self, 
                 subscriber_id: str,
                 event_types: List[str],
                 handler: Callable,
                 priority: EventPriority = EventPriority.NORMAL,
                 conditions: Optional[Callable] = None):
        self.subscription_id = str(uuid.uuid4())
        self.subscriber_id = subscriber_id
        self.event_types = event_types
        self.handler = handler
        self.priority = priority
        self.conditions = conditions or (lambda event: True)
        self.active = True

class PlayerResponseHandler(ABC):
    """玩家响应处理器抽象基类"""
    
    @abstractmethod
    def can_respond(self, event: GameEvent) -> bool:
        """检查是否可以响应事件"""
        pass
    
    @abstractmethod
    def get_response_options(self, event: GameEvent) -> List[Dict[str, Any]]:
        """获取响应选项"""
        pass
    
    @abstractmethod
    def execute_response(self, event: GameEvent, response_data: Dict[str, Any]) -> EventResponse:
        """执行响应"""
        pass

class MultiPlayerEventSystem:
    """多玩家事件系统"""
    
    def __init__(self, players: List[str]):
        self.players = players
        self.current_player_index = 0
        self.subscriptions: Dict[str, List[EventSubscription]] = {}
        self.event_history: List[GameEvent] = []
        self.response_handlers: Dict[str, PlayerResponseHandler] = {}
        self.active_events: Dict[str, GameEvent] = {}
        
    def register_player_handler(self, player_id: str, handler: PlayerResponseHandler):
        """注册玩家响应处理器"""
        self.response_handlers[player_id] = handler
    
    def subscribe_to_event(self, subscription: EventSubscription):
        """订阅事件"""
        for event_type in subscription.event_types:
            if event_type not in self.subscriptions:
                self.subscriptions[event_type] = []
            self.subscriptions[event_type].append(subscription)
            # 按优先级排序
            self.subscriptions[event_type].sort(key=lambda x: x.priority.value)
    
    def unsubscribe_from_event(self, subscription_id: str):
        """取消订阅"""
        for event_type in self.subscriptions:
            self.subscriptions[event_type] = [
                sub for sub in self.subscriptions[event_type] 
                if sub.subscription_id != subscription_id
            ]
    
    def publish_event(self, event: GameEvent) -> List[EventResponse]:
        """发布事件并处理响应"""
        print(f"发布事件: {event.event_type} (来源: {event.source_player_id})")
        
        # 记录事件
        self.event_history.append(event)
        self.active_events[event.event_id] = event
        
        # 收集所有可能的响应
        potential_responses = self._collect_potential_responses(event)
        
        # 按玩家顺序和优先级处理响应
        actual_responses = self._process_responses_in_order(event, potential_responses)
        
        # 清理事件
        if event.event_id in self.active_events:
            del self.active_events[event.event_id]
        
        return actual_responses
    
    def _collect_potential_responses(self, event: GameEvent) -> List[Tuple[str, EventResponse]]:
        """收集所有潜在响应"""
        potential_responses = []
        
        # 获取响应顺序（从当前玩家的下家开始，逆时针）
        response_order = self._get_response_order(event.source_player_id)
        
        for player_id in response_order:
            # 检查玩家是否有响应处理器
            if player_id not in self.response_handlers:
                continue
                
            handler = self.response_handlers[player_id]
            
            # 检查是否可以响应
            if not handler.can_respond(event):
                continue
            
            # 获取响应选项
            response_options = handler.get_response_options(event)
            
            for option in response_options:
                # 创建响应对象
                response = EventResponse(
                    response_id=str(uuid.uuid4()),
                    event_id=event.event_id,
                    player_id=player_id,
                    response_type=ResponseType(option.get('type', 'optional')),
                    priority=EventPriority(option.get('priority', EventPriority.NORMAL.value)),
                    action_data=option.get('data', {}),
                    conditions_met=option.get('conditions_met', True)
                )
                
                potential_responses.append((player_id, response))
        
        return potential_responses
    
    def _process_responses_in_order(self, event: GameEvent, potential_responses: List[Tuple[str, EventResponse]]) -> List[EventResponse]:
        """按顺序处理响应"""
        actual_responses = []
        
        # 按优先级分组
        priority_groups = {}
        for player_id, response in potential_responses:
            priority = response.priority
            if priority not in priority_groups:
                priority_groups[priority] = []
            priority_groups[priority].append((player_id, response))
        
        # 按优先级顺序处理
        for priority in sorted(priority_groups.keys(), key=lambda x: x.value):
            group_responses = priority_groups[priority]
            
            # 在同一优先级内，按玩家顺序处理
            response_order = self._get_response_order(event.source_player_id)
            ordered_group = []
            
            for player_id in response_order:
                for p_id, response in group_responses:
                    if p_id == player_id:
                        ordered_group.append((p_id, response))
            
            # 处理这个优先级组的响应
            for player_id, response in ordered_group:
                if self._should_process_response(event, response, actual_responses):
                    # 执行响应
                    handler = self.response_handlers[player_id]
                    executed_response = handler.execute_response(event, response.action_data)
                    actual_responses.append(executed_response)
                    
                    print(f"玩家 {player_id} 响应事件: {response.response_type.value}")
                    
                    # 某些响应可能会终止后续响应
                    if self._response_terminates_chain(response):
                        print(f"响应链被终止")
                        return actual_responses
        
        return actual_responses
    
    def _get_response_order(self, source_player_id: str) -> List[str]:
        """获取响应顺序（从源玩家的下家开始逆时针）"""
        try:
            source_index = self.players.index(source_player_id)
        except ValueError:
            return self.players.copy()
        
        # 从下家开始的顺序
        order = []
        for i in range(1, len(self.players)):
            next_index = (source_index + i) % len(self.players)
            order.append(self.players[next_index])
        
        return order
    
    def _should_process_response(self, event: GameEvent, response: EventResponse, processed_responses: List[EventResponse]) -> bool:
        """判断是否应该处理这个响应"""
        # 检查事件是否还允许响应
        if not event.response_window_open:
            return False
        
        # 检查响应条件
        if not response.conditions_met:
            return False
        
        # 检查是否与已处理的响应冲突
        for processed in processed_responses:
            if self._responses_conflict(response, processed):
                return False
        
        return True
    
    def _responses_conflict(self, response1: EventResponse, response2: EventResponse) -> bool:
        """检查两个响应是否冲突"""
        # 同一玩家不能对同一事件多次响应（除非是不同类型）
        if (response1.player_id == response2.player_id and 
            response1.event_id == response2.event_id and
            response1.response_type == response2.response_type):
            return True
        
        # 某些响应类型互斥
        exclusive_pairs = [
            (ResponseType.IMMEDIATE, ResponseType.TRIGGERED),
        ]
        
        for type1, type2 in exclusive_pairs:
            if ((response1.response_type == type1 and response2.response_type == type2) or
                (response1.response_type == type2 and response2.response_type == type1)):
                return True
        
        return False
    
    def _response_terminates_chain(self, response: EventResponse) -> bool:
        """检查响应是否终止响应链"""
        # 某些响应会终止后续响应
        terminating_actions = ['counter', 'cancel', 'redirect']
        
        action_type = response.action_data.get('action_type', '')
        return action_type in terminating_actions
    
    def get_event_subscribers(self, event_type: str) -> List[EventSubscription]:
        """获取事件的订阅者"""
        return self.subscriptions.get(event_type, [])
    
    def get_active_events(self) -> List[GameEvent]:
        """获取当前活跃的事件"""
        return list(self.active_events.values())
    
    def clear_event_history(self):
        """清空事件历史"""
        self.event_history.clear()
        self.active_events.clear()

# 具体的响应处理器实现示例
class BasicCardResponseHandler(PlayerResponseHandler):
    """基础卡牌响应处理器"""
    
    def __init__(self, player_id: str, player_cards: List[Any]):
        self.player_id = player_id
        self.player_cards = player_cards
    
    def can_respond(self, event: GameEvent) -> bool:
        """检查是否可以响应"""
        # 检查是否是目标玩家
        if self.player_id not in event.target_player_ids:
            return False
        
        # 检查是否有可用的响应卡牌
        return len(self._get_available_response_cards(event)) > 0
    
    def get_response_options(self, event: GameEvent) -> List[Dict[str, Any]]:
        """获取响应选项"""
        options = []
        available_cards = self._get_available_response_cards(event)
        
        for card in available_cards:
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
    
    def execute_response(self, event: GameEvent, response_data: Dict[str, Any]) -> EventResponse:
        """执行响应"""
        card = response_data.get('card')
        
        # 从手牌中移除卡牌
        if card in self.player_cards:
            self.player_cards.remove(card)
        
        return EventResponse(
            response_id=str(uuid.uuid4()),
            event_id=event.event_id,
            player_id=self.player_id,
            response_type=ResponseType.IMMEDIATE,
            priority=EventPriority.HIGH,
            action_data=response_data,
            conditions_met=True
        )
    
    def _get_available_response_cards(self, event: GameEvent) -> List[Any]:
        """获取可用的响应卡牌"""
        # 根据事件类型返回可用的响应卡牌
        event_type = event.event_type
        available_cards = []
        
        for card in self.player_cards:
            if hasattr(card, 'category'):
                if event_type == 'attack' and card.category == 'basic' and hasattr(card, 'name') and card.name == '闪':
                    available_cards.append(card)
                elif event_type == 'trick_card' and card.category == 'trick' and hasattr(card, 'name') and card.name == '无懈可击':
                    available_cards.append(card)
        
        return available_cards

class SkillResponseHandler(PlayerResponseHandler):
    """技能响应处理器"""
    
    def __init__(self, player_id: str, character_skills: List[Any]):
        self.player_id = player_id
        self.character_skills = character_skills
    
    def can_respond(self, event: GameEvent) -> bool:
        """检查是否可以响应"""
        # 检查是否有可触发的技能
        return len(self._get_triggerable_skills(event)) > 0
    
    def get_response_options(self, event: GameEvent) -> List[Dict[str, Any]]:
        """获取响应选项"""
        options = []
        triggerable_skills = self._get_triggerable_skills(event)
        
        for skill in triggerable_skills:
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
    
    def execute_response(self, event: GameEvent, response_data: Dict[str, Any]) -> EventResponse:
        """执行响应"""
        skill = response_data.get('skill')
        
        # 执行技能效果
        if hasattr(skill, 'execute'):
            skill.execute(event)
        
        return EventResponse(
            response_id=str(uuid.uuid4()),
            event_id=event.event_id,
            player_id=self.player_id,
            response_type=ResponseType.TRIGGERED,
            priority=EventPriority.NORMAL,
            action_data=response_data,
            conditions_met=True
        )
    
    def _get_triggerable_skills(self, event: GameEvent) -> List[Any]:
        """获取可触发的技能"""
        triggerable = []
        
        for skill in self.character_skills:
            if hasattr(skill, 'trigger_events') and event.event_type in skill.trigger_events:
                triggerable.append(skill)
        
        return triggerable
    
    def _check_skill_conditions(self, skill: Any, event: GameEvent) -> bool:
        """检查技能触发条件"""
        if hasattr(skill, 'check_conditions'):
            return skill.check_conditions(event)
        return True