/* =========================================
   三国杀神经网络可视化 - 前端逻辑
   AlphaStar 风格多分支网络
   ========================================= */

const API_BASE = "";  // 同域
const AUTO_INTERVAL_MS = 1500;

// 全局状态
let state = {
    architecture: null,
    currentInference: null,
    cardMetadata: null,
    autoMode: false,
    autoTimer: null,
    chosenAction: null,
    // 网络库状态
    networks: [],
    activeNetworkId: null,
    currentEditNetwork: null,
};

// ============ 工具函数 ============
function setStatus(cls, msg) {
    const el = document.getElementById("status-indicator");
    el.className = "status-indicator " + cls;
    el.title = msg || "";
}

async function apiGet(path) {
    const res = await fetch(API_BASE + path);
    if (!res.ok) throw new Error("HTTP " + res.status);
    return await res.json();
}

async function apiPost(path, body = {}) {
    const res = await fetch(API_BASE + path, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
    });
    if (!res.ok) throw new Error("HTTP " + res.status);
    return await res.json();
}

function formatNumber(n, digits = 4) {
    if (n === null || n === undefined || isNaN(n)) return "--";
    return Number(n).toFixed(digits);
}

function formatParams(n) {
    if (!n) return "--";
    if (n >= 1e6) return (n / 1e6).toFixed(2) + "M";
    if (n >= 1e3) return (n / 1e3).toFixed(1) + "K";
    return String(n);
}

// ============ 网络架构图渲染 ============
function renderArchitecture(arch) {
    const container = document.getElementById("architecture-diagram");
    if (!arch) {
        container.innerHTML = '<div class="loading"><span class="loading-spinner"></span>加载网络架构...</div>';
        return;
    }

    // 构建分层结构
    const branches = arch.branches || [];
    const fusion = arch.fusion_section;
    const temporal = arch.temporal_section;
    const actor = arch.actor_head;
    const critic = arch.critic_head;

    // 更新页脚
    const paramEl = document.getElementById("param-count");
    if (paramEl) paramEl.textContent = formatParams(arch.total_params);

    let html = "";

    // ===== 第1层：输入层 =====
    html += `
    <div class="arch-layer">
        <div class="arch-layer-title">① 输入层 (Structured Observation)</div>
        <div class="arch-node-row">
    `;
    const inputsMap = {
        player1_scalar: { shape: "[6]", desc: "玩家1血量等" },
        player1_hand: { shape: "[10,3]", desc: "玩家1手牌(类型/花色/点数)" },
        player1_hand_mask: { shape: "[10]", desc: "手牌掩码" },
        player1_equipment: { shape: "[4,3]", desc: "玩家1装备" },
        player1_equipment_mask: { shape: "[4]", desc: "装备掩码" },
        player2_scalar: { shape: "[6]", desc: "对手状态" },
        player2_hand_count: { shape: "[1]", desc: "对手手牌数" },
        player2_equipment_mask: { shape: "[4]", desc: "对手装备掩码" },
        global_state: { shape: "[5]", desc: "回合数/牌堆" },
    };
    for (const key of Object.keys(inputsMap)) {
        const info = inputsMap[key];
        html += `
            <div class="arch-node input" title="${info.desc}">
                <div class="arch-node-name">${key}</div>
                <div class="arch-node-shape">${info.shape}</div>
            </div>
        `;
    }
    html += `</div></div>`;

    // 连接线
    html += `<div class="arch-connector"></div>`;

    // ===== 第2层：四分支 =====
    html += `<div class="arch-layer"><div class="arch-layer-title">② 多分支编码 (AlphaStar Style)</div><div class="arch-node-row">`;
    for (const b of branches) {
        const cls = b.id.replace("_", "-");
        const params = formatParams(b.params);
        html += `
            <div class="arch-node branch-${cls}" title="${b.description}">
                <div class="arch-node-name">${b.name}</div>
                <div class="arch-node-shape">→ ${b.output_shape}</div>
                <div class="arch-node-params">${params} params</div>
            </div>
        `;
    }
    html += `</div></div>`;

    // 连接线 + 时序模块
    html += `<div class="arch-connector"></div>`;

    html += `<div class="arch-layer">
        <div class="arch-layer-title">③ 特征融合 + 时序建模</div>
        <div class="arch-node-row">
            <div class="arch-node fusion" title="${fusion.description}">
                <div class="arch-node-name">Fusion (Concat)</div>
                <div class="arch-node-shape">${fusion.input_shape}</div>
                <div class="arch-node-params">${formatParams(fusion.params)} params</div>
            </div>
            <div class="arch-node temporal" title="${temporal.description}">
                <div class="arch-node-name">Temporal (LSTM+Transformer)</div>
                <div class="arch-node-shape">History(${arch.history_len}, 48) → ${temporal.output_shape}</div>
                <div class="arch-node-params">${formatParams(temporal.params)} params</div>
            </div>
        </div>
    </div>`;

    html += `<div class="arch-connector"></div>`;

    // ===== 第3层：Actor-Critic 输出 =====
    html += `<div class="arch-layer">
        <div class="arch-layer-title">④ 策略头 & 价值头 (Actor-Critic)</div>
        <div class="arch-node-row">
            <div class="arch-node output-actor" title="${actor.description}">
                <div class="arch-node-name">π Actor (策略)</div>
                <div class="arch-node-shape">→ ${arch.num_actions} 动作概率</div>
                <div class="arch-node-params">${formatParams(actor.params)} params</div>
            </div>
            <div class="arch-node output-critic" title="${critic.description}">
                <div class="arch-node-name">V Critic (价值)</div>
                <div class="arch-node-shape">→ 1 标量状态价值</div>
                <div class="arch-node-params">${formatParams(critic.params)} params</div>
            </div>
        </div>
    </div>`;

    // 架构元数据
    html += `<div class="arch-layer" style="margin-top: 24px;">
        <div style="font-size: 11px; color: var(--text-muted); font-family: monospace;">
            模型: <strong style="color: var(--text-secondary);">${arch.model_name}</strong> | 
            输入类型: <strong style="color: var(--text-secondary);">${arch.input_type}</strong> | 
            总参数: <strong style="color: var(--accent-primary);">${formatParams(arch.total_params)}</strong>
        </div>
    </div>`;

    container.innerHTML = html;
}

