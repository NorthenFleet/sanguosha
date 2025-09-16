#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
三国杀游戏集成优化方案
展示技能系统与游戏流程的深度集成
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.models.character import CharacterFactory
from app.models.player import Player
from app.core.game import Game
from app.models.card import Card
from app.models.enums import CardType
from app.core.event_system import EventManager

class IntegratedEventSystem:
    """集成的事件系统"""
    
    def __init__(self):
        self.listeners = {}
        self.event_history = []
        self.event_stack = []  # 事件栈，处理嵌套事件
    
    def register_listener(self, event_type, callback, priority=0):
        """注册事件监听器，支持优先级"""
        if event_type not in self.listeners:
            self.listeners[event_type] = []
        
        self.listeners[event_type].append({
            'callback': callback,
            'priority': priority
        })
        
        # 按优先级排序
        self.listeners[event_type].sort(key=lambda x: x['priority'], reverse=True)
    
    def emit_event(self, event_type, **kwargs):
        """触发事件"""
        event = {
            'type': event_type,
            'data': kwargs,
            'timestamp': len(self.event_history),
            'cancelled': False
        }
        
        self.event_history.append(event)
        self.event_stack.append(event)
        
        print(f"触发事件: {event_type}")
        
        if event_type in self.listeners:
            for listener in self.listeners[event_type]:
                if not event['cancelled']:
                    try:
                        result = listener['callback'](event, **kwargs)
                        if result == 'cancel':
                            event['cancelled'] = True
                            print(f"事件 {event_type} 被取消")
                    except Exception as e:
                        print(f"事件处理器执行错误: {e}")
        
        self.event_stack.pop()
        return event
    
    def get_current_event(self):
        """获取当前正在处理的事件"""
        return self.event_stack[-1] if self.event_stack else None

