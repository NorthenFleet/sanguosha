#!/usr/bin/env python3
"""
训练评估系统
提供全面的模型评估、对战测试和性能分析功能
"""

import torch
import numpy as np
import time
import json
import os
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass, field
from collections import defaultdict, deque
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
import pandas as pd
from concurrent.futures import ThreadPoolExecutor, as_completed
import logging

from ..training_environment import SanguoshaEnvironment, TrainingConfig
from ..game_state_encoder import GameStateEncoder
from ..utils.training_utils import Logger, ModelManager

@dataclass
class EvaluationConfig:
    """评估配置"""
    # 基础评估参数
    num_episodes: int = 100
    max_steps_per_episode: int = 1000
    num_parallel_games: int = 4
    
    # 对战评估参数
    tournament_rounds: int = 10
    self_play_episodes: int = 50
    
    # 性能分析参数
    analyze_game_states: bool = True
    analyze_action_distribution: bool = True
    analyze_value_accuracy: bool = True
    
    # 统计参数
    confidence_level: float = 0.95
    bootstrap_samples: int = 1000
    
    # 保存路径
    results_dir: str = "evaluation_results"
    plots_dir: str = "evaluation_plots"

class GameResult:
    """游戏结果记录"""
    
    def __init__(self):
        self.winner: Optional[int] = None
        self.episode_length: int = 0
        self.total_reward: float = 0.0
        self.player_rewards: List[float] = []
        self.game_states: List[Any] = []
        self.actions_taken: List[int] = []
        self.action_probs: List[List[float]] = []
        self.value_estimates: List[float] = []
        self.actual_returns: List[float] = []
        self.game_duration: float = 0.0
        self.error_occurred: bool = False
        self.error_message: str = ""

class PerformanceMetrics:
    """性能指标计算器"""
    
    @staticmethod
    def calculate_win_rate(results: List[GameResult], player_id: int = 0) -> float:
        """计算胜率"""
        wins = sum(1 for result in results if result.winner == player_id)
        return wins / len(results) if results else 0.0
    
    @staticmethod
    def calculate_average_reward(results: List[GameResult], player_id: int = 0) -> float:
        """计算平均奖励"""
        if not results:
            return 0.0
        
        total_reward = 0.0
        valid_games = 0
        
        for result in results:
            if len(result.player_rewards) > player_id:
                total_reward += result.player_rewards[player_id]
                valid_games += 1
        
        return total_reward / valid_games if valid_games > 0 else 0.0
    
    @staticmethod
    def calculate_episode_length_stats(results: List[GameResult]) -> Dict[str, float]:
        """计算回合长度统计"""
        lengths = [result.episode_length for result in results if not result.error_occurred]
        
        if not lengths:
            return {'mean': 0, 'std': 0, 'min': 0, 'max': 0, 'median': 0}
        
        return {
            'mean': np.mean(lengths),
            'std': np.std(lengths),
            'min': np.min(lengths),
            'max': np.max(lengths),
            'median': np.median(lengths)
        }
    
    @staticmethod
    def calculate_value_accuracy(results: List[GameResult]) -> Dict[str, float]:
        """计算价值函数准确性"""
        all_predictions = []
        all_targets = []
        
        for result in results:
            if result.value_estimates and result.actual_returns:
                all_predictions.extend(result.value_estimates)
                all_targets.extend(result.actual_returns)
        
        if not all_predictions:
            return {'mse': float('inf'), 'mae': float('inf'), 'correlation': 0.0}
        
        predictions = np.array(all_predictions)
        targets = np.array(all_targets)
        
        mse = np.mean((predictions - targets) ** 2)
        mae = np.mean(np.abs(predictions - targets))
        correlation = np.corrcoef(predictions, targets)[0, 1] if len(predictions) > 1 else 0.0
        
        return {
            'mse': mse,
            'mae': mae,
            'correlation': correlation if not np.isnan(correlation) else 0.0
        }
    
    @staticmethod
    def calculate_action_diversity(results: List[GameResult]) -> Dict[str, float]:
        """计算动作多样性"""
        all_actions = []
        for result in results:
            all_actions.extend(result.actions_taken)
        
        if not all_actions:
            return {'entropy': 0.0, 'unique_actions': 0, 'action_distribution': {}}
        
        # 计算动作分布
        action_counts = defaultdict(int)
        for action in all_actions:
            action_counts[action] += 1
        
        total_actions = len(all_actions)
        action_probs = [count / total_actions for count in action_counts.values()]
        
        # 计算熵
        entropy = -sum(p * np.log(p) for p in action_probs if p > 0)
        
        return {
            'entropy': entropy,
            'unique_actions': len(action_counts),
            'action_distribution': dict(action_counts)
        }

