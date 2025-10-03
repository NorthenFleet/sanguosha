#!/usr/bin/env python3
"""
通用评估脚本
加载模型并运行评估、比较或锦标赛测试
"""

import argparse
import os
import sys
from pathlib import Path
from typing import Dict, Any

sys.path.append(str(Path(__file__).parent.parent))

import torch
from ai.evaluation.evaluation_system import create_evaluator, EvaluationConfig, ModelEvaluator
from ai.trainers.ppo_trainer import PPOTrainer, PPOTrainingConfig
from ai.trainers.dqn_trainer import DQNTrainingConfig, DQNNetwork
from ai.trainers.a3c_trainer import A3CTrainingConfig, A3CNetwork
from ai.utils.training_utils import ConfigManager


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="三国杀AI 通用评估脚本")
    parser.add_argument("--algorithm", choices=["ppo", "dqn", "a3c"], required=True, help="模型算法类型")
    parser.add_argument("--model", type=str, required=True, help="模型文件路径(.pth)")
    parser.add_argument("--episodes", type=int, default=100, help="评估对局数量")
    parser.add_argument("--plots_dir", type=str, default="evaluation_plots", help="图表保存目录")
    parser.add_argument("--results_dir", type=str, default="evaluation_results", help="结果保存目录")
    parser.add_argument("--config", type=str, default="", help="可选评估配置文件(JSON/YAML)")
    return parser.parse_args()


def load_model(algorithm: str, model_path: str):
    checkpoint = torch.load(model_path, map_location="cpu")
    if algorithm == "ppo":
        # 仅加载网络进行评估（简单模式）
        # 这里使用PPO的ActorCritic网络由训练器内部，但为简洁仅从checkpoint取模型状态
        # 若需要完整agent可改为通过PPOAgent加载保存文件
        raise NotImplementedError("当前评估脚本不直接加载PPOAgent，请使用训练器内评估或扩展此函数。")
    elif algorithm == "dqn":
        # 需要构造网络以载入参数
        cfg = DQNTrainingConfig()
        net = DQNNetwork(cfg)
        state_dict = checkpoint.get('network_state_dict') or checkpoint.get('model_state_dict')
        net.load_state_dict(state_dict)
        net.eval()
        return net
    elif algorithm == "a3c":
        cfg = A3CTrainingConfig()
        net = A3CNetwork(cfg)
        state_dict = checkpoint.get('network_state_dict') or checkpoint.get('model_state_dict')
        net.load_state_dict(state_dict)
        net.eval()
        return net
    else:
        raise ValueError(f"不支持的算法: {algorithm}")


def main():
    args = parse_args()
    eval_cfg_dict: Dict[str, Any] = {}
    if args.config:
        try:
            eval_cfg_dict = ConfigManager.load_config(args.config)
        except Exception as e:
            print(f"警告: 加载评估配置失败 {args.config}: {e}")

    eval_config = EvaluationConfig(
        num_episodes=args.episodes,
        results_dir=args.results_dir,
        plots_dir=args.plots_dir,
    )
    # 覆盖可选配置
    for k, v in eval_cfg_dict.get("evaluation", {}).items():
        setattr(eval_config, k, v)

    evaluator: ModelEvaluator = ModelEvaluator(eval_config)

    # 加载模型
    if args.algorithm == "ppo":
        print("提示: 目前评估脚本未直接加载PPOAgent，请用PPOTrainer的评估或扩展此脚本。")
        return

    model = load_model(args.algorithm, args.model)
    report = evaluator.evaluate_model(model, model_name=Path(args.model).stem)
    print("评估完成。主要指标:")
    print({
        'win_rate': report['metrics'].get('win_rate'),
        'average_reward': report['metrics'].get('average_reward'),
        'episode_length_mean': report['metrics'].get('episode_length_stats', {}).get('mean'),
    })


if __name__ == "__main__":
    main()