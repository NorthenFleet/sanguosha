#!/usr/bin/env python3
"""
基于基础元素的裁决系统

将三国杀的所有判定归结为对基础元素的操作和检查：
- 卡牌（手牌、牌堆、弃牌堆）
- 血量（当前血量、最大血量）
- 势力（魏、蜀、吴、群）
- 装备（武器、防具、坐骑）
- 距离（座位距离、攻击范围）

技能被视为基础元素的组合运用，而非独立的判定要素。
"""

from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class ElementType(Enum):
    """基础元素类型"""
    CARD = "card"           # 卡牌
    HEALTH = "health"       # 血量
    FACTION = "faction"     # 势力
    EQUIPMENT = "equipment" # 装备
    DISTANCE = "distance"   # 距离


@dataclass
class ElementState:
    """基础元素状态"""
    element_type: ElementType
    current_value: Any
    max_value: Optional[Any] = None
    modifiers: List[Dict[str, Any]] = None
    
    def __post_init__(self):
        if self.modifiers is None:
            self.modifiers = []


class BaseElement:
    """基础元素基类"""
    
    def __init__(self, element_type: ElementType):
        self.element_type = element_type
        self.state = ElementState(element_type, None)
    
    def get_current_value(self) -> Any:
        """获取当前值"""
        return self.state.current_value
    
    def apply_modifier(self, modifier: Dict[str, Any]) -> None:
        """应用修正"""
        self.state.modifiers.append(modifier)
    
    def calculate_final_value(self) -> Any:
        """计算最终值（应用所有修正后）"""
        value = self.state.current_value
        for modifier in self.state.modifiers:
            value = self._apply_single_modifier(value, modifier)
        return value
    
    def _apply_single_modifier(self, value: Any, modifier: Dict[str, Any]) -> Any:
        """应用单个修正"""
        # 子类实现具体的修正逻辑
        return value


class CardElement(BaseElement):
    """卡牌元素"""
    
    def __init__(self, cards: List[Any]):
        super().__init__(ElementType.CARD)
        self.state.current_value = cards
    
    def has_card(self, card_name: str) -> bool:
        """检查是否拥有指定卡牌"""
        return any(card.name == card_name for card in self.state.current_value)
    
    def count_cards(self, card_name: str = None) -> int:
        """统计卡牌数量"""
        if card_name is None:
            return len(self.state.current_value)
        return sum(1 for card in self.state.current_value if card.name == card_name)
    
    def has_card_type(self, card_type: str) -> bool:
        """检查是否拥有指定类型的卡牌"""
        return any(card.category == card_type for card in self.state.current_value)


class HealthElement(BaseElement):
    """血量元素"""
    
    def __init__(self, current_hp: int, max_hp: int):
        super().__init__(ElementType.HEALTH)
        self.state.current_value = current_hp
        self.state.max_value = max_hp
    
    def is_alive(self) -> bool:
        """检查是否存活"""
        return self.calculate_final_value() > 0
    
    def is_dying(self) -> bool:
        """检查是否濒死"""
        return self.calculate_final_value() <= 0
    
    def is_full_health(self) -> bool:
        """检查是否满血"""
        return self.calculate_final_value() >= self.state.max_value
    
    def _apply_single_modifier(self, value: int, modifier: Dict[str, Any]) -> int:
        """应用血量修正"""
        mod_type = modifier.get("type")
        mod_value = modifier.get("value", 0)
        
        if mod_type == "damage":
            return max(0, value - mod_value)
        elif mod_type == "heal":
            return min(self.state.max_value, value + mod_value)
        elif mod_type == "set":
            return mod_value
        
        return value


class FactionElement(BaseElement):
    """势力元素"""
    
    def __init__(self, faction: str):
        super().__init__(ElementType.FACTION)
        self.state.current_value = faction
    
    def is_same_faction(self, other_faction: str) -> bool:
        """检查是否同势力"""
        return self.state.current_value == other_faction
    
    def is_enemy_faction(self, other_faction: str) -> bool:
        """检查是否敌对势力"""
        # 简化的敌对关系，实际可能更复杂
        enemy_relations = {
            "魏": ["蜀", "吴"],
            "蜀": ["魏", "吴"],
            "吴": ["魏", "蜀"],
            "群": []  # 群雄与所有势力都可能敌对
        }
        return other_faction in enemy_relations.get(self.state.current_value, [])