// ============ 游戏状态渲染 ============
function renderGameState(inference) {
    const container = document.getElementById("state-display");
    if (!inference || !inference.obs) {
        container.innerHTML = '<div class="loading">暂无游戏状态，请先执行推理...</div>';
        return;
    }

    const obs = inference.obs;
    const info = inference.info || {};

    // 玩家1标量状态
    let p1Scalar = "";
    if (Array.isArray(obs.player1_scalar)) {
        obs.player1_scalar.forEach((v, i) => {
            p1Scalar += `<div class="state-row">
                <span class="state-label">特征[${i}]</span>
                <span class="state-value">${formatNumber(v, 3)}</span>
            </div>`;
        });
    }

    // 对手标量状态
    let p2Scalar = "";
    if (Array.isArray(obs.player2_scalar)) {
        obs.player2_scalar.forEach((v, i) => {
            p2Scalar += `<div class="state-row">
                <span class="state-label">特征[${i}]</span>
                <span class="state-value">${formatNumber(v, 3)}</span>
            </div>`;
        });
    }

    // 全局状态
    let globalState = "";
    if (Array.isArray(obs.global_state)) {
        obs.global_state.forEach((v, i) => {
            globalState += `<div class="state-row">
                <span class="state-label">全局[${i}]</span>
                <span class="state-value">${formatNumber(v, 2)}</span>
            </div>`;
        });
    }

    // 对手手牌数
    let oppHand = "";
    if (Array.isArray(obs.player2_hand_count)) {
        oppHand = `<div class="state-row">
            <span class="state-label">对手手牌数</span>
            <span class="state-value">${obs.player2_hand_count[0]}</span>
        </div>`;
    }

    container.innerHTML = `
        <div class="state-section">
            <div class="state-section-title">▶ 玩家1 标量状态</div>
            ${p1Scalar}
        </div>
        <div class="state-section">
            <div class="state-section-title">▶ 对手标量状态</div>
            ${p2Scalar}
        </div>
        <div class="state-section">
            <div class="state-section-title">▶ 全局回合状态</div>
            ${globalState}
            ${oppHand}
        </div>
        <div class="state-section">
            <div class="state-section-title">▶ 步数 & 历史</div>
            <div class="state-row">
                <span class="state-label">已走步数</span>
                <span class="state-value">${inference.step_count ?? 0}</span>
            </div>
            <div class="state-row">
                <span class="state-label">历史长度</span>
                <span class="state-value">${inference.history_length ?? 0}</span>
            </div>
        </div>
    `;
}

// ============ 手牌渲染 ============
function renderHandCards(inference) {
    const container = document.getElementById("hand-cards");
    if (!inference || !inference.obs || !Array.isArray(inference.obs.player1_hand)) {
        if (container) container.innerHTML = '<div style="color: var(--text-muted); font-size: 12px;">无手牌数据</div>';
        return;
    }

    const meta = state.cardMetadata || {};
    const types = meta.card_types || {};
    const suits = meta.suits || { 0: "黑桃", 1: "红桃", 2: "梅花", 3: "方块", 4: "无花色" };
    const ranks = meta.ranks || {};

    const cards = inference.obs.player1_hand;
    const mask = inference.obs.player1_hand_mask || [];
    const suitSymbols = { 0: "♠", 1: "♥", 2: "♣", 3: "♦", 4: "" };

    let html = "";
    cards.forEach((card, i) => {
        const isValid = mask[i] === 1 || mask[i] === true;
        if (!isValid) {
            html += `<div class="card empty"><div class="card-name">—</div></div>`;
            return;
        }
        const typeId = card[0];
        const suitId = card[1];
        const rankId = card[2];
        const typeName = types[typeId] || `类型${typeId}`;
        const suitName = suits[suitId] || "";
        const rankName = ranks[rankId] || rankId;
        const isRed = suitId === 1 || suitId === 3;
        const colorClass = isRed ? "red" : "black";

        html += `<div class="card ${colorClass}" title="${typeName} ${suitName} ${rankName}">
            <div class="card-suit">${suitSymbols[suitId] || ""}</div>
            <div class="card-name">${typeName}</div>
            <div class="card-rank">${rankName}</div>
        </div>`;
    });

    container.innerHTML = html;
}

