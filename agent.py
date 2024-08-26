from player import Player


class Agent(Player):
    def choose_action(self, game_state):
        """AI根据当前游戏状态选择动作"""
        # 简单AI逻辑：如果有牌就打出第一张
        print("AI玩家出牌")
        if self.hand:
            card = self.hand[0]
            target = game_state.players[1]  # 简单选择一个目标玩家
            return {"action_type": "use_card", "card": card, "target": target}
        return {"action_type": "end_turn"}

    def play_turn(self, game_state):
        action = self.choose_action(game_state)
        if action["action_type"] == "use_card":
            self.play_card(action["card"], action["target"])
        else:
            self.end_turn()
