@echo off
echo 正在启动三国杀网页游戏...
echo.

echo 1. 安装后端依赖...
cd web
pip install -r requirements.txt
if errorlevel 1 (
    echo 后端依赖安装失败，请检查Python环境
    pause
    exit /b 1
)

echo.
echo 2. 安装前端依赖...
cd frontend
npm install
if errorlevel 1 (
    echo 前端依赖安装失败，请检查Node.js环境
    pause
    exit /b 1
)

echo.
echo 3. 启动后端服务器...
start "后端服务器" python ../app.py

echo.
echo 4. 启动前端开发服务器...
start "前端服务器" npm run dev

echo.
echo 等待服务器启动...
timeout /t 5

echo.
echo 游戏启动完成！
echo 前端地址: http://localhost:3000
echo 后端API: http://localhost:5000
echo.
pause