// ============ 动作概率渲染 ============
function renderActionProbs(inference) {
    const container = document.getElementById("action-prob-chart");
    if (!inference) {
        container.innerHTML = '<div class="loading">暂无动作概率数据</div>';
        return;
    }

    const topActions = inference.top_actions || [];
    const actionMask = inference.action_mask || [];
    const chosen = inference.chosen_action;

    let html = "";
    topActions.forEach((act, i) => {
        const isValid = act.valid;
        const probPct = (act.probability * 100).toFixed(2);
        const isChosen = chosen !== undefined && chosen !== null && act.action_id === chosen;
        html += `<div class="prob-item ${isChosen ? "chosen" : ""}">
            <div class="prob-action">#${act.action_id}</div>
            <div class="prob-bar-container">
                <div class="prob-bar ${!isValid ? "invalid" : ""}" style="width: ${Math.max(2, act.probability * 100)}%;"></div>
            </div>
            <div class="prob-value">${probPct}% ${!isValid ? '<span class="prob-invalid">(非法)</span>' : ""} ${isChosen ? '✓' : ''}</div>
        </div>`;
    });

    container.innerHTML = html || '<div class="loading">无有效动作</div>';

    // 价值
    const valueEl = document.getElementById("value-number");
    if (valueEl) valueEl.textContent = formatNumber(inference.value, 4);

    const stepEl = document.getElementById("step-number");
    if (stepEl) stepEl.textContent = inference.step_count ?? 0;
}

// ============ 激活值热力图 ============
function renderActivations(inference) {
    const container = document.getElementById("activations-container");
    if (!inference || !inference.activations) {
        container.innerHTML = '<div class="loading">暂无激活值数据</div>';
        return;
    }

    const acts = inference.activations;
    const branches = [
        { key: "branch_scalar", title: "① 标量分支激活", color: "16, 185, 129" },
        { key: "branch_hand", title: "② 手牌分支激活", color: "245, 158, 11" },
        { key: "branch_equipment", title: "③ 装备分支激活", color: "99, 102, 241" },
        { key: "branch_opponent", title: "④ 对手分支激活", color: "239, 68, 68" },
        { key: "temporal", title: "时序建模激活", color: "6, 182, 212" },
        { key: "final_feature", title: "最终融合特征", color: "139, 92, 246" },
    ];

    let html = "";
    branches.forEach(b => {
        const vec = acts[b.key];
        if (!Array.isArray(vec)) return;

        const max = Math.max(...vec.map(v => Math.abs(v)));
        const sum = vec.reduce((a, b) => a + b, 0);
        const mean = sum / vec.length;

        let heatCells = "";
        vec.forEach(v => {
            const norm = max > 0 ? (Math.abs(v) / max) : 0;
            const intensity = Math.min(1, norm);
            const sign = v >= 0 ? 1 : 0;
            if (sign) {
                heatCells += `<div class="heatmap-cell" style="background: rgba(${b.color}, ${0.2 + intensity * 0.7});" title="${formatNumber(v, 3)}"></div>`;
            } else {
                heatCells += `<div class="heatmap-cell" style="background: rgba(${b.color}, ${0.15 + intensity * 0.5}); opacity: 0.6;" title="${formatNumber(v, 3)}"></div>`;
            }
        });

        html += `<div class="activation-box">
            <div class="activation-title">${b.title}</div>
            <div class="activation-stats">dim=${vec.length} | μ=${formatNumber(mean, 3)} | max=${formatNumber(max, 3)}</div>
            <div class="heatmap-grid">${heatCells}</div>
        </div>`;
    });

    container.innerHTML = html;
}

// ============ 主流程：拉取 & 渲染 ============
async function loadArchitecture() {
    try {
        setStatus("loading", "加载网络架构...");
        const data = await apiGet("/api/network/architecture");
        state.architecture = data.architecture;
        renderArchitecture(state.architecture);
        setStatus("connected", "架构已加载");
    } catch (e) {
        console.error(e);
        setStatus("error", "架构加载失败: " + e.message);
    }
}

async function loadCardMetadata() {
    try {
        const data = await apiGet("/api/game/card-metadata");
        state.cardMetadata = data;
    } catch (e) {
        console.warn("卡牌元数据加载失败", e);
    }
}

async function runInference() {
    try {
        setStatus("loading", "推理中...");
        const data = await apiPost("/api/network/inference");
        state.currentInference = data;

        renderGameState(data);
        renderActionProbs(data);
        renderHandCards(data);
        renderActivations(data);

        setStatus("connected", "推理完成");
    } catch (e) {
        console.error(e);
        setStatus("error", "推理失败: " + e.message);
    }
}

async function resetGame() {
    try {
        setStatus("loading", "重置对局...");
        await apiPost("/api/game/reset");
        await runInference();
    } catch (e) {
        console.error(e);
        setStatus("error", "重置失败: " + e.message);
    }
}

async function stepGame() {
    try {
        setStatus("loading", "AI出一步...");
        const data = await apiPost("/api/game/step");
        state.currentInference = data;
        renderGameState(data);
        renderActionProbs(data);
        renderHandCards(data);
        renderActivations(data);
        setStatus("connected", "已走一步");
    } catch (e) {
        console.error(e);
        setStatus("error", "走步失败: " + e.message);
    }
}

// ============ 自动模式 ============
function toggleAutoMode() {
    const btn = document.getElementById("btn-auto");
    if (state.autoMode) {
        // 关闭
        clearInterval(state.autoTimer);
        state.autoMode = false;
        state.autoTimer = null;
        btn.textContent = "⏩ 自动模式";
        btn.classList.remove("active");
    } else {
        // 开启
        state.autoMode = true;
        btn.textContent = "⏸ 停止自动";
        btn.classList.add("active");
        state.autoTimer = setInterval(stepGame, AUTO_INTERVAL_MS);
    }
}

