"""
技能事件处理器
实现武将技能与事件系统的集成，处理技能的事件订阅和响应
"""
from typing import Dict, List, Any, Optional, Callable, Set
from dataclasses import dataclass
from enum import Enum
from abc import ABC, abstractmethod
import uuid

from .multi_player_event_system import (
    GameEvent, EventResponse, EventSubscription, EventPriority, ResponseType
)
from .event_dispatcher import PlayerResponseHandler

class SkillTriggerType(Enum):
    """技能触发类型"""
    ACTIVE = "active"           # 主动技能
    PASSIVE = "passive"         # 被动技能
    TRIGGERED = "triggered"     # 触发技能
    CONTINUOUS = "continuous"   # 持续技能
    EQUIPMENT = "equipment"     # 装备技能

class SkillTiming(Enum):
    """技能时机"""
    BEFORE_EVENT = "before"     # 事件前
    DURING_EVENT = "during"     # 事件中
    AFTER_EVENT = "after"       # 事件后
    REPLACE_EVENT = "replace"   # 替代事件

@dataclass
class SkillEventBinding:
    """技能事件绑定"""
    skill_name: str
    event_types: List[str]
    trigger_type: SkillTriggerType
    timing: SkillTiming
    priority: EventPriority
    conditions: Optional[Callable] = None
    max_uses_per_turn: Optional[int] = None
    max_uses_per_game: Optional[int] = None

class SkillEventHandler(ABC):
    """技能事件处理器抽象基类"""
    
    def __init__(self, skill_name: str, player_id: str):
        self.skill_name = skill_name
        self.player_id = player_id
        self.uses_this_turn = 0
        self.uses_this_game = 0
        self.is_active = True
    
    @abstractmethod
    def can_trigger(self, event: GameEvent) -> bool:
        """检查技能是否可以触发"""
        pass
    
    @abstractmethod
    def get_trigger_options(self, event: GameEvent) -> List[Dict[str, Any]]:
        """获取技能触发选项"""
        pass
    
    @abstractmethod
    def execute_skill(self, event: GameEvent, option_data: Dict[str, Any]) -> EventResponse:
        """执行技能"""
        pass
    
    def reset_turn_uses(self):
        """重置回合使用次数"""
        self.uses_this_turn = 0
    
    def reset_game_uses(self):
        """重置游戏使用次数"""
        self.uses_this_game = 0
        self.uses_this_turn = 0

