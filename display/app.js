// 网页版三国杀1v1游戏 - API对接版本

// 全局游戏状态
let gameState = null;
let currentGameId = null;
let isLoading = false;

// API基础配置
const API_BASE = '/api';

// API调用封装
async function apiCall(endpoint, options = {}) {
  const url = `${API_BASE}${endpoint}`;
  const config = {
    headers: {
      'Content-Type': 'application/json',
      ...options.headers
    },
    ...options
  };
  
  try {
    const response = await fetch(url, config);
    if (!response.ok) {
      throw new Error(`API调用失败: ${response.status} ${response.statusText}`);
    }
    return await response.json();
  } catch (error) {
    console.error('API调用错误:', error);
    showError(`网络错误: ${error.message}`);
    throw error;
  }
}

// 创建新游戏
async function createGame(player1Character = '曹操', player2Character = '孙权') {
  setLoading(true);
  try {
    const result = await apiCall('/create', {
      method: 'POST',
      body: JSON.stringify({
        player1_character: player1Character,
        player2_character: player2Character
      })
    });
    
    currentGameId = result.game_id;
    addLog(`游戏创建成功，ID: ${currentGameId}`);
    await refreshGameState();
    return result;
  } catch (error) {
    addLog(`创建游戏失败: ${error.message}`);
    throw error;
  } finally {
    setLoading(false);
  }
}

// 获取游戏状态
async function getGameState() {
  if (!currentGameId) {
    throw new Error('没有活跃的游戏');
  }
  
  try {
    const state = await apiCall(`/${currentGameId}/status`);
    return state;
  } catch (error) {
    addLog(`获取游戏状态失败: ${error.message}`);
    throw error;
  }
}

// 执行游戏动作
async function executeAction(actionType, actionData = {}) {
  if (!currentGameId) {
    showError('没有活跃的游戏');
    return;
  }
  
  setLoading(true);
  try {
    const result = await apiCall(`/${currentGameId}/action`, {
      method: 'POST',
      body: JSON.stringify({
        action_type: actionType,
        ...actionData
      })
    });
    
    addLog(`执行动作: ${actionType}`);
    await refreshGameState();
    return result;
  } catch (error) {
    addLog(`执行动作失败: ${error.message}`);
    throw error;
  } finally {
    setLoading(false);
  }
}

// 刷新游戏状态并重新渲染
async function refreshGameState() {
  try {
    gameState = await getGameState();
    render();
  } catch (error) {
    console.error('刷新游戏状态失败:', error);
  }
}

// 错误提示
function showError(message) {
  const statusEl = $('status-text');
  if (statusEl) {
    statusEl.textContent = `错误: ${message}`;
    statusEl.style.color = '#ff4444';
  }
  console.error(message);
}

// 加载状态管理
function setLoading(loading) {
  isLoading = loading;
  const statusEl = $('status-text');
  if (statusEl) {
    if (loading) {
      statusEl.textContent = '处理中...';
      statusEl.style.color = '#666';
    } else {
      statusEl.textContent = currentGameId ? `游戏ID: ${currentGameId}` : '等待开始游戏';
      statusEl.style.color = '#333';
    }
  }
  
  // 禁用/启用按钮
  const buttons = ['btn-new-game', 'btn-play-card', 'btn-use-skill', 'btn-end-turn'];
  buttons.forEach(id => {
    const btn = $(id);
    if (btn) {
      btn.disabled = loading;
    }
  });
}

// 添加日志
function addLog(message) {
  if (!gameState) {
    gameState = { log: [] };
  }
  if (!gameState.log) {
    gameState.log = [];
  }
  gameState.log.push(`[${new Date().toLocaleTimeString()}] ${message}`);
  
  // 限制日志长度
  if (gameState.log.length > 50) {
    gameState.log = gameState.log.slice(-50);
  }
  
  render();
}

function $(id) { return document.getElementById(id); }

