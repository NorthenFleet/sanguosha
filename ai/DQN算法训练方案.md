# DQN算法三国杀AI训练方案

## 1. 方案概述

### 1.1 DQN算法简介

DQN（Deep Q-Network）是将深度学习与Q-Learning结合的强化学习算法，特别适合处理大状态空间的决策问题。在三国杀游戏中，DQN算法具有以下特点：

- **价值函数学习**: 直接学习状态-动作价值函数Q(s,a)
- **经验回放**: 通过经验池提高样本利用效率
- **目标网络**: 使用固定目标网络稳定训练过程
- **ε-贪婪探索**: 平衡探索与利用的策略

### 1.2 三国杀应用优势

在三国杀游戏中，DQN算法的优势包括：
- **离散动作空间**: 天然适合三国杀的离散动作选择
- **样本效率**: 经验回放机制提高数据利用率
- **稳定性**: 目标网络机制减少训练震荡
- **可解释性**: Q值可以直观反映动作价值

## 2. 网络架构设计

### 2.1 DQN网络结构

```python
class DQNNetwork(nn.Module):
    def __init__(self, config):
        super().__init__()
        self.config = config
        
        # 状态编码器（与PPO共享）
        self.state_encoder = StateEncoder(
            state_dim=config.state_dim,
            hidden_dim=config.hidden_dim,
            attention_heads=config.attention_heads
        )
        
        # Q值网络
        self.q_network = nn.Sequential(
            nn.Linear(config.hidden_dim, config.q_hidden_layers[0]),
            nn.ReLU(),
            nn.Dropout(config.dropout_rate),
            
            nn.Linear(config.q_hidden_layers[0], config.q_hidden_layers[1]),
            nn.ReLU(),
            nn.Dropout(config.dropout_rate),
            
            nn.Linear(config.q_hidden_layers[1], config.q_hidden_layers[2]),
            nn.ReLU(),
            nn.Dropout(config.dropout_rate),
            
            # 输出层：每个动作的Q值
            nn.Linear(config.q_hidden_layers[2], config.action_dim)
        )
        
        # 优势网络（Dueling DQN）
        if config.use_dueling:
            self.value_stream = nn.Sequential(
                nn.Linear(config.hidden_dim, config.value_hidden_dim),
                nn.ReLU(),
                nn.Linear(config.value_hidden_dim, 1)
            )
            
            self.advantage_stream = nn.Sequential(
                nn.Linear(config.hidden_dim, config.advantage_hidden_dim),
                nn.ReLU(),
                nn.Linear(config.advantage_hidden_dim, config.action_dim)
            )
    
    def forward(self, state, action_mask=None):
        # 状态编码
        encoded_state = self.state_encoder(state)
        
        if self.config.use_dueling:
            # Dueling DQN架构
            value = self.value_stream(encoded_state)
            advantage = self.advantage_stream(encoded_state)
            
            # Q(s,a) = V(s) + A(s,a) - mean(A(s,a))
            q_values = value + advantage - advantage.mean(dim=-1, keepdim=True)
        else:
            # 标准DQN架构
            q_values = self.q_network(encoded_state)
        
        # 应用动作掩码
        if action_mask is not None:
            q_values = q_values.masked_fill(~action_mask, -1e9)
        
        return q_values
```

### 2.2 网络配置参数

```python
@dataclass
class DQNNetworkConfig:
    # 基础参数
    state_dim: int = 366
    action_dim: int = 61
    hidden_dim: int = 256
    attention_heads: int = 8
    
    # Q网络层数
    q_hidden_layers: List[int] = field(default_factory=lambda: [512, 256, 128])
    
    # Dueling DQN参数
    use_dueling: bool = True
    value_hidden_dim: int = 256
    advantage_hidden_dim: int = 256
    
    # 正则化参数
    dropout_rate: float = 0.1
    layer_norm: bool = True
    
    # 激活函数
    activation: str = "relu"
    
    # 网络初始化
    init_method: str = "xavier_uniform"  # xavier_uniform, kaiming_normal
```

## 3. DQN算法实现

### 3.1 核心算法流程

