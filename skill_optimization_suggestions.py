#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
三国杀技能优化建议和示例代码
提供技能触发机制和游戏集成的优化方案
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.models.character import CharacterFactory
from app.models.player import Player
from app.core.base.game import Game
from app.models.card import Card
from app.models.enums import CardType
from app.models.skills import SkillManager
from app.core.events.event_system import EventManager

class OptimizedSkillManager:
    """优化的技能管理器示例"""
    
    def __init__(self):
        self.skills = {}
        self.phase_skills = {
            'prepare': [],
            'draw': [],
            'play': [],
            'discard': [],
            'end': []
        }
        self.trigger_skills = {
            'damage_dealt': [],
            'damage_received': [],
            'card_used': [],
            'card_played': [],
            'turn_start': [],
            'turn_end': []
        }
    
    def register_skill(self, skill):
        """注册技能到相应的触发时机"""
        self.skills[skill.name] = skill
        
        # 根据技能类型注册到不同的触发列表
        if hasattr(skill, 'trigger_phase'):
            if skill.trigger_phase in self.phase_skills:
                self.phase_skills[skill.trigger_phase].append(skill)
        
        if hasattr(skill, 'trigger_events'):
            for event in skill.trigger_events:
                if event in self.trigger_skills:
                    self.trigger_skills[event].append(skill)
    
    def get_phase_skills(self, phase):
        """获取特定阶段的技能"""
        return self.phase_skills.get(phase, [])
    
    def get_trigger_skills(self, event):
        """获取特定事件的触发技能"""
        return self.trigger_skills.get(event, [])
    
    def execute_phase_skills(self, game, player, phase):
        """执行阶段技能"""
        skills = self.get_phase_skills(phase)
        executed_skills = []
        
        for skill in skills:
            if skill.can_trigger(game, player, phase):
                if skill.is_mandatory or self.should_activate_skill(player, skill):
                    result = skill.execute(game, player)
                    executed_skills.append((skill, result))
        
        return executed_skills
    
    def execute_trigger_skills(self, game, player, event, **kwargs):
        """执行事件触发技能"""
        skills = self.get_trigger_skills(event)
        executed_skills = []
        
        for skill in skills:
            if skill.can_trigger(game, player, event, **kwargs):
                if skill.is_mandatory or self.should_activate_skill(player, skill):
                    result = skill.execute(game, player, **kwargs)
                    executed_skills.append((skill, result))
        
        return executed_skills
    
    def should_activate_skill(self, player, skill):
        """判断是否应该激活技能（AI决策或玩家选择）"""
        # 这里可以实现AI决策逻辑或玩家选择界面
        # 目前简化为总是激活
        return True

class EnhancedSkill:
    """增强的技能基类示例"""
    
    def __init__(self, name, description, is_mandatory=False):
        self.name = name
        self.description = description
        self.is_mandatory = is_mandatory  # 是否为锁定技
        self.trigger_phase = None  # 触发阶段
        self.trigger_events = []  # 触发事件列表
        self.usage_limit = None  # 使用次数限制
        self.current_usage = 0  # 当前使用次数
    
    def can_trigger(self, game, player, context=None, **kwargs):
        """检查技能是否可以触发"""
        # 检查使用次数限制
        if self.usage_limit and self.current_usage >= self.usage_limit:
            return False
        
        # 检查玩家状态
        if not self.check_player_condition(player):
            return False
        
        # 检查游戏状态
        if not self.check_game_condition(game):
            return False
        
        # 检查特定条件
        return self.check_specific_condition(game, player, context, **kwargs)
    
    def execute(self, game, player, **kwargs):
        """执行技能效果"""
        if not self.can_trigger(game, player, **kwargs):
            return False
        
        # 记录使用次数
        self.current_usage += 1
        
        # 执行技能效果
        result = self.perform_skill_effect(game, player, **kwargs)
        
        # 触发技能使用事件
        self.on_skill_used(game, player, result)
        
        return result
    
    def check_player_condition(self, player):
        """检查玩家条件"""
        return True
    
    def check_game_condition(self, game):
        """检查游戏条件"""
        return True
    
    def check_specific_condition(self, game, player, context=None, **kwargs):
        """检查特定条件（子类重写）"""
        return True
    
    def perform_skill_effect(self, game, player, **kwargs):
        """执行技能效果（子类重写）"""
        return True
    
    def on_skill_used(self, game, player, result):
        """技能使用后的回调"""
        print(f"{player.character.name} 发动技能【{self.name}】")
    
    def reset_usage(self):
        """重置使用次数（通常在回合结束时调用）"""
        self.current_usage = 0

class OptimizedJianXiong(EnhancedSkill):
    """优化的奸雄技能示例"""
    
    def __init__(self):
        super().__init__("奸雄", "当你受到伤害后，你可以获得对你造成伤害的牌")
        self.trigger_events = ['damage_received']
    
    def check_specific_condition(self, game, player, context=None, **kwargs):
        """检查是否有造成伤害的牌可以获得"""
        damage_card = kwargs.get('damage_card')
        return damage_card is not None
    
    def perform_skill_effect(self, game, player, **kwargs):
        """获得造成伤害的牌"""
        damage_card = kwargs.get('damage_card')
        if damage_card:
            player.hand_cards.append(damage_card)
            print(f"{player.character.name} 通过奸雄获得了 {damage_card}")
            return True
        return False

