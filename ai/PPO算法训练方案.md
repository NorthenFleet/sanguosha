# PPO算法三国杀AI训练方案

## 1. 方案概述

### 1.1 PPO算法简介

PPO（Proximal Policy Optimization）是一种策略梯度方法，特别适合处理复杂的多智能体环境。在三国杀游戏中，PPO算法具有以下优势：

- **稳定性强**: 通过限制策略更新幅度，避免训练过程中的性能崩溃
- **样本效率高**: 可以重复使用收集的经验数据进行多次更新
- **适应性好**: 能够处理连续和离散动作空间的混合场景
- **实现简单**: 相比其他算法，PPO的实现和调参相对简单

### 1.2 三国杀应用特点

在三国杀游戏中，PPO算法需要处理：
- **大状态空间**: 366维状态向量
- **复杂动作空间**: 61维动作编码
- **多智能体交互**: 3-8个玩家的复杂博弈
- **不完全信息**: 隐藏手牌和未知身份
- **长期奖励**: 游戏回合数可达数百轮

## 2. 网络架构设计

### 2.1 Actor-Critic架构

```python
class PPONetwork(nn.Module):
    def __init__(self, config):
        super().__init__()
        self.config = config
        
        # 共享状态编码器
        self.state_encoder = StateEncoder(
            state_dim=config.state_dim,
            hidden_dim=config.hidden_dim,
            attention_heads=config.attention_heads
        )
        
        # Actor网络（策略网络）
        self.actor = PolicyNetwork(
            input_dim=config.hidden_dim,
            action_dim=config.action_dim,
            hidden_layers=config.actor_layers
        )
        
        # Critic网络（价值网络）
        self.critic = ValueNetwork(
            input_dim=config.hidden_dim,
            hidden_layers=config.critic_layers
        )
    
    def forward(self, state, action_mask=None):
        # 状态编码
        encoded_state = self.state_encoder(state)
        
        # 策略输出
        action_logits = self.actor(encoded_state)
        if action_mask is not None:
            action_logits = action_logits.masked_fill(~action_mask, -1e9)
        action_probs = F.softmax(action_logits, dim=-1)
        
        # 价值输出
        state_value = self.critic(encoded_state)
        
        return action_probs, state_value
```

### 2.2 网络参数配置

```python
@dataclass
class PPONetworkConfig:
    # 基础参数
    state_dim: int = 366
    action_dim: int = 61
    hidden_dim: int = 256
    attention_heads: int = 8
    
    # Actor网络层数
    actor_layers: List[int] = field(default_factory=lambda: [512, 256, 128])
    
    # Critic网络层数
    critic_layers: List[int] = field(default_factory=lambda: [512, 256, 128])
    
    # Dropout和正则化
    dropout_rate: float = 0.1
    layer_norm: bool = True
    
    # 激活函数
    activation: str = "relu"  # relu, gelu, swish
```

## 3. PPO算法实现

### 3.1 核心算法流程

```python
class PPOTrainer:
    def __init__(self, config):
        self.config = config
        self.network = PPONetwork(config)
        self.optimizer = torch.optim.Adam(
            self.network.parameters(), 
            lr=config.learning_rate
        )
        self.experience_buffer = ExperienceBuffer()
        
    def train_step(self, experiences):
        """单步PPO训练"""
        states, actions, old_log_probs, rewards, advantages, returns = experiences
        
        # 前向传播
        action_probs, values = self.network(states)
        action_dist = Categorical(action_probs)
        new_log_probs = action_dist.log_prob(actions)
        entropy = action_dist.entropy()
        
        # 计算比率
        ratio = torch.exp(new_log_probs - old_log_probs)
        
        # PPO损失计算
        surr1 = ratio * advantages
        surr2 = torch.clamp(ratio, 1 - self.config.clip_epsilon, 
                           1 + self.config.clip_epsilon) * advantages
        policy_loss = -torch.min(surr1, surr2).mean()
        
        # 价值损失
        value_loss = F.mse_loss(values.squeeze(), returns)
        
        # 熵损失（鼓励探索）
        entropy_loss = -entropy.mean()
        
        # 总损失
        total_loss = (policy_loss + 
                     self.config.value_loss_coef * value_loss + 
                     self.config.entropy_coef * entropy_loss)
        
        # 反向传播
        self.optimizer.zero_grad()
        total_loss.backward()
        torch.nn.utils.clip_grad_norm_(
            self.network.parameters(), 
            self.config.max_grad_norm
        )
        self.optimizer.step()
        
        return {
            'policy_loss': policy_loss.item(),
            'value_loss': value_loss.item(),
            'entropy_loss': entropy_loss.item(),
            'total_loss': total_loss.item()
        }
```

