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
        
    def add_player(self, player_or_character):
        """重写添加玩家方法，确保血量正确初始化"""
        super().add_player(player_or_character)
        # 确保玩家血量正确设置为角色的最大血量
        if hasattr(player_or_character, 'character'):
            player = player_or_character
            player.hp = player.character.max_hp
            player.character.hp = player.character.max_hp
        else:
            # 如果传入的是角色，需要创建玩家
            character = player_or_character
            character.hp = character.max_hp
        
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
        if not test_mode:
            print(f"\n=== {player.character.name} 的出牌阶段 ===")
        
        # 重置每回合的杀使用标记
        player.has_used_sha = False
        
        if self.auto_mode and self.is_ai_turn():
            # AI自动出牌
            self._simple_ai_turn(player)
        else:
            # 非AI玩家的出牌逻辑 - 简化为只使用一张牌
            if player.hand_cards:
                # 随机选择一张牌
                card = random.choice(player.hand_cards)
                
                # 如果是杀且已经使用过，选择其他牌
                if card.name == "杀" and player.has_used_sha:
                    other_cards = [c for c in player.hand_cards if c.name != "杀"]
                    if other_cards:
                        card = random.choice(other_cards)
                    else:
                        return  # 没有其他牌可用，结束出牌阶段
                
                self._auto_play_card(player, card)
    
    def _auto_play_card(self, player: Player, card: Card) -> bool:
        """自动打出卡牌"""
        try:
            if card.name == "杀":
                # 检查是否已经使用过杀
                if player.has_used_sha:
                    return False
                
                # 自动选择目标
                target = self._auto_select_target(player)
                if target:
                    success = self._execute_sha_card(player, card, target)
                    if success:
                        player.has_used_sha = True  # 标记已使用杀
                    return success
            elif card.name == "桃":
                # 自动使用桃
                if player.hp < player.character.max_hp:
                    player.hp = min(player.hp + 1, player.character.max_hp)
                    player.hand_cards.remove(card)
                    self.discard_pile.append(card)
                    print(f"{player.character.name} 使用了桃，回复1点体力")
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
            if card.card_type == "装备牌" or card.category == "equipment":
                # 简化的装备逻辑
                if hasattr(card, 'subtype') and card.subtype == "weapon":
                    if player.weapon:
                        self.discard_pile.append(player.weapon)
                    player.weapon = card
                elif hasattr(card, 'subtype') and card.subtype == "armor":
                    if player.armor:
                        self.discard_pile.append(player.armor)
                    player.armor = card
                elif hasattr(card, 'subtype') and card.subtype == "horse":
                    # 处理坐骑装备
                    if not hasattr(player, 'attack_horse'):
                        player.attack_horse = None
                    if not hasattr(player, 'defense_horse'):
                        player.defense_horse = None
                    
                    # 简化处理：所有坐骑都当作进攻马
                    if player.attack_horse:
                        self.discard_pile.append(player.attack_horse)
                    player.attack_horse = card
                
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
                
                # 同时更新player.hp和player.character.hp，确保血量同步
                new_hp = max(0, target.hp - damage)
                target.hp = new_hp
                target.character.hp = new_hp
                print(f"{target.character.name} 受到 {damage} 点伤害，剩余血量: {target.hp} (Character.hp: {target.character.hp})")
            
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
        # AI自动弃牌逻辑
        max_cards = player.hp
        print(f"弃牌阶段：{player.character.name} 当前手牌 {len(player.hand_cards)} 张，血量 {player.hp}，需要弃到 {max_cards} 张")
        
        discard_count = 0
        while len(player.hand_cards) > max_cards and player.hand_cards:
            # 简单策略：优先弃掉杀牌，保留闪和桃
            card_to_discard = None
            
            # 寻找杀牌优先弃掉
            for card in player.hand_cards:
                if card.name == "杀":
                    card_to_discard = card
                    break
            
            # 如果没有杀牌，弃掉第一张牌
            if not card_to_discard and player.hand_cards:
                card_to_discard = player.hand_cards[0]
            
            if card_to_discard:
                player.hand_cards.remove(card_to_discard)
                self.discard_pile.append(card_to_discard)
                discard_count += 1
                print(f"{player.character.name} 弃掉了 {card_to_discard.name}")
                
                # 防止无限循环
                if discard_count > 10:
                    print(f"警告：{player.character.name} 弃牌过多，强制结束弃牌阶段")
                    break
            else:
                break
        
        print(f"弃牌阶段结束：{player.character.name} 剩余手牌 {len(player.hand_cards)} 张")
    
    def handle_response(self, player, card, test_mode=False):
        """重写响应处理，AI模式下自动响应"""
        # 简化的自动响应逻辑
        return True
    
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
    
    def _simple_ai_turn(self, player: Player):
        """简化的AI回合逻辑"""
        # 优先使用装备牌
        equipment_cards = [card for card in player.hand_cards if card.card_type == "装备牌"]
        for card in equipment_cards[:1]:  # 只装备一张
            self._auto_equip_card(player, card)
        
        # 使用一张杀（如果有的话）
        sha_cards = [card for card in player.hand_cards if card.name == "杀"]
        if sha_cards and not player.has_used_sha:
            target = self._auto_select_target(player)
            if target:
                success = self._execute_sha_card(player, sha_cards[0], target)
                if success:
                    player.has_used_sha = True
        
        # 如果血量不满，使用桃
        tao_cards = [card for card in player.hand_cards if card.name == "桃"]
        if tao_cards and player.hp < player.character.max_hp:
            tao_card = tao_cards[0]
            player.hp = min(player.character.max_hp, player.hp + 1)
            player.hand_cards.remove(tao_card)
            self.discard_pile.append(tao_card)
            print(f"{player.character.name} 使用了桃，回复1点体力")
    
    def is_game_over(self):
        """重写游戏结束判定，与训练环境保持一致"""
        # 使用与训练环境相同的逻辑：存活玩家数 <= 1
        alive_players = [p for p in self.players if p.hp > 0]
        return len(alive_players) <= 1
    
    def end_turn(self):
        """结束当前玩家回合"""
        # 直接实现回合切换逻辑，不调用super()
        self.current_player_index = (self.current_player_index + 1) % len(self.players)
        self.current_player = self.players[self.current_player_index] if self.players else None
        # 清除待执行动作
        self.pending_action = None
    
    def game_loop(self, test_mode=True):
        """重写游戏循环，支持自动化"""
        max_turns = 1000  # 增加最大回合数到1000
        turn_count = 0
        
        print(f"游戏开始，玩家数量: {len(self.players)}")
        for i, player in enumerate(self.players):
            print(f"玩家{i+1}: {player.character.name}, 血量: {player.hp}, 手牌: {len(player.hand_cards)}")
        
        while not self.is_game_over() and turn_count < max_turns:
            current_player = self.get_current_player()
            if not current_player:
                print("错误：当前玩家为空")
                break
                
            if current_player.hp <= 0:
                print(f"{current_player.character.name} 已死亡，跳过回合")
                self.end_turn()
                continue
            
            print(f"\n=== 第{turn_count + 1}回合：{current_player.character.name} 的回合 ===")
            print(f"当前血量: {current_player.hp}, 手牌数: {len(current_player.hand_cards)}")
            
            # 判定阶段
            self.judgment_phase()
            
            # 摸牌阶段
            self.draw_phase(current_player)
            print(f"摸牌后手牌数: {len(current_player.hand_cards)}")
            
            # 出牌阶段
            self.play_phase(current_player, test_mode=True)
            
            # 弃牌阶段
            self.discard_phase(current_player, test_mode=True)
            print(f"弃牌后手牌数: {len(current_player.hand_cards)}")
            
            # 检查游戏状态
            alive_players = [p for p in self.players if p.hp > 0]
            print(f"存活玩家数: {len(alive_players)}")
            
            # 结束回合
            self.end_turn()
            turn_count += 1
            
            # 每20回合检查一次游戏状态
            if turn_count % 20 == 0:
                print(f"\n--- 第{turn_count}回合状态检查 ---")
                for i, player in enumerate(self.players):
                    status = "存活" if player.hp > 0 else "死亡"
                    print(f"玩家{i+1} {player.character.name}: {status}, 血量: {player.hp}, 手牌: {len(player.hand_cards)}")
        
        if turn_count >= max_turns:
            print(f"游戏达到最大回合数 {max_turns}，强制结束")
        
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