class OptimizedGuanXing(EnhancedSkill):
    """优化的观星技能示例"""
    
    def __init__(self):
        super().__init__("观星", "准备阶段，你可以观看牌堆顶的X张牌，然后将之以任意顺序置于牌堆顶或牌堆底")
        self.trigger_phase = 'prepare'
        self.usage_limit = 1  # 每回合限一次
    
    def check_specific_condition(self, game, player, context=None, **kwargs):
        """检查牌堆是否有足够的牌"""
        return len(game.deck) >= 2
    
    def perform_skill_effect(self, game, player, **kwargs):
        """观星效果"""
        # 观看牌堆顶的牌
        cards_to_view = min(2, len(game.deck))
        viewed_cards = game.deck.draw(cards_to_view)
        
        print(f"{player.character.name} 观星查看了 {cards_to_view} 张牌")
        
        # 这里可以实现玩家选择重新排列的逻辑
        # 目前简化为直接放回牌堆顶
        game.deck.cards = viewed_cards + game.deck.cards
        
        return True

class GamePhaseManager:
    """游戏阶段管理器示例"""
    
    def __init__(self, skill_manager):
        self.skill_manager = skill_manager
        self.current_phase = None
        self.current_player = None
    
    def execute_phase(self, game, player, phase):
        """执行游戏阶段"""
        self.current_phase = phase
        self.current_player = player
        
        print(f"\n=== {player.character.name} 的 {phase} 阶段 ===")
        
        # 执行阶段开始事件
        self.skill_manager.execute_trigger_skills(game, player, f'{phase}_start')
        
        # 执行阶段技能
        executed_skills = self.skill_manager.execute_phase_skills(game, player, phase)
        
        # 执行阶段主要逻辑
        self.execute_phase_main_logic(game, player, phase)
        
        # 执行阶段结束事件
        self.skill_manager.execute_trigger_skills(game, player, f'{phase}_end')
        
        return executed_skills
    
    def execute_phase_main_logic(self, game, player, phase):
        """执行阶段主要逻辑"""
        if phase == 'prepare':
            print("准备阶段：重置状态，执行准备阶段技能")
        elif phase == 'draw':
            print("摸牌阶段：摸2张牌")
            for _ in range(2):
                card = game.deck.draw_card()
                if card:
                    player.hand_cards.append(card)
        elif phase == 'play':
            print("出牌阶段：可以使用手牌")
        elif phase == 'discard':
            print("弃牌阶段：弃置多余手牌")
        elif phase == 'end':
            print("结束阶段：回合结束处理")
            # 重置技能使用次数
            for skill in self.skill_manager.skills.values():
                if hasattr(skill, 'reset_usage'):
                    skill.reset_usage()

def demonstrate_optimizations():
    """演示优化方案"""
    print("三国杀技能优化方案演示")
    print("=" * 50)
    
    # 创建优化的技能管理器
    skill_manager = OptimizedSkillManager()
    
    # 注册优化的技能
    jianxiong = OptimizedJianXiong()
    guanxing = OptimizedGuanXing()
    
    skill_manager.register_skill(jianxiong)
    skill_manager.register_skill(guanxing)
    
    print(f"已注册技能: {list(skill_manager.skills.keys())}")
    print(f"准备阶段技能: {[s.name for s in skill_manager.get_phase_skills('prepare')]}")
    print(f"伤害接收触发技能: {[s.name for s in skill_manager.get_trigger_skills('damage_received')]}")
    
    # 创建游戏环境
    event_manager = EventManager()
    game = Game(event_manager)
    
    # 创建测试牌堆
    test_cards = []
    for i in range(20):
        test_cards.append(Card(name="测试牌", type=CardType.BASIC, suit="红桃", rank=i%13+1))
    game.deck.cards = test_cards
    
    # 创建玩家
    caocao = CharacterFactory.create_character("曹操")
    caocao_player = Player(caocao)
    
    zhugeliang = CharacterFactory.create_character("诸葛亮")
    zhugeliang_player = Player(zhugeliang)
    
    # 创建阶段管理器
    phase_manager = GamePhaseManager(skill_manager)
    
    # 演示阶段执行
    print("\n=== 阶段执行演示 ===")
    phases = ['prepare', 'draw', 'play', 'discard', 'end']
    
    for phase in phases:
        if phase == 'prepare':
            phase_manager.execute_phase(game, zhugeliang_player, phase)
        else:
            phase_manager.execute_phase(game, caocao_player, phase)
    
    # 演示事件触发
    print("\n=== 事件触发演示 ===")
    damage_card = Card(name="杀", type=CardType.BASIC, suit="黑桃", rank=7)
    skill_manager.execute_trigger_skills(game, caocao_player, 'damage_received', damage_card=damage_card)
    
    print(f"曹操手牌数: {len(caocao_player.hand_cards)}")

def print_optimization_recommendations():
    """打印优化建议"""
    print("\n" + "=" * 50)
    print("技能系统优化建议")
    print("=" * 50)
    
    recommendations = [
        "1. 实现统一的技能基类，包含触发条件、执行逻辑、使用限制等",
        "2. 建立完善的事件系统，支持技能对各种游戏事件的响应",
        "3. 优化技能管理器，支持按阶段和事件类型分类管理技能",
        "4. 实现技能的优先级系统，处理多个技能同时触发的情况",
        "5. 添加技能使用次数限制和重置机制",
        "6. 实现技能的AI决策逻辑或玩家选择界面",
        "7. 建立技能效果的动画和提示系统",
        "8. 实现技能的组合效果和相互作用",
        "9. 添加技能使用的日志记录和统计功能",
        "10. 优化技能与游戏流程的集成，确保游戏逻辑的一致性"
    ]
    
    for rec in recommendations:
        print(rec)
    
    print("\n实现这些优化将大大提升游戏的可玩性和稳定性！")

def main():
    """主函数"""
    try:
        demonstrate_optimizations()
        print_optimization_recommendations()
        
    except Exception as e:
        print(f"演示过程中出现错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()