class CharacterSkillManager:
    """角色技能管理器"""
    
    def __init__(self, player_id: str, character_name: str):
        self.player_id = player_id
        self.character_name = character_name
        self.skill_handlers: Dict[str, SkillEventHandler] = {}
        self.skill_bindings: Dict[str, SkillEventBinding] = {}
        self.subscriptions: Dict[str, EventSubscription] = {}
        
        # 技能状态跟踪
        self.skill_cooldowns: Dict[str, int] = {}
        self.disabled_skills: Set[str] = set()
        
        # 初始化角色技能
        self._initialize_character_skills()
    
    def _initialize_character_skills(self):
        """初始化角色技能"""
        # 根据角色名称注册相应的技能
        skill_configs = self._get_character_skill_configs()
        
        for skill_config in skill_configs:
            self.register_skill_handler(skill_config)
    
    def _get_character_skill_configs(self) -> List[Dict[str, Any]]:
        """获取角色技能配置"""
        # 这里定义各个角色的技能配置
        character_skills = {
            "曹操": [
                {
                    "name": "奸雄",
                    "handler_class": "JianXiongHandler",
                    "event_types": ["take_damage"],
                    "trigger_type": SkillTriggerType.TRIGGERED,
                    "timing": SkillTiming.AFTER_EVENT,
                    "priority": EventPriority.NORMAL
                }
            ],
            "刘备": [
                {
                    "name": "仁德",
                    "handler_class": "RenDeHandler", 
                    "event_types": ["phase_change"],
                    "trigger_type": SkillTriggerType.ACTIVE,
                    "timing": SkillTiming.DURING_EVENT,
                    "priority": EventPriority.NORMAL
                }
            ],
            "孙权": [
                {
                    "name": "制衡",
                    "handler_class": "ZhiHengHandler",
                    "event_types": ["phase_change"],
                    "trigger_type": SkillTriggerType.ACTIVE,
                    "timing": SkillTiming.DURING_EVENT,
                    "priority": EventPriority.NORMAL,
                    "max_uses_per_turn": 1
                }
            ],
            "关羽": [
                {
                    "name": "武圣",
                    "handler_class": "WuShengHandler",
                    "event_types": ["play_card"],
                    "trigger_type": SkillTriggerType.PASSIVE,
                    "timing": SkillTiming.REPLACE_EVENT,
                    "priority": EventPriority.HIGH
                }
            ],
            "张飞": [
                {
                    "name": "咆哮",
                    "handler_class": "PaoXiaoHandler",
                    "event_types": ["play_card"],
                    "trigger_type": SkillTriggerType.CONTINUOUS,
                    "timing": SkillTiming.DURING_EVENT,
                    "priority": EventPriority.LOW
                }
            ]
        }
        
        return character_skills.get(self.character_name, [])
    
    def register_skill_handler(self, skill_config: Dict[str, Any]):
        """注册技能处理器"""
        skill_name = skill_config["name"]
        handler_class_name = skill_config["handler_class"]
        
        # 创建技能处理器实例
        handler = self._create_skill_handler(handler_class_name, skill_name)
        if handler:
            self.skill_handlers[skill_name] = handler
            
            # 创建技能绑定
            binding = SkillEventBinding(
                skill_name=skill_name,
                event_types=skill_config["event_types"],
                trigger_type=SkillTriggerType(skill_config["trigger_type"]),
                timing=SkillTiming(skill_config["timing"]),
                priority=skill_config["priority"],
                max_uses_per_turn=skill_config.get("max_uses_per_turn"),
                max_uses_per_game=skill_config.get("max_uses_per_game")
            )
            self.skill_bindings[skill_name] = binding
    
    def _create_skill_handler(self, handler_class_name: str, skill_name: str) -> Optional[SkillEventHandler]:
        """创建技能处理器实例"""
        # 这里应该根据handler_class_name创建相应的处理器实例
        # 为了简化，我们使用一个通用的处理器
        return GenericSkillHandler(skill_name, self.player_id)
    
    def get_applicable_skills(self, event: GameEvent) -> List[str]:
        """获取适用于事件的技能"""
        applicable_skills = []
        
        for skill_name, binding in self.skill_bindings.items():
            # 检查事件类型匹配
            if event.event_type not in binding.event_types:
                continue
            
            # 检查技能是否被禁用
            if skill_name in self.disabled_skills:
                continue
            
            # 检查技能是否在冷却中
            if skill_name in self.skill_cooldowns and self.skill_cooldowns[skill_name] > 0:
                continue
            
            # 检查使用次数限制
            handler = self.skill_handlers[skill_name]
            if binding.max_uses_per_turn and handler.uses_this_turn >= binding.max_uses_per_turn:
                continue
            if binding.max_uses_per_game and handler.uses_this_game >= binding.max_uses_per_game:
                continue
            
            # 检查技能是否可以触发
            if handler.can_trigger(event):
                applicable_skills.append(skill_name)
        
        return applicable_skills
    
    def create_event_subscriptions(self) -> List[EventSubscription]:
        """创建事件订阅"""
        subscriptions = []
        
        for skill_name, binding in self.skill_bindings.items():
            subscription = EventSubscription(
                subscriber_id=f"{self.player_id}_{skill_name}",
                event_types=binding.event_types,
                handler=self._create_skill_event_handler(skill_name),
                priority=binding.priority,
                conditions=binding.conditions
            )
            subscriptions.append(subscription)
            self.subscriptions[skill_name] = subscription
        
        return subscriptions
    
    def _create_skill_event_handler(self, skill_name: str) -> Callable:
        """创建技能事件处理函数"""
        def handle_event(event_data: Dict[str, Any]):
            event = event_data.get('event')
            if event and skill_name in self.skill_handlers:
                handler = self.skill_handlers[skill_name]
                if handler.can_trigger(event):
                    # 这里可以触发技能或记录触发机会
                    print(f"技能 {skill_name} 可以响应事件 {event.event_type}")
        
        return handle_event
    
    def disable_skill(self, skill_name: str):
        """禁用技能"""
        self.disabled_skills.add(skill_name)
    
    def enable_skill(self, skill_name: str):
        """启用技能"""
        self.disabled_skills.discard(skill_name)
    
    def set_skill_cooldown(self, skill_name: str, turns: int):
        """设置技能冷却"""
        self.skill_cooldowns[skill_name] = turns
    
    def reduce_cooldowns(self):
        """减少冷却时间"""
        for skill_name in list(self.skill_cooldowns.keys()):
            self.skill_cooldowns[skill_name] -= 1
            if self.skill_cooldowns[skill_name] <= 0:
                del self.skill_cooldowns[skill_name]
    
    def reset_turn_uses(self):
        """重置回合使用次数"""
        for handler in self.skill_handlers.values():
            handler.reset_turn_uses()

