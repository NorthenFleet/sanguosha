from app.core.base.game import Game
from app.models.player import Player
from app.models.character import CharacterFactory
from app.core.events.event_system import EventManager

# 创建事件管理器
event_manager = EventManager()

# 创建游戏实例
game = Game(event_manager)

# 创建玩家
player1 = Player(CharacterFactory.create_character("曹操"))
player2 = Player(CharacterFactory.create_character("刘备"))

# 添加玩家
game.add_player(player1)
game.add_player(player2)

# 测试 current_player 属性
print("初始化后:")
print(f"current_player_index: {game.current_player_index}")
print(f"current_player: {game.current_player}")

# 设置当前玩家
game.current_player = game.players[game.current_player_index]
print("\n设置当前玩家后:")
print(f"current_player_index: {game.current_player_index}")
print(f"current_player: {game.current_player}")
print(f"current_player.character.name: {game.current_player.character.name}")

# 测试判定阶段
print("\n测试判定阶段:")
game.judgment_phase()