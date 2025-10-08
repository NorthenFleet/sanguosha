# A3C算法三国杀AI训练方案

## 1. 方案概述

### 1.1 A3C算法简介

A3C（Asynchronous Advantage Actor-Critic）是一种异步强化学习算法，通过多个并行的智能体异步更新全局网络参数。在三国杀游戏中，A3C算法具有以下特点：

- **异步训练**: 多个worker并行收集经验，提高训练效率
- **Actor-Critic架构**: 同时学习策略和价值函数
- **优势函数**: 使用优势函数减少方差，提高训练稳定性
- **在线学习**: 不需要经验回放，直接从环境交互中学习

### 1.2 三国杀应用优势

在三国杀游戏中，A3C算法的优势包括：
- **并行化**: 多个游戏实例同时运行，加速数据收集
- **内存效率**: 不需要大型经验回放池，节省内存
- **实时学习**: 能够快速适应游戏环境变化
- **探索多样性**: 不同worker采用不同探索策略

## 2. 网络架构设计

### 2.1 A3C网络结构

```python
class A3CNetwork(nn.Module):
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
        self.actor_layers = nn.ModuleList([
            nn.Linear(config.hidden_dim, config.actor_hidden_layers[0]),
            nn.ReLU(),
            nn.Dropout(config.dropout_rate),
            
            nn.Linear(config.actor_hidden_layers[0], config.actor_hidden_layers[1]),
            nn.ReLU(),
            nn.Dropout(config.dropout_rate),
            
            nn.Linear(config.actor_hidden_layers[1], config.action_dim)
        ])
        
        # Critic网络（价值网络）
        self.critic_layers = nn.ModuleList([
            nn.Linear(config.hidden_dim, config.critic_hidden_layers[0]),
            nn.ReLU(),
            nn.Dropout(config.dropout_rate),
            
            nn.Linear(config.critic_hidden_layers[0], config.critic_hidden_layers[1]),
            nn.ReLU(),
            nn.Dropout(config.dropout_rate),
            
            nn.Linear(config.critic_hidden_layers[1], 1)
        ])
        
        # 网络初始化
        self.apply(self._init_weights)
    
    def _init_weights(self, module):
        if isinstance(module, nn.Linear):
            if self.config.init_method == 'xavier_uniform':
                nn.init.xavier_uniform_(module.weight)
            elif self.config.init_method == 'kaiming_normal':
                nn.init.kaiming_normal_(module.weight, mode='fan_out', nonlinearity='relu')
            elif self.config.init_method == 'orthogonal':
                nn.init.orthogonal_(module.weight, gain=1.0)
            
            if module.bias is not None:
                nn.init.constant_(module.bias, 0)
    
    def forward(self, state, action_mask=None):
        # 状态编码
        encoded_state = self.state_encoder(state)
        
        # Actor前向传播
        actor_x = encoded_state
        for layer in self.actor_layers[:-1]:
            actor_x = layer(actor_x)
        
        # 策略logits
        policy_logits = self.actor_layers[-1](actor_x)
        
        # 应用动作掩码
        if action_mask is not None:
            policy_logits = policy_logits.masked_fill(~action_mask, -1e9)
        
        # 策略概率分布
        policy_probs = F.softmax(policy_logits, dim=-1)
        
        # Critic前向传播
        critic_x = encoded_state
        for layer in self.critic_layers:
            critic_x = layer(critic_x)
        
        # 状态价值
        state_value = critic_x.squeeze(-1)
        
        return policy_probs, state_value, policy_logits
    
    def get_action_and_value(self, state, action_mask=None):
        """获取动作和价值（用于推理）"""
        policy_probs, state_value, policy_logits = self.forward(state, action_mask)
        
        # 创建分布
        if action_mask is not None:
            # 只考虑合法动作
            masked_probs = policy_probs * action_mask.float()
            masked_probs = masked_probs / masked_probs.sum(dim=-1, keepdim=True)
            dist = torch.distributions.Categorical(masked_probs)
        else:
            dist = torch.distributions.Categorical(policy_probs)
        
        # 采样动作
        action = dist.sample()
        log_prob = dist.log_prob(action)
        entropy = dist.entropy()
        
        return action, log_prob, entropy, state_value
```

### 2.2 网络配置参数

```python
@dataclass
class A3CNetworkConfig:
    # 基础参数
    state_dim: int = 366
    action_dim: int = 61
    hidden_dim: int = 256
    attention_heads: int = 8
    
    # Actor网络层数
    actor_hidden_layers: List[int] = field(default_factory=lambda: [512, 256])
    
    # Critic网络层数
    critic_hidden_layers: List[int] = field(default_factory=lambda: [512, 256])
    
    # 正则化参数
    dropout_rate: float = 0.1
    layer_norm: bool = True
    
    # 激活函数
    activation: str = "relu"
    
    # 网络初始化
    init_method: str = "orthogonal"  # xavier_uniform, kaiming_normal, orthogonal
    
    # 损失权重
    value_loss_coef: float = 0.5
    entropy_coef: float = 0.01
    
    # 梯度裁剪
    max_grad_norm: float = 0.5
```

## 3. A3C算法实现

### 3.1 全局网络和Worker

