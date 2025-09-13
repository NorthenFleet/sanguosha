"""
事件系统模块
"""
from enum import Enum

class EventType(Enum):
    PLAY_CARD = "play_card"
    USE_SKILL = "use_skill"
    TAKE_DAMAGE = "take_damage"

class EventManager:
    def __init__(self):
        self.listeners = {}

    def register_listener(self, event_type, listener):
        """注册事件监听器"""
        if event_type not in self.listeners:
            self.listeners[event_type] = []
        self.listeners[event_type].append(listener)

    def trigger_event(self, event_type, **kwargs):
        """触发事件"""
        if event_type in self.listeners:
            for listener in self.listeners[event_type]:
                listener(**kwargs)