import React from 'react'

function GameBoard({ gameStatus, onPlayCard, onEndTurn }) {
  const { 
    current_player, 
    current_player_hp, 
    current_player_hand_count,
    opponent_name, 
    opponent_hp, 
    opponent_hand_count,
    phase 
  } = gameStatus

  // 模拟手牌数据（实际应该从后端获取）
  const handCards = [
    { name: '杀', type: 'basic', description: '对目标造成1点伤害' },
    { name: '闪', type: 'basic', description: '闪避攻击' },
    { name: '桃', type: 'basic', description: '回复1点体力' },
    { name: '过河拆桥', type: 'trick', description: '弃置目标一张牌' },
    { name: '顺手牵羊', type: 'trick', description: '获得目标一张牌' }
  ]

  const getCardColor = (type) => {
    switch (type) {
      case 'basic': return 'bg-red-100 border-red-300'
      case 'trick': return 'bg-blue-100 border-blue-300'
      case 'equip': return 'bg-green-100 border-green-300'
      default: return 'bg-gray-100 border-gray-300'
    }
  }

  return (
    <div className="max-w-6xl mx-auto">
      {/* 游戏状态栏 */}
      <div className="bg-white/10 backdrop-blur-md rounded-lg p-6 mb-8">
        <div className="grid grid-cols-3 gap-6 text-white">
          <div className="text-center">
            <h3 className="text-lg font-bold mb-2">当前玩家</h3>
            <div className="text-2xl font-bold text-sanguo-red">{current_player}</div>
            <div className="text-sm">血量: {current_player_hp}</div>
            <div className="text-sm">手牌: {current_player_hand_count}</div>
          </div>

          <div className="text-center">
            <h3 className="text-lg font-bold mb-2">游戏阶段</h3>
            <div className="text-xl font-bold text-sanguo-gold">{phase}</div>
            <div className="text-sm mt-2">
              <button 
                className="btn-secondary"
                onClick={onEndTurn}
              >
                结束回合
              </button>
            </div>
          </div>

          <div className="text-center">
            <h3 className="text-lg font-bold mb-2">对手</h3>
            <div className="text-2xl font-bold text-sanguo-blue">{opponent_name}</div>
            <div className="text-sm">血量: {opponent_hp}</div>
            <div className="text-sm">手牌: {opponent_hand_count}</div>
          </div>
        </div>
      </div>

      {/* 手牌区域 */}
      <div className="bg-white/5 backdrop-blur-md rounded-lg p-6">
        <h3 className="text-xl font-bold text-white mb-4">你的手牌</h3>
        
        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-4">
          {handCards.map((card, index) => (
            <div
              key={index}
              className={`hand-card ${getCardColor(card.type)} cursor-pointer transition-transform hover:scale-105`}
              onClick={() => onPlayCard(index)}
            >
              <div className="text-center">
                <div className="font-bold text-lg text-gray-800">{card.name}</div>
                <div className="text-sm text-gray-600 mt-1">{card.type}</div>
                <div className="text-xs text-gray-500 mt-2">{card.description}</div>
              </div>
            </div>
          ))}
        </div>

        <div className="mt-6 text-center">
          <p className="text-gray-300 text-sm">
            点击卡牌使用，当前阶段: {phase}
          </p>
        </div>
      </div>

      {/* 游戏操作提示 */}
      <div className="mt-8 bg-yellow-100 border border-yellow-300 rounded-lg p-4">
        <h4 className="font-bold text-yellow-800 mb-2">游戏提示</h4>
        <ul className="text-yellow-700 text-sm space-y-1">
          <li>• 使用【杀】攻击对手，对手可以用【闪】响应</li>
          <li>• 使用【桃】可以回复1点体力</li>
          <li>• 锦囊牌需要对手响应，可以用【无懈可击】抵消</li>
          <li>• 回合结束时需要弃置多余的手牌</li>
        </ul>
      </div>
    </div>
  )
}

export default GameBoard