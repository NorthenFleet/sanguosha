import websockets
import asyncio
import json
import random


class Card:
    def __init__(self, card_id, name, card_type, effect):
        self.card_id = card_id  # 卡牌的唯一标识符
        self.name = name        # 卡牌的名称
        self.type = card_type   # 卡牌的类型（如进攻、防御、策略等）
        self.effect = effect    # 卡牌的效果，可以是函数或描述

    def apply_effect(self, target):
        """应用卡牌效果，对目标产生影响"""
        # 假设效果是一个函数，传递目标参数执行
        if callable(self.effect):
            self.effect(target)





class GameState:
    def __init__(self):
        self.deck = {}           # 牌堆
        self.discard_pile = {}   # 弃牌堆
        self.players = []        # 所有参与游戏的玩家
        self.current_turn = None  # 当前回合的玩家
        self.load_and_reformat_data("cards.json", "roles.json", "skills.json")
        self.shuffle_deck()

    def load_and_reformat_data(self, card_file, role_file, skill_file):
        """加载并重新格式化卡牌、角色和技能数据"""
        self.cards = self.reformat_cards_data(self.load_json(card_file), "B")
        self.roles = self.load_json(role_file)
        self.skills = self.load_json(skill_file)
        # 初始化牌堆
        self.deck = self.cards.copy()

    def load_json(self, filepath):
        """从JSON文件加载静态数据"""
        with open(filepath, 'r') as file:
            return json.load(file)

    def reformat_cards_data(self, card_data, card_type):
        """将卡牌数据重新编排为ID索引的形式"""
        suits = {"黑桃": "S", "红桃": "H", "梅花": "C", "方块": "D"}
        ranks = {
            "A": "01", "2": "02", "3": "03", "4": "04", "5": "05", "6": "06", "7": "07", "8": "08", "9": "09", "10": "10",
            "J": "11", "Q": "12", "K": "13", "(EX)2": "EX2", "(EX)Q": "EXQ",
            "5(绝影)": "05Z", "K(爪黄飞电)": "13Z", "5(的卢)": "05D", "K(骅疆)": "13H", "K(大宛)": "13D", "5(赤兔)": "05C", "K(紫驿)": "13Y"
        }

        reformatted_data = {}
        for card_name, card_info in card_data.items():
            for suit, rank_list in card_info.items():
                if suit in suits:
                    for rank in rank_list:
                        card_id = f"{suits[suit]}{card_type}{ranks[rank]}"
                        reformatted_data[card_id] = {
                            "name": card_name,
                            "suit": suit,
                            "rank": rank,
                            "type": card_type
                        }
        return reformatted_data

    def update_state(self, event):
        """根据事件更新游戏状态"""
        # 根据事件类型和数据更新游戏状态
        pass

    def shuffle_deck(self):
        """洗牌"""
        deck_items = list(self.deck.items())
        random.shuffle(deck_items)
        self.deck = dict(deck_items)

    def draw_card(self):
        """从牌堆中抽取一张牌"""
        if self.deck:
            return self.deck.popitem()
        return None

    def discard_card(self, card):
        """将一张牌放入弃牌堆"""
        self.discard_pile[card.card_id] = card

    def next_turn(self):
        """进入下一个玩家的回合"""
        if self.players:
            self.current_turn = self.players.pop(0)
            self.players.append(self.current_turn)

    def check_game_over(self):
        """检查游戏是否结束"""
        active_players = [p for p in self.players if p.in_game]
        return len(active_players) <= 1





class StaticDataLoader:
    def __init__(self, card_file, role_file, skill_file):
        self.cards = self.load_json(card_file)
        self.roles = self.load_json(role_file)
        self.skills = self.load_json(skill_file)

    def load_json(self, filepath):
        """从JSON文件加载静态数据"""
        with open(filepath, 'r') as file:
            return json.load(file)

    def get_card_by_id(self, card_id):
        return self.cards.get(card_id)

    def get_role_by_id(self, role_id):
        return self.roles.get(role_id)

    def get_skill_by_id(self, skill_id):
        return self.skills.get(skill_id)


class WebSocketHandler:
    def __init__(self):
        self.connections = set()

    async def handler(self, websocket, path):
        """处理新连接"""
        self.connections.add(websocket)
        try:
            async for message in websocket:
                await self.receive_action_from_client(message)
        finally:
            self.connections.remove(websocket)

    async def send_update_to_clients(self, update):
        """将游戏状态更新发送给所有客户端"""
        if self.connections:
            await asyncio.wait([ws.send(update) for ws in self.connections])

    async def receive_action_from_client(self, action):
        """接收来自客户端的玩家动作"""
        # 处理玩家动作并返回更新
        pass

    def start_server(self, host='localhost', port=8765):
        start_server = websockets.serve(self.handler, host, port)
        asyncio.get_event_loop().run_until_complete(start_server)
        asyncio.get_event_loop().run_forever()
