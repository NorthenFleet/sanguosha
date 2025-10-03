#!/usr/bin/env python3
"""
训练工具模块
提供训练过程中需要的各种工具函数和类
"""

import os
import json
import yaml
import pickle
import logging
import time
import torch
import numpy as np
import matplotlib.pyplot as plt
from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass, asdict
from pathlib import Path
import shutil
from datetime import datetime
import wandb
from collections import defaultdict, deque

class ConfigManager:
    """配置管理器"""
    
    @staticmethod
    def load_config(config_path: str) -> Dict:
        """加载配置文件"""
        config_path = Path(config_path)
        
        if not config_path.exists():
            raise FileNotFoundError(f"配置文件不存在: {config_path}")
        
        if config_path.suffix == '.json':
            with open(config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        elif config_path.suffix in ['.yaml', '.yml']:
            with open(config_path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        else:
            raise ValueError(f"不支持的配置文件格式: {config_path.suffix}")
    
    @staticmethod
    def save_config(config: Dict, config_path: str):
        """保存配置文件"""
        config_path = Path(config_path)
        config_path.parent.mkdir(parents=True, exist_ok=True)
        
        if config_path.suffix == '.json':
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
        elif config_path.suffix in ['.yaml', '.yml']:
            with open(config_path, 'w', encoding='utf-8') as f:
                yaml.dump(config, f, default_flow_style=False, allow_unicode=True)
        else:
            raise ValueError(f"不支持的配置文件格式: {config_path.suffix}")
    
    @staticmethod
    def merge_configs(base_config: Dict, override_config: Dict) -> Dict:
        """合并配置"""
        merged = base_config.copy()
        
        def _merge_dict(base: Dict, override: Dict):
            for key, value in override.items():
                if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                    _merge_dict(base[key], value)
                else:
                    base[key] = value
        
        _merge_dict(merged, override_config)
        return merged

class Logger:
    """训练日志记录器"""
    
    def __init__(self, log_dir: str, experiment_name: str, use_wandb: bool = False):
        self.log_dir = Path(log_dir)
        self.experiment_name = experiment_name
        self.use_wandb = use_wandb
        
        # 创建日志目录
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
        # 设置文件日志
        self._setup_file_logging()
        
        # 设置wandb（如果启用）
        if use_wandb:
            self._setup_wandb()
        
        # 训练指标存储
        self.metrics = defaultdict(list)
        self.step_count = 0
    
    def _setup_file_logging(self):
        """设置文件日志"""
        log_file = self.log_dir / f"{self.experiment_name}.log"
        
        # 创建logger
        self.logger = logging.getLogger(self.experiment_name)
        self.logger.setLevel(logging.INFO)
        
        # 清除已有的handlers
        self.logger.handlers.clear()
        
        # 文件handler
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(logging.INFO)
        
        # 控制台handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        
        # 格式化器
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)
        
        # 添加handlers
        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)
    
    def _setup_wandb(self):
        """设置wandb"""
        try:
            wandb.init(
                project="sanguosha-ai",
                name=self.experiment_name,
                dir=str(self.log_dir)
            )
        except Exception as e:
            self.logger.warning(f"无法初始化wandb: {e}")
            self.use_wandb = False
    
    def log_metrics(self, metrics: Dict[str, float], step: Optional[int] = None):
        """记录训练指标"""
        if step is None:
            step = self.step_count
            self.step_count += 1
        
        # 存储到本地
        for key, value in metrics.items():
            self.metrics[key].append((step, value))
        
        # 记录到文件
        metric_str = " | ".join([f"{k}: {v:.4f}" for k, v in metrics.items()])
        self.logger.info(f"Step {step} - {metric_str}")
        
        # 记录到wandb
        if self.use_wandb:
            wandb.log(metrics, step=step)
    
    def log_text(self, message: str, level: str = "info"):
        """记录文本消息"""
        if level == "info":
            self.logger.info(message)
        elif level == "warning":
            self.logger.warning(message)
        elif level == "error":
            self.logger.error(message)
        elif level == "debug":
            self.logger.debug(message)
    
    def save_metrics(self, filename: str = "metrics.json"):
        """保存指标到文件"""
        metrics_file = self.log_dir / filename
        
        # 转换为可序列化的格式
        serializable_metrics = {}
        for key, values in self.metrics.items():
            serializable_metrics[key] = {
                'steps': [v[0] for v in values],
                'values': [v[1] for v in values]
            }
        
        with open(metrics_file, 'w', encoding='utf-8') as f:
            json.dump(serializable_metrics, f, indent=2)
    
    def plot_metrics(self, metrics_to_plot: List[str] = None, save_path: str = None):
        """绘制训练指标"""
        if metrics_to_plot is None:
            metrics_to_plot = list(self.metrics.keys())
        
        fig, axes = plt.subplots(len(metrics_to_plot), 1, figsize=(12, 4 * len(metrics_to_plot)))
        if len(metrics_to_plot) == 1:
            axes = [axes]
        
        for i, metric_name in enumerate(metrics_to_plot):
            if metric_name in self.metrics:
                steps, values = zip(*self.metrics[metric_name])
                axes[i].plot(steps, values)
                axes[i].set_title(metric_name)
                axes[i].set_xlabel('Step')
                axes[i].set_ylabel('Value')
                axes[i].grid(True)
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path)
        else:
            plt.savefig(self.log_dir / "training_metrics.png")
        
        plt.close()

