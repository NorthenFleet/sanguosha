from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_socketio import SocketIO, emit
import sys
import os

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.models.game import Game, Character
from app.models.player import Player
from app.models.deck import Deck

app = Flask(__name__)
app.config['SECRET_KEY'] = 'sanguosha_secret_key'
CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*")

# 游戏状态存储
games = {}

@app.route('/api/characters', methods=['GET'])
def get_characters():
    """获取所有可选武将"""
    characters = [
        {"id": 1, "name": "曹操", "max_hp": 4, "skills": ["奸雄"]},
        {"id": 2, "name": "司马懿", "max_hp": 3, "skills": ["反馈", "鬼才"]},
        {"id": 3, "name": "张辽", "max_hp": 4, "skills": ["突袭"]},
        {"id": 4, "name": "夏侯惇", "max_hp": 4, "skills": ["刚烈"]},
        {"id": 5, "name": "刘备", "max_hp": 4, "skills": ["仁德"]},
        {"id": 6, "name": "关羽", "max_hp": 4, "skills": ["武圣"]},
        {"id": 7, "name": "张飞", "max_hp": 4, "skills": ["咆哮"]},
        {"id": 8, "name": "赵云", "max_hp": 4, "skills": ["龙胆"]},
        {"id": 9, "name": "诸葛亮", "max_hp": 3, "skills": ["观星", "空城"]},
        {"id": 10, "name": "孙权", "max_hp": 4, "skills": ["制衡"]},
        {"id": 11, "name": "周瑜", "max_hp": 3, "skills": ["英姿", "反间"]},
        {"id": 12, "name": "甘宁", "max_hp": 4, "skills": ["奇袭"]},
        {"id": 13, "name": "吕蒙", "max_hp": 4, "skills": ["攻心"]}
    ]
    return jsonify(characters)

@app.route('/api/game/create', methods=['POST'])
def create_game():
    """创建新游戏"""
    data = request.json
    player1_char_id = data.get('player1_char')
    player2_char_id = data.get('player2_char')
    
    # 创建游戏实例
    game = Game()
    
    # 创建玩家
    characters = {
        1: "曹操", 2: "司马懿", 3: "张辽", 4: "夏侯惇", 5: "刘备",
        6: "关羽", 7: "张飞", 8: "赵云", 9: "诸葛亮", 10: "孙权",
        11: "周瑜", 12: "甘宁", 13: "吕蒙"
    }
    
    player1 = Player(Character(characters[player1_char_id], 4))
    player2 = Player(Character(characters[player2_char_id], 4))
    
    game.players = [player1, player2]
    game.current_player_index = 0
    game.deck = Deck()
    game.deck.shuffle()
    
    # 初始发牌
    for player in game.players:
        for _ in range(4):
            player.draw_card(game.deck)
    
    # 存储游戏状态
    game_id = len(games) + 1
    games[game_id] = game
    
    return jsonify({
        "game_id": game_id,
        "message": "游戏创建成功",
        "current_player": game.players[0].character.name
    })

@app.route('/api/game/<int:game_id>/status', methods=['GET'])
def get_game_status(game_id):
    """获取游戏状态"""
    if game_id not in games:
        return jsonify({"error": "游戏不存在"}), 404
    
    game = games[game_id]
    current_player = game.players[game.current_player_index]
    opponent = game.players[1 - game.current_player_index]
    
    return jsonify({
        "current_player": current_player.character.name,
        "current_player_hp": current_player.character.hp,
        "current_player_hand_count": len(current_player.hand_cards),
        "opponent_name": opponent.character.name,
        "opponent_hp": opponent.character.hp,
        "opponent_hand_count": len(opponent.hand_cards),
        "phase": game.current_phase
    })

@app.route('/api/game/<int:game_id>/play', methods=['POST'])
def play_card(game_id):
    """出牌"""
    if game_id not in games:
        return jsonify({"error": "游戏不存在"}), 404
    
    data = request.json
    card_index = data.get('card_index')
    
    game = games[game_id]
    current_player = game.players[game.current_player_index]
    
    if 0 <= card_index < len(current_player.hand_cards):
        card = current_player.hand_cards[card_index]
        result = game.handle_response(current_player, card)
        
        return jsonify({
            "message": f"{current_player.character.name} 使用了 {card.name}",
            "result": result
        })
    else:
        return jsonify({"error": "无效的卡牌选择"}), 400

@app.route('/api/game/<int:game_id>/end_turn', methods=['POST'])
def end_turn(game_id):
    """结束当前回合"""
    if game_id not in games:
        return jsonify({"error": "游戏不存在"}), 404
    
    game = games[game_id]
    game.current_player_index = 1 - game.current_player_index
    
    return jsonify({
        "message": "回合结束",
        "next_player": game.players[game.current_player_index].character.name
    })

if __name__ == '__main__':
    socketio.run(app, debug=True, port=5000)