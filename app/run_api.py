"""
三国杀1v1 FastAPI应用启动脚本
"""
import uvicorn
import sys
import os

# 将项目根目录添加到Python路径中
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)