```python
class DQNTrainer:
    def __init__(self, config):
        self.config = config
        
        # 主网络和目标网络
        self.q_network = DQNNetwork(config)
        self.target_network = DQNNetwork(config)
        
        # 初始化目标网络
        self.target_network.load_state_dict(self.q_network.state_dict())
        self.target_network.eval()
        
        # 优化器
        self.optimizer = torch.optim.Adam(
            self.q_network.parameters(),
            lr=config.learning_rate,
            weight_decay=config.weight_decay
        )
        
        # 经验回放池
        self.replay_buffer = ExperienceReplayBuffer(config.buffer_size)
        
        # 探索策略
        self.epsilon_scheduler = EpsilonScheduler(config)
        
        # 训练统计
        self.training_step = 0
        self.target_update_counter = 0
    
    def select_action(self, state, legal_actions, training=True):
        """选择动作（ε-贪婪策略）"""
        if training and random.random() < self.epsilon_scheduler.get_epsilon():
            # 随机探索
            return random.choice(legal_actions)
        else:
            # 贪婪选择
            with torch.no_grad():
                state_tensor = torch.tensor(state, dtype=torch.float32).unsqueeze(0)
                action_mask = torch.zeros(1, self.config.action_dim).bool()
                action_mask[0, legal_actions] = True
                
                q_values = self.q_network(state_tensor, action_mask)
                action = torch.argmax(q_values, dim=-1).item()
                
                return action
    
    def train_step(self):
        """单步DQN训练"""
        if len(self.replay_buffer) < self.config.min_buffer_size:
            return None
        
        # 从经验池采样
        batch = self.replay_buffer.sample(self.config.batch_size)
        states, actions, rewards, next_states, dones, action_masks, next_action_masks = batch
        
        # 当前Q值
        current_q_values = self.q_network(states, action_masks)
        current_q_values = current_q_values.gather(1, actions.unsqueeze(1)).squeeze(1)
        
        # 目标Q值计算
        with torch.no_grad():
            if self.config.use_double_dqn:
                # Double DQN
                next_actions = torch.argmax(
                    self.q_network(next_states, next_action_masks), 
                    dim=-1
                )
                next_q_values = self.target_network(next_states, next_action_masks)
                next_q_values = next_q_values.gather(1, next_actions.unsqueeze(1)).squeeze(1)
            else:
                # 标准DQN
                next_q_values = torch.max(
                    self.target_network(next_states, next_action_masks), 
                    dim=-1
                )[0]
            
            target_q_values = rewards + (self.config.gamma * next_q_values * (1 - dones))
        
        # 计算损失
        if self.config.loss_function == 'mse':
            loss = F.mse_loss(current_q_values, target_q_values)
        elif self.config.loss_function == 'huber':
            loss = F.smooth_l1_loss(current_q_values, target_q_values)
        else:
            raise ValueError(f"Unknown loss function: {self.config.loss_function}")
        
        # 反向传播
        self.optimizer.zero_grad()
        loss.backward()
        
        # 梯度裁剪
        if self.config.max_grad_norm > 0:
            torch.nn.utils.clip_grad_norm_(
                self.q_network.parameters(), 
                self.config.max_grad_norm
            )
        
        self.optimizer.step()
        
        # 更新目标网络
        self.target_update_counter += 1
        if self.target_update_counter % self.config.target_update_frequency == 0:
            self.update_target_network()
        
        # 更新探索率
        self.epsilon_scheduler.step()
        
        self.training_step += 1
        
        return {
            'loss': loss.item(),
            'q_values_mean': current_q_values.mean().item(),
            'target_q_mean': target_q_values.mean().item(),
            'epsilon': self.epsilon_scheduler.get_epsilon()
        }
    
    def update_target_network(self):
        """更新目标网络"""
        if self.config.soft_update:
            # 软更新
            tau = self.config.tau
            for target_param, main_param in zip(
                self.target_network.parameters(), 
                self.q_network.parameters()
            ):
                target_param.data.copy_(
                    tau * main_param.data + (1.0 - tau) * target_param.data
                )
        else:
            # 硬更新
            self.target_network.load_state_dict(self.q_network.state_dict())
```

### 3.2 经验回放机制

