# 三国杀卡牌游戏架构设计文档

## 1. 项目概述

### 1.1 项目背景
本项目旨在开发一个完整的三国杀卡牌游戏，包含命令行版本和Web API版本。游戏将实现三国杀的核心玩法，包括武将技能、卡牌系统、回合制对战等。

### 1.2 项目目标
- 实现一个功能完整的三国杀1v1对战游戏
- 提供命令行界面和Web API两种交互方式
- 支持多种武将和技能
- 具备良好的扩展性，便于后续添加新功能

### 1.3 技术栈
- 编程语言：Python 3.x
- Web框架：FastAPI
- 依赖管理：requirements.txt

## 2. 系统架构

### 2.1 整体架构
```
sanguosha/
├── app/                    # 核心应用代码
│   ├── api/               # Web API接口
│   ├── core/              # 核心游戏引擎
│   ├── data/              # 游戏数据文件
│   ├── models/            # 游戏模型类
│   ├── main.py           # FastAPI应用入口
│   ├── run_api.py        # API启动脚本
│   └── run_game.py       # 命令行游戏启动脚本
├── images/               # 游戏图片资源
├── tests/                # 测试文件
├── requirements.txt      # 项目依赖
└── README.md            # 项目说明文档
```

### 2.2 模块划分

#### 2.2.1 核心游戏模块 (app/core)
- **game_engine.py**: 游戏引擎，负责游戏的创建、管理和状态维护

#### 2.2.2 游戏模型模块 (app/models)
- **game.py**: 游戏主逻辑类
- **character.py**: 武将类和武将工厂
- **deck.py**: 牌堆管理类
- **action.py**: 动作基类和具体动作实现
- **skills.py**: 技能系统实现
- **player.py**: 玩家类

#### 2.2.3 API接口模块 (app/api)
- **game_api.py**: 游戏相关的API接口

#### 2.2.4 数据文件 (app/data)
- **JSON文件**: 存储游戏状态、图片标注等数据

## 3. 核心类设计

### 3.1 GameEngine (游戏引擎)
负责游戏的创建、管理和状态维护

**主要方法**:
- `create_game(player1_character, player2_character)`: 创建新游戏
- `get_game(game_id)`: 获取游戏实例
- `perform_action(game_id, action)`: 执行玩家动作
- `get_game_status(game_id)`: 获取游戏状态

### 3.2 Game (游戏主逻辑)
实现游戏的核心逻辑，包括回合流程、胜负判断等

**主要方法**:
- `add_player(character)`: 添加玩家
- `start_game()`: 开始游戏
- `play_phase(player)`: 出牌阶段
- `judgment_phase(player)`: 判定阶段

### 3.3 Character (武将类)
实现武将的属性和技能

**主要方法**:
- `has_skill(skill_name)`: 检查武将是否拥有指定技能
- `use_skill(skill_name, game, player, target)`: 使用技能

### 3.4 Deck (牌堆)
管理游戏的牌堆，包括摸牌、弃牌等操作

**主要方法**:
- `initialize_deck()`: 初始化牌堆
- `draw_card(count)`: 摸牌
- `discard_card(card)`: 弃牌

### 3.5 Action (动作基类)
所有动作的基类，包括卡牌动作和技能动作

## 4. API设计

### 4.1 创建游戏
- **URL**: POST /api/v1/game/create
- **参数**: player1_character, player2_character
- **返回**: game_id

### 4.2 执行动作
- **URL**: POST /api/v1/game/{game_id}/action
- **参数**: action (动作类型和参数)
- **返回**: 执行结果

### 4.3 获取游戏状态
- **URL**: GET /api/v1/game/{game_id}/status
- **参数**: game_id
- **返回**: 游戏当前状态

## 5. 开发任务分配

### 5.1 游戏规则开发 (Agent 1)
**工作目录**: /Users/sunyi/WorkSpace/sanguosha/app/core
**任务**:
1. 完善GameEngine类的功能
2. 实现游戏的完整回合流程
3. 实现胜负判断逻辑
4. 编写单元测试

### 5.2 游戏角色开发 (Agent 2)
**工作目录**: /Users/sunyi/WorkSpace/sanguosha/app/models
**任务**:
1. 扩展武将类，添加更多武将和技能
2. 实现武将技能的具体效果
3. 平衡武将技能强度
4. 编写单元测试

### 5.3 卡牌系统开发 (Agent 3)
**工作目录**: /Users/sunyi/WorkSpace/sanguosha/app/models
**任务**:
1. 扩展卡牌类型，添加更多锦囊牌
2. 实现卡牌的具体效果
3. 平衡卡牌强度
4. 编写单元测试

### 5.4 API接口开发 (Agent 4)
**工作目录**: /Users/sunyi/WorkSpace/sanguosha/app/api
**任务**:
1. 扩展game_api.py，添加更多API接口
2. 实现WebSocket支持，用于实时通信
3. 添加API文档
4. 编写API测试

### 5.5 命令行界面开发 (Agent 5)
**工作目录**: /Users/sunyi/WorkSpace/sanguosha/app
**任务**:
1. 改进run_game.py，提供更好的用户交互体验
2. 添加游戏设置选项
3. 实现游戏回放功能
4. 编写使用文档

## 6. 测试计划

### 6.1 单元测试
每个模块都需要编写单元测试，确保功能正确性

### 6.2 集成测试
测试各模块之间的协作是否正常

### 6.3 性能测试
测试游戏在高并发情况下的性能表现

## 7. 部署方案

### 7.1 开发环境
- 本地运行：python app/run_game.py
- API服务：python app/run_api.py

### 7.2 生产环境
- 使用Docker容器化部署
- 使用Nginx作为反向代理
- 使用Gunicorn作为WSGI服务器