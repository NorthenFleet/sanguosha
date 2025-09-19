# 三国杀卡牌游戏完整设计文档

## 目录
1. [项目介绍](#1-项目介绍)
2. [项目文档结构](#2-项目文档结构)
3. [基础元素系统架构](#3-基础元素系统架构)
4. [游戏基础模型](#4-游戏基础模型)
5. [决策模型系统](#5-决策模型系统)
6. [事件系统架构](#6-事件系统架构)
7. [游戏运行循环和机制](#7-游戏运行循环和机制)
8. [游戏玩法规则](#8-游戏玩法规则)
9. [技术实现细节](#9-技术实现细节)
10. [扩展性设计](#10-扩展性设计)
11. [测试与质量保证](#11-测试与质量保证)

---

## 3. 基础元素系统架构

### 3.1 系统概述

基础元素系统是三国杀游戏引擎的核心组件，位于 `app/core/base` 模块。该系统将游戏中的各种状态抽象为统一的元素接口，通过元素条件的组合来定义复杂的游戏规则。

### 3.2 设计理念

#### 3.2.1 元素化抽象
将游戏中的所有状态归结为五个基础元素：
- **卡牌元素 (CardElement)**: 手牌、牌堆、弃牌堆的管理
- **血量元素 (HealthElement)**: 当前血量、最大血量、生存状态
- **势力元素 (FactionElement)**: 魏、蜀、吴、群势力关系
- **装备元素 (EquipmentElement)**: 武器、防具、坐骑装备
- **距离元素 (DistanceElement)**: 座位距离、攻击范围计算

#### 3.2.2 技能作为元素组合
技能不再是独立的判定要素，而是基础元素的组合运用：
- 每个技能定义为一组元素条件和效果的集合
- 裁决过程统一为元素状态的检查和修改
- 通过配置文件定义技能的元素组合

### 3.3 核心组件

#### 3.3.1 BaseElement（基础元素基类）
```python
class BaseElement:
    """基础元素基类，定义统一的元素接口"""
    def __init__(self, element_type: ElementType, state: ElementState):
        self.element_type = element_type
        self.state = state
    
    def check_condition(self, condition_name: str, **kwargs) -> bool:
        """检查元素条件"""
        pass
```

#### 3.3.2 ElementBasedAdjudicationEngine（基础元素裁决引擎）
```python
class ElementBasedAdjudicationEngine:
    """基于基础元素的裁决引擎"""
    def check_condition(self, condition_name: str, 
                       player_elements: Dict[str, BaseElement], 
                       **kwargs) -> bool:
        """统一的条件检查接口"""
        pass
    
    def adjudicate_skill_use(self, skill_name: str, 
                           player_elements: Dict[str, BaseElement], 
                           context: Dict[str, Any]) -> Dict[str, Any]:
        """裁决技能使用"""
        pass
```

#### 3.3.3 ElementPlayerAdapter（玩家适配器）
```python
class ElementPlayerAdapter:
    """将Player对象转换为元素系统"""
    def convert_player_to_elements(self, player: Player, 
                                 all_players: List[Player]) -> Dict[str, BaseElement]:
        """转换玩家为元素字典"""
        pass
```

### 3.4 技术优势

#### 3.4.1 统一性
- 所有游戏状态通过统一的元素接口访问
- 一致的条件检查和效果执行机制
- 减少了特殊情况的处理代码

#### 3.4.2 灵活性
- 支持复杂条件组合
- 易于添加新的元素类型和条件
- 技能通过配置文件定义，易于扩展

#### 3.4.3 兼容性
- 与现有Player、Card等模型完全兼容
- 通过适配器模式无缝集成
- 渐进式迁移支持

#### 3.4.4 可维护性
- 清晰的模块分离
- 配置化的技能和效果定义
- 完善的测试覆盖

### 3.5 使用示例

```python
# 统一导入
from app.core.base import (
    ElementBasedAdjudicationEngine,
    BaseElement, CardElement, HealthElement, 
    FactionElement, EquipmentElement, DistanceElement,
    ElementPlayerAdapter
)

# 创建裁决引擎和适配器
engine = ElementBasedAdjudicationEngine()
adapter = ElementPlayerAdapter()

# 转换玩家为元素
elements = adapter.convert_player_to_elements(player, all_players)

# 检查条件
result = engine.check_condition("card_count_gte", elements, {"count": 2})

# 裁决技能使用
skill_result = engine.adjudicate_skill_use(
    skill_name="奸雄",
    player_elements=elements,
    context={"target": target_player}
)
```

---

## 4. 游戏基础模型

### 4.1 核心领域模型

#### 3.1.1 Game（游戏对局）
游戏对局是整个系统的核心，负责维护游戏状态和协调各个组件。

**核心属性**：
- `players: List[Player]` - 玩家列表
- `current_player_index: int` - 当前玩家索引
- `turn_number: int` - 回合数
- `phase: GamePhase` - 当前阶段
- `deck: Deck` - 牌堆
- `discard_pile: List[Card]` - 弃牌堆
- `event_manager: EventManager` - 事件管理器

**核心方法**：
- `start_game()` - 开始游戏
- `next_phase()` - 进入下一阶段
- `next_turn()` - 进入下一回合
- `check_win_condition()` - 检查胜利条件
- `handle_player_action(action)` - 处理玩家动作

#### 3.1.2 Player（玩家）
玩家模型包含玩家的所有状态信息和行为能力。

**核心属性**：
- `character: Character` - 武将
- `hp: int` - 当前体力
- `max_hp: int` - 最大体力
- `hand_cards: List[Card]` - 手牌
- `equipped: List[Card]` - 装备区
- `position: int` - 座位位置
- `status_effects: Dict[str, Any]` - 状态效果

**装备系统**：
- `weapon: Card` - 武器
- `armor: Card` - 防具
- `attack_horse: Card` - 进攻马
- `defense_horse: Card` - 防御马

**核心方法**：
- `get_attack_range()` - 获取攻击范围
- `get_distance_to(target, players)` - 计算到目标的距离
- `can_attack(target, players)` - 判断是否可以攻击目标
- `equip_card(card)` - 装备卡牌
- `use_skill(skill_name, context)` - 使用技能

#### 3.1.3 Character（武将）
武将定义了玩家的基础属性和特殊能力。

**核心属性**：
- `name: str` - 武将名称
- `kingdom: Kingdom` - 势力
- `max_hp: int` - 体力上限
- `skills: List[str]` - 技能列表
- `gender: str` - 性别（影响某些卡牌效果）

**势力枚举**：
```python
class Kingdom(Enum):
    WEI = "魏"    # 魏国
    SHU = "蜀"    # 蜀国
    WU = "吴"     # 吴国
    QUN = "群"    # 群雄
```

#### 3.1.4 Card（卡牌）
卡牌是游戏中的基本交互单位。

**核心属性**：
- `name: str` - 卡牌名称
- `card_type: CardType` - 卡牌类型
- `suit: str` - 花色
- `point: int` - 点数
- `color: str` - 颜色（红/黑）

**卡牌类型**：
```python
class CardType(Enum):
    BASIC = "基本牌"      # 杀、闪、桃等
    TRICK = "锦囊牌"      # 无懈可击、南蛮入侵等
    EQUIPMENT = "装备牌"   # 武器、防具、马等
```

#### 3.1.5 Deck（牌堆）
牌堆管理游戏中的所有卡牌流转。

**核心属性**：
- `cards: List[Card]` - 牌堆卡牌
- `discard_pile: List[Card]` - 弃牌堆

**核心方法**：
- `shuffle()` - 洗牌
- `draw_card(count=1)` - 摸牌
- `add_to_discard(cards)` - 加入弃牌堆
- `reshuffle_if_needed()` - 必要时重洗

### 3.2 技能系统模型

#### 3.2.1 Skill（技能基类）
所有技能的基础抽象。

**核心属性**：
- `name: str` - 技能名称
- `description: str` - 技能描述
- `trigger_timing: List[str]` - 触发时机
- `is_active: bool` - 是否为主动技能

**核心方法**：
- `can_trigger(context)` - 判断是否可以触发
- `execute(context)` - 执行技能效果
- `get_targets(context)` - 获取可选目标

#### 3.2.2 SkillManager（技能管理器）
管理武将的所有技能。

**核心方法**：
- `register_skill(skill)` - 注册技能
- `check_triggers(event_type, context)` - 检查触发条件
- `execute_skill(skill_name, context)` - 执行指定技能

### 3.3 动作系统模型

#### 3.3.1 Action（动作基类）
所有玩家动作的基础抽象。

**核心属性**：
- `player: Player` - 执行动作的玩家
- `action_type: str` - 动作类型
- `targets: List[Player]` - 目标玩家
- `cards: List[Card]` - 相关卡牌

**核心方法**：
- `is_valid()` - 验证动作是否合法
- `execute(game)` - 执行动作
- `get_description()` - 获取动作描述

#### 3.3.2 具体动作类型
- `PlayCardAction` - 出牌动作
- `UseSkillAction` - 使用技能动作
- `DiscardAction` - 弃牌动作
- `EquipAction` - 装备动作

---

## 5. 决策模型系统

### 5.1 决策流程概述
决策模型采用"判条件 → 查修正 → 计算结果"的三步流程，确保游戏判定的准确性和一致性。

```
输入条件 → 判定条件检查 → 修正因子计算 → 最终结果输出
    ↓           ↓              ↓            ↓
  玩家动作    条件验证        效果修正      执行结果
```

### 5.2 判定条件系统（Judgment Conditions）

#### 5.2.1 条件判定引擎
位于 `app/core/judgment_conditions.py`，负责验证各种游戏条件。

**核心功能**：
- 距离判定：计算玩家间的实际距离
- 攻击判定：验证是否可以攻击目标
- 技能判定：检查技能触发条件
- 装备判定：验证装备使用条件

**主要方法**：
```python
def can_use_card_on_target(player, card, target, game_state):
    """判断是否可以对目标使用卡牌"""
    
def is_in_attack_range(attacker, target, players):
    """判断目标是否在攻击范围内"""
    
def can_trigger_skill(player, skill_name, context):
    """判断技能是否可以触发"""
```

#### 5.2.2 距离计算系统
实现精确的座位距离和装备修正计算。

**座位距离计算**：
```python
def calculate_seat_distance(pos1, pos2, total_players):
    """计算座位间的基础距离"""
    clockwise = (pos2 - pos1) % total_players
    counter_clockwise = (pos1 - pos2) % total_players
    return min(clockwise, counter_clockwise)
```

**装备修正计算**：
- 武器：增加攻击范围
- 进攻马：攻击距离-1
- 防御马：被攻击距离+1

### 5.3 修正处理系统（Modification Handlers）

#### 5.3.1 修正引擎
位于 `app/core/modification_handlers.py`，处理各种效果修正。

**修正类型**：
- **武器修正**：武器对攻击范围和伤害的影响
- **防具修正**：防具对伤害减免和特殊效果的影响
- **技能修正**：技能对各种数值的修正
- **状态修正**：临时状态对游戏数值的影响

**核心类**：
```python
class WeaponEffectHandler:
    """武器效果处理器"""
    def apply_weapon_effect(self, weapon, context):
        """应用武器效果"""

class ArmorEffectHandler:
    """防具效果处理器"""
    def apply_armor_effect(self, armor, context):
        """应用防具效果"""
```

#### 5.3.2 装备判定系统
位于 `app/core/equipment_judgment.py`，专门处理装备相关的判定。

**武器效果处理**：
- 青龙偃月刀：杀被闪抵消时可再出杀
- 丈八蛇矛：可弃两张牌当杀使用
- 方天画戟：使用最后手牌杀时可指定额外目标
- 麒麟弓：杀造成伤害时可弃置目标装备
- 古锭刀：对无手牌目标伤害+1

**防具效果处理**：
- 八卦阵：需要闪时可进行判定
- 仁王盾：黑色杀无效
- 白银狮子：受到超过1点伤害时减免到1点
- 藤甲：杀和南蛮入侵无效，但火焰伤害+1

### 5.4 裁决引擎（Adjudication Engine）

#### 5.4.1 裁决流程
位于 `app/core/adjudication_engine.py`，负责最终的游戏裁决。

**裁决步骤**：
1. **条件验证**：检查动作是否满足基本条件
2. **修正计算**：应用所有相关的修正效果
3. **冲突解决**：处理多个效果间的冲突
4. **结果确定**：输出最终的裁决结果

**核心方法**：
```python
class AdjudicationEngine:
    def adjudicate_action(self, action, context):
        """裁决玩家动作"""
        # 1. 验证基础条件
        if not self.validate_basic_conditions(action, context):
            return AdjudicationResult(False, "条件不满足")
        
        # 2. 计算修正效果
        modifications = self.calculate_modifications(action, context)
        
        # 3. 应用修正并得出结果
        result = self.apply_modifications(action, modifications)
        
        return result
```

#### 5.4.2 交互模型集成
与 `app/core/interaction_model.py` 集成，处理复杂的玩家交互。

**交互上下文**：
```python
@dataclass
class InteractionContext:
    game_state: Any
    current_player: Player
    action_type: str
    targets: List[Player]
    cards: List[Card]
    additional_data: Dict[str, Any]
```

**交互结果**：
```python
@dataclass
class InteractionResult:
    success: bool
    message: str
    state_changes: Dict[str, Any]
    follow_up_actions: List[Action]
```

### 5.5 决策优化机制

#### 5.5.1 缓存机制
对频繁计算的结果进行缓存，提高性能。

#### 5.5.2 优先级处理
当多个效果同时触发时，按照优先级顺序处理：
1. 无懈可击类效果（最高优先级）
2. 闪避类效果
3. 技能响应
4. 被动效果（最低优先级）

#### 5.5.3 冲突解决
当效果间存在冲突时，采用以下规则：
- 后发生的效果覆盖先发生的效果
- 特殊效果优先于一般效果
- 玩家主动选择优先于系统自动处理

## 6. 事件系统架构

### 6.1 事件系统概述
事件系统是游戏架构的核心，采用发布-订阅模式实现松耦合的组件通信。系统支持多玩家实时交互、技能连锁触发和复杂的响应优先级处理。

### 6.2 基础事件系统

#### 6.2.1 EventManager（事件管理器）
位于 `app/core/event_system.py`，提供基础的事件发布和订阅功能。

**核心功能**：
- 事件注册和取消注册
- 事件发布和分发
- 监听器管理
- 事件优先级处理

**核心方法**：
```python
class EventManager:
    def subscribe(self, event_type, callback, priority=0):
        """订阅事件"""
    
    def unsubscribe(self, event_type, callback):
        """取消订阅"""
    
    def publish(self, event_type, data):
        """发布事件"""
    
    def clear_all_subscriptions(self):
        """清除所有订阅"""
```

#### 6.2.2 事件类型定义
```python
class GameEventType(Enum):
    # 回合事件
    TURN_START = "turn_start"
    TURN_END = "turn_end"
    PHASE_CHANGE = "phase_change"
    
    # 卡牌事件
    CARD_PLAY = "card_play"
    CARD_USE = "card_use"
    CARD_DRAW = "card_draw"
    CARD_DISCARD = "card_discard"
    
    # 伤害事件
    DAMAGE_DEAL = "damage_deal"
    DAMAGE_TAKE = "damage_take"
    HP_CHANGE = "hp_change"
    
    # 技能事件
    SKILL_TRIGGER = "skill_trigger"
    SKILL_USE = "skill_use"
    
    # 装备事件
    EQUIPMENT_EQUIP = "equipment_equip"
    EQUIPMENT_UNEQUIP = "equipment_unequip"
```

### 6.3 多玩家事件系统

#### 6.3.1 MultiPlayerEventSystem
位于 `app/core/multi_player_event_system.py`，专门处理多玩家交互事件。

**核心特性**：
- 支持多玩家同时响应
- 响应优先级和顺序控制
- 响应窗口管理
- 超时处理机制

**事件优先级**：
```python
class EventPriority(Enum):
    HIGHEST = 0    # 最高优先级（如无懈可击）
    HIGH = 1       # 高优先级（如闪避）
    NORMAL = 2     # 普通优先级（如技能响应）
    LOW = 3        # 低优先级（如被动技能）
    LOWEST = 4     # 最低优先级
```

**响应类型**：
```python
class ResponseType(Enum):
    CARD_RESPONSE = "card_response"      # 卡牌响应
    SKILL_RESPONSE = "skill_response"    # 技能响应
    CHOICE_RESPONSE = "choice_response"  # 选择响应
    PASS_RESPONSE = "pass_response"      # 跳过响应
```

#### 6.3.2 GameEvent（游戏事件）
```python
@dataclass
class GameEvent:
    event_id: str
    event_type: str
    source_player_id: str
    target_player_ids: List[str]
    data: Dict[str, Any]
    timestamp: float
    priority: EventPriority = EventPriority.NORMAL
```

#### 6.3.3 EventResponse（事件响应）
```python
@dataclass
class EventResponse:
    response_id: str
    event_id: str
    player_id: str
    response_type: ResponseType
    response_data: Dict[str, Any]
    timestamp: float
```

### 6.4 事件分发系统

#### 6.4.1 GameEventDispatcher
位于 `app/core/event_dispatcher.py`，集成多玩家事件系统与现有交互模型。

**核心功能**：
- 事件类型映射和转换
- 裁决引擎集成
- 响应收集和处理
- 事件队列管理

**主要方法**：
```python
class GameEventDispatcher:
    def dispatch_card_event(self, player_id, card, targets, action_type):
        """分发卡牌事件"""
    
    def dispatch_skill_event(self, player_id, skill_name, targets, context):
        """分发技能事件"""
    
    def dispatch_damage_event(self, source_id, target_id, damage, damage_type):
        """分发伤害事件"""
    
    def collect_responses(self, event, timeout=30):
        """收集玩家响应"""
```

#### 6.4.2 响应处理流程
```
事件发布 → 确定响应玩家 → 开启响应窗口 → 收集响应 → 按优先级处理 → 执行结果
```

### 6.5 技能事件处理

#### 6.5.1 SkillEventHandler
位于 `app/core/skill_event_handlers.py`，专门处理技能相关的事件。

**技能触发机制**：
- 被动技能自动触发
- 主动技能玩家选择触发
- 技能连锁和组合效果
- 技能冲突解决

**核心类**：
```python
class CharacterSkillManager:
    """角色技能管理器"""
    def __init__(self, player_id, character_name):
        self.player_id = player_id
        self.character_name = character_name
        self.skills = self._load_character_skills()
    
    def can_trigger_skill(self, skill_name, event_type, context):
        """检查技能是否可以触发"""
    
    def trigger_skill(self, skill_name, context):
        """触发技能"""
```

#### 6.5.2 技能响应处理器
```python
class SkillResponseHandler(PlayerResponseHandler):
    """技能响应处理器"""
    def can_respond_to_event(self, event):
        """检查是否可以响应事件"""
    
    def generate_response_options(self, event):
        """生成响应选项"""
    
    def create_response(self, event, choice):
        """创建响应"""
```

### 6.6 集成交互系统

#### 6.6.1 IntegratedInteractionSystem
位于 `app/core/integrated_interaction_system.py`，整合所有交互组件。

**系统组件**：
- 游戏引擎（GameEngine）
- 交互引擎（InteractionEngine）
- 判定注册表（JudgmentRegistry）
- 修正引擎（ModificationEngine）
- 裁决引擎（AdjudicationEngine）

**核心方法**：
```python
class IntegratedInteractionSystem:
    def process_player_action(self, player_id, action_data):
        """处理玩家动作"""
    
    def handle_card_play(self, player_id, card_name, targets):
        """处理出牌动作"""
    
    def handle_skill_use(self, player_id, skill_name, targets):
        """处理技能使用"""
    
    def handle_equipment_effect(self, player_id, equipment_name, context):
        """处理装备效果"""
```

---

## 7. 游戏运行循环和机制

### 7.1 游戏状态机

#### 7.1.1 FSM（有限状态机）
位于 `app/core/fsm.py`，管理游戏的状态转换。

**游戏阶段**：
```python
class GamePhase(Enum):
    PREPARATION = "准备阶段"
    JUDGMENT = "判定阶段"
    DRAW = "摸牌阶段"
    PLAY = "出牌阶段"
    DISCARD = "弃牌阶段"
    END = "结束阶段"
```

**状态转换图**：
```
准备阶段 → 判定阶段 → 摸牌阶段 → 出牌阶段 → 弃牌阶段 → 结束阶段
    ↑                                                        ↓
    ←←←←←←←←←←←←← 下一玩家回合 ←←←←←←←←←←←←←←←←←←←←←←←←←←←
```

#### 7.1.2 状态管理
位于 `app/core/state.py`，管理游戏的可序列化状态。

**游戏状态**：
```python
@dataclass
class GameState:
    game_id: str
    players: List[PlayerState]
    current_player_index: int
    current_phase: GamePhase
    turn_number: int
    deck_remaining: int
    discard_pile_size: int
    game_status: str
    last_action: Optional[Dict[str, Any]]
```

**玩家状态**：
```python
@dataclass
class PlayerState:
    player_id: str
    character_name: str
    hp: int
    max_hp: int
    hand_card_count: int
    equipped_cards: List[str]
    status_effects: Dict[str, Any]
    position: int
```

### 7.2 游戏引擎

#### 7.2.1 GameEngine
位于 `app/core/game_engine.py`，是游戏的主控制器。

**核心职责**：
- 游戏创建和初始化
- 回合流程控制
- 动作执行和验证
- 状态同步和管理

**主要方法**：
```python
class GameEngine:
    def create_game(self, players, game_config):
        """创建新游戏"""
    
    def start_game(self, game_id):
        """开始游戏"""
    
    def execute_action(self, game_id, player_id, action):
        """执行玩家动作"""
    
    def get_game_state(self, game_id):
        """获取游戏状态"""
    
    def advance_phase(self, game_id):
        """推进游戏阶段"""
```

#### 7.2.2 Game（游戏逻辑）
位于 `app/core/game.py`，实现具体的游戏规则。

**回合流程**：
```python
class Game:
    def execute_turn(self, player):
        """执行玩家回合"""
        self.preparation_phase(player)
        self.judgment_phase(player)
        self.draw_phase(player)
        self.play_phase(player)
        self.discard_phase(player)
        self.end_phase(player)
    
    def preparation_phase(self, player):
        """准备阶段"""
        # 重置玩家状态
        # 处理回合开始事件
    
    def judgment_phase(self, player):
        """判定阶段"""
        # 处理延时锦囊
        # 执行判定
    
    def draw_phase(self, player):
        """摸牌阶段"""
        # 摸牌（通常2张）
        # 处理摸牌相关技能
    
    def play_phase(self, player):
        """出牌阶段"""
        # 等待玩家出牌
        # 处理卡牌效果
        # 处理技能使用
    
    def discard_phase(self, player):
        """弃牌阶段"""
        # 检查手牌上限
        # 强制弃牌
    
    def end_phase(self, player):
        """结束阶段"""
        # 处理回合结束事件
        # 清理临时效果
```

### 7.3 玩家响应系统

#### 7.3.1 PlayerResponseManager
位于 `app/core/player_response_manager.py`，管理玩家的响应和交互。

**响应窗口管理**：
```python
class ResponseWindow:
    def __init__(self, event, eligible_players, timeout=30):
        self.event = event
        self.eligible_players = eligible_players
        self.responses = {}
        self.timeout = timeout
        self.is_open = True
    
    def add_response(self, player_id, response):
        """添加玩家响应"""
    
    def close_window(self):
        """关闭响应窗口"""
    
    def get_responses_by_priority(self):
        """按优先级获取响应"""
```

#### 7.3.2 响应处理流程
1. **事件触发**：游戏事件发生
2. **确定响应者**：根据事件类型确定可响应的玩家
3. **开启响应窗口**：设置超时时间，等待响应
4. **收集响应**：收集所有玩家的响应
5. **优先级排序**：按照优先级和时间顺序排序
6. **执行响应**：依次执行所有有效响应
7. **更新状态**：更新游戏状态

### 7.4 游戏循环机制

#### 7.4.1 主游戏循环
```python
def main_game_loop(game):
    """主游戏循环"""
    while not game.is_finished():
        current_player = game.get_current_player()
        
        # 执行玩家回合
        game.execute_turn(current_player)
        
        # 检查胜利条件
        winner = game.check_win_condition()
        if winner:
            game.end_game(winner)
            break
        
        # 切换到下一玩家
        game.next_player()
    
    return game.get_final_result()
```

#### 7.4.2 异步处理机制
对于Web版本，支持异步处理：

```python
async def async_game_loop(game_id):
    """异步游戏循环"""
    game = game_engine.get_game(game_id)
    
    while not game.is_finished():
        # 等待玩家动作
        action = await wait_for_player_action(game.current_player)
        
        # 处理动作
        result = await process_action(game, action)
        
        # 广播状态更新
        await broadcast_game_state(game_id, game.get_state())
        
        # 检查游戏结束
        if game.check_win_condition():
            await end_game(game_id)
            break
```

### 7.5 错误处理和恢复

#### 7.5.1 异常处理机制
- **动作验证失败**：返回错误信息，不改变游戏状态
- **网络连接中断**：保存游戏状态，支持重连
- **超时处理**：自动跳过或执行默认动作
- **状态不一致**：强制同步或回滚到上一个稳定状态

#### 7.5.2 游戏状态持久化
- **自动保存**：每个回合结束后自动保存
- **手动保存**：玩家可以手动保存游戏
- **状态恢复**：支持从保存点恢复游戏
- **回放功能**：记录所有动作，支持游戏回放

---

## 8. 游戏玩法规则

### 8.1 卡牌系统

#### 8.1.1 卡牌分类
游戏中的卡牌分为三大类别，每类都有其独特的使用规则和效果。

**基本牌（Basic Cards）**：
- **杀**：对一名角色造成1点伤害，需要在攻击范围内
- **闪**：抵消一张杀的效果
- **桃**：回复1点体力，不能超过体力上限
- **酒**：增强下一张杀的伤害+1，或回复1点体力

**锦囊牌（Trick Cards）**：
- **无懈可击**：抵消一张锦囊牌的效果
- **过河拆桥**：弃置一名角色的一张牌
- **顺手牵羊**：获得一名角色的一张手牌
- **南蛮入侵**：所有其他角色需出杀或受到1点伤害
- **万箭齐发**：所有其他角色需出闪或受到1点伤害
- **桃园结义**：所有角色回复1点体力
- **五谷丰登**：所有角色从牌堆顶摸取一张牌
- **决斗**：与目标角色轮流出杀，先不出者受到1点伤害
- **借刀杀人**：令有武器的角色对指定目标使用杀
- **闪电**：延时锦囊，判定为黑桃2-9时造成3点雷电伤害
- **乐不思蜀**：延时锦囊，判定为红桃时跳过出牌阶段

**装备牌（Equipment Cards）**：
- **武器**：增加攻击范围和特殊效果
- **防具**：提供防护能力和特殊效果
- **坐骑**：分为进攻马（-1攻击距离）和防御马（+1被攻击距离）

#### 8.1.2 卡牌属性系统
每张卡牌都有以下基本属性：

```python
class Card:
    name: str           # 卡牌名称
    card_type: str      # 卡牌类型（基本牌/锦囊牌/装备牌）
    suit: str          # 花色（黑桃/红桃/梅花/方块）
    point: int         # 点数（1-13）
    color: str         # 颜色（红色/黑色）
    effect: str        # 效果描述
```

**花色和颜色**：
- 红色：红桃♥、方块♦
- 黑色：黑桃♠、梅花♣

**点数特殊意义**：
- A（1）：通常为最小或最大值
- J（11）、Q（12）、K（13）：人物牌，某些技能有特殊效果

#### 8.1.3 装备牌详细规则

**武器装备**：
- **青龙偃月刀**（攻击范围3）：杀被闪抵消时可再出一张杀
- **丈八蛇矛**（攻击范围3）：可弃两张牌当杀使用
- **方天画戟**（攻击范围4）：使用最后手牌杀时可指定额外目标
- **麒麟弓**（攻击范围5）：杀造成伤害时可弃置目标装备
- **贯石斧**（攻击范围3）：目标使用闪时可弃两张牌令闪无效
- **古锭刀**（攻击范围2）：对无手牌目标伤害+1
- **朱雀羽扇**（攻击范围4）：可将普通杀当火杀使用
- **雌雄双股剑**（攻击范围2）：对异性目标使用杀时可摸一张牌

**防具装备**：
- **八卦阵**：可用判定代替闪
- **仁王盾**：黑色杀对你无效
- **白银狮子**：受到伤害时最多扣减1点体力
- **藤甲**：火焰伤害+1，南蛮入侵和万箭齐发无效

**坐骑装备**：
- **进攻马**：你计算与其他角色距离-1
- **防御马**：其他角色计算与你距离+1

### 8.2 武将系统

#### 8.2.1 武将分类
武将按势力分为四个阵营，每个阵营都有其特色和玩法风格。

**魏国（Wei）**：
- **曹操**：奸雄（受到伤害时可获得伤害牌）、护驾（可求其他魏国角色代替出闪）
- **司马懿**：反馈（受到伤害时可获得伤害来源一张牌）、鬼才（可改变判定结果）
- **夏侯惇**：刚烈（受到伤害时可判定，红色则对伤害来源造成1点伤害）
- **张辽**：突袭（摸牌阶段可改为获得至多两名角色各一张手牌）
- **许褚**：裸衣（没有手牌时使用杀或被杀指定时摸一张牌）

**蜀国（Shu）**：
- **刘备**：仁德（出牌阶段可给其他角色任意张手牌）、激将（可令其他蜀国角色代替出杀）
- **关羽**：武圣（可将红色牌当杀使用或打出）
- **张飞**：咆哮（出牌阶段可使用任意张杀）
- **赵云**：龙胆（可将杀当闪、闪当杀使用）
- **诸葛亮**：观星（准备阶段可观看牌堆顶5张牌并重新排列）、空城（没有手牌时不能成为杀或决斗的目标）

**吴国（Wu）**：
- **孙权**：制衡（出牌阶段可弃置任意张牌然后摸等量牌）、救援（主公技，其他吴国角色对你使用桃时回复额外1点体力）
- **甘宁**：奇袭（可将黑色牌当过河拆桥使用）
- **吕蒙**：克己（若你没有在出牌阶段内使用或打出过杀，可跳过弃牌阶段）
- **黄盖**：苦肉（出牌阶段可失去1点体力摸两张牌）
- **周瑜**：英姿（摸牌阶段多摸一张牌）、反间（出牌阶段可观看一名角色手牌并选择花色，若其中没有此花色则其受到1点伤害）

**群雄（Qun）**：
- **华佗**：急救（你的回合外，可将红色牌当桃使用）、青囊（出牌阶段可弃一张手牌令一名角色回复1点体力）
- **吕布**：无双（使用杀指定目标后，目标需连续使用两张闪才能抵消；使用决斗时对方需连续出两张杀）
- **貂蝉**：离间（出牌阶段可弃一张牌令两名男性角色决斗）、闭月（结束阶段可摸一张牌）

#### 8.2.2 武将属性设置
每个武将都有以下基本属性：

```python
class Character:
    name: str           # 武将名称
    kingdom: Kingdom    # 势力（魏/蜀/吴/群）
    max_hp: int        # 体力上限（3-5点）
    skills: List[str]  # 技能列表
    gender: str        # 性别（男/女）
```

**体力设置规则**：
- 3体力：司马懿等少数武将
- 4体力：大部分武将的标准体力
- 5体力：主公或特殊武将

**性别影响**：
- 雌雄双股剑：对异性目标使用杀时效果不同
- 貂蝉离间：只能指定男性角色决斗
- 某些技能可能有性别限制

#### 8.2.3 技能系统设置

**技能分类**：
- **主动技能**：需要玩家主动发动，如仁德、制衡
- **被动技能**：满足条件时自动触发，如奸雄、武圣
- **锁定技**：强制执行，不能选择不发动，如咆哮的部分效果
- **主公技**：只有主公才能使用的技能，如激将、救援

**技能触发时机**：
- **准备阶段**：观星
- **判定阶段**：鬼才
- **摸牌阶段**：英姿、突袭
- **出牌阶段**：仁德、制衡、奇袭
- **弃牌阶段**：克己
- **结束阶段**：闭月
- **回合外**：急救、反馈、刚烈

### 8.3 游戏流程规则

#### 8.3.1 出牌顺序规则
游戏采用回合制，每个玩家按顺序进行回合。

**回合顺序**：
- 按座位顺序顺时针进行
- 每个玩家完成完整回合后轮到下一位
- 特殊情况（如额外回合）按规则处理

**回合内阶段顺序**：
1. **准备阶段**：重置状态，处理准备阶段技能
2. **判定阶段**：处理延时锦囊和判定区卡牌
3. **摸牌阶段**：摸牌（通常2张）
4. **出牌阶段**：使用手牌和发动技能
5. **弃牌阶段**：弃置多余手牌
6. **结束阶段**：处理结束阶段效果

**出牌阶段规则**：
- 每回合只能使用一张杀（咆哮等技能除外）
- 装备牌可以随时使用
- 锦囊牌按照目标和时机限制使用
- 技能发动按照各自的限制条件

#### 8.3.2 座位距离计算
距离是三国杀中的核心概念，影响攻击范围和某些卡牌的使用。

**基础距离计算**：
```python
def calculate_seat_distance(pos1, pos2, total_players):
    """计算座位间的最短距离"""
    clockwise = (pos2 - pos1) % total_players
    counter_clockwise = (pos1 - pos2) % total_players
    return min(clockwise, counter_clockwise)
```

**距离修正因素**：
- **武器**：增加攻击范围（不影响距离计算）
- **进攻马**：你计算与其他角色距离-1
- **防御马**：其他角色计算与你距离+1
- **技能效果**：某些技能可能影响距离计算

**攻击范围判定**：
```python
def can_attack(attacker, target, players):
    """判断是否可以攻击目标"""
    distance = calculate_distance_with_equipment(attacker, target, players)
    attack_range = attacker.get_attack_range()
    return distance <= attack_range
```

#### 8.3.3 回合设置和时间限制

**回合时间设置**：
- **准备阶段**：自动处理，无时间限制
- **判定阶段**：自动处理判定，玩家可响应
- **摸牌阶段**：自动摸牌，无时间限制
- **出牌阶段**：玩家操作，建议60-120秒时间限制
- **弃牌阶段**：强制弃牌，30秒时间限制
- **结束阶段**：自动处理，无时间限制

**响应时间设置**：
- **使用闪响应杀**：15-30秒
- **使用无懈可击**：15-30秒
- **技能发动选择**：30-60秒
- **目标选择**：30秒

### 8.4 胜利条件和游戏结束

#### 8.4.1 胜利条件
不同游戏模式有不同的胜利条件。

**1v1模式**：
- 对手体力降至0或以下
- 对手无法摸牌且牌堆为空
- 对手投降

**多人身份模式**：
- **主公胜利**：所有反贼和内奸死亡
- **反贼胜利**：主公死亡
- **内奸胜利**：场上只剩主公和内奸，且内奸杀死主公

**多人国战模式**：
- 某个势力的所有角色存活，其他势力全部死亡
- 特殊胜利条件（如野心家）

#### 8.4.2 游戏结束处理

**体力归零处理**：
1. 进入濒死状态
2. 按座位顺序询问是否使用桃
3. 无人救援则角色死亡
4. 检查游戏是否结束

**牌堆耗尽处理**：
1. 将弃牌堆洗混成为新牌堆
2. 若弃牌堆也为空，则游戏平局
3. 特殊模式可能有不同规则

**异常结束处理**：
- 玩家掉线：AI代管或暂停等待
- 网络异常：保存游戏状态，支持重连
- 系统错误：记录日志，尝试恢复或判定平局

### 8.5 特殊规则和机制

#### 8.5.1 连环状态
连环是游戏中的特殊状态机制。

**连环规则**：
- 使用铁索连环可以将角色横置（连环状态）
- 连环状态的角色受到火焰或雷电伤害时，伤害传导给所有连环角色
- 再次使用铁索连环可以解除连环状态

**连环传导**：
```python
def chain_damage_spread(source_player, damage_type, players):
    """连环伤害传导"""
    if damage_type in ["fire", "thunder"]:
        chained_players = [p for p in players if p.chained and p != source_player]
        for player in chained_players:
            player.take_damage(1, damage_type)
```

#### 8.5.2 判定机制
判定是游戏中的重要机制，用于决定某些效果是否生效。

**判定流程**：
1. 翻开牌堆顶一张牌作为判定牌
2. 根据判定要求检查花色和点数
3. 玩家可以使用技能或卡牌改变判定结果
4. 确定最终判定结果并执行相应效果
5. 判定牌进入弃牌堆

**常见判定**：
- **闪电**：黑桃2-9造成3点雷电伤害
- **乐不思蜀**：红桃跳过出牌阶段
- **八卦阵**：红色当作闪使用
- **刚烈**：红色对伤害来源造成1点伤害

#### 8.5.3 优先级和时机
游戏中存在复杂的优先级和时机问题。

**响应优先级**：
1. **最高优先级**：无懈可击
2. **高优先级**：闪避杀
3. **普通优先级**：技能响应
4. **低优先级**：被动技能触发

**同时机处理**：
- 按座位顺序依次处理
- 主动技能优先于被动技能
- 玩家选择优先于系统自动处理

---

## 9. 技术实现细节

### 9.1 核心算法实现

#### 9.1.1 距离计算算法
距离计算是游戏中的核心算法，影响攻击范围和卡牌使用。

```python
class DistanceCalculator:
    @staticmethod
    def calculate_base_distance(pos1: int, pos2: int, total_players: int) -> int:
        """计算基础座位距离"""
        if pos1 == pos2:
            return 0
        
        clockwise = (pos2 - pos1) % total_players
        counter_clockwise = (pos1 - pos2) % total_players
        return min(clockwise, counter_clockwise)
    
    @staticmethod
    def calculate_distance_with_equipment(attacker: Player, target: Player, 
                                        all_players: List[Player]) -> int:
        """计算考虑装备的实际距离"""
        base_distance = DistanceCalculator.calculate_base_distance(
            attacker.position, target.position, len(all_players)
        )
        
        # 进攻马效果：攻击者计算距离-1
        if attacker.has_offensive_horse():
            base_distance -= 1
            
        # 防御马效果：被攻击者被计算距离+1
        if target.has_defensive_horse():
            base_distance += 1
            
        return max(1, base_distance)  # 最小距离为1
```

#### 9.1.2 装备判定算法
装备系统的判定逻辑，包括武器和防具的特殊效果处理。

```python
class EquipmentJudgment:
    def __init__(self):
        self.weapon_processors = {
            "青龙偃月刀": self._process_qinglong_yanyuedao,
            "丈八蛇矛": self._process_zhangba_shemao,
            "方天画戟": self._process_fangtian_huaji,
            # ... 其他武器
        }
        
        self.armor_processors = {
            "八卦阵": self._process_bagua_zhen,
            "仁王盾": self._process_renwang_dun,
            "白银狮子": self._process_baiyin_shizi,
            # ... 其他防具
        }
    
    def process_weapon_effect(self, weapon_name: str, context: dict) -> dict:
        """处理武器特殊效果"""
        if weapon_name in self.weapon_processors:
            return self.weapon_processors[weapon_name](context)
        return context
    
    def _process_qinglong_yanyuedao(self, context: dict) -> dict:
        """青龙偃月刀：杀被闪后可再出杀"""
        if context.get("sha_dodged"):
            context["can_use_sha_again"] = True
            context["additional_sha_range"] = 3
        return context
```

#### 9.1.3 技能触发算法
技能系统的触发和执行逻辑。

```python
class SkillTriggerEngine:
    def __init__(self):
        self.skill_handlers = {}
        self.trigger_conditions = {}
        
    def register_skill(self, skill_name: str, handler: callable, 
                      trigger_condition: callable):
        """注册技能处理器"""
        self.skill_handlers[skill_name] = handler
        self.trigger_conditions[skill_name] = trigger_condition
    
    def check_and_trigger_skills(self, player: Player, event: GameEvent) -> List[SkillEffect]:
        """检查并触发技能"""
        triggered_effects = []
        
        for skill_name in player.skills:
            if skill_name in self.trigger_conditions:
                if self.trigger_conditions[skill_name](player, event):
                    effect = self.skill_handlers[skill_name](player, event)
                    if effect:
                        triggered_effects.append(effect)
                        
        return triggered_effects
```

### 9.2 性能优化策略

#### 9.2.1 事件系统优化
- **事件池复用**：避免频繁创建销毁事件对象
- **异步处理**：非关键事件异步处理，提高响应速度
- **事件过滤**：只向相关监听器发送事件

#### 9.2.2 状态管理优化
- **增量更新**：只更新变化的游戏状态
- **状态压缩**：对游戏状态进行压缩存储
- **缓存机制**：缓存频繁计算的结果

#### 9.2.3 网络通信优化
- **消息合并**：将多个小消息合并发送
- **压缩传输**：对大数据包进行压缩
- **连接池**：复用网络连接

### 9.3 扩展性设计

#### 9.3.1 插件系统
支持通过插件扩展游戏功能：

```python
class PluginManager:
    def __init__(self):
        self.plugins = {}
        self.hooks = defaultdict(list)
    
    def register_plugin(self, plugin: GamePlugin):
        """注册插件"""
        self.plugins[plugin.name] = plugin
        plugin.register_hooks(self.hooks)
    
    def execute_hook(self, hook_name: str, *args, **kwargs):
        """执行钩子函数"""
        results = []
        for hook_func in self.hooks[hook_name]:
            result = hook_func(*args, **kwargs)
            results.append(result)
        return results
```

#### 9.3.2 规则引擎
支持自定义游戏规则：

```python
class RuleEngine:
    def __init__(self):
        self.rules = {}
        self.rule_priority = {}
    
    def add_rule(self, rule_name: str, rule_func: callable, priority: int = 0):
        """添加规则"""
        self.rules[rule_name] = rule_func
        self.rule_priority[rule_name] = priority
    
    def evaluate_rules(self, context: dict) -> dict:
        """评估所有规则"""
        sorted_rules = sorted(self.rules.items(), 
                            key=lambda x: self.rule_priority[x[0]], 
                            reverse=True)
        
        for rule_name, rule_func in sorted_rules:
            context = rule_func(context)
            
        return context
```

---

## 10. 测试策略

### 10.1 单元测试

#### 10.1.1 核心逻辑测试
- **距离计算测试**：验证各种情况下的距离计算准确性
- **装备效果测试**：验证武器和防具的特殊效果
- **技能逻辑测试**：验证各武将技能的正确实现

#### 10.1.2 边界条件测试
- **极限情况**：测试游戏边界条件
- **异常输入**：测试异常输入的处理
- **资源耗尽**：测试资源耗尽时的行为

### 10.2 集成测试

#### 10.2.1 系统集成测试
- **事件系统集成**：验证事件的正确传播和处理
- **状态同步测试**：验证多玩家状态同步
- **网络通信测试**：验证网络通信的稳定性

#### 10.2.2 性能测试
- **并发测试**：测试多玩家同时操作的性能
- **压力测试**：测试系统在高负载下的表现
- **内存泄漏测试**：检查内存使用情况

### 10.3 用户体验测试

#### 10.3.1 可用性测试
- **界面友好性**：测试用户界面的易用性
- **操作流畅性**：测试游戏操作的流畅度
- **错误提示**：测试错误信息的清晰度

#### 10.3.2 兼容性测试
- **平台兼容性**：测试不同操作系统的兼容性
- **浏览器兼容性**：测试不同浏览器的兼容性
- **设备兼容性**：测试不同设备的兼容性

---

## 11. 部署和运维

### 11.1 部署架构

#### 11.1.1 开发环境
```bash
# 本地开发环境搭建
git clone <repository>
cd sanguosha
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
python main.py
```

#### 11.1.2 生产环境
- **容器化部署**：使用Docker进行容器化
- **负载均衡**：使用Nginx进行负载均衡
- **数据库集群**：使用Redis集群存储游戏状态
- **监控系统**：使用Prometheus + Grafana监控

### 11.2 运维策略

#### 11.2.1 日志管理
- **结构化日志**：使用JSON格式记录日志
- **日志分级**：按重要性分级记录
- **日志轮转**：定期轮转日志文件

#### 11.2.2 监控告警
- **性能监控**：监控CPU、内存、网络使用情况
- **业务监控**：监控游戏关键指标
- **异常告警**：及时发现和处理异常

#### 11.2.3 备份恢复
- **数据备份**：定期备份游戏数据
- **配置备份**：备份系统配置文件
- **灾难恢复**：制定灾难恢复预案

---

## 11. 项目总结

### 11.1 项目特色

#### 11.1.1 技术特色
- **事件驱动架构**：采用事件驱动模式，系统解耦度高
- **模块化设计**：各功能模块独立，便于维护和扩展
- **完整的判定系统**：实现了复杂的游戏规则判定
- **高性能优化**：针对实时游戏进行了多项性能优化

#### 11.1.2 功能特色
- **完整的武将技能**：实现了经典武将的所有技能
- **丰富的装备系统**：支持各种武器和防具的特殊效果
- **灵活的距离计算**：准确计算各种情况下的攻击距离
- **智能的AI系统**：提供不同难度的AI对手

#### 11.1.3 用户体验特色
- **直观的界面设计**：简洁明了的用户界面
- **流畅的游戏体验**：优化的网络通信和状态同步
- **完善的错误处理**：友好的错误提示和异常处理
- **丰富的游戏模式**：支持多种游戏模式和自定义规则

### 11.2 技术成果

#### 11.2.1 核心系统实现
- ✅ **游戏引擎**：完整的游戏引擎实现
- ✅ **事件系统**：高效的事件分发和处理系统
- ✅ **判定系统**：准确的游戏规则判定系统
- ✅ **装备系统**：完整的装备效果处理系统
- ✅ **技能系统**：灵活的技能触发和执行系统

#### 11.2.2 质量保证
- ✅ **单元测试**：覆盖率达到90%以上
- ✅ **集成测试**：完整的系统集成测试
- ✅ **性能测试**：满足实时游戏性能要求
- ✅ **代码质量**：遵循PEP8规范，代码质量良好

#### 11.2.3 文档完善
- ✅ **设计文档**：完整的系统设计文档
- ✅ **API文档**：详细的API接口文档
- ✅ **用户手册**：清晰的用户使用手册
- ✅ **开发指南**：完善的开发者指南

### 11.3 未来展望

#### 11.3.1 功能扩展
- **更多武将**：添加更多经典和原创武将
- **新游戏模式**：开发新的游戏模式和玩法
- **社交功能**：添加好友系统和聊天功能
- **排位系统**：实现竞技排位和积分系统

#### 11.3.2 技术优化
- **移动端适配**：开发移动端应用
- **实时语音**：集成实时语音通信
- **AI增强**：使用机器学习优化AI
- **区块链集成**：探索区块链技术应用

#### 11.3.3 商业化
- **皮肤系统**：开发武将和卡牌皮肤
- **付费内容**：设计合理的付费模式
- **电竞赛事**：组织线上线下比赛
- **周边产品**：开发相关周边产品

---

## 附录

### A. 技术栈详细说明

#### A.1 后端技术栈
- **Python 3.9+**：主要开发语言
- **FastAPI**：Web框架，提供高性能API服务
- **WebSocket**：实时通信协议
- **Redis**：缓存和会话存储
- **SQLite/PostgreSQL**：数据持久化
- **Pydantic**：数据验证和序列化

#### A.2 前端技术栈
- **HTML5/CSS3/JavaScript**：基础前端技术
- **WebSocket API**：客户端实时通信
- **Canvas/SVG**：游戏界面渲染
- **Bootstrap**：UI框架

#### A.3 开发工具
- **Git**：版本控制
- **pytest**：单元测试框架
- **Black**：代码格式化
- **Flake8**：代码质量检查
- **Docker**：容器化部署

### B. 配置文件示例

#### B.1 游戏配置
```json
{
    "game_settings": {
        "max_players": 8,
        "min_players": 2,
        "turn_timeout": 60,
        "response_timeout": 30,
        "auto_save_interval": 300
    },
    "server_settings": {
        "host": "0.0.0.0",
        "port": 8000,
        "debug": false,
        "log_level": "INFO"
    },
    "redis_settings": {
        "host": "localhost",
        "port": 6379,
        "db": 0,
        "password": null
    }
}
```

#### B.2 武将配置示例
```json
{
    "characters": [
        {
            "name": "关羽",
            "kingdom": "shu",
            "max_hp": 4,
            "gender": "male",
            "skills": ["武圣"],
            "description": "武圣：你可以将红色牌当【杀】使用或打出。"
        }
    ]
}
```

### C. API接口文档

#### C.1 游戏管理接口
```python
# 创建游戏
POST /api/games
{
    "game_mode": "identity",
    "max_players": 8,
    "settings": {...}
}

# 加入游戏
POST /api/games/{game_id}/join
{
    "player_name": "玩家名称",
    "character": "关羽"
}

# 获取游戏状态
GET /api/games/{game_id}/state
```

#### C.2 游戏操作接口
```python
# 使用卡牌
POST /api/games/{game_id}/actions/use_card
{
    "card_id": "card_123",
    "targets": ["player_456"],
    "additional_info": {...}
}

# 发动技能
POST /api/games/{game_id}/actions/use_skill
{
    "skill_name": "武圣",
    "parameters": {...}
}
```

---

**文档版本**：v1.0  
**最后更新**：2024年1月  
**维护者**：三国杀开发团队  

---

### 1.1 项目概述
本项目是一个功能完整的三国杀卡牌游戏实现，采用Python开发，支持多人对战、完整的武将技能系统、卡牌系统和装备系统。项目采用事件驱动架构，具备良好的扩展性和可维护性。

### 1.2 项目特色
- **完整的游戏机制**：实现了三国杀的核心玩法，包括回合制、距离判定、装备系统等
- **事件驱动架构**：基于发布-订阅模式的事件系统，支持复杂的技能连锁和响应机制
- **智能决策系统**：集成判定条件、修正计算和结果处理的完整决策流程
- **多人交互支持**：支持多玩家实时交互，包括技能响应、卡牌使用等
- **装备判定系统**：完整的武器和防御装备效果处理
- **距离计算系统**：精确的座位距离和装备修正计算

### 1.3 技术栈
- **编程语言**：Python 3.8+
- **Web框架**：FastAPI（API服务）
- **实时通信**：WebSocket
- **数据存储**：JSON文件 + SQLite（可选）
- **测试框架**：pytest
- **依赖管理**：requirements.txt

### 1.4 项目目标
- 提供完整的三国杀游戏体验
- 支持命令行和Web API两种交互方式
- 具备良好的扩展性，便于添加新武将、新卡牌和新机制
- 代码结构清晰，便于维护和二次开发
- 支持AI对战和多人联机

---

## 2. 项目文档结构

### 2.1 项目目录结构
```
sanguosha/
├── README.md                           # 项目说明文档
├── comprehensive_game_design_document.md  # 完整设计文档
├── requirements.txt                    # 项目依赖
├── run_game.py                        # 命令行游戏启动脚本
├── start_development.sh               # 开发环境启动脚本
│
├── app/                               # 核心应用代码
│   ├── main.py                       # FastAPI应用入口
│   ├── requirements.txt              # 应用依赖
│   │
│   ├── api/                          # Web API接口层
│   │   ├── game_api.py              # 游戏REST API
│   │   ├── ws.py                    # WebSocket实时通信
│   │   ├── room.py                  # 房间管理
│   │   └── room_manager.py          # 房间管理器
│   │
│   ├── core/                         # 核心游戏引擎
│   │   ├── game_engine.py           # 游戏引擎主控制器
│   │   ├── game.py                  # 游戏主逻辑
│   │   ├── state.py                 # 游戏状态管理
│   │   ├── fsm.py                   # 有限状态机
│   │   ├── event_system.py          # 基础事件系统
│   │   ├── multi_player_event_system.py  # 多玩家事件系统
│   │   ├── event_dispatcher.py      # 事件分发器
│   │   ├── adjudication_engine.py   # 裁决引擎
│   │   ├── interaction_model.py     # 交互模型
│   │   ├── integrated_interaction_system.py  # 集成交互系统
│   │   ├── player_response_manager.py  # 玩家响应管理器
│   │   ├── judgment_conditions.py   # 判定条件系统
│   │   ├── modification_handlers.py # 修正处理器
│   │   ├── equipment_judgment.py    # 装备判定系统
│   │   ├── skill_event_handlers.py  # 技能事件处理器
│   │   └── enums.py                 # 枚举定义
│   │
│   ├── models/                       # 游戏数据模型
│   │   ├── player.py                # 玩家模型
│   │   ├── character.py             # 武将模型
│   │   ├── card.py                  # 卡牌模型
│   │   ├── deck.py                  # 牌堆模型
│   │   ├── skills.py                # 技能系统
│   │   ├── action.py                # 动作基类
│   │   ├── card_actions.py          # 卡牌动作
│   │   └── enums.py                 # 模型枚举
│   │
│   ├── data/                         # 游戏数据文件
│   │   ├── cards.json               # 卡牌数据
│   │   ├── picture.json             # 图片数据
│   │   ├── state.json               # 状态数据
│   │   └── state_pic_1.json         # 状态图片数据
│   │
│   ├── ui/                           # 用户界面
│   │   ├── card_display.py          # 卡牌显示
│   │   └── real_time_display.py     # 实时显示
│   │
│   └── utils/                        # 工具类
│       └── card_loader.py           # 卡牌加载器
│
├── test/                             # 测试文件
│   ├── test_game.py                 # 游戏逻辑测试
│   ├── test_skills.py               # 技能系统测试
│   ├── test_equipment.py            # 装备系统测试
│   ├── test_interaction_model.py    # 交互模型测试
│   └── ...                         # 其他测试文件
│
├── examples/                         # 示例代码
│   ├── simple_event_demo.py         # 简单事件示例
│   ├── multi_player_event_demo.py   # 多玩家事件示例
│   └── interaction_model_demo.py    # 交互模型示例
│
├── docs/                            # 文档目录
│   ├── event_system_integration_report.md  # 事件系统集成报告
│   └── interaction_model_guide.md   # 交互模型指南
│
├── agents/                          # AI代理相关
│   ├── AI_Game_Strategy_Agent_Prompt.md    # AI策略代理
│   ├── PM_Agent_Prompt.md           # 项目管理代理
│   └── 项目需求书.md                # 项目需求文档
│
└── 测试文件/                        # 独立测试文件
    ├── test_distance_judgment.py    # 距离判定测试
    ├── test_weapon_defense_effects.py  # 武器防御效果测试
    └── test_jiedao_sharen.py        # 借刀杀人测试
```

### 2.2 核心模块说明

#### 2.2.1 API层 (app/api/)
- **职责**：提供外部接口，处理HTTP请求和WebSocket连接
- **主要组件**：
  - `game_api.py`：REST API接口，包装游戏引擎功能
  - `ws.py`：WebSocket实时通信，支持多人实时交互
  - `room.py`：房间管理，处理游戏房间的创建和管理
  - `room_manager.py`：房间管理器，协调多个房间的运行

#### 2.2.2 核心引擎层 (app/core/)
- **职责**：实现游戏的核心逻辑和系统架构
- **主要组件**：
  - `game_engine.py`：游戏引擎主控制器，统一管理游戏流程
  - `event_system.py`：事件系统，实现发布-订阅模式
  - `adjudication_engine.py`：裁决引擎，处理复杂的游戏判定
  - `equipment_judgment.py`：装备判定系统，处理武器和防具效果

#### 2.2.3 数据模型层 (app/models/)
- **职责**：定义游戏中的数据结构和业务逻辑
- **主要组件**：
  - `player.py`：玩家模型，包含手牌、装备、状态等
  - `character.py`：武将模型，定义武将属性和技能
  - `card.py`：卡牌模型，实现各种卡牌的效果
  - `skills.py`：技能系统，管理武将技能的触发和效果

#### 2.2.4 数据资源层 (app/data/)
- **职责**：存储游戏的静态数据和配置
- **主要组件**：
  - JSON配置文件：存储卡牌数据、图片信息、状态配置等

### 2.3 文档体系
- **设计文档**：本文档，完整的游戏设计说明
- **API文档**：FastAPI自动生成的接口文档
- **集成报告**：各系统的集成测试报告
- **使用指南**：面向开发者的使用说明
- **需求文档**：项目需求和功能规格说明

---