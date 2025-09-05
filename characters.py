"""
三国杀武将角色实现
"""
from enum import Enum
from typing import List, Optional
from game import Card, Player, Game, CardType
from skills import SkillManager, JianXiong, FanKui, GangLie, PaoXiao, GuanXing, QiXi, KeJi, YingZi

class Kingdom(Enum):
    WEI = "魏"
    SHU = "蜀"
    WU = "吴"

class Character:
    """武将基类"""
    def __init__(self, name: str, kingdom: Kingdom, max_hp: int, skills: List[str] = None):
        self.name = name
        self.kingdom = kingdom
        self.max_hp = max_hp
        self.hp = max_hp
        self.skills = skills if skills is not None else []
        self.cards = []  # 添加手牌属性

    def has_skill(self, skill_name: str) -> bool:
        """检查角色是否拥有指定技能"""
        return skill_name in self.skills
    
    def use_skill(self, skill_name: str, game: Game, player: Player, target: Optional[Player] = None) -> bool:
        # 使用技能管理器触发技能
        # 注意：在实际项目中，skill_manager应该作为全局单例或在游戏初始化时创建并传递
        # 这里为了简化实现，每次调用都创建新的skill_manager
        skill_manager = SkillManager()
        # 注册技能（实际项目中应在初始化时注册）
        skill_manager.register_skill(JianXiong())
        skill_manager.register_skill(FanKui())
        skill_manager.register_skill(GangLie())
        skill_manager.register_skill(PaoXiao())
        skill_manager.register_skill(GuanXing())
        skill_manager.register_skill(QiXi())
        skill_manager.register_skill(KeJi())
        skill_manager.register_skill(YingZi())
        
        return skill_manager.trigger_skill(skill_name, game, player, target)

    def draw_card(self, card: Card):
        """抽牌"""
        self.cards.append(card)

    def discard_card(self, card: Card):
        """弃牌"""
        if card in self.cards:
            self.cards.remove(card)

# 扩展技能逻辑示例
class CaoCao(Character):
    """曹操"""
    def __init__(self):
        super().__init__("曹操", Kingdom.WEI, 4, ["奸雄"])
        
    def use_skill(self, skill_name: str, game: Game, player: Player, target: Optional[Player] = None) -> bool:
        return super().use_skill(skill_name, game, player, target)

class SimaYi(Character):
    """司马懿"""
    def __init__(self):
        super().__init__("司马懿", Kingdom.WEI, 3, ["反馈"])
        
    def use_skill(self, skill_name: str, game: Game, player: Player, target: Optional[Player] = None) -> bool:
        return super().use_skill(skill_name, game, player, target)

# ========== 蜀国武将 ==========
class LiuBei(Character):
    """刘备"""
    def __init__(self):
        super().__init__("刘备", Kingdom.SHU, 4, ["仁德"])
        
    def use_skill(self, skill_name: str, game: Game, player: Player, target: Optional[Player] = None) -> bool:
        if skill_name == "仁德":
            # 出牌阶段，你可以将任意数量的手牌交给一名其他角色
            print(f"{self.name} 发动技能【仁德】")
            return True
        return False

class GuanYu(Character):
    """关羽"""
    def __init__(self):
        super().__init__("关羽", Kingdom.SHU, 4, ["武圣"])
        
    def use_skill(self, skill_name: str, game: Game, player: Player, target: Optional[Player] = None) -> bool:
        if skill_name == "武圣":
            # 你可以将任意一张红色牌当【杀】使用或打出
            print(f"{self.name} 发动技能【武圣】")
            return True
        return False

class ZhaoYun(Character):
    """赵云"""
    def __init__(self):
        super().__init__("赵云", Kingdom.SHU, 4, ["龙胆"])

    def use_skill(self, skill_name: str, game: Game, player: Player, target: Optional[Player] = None) -> bool:
        if skill_name == "龙胆":
            # 你可以将任意一张黑色牌当【闪】使用或打出
            print(f"{self.name} 发动技能【龙胆】")
            return True
        return False

# ========== 吴国武将 ==========
class SunQuan(Character):
    """孙权"""
    def __init__(self):
        super().__init__("孙权", Kingdom.WU, 4, ["制衡"])
        
    def use_skill(self, skill_name: str, game: Game, player: Player, target: Optional[Player] = None) -> bool:
        if skill_name == "制衡":
            # 出牌阶段限一次，你可以弃置任意数量的牌，然后摸取等量的牌
            print(f"{self.name} 发动技能【制衡】")
            return True
        return False

class ZhouYu(Character):
    """周瑜"""
    def __init__(self):
        super().__init__("周瑜", Kingdom.WU, 3, ["英姿", "反间"])
        
    def use_skill(self, skill_name: str, game: Game, player: Player, target: Optional[Player] = None) -> bool:
        return super().use_skill(skill_name, game, player, target)

class LuMeng(Character):
    """吕蒙"""
    def __init__(self):
        super().__init__("吕蒙", Kingdom.WU, 4, ["克己"])

    def use_skill(self, skill_name: str, game: Game, player: Player, target: Optional[Player] = None) -> bool:
        return super().use_skill(skill_name, game, player, target)

# ========== 其他武将 ==========
class ZhangLiao(Character):
    """张辽"""
    def __init__(self):
        super().__init__("张辽", Kingdom.WEI, 4, ["突袭"])

    def use_skill(self, skill_name: str, game: Game, player: Player, target: Optional[Player] = None) -> bool:
        if skill_name == "突袭":
            # 摸牌阶段，你可以选择一名其他角色并获得其一张手牌
            print(f"{self.name} 发动技能【突袭】")
            return True
        return False


class XiahouDun(Character):
    """夏侯惇"""
    def __init__(self):
        super().__init__("夏侯惇", Kingdom.WEI, 4, ["刚烈"])
        
    def use_skill(self, skill_name: str, game: Game, player: Player, target: Optional[Player] = None) -> bool:
        return super().use_skill(skill_name, game, player, target)


class ZhangFei(Character):
    """张飞"""
    def __init__(self):
        super().__init__("张飞", Kingdom.SHU, 4, ["咆哮"])
        
    def use_skill(self, skill_name: str, game: Game, player: Player, target: Optional[Player] = None) -> bool:
        return super().use_skill(skill_name, game, player, target)


class ZhugeLiang(Character):
    """诸葛亮"""
    def __init__(self):
        super().__init__("诸葛亮", Kingdom.SHU, 3, ["观星"])
        
    def use_skill(self, skill_name: str, game: Game, player: Player, target: Optional[Player] = None) -> bool:
        return super().use_skill(skill_name, game, player, target)


class GanNing(Character):
    """甘宁"""
    def __init__(self):
        super().__init__("甘宁", Kingdom.WU, 4, ["奇袭"])
        
    def use_skill(self, skill_name: str, game: Game, player: Player, target: Optional[Player] = None) -> bool:
        return super().use_skill(skill_name, game, player, target)

# 武将工厂
class CharacterFactory:
    @staticmethod
    def create_character(name: str) -> Optional[Character]:
        """根据名称创建武将实例"""
        characters = {
            "曹操": CaoCao,
            "司马懿": SimaYi,
            "张辽": ZhangLiao,
            "夏侯惇": XiahouDun,
            "刘备": LiuBei,
            "关羽": GuanYu,
            "张飞": ZhangFei,
            "赵云": ZhaoYun,
            "诸葛亮": ZhugeLiang,
            "孙权": SunQuan,
            "周瑜": ZhouYu,
            "甘宁": GanNing,
            "吕蒙": LuMeng,
        }
        
        if name in characters:
            return characters[name]()
        return None