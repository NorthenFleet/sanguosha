#!/usr/bin/env python3
"""
分布式PPO (Distributed PPO) 实现
支持多进程/多机器并行训练，提升训练效率
"""

import torch
import torch.multiprocessing as mp
import torch.distributed as dist
from torch.nn.parallel import DistributedDataParallel as DDP
import numpy as np
import time
import queue
import threading
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass
import pickle
import socket
from pathlib import Path
import logging

from .ppo_agent import PPOAgent, PPOConfig, PPOBuffer, Experience
from .training_environment import SanguoshaEnvironment, TrainingConfig
from .reward_system import RewardCalculator, RewardConfig
from .self_play_trainer import SelfPlayConfig, AgentPool

@dataclass
class DistributedConfig:
    """分布式训练配置"""
    # 分布式参数
    world_size: int = 4              # 总进程数
    num_workers: int = 3             # 工作进程数
    num_learners: int = 1            # 学习进程数
    
    # 通信参数
    backend: str = "nccl"            # 通信后端 (nccl, gloo, mpi)
    master_addr: str = "localhost"   # 主节点地址
    master_port: str = "12355"       # 主节点端口
    
    # 缓冲区参数
    global_buffer_size: int = 8192   # 全局经验缓冲区大小
    local_buffer_size: int = 2048    # 本地经验缓冲区大小
    sync_interval: int = 100         # 同步间隔
    
    # 性能参数
    batch_size: int = 256            # 分布式批次大小
    gradient_accumulation: int = 4   # 梯度累积步数
    async_update: bool = True        # 异步更新
    
    # 负载均衡
    dynamic_batching: bool = True    # 动态批处理
    load_balancing: bool = True      # 负载均衡

class ParameterServer:
    """参数服务器"""
    
    def __init__(self, model_config: PPOConfig, distributed_config: DistributedConfig):
        self.model_config = model_config
        self.distributed_config = distributed_config
        
        # 创建全局模型
        self.global_agent = PPOAgent(model_config)
        self.version = 0
        
        # 同步锁
        self.lock = threading.Lock()
        
        # 统计信息
        self.update_count = 0
        self.worker_stats = {}
        
        # 梯度缓冲区
        self.gradient_buffer = []
        self.gradient_count = 0
        
    def get_parameters(self) -> Dict:
        """获取全局参数"""
        with self.lock:
            return {
                'state_dict': self.global_agent.network.state_dict(),
                'version': self.version
            }
    
    def update_parameters(self, gradients: Dict, worker_id: str) -> bool:
        """更新全局参数"""
        with self.lock:
            # 累积梯度
            self.gradient_buffer.append((gradients, worker_id))
            self.gradient_count += 1
            
            # 检查是否达到更新条件
            if self.gradient_count >= self.distributed_config.gradient_accumulation:
                self._apply_gradients()
                return True
            
            return False
    
    def _apply_gradients(self):
        """应用累积的梯度"""
        if not self.gradient_buffer:
            return
        
        # 平均梯度
        averaged_gradients = {}
        param_names = list(self.gradient_buffer[0][0].keys())
        
        for param_name in param_names:
            gradients = [grad_dict[param_name] for grad_dict, _ in self.gradient_buffer]
            averaged_gradients[param_name] = torch.stack(gradients).mean(dim=0)
        
        # 应用梯度
        with torch.no_grad():
            for name, param in self.global_agent.network.named_parameters():
                if name in averaged_gradients:
                    param.grad = averaged_gradients[name]
        
        # 优化器步骤
        self.global_agent.optimizer.step()
        self.global_agent.optimizer.zero_grad()
        
        # 更新版本
        self.version += 1
        self.update_count += 1
        
        # 清空缓冲区
        self.gradient_buffer.clear()
        self.gradient_count = 0
        
        # 记录统计信息
        worker_ids = [worker_id for _, worker_id in self.gradient_buffer]
        for worker_id in set(worker_ids):
            if worker_id not in self.worker_stats:
                self.worker_stats[worker_id] = {'updates': 0, 'last_update': time.time()}
            self.worker_stats[worker_id]['updates'] += 1
            self.worker_stats[worker_id]['last_update'] = time.time()
    
    def get_stats(self) -> Dict:
        """获取统计信息"""
        with self.lock:
            return {
                'version': self.version,
                'update_count': self.update_count,
                'worker_stats': self.worker_stats.copy(),
                'gradient_buffer_size': len(self.gradient_buffer)
            }