```python
class ExperienceReplayBuffer:
    def __init__(self, capacity):
        self.capacity = capacity
        self.buffer = []
        self.position = 0
    
    def push(self, state, action, reward, next_state, done, action_mask, next_action_mask):
        """添加经验到缓冲区"""
        if len(self.buffer) < self.capacity:
            self.buffer.append(None)
        
        self.buffer[self.position] = (
            state, action, reward, next_state, done, action_mask, next_action_mask
        )
        self.position = (self.position + 1) % self.capacity
    
    def sample(self, batch_size):
        """从缓冲区采样批次数据"""
        batch = random.sample(self.buffer, batch_size)
        
        states = torch.stack([torch.tensor(exp[0], dtype=torch.float32) for exp in batch])
        actions = torch.tensor([exp[1] for exp in batch], dtype=torch.long)
        rewards = torch.tensor([exp[2] for exp in batch], dtype=torch.float32)
        next_states = torch.stack([torch.tensor(exp[3], dtype=torch.float32) for exp in batch])
        dones = torch.tensor([exp[4] for exp in batch], dtype=torch.float32)
        action_masks = torch.stack([torch.tensor(exp[5], dtype=torch.bool) for exp in batch])
        next_action_masks = torch.stack([torch.tensor(exp[6], dtype=torch.bool) for exp in batch])
        
        return states, actions, rewards, next_states, dones, action_masks, next_action_masks
    
    def __len__(self):
        return len(self.buffer)

class PrioritizedExperienceReplay:
    """优先经验回放"""
    def __init__(self, capacity, alpha=0.6, beta=0.4, beta_increment=0.001):
        self.capacity = capacity
        self.alpha = alpha
        self.beta = beta
        self.beta_increment = beta_increment
        
        self.buffer = []
        self.priorities = np.zeros((capacity,), dtype=np.float32)
        self.position = 0
        self.max_priority = 1.0
    
    def push(self, state, action, reward, next_state, done, action_mask, next_action_mask):
        """添加经验（使用最大优先级）"""
        if len(self.buffer) < self.capacity:
            self.buffer.append(None)
        
        self.buffer[self.position] = (
            state, action, reward, next_state, done, action_mask, next_action_mask
        )
        self.priorities[self.position] = self.max_priority
        self.position = (self.position + 1) % self.capacity
    
    def sample(self, batch_size):
        """基于优先级采样"""
        if len(self.buffer) == self.capacity:
            priorities = self.priorities
        else:
            priorities = self.priorities[:self.position]
        
        # 计算采样概率
        probs = priorities ** self.alpha
        probs /= probs.sum()
        
        # 采样索引
        indices = np.random.choice(len(self.buffer), batch_size, p=probs)
        
        # 计算重要性采样权重
        weights = (len(self.buffer) * probs[indices]) ** (-self.beta)
        weights /= weights.max()
        
        # 提取经验
        batch = [self.buffer[idx] for idx in indices]
        
        states = torch.stack([torch.tensor(exp[0], dtype=torch.float32) for exp in batch])
        actions = torch.tensor([exp[1] for exp in batch], dtype=torch.long)
        rewards = torch.tensor([exp[2] for exp in batch], dtype=torch.float32)
        next_states = torch.stack([torch.tensor(exp[3], dtype=torch.float32) for exp in batch])
        dones = torch.tensor([exp[4] for exp in batch], dtype=torch.float32)
        action_masks = torch.stack([torch.tensor(exp[5], dtype=torch.bool) for exp in batch])
        next_action_masks = torch.stack([torch.tensor(exp[6], dtype=torch.bool) for exp in batch])
        weights = torch.tensor(weights, dtype=torch.float32)
        
        # 更新beta
        self.beta = min(1.0, self.beta + self.beta_increment)
        
        return states, actions, rewards, next_states, dones, action_masks, next_action_masks, weights, indices
    
    def update_priorities(self, indices, td_errors):
        """更新优先级"""
        priorities = np.abs(td_errors) + 1e-6  # 避免零优先级
        for idx, priority in zip(indices, priorities):
            self.priorities[idx] = priority
            self.max_priority = max(self.max_priority, priority)
```

### 3.3 探索策略

```python
class EpsilonScheduler:
    """ε-贪婪探索策略调度器"""
    def __init__(self, config):
        self.config = config
        self.epsilon = config.epsilon_start
        self.step_count = 0
    
    def get_epsilon(self):
        """获取当前探索率"""
        return self.epsilon
    
    def step(self):
        """更新探索率"""
        self.step_count += 1
        
        if self.config.epsilon_schedule == 'linear':
            # 线性衰减
            decay_steps = self.config.epsilon_decay_steps
            if self.step_count < decay_steps:
                self.epsilon = (
                    self.config.epsilon_start - 
                    (self.config.epsilon_start - self.config.epsilon_end) * 
                    self.step_count / decay_steps
                )
            else:
                self.epsilon = self.config.epsilon_end
                
        elif self.config.epsilon_schedule == 'exponential':
            # 指数衰减
            self.epsilon = max(
                self.config.epsilon_end,
                self.config.epsilon_start * (self.config.epsilon_decay ** self.step_count)
            )
            
        elif self.config.epsilon_schedule == 'cosine':
            # 余弦衰减
            if self.step_count < self.config.epsilon_decay_steps:
                progress = self.step_count / self.config.epsilon_decay_steps
                self.epsilon = (
                    self.config.epsilon_end + 
                    0.5 * (self.config.epsilon_start - self.config.epsilon_end) * 
                    (1 + math.cos(math.pi * progress))
                )
            else:
                self.epsilon = self.config.epsilon_end

class UCBExploration:
    """UCB（Upper Confidence Bound）探索策略"""
    def __init__(self, action_dim, c=2.0):
        self.action_dim = action_dim
        self.c = c
        self.action_counts = np.zeros(action_dim)
        self.total_count = 0
    
    def select_action(self, q_values, legal_actions):
        """基于UCB选择动作"""
        self.total_count += 1
        
        ucb_values = np.full(self.action_dim, -np.inf)
        
        for action in legal_actions:
            if self.action_counts[action] == 0:
                # 未探索的动作给予最高优先级
                ucb_values[action] = np.inf
            else:
                # UCB公式
                confidence = self.c * np.sqrt(
                    np.log(self.total_count) / self.action_counts[action]
                )
                ucb_values[action] = q_values[action] + confidence
        
        action = np.argmax(ucb_values)
        self.action_counts[action] += 1
        
        return action
```

## 4. 训练配置参数

### 4.1 DQN核心参数

