import sys
import os
import argparse
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app.core.base.path_utils import setup_paths
setup_paths()

from app.core.events.event_system import EventManager
from app.core.base.game import Game
from app.models.character import Character
from app.models.card import Deck, display_deck_info


def main_cli():
    # 初始化事件管理器和游戏实例
    event_manager = EventManager()
    game = Game(event_manager)

    # 可选武将列表
    available_characters = [
        Character("曹操", "魏", 4, ["奸雄"]),
        Character("刘备", "蜀", 4, ["仁德"]),
        Character("孙权", "吴", 4, ["制衡"]),
    ]

    # 玩家选择武将
    print("请选择你的武将:")
    for idx, character in enumerate(available_characters, start=1):
        print(f"{idx}. {character.name} ({character.kingdom}) - 血量: {character.max_hp}, 技能: {', '.join(character.skills)}")

    while True:
        try:
            user_input = input("输入武将编号: ")
            if not user_input.strip():
                print("输入不能为空，请重新选择。")
                continue
            choice = int(user_input) - 1
            if 0 <= choice < len(available_characters):
                player_character = available_characters.pop(choice)
                break
            else:
                print("无效的选择，请重新选择。")
        except (ValueError, EOFError, KeyboardInterrupt):
            print("游戏被中断或输入无效，请重新选择。")
            continue

    # 为人机选择武将
    ai_character = available_characters[0]

    # 添加玩家和人机到游戏
    game.add_player(player_character)
    game.add_player(ai_character)

    print(f"你选择了 {player_character.name} ({player_character.kingdom})")
    print(f"人机选择了 {ai_character.name} ({ai_character.kingdom})")

    # 启动游戏
    game.start_game()

    # 初始化牌堆
    deck = Deck("app/data/cards.json")
    if not deck.cards:
        print("错误: 卡牌数据加载失败，请检查 cards.json 文件内容。")
        return

    deck.shuffle()

    # 显示牌堆信息
    display_deck_info(deck)

    # 测试摸牌功能
    card = deck.draw_card()
    print(f"摸到的牌是：{card}")

    # 将摸到的牌放入弃牌堆
    deck.discard(card)

    # 再次显示牌堆信息
    display_deck_info(deck)


def main_gui():
    """启动GUI模式的游戏"""
    try:
        from PyQt5.QtWidgets import QApplication
        from app.ui.main_window import MainWindow
        
        # 初始化AI管理器
        ai_manager = None
        try:
            # 尝试导入AI组件
            from ai.ppo_agent import PPOAgent, PPOConfig
            from ai.main_trainer import load_config
            from pathlib import Path
            
            # 创建AI管理器类
            class AIPlayerManager:
                def __init__(self, config_path=None):
                    self.config_path = config_path or "ai/config/default_config.json"
                    self.ai_agents = {}
                    self.is_initialized = False
                    
                def initialize(self):
                    try:
                        config = load_config(self.config_path)
                        ppo_config = PPOConfig(**config.get('ppo', {}))
                        self.ai_agents['default'] = PPOAgent(ppo_config)
                        
                        # 尝试加载预训练模型
                        model_path = Path("models/experiments/best_model.pth")
                        if model_path.exists():
                            try:
                                self.ai_agents['default'].load_model(str(model_path))
                                print(f"成功加载预训练模型: {model_path}")
                            except Exception as e:
                                print(f"加载预训练模型失败: {e}")
                        
                        self.is_initialized = True
                        print("AI玩家系统初始化成功")
                        return True
                    except Exception as e:
                        print(f"AI玩家系统初始化失败: {e}")
                        return False
                        
                def get_ai_agent(self, agent_name='default'):
                    if not self.is_initialized:
                        return None
                    return self.ai_agents.get(agent_name)
                    
                def create_ai_player(self, character, agent_name='default'):
                    agent = self.get_ai_agent(agent_name)
                    if agent is None:
                        return None
                    return {
                        'character': character,
                        'agent': agent,
                        'type': 'ai',
                        'name': f"AI-{character.name}"
                    }
            
            # 创建并初始化AI管理器
            ai_manager = AIPlayerManager()
            ai_initialized = ai_manager.initialize()
            if not ai_initialized:
                print("AI系统初始化失败，将使用简单AI")
                ai_manager = None
                
        except ImportError as e:
            print(f"AI模块不可用: {e}")
            ai_manager = None
        except Exception as e:
            print(f"AI系统初始化错误: {e}")
            ai_manager = None
        
        # 创建Qt应用
        app = QApplication(sys.argv)
        app.setApplicationName("三国杀")
        app.setApplicationVersion("1.0")
        app.setOrganizationName("AI Game Studio")
        
        # 创建主窗口
        window = MainWindow()
        
        # 如果AI可用，将AI管理器传递给主窗口
        if ai_manager and ai_manager.is_initialized:
            window.set_ai_manager(ai_manager)
            print("AI系统已集成到GUI界面")
        
        window.show()
        sys.exit(app.exec_())
    except ImportError:
        print("错误: 无法导入PyQt5，请安装PyQt5或使用命令行模式")
        print("安装命令: pip install PyQt5")
        sys.exit(1)
    except Exception as e:
        print(f"GUI启动失败: {e}")
        sys.exit(1)


if __name__ == "__main__":
    print("注意: 此文件不再作为独立入口程序使用")
    print("请使用项目根目录的 main_launcher.py 启动游戏")
    print("示例: python main_launcher.py --mode gui")
    sys.exit(1)