// ============ 事件绑定 & 启动 ============
function bindEvents() {
    document.getElementById("btn-reset").addEventListener("click", () => {
        if (state.autoMode) toggleAutoMode();
        resetGame();
    });
    document.getElementById("btn-step").addEventListener("click", stepGame);
    document.getElementById("btn-auto").addEventListener("click", toggleAutoMode);

    // 网络库按钮
    const refreshBtn = document.getElementById("btn-network-refresh");
    if (refreshBtn) refreshBtn.addEventListener("click", loadNetworkLibrary);

    const newBtn = document.getElementById("btn-network-new");
    if (newBtn) newBtn.addEventListener("click", () => openNetworkModal(null));

    const closeBtn = document.getElementById("btn-modal-close");
    if (closeBtn) closeBtn.addEventListener("click", closeNetworkModal);

    const closeBtn2 = document.getElementById("btn-network-close");
    if (closeBtn2) closeBtn2.addEventListener("click", closeNetworkModal);

    const applyBtn = document.getElementById("btn-network-apply");
    if (applyBtn) applyBtn.addEventListener("click", applyCurrentNetwork);

    const saveBtn = document.getElementById("btn-network-save");
    if (saveBtn) saveBtn.addEventListener("click", saveCurrentNetwork);

    const delBtn = document.getElementById("btn-network-delete");
    if (delBtn) delBtn.addEventListener("click", deleteCurrentNetwork);

    // 点击蒙层空白处关闭
    const modal = document.getElementById("network-modal");
    if (modal) {
        modal.addEventListener("click", (e) => {
            if (e.target.id === "network-modal") closeNetworkModal();
        });
    }
}

async function init() {
    bindEvents();
    await Promise.all([
        loadArchitecture(),
        loadCardMetadata(),
        loadNetworkLibrary(),
    ]);
    // 初始化完成后拉一次推理
    await runInference();
}

// DOM 就绪后启动
if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
} else {
    init();
}

/* =======================================================
   网络库模块 (data_lake/network_library)
   提供网络资产的列表/查看/编辑/保存/应用/删除
   ======================================================= */

// ============ 网络库 API ============
async function loadNetworkLibrary() {
    try {
        const data = await apiGet("/api/network-library");
        state.networks = data.networks || [];
        state.activeNetworkId = data.active_network_id || null;
        renderNetworkList();
    } catch (e) {
        console.error(e);
        const list = document.getElementById("network-list");
        if (list) list.innerHTML = `<div class="loading">网络库加载失败: ${e.message}</div>`;
    }
}

async function loadNetworkDetail(networkId) {
    const data = await apiGet(`/api/network-library/${networkId}`);
    return data.network;
}

// ============ 网络库列表渲染 ============
function renderNetworkList() {
    const container = document.getElementById("network-list");
    if (!container) return;

    if (!state.networks || state.networks.length === 0) {
        container.innerHTML = '<div class="loading">暂无网络资产，点击 "+ 新建" 创建</div>';
        return;
    }

    let html = "";
    state.networks.forEach(net => {
        const isActive = net.id === state.activeNetworkId;
        const tags = (net.tags || []).slice(0, 4).map(t =>
            `<span class="network-tag">${t}</span>`
        ).join("");

        const hp = net.hyperparameters || {};
        const hpBadges = [];
        if (hp.num_actions) hpBadges.push(`<span class="network-hp-badge">A=${hp.num_actions}</span>`);
        if (hp.hidden_dim) hpBadges.push(`<span class="network-hp-badge">H=${hp.hidden_dim}</span>`);
        if (hp.history_len) hpBadges.push(`<span class="network-hp-badge">T=${hp.history_len}</span>`);

        html += `
        <div class="network-card ${isActive ? "active" : ""}" data-network-id="${net.id}">
            ${isActive ? '<div class="active-badge">ACTIVE</div>' : ''}
            <div class="network-card-header">
                <span class="network-card-id">${net.id}</span>
                <span class="network-card-status ${net.status || "active"}">${net.status || "active"}</span>
            </div>
            <div class="network-card-name">${net.name || "未命名网络"}</div>
            <div class="network-card-desc">${net.description || "无描述"}</div>
            <div class="network-card-meta">
                ${tags}
                ${hpBadges.join("")}
                ${net.param_count ? `<span class="network-hp-badge">${formatParams(net.param_count)}</span>` : ''}
                <span class="network-tag">${net.domain || "?"}</span>
                <span class="network-tag">v${net.version || "?"}</span>
            </div>
        </div>`;
    });

    container.innerHTML = html;

    // 绑定点击事件
    container.querySelectorAll(".network-card").forEach(card => {
        card.addEventListener("click", async () => {
            const id = card.getAttribute("data-network-id");
            try {
                const detail = await loadNetworkDetail(id);
                openNetworkModal(detail);
            } catch (e) {
                alert(`加载网络 ${id} 失败: ${e.message}`);
            }
        });
    });
}

function formatParams(n) {
    if (!n) return "";
    if (n >= 1e6) return (n / 1e6).toFixed(2) + "M params";
    if (n >= 1e3) return (n / 1e3).toFixed(1) + "K params";
    return n + " params";
}