```python
@dataclass
class DQNTrainingConfig:
    # 网络更新参数
    learning_rate: float = 1e-4
    weight_decay: float = 1e-5
    batch_size: int = 32
    target_update_frequency: int = 1000  # 硬更新频率
    
    # 软更新参数
    soft_update: bool = False
    tau: float = 0.005  # 软更新系数
    
    # 经验回放参数
    buffer_size: int = 100000
    min_buffer_size: int = 10000
    use_prioritized_replay: bool = True
    
    # 优先经验回放参数
    per_alpha: float = 0.6
    per_beta: float = 0.4
    per_beta_increment: float = 0.001
    
    # 探索参数
    epsilon_start: float = 1.0
    epsilon_end: float = 0.01
    epsilon_decay_steps: int = 100000
    epsilon_schedule: str = "linear"  # linear, exponential, cosine
    epsilon_decay: float = 0.995  # 指数衰减率
    
    # 训练参数
    gamma: float = 0.99  # 折扣因子
    max_grad_norm: float = 10.0  # 梯度裁剪
    
    # 算法变体
    use_double_dqn: bool = True
    use_dueling: bool = True
    
    # 损失函数
    loss_function: str = "huber"  # mse, huber
    
    # 训练频率
    train_frequency: int = 4  # 每4步训练一次
    
    # 评估参数
    eval_frequency: int = 10000
    eval_episodes: int = 100
```

### 4.2 三国杀特定配置

```python
@dataclass
class SanguoshaDQNConfig:
    # 奖励塑形
    reward_shaping: Dict[str, float] = field(default_factory=lambda: {
        'win_bonus': 100.0,
        'lose_penalty': -50.0,
        'survival_reward': 0.1,
        'damage_reward': 2.0,
        'heal_reward': 1.5,
        'card_efficiency': 0.5,
        'invalid_action_penalty': -5.0
    })
    
    # 状态预处理
    state_normalization: bool = True
    state_clipping: bool = True
    clip_range: Tuple[float, float] = (-10.0, 10.0)
    
    # 动作掩码
    use_action_masking: bool = True
    mask_invalid_actions: bool = True
    
    # 课程学习
    curriculum_learning: bool = True
    curriculum_stages: List[Dict] = field(default_factory=lambda: [
        {
            'name': 'basic_rules',
            'episodes': 20000,
            'opponents': 'random',
            'epsilon_override': 0.8
        },
        {
            'name': 'intermediate',
            'episodes': 40000,
            'opponents': 'rule_based',
            'epsilon_override': 0.5
        },
        {
            'name': 'advanced',
            'episodes': 80000,
            'opponents': 'mixed',
            'epsilon_override': None
        }
    ])
    
    # 多智能体设置
    self_play_enabled: bool = True
    self_play_ratio: float = 0.2
    opponent_update_frequency: int = 5000
```

## 5. 训练流程实现

### 5.1 主训练循环

```python
class DQNSanguoshaTrainer:
    def __init__(self, config):
        self.config = config
        self.trainer = DQNTrainer(config)
        self.env = create_sanguosha_env(config)
        self.evaluator = DQNEvaluator(config)
        self.logger = TrainingLogger(config)
        self.curriculum = CurriculumLearning(config) if config.curriculum_learning else None
        
        # 训练统计
        self.episode_count = 0
        self.total_steps = 0
        self.best_performance = 0.0
        
    def train(self):
        """主训练流程"""
        print("开始DQN训练...")
        
        while self.episode_count < self.config.max_episodes:
            # 运行一局游戏
            episode_stats = self.run_episode()
            
            # 记录统计信息
            self.logger.log_episode(episode_stats, self.episode_count)
            
            # 定期评估
            if self.episode_count % self.config.eval_frequency == 0:
                eval_results = self.evaluator.evaluate(self.trainer.q_network)
                self.logger.log_evaluation(eval_results, self.episode_count)
                
                # 保存最佳模型
                if eval_results['win_rate'] > self.best_performance:
                    self.best_performance = eval_results['win_rate']
                    self.save_model(f"best_dqn_model_ep{self.episode_count}.pth")
            
            # 更新课程学习
            if self.curriculum:
                self.curriculum.update(self.episode_count, episode_stats)
            
            self.episode_count += 1
    
    def run_episode(self):
        """运行单局游戏"""
        state = self.env.reset()
        episode_reward = 0
        episode_length = 0
        episode_loss = []
        
        while not self.env.is_done():
            # 获取合法动作
            legal_actions = self.env.get_legal_actions()
            
            # 选择动作
            action = self.trainer.select_action(state, legal_actions, training=True)
            
            # 执行动作
            next_state, reward, done, info = self.env.step(action)
            
            # 创建动作掩码
            action_mask = self.create_action_mask(legal_actions)
            next_legal_actions = self.env.get_legal_actions() if not done else []
            next_action_mask = self.create_action_mask(next_legal_actions) if not done else None
            
            # 存储经验
            self.trainer.replay_buffer.push(
                state, action, reward, next_state, done, action_mask, next_action_mask
            )
            
            # 训练网络
            if self.total_steps % self.config.train_frequency == 0:
                loss_info = self.trainer.train_step()
                if loss_info:
                    episode_loss.append(loss_info['loss'])
            
            # 更新状态
            state = next_state
            episode_reward += reward
            episode_length += 1
            self.total_steps += 1
        
        return {
            'reward': episode_reward,
            'length': episode_length,
            'avg_loss': np.mean(episode_loss) if episode_loss else 0,
            'epsilon': self.trainer.epsilon_scheduler.get_epsilon(),
            'buffer_size': len(self.trainer.replay_buffer),
            'won': self.env.did_player_win()
        }
    
    def create_action_mask(self, legal_actions):
        """创建动作掩码"""
        mask = torch.zeros(self.config.action_dim, dtype=torch.bool)
        if legal_actions:
            mask[legal_actions] = True
        return mask
```