```python
class A3CGlobalNetwork:
    """A3C全局网络"""
    def __init__(self, config):
        self.config = config
        self.network = A3CNetwork(config)
        
        # 全局优化器
        self.optimizer = torch.optim.Adam(
            self.network.parameters(),
            lr=config.learning_rate,
            weight_decay=config.weight_decay
        )
        
        # 共享参数（用于多进程）
        self.network.share_memory()
        
        # 训练统计
        self.global_step = mp.Value('i', 0)
        self.global_episode = mp.Value('i', 0)
        self.best_score = mp.Value('f', -float('inf'))
        
        # 锁机制
        self.lock = mp.Lock()
    
    def update_global_network(self, local_gradients):
        """更新全局网络参数"""
        with self.lock:
            # 应用梯度
            for global_param, local_grad in zip(self.network.parameters(), local_gradients):
                if global_param.grad is None:
                    global_param.grad = local_grad.clone()
                else:
                    global_param.grad += local_grad
            
            # 梯度裁剪
            torch.nn.utils.clip_grad_norm_(
                self.network.parameters(), 
                self.config.max_grad_norm
            )
            
            # 参数更新
            self.optimizer.step()
            self.optimizer.zero_grad()
            
            # 更新全局步数
            with self.global_step.get_lock():
                self.global_step.value += 1
    
    def get_global_params(self):
        """获取全局网络参数"""
        return self.network.state_dict()
    
    def save_model(self, path):
        """保存模型"""
        torch.save({
            'network_state_dict': self.network.state_dict(),
            'optimizer_state_dict': self.optimizer.state_dict(),
            'config': self.config,
            'global_step': self.global_step.value,
            'global_episode': self.global_episode.value
        }, path)

class A3CWorker:
    """A3C工作进程"""
    def __init__(self, worker_id, global_network, config):
        self.worker_id = worker_id
        self.global_network = global_network
        self.config = config
        
        # 本地网络
        self.local_network = A3CNetwork(config)
        
        # 环境
        self.env = create_sanguosha_env(config, worker_id)
        
        # 训练统计
        self.episode_count = 0
        self.step_count = 0
        
        # 经验缓存
        self.states = []
        self.actions = []
        self.rewards = []
        self.values = []
        self.log_probs = []
        self.entropies = []
        self.action_masks = []
    
    def sync_with_global(self):
        """同步本地网络与全局网络"""
        self.local_network.load_state_dict(self.global_network.get_global_params())
    
    def run(self):
        """Worker主循环"""
        print(f"Worker {self.worker_id} 开始训练...")
        
        while self.global_network.global_step.value < self.config.max_global_steps:
            # 同步网络参数
            self.sync_with_global()
            
            # 运行一个episode
            episode_reward = self.run_episode()
            
            # 更新全局统计
            with self.global_network.global_episode.get_lock():
                self.global_network.global_episode.value += 1
            
            # 记录日志
            if self.episode_count % self.config.log_frequency == 0:
                print(f"Worker {self.worker_id}, Episode {self.episode_count}, "
                      f"Reward: {episode_reward:.2f}, "
                      f"Global Step: {self.global_network.global_step.value}")
            
            self.episode_count += 1
    
    def run_episode(self):
        """运行单个episode"""
        state = self.env.reset()
        episode_reward = 0
        episode_length = 0
        
        # 清空经验缓存
        self.clear_experience_buffer()
        
        while not self.env.is_done() and episode_length < self.config.max_episode_length:
            # 获取合法动作
            legal_actions = self.env.get_legal_actions()
            action_mask = self.create_action_mask(legal_actions)
            
            # 选择动作
            with torch.no_grad():
                state_tensor = torch.tensor(state, dtype=torch.float32).unsqueeze(0)
                action, log_prob, entropy, value = self.local_network.get_action_and_value(
                    state_tensor, action_mask.unsqueeze(0)
                )
                
                action = action.item()
                log_prob = log_prob.item()
                entropy = entropy.item()
                value = value.item()
            
            # 执行动作
            next_state, reward, done, info = self.env.step(action)
            
            # 存储经验
            self.states.append(state)
            self.actions.append(action)
            self.rewards.append(reward)
            self.values.append(value)
            self.log_probs.append(log_prob)
            self.entropies.append(entropy)
            self.action_masks.append(action_mask)
            
            # 更新状态
            state = next_state
            episode_reward += reward
            episode_length += 1
            self.step_count += 1
            
            # 定期更新或episode结束时更新
            if (len(self.states) >= self.config.n_steps or done or 
                episode_length >= self.config.max_episode_length):
                
                # 计算最后状态的价值
                if done:
                    bootstrap_value = 0.0
                else:
                    with torch.no_grad():
                        state_tensor = torch.tensor(state, dtype=torch.float32).unsqueeze(0)
                        _, bootstrap_value, _ = self.local_network(state_tensor)
                        bootstrap_value = bootstrap_value.item()
                
                # 更新网络
                self.update_network(bootstrap_value)
                
                # 清空缓存
                self.clear_experience_buffer()
        
        return episode_reward
    
    def update_network(self, bootstrap_value):
        """更新网络参数"""
        if len(self.states) == 0:
            return
        
        # 计算折扣奖励和优势
        returns = self.compute_returns(bootstrap_value)
        advantages = self.compute_advantages(returns)
        
        # 转换为tensor
        states_tensor = torch.stack([torch.tensor(s, dtype=torch.float32) for s in self.states])
        actions_tensor = torch.tensor(self.actions, dtype=torch.long)
        returns_tensor = torch.tensor(returns, dtype=torch.float32)
        advantages_tensor = torch.tensor(advantages, dtype=torch.float32)
        old_log_probs_tensor = torch.tensor(self.log_probs, dtype=torch.float32)
        action_masks_tensor = torch.stack(self.action_masks)
        
        # 前向传播
        policy_probs, values, policy_logits = self.local_network(states_tensor, action_masks_tensor)
        
        # 计算新的log概率和熵
        dist = torch.distributions.Categorical(policy_probs)
        new_log_probs = dist.log_prob(actions_tensor)
        entropy = dist.entropy()
        
        # 计算损失
        # Actor损失（策略梯度）
        actor_loss = -(advantages_tensor * new_log_probs).mean()
        
        # Critic损失（价值函数）
        critic_loss = F.mse_loss(values, returns_tensor)
        
        # 熵损失（鼓励探索）
        entropy_loss = -entropy.mean()
        
        # 总损失
        total_loss = (actor_loss + 
                     self.config.value_loss_coef * critic_loss + 
                     self.config.entropy_coef * entropy_loss)
        
        # 计算梯度
        self.local_network.zero_grad()
        total_loss.backward()
        
        # 收集梯度
        local_gradients = []
        for param in self.local_network.parameters():
            if param.grad is not None:
                local_gradients.append(param.grad.clone())
            else:
                local_gradients.append(torch.zeros_like(param))
        
        # 更新全局网络
        self.global_network.update_global_network(local_gradients)
    
    def compute_returns(self, bootstrap_value):
        """计算折扣回报"""
        returns = []
        R = bootstrap_value
        
        for reward in reversed(self.rewards):
            R = reward + self.config.gamma * R
            returns.insert(0, R)
        
        return returns
    
    def compute_advantages(self, returns):
        """计算优势函数"""
        advantages = []
        for i in range(len(returns)):
            advantage = returns[i] - self.values[i]
            advantages.append(advantage)
        
        # 标准化优势
        if len(advantages) > 1:
            advantages = np.array(advantages)
            advantages = (advantages - advantages.mean()) / (advantages.std() + 1e-8)
            advantages = advantages.tolist()
        
        return advantages
    
    def create_action_mask(self, legal_actions):
        """创建动作掩码"""
        mask = torch.zeros(self.config.action_dim, dtype=torch.bool)
        if legal_actions:
            mask[legal_actions] = True
        return mask
    
    def clear_experience_buffer(self):
        """清空经验缓存"""
        self.states.clear()
        self.actions.clear()
        self.rewards.clear()
        self.values.clear()
        self.log_probs.clear()
        self.entropies.clear()
        self.action_masks.clear()
```

### 3.2 GAE（广义优势估计）

