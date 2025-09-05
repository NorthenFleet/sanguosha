"""
三国杀1v1游戏数据模型
"""
from pydantic import BaseModel
from typing import Optional, List


class GameCreate(BaseModel):
    """创建游戏请求数据模型"""
    player1_character: str
    player2_character: str


class GameResponse(BaseModel):
    """游戏响应数据模型"""
    game_id: str
    message: str


class PlayerAction(BaseModel):
    """玩家动作数据模型"""
    player_id: int
    action_type: str  # "draw", "play", "discard"
    card_index: Optional[int] = None
    target_player_id: Optional[int] = None


class PlayerStatus(BaseModel):
    """玩家状态数据模型"""
    player_id: int
    character_name: str
    hp: int
    max_hp: int
    hand_cards_count: int
    weapon: Optional[str] = None
    chained: bool


class GameStatus(BaseModel):
    """游戏状态数据模型"""
    game_id: str
    current_player_id: int
    current_phase: str
    players: List[PlayerStatus]
    deck_count: int