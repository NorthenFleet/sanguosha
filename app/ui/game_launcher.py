#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
游戏启动器
提供游戏的启动入口和模式扩展接口
"""

import sys
import os
from typing import Dict, Any, Optional
from PyQt5.QtWidgets import QApplication, QMessageBox
from PyQt5.QtCore import QObject, pyqtSignal

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

# 导入主窗口
from app.ui.main_window import MainWindow

# 导入游戏模式接口
try:
    from app.ui.game_1vs1_widget import Game1vs1Widget
except ImportError:
    Game1vs1Widget = None

# 为未来模式预留导入
# from app.ui.game_guozhan_widget import GameGuozhanWidget  # 国战模式
# from app.ui.game_commander_widget import GameCommanderWidget  # 统帅三军模式


class GameModeRegistry:
    """游戏模式注册器"""
    
    def __init__(self):
        self._modes = {}
        self._register_default_modes()
    
    def _register_default_modes(self):
        """注册默认游戏模式"""
        # 注册1vs1模式
        if Game1vs1Widget:
            self.register_mode(
                mode_id="1vs1",
                name="1 vs 1 对战",
                description="经典双人对战模式",
                widget_class=Game1vs1Widget,
                enabled=True
            )
        
        # 预留其他模式注册
        self.register_mode(
            mode_id="guozhan",
            name="国战模式",
            description="多人团队作战",
            widget_class=None,  # 待实现
            enabled=False
        )
        
        self.register_mode(
            mode_id="commander",
            name="统帅三军",
            description="指挥大军作战",
            widget_class=None,  # 待实现
            enabled=False
        )
        
        self.register_mode(
            mode_id="custom",
            name="自定义模式",
            description="创建自己的规则",
            widget_class=None,  # 待实现
            enabled=False
        )
    
    def register_mode(self, mode_id: str, name: str, description: str, 
                     widget_class: Optional[type] = None, enabled: bool = True):
        """注册游戏模式"""
        self._modes[mode_id] = {
            'name': name,
            'description': description,
            'widget_class': widget_class,
            'enabled': enabled
        }
    
    def get_mode(self, mode_id: str) -> Optional[Dict[str, Any]]:
        """获取游戏模式信息"""
        return self._modes.get(mode_id)
    
    def get_all_modes(self) -> Dict[str, Dict[str, Any]]:
        """获取所有游戏模式"""
        return self._modes.copy()
    
    def is_mode_available(self, mode_id: str) -> bool:
        """检查模式是否可用"""
        mode = self.get_mode(mode_id)
        return mode is not None and mode['enabled'] and mode['widget_class'] is not None


class GameLauncher(QObject):
    """游戏启动器"""
    
    # 信号定义
    game_started = pyqtSignal(str)  # 游戏开始信号
    game_ended = pyqtSignal(str)    # 游戏结束信号
    mode_changed = pyqtSignal(str)  # 模式切换信号
    
    def __init__(self):
        super().__init__()
        self.app = None
        self.main_window = None
        self.mode_registry = GameModeRegistry()
        self.current_mode = None
        
    def initialize_application(self):
        """初始化应用程序"""
        if not self.app:
            self.app = QApplication(sys.argv)
            
            # 设置应用程序信息
            self.app.setApplicationName("三国杀")
            self.app.setApplicationVersion("1.0")
            self.app.setOrganizationName("AI Game Studio")
            
            # 设置应用程序样式
            self.app.setStyle('Fusion')  # 使用Fusion样式获得更好的跨平台外观
            
        return self.app
    
    def create_main_window(self):
        """创建主窗口"""
        if not self.main_window:
            self.main_window = MainWindow()
            
            # 连接信号
            self.main_window.mode_selector.mode_selected.connect(self.on_mode_selected)
            
        return self.main_window
    
    def on_mode_selected(self, mode_id: str):
        """处理模式选择"""
        if self.mode_registry.is_mode_available(mode_id):
            self.current_mode = mode_id
            self.mode_changed.emit(mode_id)
            self.game_started.emit(mode_id)
        else:
            mode_info = self.mode_registry.get_mode(mode_id)
            if mode_info:
                QMessageBox.information(
                    self.main_window,
                    "模式不可用",
                    f"{mode_info['name']}正在开发中，敬请期待！"
                )
    
    def launch_game(self, mode_id: str = None):
        """启动游戏"""
        # 初始化应用程序
        app = self.initialize_application()
        
        # 创建主窗口
        window = self.create_main_window()
        
        # 如果指定了模式，直接启动该模式
        if mode_id and self.mode_registry.is_mode_available(mode_id):
            window.switch_to_mode(mode_id)
        
        # 显示窗口
        window.show()
        
        # 运行应用程序
        return app.exec_()
    
    def get_available_modes(self):
        """获取可用的游戏模式"""
        available_modes = {}
        for mode_id, mode_info in self.mode_registry.get_all_modes().items():
            if mode_info['enabled']:
                available_modes[mode_id] = mode_info
        return available_modes
    
    def add_custom_mode(self, mode_id: str, name: str, description: str, 
                       widget_class: type):
        """添加自定义游戏模式"""
        self.mode_registry.register_mode(
            mode_id=mode_id,
            name=name,
            description=description,
            widget_class=widget_class,
            enabled=True
        )
    
    def shutdown(self):
        """关闭游戏"""
        if self.main_window:
            self.main_window.close()
        
        if self.app:
            self.app.quit()


# 全局游戏启动器实例
_game_launcher = None


def get_game_launcher() -> GameLauncher:
    """获取游戏启动器单例"""
    global _game_launcher
    if _game_launcher is None:
        _game_launcher = GameLauncher()
    return _game_launcher


def launch_sanguosha(mode: str = None) -> int:
    """启动三国杀游戏
    
    Args:
        mode: 指定启动的游戏模式，如果为None则显示模式选择界面
        
    Returns:
        应用程序退出码
    """
    launcher = get_game_launcher()
    return launcher.launch_game(mode)


if __name__ == '__main__':
    print("注意: 此文件不再作为独立入口程序使用")
    print("请使用项目根目录的 main_launcher.py 启动游戏")
    print("示例: python main_launcher.py --mode gui")
    sys.exit(1)