class ModelManager:
    """模型管理器"""
    
    def __init__(self, model_dir: str):
        self.model_dir = Path(model_dir)
        self.model_dir.mkdir(parents=True, exist_ok=True)
    
    def save_model(self, model: torch.nn.Module, optimizer: torch.optim.Optimizer,
                   step: int, metrics: Dict[str, float], 
                   filename: str = None, is_best: bool = False) -> str:
        """保存模型"""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"model_step_{step}_{timestamp}.pth"
        
        model_path = self.model_dir / filename
        
        # 保存模型状态
        checkpoint = {
            'step': step,
            'model_state_dict': model.state_dict(),
            'optimizer_state_dict': optimizer.state_dict(),
            'metrics': metrics,
            'timestamp': datetime.now().isoformat()
        }
        
        torch.save(checkpoint, model_path)
        
        # 如果是最佳模型，创建符号链接
        if is_best:
            best_model_path = self.model_dir / "best_model.pth"
            if best_model_path.exists():
                best_model_path.unlink()
            best_model_path.symlink_to(filename)
        
        return str(model_path)
    
    def load_model(self, model: torch.nn.Module, optimizer: torch.optim.Optimizer = None,
                   model_path: str = None, load_best: bool = False) -> Dict:
        """加载模型"""
        if load_best:
            model_path = self.model_dir / "best_model.pth"
        elif model_path is None:
            raise ValueError("必须指定model_path或设置load_best=True")
        
        model_path = Path(model_path)
        if not model_path.exists():
            raise FileNotFoundError(f"模型文件不存在: {model_path}")
        
        checkpoint = torch.load(model_path, map_location='cpu')
        
        # 加载模型状态
        model.load_state_dict(checkpoint['model_state_dict'])
        
        # 加载优化器状态（如果提供）
        if optimizer is not None and 'optimizer_state_dict' in checkpoint:
            optimizer.load_state_dict(checkpoint['optimizer_state_dict'])
        
        return {
            'step': checkpoint.get('step', 0),
            'metrics': checkpoint.get('metrics', {}),
            'timestamp': checkpoint.get('timestamp', '')
        }
    
    def list_models(self) -> List[Dict]:
        """列出所有模型"""
        models = []
        for model_file in self.model_dir.glob("*.pth"):
            if model_file.name == "best_model.pth":
                continue
            
            try:
                checkpoint = torch.load(model_file, map_location='cpu')
                models.append({
                    'filename': model_file.name,
                    'path': str(model_file),
                    'step': checkpoint.get('step', 0),
                    'metrics': checkpoint.get('metrics', {}),
                    'timestamp': checkpoint.get('timestamp', ''),
                    'size_mb': model_file.stat().st_size / (1024 * 1024)
                })
            except Exception as e:
                print(f"无法读取模型文件 {model_file}: {e}")
        
        return sorted(models, key=lambda x: x['step'])
    
    def cleanup_old_models(self, keep_last_n: int = 5, keep_best: bool = True):
        """清理旧模型"""
        models = self.list_models()
        
        if len(models) <= keep_last_n:
            return
        
        # 保留最新的N个模型
        models_to_delete = models[:-keep_last_n]
        
        for model_info in models_to_delete:
            model_path = Path(model_info['path'])
            if model_path.exists():
                model_path.unlink()
                print(f"删除旧模型: {model_path.name}")

