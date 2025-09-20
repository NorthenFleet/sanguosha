"""
统一的目标选择接口
提供灵活的目标选择机制，支持单目标、多目标、条件筛选等功能
"""

from typing import List, Optional, Callable, Dict, Any
from app.models.player import Player


class TargetSelectionCriteria:
    """目标选择条件"""
    
    def __init__(self, 
                 exclude_self: bool = True,
                 exclude_dead: bool = True,
                 distance_limit: Optional[int] = None,
                 custom_filter: Optional[Callable[[Player], bool]] = None,
                 description: str = ""):
        self.exclude_self = exclude_self
        self.exclude_dead = exclude_dead
        self.distance_limit = distance_limit
        self.custom_filter = custom_filter
        self.description = description


class TargetSelector:
    """统一的目标选择器"""
    
    @staticmethod
    def select_single_target(game, player: Player, 
                           prompt: str = "选择目标玩家",
                           criteria: Optional[TargetSelectionCriteria] = None,
                           test_mode: bool = False) -> Optional[Player]:
        """选择单个目标"""
        if criteria is None:
            criteria = TargetSelectionCriteria()
        
        # 获取可选目标
        available_targets = TargetSelector._get_available_targets(
            game, player, criteria
        )
        
        if not available_targets:
            print("没有可选择的目标。")
            return None
        
        # 在2人游戏中，如果只有一个可选目标，直接返回
        if len(available_targets) == 1:
            return available_targets[0]
        
        # 测试模式下自动选择第一个目标
        if test_mode:
            return available_targets[0]
        
        # 显示目标选择界面
        return TargetSelector._show_target_selection_ui(
            available_targets, prompt
        )
    
    @staticmethod
    def select_multiple_targets(game, player: Player,
                              min_targets: int = 1,
                              max_targets: int = 1,
                              prompt: str = "选择目标玩家",
                              criteria: Optional[TargetSelectionCriteria] = None,
                              test_mode: bool = False) -> List[Player]:
        """选择多个目标"""
        if criteria is None:
            criteria = TargetSelectionCriteria()
        
        # 获取可选目标
        available_targets = TargetSelector._get_available_targets(
            game, player, criteria
        )
        
        if not available_targets:
            print("没有可选择的目标。")
            return []
        
        # 测试模式下自动选择前N个目标
        if test_mode:
            return available_targets[:min(max_targets, len(available_targets))]
        
        # 显示多目标选择界面
        return TargetSelector._show_multi_target_selection_ui(
            available_targets, min_targets, max_targets, prompt
        )
    
    @staticmethod
    def _get_available_targets(game, player: Player, 
                             criteria: TargetSelectionCriteria) -> List[Player]:
        """获取符合条件的可选目标"""
        available_targets = []
        
        for p in game.players:
            # 排除自己
            if criteria.exclude_self and p == player:
                continue
            
            # 排除死亡角色
            if criteria.exclude_dead and hasattr(p, 'character') and p.character.hp <= 0:
                continue
            
            # 距离限制
            if criteria.distance_limit is not None:
                if hasattr(player, 'get_distance_to'):
                    distance = player.get_distance_to(p)
                    if distance > criteria.distance_limit:
                        continue
            
            # 自定义过滤条件
            if criteria.custom_filter and not criteria.custom_filter(p):
                continue
            
            available_targets.append(p)
        
        return available_targets
    
    @staticmethod
    def _show_target_selection_ui(targets: List[Player], prompt: str) -> Optional[Player]:
        """显示目标选择界面"""
        print(f"\n{prompt}")
        for i, target in enumerate(targets):
            print(f"{i+1}. {target.character.name}")
        
        while True:
            try:
                user_input = input("请选择目标编号: ").strip()
                if not user_input:
                    print("输入不能为空，请重新选择。")
                    continue
                
                choice = int(user_input) - 1
                if 0 <= choice < len(targets):
                    return targets[choice]
                else:
                    print("无效的选择，请重新选择。")
            except (ValueError, EOFError, KeyboardInterrupt):
                print("输入无效或游戏被中断。")
                return None
    
    @staticmethod
    def _show_multi_target_selection_ui(targets: List[Player], 
                                      min_targets: int, 
                                      max_targets: int,
                                      prompt: str) -> List[Player]:
        """显示多目标选择界面"""
        print(f"\n{prompt}")
        print(f"需要选择 {min_targets}-{max_targets} 个目标")
        for i, target in enumerate(targets):
            print(f"{i+1}. {target.character.name}")
        
        selected_targets = []
        
        while len(selected_targets) < max_targets:
            try:
                if len(selected_targets) >= min_targets:
                    user_input = input(f"请选择目标编号（已选择{len(selected_targets)}个，输入0结束选择）: ").strip()
                    if user_input == "0":
                        break
                else:
                    user_input = input(f"请选择目标编号（已选择{len(selected_targets)}个）: ").strip()
                
                if not user_input:
                    print("输入不能为空，请重新选择。")
                    continue
                
                choice = int(user_input) - 1
                if 0 <= choice < len(targets):
                    target = targets[choice]
                    if target not in selected_targets:
                        selected_targets.append(target)
                        print(f"已选择: {target.character.name}")
                    else:
                        print("该目标已被选择，请选择其他目标。")
                else:
                    print("无效的选择，请重新选择。")
            except (ValueError, EOFError, KeyboardInterrupt):
                print("输入无效或游戏被中断。")
                break
        
        return selected_targets