### 5.2 多智能体训练

```python
class MultiAgentDQNTrainer:
    def __init__(self, config):
        self.config = config
        self.num_agents = config.num_players
        
        # 为每个智能体创建独立的DQN
        self.agents = [DQNTrainer(config) for _ in range(self.num_agents)]
        
        # 共享经验池（可选）
        if config.shared_experience:
            self.shared_buffer = ExperienceReplayBuffer(config.buffer_size)
        
        # 自我对弈管理
        self.self_play_manager = SelfPlayManager(config)
        
    def train_multi_agent(self):
        """多智能体训练"""
        for episode in range(self.config.max_episodes):
            # 选择对手配置
            opponent_config = self.self_play_manager.get_opponent_config(episode)
            
            # 运行多智能体游戏
            episode_data = self.run_multi_agent_episode(opponent_config)
            
            # 为每个智能体更新网络
            for agent_id, agent in enumerate(self.agents):
                agent_experiences = episode_data[agent_id]
                
                # 存储经验
                for exp in agent_experiences:
                    agent.replay_buffer.push(*exp)
                    
                    if self.config.shared_experience:
                        self.shared_buffer.push(*exp)
                
                # 训练网络
                if len(agent.replay_buffer) >= self.config.min_buffer_size:
                    for _ in range(self.config.updates_per_episode):
                        if self.config.shared_experience:
                            # 使用共享经验池
                            loss_info = agent.train_step_with_buffer(self.shared_buffer)
                        else:
                            # 使用个人经验池
                            loss_info = agent.train_step()
            
            # 更新自我对弈策略
            if episode % self.config.self_play_update_frequency == 0:
                self.self_play_manager.update_opponent_pool(self.agents)
    
    def run_multi_agent_episode(self, opponent_config):
        """运行多智能体游戏回合"""
        env = create_multi_agent_env(self.config, opponent_config)
        states = env.reset()
        
        episode_data = [[] for _ in range(self.num_agents)]
        
        while not env.is_done():
            actions = []
            
            # 每个智能体选择动作
            for agent_id, agent in enumerate(self.agents):
                if env.is_agent_active(agent_id):
                    legal_actions = env.get_legal_actions(agent_id)
                    action = agent.select_action(
                        states[agent_id], 
                        legal_actions, 
                        training=True
                    )
                    actions.append(action)
                else:
                    actions.append(None)
            
            # 执行联合动作
            next_states, rewards, dones, infos = env.step(actions)
            
            # 存储每个智能体的经验
            for agent_id in range(self.num_agents):
                if actions[agent_id] is not None:
                    legal_actions = env.get_legal_actions(agent_id)
                    action_mask = self.create_action_mask(legal_actions)
                    
                    next_legal_actions = env.get_legal_actions(agent_id) if not dones[agent_id] else []
                    next_action_mask = self.create_action_mask(next_legal_actions) if not dones[agent_id] else None
                    
                    episode_data[agent_id].append((
                        states[agent_id],
                        actions[agent_id],
                        rewards[agent_id],
                        next_states[agent_id],
                        dones[agent_id],
                        action_mask,
                        next_action_mask
                    ))
            
            states = next_states
        
        return episode_data
```

## 6. 高级技术优化

### 6.1 Rainbow DQN集成