class ModelEvaluator:
    """模型评估器"""
    
    def __init__(self, config: EvaluationConfig):
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # 创建结果目录
        os.makedirs(config.results_dir, exist_ok=True)
        os.makedirs(config.plots_dir, exist_ok=True)
        
        # 性能指标计算器
        self.metrics_calculator = PerformanceMetrics()
    
    def evaluate_model(self, model: torch.nn.Module, model_name: str = "model") -> Dict[str, Any]:
        """评估单个模型"""
        self.logger.info(f"开始评估模型: {model_name}")
        
        # 运行评估游戏
        results = self._run_evaluation_games(model)
        
        # 计算性能指标
        metrics = self._calculate_all_metrics(results)
        
        # 生成评估报告
        report = self._generate_evaluation_report(model_name, results, metrics)
        
        # 保存结果
        self._save_evaluation_results(model_name, report)
        
        # 生成可视化图表
        if self.config.analyze_game_states:
            self._generate_evaluation_plots(model_name, results, metrics)
        
        self.logger.info(f"模型 {model_name} 评估完成")
        return report
    
    def compare_models(self, models: Dict[str, torch.nn.Module]) -> Dict[str, Any]:
        """比较多个模型"""
        self.logger.info(f"开始比较 {len(models)} 个模型")
        
        all_results = {}
        all_metrics = {}
        
        # 评估每个模型
        for model_name, model in models.items():
            results = self._run_evaluation_games(model)
            metrics = self._calculate_all_metrics(results)
            
            all_results[model_name] = results
            all_metrics[model_name] = metrics
        
        # 生成比较报告
        comparison_report = self._generate_comparison_report(all_metrics)
        
        # 保存比较结果
        self._save_comparison_results(comparison_report)
        
        # 生成比较图表
        self._generate_comparison_plots(all_metrics)
        
        self.logger.info("模型比较完成")
        return comparison_report
    
    def tournament_evaluation(self, models: Dict[str, torch.nn.Module]) -> Dict[str, Any]:
        """锦标赛评估"""
        self.logger.info(f"开始锦标赛评估，{len(models)} 个模型参与")
        
        tournament_results = {}
        
        # 两两对战
        model_names = list(models.keys())
        for i, model1_name in enumerate(model_names):
            for j, model2_name in enumerate(model_names):
                if i != j:
                    match_key = f"{model1_name}_vs_{model2_name}"
                    self.logger.info(f"对战: {match_key}")
                    
                    results = self._run_head_to_head(
                        models[model1_name], models[model2_name],
                        model1_name, model2_name
                    )
                    
                    tournament_results[match_key] = results
        
        # 计算锦标赛统计
        tournament_stats = self._calculate_tournament_stats(tournament_results, model_names)
        
        # 保存锦标赛结果
        self._save_tournament_results(tournament_results, tournament_stats)
        
        # 生成锦标赛图表
        self._generate_tournament_plots(tournament_stats)
        
        return tournament_stats
    
    def _run_evaluation_games(self, model: torch.nn.Module) -> List[GameResult]:
        """运行评估游戏"""
        results = []
        
        # 设置模型为评估模式
        model.eval()
        
        # 创建环境和编码器
        env_config = TrainingConfig()
        state_encoder = GameStateEncoder()
        
        with ThreadPoolExecutor(max_workers=self.config.num_parallel_games) as executor:
            # 提交游戏任务
            futures = []
            for episode in range(self.config.num_episodes):
                future = executor.submit(
                    self._run_single_game, model, env_config, state_encoder, episode
                )
                futures.append(future)
            
            # 收集结果
            for future in as_completed(futures):
                try:
                    result = future.result()
                    results.append(result)
                except Exception as e:
                    self.logger.error(f"游戏执行出错: {e}")
                    error_result = GameResult()
                    error_result.error_occurred = True
                    error_result.error_message = str(e)
                    results.append(error_result)
        
        return results
    
    def _run_single_game(self, model: torch.nn.Module, env_config: TrainingConfig,
                        state_encoder: GameStateEncoder, episode_id: int) -> GameResult:
        """运行单个游戏"""
        result = GameResult()
        start_time = time.time()
        
        try:
            # 创建环境
            env = SanguoshaEnvironment(env_config)
            state = env.reset()
            
            episode_length = 0
            total_reward = 0.0
            player_rewards = [0.0] * env.num_players
            
            # 游戏循环
            while episode_length < self.config.max_steps_per_episode:
                current_player = env.current_player
                
                # 编码游戏状态
                state_vector = state_encoder.encode_game_state(state, current_player)
                action_mask = env.get_action_mask()
                
                # 转换为张量
                state_tensor = torch.FloatTensor(state_vector.to_vector()).unsqueeze(0)
                mask_tensor = torch.FloatTensor(action_mask).unsqueeze(0) if action_mask is not None else None
                
                # 模型预测
                with torch.no_grad():
                    if hasattr(model, 'get_action_and_value'):
                        action, log_prob, value, entropy, _ = model.get_action_and_value(
                            state_tensor, mask_tensor
                        )
                        action = action.item()
                        value = value.item()
                        
                        # 获取动作概率分布
                        policy, _, _ = model(state_tensor, mask_tensor)
                        action_probs = policy.squeeze().tolist()
                    else:
                        # 简单的前向传播
                        output = model(state_tensor)
                        if isinstance(output, tuple):
                            policy, value = output
                            value = value.item()
                        else:
                            policy = output
                            value = 0.0
                        
                        # 应用动作掩码
                        if mask_tensor is not None:
                            policy = policy * mask_tensor
                            policy = policy / (policy.sum(dim=-1, keepdim=True) + 1e-8)
                        
                        action = torch.argmax(policy, dim=-1).item()
                        action_probs = policy.squeeze().tolist()
                
                # 执行动作
                next_state, reward, done, info = env.step(action)
                
                # 记录数据
                if self.config.analyze_game_states:
                    result.game_states.append(state_vector.to_vector())
                    result.actions_taken.append(action)
                    result.action_probs.append(action_probs)
                    result.value_estimates.append(value)
                
                total_reward += reward
                player_rewards[current_player] += reward
                episode_length += 1
                
                if done:
                    result.winner = info.get('winner')
                    break
                
                state = next_state
            
            # 计算实际回报（如果需要）
            if self.config.analyze_value_accuracy and result.value_estimates:
                result.actual_returns = self._calculate_actual_returns(
                    [reward] * len(result.value_estimates), gamma=0.99
                )
            
            # 设置结果
            result.episode_length = episode_length
            result.total_reward = total_reward
            result.player_rewards = player_rewards
            result.game_duration = time.time() - start_time
            
        except Exception as e:
            result.error_occurred = True
            result.error_message = str(e)
            result.game_duration = time.time() - start_time
        
        return result
    
    def _calculate_actual_returns(self, rewards: List[float], gamma: float = 0.99) -> List[float]:
        """计算实际回报"""
        returns = []
        discounted_return = 0.0
        
        for reward in reversed(rewards):
            discounted_return = reward + gamma * discounted_return
            returns.insert(0, discounted_return)
        
        return returns
    
    def _calculate_all_metrics(self, results: List[GameResult]) -> Dict[str, Any]:
        """计算所有性能指标"""
        valid_results = [r for r in results if not r.error_occurred]
        
        if not valid_results:
            return {'error': 'No valid results'}
        
        metrics = {}
        
        # 基础性能指标
        metrics['win_rate'] = self.metrics_calculator.calculate_win_rate(valid_results)
        metrics['average_reward'] = self.metrics_calculator.calculate_average_reward(valid_results)
        metrics['episode_length_stats'] = self.metrics_calculator.calculate_episode_length_stats(valid_results)
        
        # 价值函数准确性
        if self.config.analyze_value_accuracy:
            metrics['value_accuracy'] = self.metrics_calculator.calculate_value_accuracy(valid_results)
        
        # 动作多样性
        if self.config.analyze_action_distribution:
            metrics['action_diversity'] = self.metrics_calculator.calculate_action_diversity(valid_results)
        
        # 游戏时长统计
        game_durations = [r.game_duration for r in valid_results]
        metrics['game_duration_stats'] = {
            'mean': np.mean(game_durations),
            'std': np.std(game_durations),
            'min': np.min(game_durations),
            'max': np.max(game_durations)
        }
        
        # 错误率
        metrics['error_rate'] = len([r for r in results if r.error_occurred]) / len(results)
        
        # 置信区间（使用bootstrap）
        if len(valid_results) > 10:
            metrics['confidence_intervals'] = self._calculate_confidence_intervals(valid_results)
        
        return metrics
    
    def _calculate_confidence_intervals(self, results: List[GameResult]) -> Dict[str, Tuple[float, float]]:
        """计算置信区间"""
        def bootstrap_metric(metric_func, n_samples=1000):
            bootstrap_values = []
            for _ in range(n_samples):
                sample = np.random.choice(results, size=len(results), replace=True)
                bootstrap_values.append(metric_func(sample))
            
            alpha = 1 - self.config.confidence_level
            lower = np.percentile(bootstrap_values, 100 * alpha / 2)
            upper = np.percentile(bootstrap_values, 100 * (1 - alpha / 2))
            return (lower, upper)
        
        return {
            'win_rate': bootstrap_metric(self.metrics_calculator.calculate_win_rate),
            'average_reward': bootstrap_metric(self.metrics_calculator.calculate_average_reward)
        }
    
    def _run_head_to_head(self, model1: torch.nn.Module, model2: torch.nn.Module,
                         model1_name: str, model2_name: str) -> Dict[str, Any]:
        """运行两个模型的对战"""
        results = []
        
        for round_num in range(self.config.tournament_rounds):
            # 每轮交换先后手
            if round_num % 2 == 0:
                result = self._run_head_to_head_game(model1, model2, 0, 1)
                result['model1_player'] = 0
                result['model2_player'] = 1
            else:
                result = self._run_head_to_head_game(model2, model1, 0, 1)
                result['model1_player'] = 1
                result['model2_player'] = 0
            
            result['round'] = round_num
            results.append(result)
        
        # 计算对战统计
        model1_wins = sum(1 for r in results if r['winner'] == r['model1_player'])
        model2_wins = sum(1 for r in results if r['winner'] == r['model2_player'])
        draws = len(results) - model1_wins - model2_wins
        
        return {
            'model1_name': model1_name,
            'model2_name': model2_name,
            'model1_wins': model1_wins,
            'model2_wins': model2_wins,
            'draws': draws,
            'total_games': len(results),
            'model1_win_rate': model1_wins / len(results),
            'detailed_results': results
        }
    
    def _run_head_to_head_game(self, model1: torch.nn.Module, model2: torch.nn.Module,
                              player1_id: int, player2_id: int) -> Dict[str, Any]:
        """运行单场对战游戏"""
        models = {player1_id: model1, player2_id: model2}
        
        env_config = TrainingConfig()
        env = SanguoshaEnvironment(env_config)
        state_encoder = GameStateEncoder()
        
        state = env.reset()
        episode_length = 0
        
        while episode_length < self.config.max_steps_per_episode:
            current_player = env.current_player
            current_model = models.get(current_player)
            
            if current_model is None:
                # 随机动作（如果没有对应的模型）
                action_mask = env.get_action_mask()
                valid_actions = [i for i, valid in enumerate(action_mask) if valid]
                action = np.random.choice(valid_actions)
            else:
                # 使用模型选择动作
                state_vector = state_encoder.encode_game_state(state, current_player)
                action_mask = env.get_action_mask()
                
                state_tensor = torch.FloatTensor(state_vector.to_vector()).unsqueeze(0)
                mask_tensor = torch.FloatTensor(action_mask).unsqueeze(0) if action_mask is not None else None
                
                with torch.no_grad():
                    if hasattr(current_model, 'get_action_and_value'):
                        action, _, _, _, _ = current_model.get_action_and_value(state_tensor, mask_tensor)
                        action = action.item()
                    else:
                        output = current_model(state_tensor)
                        if isinstance(output, tuple):
                            policy, _ = output
                        else:
                            policy = output
                        
                        if mask_tensor is not None:
                            policy = policy * mask_tensor
                            policy = policy / (policy.sum(dim=-1, keepdim=True) + 1e-8)
                        
                        action = torch.argmax(policy, dim=-1).item()
            
            state, reward, done, info = env.step(action)
            episode_length += 1
            
            if done:
                return {
                    'winner': info.get('winner'),
                    'episode_length': episode_length,
                    'player1_id': player1_id,
                    'player2_id': player2_id
                }
        
        return {
            'winner': None,  # 平局
            'episode_length': episode_length,
            'player1_id': player1_id,
            'player2_id': player2_id
        }
    
    def _generate_evaluation_report(self, model_name: str, results: List[GameResult],
                                  metrics: Dict[str, Any]) -> Dict[str, Any]:
        """生成评估报告"""
        return {
            'model_name': model_name,
            'evaluation_config': self.config,
            'total_games': len(results),
            'valid_games': len([r for r in results if not r.error_occurred]),
            'metrics': metrics,
            'timestamp': time.time()
        }
    
    def _generate_comparison_report(self, all_metrics: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
        """生成模型比较报告"""
        comparison = {
            'models': list(all_metrics.keys()),
            'metrics_comparison': {},
            'rankings': {},
            'timestamp': time.time()
        }
        
        # 比较各项指标
        for metric_name in ['win_rate', 'average_reward']:
            comparison['metrics_comparison'][metric_name] = {}
            values = []
            
            for model_name, metrics in all_metrics.items():
                value = metrics.get(metric_name, 0)
                comparison['metrics_comparison'][metric_name][model_name] = value
                values.append((model_name, value))
            
            # 排序
            values.sort(key=lambda x: x[1], reverse=True)
            comparison['rankings'][metric_name] = [name for name, _ in values]
        
        return comparison
    
    def _calculate_tournament_stats(self, tournament_results: Dict[str, Any],
                                  model_names: List[str]) -> Dict[str, Any]:
        """计算锦标赛统计"""
        # 初始化统计
        stats = {model_name: {'wins': 0, 'losses': 0, 'draws': 0} for model_name in model_names}
        
        # 统计每个模型的胜负
        for match_key, match_result in tournament_results.items():
            model1_name = match_result['model1_name']
            model2_name = match_result['model2_name']
            
            stats[model1_name]['wins'] += match_result['model1_wins']
            stats[model1_name]['losses'] += match_result['model2_wins']
            stats[model1_name]['draws'] += match_result['draws']
            
            stats[model2_name]['wins'] += match_result['model2_wins']
            stats[model2_name]['losses'] += match_result['model1_wins']
            stats[model2_name]['draws'] += match_result['draws']
        
        # 计算胜率和排名
        for model_name in model_names:
            total_games = stats[model_name]['wins'] + stats[model_name]['losses'] + stats[model_name]['draws']
            stats[model_name]['total_games'] = total_games
            stats[model_name]['win_rate'] = stats[model_name]['wins'] / total_games if total_games > 0 else 0
        
        # 排名
        ranking = sorted(model_names, key=lambda x: stats[x]['win_rate'], reverse=True)
        
        return {
            'individual_stats': stats,
            'ranking': ranking,
            'detailed_matches': tournament_results
        }
    
    def _save_evaluation_results(self, model_name: str, report: Dict[str, Any]):
        """保存评估结果"""
        results_file = os.path.join(self.config.results_dir, f"{model_name}_evaluation.json")
        with open(results_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False, default=str)
    
    def _save_comparison_results(self, comparison_report: Dict[str, Any]):
        """保存比较结果"""
        results_file = os.path.join(self.config.results_dir, "model_comparison.json")
        with open(results_file, 'w', encoding='utf-8') as f:
            json.dump(comparison_report, f, indent=2, ensure_ascii=False, default=str)
    
    def _save_tournament_results(self, tournament_results: Dict[str, Any],
                               tournament_stats: Dict[str, Any]):
        """保存锦标赛结果"""
        results_file = os.path.join(self.config.results_dir, "tournament_results.json")
        with open(results_file, 'w', encoding='utf-8') as f:
            json.dump({
                'tournament_results': tournament_results,
                'tournament_stats': tournament_stats
            }, f, indent=2, ensure_ascii=False, default=str)
    
    def _generate_evaluation_plots(self, model_name: str, results: List[GameResult],
                                 metrics: Dict[str, Any]):
        """生成评估图表"""
        # 设置图表样式
        plt.style.use('seaborn-v0_8')
        
        # 创建子图
        fig, axes = plt.subplots(2, 2, figsize=(15, 12))
        fig.suptitle(f'Model Evaluation: {model_name}', fontsize=16)
        
        # 1. 回合长度分布
        valid_results = [r for r in results if not r.error_occurred]
        episode_lengths = [r.episode_length for r in valid_results]
        
        axes[0, 0].hist(episode_lengths, bins=20, alpha=0.7, color='skyblue')
        axes[0, 0].set_title('Episode Length Distribution')
        axes[0, 0].set_xlabel('Episode Length')
        axes[0, 0].set_ylabel('Frequency')
        
        # 2. 奖励分布
        rewards = [r.total_reward for r in valid_results]
        axes[0, 1].hist(rewards, bins=20, alpha=0.7, color='lightgreen')
        axes[0, 1].set_title('Reward Distribution')
        axes[0, 1].set_xlabel('Total Reward')
        axes[0, 1].set_ylabel('Frequency')
        
        # 3. 动作分布（如果有数据）
        if 'action_diversity' in metrics and metrics['action_diversity']['action_distribution']:
            action_dist = metrics['action_diversity']['action_distribution']
            actions = list(action_dist.keys())
            counts = list(action_dist.values())
            
            axes[1, 0].bar(range(len(actions)), counts, alpha=0.7, color='orange')
            axes[1, 0].set_title('Action Distribution')
            axes[1, 0].set_xlabel('Action ID')
            axes[1, 0].set_ylabel('Count')
            axes[1, 0].set_xticks(range(0, len(actions), max(1, len(actions)//10)))
        
        # 4. 价值函数准确性（如果有数据）
        if 'value_accuracy' in metrics:
            value_acc = metrics['value_accuracy']
            metric_names = ['MSE', 'MAE', 'Correlation']
            metric_values = [value_acc['mse'], value_acc['mae'], value_acc['correlation']]
            
            axes[1, 1].bar(metric_names, metric_values, alpha=0.7, color='purple')
            axes[1, 1].set_title('Value Function Accuracy')
            axes[1, 1].set_ylabel('Value')
        
        plt.tight_layout()
        plot_file = os.path.join(self.config.plots_dir, f"{model_name}_evaluation.png")
        plt.savefig(plot_file, dpi=300, bbox_inches='tight')
        plt.close()
    
    def _generate_comparison_plots(self, all_metrics: Dict[str, Dict[str, Any]]):
        """生成模型比较图表"""
        model_names = list(all_metrics.keys())
        
        # 创建比较图表
        fig, axes = plt.subplots(1, 2, figsize=(15, 6))
        fig.suptitle('Model Comparison', fontsize=16)
        
        # 胜率比较
        win_rates = [all_metrics[name].get('win_rate', 0) for name in model_names]
        axes[0].bar(model_names, win_rates, alpha=0.7, color='skyblue')
        axes[0].set_title('Win Rate Comparison')
        axes[0].set_ylabel('Win Rate')
        axes[0].tick_params(axis='x', rotation=45)
        
        # 平均奖励比较
        avg_rewards = [all_metrics[name].get('average_reward', 0) for name in model_names]
        axes[1].bar(model_names, avg_rewards, alpha=0.7, color='lightgreen')
        axes[1].set_title('Average Reward Comparison')
        axes[1].set_ylabel('Average Reward')
        axes[1].tick_params(axis='x', rotation=45)
        
        plt.tight_layout()
        plot_file = os.path.join(self.config.plots_dir, "model_comparison.png")
        plt.savefig(plot_file, dpi=300, bbox_inches='tight')
        plt.close()
    
    def _generate_tournament_plots(self, tournament_stats: Dict[str, Any]):
        """生成锦标赛图表"""
        individual_stats = tournament_stats['individual_stats']
        model_names = list(individual_stats.keys())
        
        # 创建锦标赛结果图表
        fig, axes = plt.subplots(1, 2, figsize=(15, 6))
        fig.suptitle('Tournament Results', fontsize=16)
        
        # 胜率排名
        win_rates = [individual_stats[name]['win_rate'] for name in model_names]
        sorted_indices = sorted(range(len(win_rates)), key=lambda i: win_rates[i], reverse=True)
        sorted_names = [model_names[i] for i in sorted_indices]
        sorted_win_rates = [win_rates[i] for i in sorted_indices]
        
        axes[0].bar(sorted_names, sorted_win_rates, alpha=0.7, color='gold')
        axes[0].set_title('Tournament Win Rate Ranking')
        axes[0].set_ylabel('Win Rate')
        axes[0].tick_params(axis='x', rotation=45)
        
        # 胜负统计
        wins = [individual_stats[name]['wins'] for name in model_names]
        losses = [individual_stats[name]['losses'] for name in model_names]
        draws = [individual_stats[name]['draws'] for name in model_names]
        
        x = np.arange(len(model_names))
        width = 0.25
        
        axes[1].bar(x - width, wins, width, label='Wins', alpha=0.7, color='green')
        axes[1].bar(x, losses, width, label='Losses', alpha=0.7, color='red')
        axes[1].bar(x + width, draws, width, label='Draws', alpha=0.7, color='gray')
        
        axes[1].set_title('Tournament Win/Loss/Draw Statistics')
        axes[1].set_ylabel('Count')
        axes[1].set_xticks(x)
        axes[1].set_xticklabels(model_names, rotation=45)
        axes[1].legend()
        
        plt.tight_layout()
        plot_file = os.path.join(self.config.plots_dir, "tournament_results.png")
        plt.savefig(plot_file, dpi=300, bbox_inches='tight')
        plt.close()

def create_evaluator(config_dict: Dict = None) -> ModelEvaluator:
    """创建模型评估器的工厂函数"""
    if config_dict is None:
        config = EvaluationConfig()
    else:
        config = EvaluationConfig(**config_dict)
    
    return ModelEvaluator(config)

if __name__ == "__main__":
    # 测试评估系统
    config = EvaluationConfig(
        num_episodes=10,
        tournament_rounds=5,
        results_dir="test_evaluation_results",
        plots_dir="test_evaluation_plots"
    )
    
    evaluator = ModelEvaluator(config)
    print("评估系统测试完成！")