```python
class GAEAdvantageComputer:
    """GAE优势函数计算器"""
    def __init__(self, gamma=0.99, lambda_=0.95):
        self.gamma = gamma
        self.lambda_ = lambda_
    
    def compute_gae_advantages(self, rewards, values, next_value, dones):
        """计算GAE优势"""
        advantages = []
        gae = 0
        
        # 添加bootstrap value
        values = values + [next_value]
        
        # 反向计算GAE
        for step in reversed(range(len(rewards))):
            delta = rewards[step] + self.gamma * values[step + 1] * (1 - dones[step]) - values[step]
            gae = delta + self.gamma * self.lambda_ * (1 - dones[step]) * gae
            advantages.insert(0, gae)
        
        # 计算returns
        returns = [adv + val for adv, val in zip(advantages, values[:-1])]
        
        return advantages, returns
    
    def normalize_advantages(self, advantages):
        """标准化优势"""
        advantages = np.array(advantages)
        return (advantages - advantages.mean()) / (advantages.std() + 1e-8)

class A3CWorkerWithGAE(A3CWorker):
    """使用GAE的A3C Worker"""
    def __init__(self, worker_id, global_network, config):
        super().__init__(worker_id, global_network, config)
        self.gae_computer = GAEAdvantageComputer(config.gamma, config.lambda_)
        self.dones = []  # 添加done标志记录
    
    def run_episode(self):
        """运行单个episode（GAE版本）"""
        state = self.env.reset()
        episode_reward = 0
        episode_length = 0
        
        # 清空经验缓存
        self.clear_experience_buffer()
        
        while not self.env.is_done() and episode_length < self.config.max_episode_length:
            # 获取合法动作
            legal_actions = self.env.get_legal_actions()
            action_mask = self.create_action_mask(legal_actions)
            
            # 选择动作
            with torch.no_grad():
                state_tensor = torch.tensor(state, dtype=torch.float32).unsqueeze(0)
                action, log_prob, entropy, value = self.local_network.get_action_and_value(
                    state_tensor, action_mask.unsqueeze(0)
                )
                
                action = action.item()
                log_prob = log_prob.item()
                entropy = entropy.item()
                value = value.item()
            
            # 执行动作
            next_state, reward, done, info = self.env.step(action)
            
            # 存储经验
            self.states.append(state)
            self.actions.append(action)
            self.rewards.append(reward)
            self.values.append(value)
            self.log_probs.append(log_prob)
            self.entropies.append(entropy)
            self.action_masks.append(action_mask)
            self.dones.append(done)
            
            # 更新状态
            state = next_state
            episode_reward += reward
            episode_length += 1
            self.step_count += 1
            
            # 定期更新或episode结束时更新
            if (len(self.states) >= self.config.n_steps or done or 
                episode_length >= self.config.max_episode_length):
                
                # 计算最后状态的价值
                if done:
                    next_value = 0.0
                else:
                    with torch.no_grad():
                        state_tensor = torch.tensor(state, dtype=torch.float32).unsqueeze(0)
                        _, next_value, _ = self.local_network(state_tensor)
                        next_value = next_value.item()
                
                # 更新网络
                self.update_network_with_gae(next_value)
                
                # 清空缓存
                self.clear_experience_buffer()
        
        return episode_reward
    
    def update_network_with_gae(self, next_value):
        """使用GAE更新网络参数"""
        if len(self.states) == 0:
            return
        
        # 计算GAE优势和回报
        advantages, returns = self.gae_computer.compute_gae_advantages(
            self.rewards, self.values, next_value, self.dones
        )
        
        # 标准化优势
        advantages = self.gae_computer.normalize_advantages(advantages)
        
        # 转换为tensor
        states_tensor = torch.stack([torch.tensor(s, dtype=torch.float32) for s in self.states])
        actions_tensor = torch.tensor(self.actions, dtype=torch.long)
        returns_tensor = torch.tensor(returns, dtype=torch.float32)
        advantages_tensor = torch.tensor(advantages, dtype=torch.float32)
        action_masks_tensor = torch.stack(self.action_masks)
        
        # 前向传播
        policy_probs, values, policy_logits = self.local_network(states_tensor, action_masks_tensor)
        
        # 计算新的log概率和熵
        dist = torch.distributions.Categorical(policy_probs)
        new_log_probs = dist.log_prob(actions_tensor)
        entropy = dist.entropy()
        
        # 计算损失
        # Actor损失（策略梯度）
        actor_loss = -(advantages_tensor * new_log_probs).mean()
        
        # Critic损失（价值函数）
        critic_loss = F.mse_loss(values, returns_tensor)
        
        # 熵损失（鼓励探索）
        entropy_loss = -entropy.mean()
        
        # 总损失
        total_loss = (actor_loss + 
                     self.config.value_loss_coef * critic_loss + 
                     self.config.entropy_coef * entropy_loss)
        
        # 计算梯度
        self.local_network.zero_grad()
        total_loss.backward()
        
        # 收集梯度
        local_gradients = []
        for param in self.local_network.parameters():
            if param.grad is not None:
                local_gradients.append(param.grad.clone())
            else:
                local_gradients.append(torch.zeros_like(param))
        
        # 更新全局网络
        self.global_network.update_global_network(local_gradients)
    
    def clear_experience_buffer(self):
        """清空经验缓存（GAE版本）"""
        super().clear_experience_buffer()
        self.dones.clear()
```

## 4. 训练配置参数

### 4.1 A3C核心参数

```python
@dataclass
class A3CTrainingConfig:
    # 网络更新参数
    learning_rate: float = 1e-4
    weight_decay: float = 1e-5
    
    # A3C特定参数
    n_steps: int = 20  # 每n步更新一次
    max_episode_length: int = 1000
    max_global_steps: int = 10000000
    
    # 折扣因子
    gamma: float = 0.99
    
    # GAE参数
    use_gae: bool = True
    lambda_: float = 0.95  # GAE lambda
    
    # 损失权重
    value_loss_coef: float = 0.5
    entropy_coef: float = 0.01
    
    # 梯度裁剪
    max_grad_norm: float = 0.5
    
    # 多进程参数
    num_workers: int = 8
    
    # 日志和保存
    log_frequency: int = 100
    save_frequency: int = 10000
    eval_frequency: int = 5000
    
    # 环境参数
    env_name: str = "sanguosha"
    render: bool = False
```

### 4.2 三国杀特定配置

```python
@dataclass
class SanguoshaA3CConfig:
    # 奖励塑形
    reward_shaping: Dict[str, float] = field(default_factory=lambda: {
        'win_bonus': 100.0,
        'lose_penalty': -50.0,
        'survival_reward': 0.1,
        'damage_reward': 2.0,
        'heal_reward': 1.5,
        'card_efficiency': 0.5,
        'invalid_action_penalty': -5.0,
        'cooperation_bonus': 3.0,  # 合作奖励
        'betrayal_penalty': -2.0   # 背叛惩罚
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
            'global_steps': 1000000,
            'opponents': 'random',
            'entropy_coef': 0.02
        },
        {
            'name': 'intermediate',
            'global_steps': 3000000,
            'opponents': 'rule_based',
            'entropy_coef': 0.01
        },
        {
            'name': 'advanced',
            'global_steps': 6000000,
            'opponents': 'mixed',
            'entropy_coef': 0.005
        }
    ])
    
    # 多智能体设置
    self_play_enabled: bool = True
    self_play_ratio: float = 0.3
    opponent_update_frequency: int = 50000
    
    # 探索策略
    exploration_strategies: List[str] = field(default_factory=lambda: [
        'entropy_bonus',
        'curiosity_driven',
        'count_based'
    ])
    
    # 网络架构变体
    use_lstm: bool = False
    lstm_hidden_size: int = 256
    use_attention: bool = True
    attention_heads: int = 8
```

