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

class ReactionWindow:
    def __init__(self, event_manager, players):
        self.event_manager = event_manager
        self.players = players
        self.intent_queue = []  # 决策队列

    def open_window(self, event_type, **kwargs):
        """开启反应窗口"""
        print(f"开启反应窗口: {event_type}")
        for player in self.players:
            intent = player.react(event_type, **kwargs)  # 玩家响应
            if intent:
                self.intent_queue.append(intent)
        return self.intent_queue

class Effect:
    def __init__(self, name, countered=False, replaced=False):
        self.name = name
        self.countered = countered
        self.replaced = replaced

class EffectStack:
    def __init__(self):
        self.stack = []

    def push_effect(self, effect):
        """将效果推入栈"""
        self.stack.append(effect)

    def resolve_effects(self):
        """从栈顶开始结算效果"""
        while self.stack:
            effect = self.stack.pop()
            if effect.countered:
                print(f"效果 {effect.name} 被抵消")
            elif effect.replaced:
                print(f"效果 {effect.name} 被替换")
            else:
                print(f"结算效果: {effect.name}")