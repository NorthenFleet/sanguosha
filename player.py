class Player:
    def __init__(self, player_id, name, roles, event_manager):
        self.player_id = player_id
        self.name = name
        self.roles = roles  # 玩家可以拥有多个角色
        self.hand = []  # 手牌
        self.in_game = True  # 玩家是否还在游戏中
        self.event_manager = event_manager

    def play_turn(self, game_state):
        """处理玩家的回合，按照顺序执行各个阶段"""
        self.start_phase()
        self.judgement_phase(game_state)
        self.draw_phase(game_state)
        self.play_phase(game_state)
        self.discard_phase()
        self.end_phase()

    def start_phase(self):
        """开始阶段"""
        print(f"{self.name} 的回合开始")
        self.event_manager.trigger_event("start_phase", {"player": self})

    def judgement_phase(self, game_state):
        """判定阶段"""
        print(f"{self.name} 的判定阶段")
        self.event_manager.trigger_event(
            "judgement_phase", {"player": self, "game_state": game_state})

    def draw_phase(self, game_state):
        """摸牌阶段"""
        print(f"{self.name} 的摸牌阶段")
        for _ in range(2):  # 默认摸两张牌
            card = game_state.draw_card()
            if card:
                self.draw_card(card)

        self.event_manager.trigger_event(
            "draw_phase", {"player": self, "game_state": game_state})

    def play_phase(self, game_state):
        """出牌阶段"""
        print(f"{self.name} 的出牌阶段")
        self.event_manager.trigger_event(
            "play_phase", {"player": self, "game_state": game_state})

        # 简化为玩家手动操作出一张牌
        if self.hand:
            action = self.choose_action(game_state)
            if action["action_type"] == "use_card":
                self.play_card(action["card"], action["target"], game_state)

    def discard_phase(self):
        """弃牌阶段"""
        print(f"{self.name} 的弃牌阶段")
        while len(self.hand) > self.get_health():
            card = self.hand.pop()
            self.discard_card(card)
        self.event_manager.trigger_event("discard_phase", {"player": self})

    def end_phase(self):
        """结束阶段"""
        print(f"{self.name} 的结束阶段")
        self.event_manager.trigger_event("end_phase", {"player": self})

    def draw_card(self, card):
        """从牌堆中抽取一张牌"""
        self.hand.append(card)
        print(f"{self.name} 摸了一张牌: {card.name}")

    def play_card(self, card, target, game_state):
        """使用一张牌对目标玩家进行操作"""
        if card in self.hand:
            self.hand.remove(card)
            print(f"{self.name} 使用了 {card.name} 对 {target.name}")
            self.event_manager.trigger_event(
                "use_card", {"source": self, "target": target, "card": card})
            card.activate(game_state, self, target)

    def discard_card(self, card):
        """弃置一张牌"""
        print(f"{self.name} 弃置了一张牌: {card.name}")
        self.event_manager.trigger_event(
            "discard_card", {"player": self, "card": card})

    def get_health(self):
        """获取当前角色的体力值"""
        # 假设只管理第一个角色的体力值
        return self.roles[0].health if self.roles else 0

    def choose_action(self, game_state):
        """选择动作，可以通过用户交互实现"""
        print("人类玩家出牌")
        action_type = input(f"{self.name}, 请选择动作 (use_card/end_turn): ")
        if action_type == "use_card":
            card = self.hand[0]  # 示例：假设使用第一张牌
            target = game_state.players[1]  # 示例：假设选择第二个玩家为目标
            return {"action_type": "use_card", "card": card, "target": target}
        return {"action_type": "end_turn"}