class EquipmentElement(BaseElement):
    """装备元素"""
    
    def __init__(self, weapon=None, armor=None, attack_horse=None, defense_horse=None):
        super().__init__(ElementType.EQUIPMENT)
        self.state.current_value = {
            "weapon": weapon,
            "armor": armor,
            "attack_horse": attack_horse,
            "defense_horse": defense_horse
        }
    
    def has_weapon(self) -> bool:
        """检查是否有武器"""
        return self.state.current_value["weapon"] is not None
    
    def has_armor(self) -> bool:
        """检查是否有防具"""
        return self.state.current_value["armor"] is not None
    
    def has_horse(self, horse_type: str = None) -> bool:
        """检查是否有坐骑"""
        if horse_type is None:
            return (self.state.current_value["attack_horse"] is not None or 
                   self.state.current_value["defense_horse"] is not None)
        return self.state.current_value.get(f"{horse_type}_horse") is not None
    
    def get_attack_range_bonus(self) -> int:
        """获取攻击范围加成"""
        weapon = self.state.current_value["weapon"]
        if not weapon:
            return 0
        
        weapon_ranges = {
            "青龙偃月刀": 2,  # 基础1 + 2 = 3
            "丈八蛇矛": 2,
            "方天画戟": 3,
            "麒麟弓": 4,
            "古锭刀": 1,
            "朱雀羽扇": 3,
            "雌雄双股剑": 1
        }
        return weapon_ranges.get(weapon.name, 0)


class DistanceElement(BaseElement):
    """距离元素"""
    
    def __init__(self, position: int, total_players: int):
        super().__init__(ElementType.DISTANCE)
        self.state.current_value = {
            "position": position,
            "total_players": total_players
        }
    
    def calculate_seat_distance(self, target_position: int) -> int:
        """计算座位距离"""
        pos1 = self.state.current_value["position"]
        pos2 = target_position
        total = self.state.current_value["total_players"]
        
        clockwise = (pos2 - pos1) % total
        counter_clockwise = (pos1 - pos2) % total
        return min(clockwise, counter_clockwise)
    
    def calculate_attack_distance(self, target_position: int, equipment_element: EquipmentElement) -> int:
        """计算攻击距离（考虑装备修正）"""
        base_distance = self.calculate_seat_distance(target_position)
        
        # 进攻马：攻击距离-1
        if equipment_element.has_horse("attack"):
            base_distance -= 1
        
        return max(1, base_distance)  # 最小距离为1
    
    def calculate_defense_distance(self, attacker_position: int, equipment_element: EquipmentElement) -> int:
        """计算防御距离（考虑装备修正）"""
        base_distance = self.calculate_seat_distance(attacker_position)
        
        # 防御马：被攻击距离+1
        if equipment_element.has_horse("defense"):
            base_distance += 1
        
        return base_distance


