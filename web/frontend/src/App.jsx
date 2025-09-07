import React, { useState, useEffect } from 'react'
import axios from 'axios'
import CharacterSelection from './components/CharacterSelection'
import GameBoard from './components/GameBoard'

function App() {
  const [gameState, setGameState] = useState('selection') // selection, playing, ended
  const [gameId, setGameId] = useState(null)
  const [gameStatus, setGameStatus] = useState(null)

  const handleGameStart = (gameData) => {
    setGameId(gameData.game_id)
    setGameState('playing')
    fetchGameStatus(gameData.game_id)
  }

  const fetchGameStatus = async (id) => {
    try {
      const response = await axios.get(`http://localhost:5000/api/game/${id}/status`)
      setGameStatus(response.data)
    } catch (error) {
      console.error('获取游戏状态失败:', error)
    }
  }

  const handlePlayCard = async (cardIndex) => {
    try {
      await axios.post(`http://localhost:5000/api/game/${gameId}/play`, {
        card_index: cardIndex
      })
      fetchGameStatus(gameId)
    } catch (error) {
      console.error('出牌失败:', error)
    }
  }

  const handleEndTurn = async () => {
    try {
      await axios.post(`http://localhost:5000/api/game/${gameId}/end_turn`)
      fetchGameStatus(gameId)
    } catch (error) {
      console.error('结束回合失败:', error)
    }
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-900 via-blue-800 to-purple-900">
      <div className="container mx-auto px-4 py-8">
        <header className="text-center mb-8">
          <h1 className="text-4xl font-bold text-white mb-2">三国杀网页版</h1>
          <p className="text-gray-300">经典卡牌对战游戏</p>
        </header>

        {gameState === 'selection' && (
          <CharacterSelection onGameStart={handleGameStart} />
        )}

        {gameState === 'playing' && gameStatus && (
          <GameBoard
            gameStatus={gameStatus}
            onPlayCard={handlePlayCard}
            onEndTurn={handleEndTurn}
          />
        )}

        {gameState === 'ended' && (
          <div className="text-center">
            <h2 className="text-2xl font-bold text-white mb-4">游戏结束</h2>
            <button
              className="btn-primary"
              onClick={() => setGameState('selection')}
            >
              开始新游戏
            </button>
          </div>
        )}
      </div>
    </div>
  )
}

export default App