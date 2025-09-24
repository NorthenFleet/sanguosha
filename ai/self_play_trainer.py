#!/usr/bin/env python3
"""
三国杀自对弈训练系统
实现多智能体自对弈训练，支持技能进化和策略多样性
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import torch
import numpy as np
import random
import json
import time
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass, asdict
from collections import deque, defaultdict
import matplotlib.pyplot as plt
from pathlib import Path

from .ppo_agent import PPOAgent, PPOConfig, MultiAgentPPO
from .training_environment import SanguoshaEnvironment, TrainingConfig, ActionSpace
from .reward_system import RewardCalculator, RewardConfig, AdaptiveRewardSystem
from .game_state_encoder import GameStateEncoder

@dataclass
class SelfPlayConfig:
    """自对弈训练配置"""
    # 训练参数
    total_episodes: int = 50000
    evaluation_interval: int = 500
    save_interval: int = 1000
    
    # 智能体池参数
    agent_pool_size: int = 8
    opponent_selection_strategy: str = "diverse"  # "random", "strong", "diverse"
    
    # 自对弈参数
    self_play_ratio: float = 0.7
    random_play_ratio: float = 0.2
    historical_play_ratio: float = 0.1
    
    # 技能进化参数
    skill_mutation_rate: float = 0.1
    skill_crossover_rate: float = 0.3
    
    # 评估参数
    evaluation_games: int = 100
    evaluation_opponents: int = 5
    
    # 多样性参数
    diversity_bonus: float = 0.1
    novelty_threshold: float = 0.8

@dataclass
class AgentProfile:
    """智能体档案"""
    agent_id: str
    creation_time: float
    parent_ids: List[str]
    win_rate: float
    games_played: int
    skill_ratings: Dict[str, float]
    strategy_signature: np.ndarray
    performance_history: List[float]

class StrategyAnalyzer:
    """策略分析器"""
    
    def __init__(self):
        self.action_patterns = defaultdict(list)
        self.decision_trees = {}
    
    def analyze_strategy(self, agent: PPOAgent, game_states: List, actions: List) -> np.ndarray:
        """分析智能体的策略特征"""
        if not game_states or not actions:
            return np.zeros(32)  # 默认策略签名长度
        
        features = []
        
        # 1. 动作分布特征
        action_counts = np.bincount(actions, minlength=50)
        action_probs = action_counts / max(len(actions), 1)
        features.extend(action_probs[:10])  # 前10个动作的概率
        
        # 2. 决策时机特征
        aggressive_actions = sum(1 for a in actions if 10 <= a <= 30)  # 卡牌动作
        defensive_actions = sum(1 for a in actions if a == 0)  # 跳过动作
        features.append(aggressive_actions / max(len(actions), 1))
        features.append(defensive_actions / max(len(actions), 1))
        
        # 3. 状态响应特征
        # 分析在不同血量下的行为模式
        low_hp_actions = []
        high_hp_actions = []
        
        for i, state in enumerate(game_states):
            if hasattr(state, 'to_vector'):
                state_vec = state.to_vector()
                hp_ratio = state_vec[0] if len(state_vec) > 0 else 0.5  # 假设第一个特征是血量比例
                
                if hp_ratio < 0.3:
                    low_hp_actions.append(actions[i])
                elif hp_ratio > 0.7:
                    high_hp_actions.append(actions[i])
        
        # 低血量时的激进程度
        low_hp_aggression = sum(1 for a in low_hp_actions if 10 <= a <= 30) / max(len(low_hp_actions), 1)
        high_hp_aggression = sum(1 for a in high_hp_actions if 10 <= a <= 30) / max(len(high_hp_actions), 1)
        
        features.extend([low_hp_aggression, high_hp_aggression])
        
        # 4. 序列模式特征
        # 分析连续动作的模式
        consecutive_patterns = self._analyze_action_sequences(actions)
        features.extend(consecutive_patterns[:5])
        
        # 5. 适应性特征
        # 分析策略在游戏过程中的变化
        early_actions = actions[:len(actions)//3] if actions else []
        late_actions = actions[2*len(actions)//3:] if actions else []
        
        early_aggression = sum(1 for a in early_actions if 10 <= a <= 30) / max(len(early_actions), 1)
        late_aggression = sum(1 for a in late_actions if 10 <= a <= 30) / max(len(late_actions), 1)
        
        features.extend([early_aggression, late_aggression])
        
        # 补齐到32维
        while len(features) < 32:
            features.append(0.0)
        
        return np.array(features[:32])
    
    def _analyze_action_sequences(self, actions: List[int]) -> List[float]:
        """分析动作序列模式"""
        if len(actions) < 2:
            return [0.0] * 5
        
        patterns = []
        
        # 连续相同动作的频率
        consecutive_same = 0
        for i in range(1, len(actions)):
            if actions[i] == actions[i-1]:
                consecutive_same += 1
        patterns.append(consecutive_same / max(len(actions) - 1, 1))
        
        # 动作切换频率
        switches = sum(1 for i in range(1, len(actions)) if actions[i] != actions[i-1])
        patterns.append(switches / max(len(actions) - 1, 1))
        
        # 周期性模式检测（简化）
        period_2 = sum(1 for i in range(2, len(actions)) if actions[i] == actions[i-2])
        patterns.append(period_2 / max(len(actions) - 2, 1))
        
        # 递增/递减趋势
        increasing = sum(1 for i in range(1, len(actions)) if actions[i] > actions[i-1])
        decreasing = sum(1 for i in range(1, len(actions)) if actions[i] < actions[i-1])
        patterns.append(increasing / max(len(actions) - 1, 1))
        patterns.append(decreasing / max(len(actions) - 1, 1))
        
        return patterns

class AgentPool:
    """智能体池管理"""
    
    def __init__(self, config: SelfPlayConfig, ppo_config: PPOConfig):
        self.config = config
        self.ppo_config = ppo_config
        self.agents: Dict[str, PPOAgent] = {}
        self.profiles: Dict[str, AgentProfile] = {}
        self.strategy_analyzer = StrategyAnalyzer()
        
        # 初始化智能体池
        self._initialize_agent_pool()
    
    def _initialize_agent_pool(self):
        """初始化智能体池"""
        for i in range(self.config.agent_pool_size):
            agent_id = f"agent_{i:03d}"
            agent = PPOAgent(self.ppo_config)
            
            # 随机初始化网络参数以增加多样性
            if i > 0:
                self._mutate_agent(agent, mutation_rate=0.1)
            
            profile = AgentProfile(
                agent_id=agent_id,
                creation_time=time.time(),
                parent_ids=[],
                win_rate=0.0,
                games_played=0,
                skill_ratings={},
                strategy_signature=np.zeros(32),
                performance_history=[]
            )
            
            self.agents[agent_id] = agent
            self.profiles[agent_id] = profile
    
    def select_opponent(self, current_agent_id: str, strategy: str = "diverse") -> str:
        """选择对手"""
        available_agents = [aid for aid in self.agents.keys() if aid != current_agent_id]
        
        if not available_agents:
            return current_agent_id  # 自己和自己对战
        
        if strategy == "random":
            return random.choice(available_agents)
        
        elif strategy == "strong":
            # 选择胜率最高的对手
            best_agent = max(available_agents, 
                           key=lambda aid: self.profiles[aid].win_rate)
            return best_agent
        
        elif strategy == "diverse":
            # 选择策略最不同的对手
            current_signature = self.profiles[current_agent_id].strategy_signature
            
            max_distance = -1
            best_opponent = available_agents[0]
            
            for agent_id in available_agents:
                opponent_signature = self.profiles[agent_id].strategy_signature
                distance = np.linalg.norm(current_signature - opponent_signature)
                
                if distance > max_distance:
                    max_distance = distance
                    best_opponent = agent_id
            
            return best_opponent
        
        else:
            return random.choice(available_agents)
    
    def evolve_agent(self, parent_ids: List[str]) -> str:
        """进化产生新智能体"""
        if len(parent_ids) < 1:
            return self._create_random_agent()
        
        # 创建新智能体ID
        new_id = f"evolved_{int(time.time())}_{random.randint(1000, 9999)}"
        
        # 选择最优父代
        best_parent_id = max(parent_ids, key=lambda pid: self.profiles[pid].win_rate)
        parent_agent = self.agents[best_parent_id]
        
        # 创建新智能体
        new_agent = PPOAgent(self.ppo_config)
        
        # 复制父代网络参数
        new_agent.network.load_state_dict(parent_agent.network.state_dict())
        
        # 应用变异
        if random.random() < self.config.skill_mutation_rate:
            self._mutate_agent(new_agent, mutation_rate=0.05)
        
        # 如果有多个父代，进行交叉
        if len(parent_ids) > 1 and random.random() < self.config.skill_crossover_rate:
            other_parent_id = random.choice([pid for pid in parent_ids if pid != best_parent_id])
            self._crossover_agents(new_agent, self.agents[other_parent_id])
        
        # 创建新档案
        profile = AgentProfile(
            agent_id=new_id,
            creation_time=time.time(),
            parent_ids=parent_ids.copy(),
            win_rate=0.0,
            games_played=0,
            skill_ratings={},
            strategy_signature=np.zeros(32),
            performance_history=[]
        )
        
        # 添加到池中
        self.agents[new_id] = new_agent
        self.profiles[new_id] = profile
        
        # 如果池子满了，移除最弱的智能体
        if len(self.agents) > self.config.agent_pool_size:
            self._remove_weakest_agent()
        
        return new_id
    
    def _create_random_agent(self) -> str:
        """创建随机智能体"""
        new_id = f"random_{int(time.time())}_{random.randint(1000, 9999)}"
        agent = PPOAgent(self.ppo_config)
        
        # 随机初始化
        self._mutate_agent(agent, mutation_rate=0.2)
        
        profile = AgentProfile(
            agent_id=new_id,
            creation_time=time.time(),
            parent_ids=[],
            win_rate=0.0,
            games_played=0,
            skill_ratings={},
            strategy_signature=np.zeros(32),
            performance_history=[]
        )
        
        self.agents[new_id] = agent
        self.profiles[new_id] = profile
        
        return new_id
    
    def _mutate_agent(self, agent: PPOAgent, mutation_rate: float):
        """变异智能体参数"""
        with torch.no_grad():
            for param in agent.network.parameters():
                if random.random() < mutation_rate:
                    noise = torch.randn_like(param) * 0.01
                    param.add_(noise)
    
    def _crossover_agents(self, child_agent: PPOAgent, parent2_agent: PPOAgent):
        """智能体交叉"""
        with torch.no_grad():
            child_params = list(child_agent.network.parameters())
            parent2_params = list(parent2_agent.network.parameters())
            
            for i, (child_param, parent2_param) in enumerate(zip(child_params, parent2_params)):
                if random.random() < 0.5:  # 50%概率从第二个父代继承
                    child_param.data = parent2_param.data.clone()
    
    def _remove_weakest_agent(self):
        """移除最弱的智能体"""
        # 不移除初始智能体
        removable_agents = [aid for aid in self.agents.keys() 
                          if not aid.startswith("agent_")]
        
        if removable_agents:
            weakest_id = min(removable_agents, 
                           key=lambda aid: self.profiles[aid].win_rate)
            del self.agents[weakest_id]
            del self.profiles[weakest_id]
    
    def update_agent_profile(self, agent_id: str, game_result: str, 
                           game_states: List, actions: List):
        """更新智能体档案"""
        if agent_id not in self.profiles:
            return
        
        profile = self.profiles[agent_id]
        profile.games_played += 1
        
        # 更新胜率
        if game_result == "win":
            win_value = 1.0
        elif game_result == "draw":
            win_value = 0.5
        else:
            win_value = 0.0
        
        # 使用移动平均更新胜率
        alpha = 0.1  # 学习率
        profile.win_rate = (1 - alpha) * profile.win_rate + alpha * win_value
        
        # 更新策略签名
        if game_states and actions:
            new_signature = self.strategy_analyzer.analyze_strategy(
                self.agents[agent_id], game_states, actions
            )
            profile.strategy_signature = (0.9 * profile.strategy_signature + 
                                        0.1 * new_signature)
        
        # 更新表现历史
        profile.performance_history.append(win_value)
        if len(profile.performance_history) > 100:
            profile.performance_history = profile.performance_history[-100:]

class SelfPlayTrainer:
    """自对弈训练器"""
    
    def __init__(self, self_play_config: SelfPlayConfig, 
                 training_config: TrainingConfig,
                 ppo_config: PPOConfig,
                 reward_config: RewardConfig):
        
        self.self_play_config = self_play_config
        self.training_config = training_config
        self.ppo_config = ppo_config
        self.reward_config = reward_config
        
        # 初始化组件
        self.env = SanguoshaEnvironment(training_config)
        self.agent_pool = AgentPool(self_play_config, ppo_config)
        self.reward_calculator = RewardCalculator(reward_config)
        self.adaptive_reward = AdaptiveRewardSystem(reward_config)
        
        # 训练统计
        self.training_stats = {
            'episode_rewards': [],
            'win_rates': [],
            'agent_diversity': [],
            'training_time': [],
            'best_agents': []
        }
        
        # 创建保存目录
        self.save_dir = Path("models/self_play")
        self.save_dir.mkdir(parents=True, exist_ok=True)
    
    def train(self):
        """开始自对弈训练"""
        print("开始自对弈训练...")
        print(f"智能体池大小: {self.self_play_config.agent_pool_size}")
        print(f"总训练局数: {self.self_play_config.total_episodes}")
        
        start_time = time.time()
        
        for episode in range(self.self_play_config.total_episodes):
            episode_start_time = time.time()
            
            # 选择训练智能体
            agent_ids = list(self.agent_pool.agents.keys())
            current_agent_id = random.choice(agent_ids)
            
            # 选择对手
            opponent_id = self.agent_pool.select_opponent(
                current_agent_id, 
                self.self_play_config.opponent_selection_strategy
            )
            
            # 运行一局游戏
            episode_result = self._run_game_episode(current_agent_id, opponent_id)
            
            # 更新智能体
            self._update_agents(episode_result)
            
            # 记录统计信息
            episode_time = time.time() - episode_start_time
            self.training_stats['training_time'].append(episode_time)
            
            # 定期评估和保存
            if episode % self.self_play_config.evaluation_interval == 0:
                self._evaluate_agents(episode)
            
            if episode % self.self_play_config.save_interval == 0:
                self._save_checkpoint(episode)
            
            # 进化新智能体
            if episode % 2000 == 0 and episode > 0:
                self._evolve_population()
            
            # 打印进度
            if episode % 100 == 0:
                elapsed_time = time.time() - start_time
                avg_reward = np.mean(self.training_stats['episode_rewards'][-100:]) if self.training_stats['episode_rewards'] else 0
                print(f"Episode {episode}: Avg Reward={avg_reward:.2f}, Time={elapsed_time:.1f}s")
        
        print("训练完成!")
        self._save_final_results()
    
    def _run_game_episode(self, agent1_id: str, agent2_id: str) -> Dict:
        """运行一局游戏"""
        # 重置环境
        state, action_mask = self.env.reset(num_players=2)
        
        # 获取智能体
        agent1 = self.agent_pool.agents[agent1_id]
        agent2 = self.agent_pool.agents[agent2_id]
        
        # 游戏历史记录
        game_history = {
            'agent1_id': agent1_id,
            'agent2_id': agent2_id,
            'states': [],
            'actions': [],
            'rewards': [],
            'current_players': []
        }
        
        total_rewards = {agent1_id: 0.0, agent2_id: 0.0}
        step_count = 0
        
        while step_count < self.training_config.max_steps_per_episode:
            current_player_idx = self.env.game.current_player_index
            current_agent_id = agent1_id if current_player_idx == 0 else agent2_id
            current_agent = agent1 if current_player_idx == 0 else agent2
            
            # 选择动作
            action, log_prob, value = current_agent.select_action(
                self.env.game, 
                self.env.game.get_current_player(), 
                action_mask.astype(bool)
            )
            
            # 执行动作
            next_state, reward, done, info = self.env.step(action)
            
            # 记录历史
            game_history['states'].append(state)
            game_history['actions'].append(action)
            game_history['rewards'].append(reward)
            game_history['current_players'].append(current_player_idx)
            
            # 存储经验
            current_agent.store_experience(
                state.to_vector(), action, reward,
                next_state.to_vector(), done, log_prob, value, action_mask
            )
            
            total_rewards[current_agent_id] += reward
            
            if done:
                # 确定游戏结果
                winner_idx = 0 if info.get('winner', 0) == 0 else 1
                game_history['winner'] = agent1_id if winner_idx == 0 else agent2_id
                game_history['result'] = {
                    agent1_id: 'win' if winner_idx == 0 else 'lose',
                    agent2_id: 'win' if winner_idx == 1 else 'lose'
                }
                break
            
            state = next_state
            action_mask = self.env._get_action_mask(self.env.game.get_current_player())
            step_count += 1
        
        # 如果游戏没有正常结束，判定为平局
        if step_count >= self.training_config.max_steps_per_episode:
            game_history['winner'] = None
            game_history['result'] = {agent1_id: 'draw', agent2_id: 'draw'}
        
        game_history['total_rewards'] = total_rewards
        game_history['step_count'] = step_count
        
        return game_history
    
    def _update_agents(self, episode_result: Dict):
        """更新智能体"""
        agent1_id = episode_result['agent1_id']
        agent2_id = episode_result['agent2_id']
        
        # 更新智能体档案
        agent1_states = [s for i, s in enumerate(episode_result['states']) 
                        if episode_result['current_players'][i] == 0]
        agent1_actions = [a for i, a in enumerate(episode_result['actions']) 
                         if episode_result['current_players'][i] == 0]
        
        agent2_states = [s for i, s in enumerate(episode_result['states']) 
                        if episode_result['current_players'][i] == 1]
        agent2_actions = [a for i, a in enumerate(episode_result['actions']) 
                         if episode_result['current_players'][i] == 1]
        
        self.agent_pool.update_agent_profile(
            agent1_id, episode_result['result'][agent1_id], 
            agent1_states, agent1_actions
        )
        
        self.agent_pool.update_agent_profile(
            agent2_id, episode_result['result'][agent2_id], 
            agent2_states, agent2_actions
        )
        
        # PPO更新
        if len(self.agent_pool.agents[agent1_id].buffer.states) >= self.ppo_config.batch_size:
            self.agent_pool.agents[agent1_id].update()
        
        if len(self.agent_pool.agents[agent2_id].buffer.states) >= self.ppo_config.batch_size:
            self.agent_pool.agents[agent2_id].update()
        
        # 记录奖励
        avg_reward = (episode_result['total_rewards'][agent1_id] + 
                     episode_result['total_rewards'][agent2_id]) / 2
        self.training_stats['episode_rewards'].append(avg_reward)
    
    def _evaluate_agents(self, episode: int):
        """评估智能体性能"""
        print(f"\n=== 第{episode}局评估 ===")
        
        # 计算整体胜率
        recent_games = min(1000, len(self.training_stats['episode_rewards']))
        if recent_games > 0:
            avg_win_rate = np.mean([profile.win_rate for profile in self.agent_pool.profiles.values()])
            self.training_stats['win_rates'].append(avg_win_rate)
            print(f"平均胜率: {avg_win_rate:.3f}")
        
        # 计算策略多样性
        signatures = [profile.strategy_signature for profile in self.agent_pool.profiles.values()]
        if len(signatures) > 1:
            diversity = self._calculate_diversity(signatures)
            self.training_stats['agent_diversity'].append(diversity)
            print(f"策略多样性: {diversity:.3f}")
        
        # 找出最佳智能体
        best_agent_id = max(self.agent_pool.profiles.keys(), 
                          key=lambda aid: self.agent_pool.profiles[aid].win_rate)
        best_win_rate = self.agent_pool.profiles[best_agent_id].win_rate
        self.training_stats['best_agents'].append((episode, best_agent_id, best_win_rate))
        
        print(f"最佳智能体: {best_agent_id} (胜率: {best_win_rate:.3f})")
        
        # 显示智能体池状态
        print("智能体池状态:")
        for agent_id, profile in self.agent_pool.profiles.items():
            print(f"  {agent_id}: 胜率={profile.win_rate:.3f}, 游戏数={profile.games_played}")
    
    def _calculate_diversity(self, signatures: List[np.ndarray]) -> float:
        """计算策略多样性"""
        if len(signatures) < 2:
            return 0.0
        
        total_distance = 0.0
        count = 0
        
        for i in range(len(signatures)):
            for j in range(i + 1, len(signatures)):
                distance = np.linalg.norm(signatures[i] - signatures[j])
                total_distance += distance
                count += 1
        
        return total_distance / count if count > 0 else 0.0
    
    def _evolve_population(self):
        """进化智能体种群"""
        print("进化智能体种群...")
        
        # 选择表现最好的智能体作为父代
        sorted_agents = sorted(self.agent_pool.profiles.items(), 
                             key=lambda x: x[1].win_rate, reverse=True)
        
        top_agents = [aid for aid, _ in sorted_agents[:3]]
        
        # 创建新的进化智能体
        for _ in range(2):
            parent_ids = random.sample(top_agents, min(2, len(top_agents)))
            new_agent_id = self.agent_pool.evolve_agent(parent_ids)
            print(f"创建进化智能体: {new_agent_id} (父代: {parent_ids})")
    
    def _save_checkpoint(self, episode: int):
        """保存检查点"""
        checkpoint_dir = self.save_dir / f"checkpoint_{episode}"
        checkpoint_dir.mkdir(exist_ok=True)
        
        # 保存最佳智能体
        best_agent_id = max(self.agent_pool.profiles.keys(), 
                          key=lambda aid: self.agent_pool.profiles[aid].win_rate)
        
        best_agent = self.agent_pool.agents[best_agent_id]
        best_agent.save_model(str(checkpoint_dir / "best_agent.pth"))
        
        # 保存智能体池信息
        pool_info = {}
        for agent_id, profile in self.agent_pool.profiles.items():
            pool_info[agent_id] = {
                'win_rate': profile.win_rate,
                'games_played': profile.games_played,
                'creation_time': profile.creation_time,
                'parent_ids': profile.parent_ids,
                'strategy_signature': profile.strategy_signature.tolist()
            }
        
        with open(checkpoint_dir / "agent_pool.json", 'w') as f:
            json.dump(pool_info, f, indent=2)
        
        # 保存训练统计
        with open(checkpoint_dir / "training_stats.json", 'w') as f:
            json.dump({
                'episode_rewards': self.training_stats['episode_rewards'][-1000:],
                'win_rates': self.training_stats['win_rates'],
                'agent_diversity': self.training_stats['agent_diversity'],
                'best_agents': self.training_stats['best_agents'][-10:]
            }, f, indent=2)
        
        print(f"检查点已保存: {checkpoint_dir}")
    
    def _save_final_results(self):
        """保存最终结果"""
        final_dir = self.save_dir / "final"
        final_dir.mkdir(exist_ok=True)
        
        # 保存所有智能体
        for agent_id, agent in self.agent_pool.agents.items():
            agent.save_model(str(final_dir / f"{agent_id}.pth"))
        
        # 生成训练报告
        self._generate_training_report(final_dir)
        
        print(f"最终结果已保存: {final_dir}")
    
    def _generate_training_report(self, save_dir: Path):
        """生成训练报告"""
        # 绘制训练曲线
        plt.figure(figsize=(15, 10))
        
        # 奖励曲线
        plt.subplot(2, 3, 1)
        if self.training_stats['episode_rewards']:
            plt.plot(self.training_stats['episode_rewards'])
            plt.title('Episode Rewards')
            plt.xlabel('Episode')
            plt.ylabel('Reward')
        
        # 胜率曲线
        plt.subplot(2, 3, 2)
        if self.training_stats['win_rates']:
            plt.plot(self.training_stats['win_rates'])
            plt.title('Win Rates')
            plt.xlabel('Evaluation')
            plt.ylabel('Win Rate')
        
        # 策略多样性
        plt.subplot(2, 3, 3)
        if self.training_stats['agent_diversity']:
            plt.plot(self.training_stats['agent_diversity'])
            plt.title('Strategy Diversity')
            plt.xlabel('Evaluation')
            plt.ylabel('Diversity')
        
        # 智能体胜率分布
        plt.subplot(2, 3, 4)
        win_rates = [profile.win_rate for profile in self.agent_pool.profiles.values()]
        plt.hist(win_rates, bins=10)
        plt.title('Agent Win Rate Distribution')
        plt.xlabel('Win Rate')
        plt.ylabel('Count')
        
        # 训练时间
        plt.subplot(2, 3, 5)
        if self.training_stats['training_time']:
            plt.plot(self.training_stats['training_time'])
            plt.title('Episode Training Time')
            plt.xlabel('Episode')
            plt.ylabel('Time (s)')
        
        plt.tight_layout()
        plt.savefig(save_dir / 'training_report.png', dpi=300, bbox_inches='tight')
        plt.close()
        
        # 保存文本报告
        with open(save_dir / 'training_report.txt', 'w') as f:
            f.write("=== 三国杀AI自对弈训练报告 ===\n\n")
            f.write(f"训练配置:\n")
            f.write(f"  总训练局数: {self.self_play_config.total_episodes}\n")
            f.write(f"  智能体池大小: {self.self_play_config.agent_pool_size}\n")
            f.write(f"  评估间隔: {self.self_play_config.evaluation_interval}\n\n")
            
            f.write(f"最终结果:\n")
            if self.training_stats['episode_rewards']:
                f.write(f"  平均奖励: {np.mean(self.training_stats['episode_rewards'][-1000:]):.3f}\n")
            if self.training_stats['win_rates']:
                f.write(f"  最终胜率: {self.training_stats['win_rates'][-1]:.3f}\n")
            if self.training_stats['agent_diversity']:
                f.write(f"  策略多样性: {self.training_stats['agent_diversity'][-1]:.3f}\n")
            
            f.write(f"\n最佳智能体:\n")
            for episode, agent_id, win_rate in self.training_stats['best_agents'][-5:]:
                f.write(f"  Episode {episode}: {agent_id} (胜率: {win_rate:.3f})\n")

if __name__ == "__main__":
    # 配置参数
    self_play_config = SelfPlayConfig(total_episodes=1000)  # 测试用较小数值
    training_config = TrainingConfig()
    ppo_config = PPOConfig()
    reward_config = RewardConfig()
    
    # 创建训练器
    trainer = SelfPlayTrainer(self_play_config, training_config, ppo_config, reward_config)
    
    print("自对弈训练器初始化完成")
    print(f"智能体池大小: {len(trainer.agent_pool.agents)}")
    
    # 开始训练
    trainer.train()