class GenericSkillHandler(SkillEventHandler):
    """通用技能处理器"""
    
    def __init__(self, skill_name: str, player_id: str):
        super().__init__(skill_name, player_id)
        self.skill_effects = self._get_skill_effects()
    
    def _get_skill_effects(self) -> Dict[str, Any]:
        """获取技能效果配置"""
        # 这里定义各个技能的具体效果
        effects = {
            "奸雄": {
                "description": "当你受到伤害后，你可以获得对你造成伤害的牌",
                "trigger_condition": lambda event: event.event_type == "take_damage",
                "effect": self._jianxiong_effect
            },
            "仁德": {
                "description": "出牌阶段，你可以将任意数量的手牌交给其他角色",
                "trigger_condition": lambda event: (event.event_type == "phase_change" and 
                                                  event.data.get("new_phase") == "play"),
                "effect": self._rende_effect
            },
            "制衡": {
                "description": "出牌阶段限一次，你可以弃置任意数量的牌，然后摸等量的牌",
                "trigger_condition": lambda event: (event.event_type == "phase_change" and 
                                                  event.data.get("new_phase") == "play"),
                "effect": self._zhiheng_effect
            },
            "武圣": {
                "description": "你可以将红色牌当【杀】使用或打出",
                "trigger_condition": lambda event: event.event_type == "play_card",
                "effect": self._wusheng_effect
            },
            "咆哮": {
                "description": "锁定技，你使用【杀】无次数限制",
                "trigger_condition": lambda event: (event.event_type == "play_card" and 
                                                  hasattr(event.data.get("card"), "name") and
                                                  event.data.get("card").name == "杀"),
                "effect": self._paoxiao_effect
            }
        }
        
        return effects.get(self.skill_name, {})
    
    def can_trigger(self, event: GameEvent) -> bool:
        """检查技能是否可以触发"""
        if not self.is_active:
            return False
        
        trigger_condition = self.skill_effects.get("trigger_condition")
        if trigger_condition:
            return trigger_condition(event)
        
        return False
    
    def get_trigger_options(self, event: GameEvent) -> List[Dict[str, Any]]:
        """获取技能触发选项"""
        if not self.can_trigger(event):
            return []
        
        # 根据技能类型返回不同的选项
        options = []
        
        if self.skill_name == "奸雄":
            damage_card = event.data.get("damage_card")
            if damage_card:
                options.append({
                    "type": "triggered",
                    "priority": EventPriority.NORMAL.value,
                    "data": {
                        "action_type": "use_skill",
                        "skill_name": self.skill_name,
                        "target_card": damage_card
                    },
                    "conditions_met": True
                })
        
        elif self.skill_name in ["仁德", "制衡"]:
            options.append({
                "type": "optional",
                "priority": EventPriority.NORMAL.value,
                "data": {
                    "action_type": "use_skill",
                    "skill_name": self.skill_name
                },
                "conditions_met": True
            })
        
        elif self.skill_name == "武圣":
            # 检查是否有红色牌可以当杀使用
            options.append({
                "type": "passive",
                "priority": EventPriority.HIGH.value,
                "data": {
                    "action_type": "use_skill",
                    "skill_name": self.skill_name,
                    "replace_card": True
                },
                "conditions_met": True
            })
        
        elif self.skill_name == "咆哮":
            options.append({
                "type": "passive",
                "priority": EventPriority.LOW.value,
                "data": {
                    "action_type": "use_skill",
                    "skill_name": self.skill_name,
                    "remove_limit": True
                },
                "conditions_met": True
            })
        
        return options
    
    def execute_skill(self, event: GameEvent, option_data: Dict[str, Any]) -> EventResponse:
        """执行技能"""
        self.uses_this_turn += 1
        self.uses_this_game += 1
        
        # 执行技能效果
        effect_function = self.skill_effects.get("effect")
        if effect_function:
            effect_result = effect_function(event, option_data)
        else:
            effect_result = {"success": True, "message": f"技能 {self.skill_name} 发动"}
        
        return EventResponse(
            response_id=str(uuid.uuid4()),
            event_id=event.event_id,
            player_id=self.player_id,
            response_type=ResponseType.TRIGGERED,
            priority=EventPriority.NORMAL,
            action_data={
                "skill_name": self.skill_name,
                "effect_result": effect_result,
                **option_data
            },
            conditions_met=True
        )
    
    def _jianxiong_effect(self, event: GameEvent, option_data: Dict[str, Any]) -> Dict[str, Any]:
        """奸雄技能效果"""
        damage_card = option_data.get("target_card")
        if damage_card:
            return {
                "success": True,
                "message": f"奸雄：获得了造成伤害的牌 {getattr(damage_card, 'name', '未知牌')}",
                "gained_card": damage_card
            }
        return {"success": False, "message": "奸雄：没有可获得的牌"}
    
    def _rende_effect(self, event: GameEvent, option_data: Dict[str, Any]) -> Dict[str, Any]:
        """仁德技能效果"""
        return {
            "success": True,
            "message": "仁德：可以将手牌交给其他角色",
            "action_type": "give_cards"
        }
    
    def _zhiheng_effect(self, event: GameEvent, option_data: Dict[str, Any]) -> Dict[str, Any]:
        """制衡技能效果"""
        return {
            "success": True,
            "message": "制衡：弃置任意数量的牌，然后摸等量的牌",
            "action_type": "discard_and_draw"
        }
    
    def _wusheng_effect(self, event: GameEvent, option_data: Dict[str, Any]) -> Dict[str, Any]:
        """武圣技能效果"""
        return {
            "success": True,
            "message": "武圣：将红色牌当【杀】使用",
            "action_type": "card_conversion"
        }
    
    def _paoxiao_effect(self, event: GameEvent, option_data: Dict[str, Any]) -> Dict[str, Any]:
        """咆哮技能效果"""
        return {
            "success": True,
            "message": "咆哮：使用【杀】无次数限制",
            "action_type": "remove_limit"
        }

