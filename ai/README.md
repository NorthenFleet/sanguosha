# 三国杀AI决策智能体

基于深度神经网络和PPO算法的三国杀决策智能体，支持自对弈训练和分布式训练。

## 功能特性

### 🧠 智能决策
- **深度神经网络**: 使用Actor-Critic架构，支持注意力机制
- **PPO算法**: 稳定的策略梯度算法，适合复杂游戏环境
- **状态编码**: 完整的游戏状态向量化表示
- **动作掩码**: 智能过滤无效动作，提升训练效率

### 🎯 训练模式
- **单智能体训练**: 基础训练模式，适合初期开发
- **自对弈训练**: 智能体池管理，策略多样性保证
- **分布式训练**: 多进程并行训练，大幅提升训练效率
- **人机对战**: 与训练好的AI进行实时对战

### 🏆 奖励系统
- **多维度奖励**: 生存、伤害、手牌优势、装备、策略等
- **自适应调整**: 根据AI表现动态调整奖励参数
- **游戏评估**: 全面的游戏状态分析和评估机制

## 快速开始

### 1. 环境准备

```bash
# 安装依赖
pip install torch torchvision numpy matplotlib tensorboard

# 确保项目结构正确
cd /path/to/sanguosha
```

### 2. 基础训练

```bash
# 单智能体训练
python ai/main_trainer.py --mode single

# 使用自定义配置
python ai/main_trainer.py --mode single --config ai/config/default_config.json
```

### 3. 自对弈训练

```bash
# 自对弈训练（推荐）
python ai/main_trainer.py --mode self_play --config ai/config/default_config.json
```

### 4. 分布式训练

```bash
# 分布式训练（高性能）
python ai/main_trainer.py --mode distributed --config ai/config/default_config.json
```

### 5. 人机对战

```bash
# 加载训练好的模型进行对战
python ai/main_trainer.py --mode play --model models/experiments/best_model.pth
```

## 配置说明

### PPO参数
```json
{
  "ppo": {
    "learning_rate": 3e-4,      // 学习率
    "gamma": 0.99,              // 折扣因子
    "gae_lambda": 0.95,         // GAE参数
    "clip_epsilon": 0.2,        // PPO裁剪参数
    "value_coef": 0.5,          // 价值函数系数
    "entropy_coef": 0.01,       // 熵正则化系数
    "batch_size": 256,          // 批次大小
    "mini_batch_size": 64,      // 小批次大小
    "epochs": 4                 // 每次更新的轮数
  }
}
```

### 训练参数
```json
{
  "training": {
    "max_episodes": 50000,      // 最大训练轮数
    "max_steps_per_episode": 200, // 每轮最大步数
    "eval_interval": 1000,      // 评估间隔
    "save_interval": 5000,      // 保存间隔
    "num_players": 3            // 游戏玩家数
  }
}
```

### 奖励系统
```json
{
  "reward": {
    "survival_weight": 1.0,     // 生存奖励权重
    "damage_weight": 0.8,       // 伤害奖励权重
    "card_advantage_weight": 0.3, // 手牌优势权重
    "equipment_weight": 0.2,    // 装备奖励权重
    "win_reward": 10.0,         // 获胜奖励
    "lose_penalty": -5.0        // 失败惩罚
  }
}
```

### 分布式配置
```json
{
  "distributed": {
    "enabled": true,            // 启用分布式
    "world_size": 4,            // 总进程数
    "num_workers": 3,           // 工作进程数
    "num_learners": 1,          // 学习进程数
    "backend": "nccl",          // 通信后端
    "sync_interval": 100        // 同步间隔
  }
}
```

## 架构说明

### 核心组件

1. **GameStateEncoder** (`game_state_encoder.py`)
   - 游戏状态向量化
   - 卡牌、装备、技能编码
   - 动作掩码生成

2. **Neural Networks** (`neural_networks.py`)
   - Actor-Critic网络架构
   - 注意力机制支持
   - 多种网络类型选择

3. **PPO Agent** (`ppo_agent.py`)
   - PPO算法实现
   - 经验缓冲区管理
   - 策略和价值网络更新

4. **Training Environment** (`training_environment.py`)
   - 游戏环境封装
   - 奖励计算接口
   - 多智能体支持

5. **Reward System** (`reward_system.py`)
   - 多维度奖励计算
   - 游戏状态分析
   - 自适应奖励调整

6. **Self-Play Trainer** (`self_play_trainer.py`)
   - 智能体池管理
   - 策略多样性保证
   - 自对弈训练循环

7. **Distributed PPO** (`distributed_ppo.py`)
   - 参数服务器架构
   - 多进程并行训练
   - 异步梯度更新

### 训练流程

```
1. 初始化环境和智能体
2. 收集游戏经验
3. 计算优势函数和回报
4. 更新策略和价值网络
5. 评估智能体性能
6. 保存最佳模型
7. 重复步骤2-6
```

### 自对弈流程

```
1. 维护智能体池
2. 选择对手进行对战
3. 收集对战数据
4. 更新智能体策略
5. 评估智能体强度
6. 更新智能体池
7. 重复步骤2-6
```

## 性能优化