```python
class RainbowDQN(nn.Module):
    """集成多种DQN改进的Rainbow算法"""
    def __init__(self, config):
        super().__init__()
        self.config = config
        
        # 状态编码器
        self.state_encoder = StateEncoder(
            state_dim=config.state_dim,
            hidden_dim=config.hidden_dim,
            attention_heads=config.attention_heads
        )
        
        # Noisy Networks
        if config.use_noisy_networks:
            self.noisy_layers = nn.ModuleList([
                NoisyLinear(config.hidden_dim, config.q_hidden_layers[0]),
                NoisyLinear(config.q_hidden_layers[0], config.q_hidden_layers[1]),
                NoisyLinear(config.q_hidden_layers[1], config.q_hidden_layers[2])
            ])
        else:
            self.linear_layers = nn.ModuleList([
                nn.Linear(config.hidden_dim, config.q_hidden_layers[0]),
                nn.Linear(config.q_hidden_layers[0], config.q_hidden_layers[1]),
                nn.Linear(config.q_hidden_layers[1], config.q_hidden_layers[2])
            ])
        
        # Distributional DQN (C51)
        if config.use_distributional:
            self.num_atoms = config.num_atoms
            self.v_min = config.v_min
            self.v_max = config.v_max
            self.delta_z = (self.v_max - self.v_min) / (self.num_atoms - 1)
            
            # 价值分布输出
            self.value_dist = nn.Linear(config.q_hidden_layers[2], self.num_atoms)
            self.advantage_dist = nn.Linear(config.q_hidden_layers[2], config.action_dim * self.num_atoms)
        else:
            # 标准Q值输出
            self.value_head = nn.Linear(config.q_hidden_layers[2], 1)
            self.advantage_head = nn.Linear(config.q_hidden_layers[2], config.action_dim)
    
    def forward(self, state, action_mask=None):
        # 状态编码
        encoded_state = self.state_encoder(state)
        
        # 通过网络层
        x = encoded_state
        for i, layer in enumerate(self.get_layers()):
            x = layer(x)
            if i < len(self.get_layers()) - 1:
                x = F.relu(x)
                x = F.dropout(x, p=self.config.dropout_rate, training=self.training)
        
        if self.config.use_distributional:
            # 分布式Q学习
            value_dist = F.softmax(self.value_dist(x), dim=-1)
            advantage_dist = self.advantage_dist(x).view(-1, self.config.action_dim, self.num_atoms)
            advantage_dist = F.softmax(advantage_dist, dim=-1)
            
            # 计算Q值分布
            q_dist = value_dist.unsqueeze(1) + advantage_dist - advantage_dist.mean(dim=1, keepdim=True)
            
            # 计算期望Q值
            support = torch.linspace(self.v_min, self.v_max, self.num_atoms).to(state.device)
            q_values = torch.sum(q_dist * support, dim=-1)
            
            if action_mask is not None:
                q_values = q_values.masked_fill(~action_mask, -1e9)
            
            return q_values, q_dist
        else:
            # 标准Dueling DQN
            value = self.value_head(x)
            advantage = self.advantage_head(x)
            
            q_values = value + advantage - advantage.mean(dim=-1, keepdim=True)
            
            if action_mask is not None:
                q_values = q_values.masked_fill(~action_mask, -1e9)
            
            return q_values
    
    def get_layers(self):
        if self.config.use_noisy_networks:
            return self.noisy_layers
        else:
            return self.linear_layers
    
    def reset_noise(self):
        """重置噪声网络的噪声"""
        if self.config.use_noisy_networks:
            for layer in self.noisy_layers:
                layer.reset_noise()

class NoisyLinear(nn.Module):
    """噪声线性层"""
    def __init__(self, in_features, out_features, std_init=0.5):
        super().__init__()
        self.in_features = in_features
        self.out_features = out_features
        self.std_init = std_init
        
        # 权重参数
        self.weight_mu = nn.Parameter(torch.empty(out_features, in_features))
        self.weight_sigma = nn.Parameter(torch.empty(out_features, in_features))
        self.register_buffer('weight_epsilon', torch.empty(out_features, in_features))
        
        # 偏置参数
        self.bias_mu = nn.Parameter(torch.empty(out_features))
        self.bias_sigma = nn.Parameter(torch.empty(out_features))
        self.register_buffer('bias_epsilon', torch.empty(out_features))
        
        self.reset_parameters()
        self.reset_noise()
    
    def reset_parameters(self):
        mu_range = 1 / math.sqrt(self.in_features)
        self.weight_mu.data.uniform_(-mu_range, mu_range)
        self.weight_sigma.data.fill_(self.std_init / math.sqrt(self.in_features))
        self.bias_mu.data.uniform_(-mu_range, mu_range)
        self.bias_sigma.data.fill_(self.std_init / math.sqrt(self.out_features))
    
    def reset_noise(self):
        epsilon_in = self._scale_noise(self.in_features)
        epsilon_out = self._scale_noise(self.out_features)
        self.weight_epsilon.copy_(epsilon_out.ger(epsilon_in))
        self.bias_epsilon.copy_(epsilon_out)
    
    def _scale_noise(self, size):
        x = torch.randn(size)
        return x.sign().mul_(x.abs().sqrt_())
    
    def forward(self, input):
        if self.training:
            weight = self.weight_mu + self.weight_sigma * self.weight_epsilon
            bias = self.bias_mu + self.bias_sigma * self.bias_epsilon
        else:
            weight = self.weight_mu
            bias = self.bias_mu
        
        return F.linear(input, weight, bias)
```

### 6.2 分布式训练

