"""
自动化游戏包装器 - 用于AI训练
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import random
from typing import List, Dict, Optional, Any
from app.core.base.game import Game
from app.models.player import Player
from app.models.character import CharacterFactory
from app.models.card import Card

class AutomatedGame(Game):
    """自动化游戏类，用于AI训练，避免用户交互"""
    
    def __init__(self, event_manager, ai_player_index=0):
        super().__init__(event_manager)
        self.ai_player_index = ai_player_index  # AI控制的玩家索引
        self.auto_mode = True  # 自动模式标志
        self.pending_action = None  # 待执行的AI动作
        
    def get_current_player(self) -> Player:
        """获取当前玩家"""
        if self.players and len(self.players) > self.current_player_index:
            return self.players[self.current_player_index]
        return None
    
    def is_ai_turn(self) -> bool:
        """判断是否是AI的回合"""
        return self.current_player_index == self.ai_player_index
    
    def set_ai_action(self, action_type: str, action_data: Any = None):
        """设置AI要执行的动作"""
        self.pending_action = {
            'type': action_type,
            'data': action_data
        }
    
    def play_phase(self, player, test_mode=False):
        """重写出牌阶段，支持AI自动决策"""
        if not self.auto_mode or not self.is_ai_turn():
            # 非AI玩家或非自动模式，使用原始逻辑
            return super().play_phase(player, test_mode=True)
        
        # AI玩家的自动出牌逻辑
        while True:
            if self.pending_action:
                action = self.pending_action
                self.pending_action = None
                
                if action['type'] == 'pass':
                    # 结束出牌阶段
                    break
                elif action['type'] == 'play_card':
                    card_index = action['data']
                    if 0 <= card_index < len(player.hand_cards):
                        card = player.hand_cards[card_index]
                        self._auto_play_card(player, card)
                elif action['type'] == 'equip':
                    card_index = action['data']
                    if 0 <= card_index < len(player.hand_cards):
                        card = player.hand_cards[card_index]
                        self._auto_equip_card(player, card)
            else:
                # 没有待执行动作，结束出牌阶段
                break
    
    def _auto_play_card(self, player: Player, card: Card) -> bool:
        """自动打出卡牌"""
        try:
            if card.name == "杀":
                # 自动选择目标
                target = self._auto_select_target(player)
                if target:
                    return self._execute_sha_card(player, card, target)
            elif card.name == "桃":
                # 自动使用桃
                if player.hp < player.character.max_hp:
                    player.hp = min(player.hp + 1, player.character.max_hp)
                    player.hand_cards.remove(card)
                    self.discard_pile.append(card)
                    return True
            elif card.card_type == "装备牌":
                return self._auto_equip_card(player, card)
            else:
                # 其他卡牌的简化处理
                player.hand_cards.remove(card)
                self.discard_pile.append(card)
                return True
        except Exception as e:
            print(f"自动打牌错误: {e}")
            return False
        
        return False
    
    def _auto_equip_card(self, player: Player, card: Card) -> bool:
        """自动装备卡牌"""
        try:
            if card.card_type == "装备牌":
                # 简化的装备逻辑
                if card.sub_type == "武器牌":
                    if player.weapon:
                        self.discard_pile.append(player.weapon)
                    player.weapon = card
                elif card.sub_type == "防具牌":
                    if player.armor:
                        self.discard_pile.append(player.armor)
                    player.armor = card
                
                player.hand_cards.remove(card)
                return True
        except Exception as e:
            print(f"自动装备错误: {e}")
            return False
        
        return False
    
    def _auto_select_target(self, player: Player) -> Optional[Player]:
        """自动选择目标"""
        # 选择除自己外的第一个存活玩家
        for p in self.players:
            if p != player and p.hp > 0:
                return p
        return None
    
    def _execute_sha_card(self, attacker: Player, card: Card, target: Player) -> bool:
        """执行杀卡牌"""
        try:
            # 简化的杀卡牌逻辑
            print(f"{attacker.character.name} 对 {target.character.name} 使用了杀")
            
            # 检查目标是否有闪
            has_shan = any(c.name == "闪" for c in target.hand_cards)
            
            if has_shan and random.random() < 0.7:  # 70%概率使用闪
                # 自动使用闪
                shan_card = next(c for c in target.hand_cards if c.name == "闪")
                target.hand_cards.remove(shan_card)
                self.discard_pile.append(shan_card)
                print(f"{target.character.name} 使用了闪")
            else:
                # 造成伤害
                damage = 1
                if attacker.weapon and attacker.weapon.name in ["青龙偃月刀", "方天画戟"]:
                    damage = 2
                
                target.hp = max(0, target.hp - damage)
                print(f"{target.character.name} 受到 {damage} 点伤害，剩余血量: {target.hp}")
            
            # 移除使用的杀
            attacker.hand_cards.remove(card)
            self.discard_pile.append(card)
            return True
            
        except Exception as e:
            print(f"执行杀卡牌错误: {e}")
            return False
    
    def select_target(self, player, prompt="选择目标玩家", test_mode=False):
        """重写目标选择，AI模式下自动选择"""
        if self.auto_mode and self.is_ai_turn():
            return self._auto_select_target(player)
        else:
            # 非AI玩家，随机选择或使用默认逻辑
            return self._auto_select_target(player)
    
    def discard_phase(self, player, test_mode=False):
        """重写弃牌阶段，AI模式下自动弃牌"""
        if not self.auto_mode or not self.is_ai_turn():
            return super().discard_phase(player, test_mode=True)
        
        # AI自动弃牌逻辑
        max_cards = player.hp
        while len(player.hand_cards) > max_cards:
            # 简单策略：弃掉第一张牌
            if player.hand_cards:
                discarded_card = player.hand_cards.pop(0)
                self.discard_pile.append(discarded_card)
                print(f"{player.character.name} 弃掉了 {discarded_card.name}")
    
    def handle_response(self, player, card, test_mode=False):
        """重写响应处理，AI模式下自动响应"""
        if self.auto_mode:
            # 简化的自动响应逻辑
            return True
        else:
            return super().handle_response(player, card, test_mode=True)
    
    def auto_step(self):
        """执行一个自动化游戏步骤"""
        if not self.auto_mode:
            return
            
        current_player = self.get_current_player()
        if not current_player:
            return
            
        # 如果是AI回合且有待执行动作，执行动作
        if self.is_ai_turn() and self.pending_action:
            action = self.pending_action
            self.pending_action = None  # 清除待执行动作
            
            if action['type'] == 'pass':
                self.end_turn()
            elif action['type'] == 'play_card':
                card_index = action['data']
                if 0 <= card_index < len(current_player.hand_cards):
                    card = current_player.hand_cards[card_index]
                    self._auto_play_card(current_player, card)
            elif action['type'] == 'equip':
                card_index = action['data']
                if 0 <= card_index < len(current_player.hand_cards):
                    card = current_player.hand_cards[card_index]
                    self._auto_equip_card(current_player, card)
        else:
            # 非AI玩家的自动行为（简单AI）
            if not self.is_ai_turn():
                self._simple_ai_turn(current_player)
    
    def _simple_ai_turn(self, player: Player):
        """简单AI的回合逻辑"""
        # 简单策略：随机出一张牌或跳过
        if player.hand_cards and random.random() > 0.3:
            card = random.choice(player.hand_cards)
            if card.card_type == "装备牌":
                self._auto_equip_card(player, card)
            else:
                self._auto_play_card(player, card)
        else:
            self.end_turn()
    
    def end_turn(self):
        """结束当前玩家回合"""
        # 直接实现回合切换逻辑，不调用super()
        self.current_player_index = (self.current_player_index + 1) % len(self.players)
        self.current_player = self.players[self.current_player_index] if self.players else None
        # 清除待执行动作
        self.pending_action = None
    
    def game_loop(self, test_mode=True):
        """重写游戏循环，支持自动化"""
        max_turns = 100  # 防止无限循环
        turn_count = 0
        
        while not self.is_game_over() and turn_count < max_turns:
            current_player = self.get_current_player()
            if not current_player or current_player.hp <= 0:
                self.end_turn()
                continue
            
            print(f"\n=== {current_player.character.name} 的回合 ===")
            
            # 判定阶段
            self.judgment_phase()
            
            # 摸牌阶段
            self.draw_phase(current_player)
            
            # 出牌阶段
            self.play_phase(current_player, test_mode=True)
            
            # 弃牌阶段
            self.discard_phase(current_player, test_mode=True)
            
            # 结束回合
            self.end_turn()
            turn_count += 1
        
        # 游戏结束
        self.end_game()

if __name__ == "__main__":
    # 测试自动化游戏
    class SimpleEventManager:
        def __init__(self):
            self.events = []
        
        def emit(self, event, data=None):
            self.events.append((event, data))
        
        def trigger(self, event, data=None):
            self.emit(event, data)
        
        def clear(self):
            self.events.clear()
    
    event_manager = SimpleEventManager()
    game = AutomatedGame(event_manager, ai_player_index=0)
    
    # 添加玩家
    cao_cao = CharacterFactory.create_character("曹操")
    liu_bei = CharacterFactory.create_character("刘备")
    
    game.add_player(Player(cao_cao))
    game.add_player(Player(liu_bei))
    
    # 开始游戏
    game.start_game()
    print("自动化游戏测试完成")