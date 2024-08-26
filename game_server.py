import socket
import threading
import time
import json


class GameServer:
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.clients = []
        self.server_start_time = time.time()  # 用于同步的参考时间

    def start_server(self):
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.bind((self.host, self.port))
        server_socket.listen()
        print(f"Server started on {self.host}:{self.port}")
        while True:
            client_socket, addr = server_socket.accept()
            print(f"Client {addr} connected")
            self.clients.append(client_socket)
            threading.Thread(target=self.handle_client,
                             args=(client_socket,)).start()

    def handle_client(self, client_socket):
        while True:
            try:
                data = client_socket.recv(1024).decode('utf-8')
                if not data:
                    break
                event = json.loads(data)
                self.broadcast_event(event)
            except Exception as e:
                print(f"Error handling client: {e}")
                break

        client_socket.close()
        self.clients.remove(client_socket)
        print("Client disconnected")

    def broadcast_event(self, event):
        """将事件广播给所有客户端"""
        message = json.dumps(event)
        for client_socket in self.clients:
            client_socket.sendall(message.encode('utf-8'))

    def send_time_sync(self):
        """定期发送时间同步信号"""
        current_time = time.time() - self.server_start_time
        sync_message = json.dumps(
            {"type": "time_sync", "server_time": current_time})
        for client_socket in self.clients:
            client_socket.sendall(sync_message.encode('utf-8'))

    def run(self):
        """运行服务器主循环"""
        threading.Thread(target=self.sync_time_loop).start()

    def sync_time_loop(self):
        """定期发送时间同步消息"""
        while True:
            self.send_time_sync()
            time.sleep(1)  # 每秒同步一次时间
