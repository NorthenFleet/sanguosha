"""
三国杀1v1 FastAPI应用入口
"""
from fastapi import FastAPI
from api import game_api

app = FastAPI(title="三国杀1v1 API", description="三国杀1v1游戏的REST API接口", version="1.0.0")

# 注册API路由
app.include_router(game_api.router, prefix="/api/v1")

@app.get("/")
async def root():
    return {"message": "欢迎来到三国杀1v1游戏API"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}