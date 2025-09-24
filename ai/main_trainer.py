#!/usr/bin/env python3
"""
三国杀AI主训练脚本
整合所有AI组件，提供完整的训练和评估流程
"""

import argparse
import json
import logging
import os
import sys
from pathlib import Path
from typing import Dict, List, Optional
import torch
import numpy as np
from datetime import datetime

# 添加项目根目录到路径
sys.path.append(str(Path(__file__).parent.parent))

from ai.game_state_encoder import GameStateEncoder
from ai.neural_networks import create_networks
from ai.ppo_agent import PPOAgent, PPOConfig
from ai.training_environment import SanguoshaEnvironment, TrainingConfig
from ai.reward_system import RewardCalculator, RewardConfig
from ai.self_play_trainer import SelfPlayTrainer, SelfPlayConfig
from ai.distributed_ppo import DistributedPPOTrainer, DistributedConfig

class TrainingManager:
    """训练管理器"""
    
    def __init__(self, config_path: Optional[str] = None):
        # 加载配置
        self.config = self._load_config(config_path)
        
        # 设置日志
        self._setup_logging()
        
        # 创建保存目录
        self.save_dir = Path(self.config['save_dir'])
        self.save_dir.mkdir(parents=True, exist_ok=True)
        
        # 初始化组件
        self.state_encoder = None
        self.agent = None
        self.environment = None
        self.reward_calculator = None
        self.trainer = None
        
        self.logger = logging.getLogger(__name__)
        
    def _load_config(self, config_path: Optional[str]) -> Dict:
        """加载配置文件"""
        default_config = {
            # 基础配置
            "experiment_name": f"sanguosha_ai_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "save_dir": "models/experiments",
            "device": "cuda" if torch.cuda.is_available() else "cpu",
            "seed": 42,
            
            # PPO配置
            "ppo": {
                "learning_rate": 3e-4,
                "gamma": 0.99,
                "gae_lambda": 0.95,
                "clip_epsilon": 0.2,
                "value_coef": 0.5,
                "entropy_coef": 0.01,
                "max_grad_norm": 0.5,
                "batch_size": 256,
                "mini_batch_size": 64,
                "epochs": 4,
                "state_dim": 512,
                "action_dim": 1000,
                "hidden_dim": 256
            },
            
            # 训练配置
            "training": {
                "max_episodes": 50000,
                "max_steps_per_episode": 200,
                "eval_interval": 1000,
                "save_interval": 5000,
                "log_interval": 100,
                "num_players": 3,
                "enable_self_play": True
            },
            
            # 奖励配置
            "reward": {
                "survival_weight": 1.0,
                "damage_weight": 0.8,
                "card_advantage_weight": 0.3,
                "equipment_weight": 0.2,
                "strategy_weight": 0.5,
                "efficiency_weight": 0.3,
                "win_reward": 10.0,
                "lose_penalty": -5.0
            },
            
            # 自对弈配置
            "self_play": {
                "pool_size": 10,
                "update_interval": 2000,
                "evaluation_games": 100,
                "win_rate_threshold": 0.6,
                "diversity_weight": 0.3
            },
            
            # 分布式配置
            "distributed": {
                "enabled": False,
                "world_size": 4,
                "num_workers": 3,
                "num_learners": 1,
                "backend": "nccl",
                "master_addr": "localhost",
                "master_port": "12355"
            },
            
            # 网络架构
            "network": {
                "type": "actor_critic",  # actor_critic, dueling
                "use_attention": True,
                "attention_heads": 8,
                "dropout": 0.1
            }
        }
        
        if config_path and os.path.exists(config_path):
            with open(config_path, 'r', encoding='utf-8') as f:
                user_config = json.load(f)
            
            # 递归更新配置
            def update_dict(d, u):
                for k, v in u.items():
                    if isinstance(v, dict):
                        d[k] = update_dict(d.get(k, {}), v)
                    else:
                        d[k] = v
                return d
            
            default_config = update_dict(default_config, user_config)
        
        return default_config
    
    def _setup_logging(self):
        """设置日志"""
        log_dir = Path(self.config['save_dir']) / "logs"
        log_dir.mkdir(parents=True, exist_ok=True)
        
        log_file = log_dir / f"{self.config['experiment_name']}.log"
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler(sys.stdout)
            ]
        )
    
    def initialize_components(self):
        """初始化所有组件"""
        self.logger.info("初始化AI组件...")
        
        # 设置随机种子
        torch.manual_seed(self.config['seed'])
        np.random.seed(self.config['seed'])
        
        # 创建PPO配置
        ppo_config = PPOConfig(
            learning_rate=self.config['ppo']['learning_rate'],
            gamma=self.config['ppo']['gamma'],
            gae_lambda=self.config['ppo']['gae_lambda'],
            clip_epsilon=self.config['ppo']['clip_epsilon'],
            value_coef=self.config['ppo']['value_coef'],
            entropy_coef=self.config['ppo']['entropy_coef'],
            max_grad_norm=self.config['ppo']['max_grad_norm'],
            batch_size=self.config['ppo']['batch_size'],
            mini_batch_size=self.config['ppo']['mini_batch_size'],
            epochs=self.config['ppo']['epochs'],
            state_dim=self.config['ppo']['state_dim'],
            action_dim=self.config['ppo']['action_dim'],
            hidden_dim=self.config['ppo']['hidden_dim']
        )
        
        # 创建训练配置
        training_config = TrainingConfig(
            max_episodes=self.config['training']['max_episodes'],
            max_steps_per_episode=self.config['training']['max_steps_per_episode'],
            num_players=self.config['training']['num_players']
        )
        
        # 创建奖励配置
        reward_config = RewardConfig(
            survival_weight=self.config['reward']['survival_weight'],
            damage_weight=self.config['reward']['damage_weight'],
            card_advantage_weight=self.config['reward']['card_advantage_weight'],
            equipment_weight=self.config['reward']['equipment_weight'],
            strategy_weight=self.config['reward']['strategy_weight'],
            efficiency_weight=self.config['reward']['efficiency_weight'],
            win_reward=self.config['reward']['win_reward'],
            lose_penalty=self.config['reward']['lose_penalty']
        )
        
        # 初始化组件
        self.state_encoder = GameStateEncoder()
        self.agent = PPOAgent(ppo_config)
        self.environment = SanguoshaEnvironment(training_config)
        self.reward_calculator = RewardCalculator(reward_config)
        
        # 创建神经网络
        networks = create_networks(
            state_dim=ppo_config.state_dim,
            action_dim=ppo_config.action_dim,
            hidden_dim=ppo_config.hidden_dim,
            network_type=self.config['network']['type'],
            use_attention=self.config['network']['use_attention'],
            attention_heads=self.config['network']['attention_heads'],
            dropout=self.config['network']['dropout']
        )
        
        self.agent.network = networks
        
        self.logger.info("AI组件初始化完成")
    
    def train_single_agent(self):
        """单智能体训练"""
        self.logger.info("开始单智能体训练...")
        
        episode = 0
        best_win_rate = 0.0
        
        while episode < self.config['training']['max_episodes']:
            # 运行一个episode
            episode_reward, episode_length = self._run_episode()
            
            episode += 1
            
            # 记录日志
            if episode % self.config['training']['log_interval'] == 0:
                self.logger.info(
                    f"Episode {episode}: Reward={episode_reward:.2f}, "
                    f"Length={episode_length}, Best Win Rate={best_win_rate:.3f}"
                )
            
            # 评估
            if episode % self.config['training']['eval_interval'] == 0:
                win_rate = self._evaluate_agent()
                
                if win_rate > best_win_rate:
                    best_win_rate = win_rate
                    self._save_best_model()
                
                self.logger.info(f"评估结果: Win Rate={win_rate:.3f}")
            
            # 保存检查点
            if episode % self.config['training']['save_interval'] == 0:
                self._save_checkpoint(episode)
        
        self.logger.info("单智能体训练完成")
    
    def train_self_play(self):
        """自对弈训练"""
        self.logger.info("开始自对弈训练...")
        
        # 创建自对弈配置
        self_play_config = SelfPlayConfig(
            pool_size=self.config['self_play']['pool_size'],
            update_interval=self.config['self_play']['update_interval'],
            evaluation_games=self.config['self_play']['evaluation_games'],
            win_rate_threshold=self.config['self_play']['win_rate_threshold'],
            diversity_weight=self.config['self_play']['diversity_weight']
        )
        
        # 创建自对弈训练器
        self.trainer = SelfPlayTrainer(
            self.agent,
            self.environment,
            self.reward_calculator,
            self_play_config
        )
        
        # 开始训练
        self.trainer.train(self.config['training']['max_episodes'])
        
        self.logger.info("自对弈训练完成")
    
    def train_distributed(self):
        """分布式训练"""
        self.logger.info("开始分布式训练...")
        
        # 创建分布式配置
        distributed_config = DistributedConfig(
            world_size=self.config['distributed']['world_size'],
            num_workers=self.config['distributed']['num_workers'],
            num_learners=self.config['distributed']['num_learners'],
            backend=self.config['distributed']['backend'],
            master_addr=self.config['distributed']['master_addr'],
            master_port=self.config['distributed']['master_port']
        )
        
        # 创建训练配置
        training_config = TrainingConfig(
            max_episodes=self.config['training']['max_episodes'],
            max_steps_per_episode=self.config['training']['max_steps_per_episode'],
            num_players=self.config['training']['num_players']
        )
        
        # 创建分布式训练器
        ppo_config = PPOConfig(
            learning_rate=self.config['ppo']['learning_rate'],
            gamma=self.config['ppo']['gamma'],
            gae_lambda=self.config['ppo']['gae_lambda'],
            clip_epsilon=self.config['ppo']['clip_epsilon'],
            value_coef=self.config['ppo']['value_coef'],
            entropy_coef=self.config['ppo']['entropy_coef'],
            max_grad_norm=self.config['ppo']['max_grad_norm'],
            batch_size=self.config['ppo']['batch_size'],
            mini_batch_size=self.config['ppo']['mini_batch_size'],
            epochs=self.config['ppo']['epochs'],
            state_dim=self.config['ppo']['state_dim'],
            action_dim=self.config['ppo']['action_dim'],
            hidden_dim=self.config['ppo']['hidden_dim']
        )
        
        distributed_trainer = DistributedPPOTrainer(
            ppo_config, training_config, distributed_config
        )
        
        # 开始训练
        distributed_trainer.start_training(self.config['training']['max_episodes'])
        
        # 获取最佳智能体
        self.agent = distributed_trainer.get_best_agent()
        
        self.logger.info("分布式训练完成")
    
    def _run_episode(self) -> tuple:
        """运行单个episode"""
        state, action_mask = self.environment.reset()
        episode_reward = 0.0
        step = 0
        
        while step < self.config['training']['max_steps_per_episode']:
            # 选择动作
            action, log_prob, value = self.agent.select_action(
                self.environment.game,
                self.environment.game.get_current_player(),
                action_mask.astype(bool)
            )
            
            # 执行动作
            next_state, reward, done, info = self.environment.step(action)
            
            # 存储经验
            self.agent.store_experience(
                state.to_vector(), action, reward, 
                next_state.to_vector(), done, log_prob, value, action_mask
            )
            
            episode_reward += reward
            
            if done:
                break
            
            state = next_state
            action_mask = self.environment._get_action_mask(
                self.environment.game.get_current_player()
            )
            step += 1
        
        # 更新智能体
        if len(self.agent.buffer.experiences) >= self.agent.config.batch_size:
            self.agent.update()
        
        return episode_reward, step
    
    def _evaluate_agent(self, num_games: int = 100) -> float:
        """评估智能体"""
        wins = 0
        
        for _ in range(num_games):
            state, action_mask = self.environment.reset()
            done = False
            
            while not done:
                action, _, _ = self.agent.select_action(
                    self.environment.game,
                    self.environment.game.get_current_player(),
                    action_mask.astype(bool),
                    deterministic=True  # 评估时使用确定性策略
                )
                
                state, reward, done, info = self.environment.step(action)
                action_mask = self.environment._get_action_mask(
                    self.environment.game.get_current_player()
                )
            
            # 检查是否获胜
            if info.get('winner') == 0:  # 假设智能体是玩家0
                wins += 1
        
        return wins / num_games
    
    def _save_best_model(self):
        """保存最佳模型"""
        best_model_path = self.save_dir / "best_model.pth"
        self.agent.save_model(str(best_model_path))
        self.logger.info(f"最佳模型已保存: {best_model_path}")
    
    def _save_checkpoint(self, episode: int):
        """保存检查点"""
        checkpoint_path = self.save_dir / f"checkpoint_{episode}.pth"
        self.agent.save_model(str(checkpoint_path))
        
        # 保存配置
        config_path = self.save_dir / f"config_{episode}.json"
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(self.config, f, indent=2, ensure_ascii=False)
        
        self.logger.info(f"检查点已保存: {checkpoint_path}")
    
    def load_model(self, model_path: str):
        """加载模型"""
        if self.agent is None:
            self.initialize_components()
        
        self.agent.load_model(model_path)
        self.logger.info(f"模型已加载: {model_path}")
    
    def play_against_human(self):
        """与人类对战"""
        self.logger.info("开始与人类对战...")
        
        state, action_mask = self.environment.reset()
        
        while True:
            current_player = self.environment.game.get_current_player()
            
            if current_player.player_id == 0:  # AI回合
                action, _, _ = self.agent.select_action(
                    self.environment.game, current_player, 
                    action_mask.astype(bool), deterministic=True
                )
                
                print(f"AI选择动作: {action}")
                
            else:  # 人类回合
                print(f"轮到玩家 {current_player.player_id}")
                print(f"可用动作: {np.where(action_mask)[0].tolist()}")
                
                while True:
                    try:
                        action = int(input("请选择动作编号: "))
                        if action_mask[action]:
                            break
                        else:
                            print("无效动作，请重新选择")
                    except (ValueError, IndexError):
                        print("请输入有效的动作编号")
            
            # 执行动作
            state, reward, done, info = self.environment.step(action)
            
            if done:
                winner = info.get('winner', -1)
                if winner == 0:
                    print("AI获胜！")
                elif winner > 0:
                    print(f"玩家 {winner} 获胜！")
                else:
                    print("游戏平局")
                break
            
            action_mask = self.environment._get_action_mask(
                self.environment.game.get_current_player()
            )

def main():
    parser = argparse.ArgumentParser(description="三国杀AI训练")
    parser.add_argument('--config', type=str, help='配置文件路径')
    parser.add_argument('--mode', type=str, choices=['single', 'self_play', 'distributed', 'play'], 
                       default='single', help='训练模式')
    parser.add_argument('--model', type=str, help='预训练模型路径')
    parser.add_argument('--eval', action='store_true', help='仅评估模式')
    
    args = parser.parse_args()
    
    # 创建训练管理器
    manager = TrainingManager(args.config)
    
    # 初始化组件
    manager.initialize_components()
    
    # 加载预训练模型
    if args.model:
        manager.load_model(args.model)
    
    # 根据模式执行
    if args.eval:
        win_rate = manager._evaluate_agent(1000)
        print(f"评估结果: Win Rate = {win_rate:.3f}")
    
    elif args.mode == 'single':
        manager.train_single_agent()
    
    elif args.mode == 'self_play':
        manager.train_self_play()
    
    elif args.mode == 'distributed':
        manager.train_distributed()
    
    elif args.mode == 'play':
        manager.play_against_human()

if __name__ == "__main__":
    main()