### 3.2 经验收集与处理

```python
class ExperienceCollector:
    def __init__(self, env, network, config):
        self.env = env
        self.network = network
        self.config = config
        
    def collect_experiences(self, num_steps):
        """收集游戏经验"""
        experiences = []
        state = self.env.reset()
        
        for step in range(num_steps):
            with torch.no_grad():
                action_probs, value = self.network(state)
                action_dist = Categorical(action_probs)
                action = action_dist.sample()
                log_prob = action_dist.log_prob(action)
            
            next_state, reward, done, info = self.env.step(action)
            
            experiences.append({
                'state': state,
                'action': action,
                'log_prob': log_prob,
                'reward': reward,
                'value': value,
                'done': done
            })
            
            state = next_state if not done else self.env.reset()
        
        return self.process_experiences(experiences)
    
    def process_experiences(self, experiences):
        """处理经验数据，计算优势和回报"""
        # 计算GAE优势
        advantages = self.compute_gae_advantages(experiences)
        
        # 计算回报
        returns = advantages + torch.tensor([exp['value'] for exp in experiences])
        
        # 标准化优势
        advantages = (advantages - advantages.mean()) / (advantages.std() + 1e-8)
        
        return {
            'states': torch.stack([exp['state'] for exp in experiences]),
            'actions': torch.stack([exp['action'] for exp in experiences]),
            'log_probs': torch.stack([exp['log_prob'] for exp in experiences]),
            'rewards': torch.tensor([exp['reward'] for exp in experiences]),
            'advantages': advantages,
            'returns': returns
        }
    
    def compute_gae_advantages(self, experiences):
        """计算GAE（Generalized Advantage Estimation）优势"""
        advantages = []
        gae = 0
        
        for i in reversed(range(len(experiences))):
            if i == len(experiences) - 1:
                next_value = 0 if experiences[i]['done'] else experiences[i]['value']
            else:
                next_value = experiences[i + 1]['value']
            
            delta = (experiences[i]['reward'] + 
                    self.config.gamma * next_value - 
                    experiences[i]['value'])
            
            gae = delta + self.config.gamma * self.config.gae_lambda * gae
            advantages.insert(0, gae)
        
        return torch.tensor(advantages)
```

## 4. 训练配置参数

### 4.1 PPO超参数

```python
@dataclass
class PPOTrainingConfig:
    # PPO核心参数
    clip_epsilon: float = 0.2          # PPO裁剪参数
    value_loss_coef: float = 0.5       # 价值损失系数
    entropy_coef: float = 0.01         # 熵损失系数
    max_grad_norm: float = 0.5         # 梯度裁剪
    
    # GAE参数
    gamma: float = 0.99                # 折扣因子
    gae_lambda: float = 0.95           # GAE lambda参数
    
    # 训练参数
    learning_rate: float = 3e-4        # 学习率
    batch_size: int = 64               # 批次大小
    mini_batch_size: int = 16          # 小批次大小
    ppo_epochs: int = 4                # PPO更新轮数
    
    # 经验收集
    rollout_steps: int = 2048          # 每次收集步数
    num_envs: int = 8                  # 并行环境数
    
    # 学习率调度
    lr_schedule: str = "linear"        # linear, cosine, constant
    lr_decay_steps: int = 1000000      # 学习率衰减步数
```

### 4.2 三国杀特定参数

