"""
三国杀1v1游戏API路由
"""
from fastapi import APIRouter, HTTPException
from typing import List
from app.schemas.game_schema import GameCreate, GameResponse, PlayerAction
from app.core.base.game_engine import GameEngine
from app.core.base.path_utils import setup_paths
setup_paths()

router = APIRouter(prefix="/game", tags=["game"])

game_engine = GameEngine()

@router.post("/create", response_model=GameResponse)
async def create_game(game_data: GameCreate):
    """创建新游戏"""
    try:
        game_id = game_engine.create_game(game_data.player1_character, game_data.player2_character)
        return GameResponse(game_id=game_id, message="游戏创建成功")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/{game_id}/action")
async def perform_action(game_id: str, action: PlayerAction):
    """执行玩家动作"""
    try:
        result = game_engine.perform_action(game_id, action)
        return {"message": "动作执行成功", "result": result}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/{game_id}/status")
async def get_game_status(game_id: str):
    """获取游戏状态"""
    try:
        status = game_engine.get_game_status(game_id)
        return status
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))