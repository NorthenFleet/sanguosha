import threading


class Control:
    def __init__(self, game_manager):
        self.game_manager = game_manager

    def start(self):
        """启动用户交互线程"""
        threading.Thread(target=self.listen_user_input).start()

    def listen_user_input(self):
        """监听用户输入"""
        while True:
            # 这里假设通过控制台输入动作指令
            command = input("请输入动作指令: ")
            if command == "play_card":
                # 示例：用户选择打出一张牌
                card_id = input("请输入卡牌ID: ")
                target_id = input("请输入目标玩家ID: ")
                self.game_manager.player.play_card(card_id, target_id)
            elif command == "quit":
                break
            # 可以扩展更多用户输入处理逻辑