```python
@dataclass
class SanguoshaSpecificConfig:
    # 奖励函数权重
    win_reward: float = 100.0          # 胜利奖励
    lose_penalty: float = -50.0        # 失败惩罚
    survival_reward: float = 1.0       # 存活奖励
    damage_reward: float = 5.0         # 造成伤害奖励
    heal_reward: float = 3.0           # 治疗奖励
    card_efficiency_reward: float = 2.0 # 卡牌使用效率奖励
    
    # 课程学习参数
    curriculum_stages: List[Dict] = field(default_factory=lambda: [
        {"name": "basic_rules", "episodes": 10000, "opponents": "random"},
        {"name": "intermediate", "episodes": 20000, "opponents": "rule_based"},
        {"name": "advanced", "episodes": 50000, "opponents": "mixed"},
        {"name": "expert", "episodes": 100000, "opponents": "self_play"}
    ])
    
    # 动作掩码参数
    use_action_masking: bool = True     # 是否使用动作掩码
    invalid_action_penalty: float = -10.0  # 非法动作惩罚
    
    # 多智能体参数
    self_play_ratio: float = 0.3       # 自我对弈比例
    opponent_pool_size: int = 10       # 对手池大小
    update_opponent_interval: int = 1000  # 更新对手间隔
```

## 5. 训练流程实现

### 5.1 主训练循环

```python
class PPOSanguoshaTrainer:
    def __init__(self, config):
        self.config = config
        self.network = PPONetwork(config)
        self.collector = ExperienceCollector(
            env=create_sanguosha_env(config),
            network=self.network,
            config=config
        )
        self.evaluator = GameEvaluator(config)
        self.logger = TrainingLogger(config)
        
    def train(self):
        """主训练流程"""
        total_steps = 0
        best_win_rate = 0.0
        
        for episode in range(self.config.max_episodes):
            # 收集经验
            experiences = self.collector.collect_experiences(
                self.config.rollout_steps
            )
            
            # PPO更新
            for epoch in range(self.config.ppo_epochs):
                # 随机打乱数据
                indices = torch.randperm(len(experiences['states']))
                
                # 小批次训练
                for start in range(0, len(indices), self.config.mini_batch_size):
                    end = start + self.config.mini_batch_size
                    batch_indices = indices[start:end]
                    
                    batch_experiences = {
                        key: value[batch_indices] 
                        for key, value in experiences.items()
                    }
                    
                    loss_dict = self.train_step(batch_experiences)
                    self.logger.log_training_step(loss_dict, total_steps)
            
            total_steps += self.config.rollout_steps
            
            # 定期评估
            if episode % self.config.eval_interval == 0:
                eval_results = self.evaluator.evaluate(self.network)
                self.logger.log_evaluation(eval_results, episode)
                
                # 保存最佳模型
                if eval_results['win_rate'] > best_win_rate:
                    best_win_rate = eval_results['win_rate']
                    self.save_model(f"best_model_ep{episode}.pth")
            
            # 课程学习更新
            self.update_curriculum(episode)
            
            # 学习率调度
            self.update_learning_rate(total_steps)
```

### 5.2 课程学习实现

```python
class CurriculumLearning:
    def __init__(self, config):
        self.config = config
        self.current_stage = 0
        self.stage_episodes = 0
        
    def update_curriculum(self, episode):
        """更新课程学习阶段"""
        current_stage_config = self.config.curriculum_stages[self.current_stage]
        self.stage_episodes += 1
        
        # 检查是否需要进入下一阶段
        if (self.stage_episodes >= current_stage_config['episodes'] and 
            self.current_stage < len(self.config.curriculum_stages) - 1):
            
            self.current_stage += 1
            self.stage_episodes = 0
            
            print(f"进入课程学习阶段 {self.current_stage + 1}: "
                  f"{self.config.curriculum_stages[self.current_stage]['name']}")
            
            # 更新环境配置
            self.update_environment_config()
    
    def get_current_opponents(self):
        """获取当前阶段的对手类型"""
        return self.config.curriculum_stages[self.current_stage]['opponents']
    
    def update_environment_config(self):
        """根据当前阶段更新环境配置"""
        stage_config = self.config.curriculum_stages[self.current_stage]
        
        # 更新对手难度
        if stage_config['opponents'] == 'random':
            self.env.set_opponent_policy('random')
        elif stage_config['opponents'] == 'rule_based':
            self.env.set_opponent_policy('rule_based')
        elif stage_config['opponents'] == 'mixed':
            self.env.set_opponent_policy('mixed')
        elif stage_config['opponents'] == 'self_play':
            self.env.set_opponent_policy('self_play')
```

