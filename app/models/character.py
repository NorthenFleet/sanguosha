"""
三国杀1v1武将模块
"""
from enum import Enum
from typing import List


class Kingdom(Enum):
    WEI = "魏"
    SHU = "蜀"
    WU = "吴"
    QUN = "群"


class Character:
    """武将基类"""
    def __init__(self, name: str, kingdom: Kingdom, max_hp: int, skills: List[str]):
        self.name = name
        self.kingdom = kingdom
        self.max_hp = max_hp
        self.hp = max_hp
        self.skills = skills
    
    def has_skill(self, skill_name: str) -> bool:
        """检查武将是否拥有指定技能"""
        return skill_name in self.skills
    
    def use_skill(self, skill_name: str, game_context=None, player=None):
        """使用技能"""
        if self.has_skill(skill_name):
            print(f"{self.name} 使用了技能 {skill_name}")
            # 技能效果实现
            return True
        return False


# ========== 魏势力 ==========

class CaoCao(Character):
    """曹操"""
    def __init__(self):
        super().__init__("曹操", Kingdom.WEI, 4, ["奸雄"])


class SimaYi(Character):
    """司马懿"""
    def __init__(self):
        super().__init__("司马懿", Kingdom.WEI, 3, ["反馈"])


class ZhangLiao(Character):
    """张辽"""
    def __init__(self):
        super().__init__("张辽", Kingdom.WEI, 4, ["突袭"])


class XiaHouDun(Character):
    """夏侯惇"""
    def __init__(self):
        super().__init__("夏侯惇", Kingdom.WEI, 4, ["刚烈"])


# ========== 蜀势力 ==========

class LiuBei(Character):
    """刘备"""
    def __init__(self):
        super().__init__("刘备", Kingdom.SHU, 4, ["仁德"])
    
    def use_skill(self, skill_name: str, game_context=None, player=None):
        if skill_name == "仁德":
            print(f"{self.name} 使用了技能 {skill_name}")
            # 仁德技能逻辑：可以让对方摸牌
            return True
        return super().use_skill(skill_name, game_context, player)


class GuanYu(Character):
    """关羽"""
    def __init__(self):
        super().__init__("关羽", Kingdom.SHU, 4, ["武圣"])
    
    def use_skill(self, skill_name: str, game_context=None, player=None):
        if skill_name == "武圣":
            print(f"{self.name} 使用了技能 {skill_name}")
            # 武圣技能逻辑：可以将红色牌当杀使用
            return True
        return super().use_skill(skill_name, game_context, player)


class ZhangFei(Character):
    """张飞"""
    def __init__(self):
        super().__init__("张飞", Kingdom.SHU, 4, ["咆哮"])


class ZhaoYun(Character):
    """赵云"""
    def __init__(self):
        super().__init__("赵云", Kingdom.SHU, 4, ["龙胆"])


# ========== 吴势力 ==========

class SunQuan(Character):
    """孙权"""
    def __init__(self):
        super().__init__("孙权", Kingdom.WU, 4, ["制衡"])


class ZhouYu(Character):
    """周瑜"""
    def __init__(self):
        super().__init__("周瑜", Kingdom.WU, 3, ["英姿", "反间"])


class GanNing(Character):
    """甘宁"""
    def __init__(self):
        super().__init__("甘宁", Kingdom.WU, 4, ["奇袭"])


class LuMeng(Character):
    """吕蒙"""
    def __init__(self):
        super().__init__("吕蒙", Kingdom.WU, 4, ["克己"])


# ========== 群势力 ==========

class HuaTuo(Character):
    """华佗"""
    def __init__(self):
        super().__init__("华佗", Kingdom.QUN, 3, ["急救"])


class LvBu(Character):
    """吕布"""
    def __init__(self):
        super().__init__("吕布", Kingdom.QUN, 4, ["无双"])


class DiaoChan(Character):
    """貂蝉"""
    def __init__(self):
        super().__init__("貂蝉", Kingdom.QUN, 3, ["离间"])


class CharacterFactory:
    """武将工厂类"""
    @staticmethod
    def create_character(name: str) -> Character:
        """根据名称创建武将实例"""
        characters = {
            "曹操": CaoCao,
            "司马懿": SimaYi,
            "张辽": ZhangLiao,
            "夏侯惇": XiaHouDun,
            "刘备": LiuBei,
            "关羽": GuanYu,
            "张飞": ZhangFei,
            "赵云": ZhaoYun,
            "诸葛亮": ZhugeLiang,
            "孙权": SunQuan,
            "周瑜": ZhouYu,
            "甘宁": GanNing,
            "吕蒙": LuMeng,
            "华佗": HuaTuo,
            "吕布": LvBu,
            "貂蝉": DiaoChan
        }
        
        if name in characters:
            return characters[name]()
        else:
            raise ValueError(f"未知的武将: {name}")


class ZhugeLiang(Character):
    """诸葛亮"""
    def __init__(self):
        super().__init__("诸葛亮", Kingdom.SHU, 3, ["观星", "空城"])