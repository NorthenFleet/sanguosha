#!/usr/bin/env python3
from __future__ import annotations
"""
三国杀游戏主启动器
整合PyQt5界面和AI玩家系统，提供统一的游戏入口
"""

import sys
import os
import argparse
import logging
from pathlib import Path
from typing import Optional, Dict, Any

# 添加项目路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# 设置路径
from app.core.base.path_utils import setup_paths
setup_paths()

# 导入UI组件
try:
    from PyQt5.QtWidgets import QApplication, QMessageBox
    from PyQt5.QtCore import QThread, pyqtSignal
    from app.ui.main_window import MainWindow
    UI_AVAILABLE = True
except ImportError as e:
    print(f"警告: PyQt5不可用，将使用命令行模式: {e}")
    UI_AVAILABLE = False

# 导入AI组件
try:
    from ai.ppo_agent import PPOAgent, PPOConfig
    from ai.self_play_trainer import SelfPlayTrainer, SelfPlayConfig
    from ai.training_environment import TrainingConfig
    from ai.reward_system import RewardConfig
    from ai.main_trainer import load_config
    AI_AVAILABLE = True
except ImportError as e:
    print(f"警告: AI模块不可用: {e}")
    AI_AVAILABLE = False

# 导入游戏核心
from app.core.events.event_system import EventManager
from app.core.base.game import Game
from app.models.character import Character


class AIPlayerManager:
    """AI玩家管理器"""
    
    def __init__(self, config_path: Optional[str] = None):
        self.config_path = config_path or "ai/config/default_config.json"
        # 使用延迟注解避免在AI不可用时NameError
        self.ai_agents: Dict[str, 'PPOAgent'] = {}
        self.is_initialized = False
        
    def initialize(self) -> bool:
        """初始化AI系统"""
        if not AI_AVAILABLE:
            print("AI系统不可用，无法初始化AI玩家")
            return False
            
        try:
            # 加载配置
            config = load_config(self.config_path)
            ppo_config = PPOConfig(**config.get('ppo', {}))
            
            # 创建默认AI智能体
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
    
    def get_ai_agent(self, agent_name: str = 'default') -> Optional[PPOAgent]:
        """获取AI智能体"""
        if not self.is_initialized:
            return None
        return self.ai_agents.get(agent_name)
    
    def create_ai_player(self, character: Character, agent_name: str = 'default'):
        """创建AI玩家"""
        agent = self.get_ai_agent(agent_name)
        if agent is None:
            return None
        
        # 这里可以扩展AI玩家的具体实现
        # 目前返回一个包含AI智能体和角色信息的字典
        return {
            'character': character,
            'agent': agent,
            'type': 'ai',
            'name': f"AI-{character.name}"
        }