class IntegratedSkillSystem:
    """集成的技能系统"""
    
    def __init__(self, event_system):
        self.event_system = event_system
        self.skills = {}
        self.player_skills = {}  # 玩家技能映射
        self.skill_states = {}  # 技能状态跟踪
        
        # 注册核心事件监听器
        self._register_core_listeners()
    
    def _register_core_listeners(self):
        """注册核心事件监听器"""
        self.event_system.register_listener('turn_start', self._on_turn_start, priority=100)
        self.event_system.register_listener('turn_end', self._on_turn_end, priority=100)
        self.event_system.register_listener('phase_start', self._on_phase_start, priority=90)
        self.event_system.register_listener('phase_end', self._on_phase_end, priority=90)
        self.event_system.register_listener('card_used', self._on_card_used, priority=80)
        self.event_system.register_listener('damage_dealt', self._on_damage_dealt, priority=80)
        self.event_system.register_listener('damage_received', self._on_damage_received, priority=80)
    
    def register_player_skill(self, player, skill):
        """为玩家注册技能"""
        if player not in self.player_skills:
            self.player_skills[player] = []
        
        self.player_skills[player].append(skill)
        self.skills[skill.name] = skill
        
        # 初始化技能状态
        skill_key = f"{player.character.name}_{skill.name}"
        self.skill_states[skill_key] = {
            'usage_count': 0,
            'last_used_turn': -1,
            'active': True
        }
        
        print(f"为 {player.character.name} 注册技能: {skill.name}")
    
    def get_player_skills(self, player, skill_type=None):
        """获取玩家的技能"""
        skills = self.player_skills.get(player, [])
        if skill_type:
            skills = [s for s in skills if hasattr(s, 'skill_type') and s.skill_type == skill_type]
        return skills
    
    def can_use_skill(self, player, skill, context=None):
        """检查是否可以使用技能"""
        skill_key = f"{player.character.name}_{skill.name}"
        state = self.skill_states.get(skill_key, {})
        
        # 检查技能是否激活
        if not state.get('active', True):
            return False
        
        # 检查使用次数限制
        if hasattr(skill, 'max_usage_per_turn'):
            current_turn = context.get('current_turn', 0) if context else 0
            if (state.get('last_used_turn') == current_turn and 
                state.get('usage_count', 0) >= skill.max_usage_per_turn):
                return False
        
        # 检查技能自身条件
        return skill.can_trigger(player, context)
    
    def use_skill(self, player, skill, context=None):
        """使用技能"""
        if not self.can_use_skill(player, skill, context):
            return False
        
        skill_key = f"{player.character.name}_{skill.name}"
        state = self.skill_states[skill_key]
        
        # 更新使用状态
        current_turn = context.get('current_turn', 0) if context else 0
        if state.get('last_used_turn') != current_turn:
            state['usage_count'] = 0
        
        state['usage_count'] += 1
        state['last_used_turn'] = current_turn
        
        # 触发技能使用事件
        self.event_system.emit_event('skill_used', 
                                   player=player, 
                                   skill=skill, 
                                   context=context)
        
        # 执行技能效果
        result = skill.execute(player, context)
        
        # 触发技能执行完成事件
        self.event_system.emit_event('skill_executed', 
                                   player=player, 
                                   skill=skill, 
                                   result=result, 
                                   context=context)
        
        return result
    
    def _on_turn_start(self, event, **kwargs):
        """回合开始处理"""
        player = kwargs.get('player')
        if player:
            # 重置回合技能使用次数
            for skill in self.get_player_skills(player):
                skill_key = f"{player.character.name}_{skill.name}"
                if skill_key in self.skill_states:
                    self.skill_states[skill_key]['usage_count'] = 0
    
    def _on_turn_end(self, event, **kwargs):
        """回合结束处理"""
        player = kwargs.get('player')
        if player:
            # 处理回合结束技能
            turn_end_skills = [s for s in self.get_player_skills(player) 
                             if hasattr(s, 'trigger_timing') and 'turn_end' in s.trigger_timing]
            
            for skill in turn_end_skills:
                if self.can_use_skill(player, skill, kwargs):
                    self.use_skill(player, skill, kwargs)
    
    def _on_phase_start(self, event, **kwargs):
        """阶段开始处理"""
        player = kwargs.get('player')
        phase = kwargs.get('phase')
        
        if player and phase:
            # 处理阶段开始技能
            phase_skills = [s for s in self.get_player_skills(player) 
                          if hasattr(s, 'trigger_timing') and f'{phase}_start' in s.trigger_timing]
            
            for skill in phase_skills:
                if self.can_use_skill(player, skill, kwargs):
                    self.use_skill(player, skill, kwargs)
    
    def _on_phase_end(self, event, **kwargs):
        """阶段结束处理"""
        player = kwargs.get('player')
        phase = kwargs.get('phase')
        
        if player and phase:
            # 处理阶段结束技能
            phase_skills = [s for s in self.get_player_skills(player) 
                          if hasattr(s, 'trigger_timing') and f'{phase}_end' in s.trigger_timing]
            
            for skill in phase_skills:
                if self.can_use_skill(player, skill, kwargs):
                    self.use_skill(player, skill, kwargs)
    
    def _on_card_used(self, event, **kwargs):
        """卡牌使用处理"""
        player = kwargs.get('player')
        card = kwargs.get('card')
        
        if player and card:
            # 处理卡牌使用触发的技能
            card_skills = [s for s in self.get_player_skills(player) 
                         if hasattr(s, 'trigger_timing') and 'card_used' in s.trigger_timing]
            
            for skill in card_skills:
                if self.can_use_skill(player, skill, kwargs):
                    self.use_skill(player, skill, kwargs)
    
    def _on_damage_dealt(self, event, **kwargs):
        """造成伤害处理"""
        player = kwargs.get('source')
        
        if player:
            damage_skills = [s for s in self.get_player_skills(player) 
                           if hasattr(s, 'trigger_timing') and 'damage_dealt' in s.trigger_timing]
            
            for skill in damage_skills:
                if self.can_use_skill(player, skill, kwargs):
                    self.use_skill(player, skill, kwargs)
    
    def _on_damage_received(self, event, **kwargs):
        """受到伤害处理"""
        player = kwargs.get('target')
        
        if player:
            damage_skills = [s for s in self.get_player_skills(player) 
                           if hasattr(s, 'trigger_timing') and 'damage_received' in s.trigger_timing]
            
            for skill in damage_skills:
                if self.can_use_skill(player, skill, kwargs):
                    self.use_skill(player, skill, kwargs)

