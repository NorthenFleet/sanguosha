#!/bin/bash

# 三国杀游戏开发环境启动脚本

echo "正在启动三国杀游戏开发环境..."

# 启动API服务
echo "启动API服务..."
python app/run_api.py &

# 启动命令行游戏
echo "启动命令行游戏..."
python app/run_game.py

echo "开发环境启动完成！"