class SkillResponseHandler(PlayerResponseHandler):
    """技能响应处理器"""
    
    def __init__(self, player_id: str, skill_manager: CharacterSkillManager):
        self.player_id = player_id
        self.skill_manager = skill_manager
    
    def can_respond(self, event: GameEvent) -> bool:
        """检查是否可以响应"""
        applicable_skills = self.skill_manager.get_applicable_skills(event)
        return len(applicable_skills) > 0
    
    def get_response_options(self, event: GameEvent) -> List[Dict[str, Any]]:
        """获取响应选项"""
        options = []
        applicable_skills = self.skill_manager.get_applicable_skills(event)
        
        for skill_name in applicable_skills:
            handler = self.skill_manager.skill_handlers[skill_name]
            skill_options = handler.get_trigger_options(event)
            options.extend(skill_options)
        
        return options
    
    def execute_response(self, event: GameEvent, response_data: Dict[str, Any]) -> EventResponse:
        """执行响应"""
        skill_name = response_data.get("skill_name")
        
        if skill_name and skill_name in self.skill_manager.skill_handlers:
            handler = self.skill_manager.skill_handlers[skill_name]
            return handler.execute_skill(event, response_data)
        
        # 默认响应
        return EventResponse(
            response_id=str(uuid.uuid4()),
            event_id=event.event_id,
            player_id=self.player_id,
            response_type=ResponseType.OPTIONAL,
            priority=EventPriority.NORMAL,
            action_data=response_data,
            conditions_met=False
        )