## 6. 性能优化策略

### 6.1 并行化训练

```python
class ParallelPPOTrainer:
    def __init__(self, config):
        self.config = config
        self.num_workers = config.num_envs
        
        # 创建多个环境进程
        self.envs = [
            create_sanguosha_env(config) 
            for _ in range(self.num_workers)
        ]
        
        # 共享网络参数
        self.shared_network = PPONetwork(config)
        self.shared_network.share_memory()
        
    def parallel_collect_experiences(self):
        """并行收集经验"""
        with multiprocessing.Pool(self.num_workers) as pool:
            # 每个进程收集一部分经验
            results = pool.map(
                self.collect_worker_experiences,
                [(i, self.config.rollout_steps // self.num_workers) 
                 for i in range(self.num_workers)]
            )
        
        # 合并所有经验
        combined_experiences = self.combine_experiences(results)
        return combined_experiences
    
    def collect_worker_experiences(self, args):
        """单个工作进程收集经验"""
        worker_id, steps_per_worker = args
        env = self.envs[worker_id]
        
        experiences = []
        state = env.reset()
        
        for step in range(steps_per_worker):
            with torch.no_grad():
                action_probs, value = self.shared_network(state)
                action_dist = Categorical(action_probs)
                action = action_dist.sample()
                log_prob = action_dist.log_prob(action)
            
            next_state, reward, done, info = env.step(action)
            
            experiences.append({
                'state': state,
                'action': action,
                'log_prob': log_prob,
                'reward': reward,
                'value': value,
                'done': done
            })
            
            state = next_state if not done else env.reset()
        
        return experiences
```

### 6.2 内存优化

```python
class MemoryOptimizedPPO:
    def __init__(self, config):
        self.config = config
        self.gradient_accumulation_steps = config.gradient_accumulation_steps
        
    def train_with_gradient_accumulation(self, experiences):
        """使用梯度累积的训练"""
        total_loss = 0
        self.optimizer.zero_grad()
        
        # 分批处理以节省内存
        batch_size = len(experiences['states'])
        mini_batch_size = batch_size // self.gradient_accumulation_steps
        
        for i in range(self.gradient_accumulation_steps):
            start_idx = i * mini_batch_size
            end_idx = (i + 1) * mini_batch_size
            
            mini_batch = {
                key: value[start_idx:end_idx] 
                for key, value in experiences.items()
            }
            
            # 前向传播
            loss_dict = self.compute_loss(mini_batch)
            loss = loss_dict['total_loss'] / self.gradient_accumulation_steps
            
            # 反向传播（累积梯度）
            loss.backward()
            total_loss += loss.item()
        
        # 梯度裁剪和参数更新
        torch.nn.utils.clip_grad_norm_(
            self.network.parameters(), 
            self.config.max_grad_norm
        )
        self.optimizer.step()
        
        return {'total_loss': total_loss}
```

## 7. 评估与监控

### 7.1 训练指标监控

```python
class PPOMetricsTracker:
    def __init__(self):
        self.metrics = {
            'policy_loss': [],
            'value_loss': [],
            'entropy_loss': [],
            'clip_fraction': [],
            'kl_divergence': [],
            'explained_variance': []
        }
        
    def update_metrics(self, loss_dict, experiences):
        """更新训练指标"""
        self.metrics['policy_loss'].append(loss_dict['policy_loss'])
        self.metrics['value_loss'].append(loss_dict['value_loss'])
        self.metrics['entropy_loss'].append(loss_dict['entropy_loss'])
        
        # 计算裁剪比例
        clip_fraction = self.compute_clip_fraction(experiences)
        self.metrics['clip_fraction'].append(clip_fraction)
        
        # 计算KL散度
        kl_div = self.compute_kl_divergence(experiences)
        self.metrics['kl_divergence'].append(kl_div)
        
        # 计算解释方差
        explained_var = self.compute_explained_variance(experiences)
        self.metrics['explained_variance'].append(explained_var)
    
    def compute_clip_fraction(self, experiences):
        """计算被裁剪的比例"""
        ratio = torch.exp(experiences['new_log_probs'] - experiences['old_log_probs'])
        clip_lower = ratio < (1 - self.config.clip_epsilon)
        clip_upper = ratio > (1 + self.config.clip_epsilon)
        clip_fraction = (clip_lower | clip_upper).float().mean()
        return clip_fraction.item()
    
    def compute_kl_divergence(self, experiences):
        """计算新旧策略的KL散度"""
        kl_div = (experiences['old_log_probs'] - experiences['new_log_probs']).mean()
        return kl_div.item()
    
    def compute_explained_variance(self, experiences):
        """计算价值函数的解释方差"""
        values = experiences['values']
        returns = experiences['returns']
        
        var_returns = torch.var(returns)
        var_residual = torch.var(returns - values)
        
        if var_returns > 0:
            explained_var = 1 - var_residual / var_returns
        else:
            explained_var = 0
        
        return explained_var.item()
```