// ============ 模态框：打开/关闭 ============
function openNetworkModal(network) {
    state.currentEditNetwork = network ? JSON.parse(JSON.stringify(network)) : createDefaultNetwork();

    const modal = document.getElementById("network-modal");
    const titleEl = document.getElementById("network-modal-title");
    titleEl.textContent = network ? `编辑: ${network.name}` : "新建网络资产";

    // 填充字段
    const n = state.currentEditNetwork;
    setVal("net-f-id", n.id || "");
    setVal("net-f-name", n.name || "");
    setVal("net-f-version", n.version || "1.0.0");
    setVal("net-f-domain", n.domain || "sanguosha");
    setVal("net-f-algorithm", n.algorithm || "ppo");
    setVal("net-f-status", n.status || "active");
    setVal("net-f-description", n.description || "");

    const hp = n.hyperparameters || {};
    setVal("hp-num-actions", hp.num_actions || 100);
    setVal("hp-state-dim", hp.state_dim || 48);
    setVal("hp-history-len", hp.history_len || 10);
    setVal("hp-hidden-dim", hp.hidden_dim || 256);
    setVal("hp-card-type-vocab", hp.card_type_vocab || 30);
    setVal("hp-suit-vocab", hp.suit_vocab || 6);
    setVal("hp-rank-vocab", hp.rank_vocab || 15);
    setVal("hp-card-emb-dim", hp.card_emb_dim || 32);
    setVal("hp-num-branches", hp.num_branches || 4);
    setVal("hp-branch-hidden", hp.branch_hidden || 64);

    setVal("net-f-graph", JSON.stringify(n.network_graph || {}, null, 2));
    setVal("net-f-input", JSON.stringify(n.input_signature || {}, null, 2));
    setVal("net-f-output", JSON.stringify(n.output_signature || {}, null, 2));
    setVal("net-f-vis", JSON.stringify(n.visualization_config || {}, null, 2));
    setVal("net-f-train", JSON.stringify(n.training_compatibility || {}, null, 2));

    modal.classList.remove("hidden");
}

function closeNetworkModal() {
    const modal = document.getElementById("network-modal");
    modal.classList.add("hidden");
    state.currentEditNetwork = null;
}

function setVal(id, val) {
    const el = document.getElementById(id);
    if (!el) return;
    el.value = (typeof val === "object" && val !== null) ? JSON.stringify(val, null, 2) : String(val);
}

function getVal(id) {
    const el = document.getElementById(id);
    return el ? el.value.trim() : "";
}

// ============ 默认网络模板 ============
function createDefaultNetwork() {
    return {
        id: "custom_network_" + Date.now(),
        name: "自定义 AlphaStar 风格网络",
        version: "0.1.0",
        created_at: new Date().toISOString().slice(0, 10),
        last_updated: new Date().toISOString().slice(0, 10),
        framework: "pytorch",
        algorithm: "ppo",
        domain: "sanguosha",
        status: "draft",
        tags: ["custom", "alphastar", "actor-critic"],
        description: "通过 5130 前端编辑的网络资产。可以修改超参数、分支配置和网络结构。",
        hyperparameters: {
            num_actions: 100,
            state_dim: 48,
            history_len: 10,
            hidden_dim: 256,
            card_type_vocab: 30,
            suit_vocab: 6,
            rank_vocab: 15,
            card_emb_dim: 32,
            num_branches: 4,
            branch_hidden: 64,
            activation: "ReLU",
            layer_norm: true,
        },
        input_signature: {
            player1_scalar: { shape: [6], dtype: "float32", description: "玩家1血量/手牌比例/技能标记" },
            player1_hand: { shape: [10, 3], dtype: "int64", description: "玩家1手牌 [type, suit, rank]" },
            player1_hand_mask: { shape: [10], dtype: "float32", description: "手牌有效掩码" },
            player1_equipment: { shape: [4, 3], dtype: "int64", description: "玩家1装备" },
            player1_equipment_mask: { shape: [4], dtype: "float32", description: "装备掩码" },
            player2_scalar: { shape: [6], dtype: "float32", description: "对手状态" },
            player2_hand_count: { shape: [1], dtype: "float32", description: "对手手牌数" },
            player2_equipment_mask: { shape: [4], dtype: "float32", description: "对手装备存在性" },
            global_state: { shape: [5], dtype: "float32", description: "回合/牌堆" },
            history: { shape: [10, 48], dtype: "float32", description: "历史状态序列" },
        },
        output_signature: {
            action_probs: { shape: [100], dtype: "float32", description: "动作概率" },
            value: { shape: [1], dtype: "float32", description: "状态价值" },
        },
        network_graph: {
            nodes: [
                { id: "branch_scalar", type: "module", label: "标量分支 (Linear+LN)", params: 1344 },
                { id: "branch_hand", type: "module", label: "手牌分支 (Embedding+Linear)", params: 7968 },
                { id: "branch_equipment", type: "module", label: "装备分支", params: 6336 },
                { id: "branch_opponent", type: "module", label: "对手分支", params: 448 },
                { id: "feature_fusion", type: "module", label: "特征融合", params: 131840 },
                { id: "actor_head", type: "head", label: "策略头 Actor", params: 91428 },
                { id: "critic_head", type: "head", label: "价值头 Critic", params: 66049 },
            ],
            edges: [
                { from: "branch_scalar", to: "feature_fusion" },
                { from: "branch_hand", to: "feature_fusion" },
                { from: "branch_equipment", to: "feature_fusion" },
                { from: "branch_opponent", to: "feature_fusion" },
                { from: "feature_fusion", to: "actor_head" },
                { from: "feature_fusion", to: "critic_head" },
            ],
        },
        visualization_config: {
            layout: "layered",
            show_params: true,
            show_activations: true,
            heatmap_grid: {
                enabled: true,
                cell_min: 8,
                branches: ["branch_scalar", "branch_hand", "branch_equipment",
                           "branch_opponent", "temporal", "final_feature"],
            },
        },
        training_compatibility: {
            algorithm: "ppo",
            trainer_class: "SanguoshaTrainer",
            env_class: "SanguoshaEnv",
            observation_type: "structured_dict",
            requires_history: true,
            action_mask: true,
            reward_range: [-1.0, 1.0],
            loss_terms: ["policy_loss", "value_loss", "entropy_bonus"],
        },
        param_count: 0,
        notes: "这是一个通过前端创建的模板，你可以修改任意字段后点击 '保存到 data_lake'。",
    };
}

