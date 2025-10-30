// 简单的静态预览脚本：填充演示数据并渲染到布局

const demoState = {
  player: {
    name: '曹操',
    character: '魏·曹操',
    hp: 3,
    maxHp: 4,
    equipment: {
      weapon: { name: '青釭剑' },
      defense: null,
      attack_horse: null,
      defense_horse: { name: '的卢' }
    },
    judgment: [ { name: '乐不思蜀' } ],
    hand: [
      { name: '杀' }, { name: '闪' }, { name: '桃' }, { name: '借刀杀人' }, { name: '过河拆桥' }
    ]
  },
  opponent: {
    name: '孙权',
    character: '吴·孙权',
    hp: 4,
    maxHp: 4,
    equipment: {
      weapon: null,
      defense: { name: '八卦阵' },
      attack_horse: { name: '赤兔' },
      defense_horse: null
    },
    judgment: [],
    handCount: 4
  },
  deckCount: 35,
  discardCount: 2,
  log: [
    '游戏开始，曹操先手。',
    '曹操打出【杀】，目标孙权。',
    '孙权打出【闪】，抵消伤害。',
    '曹操出【过河拆桥】，弃置孙权装备【八卦阵】。'
  ]
};

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
  // 玩家信息
  setText('player-name', demoState.player.name);
  setText('player-character', demoState.player.character);
  renderHp('player-hp-fill', 'player-hp-text', demoState.player.hp, demoState.player.maxHp);
  renderEquipment('player', demoState.player.equipment);
  renderJudgment('player-judgment', demoState.player.judgment);
  setText('player-hand-count', String(demoState.player.hand.length));
  renderHand('player-hand', demoState.player.hand);

  // 对手信息
  setText('opponent-name', demoState.opponent.name);
  setText('opponent-character', demoState.opponent.character);
  renderHp('opponent-hp-fill', 'opponent-hp-text', demoState.opponent.hp, demoState.opponent.maxHp);
  renderEquipment('opponent', demoState.opponent.equipment);
  renderJudgment('opponent-judgment', demoState.opponent.judgment);
  renderHand('opponent-hand', Array(demoState.opponent.handCount).fill({ name: '未知' }), true);

  // 中央与状态
  setText('deck-count', String(demoState.deckCount));
  setText('discard-count', String(demoState.discardCount));
  renderLog('log', demoState.log);
  setText('status-text', '演示布局：仅静态预览');
}

function bindControls() {
  $('btn-new-game').addEventListener('click', () => {
    demoState.log.push('点击【新游戏】（静态预览，无实际逻辑）');
    render();
  });
  $('btn-back').addEventListener('click', () => {
    demoState.log.push('点击【返回菜单】（静态预览，无实际逻辑）');
    render();
  });
  $('btn-play-card').addEventListener('click', () => {
    demoState.log.push('点击【出牌】（静态预览）');
    render();
  });
  $('btn-use-skill').addEventListener('click', () => {
    demoState.log.push('点击【技能】（静态预览）');
    render();
  });
  $('btn-end-turn').addEventListener('click', () => {
    demoState.log.push('点击【结束回合】（静态预览）');
    render();
  });
}

document.addEventListener('DOMContentLoaded', () => {
  bindControls();
  render();
});