class PerformanceMonitor:
    """性能监控器"""
    
    def __init__(self, window_size: int = 100):
        self.window_size = window_size
        self.metrics = defaultdict(lambda: deque(maxlen=window_size))
        self.start_time = time.time()
    
    def update(self, metrics: Dict[str, float]):
        """更新指标"""
        for key, value in metrics.items():
            self.metrics[key].append(value)
    
    def get_stats(self) -> Dict[str, Dict[str, float]]:
        """获取统计信息"""
        stats = {}
        for key, values in self.metrics.items():
            if values:
                stats[key] = {
                    'mean': np.mean(values),
                    'std': np.std(values),
                    'min': np.min(values),
                    'max': np.max(values),
                    'latest': values[-1]
                }
        return stats
    
    def get_training_speed(self) -> Dict[str, float]:
        """获取训练速度统计"""
        elapsed_time = time.time() - self.start_time
        
        if 'episode_count' in self.metrics:
            episodes = len(self.metrics['episode_count'])
            episodes_per_hour = episodes / (elapsed_time / 3600)
        else:
            episodes_per_hour = 0
        
        if 'step_count' in self.metrics:
            steps = len(self.metrics['step_count'])
            steps_per_second = steps / elapsed_time
        else:
            steps_per_second = 0
        
        return {
            'elapsed_time_hours': elapsed_time / 3600,
            'episodes_per_hour': episodes_per_hour,
            'steps_per_second': steps_per_second
        }