## 5. 训练流程实现

### 5.1 主训练器

```python
class A3CSanguoshaTrainer:
    def __init__(self, config):
        self.config = config
        
        # 创建全局网络
        self.global_network = A3CGlobalNetwork(config)
        
        # 创建评估器
        self.evaluator = A3CEvaluator(config)
        
        # 创建日志记录器
        self.logger = TrainingLogger(config)
        
        # 课程学习管理器
        if config.curriculum_learning:
            self.curriculum = CurriculumLearning(config)
        
        # 训练统计
        self.start_time = time.time()
        
    def train(self):
        """主训练流程"""
        print(f"开始A3C训练，使用 {self.config.num_workers} 个worker...")
        
        # 创建worker进程
        processes = []
        for worker_id in range(self.config.num_workers):
            if self.config.use_gae:
                worker = A3CWorkerWithGAE(worker_id, self.global_network, self.config)
            else:
                worker = A3CWorker(worker_id, self.global_network, self.config)
            
            process = mp.Process(target=worker.run)
            process.start()
            processes.append(process)
        
        # 主进程监控和评估
        self.monitor_training()
        
        # 等待所有worker完成
        for process in processes:
            process.join()
        
        print("A3C训练完成！")
    
    def monitor_training(self):
        """监控训练进度"""
        last_eval_step = 0
        last_save_step = 0
        
        while self.global_network.global_step.value < self.config.max_global_steps:
            current_step = self.global_network.global_step.value
            current_episode = self.global_network.global_episode.value
            
            # 定期评估
            if current_step - last_eval_step >= self.config.eval_frequency:
                eval_results = self.evaluator.evaluate(self.global_network.network)
                self.logger.log_evaluation(eval_results, current_step)
                
                # 更新最佳性能
                if eval_results['win_rate'] > self.global_network.best_score.value:
                    with self.global_network.best_score.get_lock():
                        self.global_network.best_score.value = eval_results['win_rate']
                    
                    # 保存最佳模型
                    self.global_network.save_model(f"best_a3c_model_step{current_step}.pth")
                
                last_eval_step = current_step
            
            # 定期保存
            if current_step - last_save_step >= self.config.save_frequency:
                self.global_network.save_model(f"a3c_checkpoint_step{current_step}.pth")
                last_save_step = current_step
            
            # 更新课程学习
            if hasattr(self, 'curriculum'):
                self.curriculum.update(current_step)
            
            # 打印进度
            if current_step % 10000 == 0:
                elapsed_time = time.time() - self.start_time
                steps_per_sec = current_step / elapsed_time if elapsed_time > 0 else 0
                print(f"Global Step: {current_step}, Episode: {current_episode}, "
                      f"Steps/sec: {steps_per_sec:.2f}, "
                      f"Best Score: {self.global_network.best_score.value:.3f}")
            
            time.sleep(10)  # 每10秒检查一次
```

### 5.2 LSTM增强版本

```python
class A3CLSTMNetwork(nn.Module):
    """带LSTM的A3C网络"""
    def __init__(self, config):
        super().__init__()
        self.config = config
        
        # 状态编码器
        self.state_encoder = StateEncoder(
            state_dim=config.state_dim,
            hidden_dim=config.hidden_dim,
            attention_heads=config.attention_heads
        )
        
        # LSTM层
        self.lstm = nn.LSTM(
            input_size=config.hidden_dim,
            hidden_size=config.lstm_hidden_size,
            num_layers=1,
            batch_first=True
        )
        
        # Actor网络
        self.actor = nn.Sequential(
            nn.Linear(config.lstm_hidden_size, config.actor_hidden_layers[0]),
            nn.ReLU(),
            nn.Dropout(config.dropout_rate),
            nn.Linear(config.actor_hidden_layers[0], config.action_dim)
        )
        
        # Critic网络
        self.critic = nn.Sequential(
            nn.Linear(config.lstm_hidden_size, config.critic_hidden_layers[0]),
            nn.ReLU(),
            nn.Dropout(config.dropout_rate),
            nn.Linear(config.critic_hidden_layers[0], 1)
        )
        
        # 初始化LSTM隐藏状态
        self.hidden_size = config.lstm_hidden_size
        
    def forward(self, state, hidden_state=None, action_mask=None):
        batch_size = state.size(0)
        seq_len = state.size(1) if len(state.shape) == 3 else 1
        
        # 如果输入是2D，添加序列维度
        if len(state.shape) == 2:
            state = state.unsqueeze(1)
        
        # 状态编码
        encoded_state = self.state_encoder(state.view(-1, state.size(-1)))
        encoded_state = encoded_state.view(batch_size, seq_len, -1)
        
        # LSTM前向传播
        if hidden_state is None:
            hidden_state = self.init_hidden(batch_size, state.device)
        
        lstm_out, new_hidden_state = self.lstm(encoded_state, hidden_state)
        
        # 取最后一个时间步的输出
        lstm_out = lstm_out[:, -1, :]
        
        # Actor和Critic输出
        policy_logits = self.actor(lstm_out)
        state_value = self.critic(lstm_out).squeeze(-1)
        
        # 应用动作掩码
        if action_mask is not None:
            if len(action_mask.shape) == 3:
                action_mask = action_mask[:, -1, :]  # 取最后一个时间步
            policy_logits = policy_logits.masked_fill(~action_mask, -1e9)
        
        # 策略概率分布
        policy_probs = F.softmax(policy_logits, dim=-1)
        
        return policy_probs, state_value, policy_logits, new_hidden_state
    
    def init_hidden(self, batch_size, device):
        """初始化LSTM隐藏状态"""
        h0 = torch.zeros(1, batch_size, self.hidden_size).to(device)
        c0 = torch.zeros(1, batch_size, self.hidden_size).to(device)
        return (h0, c0)
    
    def get_action_and_value(self, state, hidden_state=None, action_mask=None):
        """获取动作和价值（LSTM版本）"""
        policy_probs, state_value, policy_logits, new_hidden_state = self.forward(
            state, hidden_state, action_mask
        )
        
        # 创建分布
        if action_mask is not None:
            masked_probs = policy_probs * action_mask.float()
            masked_probs = masked_probs / masked_probs.sum(dim=-1, keepdim=True)
            dist = torch.distributions.Categorical(masked_probs)
        else:
            dist = torch.distributions.Categorical(policy_probs)
        
        # 采样动作
        action = dist.sample()
        log_prob = dist.log_prob(action)
        entropy = dist.entropy()
        
        return action, log_prob, entropy, state_value, new_hidden_state

class A3CLSTMWorker(A3CWorkerWithGAE):
    """使用LSTM的A3C Worker"""
    def __init__(self, worker_id, global_network, config):
        super().__init__(worker_id, global_network, config)
        
        # 替换为LSTM网络
        self.local_network = A3CLSTMNetwork(config)
        
        # LSTM隐藏状态
        self.hidden_states = []
        self.current_hidden_state = None
    
    def run_episode(self):
        """运行单个episode（LSTM版本）"""
        state = self.env.reset()
        episode_reward = 0
        episode_length = 0
        
        # 重置LSTM隐藏状态
        self.current_hidden_state = None
        
        # 清空经验缓存
        self.clear_experience_buffer()
        
        while not self.env.is_done() and episode_length < self.config.max_episode_length:
            # 获取合法动作
            legal_actions = self.env.get_legal_actions()
            action_mask = self.create_action_mask(legal_actions)
            
            # 选择动作
            with torch.no_grad():
                state_tensor = torch.tensor(state, dtype=torch.float32).unsqueeze(0)
                action, log_prob, entropy, value, new_hidden_state = self.local_network.get_action_and_value(
                    state_tensor, self.current_hidden_state, action_mask.unsqueeze(0)
                )
                
                action = action.item()
                log_prob = log_prob.item()
                entropy = entropy.item()
                value = value.item()
                
                # 更新隐藏状态
                self.current_hidden_state = new_hidden_state
            
            # 执行动作
            next_state, reward, done, info = self.env.step(action)
            
            # 存储经验
            self.states.append(state)
            self.actions.append(action)
            self.rewards.append(reward)
            self.values.append(value)
            self.log_probs.append(log_prob)
            self.entropies.append(entropy)
            self.action_masks.append(action_mask)
            self.dones.append(done)
            self.hidden_states.append(self.current_hidden_state)
            
            # 更新状态
            state = next_state
            episode_reward += reward
            episode_length += 1
            self.step_count += 1
            
            # 定期更新或episode结束时更新
            if (len(self.states) >= self.config.n_steps or done or 
                episode_length >= self.config.max_episode_length):
                
                # 计算最后状态的价值
                if done:
                    next_value = 0.0
                else:
                    with torch.no_grad():
                        state_tensor = torch.tensor(state, dtype=torch.float32).unsqueeze(0)
                        _, next_value, _, _ = self.local_network(state_tensor, self.current_hidden_state)
                        next_value = next_value.item()
                
                # 更新网络
                self.update_network_with_gae(next_value)
                
                # 清空缓存
                self.clear_experience_buffer()
        
        return episode_reward
    
    def clear_experience_buffer(self):
        """清空经验缓存（LSTM版本）"""
        super().clear_experience_buffer()
        self.hidden_states.clear()
```