```python
class DistributedDQNTrainer:
    """分布式DQN训练器"""
    def __init__(self, config, rank, world_size):
        self.config = config
        self.rank = rank
        self.world_size = world_size
        
        # 初始化分布式环境
        torch.distributed.init_process_group(
            backend='nccl',
            rank=rank,
            world_size=world_size
        )
        
        # 创建网络
        self.q_network = DQNNetwork(config).to(rank)
        self.target_network = DQNNetwork(config).to(rank)
        
        # 包装为分布式模型
        self.q_network = torch.nn.parallel.DistributedDataParallel(
            self.q_network, device_ids=[rank]
        )
        
        # 同步初始参数
        self.sync_networks()
        
        # 分布式经验池
        self.replay_buffer = DistributedExperienceBuffer(config, rank, world_size)
        
    def sync_networks(self):
        """同步网络参数"""
        for param in self.q_network.parameters():
            torch.distributed.broadcast(param.data, src=0)
        
        self.target_network.load_state_dict(self.q_network.module.state_dict())
    
    def train_distributed(self):
        """分布式训练主循环"""
        for episode in range(self.config.max_episodes // self.world_size):
            # 每个进程运行独立的游戏
            episode_data = self.run_episode()
            
            # 收集经验到分布式缓冲区
            self.replay_buffer.add_episode_data(episode_data)
            
            # 同步训练
            if episode % self.config.sync_frequency == 0:
                self.distributed_train_step()
    
    def distributed_train_step(self):
        """分布式训练步骤"""
        # 从分布式缓冲区采样
        batch = self.replay_buffer.sample_distributed(self.config.batch_size)
        
        if batch is None:
            return
        
        # 计算损失
        loss = self.compute_loss(batch)
        
        # 反向传播
        self.optimizer.zero_grad()
        loss.backward()
        
        # 梯度同步
        torch.distributed.all_reduce(loss)
        loss /= self.world_size
        
        # 参数更新
        self.optimizer.step()
        
        # 定期同步目标网络
        if self.training_step % self.config.target_update_frequency == 0:
            self.sync_target_network()
    
    def sync_target_network(self):
        """同步目标网络"""
        self.target_network.load_state_dict(self.q_network.module.state_dict())
        
        # 广播到所有进程
        for param in self.target_network.parameters():
            torch.distributed.broadcast(param.data, src=0)
```

## 7. 评估与分析

### 7.1 Q值分析工具

```python
class QValueAnalyzer:
    """Q值分析工具"""
    def __init__(self, network, env):
        self.network = network
        self.env = env
        
    def analyze_q_values(self, state, legal_actions):
        """分析状态的Q值分布"""
        with torch.no_grad():
            state_tensor = torch.tensor(state, dtype=torch.float32).unsqueeze(0)
            action_mask = torch.zeros(1, self.env.action_dim).bool()
            action_mask[0, legal_actions] = True
            
            q_values = self.network(state_tensor, action_mask).squeeze(0)
            
            # 分析结果
            analysis = {
                'q_values': q_values.cpu().numpy(),
                'legal_actions': legal_actions,
                'best_action': torch.argmax(q_values).item(),
                'q_value_range': (q_values.min().item(), q_values.max().item()),
                'q_value_std': q_values.std().item(),
                'action_rankings': torch.argsort(q_values, descending=True).cpu().numpy()
            }
            
            return analysis
    
    def visualize_q_values(self, state, legal_actions, action_names=None):
        """可视化Q值分布"""
        analysis = self.analyze_q_values(state, legal_actions)
        
        plt.figure(figsize=(12, 6))
        
        # Q值柱状图
        plt.subplot(1, 2, 1)
        q_values = analysis['q_values']
        colors = ['green' if i in legal_actions else 'red' for i in range(len(q_values))]
        
        bars = plt.bar(range(len(q_values)), q_values, color=colors, alpha=0.7)
        plt.title('Q-Values Distribution')
        plt.xlabel('Action Index')
        plt.ylabel('Q-Value')
        
        # 标记最佳动作
        best_action = analysis['best_action']
        bars[best_action].set_color('gold')
        bars[best_action].set_edgecolor('black')
        bars[best_action].set_linewidth(2)
        
        # 合法动作排名
        plt.subplot(1, 2, 2)
        legal_q_values = [q_values[i] for i in legal_actions]
        legal_action_names = [f"Action {i}" if action_names is None else action_names[i] 
                             for i in legal_actions]
        
        sorted_indices = np.argsort(legal_q_values)[::-1]
        sorted_actions = [legal_actions[i] for i in sorted_indices]
        sorted_q_values = [legal_q_values[i] for i in sorted_indices]
        sorted_names = [legal_action_names[i] for i in sorted_indices]
        
        plt.barh(range(len(sorted_actions)), sorted_q_values)
        plt.yticks(range(len(sorted_actions)), sorted_names)
        plt.title('Legal Actions Ranking')
        plt.xlabel('Q-Value')
        
        plt.tight_layout()
        plt.show()
        
        return analysis
```

### 7.2 训练诊断工具