class DistributedWorker:
    """分布式工作进程"""
    
    def __init__(self, worker_id: str, rank: int, world_size: int,
                 ppo_config: PPOConfig, training_config: TrainingConfig,
                 distributed_config: DistributedConfig):
        
        self.worker_id = worker_id
        self.rank = rank
        self.world_size = world_size
        self.ppo_config = ppo_config
        self.training_config = training_config
        self.distributed_config = distributed_config
        
        # 初始化分布式环境
        self._init_distributed()
        
        # 创建本地智能体
        self.local_agent = PPOAgent(ppo_config)
        
        # 创建环境
        self.env = SanguoshaEnvironment(training_config)
        
        # 创建奖励计算器
        reward_config = RewardConfig()
        self.reward_calculator = RewardCalculator(reward_config)
        
        # 本地缓冲区
        self.local_buffer = PPOBuffer(
            distributed_config.local_buffer_size, 
            ppo_config.state_dim
        )
        
        # 统计信息
        self.episode_count = 0
        self.step_count = 0
        self.last_sync_time = time.time()
        
        # 参数服务器连接
        self.parameter_server = None
        self.local_version = -1
        
    def _init_distributed(self):
        """初始化分布式环境"""
        os.environ['MASTER_ADDR'] = self.distributed_config.master_addr
        os.environ['MASTER_PORT'] = self.distributed_config.master_port
        
        # 初始化进程组
        dist.init_process_group(
            backend=self.distributed_config.backend,
            rank=self.rank,
            world_size=self.world_size
        )
        
        # 设置设备
        if torch.cuda.is_available():
            torch.cuda.set_device(self.rank % torch.cuda.device_count())
            self.device = torch.device(f"cuda:{self.rank % torch.cuda.device_count()}")
        else:
            self.device = torch.device("cpu")
        
        self.local_agent.network.to(self.device)
    
    def connect_parameter_server(self, parameter_server: ParameterServer):
        """连接参数服务器"""
        self.parameter_server = parameter_server
        self._sync_parameters()
    
    def _sync_parameters(self):
        """同步参数"""
        if not self.parameter_server:
            return
        
        params = self.parameter_server.get_parameters()
        
        if params['version'] > self.local_version:
            self.local_agent.network.load_state_dict(params['state_dict'])
            self.local_version = params['version']
    
    def run_episodes(self, num_episodes: int):
        """运行训练episodes"""
        for episode in range(num_episodes):
            self._run_single_episode()
            
            # 定期同步参数
            if episode % self.distributed_config.sync_interval == 0:
                self._sync_parameters()
                self._send_gradients()
    
    def _run_single_episode(self):
        """运行单个episode"""
        state, action_mask = self.env.reset()
        episode_reward = 0.0
        step = 0
        
        while step < self.training_config.max_steps_per_episode:
            # 选择动作
            action, log_prob, value = self.local_agent.select_action(
                self.env.game, 
                self.env.game.get_current_player(),
                action_mask.astype(bool)
            )
            
            # 执行动作
            next_state, reward, done, info = self.env.step(action)
            
            # 存储经验
            experience = Experience(
                state=state.to_vector(),
                action=action,
                reward=reward,
                next_state=next_state.to_vector(),
                done=done,
                log_prob=log_prob,
                value=value,
                action_mask=action_mask
            )
            
            self.local_buffer.add(experience)
            episode_reward += reward
            
            if done:
                break
            
            state = next_state
            action_mask = self.env._get_action_mask(self.env.game.get_current_player())
            step += 1
        
        self.episode_count += 1
        self.step_count += step
        
        # 如果缓冲区满了，进行本地更新
        if self.local_buffer.size >= self.ppo_config.batch_size:
            self._local_update()
    
    def _local_update(self):
        """本地更新"""
        if self.local_buffer.size < self.ppo_config.batch_size:
            return
        
        # 计算GAE
        self.local_buffer.compute_gae(
            self.ppo_config.gamma, 
            self.ppo_config.gae_lambda
        )
        
        # 收集梯度
        gradients = self._compute_gradients()
        
        # 发送梯度到参数服务器
        if self.parameter_server and gradients:
            self.parameter_server.update_parameters(gradients, self.worker_id)
        
        # 清空本地缓冲区
        self.local_buffer.clear()
    
    def _compute_gradients(self) -> Optional[Dict]:
        """计算梯度"""
        if self.local_buffer.size == 0:
            return None
        
        gradients = {}
        
        # 进行一轮PPO更新并收集梯度
        for batch in self.local_buffer.get_batches(self.ppo_config.mini_batch_size):
            states = batch['states'].to(self.device)
            actions = batch['actions'].to(self.device)
            old_log_probs = batch['old_log_probs'].to(self.device)
            advantages = batch['advantages'].to(self.device)
            returns = batch['returns'].to(self.device)
            action_masks = batch['action_masks'].to(self.device)
            
            # 前向传播
            action_probs, values = self.local_agent.network(states, action_masks)
            dist = torch.distributions.Categorical(action_probs)
            new_log_probs = dist.log_prob(actions)
            entropy = dist.entropy()
            
            # 计算损失
            ratio = torch.exp(new_log_probs - old_log_probs)
            surr1 = ratio * advantages
            surr2 = torch.clamp(ratio, 1 - self.ppo_config.clip_epsilon, 1 + self.ppo_config.clip_epsilon) * advantages
            policy_loss = -torch.min(surr1, surr2).mean()
            
            value_loss = torch.nn.functional.mse_loss(values, returns)
            entropy_loss = -entropy.mean()
            
            total_loss = (policy_loss + 
                         self.ppo_config.value_coef * value_loss + 
                         self.ppo_config.entropy_coef * entropy_loss)
            
            # 反向传播
            self.local_agent.optimizer.zero_grad()
            total_loss.backward()
            
            # 收集梯度
            for name, param in self.local_agent.network.named_parameters():
                if param.grad is not None:
                    if name not in gradients:
                        gradients[name] = param.grad.clone()
                    else:
                        gradients[name] += param.grad.clone()
        
        # 平均梯度
        num_batches = len(list(self.local_buffer.get_batches(self.ppo_config.mini_batch_size)))
        for name in gradients:
            gradients[name] /= num_batches
        
        return gradients
    
    def _send_gradients(self):
        """发送梯度（异步）"""
        if not self.distributed_config.async_update:
            return
        
        # 这里可以实现异步梯度发送逻辑
        pass
    
    def get_stats(self) -> Dict:
        """获取工作进程统计信息"""
        return {
            'worker_id': self.worker_id,
            'rank': self.rank,
            'episode_count': self.episode_count,
            'step_count': self.step_count,
            'buffer_size': self.local_buffer.size,
            'local_version': self.local_version,
            'last_sync_time': self.last_sync_time
        }

