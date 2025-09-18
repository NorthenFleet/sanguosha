"""
三国杀1v1玩家模块
"""
from typing import List
from .character import Character
from .card import Card

class Player:
    """玩家类"""
    def __init__(self, character: Character):
        self.character = character
        self.hp = character.hp
        self.hand_cards: List[Card] = []
        self.weapon = None  # 武器牌
        self.defense = None  # 防御牌
        self.attack_horse = None  # 进攻马
        self.defense_horse = None  # 防御马
        self.equipped = []  # 初始化 equipped 属性为空列表
        self.judgment_area = []  # 判定区
        self.chained = False
        self.has_used_sha = False  # 跟踪本回合是否使用过杀

    def draw_card(self, deck: List[Card], count: int):
        """从牌堆摸牌"""
        for _ in range(count):
            if deck:
                self.hand_cards.append(deck.pop())

    def discard_card(self, card: str):
        """弃牌"""
        if card in self.hand_cards:
            self.hand_cards.remove(card)

    def get_attack_range(self):
        """获取攻击范围"""
        base_range = 1  # 基础攻击范围
        
        # 武器装备影响攻击范围
        if self.weapon:
            if self.weapon.name == "青龙偃月刀":
                base_range = 3
            elif self.weapon.name == "丈八蛇矛":
                base_range = 3
            elif self.weapon.name == "方天画戟":
                base_range = 4
            elif self.weapon.name == "麒麟弓":
                base_range = 5
        
        return base_range
    
    def get_distance_to(self, target_player):
        """计算到目标玩家的距离"""
        # 在1v1模式中，基础距离为1
        base_distance = 1
        
        # 进攻马减少距离
        if self.attack_horse:
            base_distance -= 1
        
        # 目标的防御马增加距离
        if target_player.defense_horse:
            base_distance += 1
        
        return max(1, base_distance)  # 距离最小为1
    
    def can_attack(self, target_player):
        """判断是否可以攻击目标玩家"""
        attack_range = self.get_attack_range()
        distance = self.get_distance_to(target_player)
        return distance <= attack_range
    
    def has_weapon_effect(self, weapon_name):
        """检查是否装备了指定武器"""
        return self.weapon and self.weapon.name == weapon_name
    
    def has_defense_equipment(self, equipment_name):
        """检查是否装备了指定防御装备"""
        return self.defense and self.defense.name == equipment_name
    
    def perform_judgment(self, judgment_type="八卦阵"):
        """执行判定"""
        import random
        
        # 模拟判定牌（简化版本，实际应该从牌堆顶翻牌）
        suits = ["红桃", "方片", "梅花", "黑桃"]
        numbers = list(range(1, 14))  # A到K
        
        suit = random.choice(suits)
        number = random.choice(numbers)
        
        print(f"判定牌：{suit}{number}")
        
        if judgment_type == "八卦阵":
            # 八卦阵：红色判定成功
            success = suit in ["红桃", "方片"]
            if success:
                print(f"判定成功！{suit}为红色，视为使用了一张闪。")
            else:
                print(f"判定失败！{suit}为黑色。")
            return success
        
        return False
    
    def can_dodge_with_bagua(self):
        """八卦阵判定是否可以闪避"""
        if self.has_defense_equipment("八卦阵"):
            print(f"{self.character.name} 装备了八卦阵，进行判定...")
            return self.perform_judgment("八卦阵")
        return False

    def use_card(self, card):
        """使用牌"""
        original_card_str = None
        target_card = None
        
        if isinstance(card, str):
            original_card_str = card
            # 将字符串解析为 Card 对象
            target_card = next((c for c in self.hand_cards if str(c) == card), None)
            if not target_card:
                print(f"错误: 未找到匹配的卡牌 {original_card_str}")
                return False
        else:
            target_card = card

        print(f"[DEBUG] 当前手牌: {self.hand_cards}")
        print(f"[DEBUG] 使用的卡牌: {target_card}")
        
        # 直接从手牌中移除找到的卡牌
        if target_card in self.hand_cards:
            self.hand_cards.remove(target_card)
            print(f"[DEBUG] 卡牌 {target_card} 已从手牌移除")
            
            # 处理装备牌逻辑
            if hasattr(target_card, 'type') and target_card.type:
                # 检查不同的装备牌类型表示方式
                is_equipment = False
                if hasattr(target_card.type, 'value') and target_card.type.value == "装备牌":
                    is_equipment = True
                elif str(target_card.type) == "CardType.EQUIP":
                    is_equipment = True
                elif hasattr(target_card.type, 'name') and target_card.type.name == "EQUIP":
                    is_equipment = True
                
                if is_equipment:
                    print(f"[DEBUG] 检测到装备牌: {target_card.name}")
                    self._equip_card(target_card)
                else:
                    # 处理基本牌效果
                    self._handle_basic_card_effect(target_card)
            elif hasattr(target_card, 'category') and target_card.category == "equipment":
                print(f"[DEBUG] 检测到装备牌(category): {target_card.name}")
                self._equip_card(target_card)
            else:
                # 处理其他牌的效果
                self._handle_basic_card_effect(target_card)
            return True
        else:
            print(f"[ERROR] 卡牌 {target_card} 不在手牌中")
            return False
    
    def _handle_basic_card_effect(self, card):
        """处理基本牌效果"""
        print(f"[DEBUG] 处理基本牌效果: {card.name}")
        
        if card.name == "桃":
            # 桃的效果：回复1点体力
            if self.hp < self.character.max_hp:
                self.hp += 1
                print(f"[DEBUG] 使用桃回复体力，当前血量: {self.hp}")
            else:
                print(f"[DEBUG] 体力已满，桃无效果")
        elif card.name == "杀":
            print(f"[DEBUG] 使用杀，需要指定目标")
        elif card.name == "闪":
            print(f"[DEBUG] 使用闪，抵消杀的效果")
        else:
            # 检查是否为锦囊牌
            if hasattr(card, 'type') and str(card.type) == "CardType.TRICK":
                self._handle_trick_card_effect(card)
            else:
                print(f"[DEBUG] 未知基本牌效果: {card.name}")

    def _handle_trick_card_effect(self, card):
        """处理锦囊牌效果"""
        print(f"[DEBUG] 处理锦囊牌效果: {card.name}")
        
        if card.name == "无中生有":
            # 无中生有：摸两张牌
            print(f"[DEBUG] 无中生有效果：摸两张牌")
            # 这里需要牌堆才能摸牌，暂时模拟
            print(f"[DEBUG] 模拟摸两张牌")
        elif card.name == "五谷丰登":
            print(f"[DEBUG] 五谷丰登效果：所有玩家各摸一张牌")
        elif card.name == "南蛮入侵":
            print(f"[DEBUG] 南蛮入侵效果：所有其他玩家需要出杀或受到伤害")
        elif card.name == "万箭齐发":
            print(f"[DEBUG] 万箭齐发效果：所有其他玩家需要出闪或受到伤害")
        elif card.name == "顺手牵羊":
            print(f"[DEBUG] 顺手牵羊效果：获得目标玩家一张牌")
        elif card.name == "决斗":
            print(f"[DEBUG] 决斗效果：与目标玩家轮流出杀")
        else:
            print(f"[DEBUG] 未知锦囊牌效果: {card.name}")

    def _equip_card(self, card):
        """装备卡牌"""
        print(f"[DEBUG] 开始装备卡牌: {card.name}")
        
        if card.name in ["青龙偃月刀", "丈八蛇矛", "方天画戟", "麒麟弓"]:
            # 替换武器
            if self.weapon:
                self.equipped.remove(self.weapon)
            self.weapon = card
            print(f"[DEBUG] 装备武器: {card.name}")
        elif card.name in ["八卦阵", "仁王盾"]:
            # 替换防御装备
            if self.defense:
                self.equipped.remove(self.defense)
            self.defense = card
            print(f"[DEBUG] 装备防御: {card.name}")
        elif card.name in ["赤兔", "的卢", "爪黄飞电"]:
            # 替换进攻马
            if self.attack_horse:
                self.equipped.remove(self.attack_horse)
            self.attack_horse = card
            print(f"[DEBUG] 装备进攻马: {card.name}")
        elif card.name in ["绝影", "紫骍"]:
            # 替换防御马
            if self.defense_horse:
                self.equipped.remove(self.defense_horse)
            self.defense_horse = card
            print(f"[DEBUG] 装备防御马: {card.name}")
        else:
            print(f"[DEBUG] 未知装备类型: {card.name}")
        
        # 添加到装备列表
        self.equipped.append(card)
        print(f"[DEBUG] 装备列表更新: {[eq.name for eq in self.equipped]}")
    
    def get_all_cards(self):
        """获取玩家所有区域的牌（手牌、装备区、判定区）"""
        all_cards = {
            'hand': self.hand_cards.copy(),
            'equipment': self.equipped.copy(),
            'judgment': self.judgment_area.copy()
        }
        return all_cards
    
    def remove_card_from_area(self, card, area):
        """从指定区域移除牌"""
        if area == 'hand' and card in self.hand_cards:
            self.hand_cards.remove(card)
            return True
        elif area == 'equipment' and card in self.equipped:
            self.equipped.remove(card)
            # 同时清除对应的装备引用
            if card == self.weapon:
                self.weapon = None
            elif card == self.defense:
                self.defense = None
            elif card == self.attack_horse:
                self.attack_horse = None
            elif card == self.defense_horse:
                self.defense_horse = None
            return True
        elif area == 'judgment' and card in self.judgment_area:
            self.judgment_area.remove(card)
            return True
        return False