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
        self.hp = character.max_hp  # 使用max_hp而不是hp，确保初始血量正确
        self.hand_cards: List[Card] = []
        self.weapon = None  # 武器牌
        self.defense = None  # 防御牌
        self.attack_horse = None  # 进攻马
        self.defense_horse = None  # 防御马
        self.equipped = []  # 初始化 equipped 属性为空列表
        self.judgment_area = []  # 判定区
        self.chained = False
        self.has_used_sha = False  # 跟踪本回合是否使用过杀
        self.position = 0  # 玩家座位位置（用于多人游戏距离计算）

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
            weapon_ranges = {
                "青龙偃月刀": 3,
                "丈八蛇矛": 3,
                "方天画戟": 4,
                "麒麟弓": 5,
                "古锭刀": 2,
                "朱雀羽扇": 4,
                "雌雄双股剑": 2
            }
            base_range = weapon_ranges.get(self.weapon.name, 1)
        
        return base_range
    
    def get_weapon_effects(self):
        """获取武器的特殊效果"""
        if not self.weapon:
            return {}
        
        weapon_effects = {
            "青龙偃月刀": {
                "type": "attack_enhancement",
                "description": "当你使用的杀被闪抵消时，你可以立即对同一目标再使用一张杀",
                "trigger": "sha_dodged",
                "effect": "extra_sha"
            },
            "丈八蛇矛": {
                "type": "card_substitute",
                "description": "你可以将两张手牌当杀使用或打出",
                "trigger": "need_sha",
                "effect": "two_cards_as_sha"
            },
            "方天画戟": {
                "type": "multi_target",
                "description": "当你使用的杀是你最后的手牌时，你可以额外指定至多两个目标",
                "trigger": "last_card_sha",
                "effect": "multi_target_sha"
            },
            "麒麟弓": {
                "type": "equipment_destroy",
                "description": "当你使用杀对目标造成伤害时，你可以弃置其装备区里的一张牌",
                "trigger": "sha_damage",
                "effect": "destroy_equipment"
            },
            "古锭刀": {
                "type": "damage_enhancement",
                "description": "当你使用的杀对目标造成伤害时，若其没有手牌，此伤害+1",
                "trigger": "sha_damage",
                "effect": "extra_damage_no_hand"
            },
            "朱雀羽扇": {
                "type": "fire_damage",
                "description": "你可以将一张普通杀当火杀使用",
                "trigger": "use_sha",
                "effect": "fire_sha"
            },
            "雌雄双股剑": {
                "type": "gender_effect",
                "description": "当你使用杀指定异性角色为目标时，你可以令其选择：弃置一张手牌，或令你摸一张牌",
                "trigger": "sha_target_different_gender",
                "effect": "discard_or_draw"
            }
        }
        
        return weapon_effects.get(self.weapon.name, {})
    
    def get_distance_to(self, target_player, all_players=None):
        """计算到目标玩家的距离"""
        if all_players is None or len(all_players) <= 2:
            # 在1v1模式中，基础距离为1
            base_distance = 1
        else:
            # 多人游戏中，计算座位距离
            base_distance = self._calculate_seat_distance(target_player, all_players)
        
        # 进攻马减少距离
        if self.attack_horse:
            base_distance -= 1
        
        # 目标的防御马增加距离
        if target_player.defense_horse:
            base_distance += 1
        
        return max(1, base_distance)  # 距离最小为1
    
    def _calculate_seat_distance(self, target_player, all_players):
        """计算座位距离（多人游戏）"""
        if not all_players or len(all_players) <= 2:
            return 1
        
        # 获取玩家在座位中的位置
        try:
            my_index = all_players.index(self)
            target_index = all_players.index(target_player)
        except ValueError:
            # 如果找不到玩家，返回默认距离
            return 1
        
        total_players = len(all_players)
        
        # 计算顺时针和逆时针的距离
        clockwise_distance = (target_index - my_index) % total_players
        counter_clockwise_distance = (my_index - target_index) % total_players
        
        # 返回较小的距离
        return min(clockwise_distance, counter_clockwise_distance)
    
    def can_attack(self, target_player, all_players=None):
        """判断是否可以攻击目标玩家"""
        attack_range = self.get_attack_range()
        distance = self.get_distance_to(target_player, all_players)
        return distance <= attack_range
    
    def can_use_card_on_target(self, target_player, card_name, all_players=None):
        """判断是否可以对目标使用指定牌或技能"""
        # 获取攻击范围和实际距离
        attack_range = self.get_attack_range()
        actual_distance = self.get_distance_to(target_player, all_players)
        
        # 判定结果
        can_use = actual_distance <= attack_range
        
        if not can_use:
            print(f"距离判定失败：实际距离 {actual_distance} 大于攻击范围 {attack_range}，无法对 {target_player.character.name} 使用 {card_name}")
        else:
            print(f"距离判定成功：实际距离 {actual_distance} 在攻击范围 {attack_range} 内，可以对 {target_player.character.name} 使用 {card_name}")
        
        return can_use
    
    def has_weapon_effect(self, weapon_name):
        """检查是否装备了指定武器"""
        return self.weapon and self.weapon.name == weapon_name
    
    def has_defense_equipment(self, equipment_name):
        """检查是否装备了指定防御装备"""
        return self.defense and self.defense.name == equipment_name
    
    def get_defense_equipment_effects(self):
        """获取防御装备的特殊效果"""
        if not self.defense:
            return {}
        
        defense_effects = {
            "八卦阵": {
                "type": "dodge_enhancement",
                "skill_type": "non_locked",  # 非锁定技
                "description": "当你需要使用或打出闪时，你可以进行判定：若结果为红色，则视为你使用或打出了一张闪",
                "trigger": "need_shan",
                "effect": "judgment_shan",
                "judgment_condition": "red",
                "can_choose": True  # 可以选择是否发动
            },
            "仁王盾": {
                "type": "damage_prevention",
                "skill_type": "locked",  # 锁定技
                "description": "黑色的杀对你无效",
                "trigger": "receive_sha",
                "effect": "prevent_black_sha",
                "can_choose": False  # 自动触发，不可选择
            },
            "白银狮子": {
                "type": "damage_reduction",
                "skill_type": "non_locked",  # 非锁定技
                "description": "当你受到伤害时，若此伤害大于1点，你可以防止多余的伤害",
                "trigger": "receive_damage",
                "effect": "reduce_damage_to_1",
                "can_choose": True  # 可以选择是否发动
            },
            "藤甲": {
                "type": "damage_prevention_fire_weakness",
                "skill_type": "locked",  # 锁定技
                "description": "南蛮入侵、万箭齐发和普通杀对你无效。你受到火焰伤害时，此伤害+1",
                "trigger": "receive_damage",
                "effect": "prevent_normal_damage_fire_weakness",
                "can_choose": False  # 自动触发，不可选择
            }
        }
        
        return defense_effects.get(self.defense.name, {})
    
    def calculate_damage_reduction(self, damage_amount, damage_source=None):
        """计算防御装备的伤害减免"""
        if not self.defense:
            return damage_amount
        
        defense_effect = self.get_defense_equipment_effects()
        
        if defense_effect.get("type") == "damage_reduction":
            # 白银狮子：伤害大于1时减少到1
            if damage_amount > 1:
                print(f"[防御装备] {self.character.name}的{self.defense.name}发动，伤害从{damage_amount}减少到1")
                return 1
        elif defense_effect.get("type") == "damage_prevention_fire_weakness":
            # 藤甲：火焰伤害+1，其他特定伤害无效
            if damage_source and hasattr(damage_source, 'damage_type'):
                if damage_source.damage_type == "fire":
                    print(f"[防御装备] {self.character.name}的{self.defense.name}：火焰伤害+1")
                    return damage_amount + 1
                elif damage_source.name in ["南蛮入侵", "万箭齐发"] or (damage_source.name == "杀" and not hasattr(damage_source, 'damage_type')):
                    print(f"[防御装备] {self.character.name}的{self.defense.name}：{damage_source.name}无效")
                    return 0
        
        return damage_amount
    
    def can_prevent_damage(self, damage_source):
        """判断是否可以防止伤害"""
        if not self.defense:
            return False
        
        defense_effect = self.get_defense_equipment_effects()
        
        if defense_effect.get("type") == "damage_prevention":
            # 仁王盾：黑色杀无效（锁定技，自动触发）
            if damage_source.name == "杀" and hasattr(damage_source, 'suit'):
                if damage_source.suit in ["黑桃", "梅花"]:
                    print(f"[防御装备] {self.character.name}的{self.defense.name}发动：黑色杀无效")
                    return True
        
        return False
    
    def can_trigger_defense_equipment(self, trigger_type, context=None):
        """检查防御装备是否可以触发"""
        if not self.defense:
            return False
        
        defense_effect = self.get_defense_equipment_effects()
        
        # 检查触发条件
        if defense_effect.get("trigger") != trigger_type:
            return False
        
        # 特殊检查：仁王盾需要检查杀的颜色
        if (defense_effect.get("effect") == "prevent_black_sha" and 
            trigger_type == "receive_sha" and context and "card" in context):
            card = context["card"]
            if hasattr(card, 'suit') and card.suit in ["黑桃", "梅花"]:
                return True
            else:
                return False
        
        # 锁定技自动触发
        if defense_effect.get("skill_type") == "locked":
            return True
        
        # 非锁定技需要玩家选择
        if defense_effect.get("skill_type") == "non_locked" and defense_effect.get("can_choose"):
            return True
        
        return False
    
    def ask_defense_equipment_choice(self, trigger_type, context=None):
        """询问玩家是否发动防御装备（仅对非锁定技）"""
        if not self.defense:
            return False
        
        defense_effect = self.get_defense_equipment_effects()
        
        # 只有非锁定技才需要询问
        if defense_effect.get("skill_type") != "non_locked" or not defense_effect.get("can_choose"):
            return False
        
        # 检查触发条件
        if defense_effect.get("trigger") != trigger_type:
            return False
        
        print(f"[防御装备选择] {self.character.name}装备了{self.defense.name}")
        print(f"效果：{defense_effect.get('description')}")
        
        # 在实际游戏中，这里应该通过UI让玩家选择
        # 这里简化为自动选择（可以根据需要修改）
        choice = input(f"是否发动{self.defense.name}？(y/n): ").lower().strip()
        return choice in ['y', 'yes', '是']
    
    def perform_judgment(self, judgment_type="八卦阵", judgment_system=None):
        """执行判定"""
        if judgment_system:
            # 使用新的判定系统
            from ..core.judgment_system import JudgmentType
            
            judgment_type_map = {
                "八卦阵": JudgmentType.BAGUA_ZHEN,
                "闪电": JudgmentType.LIGHTNING,
                "乐不思蜀": JudgmentType.LEBUSISHU,
                "兵粮寸断": JudgmentType.BINGLIANG
            }
            
            judgment_enum = judgment_type_map.get(judgment_type, JudgmentType.BAGUA_ZHEN)
            result = judgment_system.perform_judgment(judgment_enum, self.character.name)
            
            return result.success if result else False
        else:
            # 兼容旧的简化判定逻辑
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
    
    def can_dodge_with_bagua(self, judgment_system=None):
        """八卦阵判定是否可以闪避"""
        if self.has_defense_equipment("八卦阵"):
            print(f"{self.character.name} 装备了八卦阵，可以进行判定来响应杀...")
            return self.perform_judgment("八卦阵", judgment_system)
        return False
    
    def ask_bagua_response(self):
        """询问是否使用八卦阵响应杀"""
        if self.has_defense_equipment("八卦阵"):
            choice = input(f"{self.character.name} 装备了八卦阵，是否进行判定来响应杀？(y/n): ").lower().strip()
            return choice in ['y', 'yes', '是']
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
        
        if card.name in ["青龙偃月刀", "丈八蛇矛", "方天画戟", "麒麟弓", "古锭刀", "朱雀羽扇", "雌雄双股剑"]:
            # 替换武器
            if self.weapon:
                self.equipped.remove(self.weapon)
            self.weapon = card
            print(f"[DEBUG] 装备武器: {card.name}")
        elif card.name in ["八卦阵", "仁王盾", "白银狮子", "藤甲"]:
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