### 7.2 游戏性能评估

```python
class GamePerformanceEvaluator:
    def __init__(self, config):
        self.config = config
        self.eval_env = create_sanguosha_env(config, eval_mode=True)
        
    def evaluate_model(self, network, num_games=100):
        """评估模型游戏性能"""
        results = {
            'win_rate': 0,
            'avg_game_length': 0,
            'avg_damage_dealt': 0,
            'avg_cards_played': 0,
            'character_win_rates': {},
            'action_distribution': {}
        }
        
        total_wins = 0
        total_game_length = 0
        total_damage = 0
        total_cards = 0
        character_stats = {}
        action_counts = {}
        
        for game_id in range(num_games):
            game_result = self.play_evaluation_game(network)
            
            # 统计基础指标
            if game_result['won']:
                total_wins += 1
            
            total_game_length += game_result['game_length']
            total_damage += game_result['damage_dealt']
            total_cards += game_result['cards_played']
            
            # 统计角色胜率
            character = game_result['character']
            if character not in character_stats:
                character_stats[character] = {'games': 0, 'wins': 0}
            character_stats[character]['games'] += 1
            if game_result['won']:
                character_stats[character]['wins'] += 1
            
            # 统计动作分布
            for action, count in game_result['action_counts'].items():
                action_counts[action] = action_counts.get(action, 0) + count
        
        # 计算最终结果
        results['win_rate'] = total_wins / num_games
        results['avg_game_length'] = total_game_length / num_games
        results['avg_damage_dealt'] = total_damage / num_games
        results['avg_cards_played'] = total_cards / num_games
        
        # 计算角色胜率
        for character, stats in character_stats.items():
            results['character_win_rates'][character] = stats['wins'] / stats['games']
        
        # 计算动作分布
        total_actions = sum(action_counts.values())
        for action, count in action_counts.items():
            results['action_distribution'][action] = count / total_actions
        
        return results
    
    def play_evaluation_game(self, network):
        """进行单局评估游戏"""
        state = self.eval_env.reset()
        game_result = {
            'won': False,
            'game_length': 0,
            'damage_dealt': 0,
            'cards_played': 0,
            'character': self.eval_env.get_player_character(),
            'action_counts': {}
        }
        
        while not self.eval_env.is_done():
            with torch.no_grad():
                action_probs, _ = network(state)
                action = torch.multinomial(action_probs, 1).item()
            
            state, reward, done, info = self.eval_env.step(action)
            
            # 更新统计信息
            game_result['game_length'] += 1
            game_result['damage_dealt'] += info.get('damage_dealt', 0)
            game_result['cards_played'] += info.get('cards_played', 0)
            
            action_name = self.eval_env.get_action_name(action)
            game_result['action_counts'][action_name] = \
                game_result['action_counts'].get(action_name, 0) + 1
        
        game_result['won'] = self.eval_env.did_player_win()
        return game_result
```

## 8. 实际部署指南

### 8.1 模型保存与加载