class IntegratedSkill:
    """集成的技能基类"""
    
    def __init__(self, name, description):
        self.name = name
        self.description = description
        self.trigger_timing = []  # 触发时机列表
        self.skill_type = 'active'  # 技能类型：active, passive, locked
        self.max_usage_per_turn = None  # 每回合最大使用次数
    
    def can_trigger(self, player, context=None):
        """检查技能是否可以触发"""
        return True
    
    def execute(self, player, context=None):
        """执行技能效果"""
        print(f"{player.character.name} 发动技能【{self.name}】")
        return self.perform_effect(player, context)
    
    def perform_effect(self, player, context=None):
        """执行具体效果（子类重写）"""
        return True

class IntegratedJianXiong(IntegratedSkill):
    """集成的奸雄技能"""
    
    def __init__(self):
        super().__init__("奸雄", "当你受到伤害后，你可以获得对你造成伤害的牌")
        self.trigger_timing = ['damage_received']
        self.skill_type = 'passive'
    
    def can_trigger(self, player, context=None):
        """检查是否有造成伤害的牌"""
        if not context:
            return False
        return context.get('damage_card') is not None
    
    def perform_effect(self, player, context=None):
        """获得造成伤害的牌"""
        damage_card = context.get('damage_card')
        if damage_card:
            player.hand_cards.append(damage_card)
            print(f"  → {player.character.name} 获得了 {damage_card}")
            return True
        return False

class IntegratedRenDe(IntegratedSkill):
    """集成的仁德技能"""
    
    def __init__(self):
        super().__init__("仁德", "出牌阶段，你可以将任意张手牌交给其他角色")
        self.trigger_timing = ['play_phase']
        self.skill_type = 'active'
    
    def can_trigger(self, player, context=None):
        """检查是否有手牌可以给出"""
        return len(player.hand_cards) > 0
    
    def perform_effect(self, player, context=None):
        """给出手牌"""
        if len(player.hand_cards) > 0:
            # 简化实现：给出一张手牌
            given_card = player.hand_cards.pop(0)
            print(f"  → {player.character.name} 通过仁德给出了 {given_card}")
            return True
        return False