// ============ 从表单收集网络资产对象 ============
function collectNetworkFromForm() {
    const parseJSON = (text, fallback) => {
        if (!text) return fallback;
        try {
            return JSON.parse(text);
        } catch (e) {
            throw new Error(`JSON 解析失败: ${e.message}`);
        }
    };

    const n = {
        id: getVal("net-f-id") || `network_${Date.now()}`,
        name: getVal("net-f-name") || "未命名网络",
        version: getVal("net-f-version") || "1.0.0",
        domain: getVal("net-f-domain") || "sanguosha",
        algorithm: getVal("net-f-algorithm") || "ppo",
        status: getVal("net-f-status") || "active",
        description: getVal("net-f-description") || "",
        created_at: state.currentEditNetwork?.created_at || new Date().toISOString().slice(0, 10),
        last_updated: new Date().toISOString().slice(0, 10),
        hyperparameters: {
            num_actions: parseInt(getVal("hp-num-actions")) || 100,
            state_dim: parseInt(getVal("hp-state-dim")) || 48,
            history_len: parseInt(getVal("hp-history-len")) || 10,
            hidden_dim: parseInt(getVal("hp-hidden-dim")) || 256,
            card_type_vocab: parseInt(getVal("hp-card-type-vocab")) || 30,
            suit_vocab: parseInt(getVal("hp-suit-vocab")) || 6,
            rank_vocab: parseInt(getVal("hp-rank-vocab")) || 15,
            card_emb_dim: parseInt(getVal("hp-card-emb-dim")) || 32,
            num_branches: parseInt(getVal("hp-num-branches")) || 4,
            branch_hidden: parseInt(getVal("hp-branch-hidden")) || 64,
            activation: "ReLU",
            layer_norm: true,
        },
        network_graph: parseJSON(getVal("net-f-graph"), { nodes: [], edges: [] }),
        input_signature: parseJSON(getVal("net-f-input"), {}),
        output_signature: parseJSON(getVal("net-f-output"), {}),
        visualization_config: parseJSON(getVal("net-f-vis"), { layout: "layered" }),
        training_compatibility: parseJSON(getVal("net-f-train"), {}),
        tags: state.currentEditNetwork?.tags || ["custom"],
        param_count: state.currentEditNetwork?.param_count || 0,
        consumers: ["neural_visualization_server:5130"],
    };
    return n;
}

// ============ 保存/应用/删除 操作 ============
async function saveCurrentNetwork() {
    try {
        const payload = collectNetworkFromForm();
        const res = await apiPost("/api/network-library", payload);
        alert(`✓ ${res.message}\n保存路径: ${res.path || "(data_lake/network_library/)"}`);
        state.currentEditNetwork = payload;
        await loadNetworkLibrary();
    } catch (e) {
        alert(`保存失败: ${e.message}`);
    }
}

async function applyCurrentNetwork() {
    if (!state.currentEditNetwork || !state.currentEditNetwork.id) {
        alert("请先保存网络，然后才能应用");
        return;
    }
    const networkId = state.currentEditNetwork.id;
    if (!confirm(`将把 "${networkId}" 应用为 5130 服务的活动模型。\n` +
                 `这将根据该网络的超参数重新构建 SanguoshaActorCritic，并重置对局状态。\n\n继续？`)) {
        return;
    }
    try {
        const res = await apiPost(`/api/network-library/${networkId}/apply`);
        state.activeNetworkId = networkId;
        alert(`✓ ${res.message}\n\n活动模型已切换。`);
        closeNetworkModal();
        // 刷新网络架构和推理
        await loadArchitecture();
        await runInference();
        await loadNetworkLibrary();
    } catch (e) {
        alert(`应用失败: ${e.message}`);
    }
}

async function deleteCurrentNetwork() {
    if (!state.currentEditNetwork || !state.currentEditNetwork.id) return;
    const networkId = state.currentEditNetwork.id;
    if (networkId === state.activeNetworkId) {
        alert("⚠ 无法删除当前活动模型，请先应用其他网络再删除。");
        return;
    }
    if (!confirm(`确定从 data_lake 中删除网络 "${networkId}"？此操作不可撤销。`)) return;

    try {
        const res = await apiDelete(`/api/network-library/${networkId}`);
        alert("✓ " + (res.message || "已删除"));
        closeNetworkModal();
        await loadNetworkLibrary();
    } catch (e) {
        alert(`删除失败: ${e.message}`);
    }
}

// 辅助：DELETE 方法
async function apiDelete(path) {
    const res = await fetch(API_BASE + path, { method: "DELETE" });
    if (!res.ok) throw new Error("HTTP " + res.status);
    return await res.json();
}

// ============================================================
// 训练控制逻辑
// ============================================================

let TRAINING_POLLER = null;
let TRAINING_HISTORY = [];
let LAST_TRAINED_NETWORK = null;

