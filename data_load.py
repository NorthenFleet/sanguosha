import json


class StaticDataLoader:
    def __init__(self, card_file, role_file, skill_file):
        self.cards = self.reformat_cards_data(self.load_json(card_file), "B")
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

    # 卡牌整理函数
    def reformat_cards_data(self, card_data, card_type):
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
