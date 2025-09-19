# 三国杀项目

## 项目结构

```
├── app/
│   ├── api/
│   │   ├── game_api.py       # 游戏相关API
│   │   ├── room.py           # 房间管理模块
│   │   ├── room_manager.py   # 房间管理逻辑
│   │   └── ws.py             # WebSocket服务
│   ├── core/
│   │   ├── enums.py          # 枚举类型
│   │   ├── event_system.py   # 事件系统
│   │   ├── fsm.py            # 有限状态机
│   │   ├── game.py           # 游戏逻辑
│   │   ├── game_engine.py    # 游戏引擎
│   │   ├── path_utils.py     # 路径管理工具
│   │   └── state.py          # 游戏状态管理
│   ├── models/
│   │   ├── action.py         # 动作模型
│   │   ├── character.py      # 角色模型
│   │   ├── deck.py           # 牌堆模型
│   │   ├── player.py         # 玩家模型
│   │   ├── recongnize.py     # 识别模块
│   │   └── skills.py         # 技能模型
│   ├── data/
│   │   ├── picture.json      # 图片数据
│   │   ├── state.json        # 状态数据
│   │   └── state_pic_1.json  # 状态图片数据
│   └── main.py               # 项目入口
```

## 系统架构设计

### 1. 模块划分
- **API 层**：负责处理客户端请求，提供游戏相关的接口。
- **核心逻辑层**：实现游戏的核心逻辑，包括状态管理、事件系统和游戏引擎。
- **数据模型层**：定义游戏中的数据结构，如角色、牌堆、技能等。
- **数据层**：存储游戏的静态数据，如图片和状态配置。

### 2. 交互流程
1. 客户端通过 API 层发送请求。
2. API 层调用核心逻辑层处理请求。
3. 核心逻辑层根据数据模型层的定义操作数据。
4. 数据层提供静态数据支持。

### 3. 技术选型
- **编程语言**：Python 3.x
- **框架**：FastAPI（API 层）
- **数据库**：SQLite（轻量级存储）
- **测试工具**：pytest（单元测试）

### 4. 架构总览
- 分层架构：API 层 → 核心领域层（引擎/状态/事件/FSM）→ 数据模型层 → 数据资源层。
- 模块边界清晰：API 层不直接操作模型，只通过 GameEngine 与 EventSystem 驱动流程。
- 可扩展点：技能系统、事件监听、状态机节点、卡牌与角色均以组合/注册的方式扩展。

架构示意（文本化）：
```
Client / CLI / Bot
      │
      ▼
   API 层 (FastAPI, /game, /ws)
      │ 调用
      ▼
核心领域层 ── GameEngine ──► Game ──► State ──► FSM
      │                     │        │
      │                     │        └─► EventSystem（发布/订阅）
      │                     └─► Models（Player/Character/Card/Deck/...）
      ▼
数据资源层（app/data）
```

### 5. 核心领域模型
- Game（核心对局）：维护玩家队列、当前回合、胜负判定、全局事件派发。
- Player（玩家）：手牌、装备、状态（如连环）、可执行的动作集合。
- Character（武将）：体力、势力、技能集合，负责被动/主动技能触发入口。
- Card / CardType（牌与类型）：基础行为载体（如杀/闪/桃/酒/装备），由引擎解释。
- Deck（牌堆）：洗牌、摸牌、弃牌回收与重洗逻辑。
- Action（动作）：标准化玩家行为（出牌、弃牌、发动技能等）。
- Skills（技能）：通过 SkillManager 进行注册与触发，技能本身解耦合于具体流程。
- EventManager（事件系统）：发布/订阅机制，支持优先级、取消与冒泡（可按需增强）。
- FSM（有限状态机）：将「准备 → 判定 → 摸牌 → 出牌 → 弃牌 → 结束」串联为可扩展节点。

### 6. 模块职责详解
- API 层（app/api）
  - game_api.py：REST 接口，包装 GameEngine 能力，返回对局状态快照。
  - ws.py：WebSocket 推送（如状态更新、事件广播）。
  - room/room_manager：对局编排（匹配、房间生命周期）。
- 核心逻辑层（app/core）
  - game_engine.py：驱动整局流程与步骤调度，是外部唯一入口。
  - game.py：领域规则落地（如判定胜负、回合推进）。
  - state.py：统一管理可序列化的对局状态，便于快照/回放。
  - event_system.py：事件发布/订阅，降低模块耦合度。
  - fsm.py：各阶段状态与转换关系的定义与执行。
  - path_utils.py：统一路径管理，保证运行/调试一致性。
- 数据模型层（app/models）
  - action/character/deck/player/skills 等：领域对象的结构与基本行为。
- 数据资源层（app/data）
  - 静态资源与配置（如 picture.json、state.json）。

### 7. 关键流程说明
- 启动流程
  1) 入口加载 path_utils.setup_paths() → 2) 初始化 EventManager、GameEngine → 3) 创建 Game/Deck/Players → 4) 进入回合循环。
- 回合主流程（简化）
  - 准备阶段 → 判定阶段 → 摸牌阶段 → 出牌阶段（触发大量事件/技能）→ 弃牌阶段 → 结束阶段。
- 事件派发流程
  - 事件源（引擎/模型）发出事件 → EventManager 通知监听器（技能/系统逻辑）→ 可改变状态或追加新事件。
