#!/usr/bin/env python3
"""
通用强化学习训练脚本
支持选择算法(PPO/DQN/A3C)、加载配置、覆盖参数并启动训练
"""

import argparse
import os
import sys
from pathlib import Path
from typing import Dict, Any

sys.path.append(str(Path(__file__).parent.parent))

from ai.utils.training_utils import ConfigManager
from ai.trainers.ppo_trainer import PPOTrainer, PPOTrainingConfig
from ai.trainers.dqn_trainer import MultiAgentDQNTrainer, DQNTrainingConfig, create_dqn_trainer
from ai.trainers.a3c_trainer import A3CTrainer, A3CTrainingConfig, create_a3c_trainer


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="三国杀AI 通用训练脚本")
    parser.add_argument("--algorithm", choices=["ppo", "dqn", "a3c"], default="ppo", help="选择训练算法")
    parser.add_argument("--config", type=str, default="", help="配置文件路径(JSON/YAML)")
    parser.add_argument("--episodes", type=int, default=10000, help="训练回合数/步数(依据算法使用)")
    parser.add_argument("--log_dir", type=str, default="logs", help="日志目录")
    parser.add_argument("--model_dir", type=str, default="models", help="模型保存目录")
    parser.add_argument("--self_play", action="store_true", help="启用自对弈(仅PPO/DQN部分支持)")
    parser.add_argument("--num_workers", type=int, default=4, help="A3C worker数量")
    parser.add_argument("--eval_interval", type=int, default=1000, help="评估间隔")
    parser.add_argument("--save_interval", type=int, default=5000, help="保存间隔")
    parser.add_argument("--seed", type=int, default=42, help="随机种子")
    return parser.parse_args()


def build_ppo_trainer(args: argparse.Namespace, user_cfg: Dict[str, Any]) -> PPOTrainer:
    cfg = PPOTrainingConfig(
        max_episodes=args.episodes,
        evaluation_interval=args.eval_interval,
        save_interval=args.save_interval,
        log_dir=os.path.join(args.log_dir, "ppo"),
        model_dir=os.path.join(args.model_dir, "ppo"),
        self_play=args.self_play,
    )
    # 覆盖用户配置（如提供）
    for k, v in (user_cfg or {}).get("ppo_training", {}).items():
        setattr(cfg, k, v)
    return PPOTrainer(cfg)


def build_dqn_trainer(args: argparse.Namespace, user_cfg: Dict[str, Any]) -> MultiAgentDQNTrainer:
    cfg = DQNTrainingConfig(
        max_episodes=args.episodes,
        evaluation_interval=args.eval_interval,
        save_interval=args.save_interval,
        log_dir=os.path.join(args.log_dir, "dqn"),
        model_dir=os.path.join(args.model_dir, "dqn"),
        self_play=args.self_play,
    )
    # 覆盖用户配置（如提供）
    for k, v in (user_cfg or {}).get("dqn_training", {}).items():
        setattr(cfg, k, v)
    return create_dqn_trainer(vars(cfg))


def build_a3c_trainer(args: argparse.Namespace, user_cfg: Dict[str, Any]) -> A3CTrainer:
    cfg = A3CTrainingConfig(
        max_global_steps=max(args.episodes, 100000),
        evaluation_interval=args.eval_interval,
        save_interval=args.save_interval,
        log_dir=os.path.join(args.log_dir, "a3c"),
        model_dir=os.path.join(args.model_dir, "a3c"),
        num_workers=args.num_workers,
    )
    # 覆盖用户配置（如提供）
    for k, v in (user_cfg or {}).get("a3c_training", {}).items():
        setattr(cfg, k, v)
    return create_a3c_trainer(vars(cfg))


def main():
    args = parse_args()
    user_cfg = {}
    if args.config:
        try:
            user_cfg = ConfigManager.load_config(args.config)
        except Exception as e:
            print(f"警告: 加载配置失败 {args.config}: {e}")

    os.makedirs(args.log_dir, exist_ok=True)
    os.makedirs(args.model_dir, exist_ok=True)

    if args.algorithm == "ppo":
        trainer = build_ppo_trainer(args, user_cfg)
        best = trainer.train()
        print(f"PPO训练完成，最佳模型: {best}")
    elif args.algorithm == "dqn":
        trainer = build_dqn_trainer(args, user_cfg)
        best = trainer.train()
        print(f"DQN训练完成，最佳模型: {best}")
    elif args.algorithm == "a3c":
        # A3C训练使用全局步数，episodes参数将作为近似目标步数
        trainer = build_a3c_trainer(args, user_cfg)
        best = trainer.train()
        print(f"A3C训练完成，最佳模型: {best}")


if __name__ == "__main__":
    main()