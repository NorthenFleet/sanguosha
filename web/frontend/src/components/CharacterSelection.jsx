import React, { useState, useEffect } from 'react'
import axios from 'axios'

function CharacterSelection({ onGameStart }) {
  const [characters, setCharacters] = useState([])
  const [selectedChar1, setSelectedChar1] = useState(null)
  const [selectedChar2, setSelectedChar2] = useState(null)

  useEffect(() => {
    fetchCharacters()
  }, [])

  const fetchCharacters = async () => {
    try {
      const response = await axios.get('http://localhost:5000/api/characters')
      setCharacters(response.data)
    } catch (error) {
      console.error('获取武将列表失败:', error)
    }
  }

  const handleStartGame = async () => {
    if (!selectedChar1 || !selectedChar2) {
      alert('请选择两名武将')
      return
    }

    try {
      const response = await axios.post('http://localhost:5000/api/game/create', {
        player1_char: selectedChar1,
        player2_char: selectedChar2
      })
      onGameStart(response.data)
    } catch (error) {
      console.error('创建游戏失败:', error)
      alert('创建游戏失败，请重试')
    }
  }

  return (
    <div className="max-w-4xl mx-auto">
      <div className="text-center mb-8">
        <h2 className="text-3xl font-bold text-white mb-4">选择武将</h2>
        <p className="text-gray-300">请为两名玩家选择武将开始游戏</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-8 mb-8">
        {/* 玩家1选择 */}
        <div className="character-card">
          <h3 className="text-xl font-bold text-sanguo-red mb-4">玩家1</h3>
          <div className="grid grid-cols-2 gap-3">
            {characters.map(char => (
              <button
                key={char.id}
                className={`p-3 rounded border-2 transition-all ${
                  selectedChar1 === char.id
                    ? 'border-sanguo-red bg-red-100'
                    : 'border-gray-300 hover:border-sanguo-blue'
                }`}
                onClick={() => setSelectedChar1(char.id)}
              >
                <div className="font-bold text-sanguo-blue">{char.name}</div>
                <div className="text-sm text-gray-600">血量: {char.max_hp}</div>
              </button>
            ))}
          </div>
        </div>

        {/* 玩家2选择 */}
        <div className="character-card">
          <h3 className="text-xl font-bold text-sanguo-blue mb-4">玩家2</h3>
          <div className="grid grid-cols-2 gap-3">
            {characters.map(char => (
              <button
                key={char.id}
                className={`p-3 rounded border-2 transition-all ${
                  selectedChar2 === char.id
                    ? 'border-sanguo-blue bg-blue-100'
                    : 'border-gray-300 hover:border-sanguo-red'
                }`}
                onClick={() => setSelectedChar2(char.id)}
              >
                <div className="font-bold text-sanguo-red">{char.name}</div>
                <div className="text-sm text-gray-600">血量: {char.max_hp}</div>
              </button>
            ))}
          </div>
        </div>
      </div>

      <div className="text-center">
        <button
          className="btn-primary text-lg px-8 py-3"
          onClick={handleStartGame}
          disabled={!selectedChar1 || !selectedChar2}
        >
          开始游戏
        </button>
      </div>
    </div>
  )
}

export default CharacterSelection