class DistributedPPOTrainer:
    """分布式PPO训练器"""
    
    def __init__(self, ppo_config: PPOConfig, training_config: TrainingConfig,
                 distributed_config: DistributedConfig):
        
        self.ppo_config = ppo_config
        self.training_config = training_config
        self.distributed_config = distributed_config
        
        # 参数服务器
        self.parameter_server = ParameterServer(ppo_config, distributed_config)
        
        # 工作进程池
        self.workers = []
        self.worker_processes = []
        
        # 训练统计
        self.training_stats = {
            'global_episodes': 0,
            'global_steps': 0,
            'parameter_updates': 0,
            'throughput': [],
            'worker_stats': {}
        }
        
        # 保存目录
        self.save_dir = Path("models/distributed_ppo")
        self.save_dir.mkdir(parents=True, exist_ok=True)
        
        # 日志
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
    
    def start_training(self, total_episodes: int):
        """开始分布式训练"""
        self.logger.info("启动分布式PPO训练...")
        self.logger.info(f"配置: {self.distributed_config.num_workers}个工作进程, "
                        f"{self.distributed_config.num_learners}个学习进程")
        
        try:
            # 启动工作进程
            self._start_workers()
            
            # 监控训练进度
            self._monitor_training(total_episodes)
            
        except KeyboardInterrupt:
            self.logger.info("收到中断信号，停止训练...")
        finally:
            self._cleanup()
    
    def _start_workers(self):
        """启动工作进程"""
        for i in range(self.distributed_config.num_workers):
            worker_id = f"worker_{i}"
            
            # 创建工作进程
            process = mp.Process(
                target=self._worker_main,
                args=(worker_id, i, self.distributed_config.world_size)
            )
            process.start()
            self.worker_processes.append(process)
            
            self.logger.info(f"启动工作进程: {worker_id}")
    
    def _worker_main(self, worker_id: str, rank: int, world_size: int):
        """工作进程主函数"""
        try:
            # 创建工作进程
            worker = DistributedWorker(
                worker_id, rank, world_size,
                self.ppo_config, self.training_config, self.distributed_config
            )
            
            # 连接参数服务器
            worker.connect_parameter_server(self.parameter_server)
            
            # 运行训练
            episodes_per_worker = self.training_config.max_episodes // self.distributed_config.num_workers
            worker.run_episodes(episodes_per_worker)
            
        except Exception as e:
            self.logger.error(f"工作进程 {worker_id} 出错: {e}")
    
    def _monitor_training(self, total_episodes: int):
        """监控训练进度"""
        start_time = time.time()
        last_check_time = start_time
        last_episodes = 0
        
        while self.training_stats['global_episodes'] < total_episodes:
            time.sleep(10)  # 每10秒检查一次
            
            current_time = time.time()
            
            # 收集统计信息
            server_stats = self.parameter_server.get_stats()
            self.training_stats['parameter_updates'] = server_stats['update_count']
            
            # 计算吞吐量
            time_elapsed = current_time - last_check_time
            episodes_elapsed = self.training_stats['global_episodes'] - last_episodes
            
            if time_elapsed > 0:
                throughput = episodes_elapsed / time_elapsed
                self.training_stats['throughput'].append(throughput)
            
            # 打印进度
            self.logger.info(
                f"进度: {self.training_stats['global_episodes']}/{total_episodes} episodes, "
                f"参数更新: {self.training_stats['parameter_updates']}, "
                f"吞吐量: {throughput:.2f} episodes/s"
            )
            
            # 定期保存
            if self.training_stats['global_episodes'] % 1000 == 0:
                self._save_checkpoint()
            
            last_check_time = current_time
            last_episodes = self.training_stats['global_episodes']
    
    def _save_checkpoint(self):
        """保存检查点"""
        checkpoint_path = self.save_dir / f"checkpoint_{self.training_stats['global_episodes']}.pth"
        
        # 保存全局模型
        self.parameter_server.global_agent.save_model(str(checkpoint_path))
        
        # 保存训练统计
        stats_path = self.save_dir / f"stats_{self.training_stats['global_episodes']}.json"
        with open(stats_path, 'w') as f:
            import json
            json.dump(self.training_stats, f, indent=2)
        
        self.logger.info(f"检查点已保存: {checkpoint_path}")
    
    def _cleanup(self):
        """清理资源"""
        self.logger.info("清理分布式训练资源...")
        
        # 终止工作进程
        for process in self.worker_processes:
            if process.is_alive():
                process.terminate()
                process.join(timeout=5)
                if process.is_alive():
                    process.kill()
        
        # 清理分布式环境
        if dist.is_initialized():
            dist.destroy_process_group()
        
        self.logger.info("资源清理完成")
    
    def get_best_agent(self) -> PPOAgent:
        """获取最佳智能体"""
        return self.parameter_server.global_agent

