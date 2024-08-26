class Event:
    def __init__(self, event_type, source, target=None, payload=None):
        self.event_type = event_type  # 事件类型，如 "use_card", "attack", "defend"
        self.source = source          # 触发事件的角色或对象
        self.target = target          # 事件的目标角色或对象
        self.payload = payload        # 事件的附加信息，如卡牌、技能等


class EventQueue:
    def __init__(self):
        self.queue = []

    def add_event(self, event):
        """将事件加入队列"""
        self.queue.append(event)

    def get_next_event(self):
        """从队列中取出下一个事件"""
        if self.queue:
            return self.queue.pop(0)
        return None

    def has_events(self):
        """检查队列中是否还有事件"""
        return len(self.queue) > 0

    def clear(self):
        """清空事件队列（可选，用于调试或游戏重置）"""
        self.queue.clear()


class EventManager:
    def __init__(self):
        self.listeners = {}

    def register_listener(self, event_type, listener):
        self.listeners.setdefault(event_type, []).append(listener)

    def trigger_event(self, event_type, data):
        for listener in self.listeners.get(event_type, []):
            listener(data)


class EventHandler:
    def __init__(self, game_manager):
        self.game_manager = game_manager

    def handle_event(self, event):
        """根据事件类型处理事件"""
        if event.event_type == "use_card":
            self.handle_use_card_event(event)
        elif event.event_type == "attack":
            self.handle_attack_event(event)
        # 处理其他事件类型
        # ...

    def handle_use_card_event(self, event):
        """处理使用卡牌的事件"""
        card = event.payload['card']
        print(f"{event.source} 使用了 {card['name']} 指向 {event.target}")

        # 可能生成新的事件，如"attack"事件
        if card['name'] == '杀':
            new_event = Event("attack", event.source,
                              event.target, {"damage": 1})
            self.game_manager.event_queue.add_event(new_event)

    def handle_attack_event(self, event):
        """处理攻击事件"""
        damage = event.payload['damage']
        print(f"{event.source} 攻击了 {event.target}，造成了 {damage} 点伤害")
        # 响应顺序，可以根据游戏逻辑产生防御事件等
        # self.game_manager.check_defense(event.target)