class ExperimentManager:
    """实验管理器"""
    
    def __init__(self, base_dir: str):
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)
    
    def create_experiment(self, experiment_name: str, config: Dict) -> str:
        """创建新实验"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        exp_name = f"{experiment_name}_{timestamp}"
        exp_dir = self.base_dir / exp_name
        exp_dir.mkdir(parents=True, exist_ok=True)
        
        # 保存实验配置
        config_path = exp_dir / "config.json"
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
        
        # 创建子目录
        (exp_dir / "logs").mkdir(exist_ok=True)
        (exp_dir / "models").mkdir(exist_ok=True)
        (exp_dir / "plots").mkdir(exist_ok=True)
        
        return str(exp_dir)
    
    def list_experiments(self) -> List[Dict]:
        """列出所有实验"""
        experiments = []
        for exp_dir in self.base_dir.iterdir():
            if exp_dir.is_dir():
                config_path = exp_dir / "config.json"
                if config_path.exists():
                    try:
                        with open(config_path, 'r', encoding='utf-8') as f:
                            config = json.load(f)
                        
                        experiments.append({
                            'name': exp_dir.name,
                            'path': str(exp_dir),
                            'config': config,
                            'created_time': datetime.fromtimestamp(exp_dir.stat().st_ctime)
                        })
                    except Exception as e:
                        print(f"无法读取实验配置 {exp_dir}: {e}")
        
        return sorted(experiments, key=lambda x: x['created_time'], reverse=True)
    
    def compare_experiments(self, experiment_names: List[str], metric_name: str):
        """比较实验结果"""
        plt.figure(figsize=(12, 6))
        
        for exp_name in experiment_names:
            exp_dir = self.base_dir / exp_name
            metrics_file = exp_dir / "logs" / "metrics.json"
            
            if metrics_file.exists():
                with open(metrics_file, 'r', encoding='utf-8') as f:
                    metrics = json.load(f)
                
                if metric_name in metrics:
                    steps = metrics[metric_name]['steps']
                    values = metrics[metric_name]['values']
                    plt.plot(steps, values, label=exp_name)
        
        plt.xlabel('Step')
        plt.ylabel(metric_name)
        plt.title(f'Comparison of {metric_name}')
        plt.legend()
        plt.grid(True)
        plt.show()

class TrainingUtils:
    """训练工具集合"""
    
    @staticmethod
    def set_seed(seed: int):
        """设置随机种子"""
        torch.manual_seed(seed)
        torch.cuda.manual_seed(seed)
        torch.cuda.manual_seed_all(seed)
        np.random.seed(seed)
        torch.backends.cudnn.deterministic = True
        torch.backends.cudnn.benchmark = False
    
    @staticmethod
    def get_device(prefer_gpu: bool = True) -> torch.device:
        """获取计算设备"""
        if prefer_gpu and torch.cuda.is_available():
            device = torch.device('cuda')
            print(f"使用GPU: {torch.cuda.get_device_name()}")
        else:
            device = torch.device('cpu')
            print("使用CPU")
        return device
    
    @staticmethod
    def count_parameters(model: torch.nn.Module) -> int:
        """计算模型参数数量"""
        return sum(p.numel() for p in model.parameters() if p.requires_grad)
    
    @staticmethod
    def get_model_size(model: torch.nn.Module) -> float:
        """获取模型大小（MB）"""
        param_size = 0
        buffer_size = 0
        
        for param in model.parameters():
            param_size += param.nelement() * param.element_size()
        
        for buffer in model.buffers():
            buffer_size += buffer.nelement() * buffer.element_size()
        
        size_mb = (param_size + buffer_size) / (1024 * 1024)
        return size_mb
    
    @staticmethod
    def create_lr_scheduler(optimizer: torch.optim.Optimizer, 
                          scheduler_type: str = "cosine",
                          **kwargs) -> torch.optim.lr_scheduler._LRScheduler:
        """创建学习率调度器"""
        if scheduler_type == "cosine":
            return torch.optim.lr_scheduler.CosineAnnealingLR(
                optimizer, T_max=kwargs.get('T_max', 1000)
            )
        elif scheduler_type == "step":
            return torch.optim.lr_scheduler.StepLR(
                optimizer, 
                step_size=kwargs.get('step_size', 100),
                gamma=kwargs.get('gamma', 0.1)
            )
        elif scheduler_type == "exponential":
            return torch.optim.lr_scheduler.ExponentialLR(
                optimizer, gamma=kwargs.get('gamma', 0.95)
            )
        elif scheduler_type == "plateau":
            return torch.optim.lr_scheduler.ReduceLROnPlateau(
                optimizer, 
                mode=kwargs.get('mode', 'min'),
                patience=kwargs.get('patience', 10)
            )
        else:
            raise ValueError(f"不支持的调度器类型: {scheduler_type}")
    
    @staticmethod
    def save_training_script(script_content: str, save_path: str):
        """保存训练脚本"""
        with open(save_path, 'w', encoding='utf-8') as f:
            f.write(script_content)
        
        # 设置执行权限
        os.chmod(save_path, 0o755)

# 便捷函数
def setup_training_environment(config: Dict, experiment_name: str = None) -> Dict:
    """设置训练环境"""
    if experiment_name is None:
        experiment_name = f"experiment_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    # 创建实验管理器
    exp_manager = ExperimentManager(config.get('base_dir', 'experiments'))
    exp_dir = exp_manager.create_experiment(experiment_name, config)
    
    # 创建日志记录器
    logger = Logger(
        log_dir=os.path.join(exp_dir, 'logs'),
        experiment_name=experiment_name,
        use_wandb=config.get('use_wandb', False)
    )
    
    # 创建模型管理器
    model_manager = ModelManager(os.path.join(exp_dir, 'models'))
    
    # 创建性能监控器
    performance_monitor = PerformanceMonitor(
        window_size=config.get('monitor_window_size', 100)
    )
    
    # 设置随机种子
    if 'seed' in config:
        TrainingUtils.set_seed(config['seed'])
    
    # 获取设备
    device = TrainingUtils.get_device(config.get('use_gpu', True))
    
    return {
        'experiment_dir': exp_dir,
        'logger': logger,
        'model_manager': model_manager,
        'performance_monitor': performance_monitor,
        'device': device,
        'config': config
    }

if __name__ == "__main__":
    # 测试训练工具
    config = {
        'seed': 42,
        'use_gpu': True,
        'use_wandb': False,
        'base_dir': 'test_experiments'
    }
    
    env = setup_training_environment(config, "test_experiment")
    print(f"实验目录: {env['experiment_dir']}")
    print(f"设备: {env['device']}")
    
    # 测试日志记录
    logger = env['logger']
    logger.log_metrics({'loss': 0.5, 'accuracy': 0.8}, step=1)
    logger.log_text("测试日志消息")
    
    print("训练工具测试完成！")