// 启动时：加载默认训练配置 & 网络列表
async function loadTrainingDefaultConfig() {
    try {
        const cfg = await apiGet("/api/training/default-config");
        // 填充下拉框
        const sel = document.getElementById("cfg-network");
        if (sel) {
            sel.innerHTML = "";
            (cfg.available_networks || []).forEach(id => {
                const opt = document.createElement("option");
                opt.value = id; opt.textContent = id;
                sel.appendChild(opt);
            });
        }
        // 填充其它字段
        setInputSafe("cfg-steps", cfg.total_steps);
        setInputSafe("cfg-lr", cfg.learning_rate);
        setInputSafe("cfg-gamma", cfg.gamma);
        setInputSafe("cfg-entropy", cfg.entropy_coef);
        setInputSafe("cfg-value", cfg.value_coef);
        setInputSafe("cfg-batch", cfg.batch_size);
        setInputSafe("cfg-save", cfg.save_interval);
        setInputSafe("cfg-log", cfg.log_interval);
    } catch (e) {
        console.warn("loadTrainingDefaultConfig failed:", e);
    }
}
function setInputSafe(id, val) {
    const el = document.getElementById(id);
    if (el) el.value = val;
}

// 训练启动
async function startTraining() {
    const networkId = document.getElementById("cfg-network").value;
    if (!confirm(`确认启动 ${networkId} 训练？将从 data_lake 加载此网络，并启动 PPO 无头训练。`)) {
        return;
    }

    const payload = {
        network_id: networkId,
        total_steps: parseInt(document.getElementById("cfg-steps").value, 10),
        learning_rate: parseFloat(document.getElementById("cfg-lr").value),
        gamma: parseFloat(document.getElementById("cfg-gamma").value),
        entropy_coef: parseFloat(document.getElementById("cfg-entropy").value),
        value_coef: parseFloat(document.getElementById("cfg-value").value),
        batch_size: parseInt(document.getElementById("cfg-batch").value, 10),
        save_interval: parseInt(document.getElementById("cfg-save").value, 10),
        log_interval: parseInt(document.getElementById("cfg-log").value, 10),
    };

    try {
        const res = await apiPost("/api/training/start", payload);
        if (!res.success) {
            alert("启动失败: " + res.message);
            return;
        }
        alert("✓ " + res.message);
        setTrainingUIState(true);
        startTrainingPoller();
    } catch (e) {
        alert("训练启动失败: " + e.message);
    }
}

// 停止训练
async function stopTraining() {
    try {
        const res = await apiPost("/api/training/stop");
        alert("✓ " + res.message);
    } catch (e) {
        alert("停止失败: " + e.message);
    }
}

// 切换 UI 状态
function setTrainingUIState(isRunning) {
    const start = document.getElementById("btn-training-start");
    const stop = document.getElementById("btn-training-stop");
    const statusEl = document.getElementById("training-status");
    const apply = document.getElementById("btn-training-apply");
    if (start) start.disabled = isRunning;
    if (stop) stop.disabled = !isRunning;
    if (statusEl) {
        if (isRunning) {
            statusEl.textContent = "训练中";
            statusEl.className = "badge badge-running";
        } else {
            statusEl.textContent = TRAINING_HISTORY.length > 0 ? "已停止" : "空闲";
            statusEl.className = TRAINING_HISTORY.length > 0 ? "badge badge-stopped" : "badge badge-idle";
        }
    }
    if (apply) {
        apply.disabled = TRAINING_HISTORY.length === 0;
    }
}

// 轮询训练状态
function startTrainingPoller() {
    stopTrainingPoller();
    TRAINING_POLLER = setInterval(async () => {
        try {
            const status = await apiGet("/api/training/status");
            updateTrainingStatusUI(status);
            if (status.running || TRAINING_HISTORY.length > 0) {
                const hist = await apiGet("/api/training/history?limit=200");
                if (Array.isArray(hist.history) && hist.history.length > 0) {
                    TRAINING_HISTORY = hist.history;
                    updateTrainingCharts();
                    if (hist.logs && Array.isArray(hist.logs)) {
                        updateTrainingLogs(hist.logs);
                    }
                }
            }
            if (!status.running && TRAINING_POLLER && status.total_steps > 0 && status.current_step >= status.total_steps) {
                setTrainingUIState(false);
                stopTrainingPoller();
                LAST_TRAINED_NETWORK = status.config ? status.config.network_id : null;
            }
        } catch (e) {
            console.warn("training poll error:", e);
        }
    }, 1500);
}

function stopTrainingPoller() {
    if (TRAINING_POLLER) {
        clearInterval(TRAINING_POLLER);
        TRAINING_POLLER = null;
    }
}

// 更新训练状态 UI
function updateTrainingStatusUI(status) {
    const pct = status.total_steps > 0 ? (status.current_step / status.total_steps * 100) : 0;
    const fill = document.getElementById("progress-fill");
    if (fill) fill.style.width = pct.toFixed(1) + "%";

    const pctEl = document.getElementById("training-progress-pct");
    if (pctEl) pctEl.textContent = pct.toFixed(1) + "%";

    const stepInfo = document.getElementById("training-step-info");
    if (stepInfo) stepInfo.textContent = `${status.current_step} / ${status.total_steps} 步`;

    const elapsed = document.getElementById("training-elapsed");
    if (elapsed) elapsed.textContent = `${status.elapsed_sec.toFixed(1)}s`;

    const sps = document.getElementById("training-sps");
    if (sps) sps.textContent = `${(status.steps_per_sec || 0).toFixed(1)} step/s`;

    if (status.metrics) {
        setTextSafe("m-loss", (status.metrics.last_loss || 0).toFixed(4));
        const r = status.metrics.last_reward || 0;
        setTextSafe("m-reward", (r >= 0 ? "+" : "") + r.toFixed(2));
        setTextSafe("m-avg", (status.metrics.avg_reward_100 || 0).toFixed(3));
        setTextSafe("m-ep", status.metrics.episode_count || 0);
        setTextSafe("m-ent", (status.metrics.entropy || 0).toFixed(3));
        const bestEl = document.getElementById("m-best");
        if (bestEl) bestEl.textContent = (typeof status.metrics.best_reward === "number" && isFinite(status.metrics.best_reward) ? status.metrics.best_reward.toFixed(3) : "--");
    }
}
function setTextSafe(id, val) {
    const el = document.getElementById(id);
    if (el) el.textContent = val;
}