## 6. 高级技术优化

### 6.1 好奇心驱动探索

```python
class CuriosityModule(nn.Module):
    """好奇心驱动探索模块"""
    def __init__(self, config):
        super().__init__()
        self.config = config
        
        # 特征编码器
        self.feature_encoder = nn.Sequential(
            nn.Linear(config.state_dim, config.curiosity_hidden_dim),
            nn.ReLU(),
            nn.Linear(config.curiosity_hidden_dim, config.feature_dim)
        )
        
        # 逆向模型（预测动作）
        self.inverse_model = nn.Sequential(
            nn.Linear(config.feature_dim * 2, config.curiosity_hidden_dim),
            nn.ReLU(),
            nn.Linear(config.curiosity_hidden_dim, config.action_dim)
        )
        
        # 前向模型（预测下一状态特征）
        self.forward_model = nn.Sequential(
            nn.Linear(config.feature_dim + config.action_dim, config.curiosity_hidden_dim),
            nn.ReLU(),
            nn.Linear(config.curiosity_hidden_dim, config.feature_dim)
        )
    
    def forward(self, state, next_state, action):
        # 编码状态特征
        state_features = self.feature_encoder(state)
        next_state_features = self.feature_encoder(next_state)
        
        # 逆向模型预测
        inverse_input = torch.cat([state_features, next_state_features], dim=-1)
        predicted_action = self.inverse_model(inverse_input)
        
        # 前向模型预测
        action_onehot = F.one_hot(action, num_classes=self.config.action_dim).float()
        forward_input = torch.cat([state_features, action_onehot], dim=-1)
        predicted_next_features = self.forward_model(forward_input)
        
        # 计算内在奖励（预测误差）
        intrinsic_reward = F.mse_loss(
            predicted_next_features, 
            next_state_features.detach(), 
            reduction='none'
        ).mean(dim=-1)
        
        return intrinsic_reward, predicted_action, predicted_next_features

class A3CWorkerWithCuriosity(A3CWorkerWithGAE):
    """带好奇心驱动的A3C Worker"""
    def __init__(self, worker_id, global_network, config):
        super().__init__(worker_id, global_network, config)
        
        # 好奇心模块
        self.curiosity_module = CuriosityModule(config)
        
        # 好奇心优化器
        self.curiosity_optimizer = torch.optim.Adam(
            self.curiosity_module.parameters(),
            lr=config.curiosity_lr
        )
        
        # 内在奖励记录
        self.intrinsic_rewards = []
    
    def run_episode(self):
        """运行单个episode（好奇心版本）"""
        state = self.env.reset()
        episode_reward = 0
        episode_intrinsic_reward = 0
        episode_length = 0
        
        # 清空经验缓存
        self.clear_experience_buffer()
        
        while not self.env.is_done() and episode_length < self.config.max_episode_length:
            # 获取合法动作
            legal_actions = self.env.get_legal_actions()
            action_mask = self.create_action_mask(legal_actions)
            
            # 选择动作
            with torch.no_grad():
                state_tensor = torch.tensor(state, dtype=torch.float32).unsqueeze(0)
                action, log_prob, entropy, value = self.local_network.get_action_and_value(
                    state_tensor, action_mask.unsqueeze(0)
                )
                
                action = action.item()
                log_prob = log_prob.item()
                entropy = entropy.item()
                value = value.item()
            
            # 执行动作
            next_state, reward, done, info = self.env.step(action)
            
            # 计算内在奖励
            with torch.no_grad():
                state_tensor = torch.tensor(state, dtype=torch.float32).unsqueeze(0)
                next_state_tensor = torch.tensor(next_state, dtype=torch.float32).unsqueeze(0)
                action_tensor = torch.tensor([action], dtype=torch.long)
                
                intrinsic_reward, _, _ = self.curiosity_module(
                    state_tensor, next_state_tensor, action_tensor
                )
                intrinsic_reward = intrinsic_reward.item()
            
            # 组合外在和内在奖励
            total_reward = reward + self.config.intrinsic_reward_coef * intrinsic_reward
            
            # 存储经验
            self.states.append(state)
            self.actions.append(action)
            self.rewards.append(total_reward)  # 使用组合奖励
            self.values.append(value)
            self.log_probs.append(log_prob)
            self.entropies.append(entropy)
            self.action_masks.append(action_mask)
            self.dones.append(done)
            self.intrinsic_rewards.append(intrinsic_reward)
            
            # 更新状态
            state = next_state
            episode_reward += reward
            episode_intrinsic_reward += intrinsic_reward
            episode_length += 1
            self.step_count += 1
            
            # 定期更新或episode结束时更新
            if (len(self.states) >= self.config.n_steps or done or 
                episode_length >= self.config.max_episode_length):
                
                # 计算最后状态的价值
                if done:
                    next_value = 0.0
                else:
                    with torch.no_grad():
                        state_tensor = torch.tensor(state, dtype=torch.float32).unsqueeze(0)
                        _, next_value, _ = self.local_network(state_tensor)
                        next_value = next_value.item()
                
                # 更新网络
                self.update_network_with_curiosity(next_value)
                
                # 清空缓存
                self.clear_experience_buffer()
        
        return episode_reward, episode_intrinsic_reward
    
    def update_network_with_curiosity(self, next_value):
        """使用好奇心模块更新网络"""
        if len(self.states) == 0:
            return
        
        # 标准A3C更新
        self.update_network_with_gae(next_value)
        
        # 更新好奇心模块
        self.update_curiosity_module()
    
    def update_curiosity_module(self):
        """更新好奇心模块"""
        if len(self.states) < 2:
            return
        
        # 准备数据
        states = torch.stack([torch.tensor(s, dtype=torch.float32) for s in self.states[:-1]])
        next_states = torch.stack([torch.tensor(s, dtype=torch.float32) for s in self.states[1:]])
        actions = torch.tensor(self.actions[:-1], dtype=torch.long)
        
        # 前向传播
        intrinsic_rewards, predicted_actions, predicted_next_features = self.curiosity_module(
            states, next_states, actions
        )
        
        # 计算损失
        # 逆向模型损失
        inverse_loss = F.cross_entropy(predicted_actions, actions)
        
        # 前向模型损失（已在模块内计算）
        forward_loss = intrinsic_rewards.mean()
        
        # 总损失
        curiosity_loss = (self.config.inverse_loss_coef * inverse_loss + 
                         self.config.forward_loss_coef * forward_loss)
        
        # 更新好奇心模块
        self.curiosity_optimizer.zero_grad()
        curiosity_loss.backward()
        self.curiosity_optimizer.step()
    
    def clear_experience_buffer(self):
        """清空经验缓存（好奇心版本）"""
        super().clear_experience_buffer()
        self.intrinsic_rewards.clear()
```

