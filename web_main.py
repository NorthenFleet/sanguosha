#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Web 入口：FastAPI + 静态页面
 - 静态托管 /display 下的网页
 - 集成基础游戏API（复用 app/api/game_api.py 的 router）

运行：
  uvicorn app.web_main:app --host 0.0.0.0 --port 8001 --reload
"""

import os
import sys
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

# 确保项目根目录在路径中
ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

# 初始化路径（兼容项目内的相对导入）
from app.core.base.path_utils import setup_paths
setup_paths()

app = FastAPI(title="Sanguosha Web Entry", version="0.1.0")

# CORS（如需从不同源访问）
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 静态托管 display 目录
display_dir = ROOT / "display"
app.mount("/display", StaticFiles(directory=str(display_dir), html=True), name="display")

# 集成游戏API路由
try:
    from app.api.game_api import router as game_router
    app.include_router(game_router)
except Exception as e:
    # 保持入口可启动，即使API暂不可用
    import logging
    logging.getLogger(__name__).warning(f"Game API router unavailable: {e}")

# 备用：直接在入口提供基础API（/api 前缀），避免依赖缺失
from typing import Optional, Any, Dict
try:
    from pydantic import BaseModel
    from app.core.base.game_engine import GameEngine

    class GameCreate(BaseModel):
        player1_character: str
        player2_character: str

    class PlayerAction(BaseModel):
        type: Optional[str] = None
        payload: Optional[Dict[str, Any]] = None

    engine = GameEngine()

    @app.post("/api/create")
    async def api_create_game(req: GameCreate):
        game_id = engine.create_game(req.player1_character, req.player2_character)
        return {"game_id": game_id, "message": "游戏创建成功"}

    @app.get("/api/{game_id}/status")
    async def api_status(game_id: str):
        return engine.get_game_status(game_id)

    @app.post("/api/{game_id}/action")
    async def api_action(game_id: str, action: PlayerAction):
        return engine.perform_action(game_id, action.dict())
except Exception as e:
    import logging
    logging.getLogger(__name__).warning(f"Fallback API unavailable: {e}")

@app.get("/")
def root():
    return {"message": "Sanguosha web entry running", "docs": "/docs", "ui": "/display/index.html"}