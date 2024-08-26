import time
import json
import threading
import socket
from player import Player
from env import GameState
from event import EventManager
from control import Control
from agent import Agent
from env import StaticDataLoader
from game_manager import GameManager


class GameClient:
    def __init__(self, host, port, connect_server=True):
        self.host = host
        self.port = port
        self.game_manager = None
        self.socket = None
        self.local_time_offset = 0  # 本地时间偏移量，用于时间同步
        self.connect_server = connect_server  # 是否连接服务器

        if self.connect_server:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    def connect(self):
        if self.connect_server:
            self.socket.connect((self.host, self.port))
            threading.Thread(target=self.receive_events).start()

    def send_event(self, event_type, data):
        """将事件发送到服务器"""
        if self.connect_server:
            event = json.dumps({"type": event_type, "data": data})
            self.socket.sendall(event.encode('utf-8'))
        else:
            # 单机模式下，直接在本地处理事件
            self.handle_event({"type": event_type, "data": data})

    def receive_events(self):
        while True:
            try:
                data = self.socket.recv(1024).decode('utf-8')
                if not data:
                    break
                event = json.loads(data)
                if event["type"] == "time_sync":
                    self.sync_time(event["server_time"])
                else:
                    self.handle_event(event)
            except Exception as e:
                print(f"Error receiving events: {e}")
                break

    def sync_time(self, server_time):
        """根据服务器时间同步本地时间"""
        self.local_time_offset = server_time - \
            (time.time() - self.player.start_time)
        print(f"Time synchronized, local offset: {self.local_time_offset}")

    def handle_event(self, event):
        """处理接收到的事件，根据时间戳排序和延迟补偿"""
        current_time = time.time() - self.player.start_time + self.local_time_offset
        event_time = event.get("timestamp", current_time)

        delay = event_time - current_time
        if delay > 0:
            time.sleep(delay)  # 等待到达预定的时间点处理事件

        self.event_manager.trigger_event(event["type"], event["data"])


if __name__ == "__main__":
    host = "127.0.0.1"
    port = 8000
    single_player_mode = True  # 如果为True则启动单机模式

    # 加载静态数据
    static_data_loader = StaticDataLoader(
        role_file='roles.json',
        skill_file='skills.json',
        card_file='cards.json'
    )

    # 初始化游戏状态
    game_state = GameState()

    # 创建事件管理器
    event_manager = EventManager()

    if single_player_mode:
        # 单机模式下，不连接服务器
        client = GameClient(host, port, connect_server=False)
    else:
        # 联机模式下，连接服务器
        client = GameClient(host, port, connect_server=True)
        client.connect()

    # 创建玩家
    role_1 = static_data_loader.get_role_by_id(1)  # 赵云
    role_2 = static_data_loader.get_role_by_id(2)  # 郭嘉
    human_player = Player(player_id=1, name="Player 1", roles=[
                          role_1], event_manager=event_manager)
    ai_player = Agent(player_id=2, name="AI", roles=[
                      role_2], event_manager=event_manager)

    # 将玩家放入列表中
    players = [human_player, ai_player]

    game_manager = GameManager(
        game_state=game_state, players=players, event_manager=event_manager, static_data=static_data_loader)

    # 将 GameManager 设置到客户端，以便客户端可以更新游戏状态
    client.game_manager = game_manager

    if single_player_mode:
        # 启动用户交互
        control = Control(game_manager)
        control.start()

    # 启动游戏管理器
    game_manager.run()