### 6.2 分层强化学习

```python
class HierarchicalA3C:
    """分层A3C实现"""
    def __init__(self, config):
        self.config = config
        
        # 高层策略网络（选择子目标）
        self.high_level_network = A3CNetwork(config.high_level_config)
        
        # 低层策略网络（执行原子动作）
        self.low_level_network = A3CNetwork(config.low_level_config)
        
        # 子目标定义
        self.subgoals = self.define_subgoals()
        
    def define_subgoals(self):
        """定义三国杀中的子目标"""
        return {
            0: "survive",      # 生存
            1: "attack",       # 攻击
            2: "defend",       # 防御
            3: "support",      # 支援
            4: "collect",      # 收集资源
            5: "special"       # 使用特殊技能
        }
    
    def select_hierarchical_action(self, state, timestep):
        """分层动作选择"""
        # 高层决策（每k步选择一次子目标）
        if timestep % self.config.subgoal_duration == 0:
            with torch.no_grad():
                state_tensor = torch.tensor(state, dtype=torch.float32).unsqueeze(0)
                subgoal_probs, _, _ = self.high_level_network(state_tensor)
                subgoal_dist = torch.distributions.Categorical(subgoal_probs)
                self.current_subgoal = subgoal_dist.sample().item()
        
        # 低层决策（根据子目标选择具体动作）
        conditioned_state = self.condition_state_on_subgoal(state, self.current_subgoal)
        
        with torch.no_grad():
            conditioned_state_tensor = torch.tensor(conditioned_state, dtype=torch.float32).unsqueeze(0)
            action_probs, value, _ = self.low_level_network(conditioned_state_tensor)
            action_dist = torch.distributions.Categorical(action_probs)
            action = action_dist.sample().item()
        
        return action, self.current_subgoal
    
    def condition_state_on_subgoal(self, state, subgoal):
        """根据子目标调整状态表示"""
        # 在状态向量中添加子目标信息
        subgoal_onehot = np.zeros(len(self.subgoals))
        subgoal_onehot[subgoal] = 1.0
        
        conditioned_state = np.concatenate([state, subgoal_onehot])
        return conditioned_state
```

## 7. 评估与分析

### 7.1 A3C性能评估

```python
class A3CEvaluator:
    """A3C性能评估器"""
    def __init__(self, config):
        self.config = config
        self.eval_env = create_sanguosha_env(config, eval_mode=True)
        
    def evaluate(self, network, num_episodes=100):
        """评估网络性能"""
        network.eval()
        
        results = {
            'win_rate': 0.0,
            'avg_reward': 0.0,
            'avg_episode_length': 0.0,
            'avg_survival_time': 0.0,
            'action_distribution': np.zeros(self.config.action_dim),
            'value_estimates': []
        }
        
        total_reward = 0
        total_length = 0
        total_survival = 0
        wins = 0
        
        for episode in range(num_episodes):
            state = self.eval_env.reset()
            episode_reward = 0
            episode_length = 0
            episode_actions = []
            episode_values = []
            
            while not self.eval_env.is_done():
                legal_actions = self.eval_env.get_legal_actions()
                action_mask = self.create_action_mask(legal_actions)
                
                with torch.no_grad():
                    state_tensor = torch.tensor(state, dtype=torch.float32).unsqueeze(0)
                    action, _, _, value = network.get_action_and_value(
                        state_tensor, action_mask.unsqueeze(0)
                    )
                    
                    action = action.item()
                    value = value.item()
                
                next_state, reward, done, info = self.eval_env.step(action)
                
                episode_actions.append(action)
                episode_values.append(value)
                episode_reward += reward
                episode_length += 1
                
                state = next_state
            
            # 统计结果
            if self.eval_env.did_player_win():
                wins += 1
            
            total_reward += episode_reward
            total_length += episode_length
            total_survival += self.eval_env.get_survival_time()
            
            # 动作分布统计
            for action in episode_actions:
                results['action_distribution'][action] += 1
            
            results['value_estimates'].extend(episode_values)
        
        # 计算平均值
        results['win_rate'] = wins / num_episodes
        results['avg_reward'] = total_reward / num_episodes
        results['avg_episode_length'] = total_length / num_episodes
        results['avg_survival_time'] = total_survival / num_episodes
        
        # 归一化动作分布
        total_actions = results['action_distribution'].sum()
        if total_actions > 0:
            results['action_distribution'] /= total_actions
        
        network.train()
        return results
    
    def create_action_mask(self, legal_actions):
        """创建动作掩码"""
        mask = torch.zeros(self.config.action_dim, dtype=torch.bool)
        if legal_actions:
            mask[legal_actions] = True
        return mask
    
    def analyze_policy_entropy(self, network, test_states):
        """分析策略熵"""
        network.eval()
        entropies = []
        
        with torch.no_grad():
            for state in test_states:
                state_tensor = torch.tensor(state, dtype=torch.float32).unsqueeze(0)
                policy_probs, _, _ = network(state_tensor)
                
                dist = torch.distributions.Categorical(policy_probs)
                entropy = dist.entropy().item()
                entropies.append(entropy)
        
        network.train()
        return {
            'mean_entropy': np.mean(entropies),
            'std_entropy': np.std(entropies),
            'min_entropy': np.min(entropies),
            'max_entropy': np.max(entropies)
        }
```