class GameLauncher:
    """游戏启动器"""
    
    def __init__(self):
        self.ai_manager = AIPlayerManager()
        self.setup_logging()
        
    def setup_logging(self):
        """设置日志"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('logs/game_launcher.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
        
        # 确保日志目录存在
        Path('logs').mkdir(exist_ok=True)
    
    def launch_gui_mode(self, enable_ai: bool = True) -> int:
        """启动GUI模式"""
        if not UI_AVAILABLE:
            print("错误: PyQt5不可用，无法启动GUI模式")
            return 1
        
        self.logger.info("启动GUI模式")
        
        # 初始化AI系统（如果启用）
        if enable_ai:
            ai_initialized = self.ai_manager.initialize()
            if not ai_initialized:
                reply = input("AI系统初始化失败，是否继续启动GUI？(y/n): ")
                if reply.lower() != 'y':
                    return 1
        
        # 创建Qt应用
        app = QApplication(sys.argv)
        app.setApplicationName("三国杀")
        app.setApplicationVersion("1.0")
        app.setOrganizationName("AI Game Studio")
        
        # 创建主窗口
        main_window = MainWindow()
        
        # 如果AI可用，将AI管理器传递给主窗口
        if enable_ai and self.ai_manager.is_initialized:
            main_window.set_ai_manager(self.ai_manager)
        
        # 显示窗口
        main_window.show()
        
        self.logger.info("GUI界面已启动")
        
        # 运行应用
        return app.exec_()
    
    def launch_console_mode(self, enable_ai: bool = True) -> int:
        """启动控制台模式"""
        self.logger.info("启动控制台模式")
        
        # 初始化AI系统（如果启用）
        if enable_ai:
            ai_initialized = self.ai_manager.initialize()
            if not ai_initialized:
                print("AI系统初始化失败，将使用基础游戏模式")
        
        # 运行原有的控制台游戏逻辑
        return self._run_console_game(enable_ai and self.ai_manager.is_initialized)
    
    def _run_console_game(self, ai_enabled: bool) -> int:
        """运行控制台游戏"""
        try:
            # 初始化事件管理器和游戏实例
            event_manager = EventManager()
            game = Game(event_manager)

            # 可选武将列表
            available_characters = [
                Character("曹操", "魏", 4, ["奸雄"]),
                Character("刘备", "蜀", 4, ["仁德"]),
                Character("孙权", "吴", 4, ["制衡"]),
            ]

            print("=== 三国杀游戏 ===")
            print("请选择你的武将:")
            for idx, character in enumerate(available_characters, start=1):
                print(f"{idx}. {character.name} ({character.kingdom}) - 血量: {character.max_hp}, 技能: {', '.join(character.skills)}")

            # 玩家选择武将
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

            # 为对手选择武将
            opponent_character = available_characters[0]

            # 添加玩家到游戏
            game.add_player(player_character)
            
            if ai_enabled:
                # 创建AI玩家
                ai_player = self.ai_manager.create_ai_player(opponent_character)
                if ai_player:
                    game.add_player(opponent_character)  # 暂时添加角色，后续可以扩展AI玩家逻辑
                    print(f"你选择了 {player_character.name} ({player_character.kingdom})")
                    print(f"AI选择了 {opponent_character.name} ({opponent_character.kingdom})")
                else:
                    print("AI玩家创建失败，使用普通玩家")
                    game.add_player(opponent_character)
            else:
                game.add_player(opponent_character)
                print(f"你选择了 {player_character.name} ({player_character.kingdom})")
                print(f"对手选择了 {opponent_character.name} ({opponent_character.kingdom})")

            # 启动游戏
            print("\n游戏开始！")
            game.start_game()
            
            return 0
            
        except Exception as e:
            self.logger.error(f"控制台游戏运行错误: {e}")
            return 1
    
    def launch_ai_training(self, config_path: Optional[str] = None) -> int:
        """启动AI训练模式"""
        if not AI_AVAILABLE:
            print("错误: AI模块不可用，无法启动训练模式")
            return 1
        
        self.logger.info("启动AI训练模式")
        
        try:
            from ai.main_trainer import main as ai_main
            # 这里可以传递训练参数
            return ai_main()
        except Exception as e:
            self.logger.error(f"AI训练启动失败: {e}")
            return 1


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="三国杀游戏启动器")
    parser.add_argument(
        '--mode', 
        choices=['gui', 'console', 'train'], 
        default='gui',
        help='启动模式: gui(图形界面), console(控制台), train(AI训练)'
    )
    parser.add_argument(
        '--no-ai', 
        action='store_true',
        help='禁用AI玩家系统'
    )
    parser.add_argument(
        '--config',
        type=str,
        help='AI配置文件路径'
    )
    parser.add_argument(
        '--debug',
        action='store_true',
        help='启用调试模式'
    )
    
    args = parser.parse_args()
    
    # 设置调试模式
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # 创建启动器
    launcher = GameLauncher()
    
    # 根据模式启动
    if args.mode == 'gui':
        return launcher.launch_gui_mode(enable_ai=not args.no_ai)
    elif args.mode == 'console':
        return launcher.launch_console_mode(enable_ai=not args.no_ai)
    elif args.mode == 'train':
        return launcher.launch_ai_training(args.config)
    else:
        print(f"未知模式: {args.mode}")
        return 1


if __name__ == '__main__':
    try:
        exit_code = main()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n游戏被用户中断")
        sys.exit(0)
    except Exception as e:
        print(f"启动器发生未处理的错误: {e}")
        sys.exit(1)