function setText(id, text) { $(id).textContent = text; }

function renderHp(fillId, textId, hp, maxHp) {
  const pct = Math.max(0, Math.min(100, Math.round(hp / maxHp * 100)));
  $(fillId).style.width = pct + '%';
  setText(textId, `${hp} / ${maxHp}`);
}

function renderEquipment(prefix, eq) {
  const slots = [
    { key: 'weapon', el: `${prefix}-weapon` },
    { key: 'defense', el: `${prefix}-defense` },
    { key: 'attack_horse', el: `${prefix}-attack-horse` },
    { key: 'defense_horse', el: `${prefix}-defense-horse` },
  ];
  slots.forEach(s => {
    const node = $(s.el);
    node.innerHTML = '';
    const card = eq[s.key];
    if (card) {
      const pill = document.createElement('div');
      pill.className = 'card-pill';
      pill.textContent = card.name;
      node.appendChild(pill);
    } else {
      node.textContent = '空';
    }
  });
}

function renderJudgment(id, cards) {
  const node = $(id);
  node.innerHTML = '';
  if (!cards || cards.length === 0) {
    const empty = document.createElement('div');
    empty.className = 'card-slot';
    empty.textContent = '无';
    node.appendChild(empty);
    return;
  }
  cards.forEach(c => {
    const pill = document.createElement('div');
    pill.className = 'card-pill';
    pill.textContent = c.name;
    node.appendChild(pill);
  });
}

function renderHand(id, cards, blurOpponent = false) {
  const node = $(id);
  node.innerHTML = '';
  cards.forEach(c => {
    const card = document.createElement('div');
    card.className = 'card';
    card.textContent = c.name;
    node.appendChild(card);
  });
  if (blurOpponent) {
    node.querySelectorAll('.card').forEach(el => el.classList.add('opponent'));
  }
}

function renderLog(id, entries) {
  const node = $(id);
  node.innerHTML = '';
  entries.forEach(e => {
    const div = document.createElement('div');
    div.className = 'log-entry';
    div.textContent = e;
    node.appendChild(div);
  });
  node.scrollTop = node.scrollHeight;
}