```python
class DQNDiagnostics:
    """DQN训练诊断工具"""
    def __init__(self, trainer):
        self.trainer = trainer
        self.metrics_history = {
            'q_values': [],
            'target_q_values': [],
            'td_errors': [],
            'loss_values': [],
            'epsilon_values': [],
            'buffer_size': []
        }
    
    def update_metrics(self, batch_data, loss_info):
        """更新诊断指标"""
        states, actions, rewards, next_states, dones, _, _ = batch_data
        
        with torch.no_grad():
            # 当前Q值
            current_q = self.trainer.q_network(states).gather(1, actions.unsqueeze(1)).squeeze(1)
            
            # 目标Q值
            next_q = self.trainer.target_network(next_states).max(1)[0]
            target_q = rewards + (self.trainer.config.gamma * next_q * (1 - dones))
            
            # TD误差
            td_errors = torch.abs(current_q - target_q)
            
            # 记录指标
            self.metrics_history['q_values'].append(current_q.mean().item())
            self.metrics_history['target_q_values'].append(target_q.mean().item())
            self.metrics_history['td_errors'].append(td_errors.mean().item())
            self.metrics_history['loss_values'].append(loss_info['loss'])
            self.metrics_history['epsilon_values'].append(loss_info['epsilon'])
            self.metrics_history['buffer_size'].append(len(self.trainer.replay_buffer))
    
    def plot_training_curves(self):
        """绘制训练曲线"""
        fig, axes = plt.subplots(2, 3, figsize=(15, 10))
        
        # Q值趋势
        axes[0, 0].plot(self.metrics_history['q_values'], label='Current Q')
        axes[0, 0].plot(self.metrics_history['target_q_values'], label='Target Q')
        axes[0, 0].set_title('Q-Values Trend')
        axes[0, 0].legend()
        
        # TD误差
        axes[0, 1].plot(self.metrics_history['td_errors'])
        axes[0, 1].set_title('TD Error')
        
        # 损失函数
        axes[0, 2].plot(self.metrics_history['loss_values'])
        axes[0, 2].set_title('Training Loss')
        
        # 探索率
        axes[1, 0].plot(self.metrics_history['epsilon_values'])
        axes[1, 0].set_title('Epsilon (Exploration Rate)')
        
        # 经验池大小
        axes[1, 1].plot(self.metrics_history['buffer_size'])
        axes[1, 1].set_title('Replay Buffer Size')
        
        # Q值分布
        if len(self.metrics_history['q_values']) > 100:
            recent_q_values = self.metrics_history['q_values'][-100:]
            axes[1, 2].hist(recent_q_values, bins=20, alpha=0.7)
            axes[1, 2].set_title('Recent Q-Values Distribution')
        
        plt.tight_layout()
        plt.show()
    
    def diagnose_training_issues(self):
        """诊断训练问题"""
        issues = []
        
        # 检查Q值爆炸
        recent_q_values = self.metrics_history['q_values'][-100:] if len(self.metrics_history['q_values']) > 100 else self.metrics_history['q_values']
        if recent_q_values and max(recent_q_values) > 1000:
            issues.append("Q值可能出现爆炸，建议降低学习率或增加梯度裁剪")
        
        # 检查学习停滞
        if len(self.metrics_history['loss_values']) > 1000:
            recent_loss = self.metrics_history['loss_values'][-500:]
            if np.std(recent_loss) < 0.01:
                issues.append("损失函数变化很小，可能出现学习停滞")
        
        # 检查探索不足
        current_epsilon = self.metrics_history['epsilon_values'][-1] if self.metrics_history['epsilon_values'] else 1.0
        if current_epsilon < 0.01 and len(self.metrics_history['epsilon_values']) < 50000:
            issues.append("探索率衰减过快，可能导致探索不足")
        
        # 检查经验池
        buffer_size = self.metrics_history['buffer_size'][-1] if self.metrics_history['buffer_size'] else 0
        if buffer_size < self.trainer.config.min_buffer_size:
            issues.append("经验池大小不足，影响训练稳定性")
        
        return issues
```

## 8. 部署与优化

### 8.1 模型压缩

```python
def compress_dqn_model(model, compression_ratio=0.5):
    """压缩DQN模型"""
    # 权重剪枝
    for name, module in model.named_modules():
        if isinstance(module, nn.Linear):
            # 计算剪枝阈值
            weight = module.weight.data
            threshold = torch.quantile(torch.abs(weight), compression_ratio)
            
            # 应用剪枝
            mask = torch.abs(weight) > threshold
            module.weight.data *= mask.float()
    
    return model

def quantize_dqn_model(model):
    """量化DQN模型"""
    # 动态量化
    quantized_model = torch.quantization.quantize_dynamic(
        model, 
        {nn.Linear}, 
        dtype=torch.qint8
    )
    
    return quantized_model
```

### 8.2 推理优化

```python
class OptimizedDQNInference:
    def __init__(self, model_path, device='cpu'):
        self.device = device
        
        # 加载模型
        checkpoint = torch.load(model_path, map_location=device)
        self.network = DQNNetwork(checkpoint['config'])
        self.network.load_state_dict(checkpoint['network_state_dict'])
        self.network.eval()
        
        # 模型优化
        self.network = torch.jit.script(self.network)
        
        # 预热
        self.warmup()
    
    def warmup(self):
        """预热推理"""
        dummy_state = torch.randn(1, 366).to(self.device)
        dummy_mask = torch.ones(1, 61).bool().to(self.device)
        
        with torch.no_grad():
            for _ in range(10):
                _ = self.network(dummy_state, dummy_mask)
    
    @torch.no_grad()
    def get_best_action(self, state, legal_actions):
        """获取最佳动作"""
        state_tensor = torch.tensor(state, dtype=torch.float32).unsqueeze(0).to(self.device)
        action_mask = torch.zeros(1, 61).bool().to(self.device)
        action_mask[0, legal_actions] = True
        
        q_values = self.network(state_tensor, action_mask)
        action = torch.argmax(q_values, dim=-1).item()
        
        return action, q_values.squeeze(0).cpu().numpy()
```

这个DQN训练方案提供了完整的实现框架，包括基础DQN、Double DQN、Dueling DQN、优先经验回放、Rainbow DQN等多种变体，以及分布式训练、模型压缩等高级功能。接下来我将创建A3C算法的训练方案。