class CardTargetSelector:
    """卡牌专用目标选择器"""
    
    @staticmethod
    def select_jiedao_targets(game, player: Player, test_mode: bool = False) -> tuple:
        """借刀杀人的双目标选择"""
        # 第一步：选择装备武器的角色
        weapon_criteria = TargetSelectionCriteria(
            exclude_self=True,
            custom_filter=lambda p: hasattr(p, 'weapon') and p.weapon is not None,
            description="选择装备武器的角色"
        )
        
        weapon_holder = TargetSelector.select_single_target(
            game, player, "选择【借刀杀人】的武器持有者", weapon_criteria, test_mode
        )
        
        if not weapon_holder:
            return None, None
        
        # 第二步：选择攻击目标
        attack_criteria = TargetSelectionCriteria(
            exclude_self=False,  # 可以攻击借刀杀人的使用者
            custom_filter=lambda p: (p != weapon_holder and 
                                   weapon_holder.can_attack(p, game.players)),
            description="选择攻击目标"
        )
        
        attack_target = TargetSelector.select_single_target(
            game, weapon_holder, f"选择 {weapon_holder.character.name} 要攻击的目标", 
            attack_criteria, test_mode
        )
        
        return weapon_holder, attack_target
    
    @staticmethod
    def select_guohe_target(game, player: Player, test_mode: bool = False) -> Optional[Player]:
        """过河拆桥目标选择"""
        criteria = TargetSelectionCriteria(
            exclude_self=True,
            custom_filter=lambda p: len(p.get_all_cards()['hand']) > 0 or 
                                  len(p.get_all_cards()['equipment']) > 0 or
                                  len(p.get_all_cards()['judgment']) > 0,
            description="选择有牌的角色"
        )
        
        return TargetSelector.select_single_target(
            game, player, "选择【过河拆桥】的目标", criteria, test_mode
        )
    
    @staticmethod
    def select_shunshou_target(game, player: Player, test_mode: bool = False) -> Optional[Player]:
        """顺手牵羊目标选择"""
        criteria = TargetSelectionCriteria(
            exclude_self=True,
            distance_limit=1,
            custom_filter=lambda p: len(p.get_all_cards()['hand']) > 0 or 
                                  len(p.get_all_cards()['equipment']) > 0 or
                                  len(p.get_all_cards()['judgment']) > 0,
            description="选择距离为1且有牌的角色"
        )
        
        return TargetSelector.select_single_target(
            game, player, "选择【顺手牵羊】的目标", criteria, test_mode
        )
    
    @staticmethod
    def select_juedou_target(game, player: Player, test_mode: bool = False) -> Optional[Player]:
        """决斗目标选择"""
        criteria = TargetSelectionCriteria(
            exclude_self=True,
            description="选择决斗对象"
        )
        
        return TargetSelector.select_single_target(
            game, player, "选择【决斗】的目标", criteria, test_mode
        )