### 7.2 训练诊断工具

```python
class A3CDiagnostics:
    """A3C训练诊断工具"""
    def __init__(self):
        self.metrics = {
            'actor_loss': [],
            'critic_loss': [],
            'entropy_loss': [],
            'total_loss': [],
            'policy_entropy': [],
            'value_estimates': [],
            'advantages': [],
            'gradient_norms': []
        }
    
    def update_metrics(self, loss_info, gradients):
        """更新诊断指标"""
        self.metrics['actor_loss'].append(loss_info.get('actor_loss', 0))
        self.metrics['critic_loss'].append(loss_info.get('critic_loss', 0))
        self.metrics['entropy_loss'].append(loss_info.get('entropy_loss', 0))
        self.metrics['total_loss'].append(loss_info.get('total_loss', 0))
        self.metrics['policy_entropy'].append(loss_info.get('entropy', 0))
        self.metrics['value_estimates'].extend(loss_info.get('values', []))
        self.metrics['advantages'].extend(loss_info.get('advantages', []))
        
        # 计算梯度范数
        grad_norm = sum(grad.norm().item() for grad in gradients if grad is not None)
        self.metrics['gradient_norms'].append(grad_norm)
    
    def plot_diagnostics(self):
        """绘制诊断图表"""
        fig, axes = plt.subplots(2, 4, figsize=(20, 10))
        
        # 损失曲线
        axes[0, 0].plot(self.metrics['actor_loss'], label='Actor Loss')
        axes[0, 0].plot(self.metrics['critic_loss'], label='Critic Loss')
        axes[0, 0].plot(self.metrics['total_loss'], label='Total Loss')
        axes[0, 0].set_title('Training Losses')
        axes[0, 0].legend()
        
        # 策略熵
        axes[0, 1].plot(self.metrics['policy_entropy'])
        axes[0, 1].set_title('Policy Entropy')
        
        # 价值估计分布
        if self.metrics['value_estimates']:
            axes[0, 2].hist(self.metrics['value_estimates'][-1000:], bins=50, alpha=0.7)
            axes[0, 2].set_title('Value Estimates Distribution')
        
        # 优势分布
        if self.metrics['advantages']:
            axes[0, 3].hist(self.metrics['advantages'][-1000:], bins=50, alpha=0.7)
            axes[0, 3].set_title('Advantages Distribution')
        
        # 梯度范数
        axes[1, 0].plot(self.metrics['gradient_norms'])
        axes[1, 0].set_title('Gradient Norms')
        
        # 损失比例
        if len(self.metrics['total_loss']) > 0:
            recent_actor = np.mean(self.metrics['actor_loss'][-100:])
            recent_critic = np.mean(self.metrics['critic_loss'][-100:])
            recent_entropy = np.mean(self.metrics['entropy_loss'][-100:])
            
            axes[1, 1].pie([recent_actor, recent_critic, abs(recent_entropy)], 
                          labels=['Actor', 'Critic', 'Entropy'],
                          autopct='%1.1f%%')
            axes[1, 1].set_title('Loss Components Ratio')
        
        # 训练稳定性指标
        if len(self.metrics['total_loss']) > 100:
            window_size = 100
            rolling_std = []
            for i in range(window_size, len(self.metrics['total_loss'])):
                window = self.metrics['total_loss'][i-window_size:i]
                rolling_std.append(np.std(window))
            
            axes[1, 2].plot(rolling_std)
            axes[1, 2].set_title('Training Stability (Rolling Std)')
        
        # 学习进度
        if len(self.metrics['value_estimates']) > 1000:
            # 计算价值估计的变化趋势
            window_size = 500
            value_trends = []
            for i in range(window_size, len(self.metrics['value_estimates']), window_size):
                window = self.metrics['value_estimates'][i-window_size:i]
                value_trends.append(np.mean(window))
            
            axes[1, 3].plot(value_trends)
            axes[1, 3].set_title('Value Estimation Trend')
        
        plt.tight_layout()
        plt.show()
    
    def diagnose_issues(self):
        """诊断训练问题"""
        issues = []
        
        # 检查梯度爆炸
        if len(self.metrics['gradient_norms']) > 10:
            recent_grads = self.metrics['gradient_norms'][-10:]
            if np.mean(recent_grads) > 10.0:
                issues.append("梯度爆炸：建议降低学习率或增强梯度裁剪")
        
        # 检查梯度消失
        if len(self.metrics['gradient_norms']) > 10:
            recent_grads = self.metrics['gradient_norms'][-10:]
            if np.mean(recent_grads) < 1e-6:
                issues.append("梯度消失：建议检查网络初始化或增加学习率")
        
        # 检查策略熵
        if len(self.metrics['policy_entropy']) > 100:
            recent_entropy = self.metrics['policy_entropy'][-100:]
            if np.mean(recent_entropy) < 0.1:
                issues.append("策略过于确定：建议增加熵系数")
            elif np.mean(recent_entropy) > 2.0:
                issues.append("策略过于随机：建议降低熵系数")
        
        # 检查价值函数学习
        if len(self.metrics['critic_loss']) > 100:
            recent_critic_loss = self.metrics['critic_loss'][-100:]
            if np.std(recent_critic_loss) < 1e-6:
                issues.append("价值函数学习停滞：建议检查奖励设计")
        
        return issues
```

## 8. 部署与优化

### 8.1 模型压缩