function render() {
  if (!gameState) {
    // 没有游戏状态时显示默认界面
    setText('player-name', '等待开始');
    setText('player-character', '选择角色');
    setText('player-hp-text', '0 / 0');
    $('player-hp-fill').style.width = '0%';
    
    setText('opponent-name', '等待对手');
    setText('opponent-character', '选择角色');
    setText('opponent-hp-text', '0 / 0');
    $('opponent-hp-fill').style.width = '0%';
    
    setText('deck-count', '0');
    setText('discard-count', '0');
    setText('player-hand-count', '0');
    
    // 清空装备和判定区
    ['player', 'opponent'].forEach(prefix => {
      ['weapon', 'defense', 'attack-horse', 'defense-horse'].forEach(slot => {
        const el = $(`${prefix}-${slot}`);
        if (el) el.textContent = '空';
      });
      const judgmentEl = $(`${prefix}-judgment`);
      if (judgmentEl) judgmentEl.textContent = '无';
    });
    
    // 清空手牌
    const playerHandEl = $('player-hand');
    const opponentHandEl = $('opponent-hand');
    if (playerHandEl) playerHandEl.innerHTML = '';
    if (opponentHandEl) opponentHandEl.innerHTML = '';
    
    // 显示日志
    if (gameState && gameState.log) {
      renderLog('log', gameState.log);
    } else {
      renderLog('log', ['等待开始游戏...']);
    }
    
    return;
  }

  // 渲染玩家信息（适配GameEngine返回的数据结构）
  const players = gameState.players || [];
  const player = players[0]; // 玩家1
  const opponent = players[1]; // 玩家2
  
  if (player) {
    setText('player-name', `玩家1`);
    setText('player-character', player.character_name || '未知角色');
    renderHp('player-hp-fill', 'player-hp-text', player.hp || 0, player.max_hp || 4);
    
    // 装备区（暂时简化处理）
    const playerEquipment = {
      weapon: player.weapon ? { name: player.weapon } : null,
      defense: null,
      attack_horse: null,
      defense_horse: null
    };
    renderEquipment('player', playerEquipment);
    
    // 判定区（暂时为空）
    renderJudgment('player-judgment', []);
    
    // 手牌
    if (player.hand_cards && Array.isArray(player.hand_cards)) {
      setText('player-hand-count', String(player.hand_cards.length));
      const handCards = player.hand_cards.map(card => ({ name: card }));
      renderHand('player-hand', handCards);
    } else {
      setText('player-hand-count', String(player.hand_cards_count || 0));
      renderHand('player-hand', Array(player.hand_cards_count || 0).fill({ name: '手牌' }));
    }
  }

  if (opponent) {
    setText('opponent-name', `玩家2`);
    setText('opponent-character', opponent.character_name || '未知角色');
    renderHp('opponent-hp-fill', 'opponent-hp-text', opponent.hp || 0, opponent.max_hp || 4);
    
    // 装备区
    const opponentEquipment = {
      weapon: opponent.weapon ? { name: opponent.weapon } : null,
      defense: null,
      attack_horse: null,
      defense_horse: null
    };
    renderEquipment('opponent', opponentEquipment);
    
    // 判定区
    renderJudgment('opponent-judgment', []);
    
    // 对手手牌（不显示具体内容）
    const opponentHandCount = opponent.hand_cards_count || 0;
    renderHand('opponent-hand', Array(opponentHandCount).fill({ name: '未知' }), true);
  }

  // 渲染中央区域
  setText('deck-count', String(gameState.deck_count || 0));
  setText('discard-count', '0'); // 暂时没有弃牌堆数据
  
  // 渲染日志
  const logEntries = gameState.log || ['游戏进行中...'];
  renderLog('log', logEntries);
  
  // 更新状态文本
  let statusText = '';
  if (gameState.current_phase) {
    statusText = `当前阶段: ${gameState.current_phase}`;
  }
  if (gameState.current_player_id) {
    statusText += ` | 当前玩家: 玩家${gameState.current_player_id}`;
  }
  if (!statusText) {
    statusText = currentGameId ? `游戏ID: ${currentGameId}` : '等待开始游戏';
  }
  setText('status-text', statusText);
}

function bindControls() {
  $('btn-new-game').addEventListener('click', async () => {
    try {
      await createGame('曹操', '孙权');
    } catch (error) {
      console.error('创建游戏失败:', error);
    }
  });
  
  $('btn-back').addEventListener('click', () => {
    if (confirm('确定要返回菜单吗？当前游戏将会丢失。')) {
      currentGameId = null;
      gameState = null;
      addLog('返回主菜单');
      render();
    }
  });
  
  $('btn-play-card').addEventListener('click', async () => {
    if (!currentGameId) {
      showError('请先创建游戏');
      return;
    }
    try {
      await executeAction('play_card', { card_index: 0 });
    } catch (error) {
      console.error('出牌失败:', error);
    }
  });
  
  $('btn-use-skill').addEventListener('click', async () => {
    if (!currentGameId) {
      showError('请先创建游戏');
      return;
    }
    try {
      await executeAction('use_skill', { skill_name: 'default' });
    } catch (error) {
      console.error('使用技能失败:', error);
    }
  });
  
  $('btn-end-turn').addEventListener('click', async () => {
    if (!currentGameId) {
      showError('请先创建游戏');
      return;
    }
    try {
      await executeAction('end_turn');
    } catch (error) {
      console.error('结束回合失败:', error);
    }
  });
}

document.addEventListener('DOMContentLoaded', () => {
  bindControls();
  render();
  addLog('网页版三国杀已加载，点击【新游戏】开始');
});