```python
def save_ppo_model(network, optimizer, config, metrics, filepath):
    """保存PPO模型"""
    checkpoint = {
        'network_state_dict': network.state_dict(),
        'optimizer_state_dict': optimizer.state_dict(),
        'config': config,
        'training_metrics': metrics,
        'model_type': 'PPO',
        'version': '1.0',
        'timestamp': datetime.now().isoformat()
    }
    torch.save(checkpoint, filepath)

def load_ppo_model(filepath, device='cpu'):
    """加载PPO模型"""
    checkpoint = torch.load(filepath, map_location=device)
    
    # 重建网络
    config = checkpoint['config']
    network = PPONetwork(config)
    network.load_state_dict(checkpoint['network_state_dict'])
    network.to(device)
    network.eval()
    
    return network, checkpoint
```

### 8.2 推理优化

```python
class OptimizedPPOInference:
    def __init__(self, model_path, device='cpu'):
        self.device = device
        self.network, self.checkpoint = load_ppo_model(model_path, device)
        
        # 模型优化
        self.network = torch.jit.script(self.network)  # JIT编译
        
        # 预热推理
        self.warmup_inference()
    
    def warmup_inference(self):
        """预热推理以优化性能"""
        dummy_state = torch.randn(1, 366).to(self.device)
        dummy_mask = torch.ones(1, 61).bool().to(self.device)
        
        with torch.no_grad():
            for _ in range(10):
                _ = self.network(dummy_state, dummy_mask)
    
    @torch.no_grad()
    def get_action(self, game_state, legal_actions):
        """获取最优动作"""
        # 状态编码
        state_tensor = torch.tensor(game_state, dtype=torch.float32).unsqueeze(0).to(self.device)
        
        # 动作掩码
        action_mask = torch.zeros(1, 61).bool().to(self.device)
        action_mask[0, legal_actions] = True
        
        # 模型推理
        action_probs, _ = self.network(state_tensor, action_mask)
        
        # 选择动作（可以选择贪婪或采样）
        if self.use_greedy:
            action = torch.argmax(action_probs, dim=-1).item()
        else:
            action = torch.multinomial(action_probs, 1).item()
        
        return action
```

## 9. 调参建议

### 9.1 关键超参数调优

1. **clip_epsilon (0.1-0.3)**
   - 较小值：更保守的策略更新，训练稳定但可能较慢
   - 较大值：更激进的更新，可能不稳定但收敛更快
   - 建议：从0.2开始，根据训练稳定性调整

2. **learning_rate (1e-5 - 1e-3)**
   - 三国杀复杂环境建议使用较小学习率
   - 建议：3e-4，配合学习率衰减

3. **ppo_epochs (3-10)**
   - 每批经验的重复使用次数
   - 过多可能导致过拟合，过少可能样本效率低
   - 建议：4-6次

4. **batch_size & mini_batch_size**
   - batch_size建议2048-4096
   - mini_batch_size建议64-256
   - 需要根据GPU内存调整

### 9.2 三国杀特定调优

1. **奖励函数权重**
   - 胜利奖励应该显著高于其他奖励
   - 避免稀疏奖励，增加中间奖励
   - 根据游戏表现动态调整权重

2. **课程学习进度**
   - 初期对手应该足够简单让AI学会基本规则
   - 逐步增加对手难度
   - 监控胜率，避免难度跳跃过大

3. **动作掩码**
   - 必须使用动作掩码避免非法动作
   - 非法动作惩罚要足够大
   - 考虑软掩码而非硬掩码

## 10. 常见问题与解决方案

### 10.1 训练不稳定

**问题**: 训练过程中性能波动大，甚至出现性能崩溃

**解决方案**:
- 降低学习率
- 减小clip_epsilon
- 增加价值损失系数
- 使用梯度裁剪
- 检查奖励函数设计

### 10.2 收敛速度慢

**问题**: 训练很长时间仍无明显改善

**解决方案**:
- 检查奖励函数是否过于稀疏
- 增加熵系数鼓励探索
- 调整课程学习进度
- 使用预训练模型
- 增加网络容量

### 10.3 过拟合问题

**问题**: 训练集表现好但泛化能力差

**解决方案**:
- 增加对手多样性
- 使用Dropout和正则化
- 减少PPO更新轮数
- 增加经验收集的随机性
- 定期评估不同对手

这个PPO训练方案提供了完整的实现框架，可以直接用于开发三国杀AI的训练代码。接下来我将创建DQN和A3C的训练方案。