```python
class A3CModelCompressor:
    """A3C模型压缩器"""
    def __init__(self, config):
        self.config = config
    
    def quantize_model(self, model, quantization_type='dynamic'):
        """模型量化"""
        if quantization_type == 'dynamic':
            quantized_model = torch.quantization.quantize_dynamic(
                model, {nn.Linear}, dtype=torch.qint8
            )
        elif quantization_type == 'static':
            # 静态量化需要校准数据
            model.qconfig = torch.quantization.get_default_qconfig('fbgemm')
            torch.quantization.prepare(model, inplace=True)
            # 这里需要运行校准数据
            torch.quantization.convert(model, inplace=True)
            quantized_model = model
        
        return quantized_model
    
    def prune_model(self, model, pruning_ratio=0.2):
        """模型剪枝"""
        import torch.nn.utils.prune as prune
        
        # 结构化剪枝
        for name, module in model.named_modules():
            if isinstance(module, nn.Linear):
                prune.l1_unstructured(module, name='weight', amount=pruning_ratio)
                prune.remove(module, 'weight')
        
        return model
    
    def distill_model(self, teacher_model, student_config, distillation_data):
        """知识蒸馏"""
        # 创建学生模型（更小的网络）
        student_model = A3CNetwork(student_config)
        
        # 蒸馏损失函数
        def distillation_loss(student_logits, teacher_logits, temperature=3.0):
            teacher_probs = F.softmax(teacher_logits / temperature, dim=-1)
            student_log_probs = F.log_softmax(student_logits / temperature, dim=-1)
            return F.kl_div(student_log_probs, teacher_probs, reduction='batchmean')
        
        # 训练学生模型
        optimizer = torch.optim.Adam(student_model.parameters(), lr=1e-4)
        
        for epoch in range(self.config.distillation_epochs):
            for batch in distillation_data:
                states, actions, rewards = batch
                
                # 教师模型输出
                with torch.no_grad():
                    teacher_probs, teacher_values, teacher_logits = teacher_model(states)
                
                # 学生模型输出
                student_probs, student_values, student_logits = student_model(states)
                
                # 计算损失
                policy_loss = distillation_loss(student_logits, teacher_logits)
                value_loss = F.mse_loss(student_values, teacher_values)
                
                total_loss = policy_loss + 0.5 * value_loss
                
                # 更新学生模型
                optimizer.zero_grad()
                total_loss.backward()
                optimizer.step()
        
        return student_model

### 8.2 推理优化

class A3CInferenceOptimizer:
    """A3C推理优化器"""
    def __init__(self, model, config):
        self.model = model
        self.config = config
        
        # 编译模型以提高推理速度
        if hasattr(torch, 'jit'):
            self.model = torch.jit.script(model)
    
    def batch_inference(self, states, action_masks=None):
        """批量推理"""
        self.model.eval()
        
        with torch.no_grad():
            if action_masks is not None:
                policy_probs, values, _ = self.model(states, action_masks)
            else:
                policy_probs, values, _ = self.model(states)
            
            # 批量采样动作
            dists = torch.distributions.Categorical(policy_probs)
            actions = dists.sample()
            log_probs = dists.log_prob(actions)
            
        return actions, log_probs, values
    
    def optimize_for_mobile(self, model):
        """移动端优化"""
        # 转换为移动端格式
        model.eval()
        example_input = torch.randn(1, self.config.state_dim)
        
        traced_model = torch.jit.trace(model, example_input)
        optimized_model = torch.utils.mobile_optimizer.optimize_for_mobile(traced_model)
        
        return optimized_model
```

## 9. 实际部署指南

### 9.1 训练脚本

```python
# train_a3c.py
import multiprocessing as mp
from ai.A3C算法训练方案 import *

def main():
    # 配置参数
    config = A3CTrainingConfig(
        learning_rate=1e-4,
        num_workers=8,
        max_global_steps=10000000,
        n_steps=20,
        gamma=0.99,
        use_gae=True,
        lambda_=0.95
    )
    
    # 创建训练器
    trainer = A3CSanguoshaTrainer(config)
    
    # 开始训练
    trainer.train()

if __name__ == "__main__":
    mp.set_start_method('spawn')  # 设置多进程启动方法
    main()
```

### 9.2 推理脚本

```python
# inference_a3c.py
import torch
from ai.A3C算法训练方案 import A3CNetwork, A3CNetworkConfig

def load_trained_model(model_path):
    """加载训练好的模型"""
    checkpoint = torch.load(model_path, map_location='cpu')
    config = checkpoint['config']
    
    model = A3CNetwork(config)
    model.load_state_dict(checkpoint['network_state_dict'])
    model.eval()
    
    return model, config

def play_game_with_a3c(model, env):
    """使用A3C模型进行游戏"""
    state = env.reset()
    total_reward = 0
    
    while not env.is_done():
        # 获取合法动作
        legal_actions = env.get_legal_actions()
        action_mask = create_action_mask(legal_actions, model.config.action_dim)
        
        # 选择动作
        with torch.no_grad():
            state_tensor = torch.tensor(state, dtype=torch.float32).unsqueeze(0)
            action, _, _, _ = model.get_action_and_value(
                state_tensor, action_mask.unsqueeze(0)
            )
            action = action.item()
        
        # 执行动作
        next_state, reward, done, info = env.step(action)
        
        state = next_state
        total_reward += reward
    
    return total_reward

def create_action_mask(legal_actions, action_dim):
    """创建动作掩码"""
    mask = torch.zeros(action_dim, dtype=torch.bool)
    if legal_actions:
        mask[legal_actions] = True
    return mask

if __name__ == "__main__":
    # 加载模型
    model, config = load_trained_model("best_a3c_model.pth")
    
    # 创建环境
    env = create_sanguosha_env(config, eval_mode=True)
    
    # 进行游戏
    reward = play_game_with_a3c(model, env)
    print(f"游戏结束，总奖励: {reward}")
```

## 10. 调参建议

### 10.1 超参数调优

1. **学习率调整**：
   - 初始学习率：1e-4 到 1e-3
   - 使用学习率衰减：每100万步衰减0.9
   - 不同网络组件可使用不同学习率

2. **网络架构**：
   - 隐藏层大小：256-512
   - 注意力头数：4-8
   - Dropout率：0.1-0.3

3. **训练参数**：
   - n_steps：10-50
   - gamma：0.95-0.99
   - lambda（GAE）：0.9-0.98

### 10.2 常见问题解决

1. **训练不稳定**：
   - 降低学习率
   - 增强梯度裁剪
   - 使用GAE

2. **收敛缓慢**：
   - 增加worker数量
   - 调整奖励函数
   - 使用课程学习

3. **过拟合**：
   - 增加Dropout
   - 使用正则化
   - 增加训练数据多样性

## 11. 总结

A3C算法在三国杀AI训练中具有以下优势：
- 异步并行训练，提高效率
- 不需要经验回放，节省内存
- 适合多智能体环境
- 支持连续学习

通过本方案的实施，可以训练出高性能的三国杀AI智能体，并为后续的算法改进和优化提供基础。