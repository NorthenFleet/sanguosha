# 三国杀网页版

基于React + Flask的三国杀网页小游戏，支持1v1对战。

## 功能特性

- 🎮 经典三国杀1v1对战
- 🎨 现代化美观界面
- 📱 响应式设计
- ⚡ 实时游戏状态更新
- 🃏 完整的卡牌系统

## 技术栈

### 后端
- Flask (Python Web框架)
- Flask-CORS (跨域支持)
- 原生三国杀游戏逻辑

### 前端
- React 18
- Vite (构建工具)
- Tailwind CSS (样式框架)
- Axios (HTTP客户端)

## 快速开始

### 前提条件
- Python 3.8+
- Node.js 16+
- npm 或 yarn

### 安装和运行

1. 一键启动（推荐）
```bash
cd web
start.bat
```

2. 手动启动

后端：
```bash
cd web
pip install -r requirements.txt
python app.py
```

前端：
```bash
cd web/frontend
npm install
npm run dev
```

3. 访问游戏
打开浏览器访问: http://localhost:3000

## 游戏玩法

1. 选择两名武将开始游戏
2. 轮流进行回合
3. 每个回合包含：判定阶段、摸牌阶段、出牌阶段、弃牌阶段
4. 使用卡牌攻击对手或回复体力
5. 对手可以响应某些卡牌
6. 将对手体力降至0获胜

## 项目结构

```
web/
├── app.py                 # Flask后端服务器
├── requirements.txt       # Python依赖
├── start.bat             # 一键启动脚本
├── frontend/             # React前端
│   ├── src/
│   │   ├── components/   # React组件
│   │   ├── App.jsx       # 主应用组件
│   │   └── index.css     # 样式文件
│   ├── package.json       # Node.js依赖
│   └── vite.config.js    # Vite配置
└── README.md
```

## API接口

- `GET /api/characters` - 获取可选武将列表
- `POST /api/game/create` - 创建新游戏
- `GET /api/game/{id}/status` - 获取游戏状态
- `POST /api/game/{id}/play` - 出牌
- `POST /api/game/{id}/end_turn` - 结束回合

## 开发说明

游戏逻辑基于原有的Python三国杀代码，通过Flask提供RESTful API接口，React前端调用这些接口实现游戏交互。