class AsyncParameterServer:
    """异步参数服务器"""
    
    def __init__(self, model_config: PPOConfig):
        self.model_config = model_config
        self.global_agent = PPOAgent(model_config)
        
        # 异步队列
        self.gradient_queue = queue.Queue(maxsize=1000)
        self.parameter_queue = queue.Queue(maxsize=100)
        
        # 异步处理线程
        self.gradient_thread = threading.Thread(target=self._process_gradients)
        self.parameter_thread = threading.Thread(target=self._serve_parameters)
        
        self.running = False
    
    def start(self):
        """启动异步服务"""
        self.running = True
        self.gradient_thread.start()
        self.parameter_thread.start()
    
    def stop(self):
        """停止异步服务"""
        self.running = False
        self.gradient_thread.join()
        self.parameter_thread.join()
    
    def _process_gradients(self):
        """处理梯度队列"""
        while self.running:
            try:
                gradients, worker_id = self.gradient_queue.get(timeout=1)
                
                # 应用梯度
                with torch.no_grad():
                    for name, param in self.global_agent.network.named_parameters():
                        if name in gradients:
                            param.grad = gradients[name]
                
                self.global_agent.optimizer.step()
                self.global_agent.optimizer.zero_grad()
                
            except queue.Empty:
                continue
            except Exception as e:
                logging.error(f"梯度处理错误: {e}")
    
    def _serve_parameters(self):
        """提供参数服务"""
        while self.running:
            try:
                # 定期更新参数队列
                params = self.global_agent.network.state_dict()
                
                if not self.parameter_queue.full():
                    self.parameter_queue.put(params)
                
                time.sleep(0.1)  # 100ms更新一次
                
            except Exception as e:
                logging.error(f"参数服务错误: {e}")
    
    def submit_gradients(self, gradients: Dict, worker_id: str):
        """提交梯度"""
        try:
            self.gradient_queue.put((gradients, worker_id), timeout=1)
        except queue.Full:
            logging.warning(f"梯度队列满，丢弃来自 {worker_id} 的梯度")
    
    def get_parameters(self) -> Optional[Dict]:
        """获取参数"""
        try:
            return self.parameter_queue.get_nowait()
        except queue.Empty:
            return None

if __name__ == "__main__":
    # 配置参数
    ppo_config = PPOConfig()
    training_config = TrainingConfig(max_episodes=10000)
    distributed_config = DistributedConfig(
        world_size=4,
        num_workers=3,
        num_learners=1
    )
    
    # 创建分布式训练器
    trainer = DistributedPPOTrainer(ppo_config, training_config, distributed_config)
    
    print("分布式PPO训练器初始化完成")
    print(f"配置: {distributed_config.num_workers}个工作进程")
    
    # 开始训练
    trainer.start_training(total_episodes=10000)