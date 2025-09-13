# 三国杀1v1游戏设计与开发文档

## 1. 项目概述

### 1.1 项目背景

三国杀是一款非常受欢迎的桌面卡牌游戏，结合了中国三国时期的历史背景和策略性玩法。本项目旨在实现一个简化的三国杀1v1对战游戏，让玩家能够通过命令行界面体验游戏的核心玩法。

### 1.2 项目目标

构建一个命令行版的三国杀游戏系统，支持玩家之间的对战，为后续AI对战和图形界面开发奠定基础。通过该项目实践面向对象编程、游戏逻辑设计和软件工程方法。

---

## 2. 技术设计

### 2.1 技术选型

- **编程语言**：Python 3.x
- **核心模块**：纯Python实现，无外部依赖
- **架构**：面向对象设计，模块化架构
- **测试**：单元测试和集成测试支持

### 2.2 系统架构

项目采用模块化设计，文件结构如下：

```
sanguosha/
├── app/
│   ├── core/                # 核心逻辑
│   │   ├── game_engine.py   # 游戏引擎
│   │   └── room.py          # 房间管理
│   ├── models/              # 数据模型
│   │   ├── player.py        # 玩家类
│   │   ├── game.py          # 游戏逻辑
│   │   ├── character.py     # 武将类
│   │   ├── deck.py          # 牌堆类
│   │   └── skills.py        # 技能类
│   ├── main.py              # 游戏入口
│   └── schemas/             # 数据模式
├── tests/                   # 测试用例
├── README.md                # 项目说明文档
└── requirements.txt         # 项目依赖
```

---

## 3. 核心模块设计

### 3.1 玩家模块

玩家模块定义了玩家的基本属性和操作方法：

- **属性**：
  - `character`：玩家的角色。
  - `hand_cards`：玩家的手牌。
  - `weapon`：玩家装备的武器。
  - `chained`：玩家是否处于铁锁连环状态。

- **方法**：
  - `draw_card(deck, count)`：从牌堆摸牌。
  - `discard_card(card)`：弃牌。
  - `use_card(card)`：使用牌。

### 3.2 游戏模块

游戏模块负责管理游戏的整体逻辑，包括初始化、回合管理和胜负判断：

- **属性**：
  - `players`：参与游戏的玩家列表。
  - `deck`：游戏使用的牌堆。
  - `current_player_index`：当前回合的玩家索引。

- **方法**：
  - `start_game()`：初始化游戏，发牌并开始。
  - `next_turn()`：进入下一回合。
  - `play_turn()`：执行当前玩家的回合。
  - `check_winner()`：检查游戏是否有胜者。

### 3.3 事件系统

事件系统用于管理玩家之间的交互逻辑，确保游戏流程的清晰和可扩展性：

- **事件类型**：
  - `PLAY_CARD`：出牌事件。
  - `USE_SKILL`：技能发动事件。
  - `TAKE_DAMAGE`：受到伤害事件。

- **事件管理器**：
  - `register_listener(event_type, listener)`：注册事件监听器。
  - `trigger_event(event_type, **kwargs)`：触发事件。

- **示例代码**：
```python
class EventManager:
    def __init__(self):
        self.listeners = {}

    def register_listener(self, event_type, listener):
        if event_type not in self.listeners:
            self.listeners[event_type] = []
        self.listeners[event_type].append(listener)

    def trigger_event(self, event_type, **kwargs):
        if event_type in self.listeners:
            for listener in self.listeners[event_type]:
                listener(**kwargs)
```

---

## 4. 测试与优化

### 4.1 测试计划

列出测试用例和覆盖范围。

### 4.2 性能优化

描述项目的优化方向和方法。

---

## 5. 后续计划

### 5.1 功能扩展

- AI对战
- 图形界面
- 网络对战

### 5.2 国际化支持

支持多语言版本。