class IntegratedGameEngine:
    """集成的游戏引擎"""
    
    def __init__(self):
        self.event_system = IntegratedEventSystem()
        self.skill_system = IntegratedSkillSystem(self.event_system)
        self.players = []
        self.current_player_index = 0
        self.current_turn = 0
        self.current_phase = None
    
    def add_player(self, player):
        """添加玩家"""
        self.players.append(player)
        
        # 为玩家注册技能
        character_name = player.character.name
        if character_name == "曹操":
            self.skill_system.register_player_skill(player, IntegratedJianXiong())
        elif character_name == "刘备":
            self.skill_system.register_player_skill(player, IntegratedRenDe())
    
    def get_current_player(self):
        """获取当前玩家"""
        return self.players[self.current_player_index]
    
    def next_player(self):
        """切换到下一个玩家"""
        self.current_player_index = (self.current_player_index + 1) % len(self.players)
        if self.current_player_index == 0:
            self.current_turn += 1
    
    def execute_turn(self, player):
        """执行玩家回合"""
        print(f"\n=== {player.character.name} 的第 {self.current_turn + 1} 回合 ===")
        
        # 触发回合开始事件
        self.event_system.emit_event('turn_start', 
                                   player=player, 
                                   current_turn=self.current_turn)
        
        # 执行各个阶段
        phases = ['prepare', 'draw', 'play', 'discard', 'end']
        for phase in phases:
            self.execute_phase(player, phase)
        
        # 触发回合结束事件
        self.event_system.emit_event('turn_end', 
                                   player=player, 
                                   current_turn=self.current_turn)
    
    def execute_phase(self, player, phase):
        """执行游戏阶段"""
        self.current_phase = phase
        print(f"\n--- {phase.upper()} 阶段 ---")
        
        # 触发阶段开始事件
        context = {
            'player': player,
            'phase': phase,
            'current_turn': self.current_turn
        }
        
        self.event_system.emit_event('phase_start', **context)
        
        # 执行阶段主要逻辑
        self.execute_phase_logic(player, phase, context)
        
        # 触发阶段结束事件
        self.event_system.emit_event('phase_end', **context)
    
    def execute_phase_logic(self, player, phase, context):
        """执行阶段主要逻辑"""
        if phase == 'prepare':
            print("准备阶段：重置状态")
        elif phase == 'draw':
            print("摸牌阶段：摸2张牌")
            # 模拟摸牌
            for i in range(2):
                card = Card(name=f"测试牌{i+1}", type=CardType.BASIC, suit="红桃", rank=i+1)
                player.hand_cards.append(card)
        elif phase == 'play':
            print("出牌阶段：可以使用手牌和技能")
            # 尝试使用主动技能
            active_skills = self.skill_system.get_player_skills(player, 'active')
            for skill in active_skills:
                if self.skill_system.can_use_skill(player, skill, context):
                    self.skill_system.use_skill(player, skill, context)
        elif phase == 'discard':
            print("弃牌阶段：弃置多余手牌")
        elif phase == 'end':
            print("结束阶段：回合结束处理")
    
    def simulate_damage(self, source, target, damage_card=None):
        """模拟伤害"""
        print(f"\n{source.character.name} 对 {target.character.name} 造成伤害")
        
        # 触发造成伤害事件
        self.event_system.emit_event('damage_dealt', 
                                   source=source, 
                                   target=target, 
                                   damage_card=damage_card)
        
        # 触发受到伤害事件
        self.event_system.emit_event('damage_received', 
                                   source=source, 
                                   target=target, 
                                   damage_card=damage_card)

def demonstrate_integration():
    """演示游戏集成"""
    print("三国杀游戏集成优化演示")
    print("=" * 50)
    
    # 创建游戏引擎
    game_engine = IntegratedGameEngine()
    
    # 创建玩家
    caocao = CharacterFactory.create_character("曹操")
    caocao_player = Player(caocao)
    
    liubei = CharacterFactory.create_character("刘备")
    liubei_player = Player(liubei)
    
    # 添加玩家到游戏
    game_engine.add_player(caocao_player)
    game_engine.add_player(liubei_player)
    
    print(f"游戏开始！参与玩家: {[p.character.name for p in game_engine.players]}")
    
    # 执行几个回合
    for turn in range(2):
        current_player = game_engine.get_current_player()
        game_engine.execute_turn(current_player)
        
        # 模拟一些事件
        if turn == 0:
            # 模拟曹操受到伤害
            damage_card = Card(name="杀", type=CardType.BASIC, suit="黑桃", rank=7)
            game_engine.simulate_damage(liubei_player, caocao_player, damage_card)
        
        game_engine.next_player()
    
    print(f"\n曹操最终手牌数: {len(caocao_player.hand_cards)}")
    print(f"刘备最终手牌数: {len(liubei_player.hand_cards)}")

def print_integration_summary():
    """打印集成总结"""
    print("\n" + "=" * 50)
    print("游戏集成优化总结")
    print("=" * 50)
    
    improvements = [
        "✓ 实现了统一的事件系统，支持事件优先级和嵌套处理",
        "✓ 建立了完整的技能生命周期管理",
        "✓ 实现了技能与游戏阶段的深度集成",
        "✓ 添加了技能使用次数和状态跟踪",
        "✓ 支持多种技能触发时机和类型",
        "✓ 实现了事件驱动的游戏逻辑",
        "✓ 提供了可扩展的技能注册机制",
        "✓ 建立了完整的游戏引擎架构"
    ]
    
    for improvement in improvements:
        print(improvement)
    
    print("\n这些优化使得技能系统与游戏核心逻辑完美融合！")

def main():
    """主函数"""
    try:
        demonstrate_integration()
        print_integration_summary()
        
    except Exception as e:
        print(f"演示过程中出现错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()