// Canvas 曲线绘制（不依赖任何库）
function drawChart(canvasId, data, color) {
    const c = document.getElementById(canvasId);
    if (!c) return;
    const ctx = c.getContext("2d");
    const dpr = window.devicePixelRatio || 1;
    const rect = c.getBoundingClientRect();
    c.width = rect.width * dpr;
    c.height = rect.height * dpr;
    ctx.scale(dpr, dpr);
    ctx.clearRect(0, 0, rect.width, rect.height);
    const W = rect.width, H = rect.height;
    const pad = 8;
    if (!data || data.length === 0) {
        ctx.fillStyle = "#64748b";
        ctx.font = "12px monospace";
        ctx.fillText("暂无数据", pad + 10, H / 2);
        return;
    }
    const vals = data.map(v => !isFinite(v) ? 0 : v);
    const minV = Math.min(...vals);
    const maxV = Math.max(...vals);
    const range = (maxV - minV) || 1;
    // 折线
    ctx.strokeStyle = color;
    ctx.lineWidth = 2;
    ctx.beginPath();
    for (let i = 0; i < vals.length; i++) {
        const x = pad + (i / Math.max(vals.length - 1, 1)) * (W - 2 * pad);
        const y = H - pad - ((vals[i] - minV) / range) * (H - 2 * pad);
        if (i === 0) ctx.moveTo(x, y);
        else ctx.lineTo(x, y);
    }
    ctx.stroke();
    // 填充区域
    ctx.fillStyle = color + "2E";
    ctx.beginPath();
    for (let i = 0; i < vals.length; i++) {
        const x = pad + (i / Math.max(vals.length - 1, 1)) * (W - 2 * pad);
        const y = H - pad - ((vals[i] - minV) / range) * (H - 2 * pad);
        if (i === 0) ctx.moveTo(x, y);
        else ctx.lineTo(x, y);
    }
    ctx.lineTo(pad + (W - 2 * pad), H - pad);
    ctx.lineTo(pad, H - pad);
    ctx.closePath();
    ctx.fill();
    // min/max 标注
    ctx.fillStyle = "#64748b";
    ctx.font = "10px monospace";
    ctx.fillText("max " + maxV.toFixed(3), pad, 12);
    ctx.fillText("min " + minV.toFixed(3), pad, H - 4);
}

function updateTrainingCharts() {
    drawChart("chart-loss", TRAINING_HISTORY.map(d => d.loss), "#ef4444");
    drawChart("chart-reward", TRAINING_HISTORY.map(d => d.avg_reward_100), "#10b981");
    drawChart("chart-actor", TRAINING_HISTORY.map(d => d.actor_loss), "#3b82f6");
    drawChart("chart-critic", TRAINING_HISTORY.map(d => d.critic_loss), "#8b5cf6");
}

function updateTrainingLogs(logs) {
    const logEl = document.getElementById("training-log");
    if (!logEl) return;
    if (!logs || logs.length === 0) {
        logEl.textContent = "暂无日志...";
    } else {
        logEl.textContent = logs.slice(-50).join("\n");
        logEl.scrollTop = logEl.scrollHeight;
    }
}

// 把训练网络应用到可视化面板
async function applyTrainedNetworkToViz() {
    const networkId = document.getElementById("cfg-network").value;
    if (!networkId) return;
    if (!confirm(`将 ${networkId} 应用为活动模型？`)) return;
    try {
        const res = await apiPost(`/api/network-library/${networkId}/apply`);
        alert("✓ " + (res.message || "已应用"));
        state.activeNetworkId = networkId;
        await loadArchitecture();
        await runInference();
    } catch (e) {
        alert("应用失败: " + e.message);
    }
}

// 绑定训练面板按钮事件
function initTrainingUI() {
    const startBtn = document.getElementById("btn-training-start");
    const stopBtn = document.getElementById("btn-training-stop");
    const refreshBtn = document.getElementById("btn-training-refresh");
    const applyBtn = document.getElementById("btn-training-apply");

    if (startBtn) startBtn.addEventListener("click", startTraining);
    if (stopBtn) stopBtn.addEventListener("click", stopTraining);
    if (refreshBtn) refreshBtn.addEventListener("click", async () => {
        try {
            const status = await apiGet("/api/training/status");
            updateTrainingStatusUI(status);
            const hist = await apiGet("/api/training/history?limit=200");
            if (Array.isArray(hist.history) && hist.history.length > 0) {
                TRAINING_HISTORY = hist.history;
                updateTrainingCharts();
                updateTrainingLogs(hist.logs || []);
            }
        } catch (e) { console.warn(e); }
    });
    if (applyBtn) applyBtn.addEventListener("click", applyTrainedNetworkToViz);
}

// ============================================================
// 扩展 initApp：增加训练相关初始化
// ============================================================
const _origInitApp = initApp;
initApp = async function() {
    await _origInitApp();
    await loadTrainingDefaultConfig();
    initTrainingUI();
    try {
        const status = await apiGet("/api/training/status");
        updateTrainingStatusUI(status);
        if (status.running) {
            setTrainingUIState(true);
            startTrainingPoller();
        }
    } catch (e) {
        console.warn("training status check failed:", e);
    }
};

