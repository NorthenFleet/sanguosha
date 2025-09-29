#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
游戏模式接口定义
为不同游戏模式提供标准化接口，便于扩展和管理
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from PyQt5.QtWidgets import QWidget
from PyQt5.QtCore import QObject, pyqtSignal


class GameModeInterface(QWidget, ABC):
    """游戏模式接口基类"""
    
    # 通用信号定义
    game_started = pyqtSignal()           # 游戏开始
    game_ended = pyqtSignal(dict)         # 游戏结束，传递结果
    game_paused = pyqtSignal()            # 游戏暂停
    game_resumed = pyqtSignal()           # 游戏恢复
    back_to_menu = pyqtSignal()           # 返回主菜单
    player_action = pyqtSignal(dict)      # 玩家动作
    game_state_changed = pyqtSignal(dict) # 游戏状态变化
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._game_state = "idle"  # idle, running, paused, ended
        self._players = []
        self._settings = {}
        
    @abstractmethod
    def get_mode_info(self) -> Dict[str, Any]:
        """获取模式信息
        
        Returns:
            包含模式ID、名称、描述等信息的字典
        """
        pass
    
    @abstractmethod
    def initialize_game(self, settings: Dict[str, Any] = None):
        """初始化游戏
        
        Args:
            settings: 游戏设置参数
        """
        pass
    
    @abstractmethod
    def start_new_game(self):
        """开始新游戏"""
        pass
    
    @abstractmethod
    def pause_game(self):
        """暂停游戏"""
        pass
    
    @abstractmethod
    def resume_game(self):
        """恢复游戏"""
        pass
    
    @abstractmethod
    def end_game(self, result: Dict[str, Any] = None):
        """结束游戏
        
        Args:
            result: 游戏结果
        """
        pass
    
    @abstractmethod
    def get_game_state(self) -> Dict[str, Any]:
        """获取当前游戏状态"""
        pass
    
    @abstractmethod
    def handle_player_action(self, action: Dict[str, Any]):
        """处理玩家动作
        
        Args:
            action: 玩家动作数据
        """
        pass
    
    def get_supported_player_count(self) -> tuple:
        """获取支持的玩家数量范围
        
        Returns:
            (最小玩家数, 最大玩家数)
        """
        return (1, 1)  # 默认单人游戏
    
    def get_default_settings(self) -> Dict[str, Any]:
        """获取默认设置"""
        return {
            'difficulty': 'normal',
            'turn_time': 60,
            'auto_save': True
        }
    
    def validate_settings(self, settings: Dict[str, Any]) -> bool:
        """验证设置参数
        
        Args:
            settings: 设置参数
            
        Returns:
            是否有效
        """
        return True  # 默认实现，子类可重写
    
    def save_game(self, filename: str = None) -> bool:
        """保存游戏
        
        Args:
            filename: 保存文件名
            
        Returns:
            是否保存成功
        """
        # 默认实现，子类可重写
        return False
    
    def load_game(self, filename: str) -> bool:
        """加载游戏
        
        Args:
            filename: 游戏文件名
            
        Returns:
            是否加载成功
        """
        # 默认实现，子类可重写
        return False


class Vs1ModeInterface(GameModeInterface):
    """1vs1模式接口"""
    
    def get_mode_info(self) -> Dict[str, Any]:
        return {
            'id': '1vs1',
            'name': '1 vs 1 对战',
            'description': '经典双人对战模式',
            'min_players': 2,
            'max_players': 2,
            'supports_ai': True,
            'supports_network': False
        }
    
    def get_supported_player_count(self) -> tuple:
        return (2, 2)


