#!/usr/bin/env python3
"""
三国杀神经网络可视化服务器 (端口 5130)

提供 AlphaStar 风格多分支网络架构的可视化接口
- 网络架构元数据
- 实时推理 (游戏状态 -> 动作概率 + 价值)
- 各分支激活值、卡牌嵌入
- 静态前端页面挂载
"""
import sys
import os
import json
import uuid
import time
from pathlib import Path
from typing import Dict, List, Optional, Any
from collections import deque

# 确保 one-sim/sanguosha 模块可导入
PROJECT_ROOT = Path(__file__).parent.parent.parent
ONE_SIM_SANGUOSHA = PROJECT_ROOT / "one-sim" / "sanguosha"
sys.path.insert(0, str(ONE_SIM_SANGUOSHA / "src"))

import numpy as np
import torch
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

# 从 one-sim/sanguosha 加载环境和模型
from envs.sanguosha_env import SanguoshaEnv
from agents.dnn_agent import (
    SanguoshaActorCritic,
    SanguoshaTrainer,
    StructuredEncoder,
    TemporalModel,
    PositionalEncoding,
)


# --------- 全局状态 ---------
app = FastAPI(title="Sanguosha Neural Visualization", version="1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 全局缓存 - 游戏环境与模型实例
_NETWORK_LIBRARY_ROOT = (
    Path(__file__).parent.parent.parent / "one-sim" / "data_lake" / "network_library"
)

_STATE = {
    "env": None,
    "model": None,
    "trainer": None,
    "obs": None,
    "info": None,
    "history": deque(maxlen=10),
    "last_action_probs": None,
    "last_value": None,
    "step_count": 0,
    "active_network_id": "sanguosha_alphastar_actor_critic",
}

# ============ 训练管理器 ============
_TRAINING_STATE = {
    "running": False,
    "thread": None,
    "should_stop": False,
    "progress": 0.0,           # 0.0 ~ 1.0
    "current_step": 0,
    "total_steps": 0,
    "start_time": 0.0,
    "config": None,            # 当前训练配置
    # 历史数据
    "step_history": [],        # [{step, loss, reward, episode, actor_loss, critic_loss, entropy, lr}]
    "recent_logs": deque(maxlen=500),  # 训练日志
    "metrics": {
        "last_loss": 0.0,
        "last_reward": 0.0,
        "episode_count": 0,
        "best_reward": -float("inf"),
        "avg_reward_100": 0.0,
    },
    "lock": None,              # threading.Lock
}

def _ensure_training_lock():
    if _TRAINING_STATE["lock"] is None:
        import threading
        _TRAINING_STATE["lock"] = threading.Lock()


def _training_thread(config: Dict[str, Any]):
    """后台训练线程：无头模式 PPO 风格训练，收集并记录所有关键指标"""
    import threading
    _ensure_training_lock()

    steps = int(config.get("total_steps", 1000))
    save_interval = int(config.get("save_interval", 200))
    log_interval = int(config.get("log_interval", 20))
    learning_rate = float(config.get("learning_rate", 3e-4))
    gamma = float(config.get("gamma", 0.99))
    entropy_coef = float(config.get("entropy_coef", 0.01))
    value_coef = float(config.get("value_coef", 0.5))
    batch_size = int(config.get("batch_size", 128))
    network_id = config.get("network_id", _STATE["active_network_id"])

    # --- 加载 & 应用网络资产 ---
    try:
        network = _load_network(network_id)
        msg = _rebuild_model_from_network(network)
        _TRAINING_STATE["recent_logs"].append(
            f"[init] 已加载网络资产 {network_id}: {msg}"
        )
    except Exception as e:
        _TRAINING_STATE["recent_logs"].append(f"[error] 加载网络资产失败: {e}")
        _TRAINING_STATE["running"] = False
        return

    model = _STATE["model"]
    trainer_obj = _STATE["trainer"]
    env = _STATE["env"]
    hp = network.get("hyperparameters", {})
    num_actions = int(hp.get("num_actions", 100))
    history_len = int(hp.get("history_len", 10))

    # --- 构造优化器 ---
    import torch
    try:
        optimizer = torch.optim.Adam(model.parameters(), lr=learning_rate)
    except Exception as e:
        optimizer = None
        _TRAINING_STATE["recent_logs"].append(f"[warn] optimizer 构造失败: {e}")

    # --- 切换到 train 模式 ---
    model.train()

    # --- 训练循环 ---
    _TRAINING_STATE["start_time"] = time.time()
    _TRAINING_STATE["total_steps"] = steps
    _TRAINING_STATE["current_step"] = 0

    # 训练缓存（简单 PPO 收集 rollout）
    rollout_buffer = []
    running_reward = 0.0
    episode_reward = 0.0
    last_episode_steps = 0
    episode_count = 0

    # 重置环境
    _STATE["obs"], _STATE["info"] = env.reset()
    _STATE["history"].clear()
    flat = _flatten_obs_for_history(_STATE["obs"])
    for _ in range(history_len):
        _STATE["history"].append(flat.copy())

    _TRAINING_STATE["recent_logs"].append(
        f"[init] 无头训练模式启动: steps={steps}, lr={learning_rate}, batch={batch_size}, algorithm=ppo"
    )

    for step in range(1, steps + 1):
        if _TRAINING_STATE["should_stop"]:
            _TRAINING_STATE["recent_logs"].append(f"[stop] 在 step {step} 收到停止信号")
            break

        # --- 推理选择动作 ---
        history_tensor = torch.tensor(
            list(_STATE["history"]), dtype=torch.float32
        ).unsqueeze(0)
        try:
            action_mask = trainer_obj._get_action_mask(_STATE["info"])
        except Exception:
            action_mask = torch.ones(num_actions)

        with torch.no_grad():
            action_probs, value = model(_STATE["obs"], history_tensor, action_mask.unsqueeze(0))

        # 随机采样或 argmax（训练中加入噪声/随机）
        if torch.rand(1).item() < 0.1:  # 10% 随机探索
            valid = torch.where(action_mask > 0)[0]
            if len(valid) > 0:
                chosen = int(valid[torch.randint(0, len(valid), (1,)).item()])
            else:
                chosen = int(torch.argmax(action_probs, dim=-1).item())
        else:
            # 从概率分布采样
            probs = action_probs[0].clone()
            probs = probs * action_mask
            if probs.sum() > 0:
                probs = probs / probs.sum()
                chosen = int(torch.multinomial(probs, 1).item())
            else:
                chosen = int(torch.argmax(action_probs, dim=-1).item())

        # --- 执行环境 step ---
        next_obs, reward, terminated, truncated, next_info = env.step(chosen)
        episode_reward += reward
        running_reward += reward

        # 记录 rollout
        rollout_buffer.append({
            "obs": _STATE["obs"],
            "action": chosen,
            "reward": float(reward),
            "value": float(value.item()),
            "next_obs": next_obs,
            "terminated": terminated,
            "log_prob": float(torch.log(action_probs[0, chosen] + 1e-8).item()),
            "action_mask": action_mask.clone(),
        })

        # 更新状态
        _STATE["obs"] = next_obs
        _STATE["info"] = next_info
        _STATE["history"].append(_flatten_obs_for_history(next_obs))

        # --- 回合终止 ---
        if terminated or truncated or (step - last_episode_steps > 300):
            episode_count += 1
            avg_r = episode_reward / max(1, step - last_episode_steps)
            _TRAINING_STATE["metrics"]["avg_reward_100"] = (
                _TRAINING_STATE["metrics"]["avg_reward_100"] * 0.95 + avg_r * 0.05
            )
            if avg_r > _TRAINING_STATE["metrics"]["best_reward"]:
                _TRAINING_STATE["metrics"]["best_reward"] = avg_r
            last_episode_steps = step
            episode_reward = 0.0
            _STATE["obs"], _STATE["info"] = env.reset()
            _STATE["history"].clear()
            flat = _flatten_obs_for_history(_STATE["obs"])
            for _ in range(history_len):
                _STATE["history"].append(flat.copy())

        # --- PPO 更新 ---
        loss_val = 0.0
        actor_loss_val = 0.0
        critic_loss_val = 0.0
        entropy_val = 0.0

        if len(rollout_buffer) >= batch_size and optimizer is not None:
            # 计算 returns & advantages (简单 GAEs)
            returns = []
            advantages = []
            R = 0.0
            for i in reversed(range(len(rollout_buffer))):
                if rollout_buffer[i]["terminated"]:
                    R = 0.0
                R = rollout_buffer[i]["reward"] + gamma * R
                returns.insert(0, R)
                advantages.insert(0, R - rollout_buffer[i]["value"])

            # 标准化 advantages
            adv_tensor = torch.tensor(advantages, dtype=torch.float32)
            if adv_tensor.std() > 1e-8:
                adv_tensor = (adv_tensor - adv_tensor.mean()) / (adv_tensor.std() + 1e-8)

            # 构建 mini-batch
            indices = torch.randperm(len(rollout_buffer))[:batch_size]
            total_loss_accum = 0.0
            actor_loss_accum = 0.0
            critic_loss_accum = 0.0
            entropy_accum = 0.0
            n_batches = 0

            for idx in indices:
                item = rollout_buffer[idx]
                hist_t = torch.tensor(list(_STATE["history"]), dtype=torch.float32).unsqueeze(0)
                # 推理当前策略
                try:
                    cur_probs, cur_value = model(item["obs"], hist_t, item["action_mask"].unsqueeze(0))
                except Exception:
                    continue

                cur_log_prob = torch.log(cur_probs[0, item["action"]] + 1e-8)
                ratio = torch.exp(cur_log_prob - item["log_prob"])

                # PPO clipped
                adv = adv_tensor[idx] if idx < len(adv_tensor) else 0.0
                surr1 = ratio * adv
                surr2 = torch.clamp(ratio, 0.8, 1.2) * adv
                actor_loss = -torch.min(surr1, surr2)

                # Critic loss
                critic_loss = 0.5 * (cur_value[0, 0] - returns[idx]) ** 2

                # Entropy
                entropy = -torch.sum(cur_probs[0] * torch.log(cur_probs[0] + 1e-8))

                loss = actor_loss + value_coef * critic_loss - entropy_coef * entropy

                optimizer.zero_grad()
                try:
                    loss.backward()
                    torch.nn.utils.clip_grad_norm_(model.parameters(), 0.5)
                    optimizer.step()
                except Exception:
                    pass

                total_loss_accum += float(loss.item())
                actor_loss_accum += float(actor_loss.item())
                critic_loss_accum += float(critic_loss.item())
                entropy_accum += float(entropy.item())
                n_batches += 1

            if n_batches > 0:
                loss_val = total_loss_accum / n_batches
                actor_loss_val = actor_loss_accum / n_batches
                critic_loss_val = critic_loss_accum / n_batches
                entropy_val = entropy_accum / n_batches

            # 清空 buffer（仅保留最新的一部分用于持续学习）
            rollout_buffer = rollout_buffer[-64:]

        # --- 记录进度 ---
        _TRAINING_STATE["current_step"] = step
        _TRAINING_STATE["progress"] = step / steps
        _TRAINING_STATE["metrics"]["last_loss"] = loss_val
        _TRAINING_STATE["metrics"]["last_reward"] = float(reward)
        _TRAINING_STATE["metrics"]["episode_count"] = episode_count

        # --- 写入历史（每 log_interval 步）---
        if step % log_interval == 0:
            elapsed = time.time() - _TRAINING_STATE["start_time"]
            with _TRAINING_STATE["lock"]:
                _TRAINING_STATE["step_history"].append({
                    "step": step,
                    "loss": round(loss_val, 6),
                    "reward": round(float(reward), 4),
                    "episode": episode_count,
                    "actor_loss": round(actor_loss_val, 6),
                    "critic_loss": round(critic_loss_val, 6),
                    "entropy": round(entropy_val, 4),
                    "avg_reward_100": round(_TRAINING_STATE["metrics"]["avg_reward_100"], 4),
                    "elapsed_sec": round(elapsed, 1),
                    "steps_per_sec": round(step / max(elapsed, 0.001), 2),
                    "network_id": network_id,
                })
            _TRAINING_STATE["recent_logs"].append(
                f"[step {step}/{steps}] ep={episode_count} loss={loss_val:.4f} "
                f"reward={reward:+.2f} avg100={_TRAINING_STATE['metrics']['avg_reward_100']:.3f} "
                f"entropy={entropy_val:.3f} elapsed={elapsed:.1f}s"
            )

        # --- 保存间隔 ---
        if save_interval > 0 and step % save_interval == 0:
            # 更新网络资产中的训练状态（不写模型权重，仅记录训练进度）
            try:
                net_data = _load_network(network_id)
                net_data.setdefault("training_compatibility", {})
                tc = net_data["training_compatibility"]
                tc["last_train_step"] = step
                tc["last_train_loss"] = loss_val
                tc["last_train_reward"] = _TRAINING_STATE["metrics"]["avg_reward_100"]
                tc["total_episodes_trained"] = tc.get("total_episodes_trained", 0) + episode_count
                tc["last_updated"] = time.strftime("%Y-%m-%d %H:%M:%S")
                _save_network(network_id, net_data)
                _TRAINING_STATE["recent_logs"].append(
                    f"[save] step {step} 网络资产已更新到 data_lake: {network_id}"
                )
            except Exception as e:
                _TRAINING_STATE["recent_logs"].append(f"[warn] 更新网络资产失败: {e}")

        # --- 控制训练节奏，避免 CPU 满载 ---
        if step % 50 == 0:
            time.sleep(0.05)

    # --- 训练结束 ---
    model.eval()
    elapsed_total = time.time() - _TRAINING_STATE["start_time"]
    _TRAINING_STATE["recent_logs"].append(
        f"[done] 训练完成, total_steps={_TRAINING_STATE['current_step']}, "
        f"episodes={episode_count}, elapsed={elapsed_total:.1f}s, "
        f"best_avg_reward={_TRAINING_STATE['metrics']['best_reward']:.4f}"
    )
    _TRAINING_STATE["running"] = False
    _TRAINING_STATE["should_stop"] = False


def _list_network_files() -> List[Path]:
    """扫描 network_library 目录下的 *.json 文件（排除 manifest/schema）"""
    if not _NETWORK_LIBRARY_ROOT.exists():
        return []
    excluded = {"manifest.json", "network_asset_schema.yaml", "README.md"}
    return sorted([
        p for p in _NETWORK_LIBRARY_ROOT.glob("*.json")
        if p.name not in excluded
    ])


def _load_network(network_id: str) -> Dict[str, Any]:
    """加载单个网络资产文件"""
    path = _NETWORK_LIBRARY_ROOT / f"{network_id}.json"
    if not path.exists():
        raise HTTPException(status_code=404, detail=f"network {network_id} not found")
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def _validate_network_payload(data: Dict[str, Any]) -> str:
    """校验网络资产 payload 的必填字段，返回 network_id"""
    for key in ["id", "name", "description", "version", "hyperparameters",
                "input_signature", "output_signature", "network_graph"]:
        if key not in data:
            raise HTTPException(status_code=400, detail=f"missing required field: {key}")
    return data["id"]


def _save_network(network_id: str, data: Dict[str, Any]) -> Path:
    """保存/覆盖网络资产到 data_lake"""
    _NETWORK_LIBRARY_ROOT.mkdir(parents=True, exist_ok=True)
    data.setdefault("last_updated", time.strftime("%Y-%m-%d"))
    data["id"] = network_id  # 保证 id 与文件名一致
    path = _NETWORK_LIBRARY_ROOT / f"{network_id}.json"
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    return path


def _rebuild_model_from_network(network: Dict[str, Any]) -> str:
    """根据网络资产中的 hyperparameters 重新构建活动模型"""
    hp = network.get("hyperparameters", {})
    num_actions = int(hp.get("num_actions", 100))
    state_dim = int(hp.get("state_dim", 48))
    history_len = int(hp.get("history_len", 10))
    hidden_dim = int(hp.get("hidden_dim", 256))

    _ensure_initialized()
    new_model = SanguoshaActorCritic(
        num_actions=num_actions,
        state_dim=state_dim,
        history_len=history_len,
        hidden_dim=hidden_dim,
    )
    new_model.eval()
    _STATE["model"] = new_model
    _STATE["trainer"] = SanguoshaTrainer(
        _STATE["env"], new_model,
        algorithm=network.get("algorithm", "ppo"),
        history_len=history_len,
    )
    _STATE["history"] = deque(maxlen=history_len)
    _STATE["active_network_id"] = network["id"]
    _STATE["obs"], _STATE["info"] = _STATE["env"].reset()
    _STATE["step_count"] = 0
    _STATE["last_action_probs"] = None
    _STATE["last_value"] = None
    return f"已应用 {network['id']} (num_actions={num_actions}, hidden_dim={hidden_dim})"


def _ensure_initialized():
    """延迟初始化，避免导入时创建沉重对象"""
    if _STATE["env"] is None:
        _STATE["env"] = SanguoshaEnv()
        _STATE["model"] = SanguoshaActorCritic(
            num_actions=100, state_dim=48, history_len=10, hidden_dim=256
        )
        _STATE["model"].eval()  # 评估模式
        _STATE["trainer"] = SanguoshaTrainer(
            _STATE["env"], _STATE["model"], algorithm="ppo", history_len=10
        )
        print("[NeuralVis] 环境与模型已初始化")


# --------- 网络架构元数据 ---------
def get_network_architecture() -> Dict[str, Any]:
    """生成网络架构的结构化描述（用于前端绘制）"""
    _ensure_initialized()

    encoder = _STATE["model"].state_encoder
    temporal = _STATE["model"].temporal_model

    def count_params(module: torch.nn.Module) -> int:
        return sum(p.numel() for p in module.parameters())

    # 计算各分支输出维度
    hidden_dim_quarter = encoder.scalar_fc[0].out_features  # 64

    branches = [
        {
            "id": "branch_scalar",
            "name": "标量分支 (Scalar Branch)",
            "description": "处理玩家血量/手牌数/技能标记/全局回合状态",
            "inputs": [
                {"name": "player1_scalar", "shape": [6], "description": "玩家1血量、手牌比例、技能标记"},
                {"name": "player2_scalar", "shape": [6], "description": "对手血量、手牌数等"},
                {"name": "global_state", "shape": [5], "description": "当前玩家/回合数/牌堆剩余"},
                {"name": "player2_hand_count", "shape": [1], "description": "对手手牌数标量"},
            ],
            "layers": [
                {"type": "Linear", "in_features": 18, "out_features": hidden_dim_quarter},
                {"type": "ReLU"},
                {"type": "LayerNorm", "features": hidden_dim_quarter},
            ],
            "output_shape": [hidden_dim_quarter],
            "params": count_params(encoder.scalar_fc),
        },
        {
            "id": "branch_hand",
            "name": "手牌分支 (Hand Branch)",
            "description": "处理玩家手牌列表 - 每张牌编码 [类型,花色,点数]",
            "inputs": [
                {"name": "player1_hand", "shape": [10, 3], "description": "最多10张手牌,每张3维"},
                {"name": "player1_hand_mask", "shape": [10], "description": "0/1掩码标记有效牌位置"},
            ],
            "embeddings": [
                {"name": "type_emb", "shape": [30, 32], "description": "卡牌类型嵌入"},
                {"name": "suit_emb", "shape": [6, 32], "description": "花色嵌入 (黑桃/红桃/梅花/方块)"},
                {"name": "rank_emb", "shape": [15, 32], "description": "点数嵌入 (1-13)"},
            ],
            "layers": [
                {"type": "Concat(3 embeddings)", "in_features": 96, "out_features": 96},
                {"type": "Linear + ReLU + LN", "in_features": 96, "out_features": hidden_dim_quarter},
                {"type": "MaskedAverage", "description": "按手牌掩码加权平均"},
            ],
            "output_shape": [hidden_dim_quarter],
            "params": count_params(encoder.type_embedding)
                      + count_params(encoder.suit_embedding)
                      + count_params(encoder.rank_embedding)
                      + count_params(encoder.card_fusion),
        },
        {
            "id": "branch_equipment",
            "name": "装备分支 (Equipment Branch)",
            "description": "处理玩家装备 - 武器/防具/防御马/-1马",
            "inputs": [
                {"name": "player1_equipment", "shape": [4, 3], "description": "4个装备槽位,每槽3维"},
                {"name": "player1_equipment_mask", "shape": [4], "description": "0/1掩码标记是否装备"},
            ],
            "note": "共享手牌分支的嵌入权重 (type/suit/rank embedding)",
            "layers": [
                {"type": "SharedEmbedding(30,6,15)", "emb_dim": 32},
                {"type": "Linear + ReLU + LN", "out_features": hidden_dim_quarter},
                {"type": "MaskedAverage"},
            ],
            "output_shape": [hidden_dim_quarter],
            "params": count_params(encoder.card_fusion),  # 与手牌共享嵌入,只算融合层
        },
        {
            "id": "branch_opponent",
            "name": "对手分支 (Opponent Branch)",
            "description": "不完全信息下的对手装备可见性 (只能看到有无, 不能看到具体牌)",
            "inputs": [
                {"name": "player2_equipment_mask", "shape": [4], "description": "对手4个装备槽位的存在性"},
            ],
            "layers": [
                {"type": "Linear", "in_features": 4, "out_features": hidden_dim_quarter},
                {"type": "ReLU"},
                {"type": "LayerNorm", "features": hidden_dim_quarter},
            ],
            "output_shape": [hidden_dim_quarter],
            "params": count_params(encoder.opp_fc),
        },
    ]

    fusion_dim = hidden_dim_quarter * 4
    temporal_dim = 256

    return {
        "model_name": "SanguoshaActorCritic (AlphaStar-style Multi-branch)",
        "total_params": count_params(_STATE["model"]),
        "input_type": "structured dict (9 keys)",
        "num_actions": 100,
        "history_len": 10,
        "branches": branches,
        "fusion_section": {
            "description": "四分支特征拼接 + LSTM/Transformer 时序特征拼接",
            "input_shape": [fusion_dim + temporal_dim],
            "layers": [
                {"type": "Linear", "in_features": fusion_dim + temporal_dim, "out_features": 256},
                {"type": "ReLU"},
                {"type": "LayerNorm", "features": 256},
            ],
            "params": count_params(_STATE["model"].feature_fusion),
        },
        "temporal_section": {
            "description": "时序建模 - LSTM 短期记忆 + Transformer 长期记忆 + Multi-Head Attention",
            "input_shape": [10, 48],  # 历史长度10, 每步48维扁平状态
            "components": [
                {
                    "name": "PositionalEncoding",
                    "in_features": 48,
                    "max_len": 10,
                    "description": "为历史序列注入时序位置信息",
                },
                {
                    "name": "LSTM",
                    "input_size": 48,
                    "hidden_size": 128,
                    "num_layers": 1,
                    "description": "提取短期时序依赖",
                },
                {
                    "name": "TransformerEncoder",
                    "d_model": 48,
                    "nhead": 4,
                    "num_layers": 2,
                    "dim_feedforward": 256,
                    "description": "提取长期时序依赖",
                },
                {
                    "name": "MultiheadAttention",
                    "embed_dim": 48,
                    "num_heads": 4,
                    "description": "当前状态关注关键历史时刻",
                },
            ],
            "output_shape": [256],
            "params": count_params(temporal),
        },
        "actor_head": {
            "description": "策略头 - 输出每个动作的概率",
            "layers": [
                {"type": "Linear", "in_features": 256, "out_features": 256},
                {"type": "ReLU"},
                {"type": "Linear", "in_features": 256, "out_features": 100},
                {"type": "Softmax", "dim": -1},
            ],
            "params": count_params(_STATE["model"].actor_head),
        },
        "critic_head": {
            "description": "价值头 - 估计当前状态期望回报",
            "layers": [
                {"type": "Linear", "in_features": 256, "out_features": 256},
                {"type": "ReLU"},
                {"type": "Linear", "in_features": 256, "out_features": 1},
            ],
            "params": count_params(_STATE["model"].critic_head),
        },
        "data_flow": [
            {"from": "structured obs (dict)", "to": "4 branches"},
            {"from": "4 branches", "to": "concat -> fusion (256)"},
            {"from": "history (10, 48)", "to": "temporal model -> 256"},
            {"from": "fusion(256) + temporal(256)", "to": "feature_fusion -> 256"},
            {"from": "feature_fusion(256)", "to": "actor_head -> action_probs(100)"},
            {"from": "feature_fusion(256)", "to": "critic_head -> value(1)"},
        ],
    }


# --------- 推理辅助 ---------
def _serialize_obs(obs: Any) -> Dict:
    """将观测转换为 JSON 可序列化格式"""
    if isinstance(obs, dict):
        result = {}
        for k, v in obs.items():
            if isinstance(v, np.ndarray):
                result[k] = v.tolist()
            elif isinstance(v, (int, float, str, list)):
                result[k] = v
            else:
                result[k] = str(v)
        return result
    elif isinstance(obs, np.ndarray):
        return obs.tolist()
    return obs


def _flatten_obs_for_history(obs_dict: Dict) -> np.ndarray:
    """将字典观测扁平化为48维向量，用于历史序列"""
    if isinstance(obs_dict, dict):
        parts = []
        for key in ["player1_scalar", "player2_scalar", "global_state", "player2_hand_count"]:
            if key in obs_dict:
                val = obs_dict[key]
                if isinstance(val, np.ndarray):
                    parts.append(val.flatten())
                else:
                    parts.append(np.array(val).flatten())
        flat = np.concatenate(parts) if parts else np.zeros(48, dtype=np.float32)
        if flat.shape[0] < 48:
            flat = np.pad(flat, (0, 48 - flat.shape[0]))
        return flat[:48].astype(np.float32)
    return obs_dict


def _collect_activations(obs: Dict, history_tensor: torch.Tensor) -> Dict:
    """收集各分支的激活值/特征向量 (用于可视化)"""
    model = _STATE["model"]
    encoder = model.state_encoder
    activations = {}

    # 1. 收集各分支的特征
    with torch.no_grad():
        # 标量分支
        p1_scalar = torch.FloatTensor(np.array(obs["player1_scalar"])).unsqueeze(0)
        p2_scalar = torch.FloatTensor(np.array(obs["player2_scalar"])).unsqueeze(0)
        g_state = torch.FloatTensor(np.array(obs["global_state"])).unsqueeze(0)
        p2_hc = torch.FloatTensor(np.array(obs["player2_hand_count"])).unsqueeze(0)
        scalar_concat = torch.cat([p1_scalar, p2_scalar, g_state, p2_hc], dim=-1)
        scalar_feat = encoder.scalar_fc(scalar_concat)
        activations["branch_scalar"] = scalar_feat[0].tolist()

        # 手牌分支
        p1_hand = torch.LongTensor(np.array(obs["player1_hand"])).unsqueeze(0)
        p1_hand_mask = torch.FloatTensor(np.array(obs["player1_hand_mask"])).unsqueeze(0)
        type_emb = encoder.type_embedding(p1_hand[:, :, 0])
        suit_emb = encoder.suit_embedding(p1_hand[:, :, 1])
        rank_emb = encoder.rank_embedding(p1_hand[:, :, 2])
        combined_emb = torch.cat([type_emb, suit_emb, rank_emb], dim=-1)
        seq_len = combined_emb.size(1)
        combined_flat = combined_emb.reshape(1 * seq_len, -1)
        card_feat_flat = encoder.card_fusion(combined_flat)
        card_features = card_feat_flat.reshape(1, seq_len, -1)
        mask_expanded = p1_hand_mask.float().unsqueeze(-1)
        total = mask_expanded.sum(dim=1, keepdim=True) + 1e-8
        hand_feat = (card_features * mask_expanded).sum(dim=1) / total.squeeze(1)
        activations["branch_hand"] = hand_feat[0].tolist()
        activations["hand_per_card"] = card_features[0].tolist()
        activations["hand_mask"] = p1_hand_mask[0].tolist()

        # 装备分支
        p1_equip = torch.LongTensor(np.array(obs["player1_equipment"])).unsqueeze(0)
        p1_equip_mask = torch.FloatTensor(np.array(obs["player1_equipment_mask"])).unsqueeze(0)
        eq_type = encoder.type_embedding(p1_equip[:, :, 0])
        eq_suit = encoder.suit_embedding(p1_equip[:, :, 1])
        eq_rank = encoder.rank_embedding(p1_equip[:, :, 2])
        eq_combined = torch.cat([eq_type, eq_suit, eq_rank], dim=-1)
        eq_len = eq_combined.size(1)
        eq_flat = eq_combined.reshape(1 * eq_len, -1)
        eq_feat_flat = encoder.card_fusion(eq_flat)
        eq_features = eq_feat_flat.reshape(1, eq_len, -1)
        eq_mask_expanded = p1_equip_mask.float().unsqueeze(-1)
        eq_total = eq_mask_expanded.sum(dim=1, keepdim=True) + 1e-8
        equip_feat = (eq_features * eq_mask_expanded).sum(dim=1) / eq_total.squeeze(1)
        activations["branch_equipment"] = equip_feat[0].tolist()
        activations["equipment_per_slot"] = eq_features[0].tolist()
        activations["equipment_mask"] = p1_equip_mask[0].tolist()

        # 对手分支
        p2_equip_mask = torch.FloatTensor(np.array(obs["player2_equipment_mask"])).unsqueeze(0)
        opp_feat = encoder.opp_fc(p2_equip_mask.float())
        activations["branch_opponent"] = opp_feat[0].tolist()

        # 完整融合
        combined = torch.cat([scalar_feat, hand_feat, equip_feat, opp_feat], dim=-1)
        activations["fusion_input"] = combined[0].tolist()

        # 时序
        if history_tensor is not None and history_tensor.size(1) > 0:
            with torch.no_grad():
                temporal_feat = model.temporal_model(history_tensor)
            activations["temporal"] = temporal_feat[0].tolist()
        else:
            activations["temporal"] = [0.0] * 256

        # 最终特征融合
        final_input = torch.cat([combined, torch.FloatTensor([activations["temporal"]])], dim=-1)
        final_feat = model.feature_fusion(final_input)
        activations["final_feature"] = final_feat[0].tolist()

    return activations


# --------- API 数据模型 ---------
class ActionRequest(BaseModel):
    action: Optional[int] = None  # 若为空,则让AI选择


# --------- API 路由 ---------
@app.get("/api/health")
async def health():
    return {"status": "ok", "service": "sanguosha-neural-vis", "port": 5130}


@app.get("/api/network/architecture")
async def get_architecture():
    return {"architecture": get_network_architecture()}


@app.post("/api/game/reset")
async def reset_game():
    _ensure_initialized()
    _STATE["obs"], _STATE["info"] = _STATE["env"].reset()
    _STATE["history"].clear()
    flat = _flatten_obs_for_history(_STATE["obs"])
    for _ in range(10):
        _STATE["history"].append(flat.copy())
    _STATE["step_count"] = 0
    _STATE["last_action_probs"] = None
    _STATE["last_value"] = None
    return {
        "obs": _serialize_obs(_STATE["obs"]),
        "info": _STATE["info"],
        "step_count": 0,
    }


@app.post("/api/game/step")
async def step_game(req: ActionRequest):
    _ensure_initialized()
    if _STATE["obs"] is None:
        await reset_game()

    model = _STATE["model"]
    env = _STATE["env"]
    trainer = _STATE["trainer"]

    # 构建历史
    history = torch.tensor(list(_STATE["history"]), dtype=torch.float32).unsqueeze(0)

    # 模型推理
    action_mask = trainer._get_action_mask(_STATE["info"])
    with torch.no_grad():
        action_probs_tensor, value_tensor = model(
            _STATE["obs"], history, action_mask.unsqueeze(0)
        )

    # 选择动作
    if req.action is not None and 0 <= req.action < 100 and action_mask[req.action] > 0:
        chosen_action = req.action
    else:
        chosen_action = int(torch.argmax(action_probs_tensor, dim=-1).item())

    # 执行一步
    next_obs, reward, terminated, truncated, next_info = env.step(chosen_action)

    # 更新历史
    _STATE["history"].append(_flatten_obs_for_history(next_obs))
    _STATE["obs"] = next_obs
    _STATE["info"] = next_info
    _STATE["step_count"] += 1
    _STATE["last_action_probs"] = action_probs_tensor[0].tolist()
    _STATE["last_value"] = float(value_tensor.item())

    return {
        "obs": _serialize_obs(next_obs),
        "info": next_info,
        "reward": float(reward),
        "terminated": terminated,
        "truncated": truncated,
        "chosen_action": chosen_action,
        "action_probs": _STATE["last_action_probs"],
        "value": _STATE["last_value"],
        "action_mask": action_mask.tolist(),
        "step_count": _STATE["step_count"],
    }


@app.post("/api/network/inference")
async def run_inference():
    """对当前状态执行一次完整推理，返回所有可视化数据"""
    _ensure_initialized()
    if _STATE["obs"] is None:
        await reset_game()

    model = _STATE["model"]
    trainer = _STATE["trainer"]
    history = torch.tensor(list(_STATE["history"]), dtype=torch.float32).unsqueeze(0)
    action_mask = trainer._get_action_mask(_STATE["info"])

    with torch.no_grad():
        action_probs_tensor, value_tensor = model(
            _STATE["obs"], history, action_mask.unsqueeze(0)
        )

    activations = _collect_activations(_STATE["obs"], history)

    # 分析 top-k 动作
    probs = action_probs_tensor[0].numpy()
    top_indices = np.argsort(probs)[-10:][::-1]
    top_actions = [
        {"action_id": int(i), "probability": float(probs[i]), "valid": bool(action_mask[i] > 0)}
        for i in top_indices
    ]

    return {
        "obs": _serialize_obs(_STATE["obs"]),
        "info": _STATE["info"],
        "action_probs": probs.tolist(),
        "value": float(value_tensor.item()),
        "action_mask": action_mask.tolist(),
        "top_actions": top_actions,
        "activations": activations,
        "history_length": len(_STATE["history"]),
        "step_count": _STATE["step_count"],
    }


@app.get("/api/network/embedding/{kind}")
async def get_embedding(kind: str):
    """返回指定嵌入的向量 (供t-SNE/降维可视化)"""
    _ensure_initialized()
    encoder = _STATE["model"].state_encoder
    valid = {"type", "suit", "rank"}
    if kind not in valid:
        raise HTTPException(status_code=400, detail=f"kind must be in {valid}")
    emb_map = {"type": encoder.type_embedding, "suit": encoder.suit_embedding, "rank": encoder.rank_embedding}
    with torch.no_grad():
        vectors = emb_map[kind].weight.numpy().tolist()
    labels = []
    if kind == "type":
        labels = [f"类型_{i}" for i in range(len(vectors))]
    elif kind == "suit":
        labels = ["黑桃", "红桃", "梅花", "方块", "无花色", "空"]
        labels = labels[: len(vectors)]
    else:
        labels = [f"点数_{i}" for i in range(len(vectors))]
    return {"kind": kind, "vectors": vectors, "labels": labels}


@app.get("/api/game/card-metadata")
async def get_card_metadata():
    """返回卡牌元数据 (用于前端展示卡牌含义)"""
    _ensure_initialized()
    return {
        "card_types": {
            0: "杀", 1: "闪", 2: "桃", 3: "酒", 4: "无中生有",
            5: "顺手牵羊", 6: "过河拆桥", 7: "决斗", 8: "南蛮入侵",
            9: "万箭齐发", 10: "无懈可击", 11: "乐不思蜀", 12: "兵粮寸断",
        },
        "suits": {0: "黑桃", 1: "红桃", 2: "梅花", 3: "方块", 4: "无花色"},
        "ranks": {i: (str(i) if 1 < i <= 10 else ("A" if i == 1 else ("J" if i == 11 else ("Q" if i == 12 else "K")))) for i in range(1, 14)},
        "equipment_slots": {0: "武器", 1: "防具", 2: "+1马(防御)", 3: "-1马(进攻)"},
    }


# ================== 网络库 API (data_lake/network_library) ==================

@app.get("/api/network-library")
async def list_networks():
    """列出网络库中所有网络资产（摘要信息）"""
    files = _list_network_files()
    result = []
    for path in files:
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            result.append({
                "id": data.get("id", path.stem),
                "name": data.get("name", path.stem),
                "version": data.get("version", "?"),
                "description": data.get("description", ""),
                "domain": data.get("domain", "unknown"),
                "algorithm": data.get("algorithm", "unknown"),
                "tags": data.get("tags", []),
                "status": data.get("status", "active"),
                "param_count": data.get("param_count"),
                "hyperparameters": data.get("hyperparameters", {}),
            })
        except Exception as e:
            result.append({"id": path.stem, "error": f"failed to parse: {e}"})
    return {
        "count": len(result),
        "active_network_id": _STATE.get("active_network_id"),
        "networks": result,
    }


@app.get("/api/network-library/{network_id}")
async def get_network(network_id: str):
    """读取单个网络资产的完整结构"""
    data = _load_network(network_id)
    return {"network": data}


@app.post("/api/network-library")
async def create_or_update_network(payload: Dict[str, Any]):
    """保存/覆盖网络资产到 data_lake/network_library。
    若 payload 中 id 已存在，则覆盖原文件。
    """
    network_id = _validate_network_payload(payload)
    path = _save_network(network_id, payload)
    return {
        "success": True,
        "network_id": network_id,
        "path": str(path),
        "message": f"网络资产 {network_id} 已保存",
    }


@app.delete("/api/network-library/{network_id}")
async def delete_network(network_id: str):
    """删除指定网络资产（同时确保不能删除当前活动网络）"""
    path = _NETWORK_LIBRARY_ROOT / f"{network_id}.json"
    if not path.exists():
        raise HTTPException(status_code=404, detail=f"network {network_id} not found")
    if _STATE.get("active_network_id") == network_id:
        raise HTTPException(
            status_code=400,
            detail=f"cannot delete active network {network_id}; 先应用其他网络再删除"
        )
    path.unlink()
    return {"success": True, "message": f"已删除 {network_id}"}


@app.post("/api/network-library/{network_id}/apply")
async def apply_network(network_id: str):
    """将 data_lake 中的网络资产应用为 5130 服务的活动模型：
    - 根据 hyperparameters 重新构建 SanguoshaActorCritic
    - 重置对局状态与历史序列
    """
    network = _load_network(network_id)
    message = _rebuild_model_from_network(network)
    return {
        "success": True,
        "active_network_id": network_id,
        "message": message,
        "hyperparameters": network.get("hyperparameters"),
    }


@app.get("/api/network-library/meta/schema")
async def get_network_schema():
    """返回 network_asset_schema.yaml 的内容，方便前端了解字段结构"""
    schema_path = _NETWORK_LIBRARY_ROOT / "network_asset_schema.yaml"
    alt_path = _NETWORK_LIBRARY_ROOT.parent / "structure" / "network_asset_schema.yaml"
    for p in (schema_path, alt_path):
        if p.exists():
            with open(p, "r", encoding="utf-8") as f:
                content = f.read()
            return {"schema_path": str(p), "content": content}
    raise HTTPException(status_code=404, detail="schema file not found")


@app.get("/api/network-library/meta/manifest")
async def get_network_manifest():
    """返回 network_library/manifest.json 的内容"""
    manifest_path = _NETWORK_LIBRARY_ROOT / "manifest.json"
    if not manifest_path.exists():
        raise HTTPException(status_code=404, detail="manifest not found")
    with open(manifest_path, "r", encoding="utf-8") as f:
        return json.load(f)


# ============ 训练 API ============
class TrainingConfigRequest(BaseModel):
    network_id: str = "sanguosha_alphastar_actor_critic"
    total_steps: int = 2000
    learning_rate: float = 3e-4
    gamma: float = 0.99
    entropy_coef: float = 0.01
    value_coef: float = 0.5
    batch_size: int = 128
    save_interval: int = 200
    log_interval: int = 20


@app.get("/api/training/status")
async def get_training_status():
    """获取当前训练状态与进度"""
    elapsed = time.time() - _TRAINING_STATE["start_time"] if _TRAINING_STATE["start_time"] > 0 else 0.0
    with _TRAINING_STATE["lock"] if _TRAINING_STATE["lock"] else __import__("contextlib").nullcontext():
        return {
            "running": _TRAINING_STATE["running"],
            "current_step": _TRAINING_STATE["current_step"],
            "total_steps": _TRAINING_STATE["total_steps"],
            "progress": _TRAINING_STATE["progress"],
            "elapsed_sec": round(elapsed, 1),
            "steps_per_sec": round(_TRAINING_STATE["current_step"] / max(elapsed, 0.001), 2) if elapsed > 0 else 0,
            "config": _TRAINING_STATE["config"],
            "metrics": _TRAINING_STATE["metrics"],
            "history_points": len(_TRAINING_STATE["step_history"]),
            "log_lines": len(_TRAINING_STATE["recent_logs"]),
            "active_network_id": _STATE["active_network_id"],
        }


@app.get("/api/training/history")
async def get_training_history(limit: int = 100):
    """获取训练历史数据（用于绘制曲线）"""
    with _TRAINING_STATE["lock"] if _TRAINING_STATE["lock"] else __import__("contextlib").nullcontext():
        data = _TRAINING_STATE["step_history"][-limit:]
        logs = list(_TRAINING_STATE["recent_logs"])[-50:]
    return {"history": data, "logs": logs, "total_points": len(_TRAINING_STATE["step_history"])}


@app.post("/api/training/start")
async def start_training(config: TrainingConfigRequest):
    """启动无头模式训练

    流程：
    1. 从 data_lake 加载指定 network_id 的网络资产
    2. 按超参数重建 PyTorch 模型
    3. 在后台线程中启动 PPO 风格训练
    4. 每 save_interval 步将训练状态写回网络资产
    """
    if _TRAINING_STATE["running"]:
        return {"success": False, "message": "已有训练在运行中，请先停止"}

    # 校验网络资产是否存在
    net_path = _NETWORK_LIBRARY_ROOT / f"{config.network_id}.json"
    if not net_path.exists():
        raise HTTPException(status_code=404, detail=f"network {config.network_id} not found in data_lake")

    _ensure_initialized()
    _ensure_training_lock()

    _TRAINING_STATE["running"] = True
    _TRAINING_STATE["should_stop"] = False
    _TRAINING_STATE["progress"] = 0.0
    _TRAINING_STATE["current_step"] = 0
    _TRAINING_STATE["total_steps"] = config.total_steps
    _TRAINING_STATE["step_history"] = []
    _TRAINING_STATE["recent_logs"].clear()
    _TRAINING_STATE["metrics"] = {
        "last_loss": 0.0,
        "last_reward": 0.0,
        "episode_count": 0,
        "best_reward": -float("inf"),
        "avg_reward_100": 0.0,
    }
    _TRAINING_STATE["config"] = config.dict()

    import threading
    t = threading.Thread(target=_training_thread, args=(config.dict(),), daemon=True)
    _TRAINING_STATE["thread"] = t
    t.start()

    return {
        "success": True,
        "message": f"已启动训练: {config.network_id}, {config.total_steps} 步, lr={config.learning_rate}",
        "config": config.dict(),
    }


@app.post("/api/training/stop")
async def stop_training():
    """停止当前训练"""
    if not _TRAINING_STATE["running"]:
        return {"success": True, "message": "当前无运行中的训练"}
    _TRAINING_STATE["should_stop"] = True
    return {"success": True, "message": "已发送停止信号，训练将在当前 step 后终止..."}


@app.get("/api/training/default-config")
async def get_training_default_config():
    """返回默认训练配置，供前端填充表单"""
    _ensure_initialized()
    return {
        "network_id": _STATE["active_network_id"],
        "total_steps": 2000,
        "learning_rate": 3e-4,
        "gamma": 0.99,
        "entropy_coef": 0.01,
        "value_coef": 0.5,
        "batch_size": 128,
        "save_interval": 200,
        "log_interval": 20,
        "available_networks": [p.stem for p in _list_network_files()],
    }


# --------- 前端页面 ---------
@app.get("/", response_class=HTMLResponse)
async def root():
    """前端主页 - 展示网络架构与实时决策"""
    index_file = Path(__file__).parent / "neural_vis_frontend" / "index.html"
    if index_file.exists():
        with open(index_file, "r", encoding="utf-8") as f:
            return f.read()
    return HTMLResponse("<h1>Neural Visualization - 前端未找到，请访问 /docs 查看 API</h1>")


@app.get("/{filename:path}")
async def serve_static(filename: str):
    """提供静态文件服务"""
    safe_path = (Path(__file__).parent / "neural_vis_frontend" / filename).resolve()
    frontend_root = (Path(__file__).parent / "neural_vis_frontend").resolve()
    if not str(safe_path).startswith(str(frontend_root)):
        raise HTTPException(status_code=403, detail="path forbidden")
    if safe_path.exists() and safe_path.is_file():
        return FileResponse(str(safe_path))
    raise HTTPException(status_code=404, detail="not found")


def main():
    import uvicorn

    print("=" * 60)
    print("三国杀神经网络可视化服务器 - 端口 5130")
    print("=" * 60)
    print("  主页:     http://localhost:5130/")
    print("  API文档:  http://localhost:5130/docs")
    print("=" * 60)

    _ensure_initialized()
    uvicorn.run(app, host="0.0.0.0", port=5130, log_level="info")


if __name__ == "__main__":
    main()
