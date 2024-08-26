from player import Player


class GameManager:
    def __init__(self, game_state, event_manager, static_data):
        self.game_state = game_state
        self.event_manager = event_manager
        self.static_data = static_data  # 静态数据
        self.players = []  # 用于存储初始化后的玩家列表
        self.current_player_index = 0  # 用于跟踪当前玩家的索引
        self.events = []  # 事件队列

    def initialize_game(self, player_infos):
        """初始化游戏，包括加载静态数据和设置初始状态"""
        for info in player_infos:
            role = self.static_data.get_role_by_id(info['role_id'])
            player = Player(
                player_id=info['player_id'], name=info['name'], roles=[role], event_manager=self.event_manager)
            self.players.append(player)
        self.game_state.shuffle_deck()

    def update_game(self, event):
        """接收到事件后更新游戏"""
        self.game_state.update_state(event)
        event_type = event['type']
        if event_type == "use_card":
            source = event['source']
            target = event['target']
            card = event['card']
            source.play_card(card, target, self.game_state)
        # 这里可以扩展处理更多的事件类型
        self.handle_events()

    def next_turn(self):
        """切换到下一个玩家的回合"""
        current_player = self.players[self.current_player_index]
        current_player.play_turn(self.game_state)
        self.next_player()

    def next_player(self):
        """将当前玩家索引指向下一个玩家"""
        self.current_player_index = (
            self.current_player_index + 1) % len(self.players)

    def run(self):
        """主游戏循环"""
        while not self.game_state.check_game_over():
            current_player = self.players[self.current_player_index]
            print(f"当前是 {current_player.name} 的回合")
            current_player.play_turn(self.game_state)
            self.next_turn()

        print("游戏结束")
        winner = [p for p in self.players if p.in_game]
        if winner:
            print(f"胜利者是: {winner[0].name}")
        else:
            print("所有玩家都已出局，无人获胜")

    def create_event(self, event_type, source, target):
        """创建事件并添加到事件队列"""
        self.events.append(
            {"type": event_type, "source": source, "target": target})

    def process_turn(self, player):
        print(f"{player.name} 的出牌阶段开始")
        # 示例：玩家选择一个目标发起决斗
        target = self.get_target_player()
        if target.is_alive():
            player.play_card('决斗', target=target, game_state=self.game_state)
        self.handle_events()
        print(f"{player.name} 的回合结束")

    def handle_events(self):
        """处理事件队列中的所有事件"""
        while self.events:
            event = self.events.pop(0)
            event_type = event["type"]
            source = event["source"]
            target = event["target"]

            if event_type == "duel":
                target.respond_to_duel(self, source)
            elif event_type == "slash":
                target.respond_to_slash(self, source)
            elif event_type == "peach":
                target.respond_to_peach(self, source)
            # 可以扩展更多事件的处理逻辑

    def get_target_player(self):
        """根据当前玩家选择目标（示例，通常应根据游戏逻辑）"""
        target_index = (self.current_player_index + 1) % len(self.players)
        return self.players[target_index]

    def handle_player_action(self, player, action):
        """处理玩家的动作"""
        # 根据具体的action逻辑处理
        pass

    def end_game(self):
        """结束游戏并处理胜利条件"""
        if self.game_state.check_game_over():
            print("Game Over!")
            winner = [p for p in self.players if p.in_game]
            if winner:
                print(f"胜利者是: {winner[0].name}")
            else:
                print("所有玩家都已出局，无人获胜")