class GuozhanModeInterface(GameModeInterface):
    """国战模式接口"""
    
    def get_mode_info(self) -> Dict[str, Any]:
        return {
            'id': 'guozhan',
            'name': '国战模式',
            'description': '多人团队作战模式',
            'min_players': 4,
            'max_players': 8,
            'supports_ai': True,
            'supports_network': True,
            'teams': ['魏', '蜀', '吴', '群']
        }
    
    def get_supported_player_count(self) -> tuple:
        return (4, 8)
    
    @abstractmethod
    def get_team_info(self) -> Dict[str, List[str]]:
        """获取队伍信息
        
        Returns:
            队伍名称到玩家列表的映射
        """
        pass
    
    @abstractmethod
    def handle_team_action(self, team: str, action: Dict[str, Any]):
        """处理队伍动作
        
        Args:
            team: 队伍名称
            action: 动作数据
        """
        pass


class CommanderModeInterface(GameModeInterface):
    """统帅三军模式接口"""
    
    def get_mode_info(self) -> Dict[str, Any]:
        return {
            'id': 'commander',
            'name': '统帅三军',
            'description': '指挥大军作战模式',
            'min_players': 2,
            'max_players': 6,
            'supports_ai': True,
            'supports_network': True,
            'has_commander': True
        }
    
    def get_supported_player_count(self) -> tuple:
        return (2, 6)
    
    @abstractmethod
    def get_commander_info(self) -> Dict[str, Any]:
        """获取统帅信息"""
        pass
    
    @abstractmethod
    def handle_commander_skill(self, skill_id: str, targets: List[str]):
        """处理统帅技能
        
        Args:
            skill_id: 技能ID
            targets: 目标列表
        """
        pass


class CustomModeInterface(GameModeInterface):
    """自定义模式接口"""
    
    def __init__(self, mode_config: Dict[str, Any], parent=None):
        super().__init__(parent)
        self._mode_config = mode_config
    
    def get_mode_info(self) -> Dict[str, Any]:
        return self._mode_config.get('info', {
            'id': 'custom',
            'name': '自定义模式',
            'description': '用户自定义规则模式',
            'min_players': 1,
            'max_players': 10,
            'supports_ai': True,
            'supports_network': False
        })
    
    @abstractmethod
    def load_custom_rules(self, rules_file: str):
        """加载自定义规则
        
        Args:
            rules_file: 规则文件路径
        """
        pass
    
    @abstractmethod
    def validate_custom_rules(self, rules: Dict[str, Any]) -> bool:
        """验证自定义规则
        
        Args:
            rules: 规则数据
            
        Returns:
            是否有效
        """
        pass


# 模式工厂类
class GameModeFactory:
    """游戏模式工厂"""
    
    _mode_classes = {
        '1vs1': Vs1ModeInterface,
        'guozhan': GuozhanModeInterface,
        'commander': CommanderModeInterface,
        'custom': CustomModeInterface
    }
    
    @classmethod
    def register_mode(cls, mode_id: str, mode_class: type):
        """注册新的游戏模式
        
        Args:
            mode_id: 模式ID
            mode_class: 模式类
        """
        if not issubclass(mode_class, GameModeInterface):
            raise ValueError(f"模式类 {mode_class} 必须继承自 GameModeInterface")
        
        cls._mode_classes[mode_id] = mode_class
    
    @classmethod
    def create_mode(cls, mode_id: str, **kwargs) -> Optional[GameModeInterface]:
        """创建游戏模式实例
        
        Args:
            mode_id: 模式ID
            **kwargs: 创建参数
            
        Returns:
            游戏模式实例
        """
        mode_class = cls._mode_classes.get(mode_id)
        if mode_class:
            return mode_class(**kwargs)
        return None
    
    @classmethod
    def get_available_modes(cls) -> List[str]:
        """获取可用的游戏模式列表"""
        return list(cls._mode_classes.keys())
    
    @classmethod
    def get_mode_info(cls, mode_id: str) -> Optional[Dict[str, Any]]:
        """获取模式信息
        
        Args:
            mode_id: 模式ID
            
        Returns:
            模式信息
        """
        mode_class = cls._mode_classes.get(mode_id)
        if mode_class and hasattr(mode_class, 'get_mode_info'):
            # 创建临时实例获取信息
            try:
                temp_instance = mode_class()
                return temp_instance.get_mode_info()
            except:
                return None
        return None