### 训练加速
- **分布式训练**: 多进程并行，提升3-4倍训练速度
- **动态批处理**: 根据性能动态调整批次大小
- **梯度累积**: 减少通信开销，提升训练稳定性
- **异步更新**: 参数服务器异步更新，减少等待时间

### 内存优化
- **经验缓冲区**: 循环缓冲区，控制内存使用
- **状态压缩**: 高效的状态编码，减少存储空间
- **梯度检查点**: 减少前向传播内存占用

### 网络优化
- **注意力机制**: 关注重要信息，提升决策质量
- **残差连接**: 缓解梯度消失，加速收敛
- **批归一化**: 稳定训练过程，提升泛化能力

## 评估指标

### 训练指标
- **Episode Reward**: 每轮游戏奖励
- **Win Rate**: 对战胜率
- **Policy Loss**: 策略损失
- **Value Loss**: 价值损失
- **Entropy**: 策略熵（探索程度）

### 性能指标
- **Training Speed**: 训练速度（episodes/hour）
- **Convergence Time**: 收敛时间
- **Memory Usage**: 内存使用量
- **GPU Utilization**: GPU利用率

### 游戏指标
- **Average Game Length**: 平均游戏长度
- **Action Diversity**: 动作多样性
- **Strategy Complexity**: 策略复杂度

## 故障排除

### 常见问题

1. **CUDA内存不足**
   ```bash
   # 减少批次大小
   "batch_size": 128,
   "mini_batch_size": 32
   ```

2. **训练不收敛**
   ```bash
   # 调整学习率和裁剪参数
   "learning_rate": 1e-4,
   "clip_epsilon": 0.1
   ```

3. **分布式训练失败**
   ```bash
   # 检查网络配置
   "backend": "gloo",  # 使用CPU后端
   "master_addr": "127.0.0.1"
   ```

### 调试技巧

1. **启用详细日志**
   ```python
   logging.basicConfig(level=logging.DEBUG)
   ```

2. **可视化训练过程**
   ```bash
   tensorboard --logdir models/experiments/logs
   ```

3. **检查模型输出**
   ```python
   # 在训练脚本中添加
   print(f"Action probs: {action_probs}")
   print(f"Value: {value}")
   ```

## 扩展开发

### 添加新的奖励函数
```python
# 在 reward_system.py 中添加
def custom_reward(self, game_state, action, next_state):
    # 自定义奖励逻辑
    return reward_value
```

### 自定义网络架构
```python
# 在 neural_networks.py 中添加
class CustomNetwork(nn.Module):
    def __init__(self, state_dim, action_dim):
        # 自定义网络结构
        pass
```

### 新的训练策略
```python
# 继承 SelfPlayTrainer
class CustomTrainer(SelfPlayTrainer):
    def custom_training_loop(self):
        # 自定义训练逻辑
        pass
```

## 贡献指南

1. Fork项目
2. 创建特性分支
3. 提交更改
4. 创建Pull Request

## 许可证

MIT License

## 联系方式

如有问题或建议，请提交Issue或联系开发团队。

---

## 通用训练脚本与评估

### 通用训练脚本（推荐）

统一入口，简化算法切换与参数管理：

```bash
# 选择算法：ppo / dqn / a3c
python ai/scripts/train_rl.py --algorithm ppo --episodes 20000 --self_play --eval_interval 1000
python ai/scripts/train_rl.py --algorithm dqn --episodes 30000 --eval_interval 1000 --save_interval 5000
python ai/scripts/train_rl.py --algorithm a3c --episodes 100000 --num_workers 8 --eval_interval 5000

# 指定日志与模型目录
python ai/scripts/train_rl.py --algorithm ppo --log_dir logs --model_dir models

# 指定外部配置（JSON/YAML），并与CLI覆盖合并
python ai/scripts/train_rl.py --algorithm ppo --config ai/config/default_config.json
```

训练过程会在控制台与日志中显示关键指标：
- PPO：`Reward`、`Length`、`WinRate`、`PolicyLoss`、`ValueLoss`、`Entropy`。
- DQN：`Reward`、`Length`、`WinRate`、`Loss`、`AvgQValue`、`TDError`、`Epsilon`。
- A3C：`ActorLoss`、`CriticLoss`、`EntropyLoss`、`EpisodeReward`、`EpisodeLength`（worker聚合）。

日志与模型输出位置默认：
- 日志：`logs/<algo>/<experiment>.log`
- 模型：`models/<algo>/`（包含最佳模型与检查点）

可视化建议：
- 在配置中启用 `use_wandb: true` 使用 Weights & Biases 实时追踪。
- 使用训练工具模块生成 `metrics.json` 与 `training_metrics.png` 离线查看。

### 脚本化评估

使用通用评估脚本对不同算法的模型进行评估：

```bash
# 选择算法并提供模型文件
python ai/scripts/evaluate_rl.py --algorithm dqn --model models/dqn/best_model.pth
python ai/scripts/evaluate_rl.py --algorithm a3c --model models/a3c/best_model.pth

# 可选评估配置（例如对局数量、对手类型等）
python ai/scripts/evaluate_rl.py --algorithm ppo --config ai/config/eval_config.yaml
```

评估脚本将输出主要指标（胜率、平均奖励、回合长度等），并可生成报告与图表（详见 `ai/evaluation/evaluation_system.py`）。