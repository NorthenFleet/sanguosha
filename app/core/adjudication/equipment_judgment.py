#!/usr/bin/env python3
"""
装备判定系统
处理武器和防御装备的功能属性判定
"""

from typing import Dict, Any, Optional
from ...models.player import Player
from ...models.card import Card


class EquipmentJudgment:
    """装备判定系统"""
    
    def __init__(self):
        self.weapon_handlers = {
            "青龙偃月刀": self._handle_qinglong_yanyuedao,
            "丈八蛇矛": self._handle_zhangba_shemao,
            "方天画戟": self._handle_fangtian_huaji,
            "麒麟弓": self._handle_qilin_gong,
            "古锭刀": self._handle_guding_dao,
            "朱雀羽扇": self._handle_zhuque_yushan,
            "雌雄双股剑": self._handle_cixiong_shuanggujian
        }
        
        self.defense_handlers = {
            "八卦阵": self._handle_bagua_zhen,
            "仁王盾": self._handle_renwang_dun,
            "白银狮子": self._handle_baiyin_shizi,
            "藤甲": self._handle_tengjia
        }
    
    def judge_weapon_effect(self, attacker: Player, target: Player, card: Card, context: Dict[str, Any]) -> Dict[str, Any]:
        """判定武器效果"""
        if not attacker.weapon:
            return {"can_trigger": False, "effect": None}
        
        weapon_name = attacker.weapon.name
        if weapon_name in self.weapon_handlers:
            return self.weapon_handlers[weapon_name](attacker, target, card, context)
        
        return {"can_trigger": False, "effect": None}
    
    def judge_defense_effect(self, defender: Player, attacker: Player, card: Card, context: Dict[str, Any]) -> Dict[str, Any]:
        """判定防御装备效果"""
        if not defender.defense:
            return {"can_trigger": False, "effect": None}
        
        defense_name = defender.defense.name
        if defense_name in self.defense_handlers:
            return self.defense_handlers[defense_name](defender, attacker, card, context)
        
        return {"can_trigger": False, "effect": None}
    
    def calculate_final_damage(self, attacker: Player, defender: Player, base_damage: int, damage_source: Card) -> int:
        """计算最终伤害（考虑武器增强和防御减免）"""
        final_damage = base_damage
        
        # 武器伤害增强
        if attacker.weapon:
            weapon_effect = attacker.get_weapon_effects()
            if weapon_effect.get("type") == "damage_enhancement":
                # 古锭刀：目标没有手牌时伤害+1
                if weapon_effect.get("effect") == "extra_damage_no_hand" and len(defender.hand_cards) == 0:
                    final_damage += 1
                    print(f"[武器效果] {attacker.character.name}的{attacker.weapon.name}发动：目标无手牌，伤害+1")
        
        # 防御装备减免
        final_damage = defender.calculate_damage_reduction(final_damage, damage_source)
        
        return max(0, final_damage)
    
    # 武器效果处理器
    def _handle_qinglong_yanyuedao(self, attacker: Player, target: Player, card: Card, context: Dict[str, Any]) -> Dict[str, Any]:
        """青龙偃月刀：当你使用的杀被闪抵消时，你可以立即对同一目标再使用一张杀"""
        if context.get("trigger") == "sha_dodged" and card.name == "杀":
            # 检查是否还有杀可以使用
            has_sha = any(c.name == "杀" for c in attacker.hand_cards)
            return {
                "can_trigger": has_sha,
                "effect": "extra_sha",
                "description": f"{attacker.character.name}的青龙偃月刀发动，可以再使用一张杀"
            }
        return {"can_trigger": False, "effect": None}
    
    def _handle_zhangba_shemao(self, attacker: Player, target: Player, card: Card, context: Dict[str, Any]) -> Dict[str, Any]:
        """丈八蛇矛：你可以将两张手牌当杀使用或打出"""
        if context.get("trigger") == "need_sha" and len(attacker.hand_cards) >= 2:
            return {
                "can_trigger": True,
                "effect": "two_cards_as_sha",
                "description": f"{attacker.character.name}的丈八蛇矛发动，可以将两张手牌当杀使用"
            }
        return {"can_trigger": False, "effect": None}
    
    def _handle_fangtian_huaji(self, attacker: Player, target: Player, card: Card, context: Dict[str, Any]) -> Dict[str, Any]:
        """方天画戟：当你使用的杀是你最后的手牌时，你可以额外指定至多两个目标"""
        if context.get("trigger") == "use_sha" and len(attacker.hand_cards) == 1 and card.name == "杀":
            return {
                "can_trigger": True,
                "effect": "multi_target_sha",
                "description": f"{attacker.character.name}的方天画戟发动，可以额外指定至多两个目标"
            }
        return {"can_trigger": False, "effect": None}
    
    def _handle_qilin_gong(self, attacker: Player, target: Player, card: Card, context: Dict[str, Any]) -> Dict[str, Any]:
        """麒麟弓：当你使用杀对目标造成伤害时，你可以弃置其装备区里的一张牌"""
        if context.get("trigger") == "sha_damage" and len(target.equipped) > 0:
            return {
                "can_trigger": True,
                "effect": "destroy_equipment",
                "description": f"{attacker.character.name}的麒麟弓发动，可以弃置{target.character.name}装备区的一张牌"
            }
        return {"can_trigger": False, "effect": None}
    
    def _handle_guding_dao(self, attacker: Player, target: Player, card: Card, context: Dict[str, Any]) -> Dict[str, Any]:
        """古锭刀：当你使用的杀对目标造成伤害时，若其没有手牌，此伤害+1"""
        if context.get("trigger") == "sha_damage" and len(target.hand_cards) == 0:
            return {
                "can_trigger": True,
                "effect": "extra_damage_no_hand",
                "description": f"{attacker.character.name}的古锭刀发动，{target.character.name}无手牌，伤害+1"
            }
        return {"can_trigger": False, "effect": None}
    
    def _handle_zhuque_yushan(self, attacker: Player, target: Player, card: Card, context: Dict[str, Any]) -> Dict[str, Any]:
        """朱雀羽扇：你可以将一张普通杀当火杀使用"""
        if context.get("trigger") == "use_sha" and card.name == "杀" and not hasattr(card, 'damage_type'):
            return {
                "can_trigger": True,
                "effect": "fire_sha",
                "description": f"{attacker.character.name}的朱雀羽扇发动，将杀当火杀使用"
            }
        return {"can_trigger": False, "effect": None}
    
    def _handle_cixiong_shuanggujian(self, attacker: Player, target: Player, card: Card, context: Dict[str, Any]) -> Dict[str, Any]:
        """雌雄双股剑：当你使用杀指定异性角色为目标时，你可以令其选择：弃置一张手牌，或令你摸一张牌"""
        if (context.get("trigger") == "sha_target" and 
            hasattr(attacker.character, 'gender') and hasattr(target.character, 'gender') and
            attacker.character.gender != target.character.gender):
            return {
                "can_trigger": True,
                "effect": "discard_or_draw",
                "description": f"{attacker.character.name}的雌雄双股剑发动，{target.character.name}选择弃牌或让攻击者摸牌"
            }
        return {"can_trigger": False, "effect": None}
    
    # 防御装备效果处理器
    def _handle_bagua_zhen(self, defender: Player, attacker: Player, card: Card, context: Dict[str, Any]) -> Dict[str, Any]:
        """八卦阵：当你需要使用或打出闪时，你可以进行判定：若结果为红色，则视为你使用或打出了一张闪"""
        if context.get("trigger") == "need_shan":
            # 非锁定技，需要玩家选择
            if defender.ask_defense_equipment_choice("need_shan", context):
                return {
                    "can_trigger": True,
                    "effect": "judgment_shan",
                    "description": f"{defender.character.name}的八卦阵发动，进行判定"
                }
            else:
                return {
                    "can_trigger": False,
                    "effect": None,
                    "description": f"{defender.character.name}选择不发动八卦阵"
                }
        return {"can_trigger": False, "effect": None}
    
    def _handle_renwang_dun(self, defender: Player, attacker: Player, card: Card, context: Dict[str, Any]) -> Dict[str, Any]:
        """仁王盾：黑色的杀对你无效"""
        if (context.get("trigger") == "receive_sha" and card.name == "杀" and 
            hasattr(card, 'suit') and card.suit in ["黑桃", "梅花"]):
            # 锁定技，自动触发
            return {
                "can_trigger": True,
                "effect": "prevent_black_sha",
                "description": f"{defender.character.name}的仁王盾自动发动，黑色杀无效"
            }
        return {"can_trigger": False, "effect": None}
    
    def _handle_baiyin_shizi(self, defender: Player, attacker: Player, card: Card, context: Dict[str, Any]) -> Dict[str, Any]:
        """白银狮子：当你受到伤害时，若此伤害大于1点，你可以防止多余的伤害"""
        if context.get("trigger") == "receive_damage" and context.get("damage_amount", 0) > 1:
            return {
                "can_trigger": True,
                "effect": "reduce_damage_to_1",
                "description": f"{defender.character.name}的白银狮子发动，伤害减少到1点"
            }
        return {"can_trigger": False, "effect": None}
    
    def _handle_tengjia(self, defender: Player, attacker: Player, card: Card, context: Dict[str, Any]) -> Dict[str, Any]:
        """藤甲：南蛮入侵、万箭齐发和普通杀对你无效。你受到火焰伤害时，此伤害+1"""
        if context.get("trigger") == "receive_damage":
            if card.name in ["南蛮入侵", "万箭齐发"] or (card.name == "杀" and not hasattr(card, 'damage_type')):
                return {
                    "can_trigger": True,
                    "effect": "prevent_normal_damage",
                    "description": f"{defender.character.name}的藤甲发动，{card.name}无效"
                }
            elif hasattr(card, 'damage_type') and card.damage_type == "fire":
                return {
                    "can_trigger": True,
                    "effect": "fire_weakness",
                    "description": f"{defender.character.name}的藤甲：火焰伤害+1"
                }
        return {"can_trigger": False, "effect": None}


# 全局装备判定系统实例
equipment_judgment = EquipmentJudgment()