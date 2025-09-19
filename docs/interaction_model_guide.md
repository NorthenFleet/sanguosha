# 三国杀通用交互模型使用指南

## 概述

本文档介绍三国杀游戏中实现的"判断-修正-裁决"三阶段通用交互模型。该模型能够处理所有游戏中的卡牌使用、技能触发、伤害计算等复杂交互逻辑。

## 核心架构

### 三阶段处理流程

```
输入交互请求 → 判断阶段 → 修正阶段 → 裁决阶段 → 输出最终结果
```

1. **判断阶段（Judgment Phase）**：检查交互是否满足基本条件
2. **修正阶段（Modification Phase）**：处理各种响应、技能效果和修正
3. **裁决阶段（Adjudication Phase）**：计算最终结果并执行效果

## 核心组件

### 1. 交互上下文（InteractionContext）

```python
from app.core.interaction.interaction_model import InteractionContext, InteractionType

context = InteractionContext(
    interaction_type=InteractionType.CARD_USE,
    source_player=player1,
    target_player=player2,
    card=sha_card,
    amount=1
)
```

### 2. 交互引擎（InteractionEngine）

```python
from app.core.interaction.interaction_model import InteractionEngine

engine = InteractionEngine()
result = engine.process_interaction(context)
```

### 3. 集成交互系统（IntegratedInteractionSystem）

```python
from app.core.integrated_interaction_system import EnhancedGameEngine

game_engine = EnhancedGameEngine()
game_id = game_engine.create_game("曹操", "刘备")

# 使用卡牌
result = game_engine.use_card(game_id, player_index=0, card_name="杀", target_index=1)

# 使用技能
result = game_engine.use_skill(game_id, player_index=0, skill_name="奸雄")

# 处理伤害
result = game_engine.interaction_system.process_damage(game_id, source_index=0, target_index=1, damage=2)
```

## 扩展指南

### 添加新的判断条件

```python
from app.core.adjudication.judgment_conditions import default_judgment_registry

def can_use_new_card(context):
    # 实现判断逻辑
    return True

# 注册条件
default_judgment_registry.register_condition("use_new_card", can_use_new_card)
```

### 添加新的修正处理器

```python
from app.core.adjudication.modification_handlers import ModificationHandler, ModificationPriority, ModificationResult

class NewSkillHandler(ModificationHandler):
    def __init__(self):
        super().__init__(ModificationPriority.HIGH)
    
    def can_handle(self, context):
        # 判断是否能处理此交互
        return context.skill == "新技能"
    
    def handle(self, context):
        # 实现修正逻辑
        return ModificationResult(
            success=True,
            modified_context=context,
            description="新技能效果"
        )

# 注册处理器
from app.core.adjudication.modification_handlers import ModificationEngine
engine = ModificationEngine()
engine.register_handler(NewSkillHandler())
```

### 添加新的裁决处理器

```python
from app.core.interaction.interaction_model import InteractionType, InteractionResult

def new_interaction_resolution(context):
    # 实现裁决逻辑
    return InteractionResult.SUCCESS

# 注册裁决处理器
engine.resolution_phase.add_resolution_handler(
    InteractionType.SKILL_USE, 
    new_interaction_resolution
)
```

## 交互类型

系统支持以下交互类型：

- `CARD_USE`: 使用卡牌
- `CARD_PLAY`: 打出卡牌
- `SKILL_TRIGGER`: 技能触发
- `SKILL_USE`: 主动使用技能
- `DAMAGE`: 造成伤害
- `HEAL`: 回复体力
- `DRAW_CARD`: 摸牌
- `DISCARD_CARD`: 弃牌

## 修正优先级

修正处理器按以下优先级执行：

1. `HIGHEST`: 锁定技等最高优先级效果
2. `HIGH`: 主动技能
3. `NORMAL`: 装备效果
4. `LOW`: 被动效果
5. `LOWEST`: 默认规则

## 使用示例

### 基本卡牌使用

```python
# 创建游戏
engine = EnhancedGameEngine()
game_id = engine.create_game("曹操", "刘备")

# 使用杀
result = engine.use_card(game_id, 0, "杀", 1)
print(f"结果: {result['success']}")
print(f"摘要: {result['summary']}")
```

### 技能使用

```python
# 使用奸雄技能
result = engine.use_skill(game_id, 0, "奸雄")
print(f"技能使用结果: {result}")
```

### 伤害处理

```python
# 处理伤害
result = engine.interaction_system.process_damage(game_id, 0, 1, 2)
summary = engine.interaction_system.adjudication_engine.create_summary(result)
print(f"伤害结果: {summary}")
```

## 调试和日志

系统提供详细的日志记录：

```python
import logging
logging.basicConfig(level=logging.INFO)

# 运行交互时会输出详细日志
result = engine.use_card(game_id, 0, "杀", 1)
```

## 测试

运行测试验证系统功能：

```bash
# 运行交互模型测试
python test/test_interaction_model.py

# 运行演示程序
python examples/interaction_model_demo.py
```

## 最佳实践

1. **条件检查**：在判断阶段进行充分的条件检查
2. **优先级设置**：合理设置修正处理器的优先级
3. **错误处理**：在各阶段添加适当的错误处理
4. **日志记录**：使用日志记录关键交互过程
5. **测试覆盖**：为新功能编写充分的测试

## 常见问题

### Q: 如何处理复杂的技能交互？
A: 通过修正阶段的多个处理器协作，按优先级顺序处理各种效果。

### Q: 如何确保交互的正确性？
A: 系统提供三阶段验证，每个阶段都有相应的检查机制。

### Q: 如何扩展新的卡牌类型？
A: 添加相应的判断条件、修正处理器和裁决处理器即可。

## 总结

三国杀通用交互模型提供了一个灵活、可扩展的框架来处理游戏中的各种复杂交互。通过三阶段处理机制，系统能够准确处理卡牌使用、技能触发、响应处理等各种游戏逻辑。