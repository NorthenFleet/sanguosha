"""
三国杀1v1游戏API数据模型
"""
from pydantic import BaseModel
from typing import List, Optional

class GameCreate(BaseModel):
    """创建游戏请求数据模型"""
    player1_character: str
    player2_character: str

class PlayerAction(BaseModel):
    """玩家动作数据模型"""
    player_id: int
    action_type: str
    target_player_id: Optional[int] = None
    card_name: Optional[str] = None

class PlayerStatus(BaseModel):
    """玩家状态数据模型"""
    player_id: int
    character_name: str
    hp: int
    max_hp: int
    hand_cards_count: int

class GameStatus(BaseModel):
    """游戏状态数据模型"""
    game_id: str
    current_player_id: int
    players: List[PlayerStatus]
    game_phase: str
    game_over: bool
    winner: Optional[int] = None

class GameResponse(BaseModel):
    """游戏响应数据模型"""
    game_id: str
    message: str
