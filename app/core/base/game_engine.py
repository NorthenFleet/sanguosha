"""
三国杀1v1游戏核心引擎
"""
import uuid
from typing import Dict, Optional
from .game import Game
from ...models.player import Player
from ...models.character import CharacterFactory


class GameEngine:
    """游戏引擎类"""
    
    def __init__(self):
        self.games: Dict[str, Game] = {}
    
    def create_game(self, player1_character: str, player2_character: str) -> str:
        """创建新游戏"""
        # 验证武将选择
        available_characters = ["曹操", "司马懿", "张辽", "夏侯惇", "刘备", "关羽", "张飞", "赵云", 
                             "诸葛亮", "孙权", "周瑜", "甘宁", "吕蒙"]
        
        if player1_character not in available_characters:
            raise ValueError(f"无效的武将选择: {player1_character}")
        
        if player2_character not in available_characters:
            raise ValueError(f"无效的武将选择: {player2_character}")
        
        if player1_character == player2_character:
            raise ValueError("两位玩家不能选择相同的武将")
        
        # 创建游戏实例
        game_id = str(uuid.uuid4())
        from ..events.event_system import EventManager
        event_manager = EventManager()
        game = Game(event_manager)
        
        # 创建玩家
        p1_character = CharacterFactory.create_character(player1_character)
        p2_character = CharacterFactory.create_character(player2_character)
        
        game.add_player(p1_character)
        game.add_player(p2_character)
        
        # 初始化游戏
        game.initialize_deck()
        
        # 设置当前玩家
        game.current_player = game.players[0]
        
        # 初始摸牌
        for player in game.players:
            for _ in range(4):
                card = game.deck.draw_card()
                if card:
                    player.hand_cards.append(card)
        
        self.games[game_id] = game
        return game_id
    
    def get_game(self, game_id: str) -> Optional[Game]:
        """获取游戏实例"""
        return self.games.get(game_id)
    
    def perform_action(self, game_id: str, action):
        """执行玩家动作"""
        game = self.get_game(game_id)
        if not game:
            raise ValueError(f"游戏不存在: {game_id}")
        
        # 这里应该实现具体的动作逻辑
        # 暂时返回成功
        return {"status": "success"}
    
    def get_game_status(self, game_id: str):
        """获取游戏状态"""
        game = self.get_game(game_id)
        if not game:
            raise ValueError(f"游戏不存在: {game_id}")
        
        # 构建游戏状态响应
        players_status = []
        for i, player in enumerate(game.players):
            # 获取手牌详情
            hand_cards = []
            for card in player.hand_cards:
                if hasattr(card, 'name'):
                    hand_cards.append(card.name)
                else:
                    hand_cards.append(str(card))
            
            players_status.append({
                "player_id": i+1,
                "character_name": player.character.name,
                "hp": player.character.hp,
                "max_hp": player.character.max_hp,
                "hand_cards_count": len(player.hand_cards),
                "hand_cards": hand_cards,
                "skills": player.character.skills,
                "weapon": player.weapon.name if player.weapon else None,
                "chained": player.chained
            })
        
        return {
            "game_id": game_id,
            "current_player_id": game.current_player_index + 1,
            "current_phase": game.current_phase,
            "players": players_status,
            "deck_count": len(game.deck.cards)
        }