- 出牌流程（示例）
  - Player.use_card → 校验（时机/距离/次数/限制）→ 触发事件（Before/After）→ 更新状态（扣牌、结算）。

### 8. 依赖与包结构约定
- 所有跨包导入一律使用绝对导入（如 `from app.core.base.game import Game`），避免相对导入在调试中失效。
- 顶层通过 `path_utils.setup_paths()` 确保根目录加入 sys.path。
- 新增模块需在相应包添加 `__init__.py`（已存在 core 的 __init__.py）。

### 9. 配置与环境
- Python：3.10+（建议）
- 依赖安装：`pip install -r requirements.txt`（根目录）
- 运行：`PYTHONPATH=. python -m app.main` 或 `python run_game.py`
- 调试（pdb 示例）：`PYTHONPATH=. python -m pdb app/main.py`
- VSCode/IDE 调试：将工作目录设置为仓库根路径，并在入口第一行调用 `setup_paths()`。

### 10. 路径管理（重要）
- 在需要独立运行/调试的脚本顶部加入：
  ```python
  from app.core.path_utils import setup_paths
  setup_paths()
  ```
- 原则：入口尽早设置路径，避免 `ModuleNotFoundError: No module named 'app'`。

### 11. API 设计总览（摘要）
- 路由前缀：`/game`
  - POST `/game/start`：创建/开始新对局（可选择模式、玩家/AI）。
  - POST `/game/action`：提交玩家动作（出牌/弃牌/使用技能等）。
  - GET `/game/state`：获取当前对局状态快照。
- WebSocket：`/ws`（示例），用于实时状态推送及事件广播。
- 说明：实际路由以 `app/api/*.py` 为准，此处为推荐规范与演进方向。

### 12. 状态与持久化
- 运行时状态保存在内存（state.py 可序列化），便于快照与回放。
- 可扩展：
  - 将快照写入 SQLite/文件系统；
  - 使用事件溯源（Event Sourcing）记录关键事件。

### 13. 错误处理与日志
- 统一错误模型：领域错误（规则、时机）、系统错误（I/O、序列化）。
- 日志建议：核心事件/回合切换/技能触发点打 INFO；异常栈打 ERROR。
- API 层使用全局异常处理器返回结构化错误响应。

### 14. 测试策略
- 单元测试：对 `game.py / game_engine.py / event_system.py / fsm.py` 的纯函数与规则做覆盖。
- 集成测试：以回合为粒度跑典型用例（如杀-闪-伤害-桃的链路）。
- 回归测试：新增技能/牌型时补充典型与边界用例。
- 建议使用 `pytest` 并引入覆盖率统计（coverage）。

### 15. 性能与扩展性
- 通过事件系统解耦，减少分支膨胀；
- 技能注册与裁剪：按模式或房间配置加载必要技能；
- 数据结构上避免 O(n^2) 热点（如查找、筛选），关键路径可局部缓存；
- 支持 AI Agent 接入（观察者/指令流），通过引擎统一调度。

### 16. 安全与对战公平性（如引入网络对战）
- 动作校验与重放校验，防止非法客户端指令；
- 随机性（洗牌/判定）需在服务器端完成并可审计；
- 如走 WebSocket，应对消息做限流与签名（可按需迭代）。

### 17. 多 Agent 协作规范
- 角色分工（示例）：
  - PM_Agent：拆解需求、维护 Roadmap 与任务看板；
  - UIUX_Designer_Agent：交互稿、信息架构与可视化规范；
  - Mobile_Client_Flutter_Agent：移动端交互实现；
  - AI_Game_Strategy_Agent：AI 策略/搜索/评估函数；
  - Testing_Agent：测试用例生成、覆盖率监控与回归；
- 协作流程：
  1) PM 定义需求与验收口径；
  2) 核心领域层先行演进（保证稳定 API）；
  3) 前端/移动/AI 并行开发，基于状态快照与事件模拟联调；
  4) 提交 PR 走自动化测试与 Code Review。
- 资产归档：每个 Agent 在 `agents/` 维护各自 Prompt/规范/决策记录。

### 18. 开发规范（摘录）
- 命名：统一使用小写下划线（Python 模块/文件），类名使用帕斯卡命名；
- 导入：绝对导入优先，禁止跨层直接耦合；
- 注释：关键规则与时机点必须有文档字符串与示例；
- 类型：核心模块建议补充类型注解，便于静态检查；
- 提交：一功能一提交，描述清晰，可回滚。

### 19. 路线图（Roadmap）
- v0.1：命令行 1v1 可玩 + 事件系统雏形 + 回合完整链路；
- v0.2：技能体系完善、更多牌型、AI 简单策略；
- v0.3：API/WS 联机 + 房间匹配；
- v0.4：移动端/可视化界面 + 回放/复盘工具；
- v1.0：完整对战平台与生态（观战/天梯/复盘/战报）。

### 20. 术语表（节选）
- 判定：在特定时机翻开牌进行效果判定（如乐不思蜀）。
- 锁定技：满足条件必然发动的技能。
- 主动技：玩家在时机窗口主动选择发动的技能。
- 伤害结算：包含来源、目标、伤害值、可被修改或转移的过程。