class ElementBasedAdjudicationEngine:
    """基于基础元素的裁决引擎"""
    
    def __init__(self):
        self.element_checkers: Dict[str, Callable] = {}
        self.skill_compositions: Dict[str, List[Dict[str, Any]]] = {}
        self._register_default_checkers()
    
    def _register_default_checkers(self):
        """注册默认的元素检查器"""
        self.element_checkers.update({
            "has_card": self._check_has_card,
            "is_alive": self._check_is_alive,
            "in_attack_range": self._check_in_attack_range,
            "same_faction": self._check_same_faction,
            "has_weapon": self._check_has_weapon,
            "has_armor": self._check_has_armor,
        })
    
    def register_skill_composition(self, skill_name: str, element_requirements: List[Dict[str, Any]]):
        """注册技能的基础元素组合"""
        self.skill_compositions[skill_name] = element_requirements
    
    def check_element_condition(self, condition_name: str, player_elements: Dict[str, BaseElement], 
                              target_elements: Dict[str, BaseElement] = None, **kwargs) -> bool:
        """检查基础元素条件"""
        if condition_name not in self.element_checkers:
            logger.warning(f"未知的元素检查条件: {condition_name}")
            return False
        
        return self.element_checkers[condition_name](player_elements, target_elements, **kwargs)
    
    def check_skill_requirements(self, skill_name: str, player_elements: Dict[str, BaseElement],
                               target_elements: Dict[str, BaseElement] = None) -> bool:
        """检查技能的基础元素需求"""
        if skill_name not in self.skill_compositions:
            logger.warning(f"未注册的技能: {skill_name}")
            return False
        
        requirements = self.skill_compositions[skill_name]
        for requirement in requirements:
            condition = requirement["condition"]
            if not self.check_element_condition(condition, player_elements, target_elements, **requirement.get("params", {})):
                return False
        
        return True
    
    # 基础元素检查器实现
    def _check_has_card(self, player_elements: Dict[str, BaseElement], 
                       target_elements: Dict[str, BaseElement], card_name: str = None, **kwargs) -> bool:
        """检查是否有指定卡牌"""
        card_element = player_elements.get("card")
        if not isinstance(card_element, CardElement):
            return False
        
        if card_name:
            return card_element.has_card(card_name)
        return card_element.count_cards() > 0
    
    def _check_is_alive(self, player_elements: Dict[str, BaseElement], 
                       target_elements: Dict[str, BaseElement], **kwargs) -> bool:
        """检查是否存活"""
        health_element = player_elements.get("health")
        if not isinstance(health_element, HealthElement):
            return False
        return health_element.is_alive()
    
    def _check_in_attack_range(self, player_elements: Dict[str, BaseElement], 
                              target_elements: Dict[str, BaseElement], **kwargs) -> bool:
        """检查是否在攻击范围内"""
        if not target_elements:
            return False
        
        player_distance = player_elements.get("distance")
        player_equipment = player_elements.get("equipment")
        target_distance = target_elements.get("distance")
        target_equipment = target_elements.get("equipment")
        
        if not all([player_distance, player_equipment, target_distance, target_equipment]):
            return False
        
        # 计算攻击距离
        attack_distance = player_distance.calculate_attack_distance(
            target_distance.state.current_value["position"], player_equipment)
        
        # 计算防御距离
        defense_distance = target_distance.calculate_defense_distance(
            player_distance.state.current_value["position"], target_equipment)
        
        # 获取攻击范围
        base_range = 1
        weapon_bonus = player_equipment.get_attack_range_bonus()
        attack_range = base_range + weapon_bonus
        
        return min(attack_distance, defense_distance) <= attack_range
    
    def _check_same_faction(self, player_elements: Dict[str, BaseElement], 
                           target_elements: Dict[str, BaseElement], **kwargs) -> bool:
        """检查是否同势力"""
        if not target_elements:
            return False
        
        player_faction = player_elements.get("faction")
        target_faction = target_elements.get("faction")
        
        if not all([player_faction, target_faction]):
            return False
        
        return player_faction.is_same_faction(target_faction.state.current_value)
    
    def _check_has_weapon(self, player_elements: Dict[str, BaseElement], 
                         target_elements: Dict[str, BaseElement], **kwargs) -> bool:
        """检查是否有武器"""
        equipment_element = player_elements.get("equipment")
        if not isinstance(equipment_element, EquipmentElement):
            return False
        return equipment_element.has_weapon()
    
    def _check_has_armor(self, player_elements: Dict[str, BaseElement], 
                        target_elements: Dict[str, BaseElement], **kwargs) -> bool:
        """检查是否有防具"""
        equipment_element = player_elements.get("equipment")
        if not isinstance(equipment_element, EquipmentElement):
            return False
        return equipment_element.has_armor()


# 全局实例
element_adjudication_engine = ElementBasedAdjudicationEngine()

# 注册一些常见技能的基础元素组合
element_adjudication_engine.register_skill_composition("奸雄", [
    {"condition": "is_alive", "description": "角色必须存活"},
    {"condition": "has_card", "params": {"card_name": None}, "description": "可以获得造成伤害的牌"}
])

element_adjudication_engine.register_skill_composition("突袭", [
    {"condition": "is_alive", "description": "角色必须存活"},
    {"condition": "has_card", "params": {"card_name": None}, "description": "需要有手牌进行突袭"}
])