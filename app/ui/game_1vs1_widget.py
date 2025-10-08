#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
1vs1游戏界面
实现双人对战的完整游戏界面
"""

import sys
import os
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, 
                             QPushButton, QLabel, QFrame, QScrollArea, 
                             QMessageBox, QProgressBar, QTextEdit, QSplitter,
                             QGroupBox, QListWidget, QListWidgetItem, QDialog,
                             QDialogButtonBox, QComboBox, QSpinBox)
from PyQt5.QtCore import Qt, pyqtSignal, QTimer, QThread, pyqtSlot, QSize
from PyQt5.QtGui import QFont, QPixmap, QIcon, QPalette, QColor, QPainter, QBrush
from typing import Dict, List, Optional, Callable

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from app.core.base.game import Game
from app.models.player import Player
from app.models.character import Character
from app.models.card import Card
from app.ui.player_selection_dialog import PlayerSelectionDialog

class CardWidget(QFrame):
    """卡牌显示组件"""
    
    card_clicked = pyqtSignal(object)  # 卡牌点击信号
    
    def __init__(self, card: Card, selectable: bool = True):
        super().__init__()
        self.card = card
        self.selectable = selectable
        self.selected = False
        self.init_ui()
        
    def init_ui(self):
        """初始化卡牌UI"""
        self.setFixedSize(80, 120)
        self.setFrameStyle(QFrame.Box)
        self.setLineWidth(2)
        
        layout = QVBoxLayout()
        layout.setContentsMargins(5, 5, 5, 5)
        
        # 卡牌名称
        name_label = QLabel(self.card.name)
        name_label.setFont(QFont("SimHei", 8, QFont.Bold))
        name_label.setAlignment(Qt.AlignCenter)
        name_label.setWordWrap(True)
        
        # 卡牌花色和点数
        suit_point = QLabel(f"{self.card.suit} {self.card.rank}")
        suit_point.setFont(QFont("SimHei", 7))
        suit_point.setAlignment(Qt.AlignCenter)
        
        # 卡牌类型
        type_label = QLabel(self.card.card_type)
        type_label.setFont(QFont("SimHei", 6))
        type_label.setAlignment(Qt.AlignCenter)
        
        layout.addWidget(name_label)
        layout.addWidget(suit_point)
        layout.addStretch()
        layout.addWidget(type_label)
        
        self.setLayout(layout)
        self.update_style()
        
    def update_style(self):
        """更新卡牌样式"""
        if self.selected:
            self.setStyleSheet("""
                QFrame {
                    background-color: #FFD700;
                    border: 3px solid #FF6347;
                    border-radius: 8px;
                }
                QLabel {
                    color: #8B4513;
                }
            """)
        elif self.selectable:
            self.setStyleSheet("""
                QFrame {
                    background-color: #F5F5DC;
                    border: 2px solid #8B4513;
                    border-radius: 8px;
                }
                QFrame:hover {
                    background-color: #FFFACD;
                    border-color: #DAA520;
                }
                QLabel {
                    color: #8B4513;
                }
            """)
        else:
            self.setStyleSheet("""
                QFrame {
                    background-color: #D3D3D3;
                    border: 2px solid #A9A9A9;
                    border-radius: 8px;
                }
                QLabel {
                    color: #696969;
                }
            """)
            
    def mousePressEvent(self, event):
        """鼠标点击事件"""
        if self.selectable and event.button() == Qt.LeftButton:
            self.selected = not self.selected
            self.update_style()
            self.card_clicked.emit(self.card)
            
    def set_selected(self, selected: bool):
        """设置选中状态"""
        self.selected = selected
        self.update_style()


class PlayerInfoWidget(QFrame):
    """玩家信息显示组件"""
    
    def __init__(self, player: Player, is_current: bool = False):
        super().__init__()
        self.player = player
        self.is_current = is_current
        self.init_ui()
        
    def init_ui(self):
        """初始化玩家信息UI"""
        self.setFrameStyle(QFrame.Box)
        self.setLineWidth(2)
        self.setFixedHeight(150)
        
        layout = QVBoxLayout()
        
        # 玩家名称和角色
        name_layout = QHBoxLayout()
        
        name_label = QLabel(self.player.name)
        name_label.setFont(QFont("SimHei", 12, QFont.Bold))
        
        character_label = QLabel(f"({self.player.character.name})" if self.player.character else "")
        character_label.setFont(QFont("SimHei", 10))
        
        name_layout.addWidget(name_label)
        name_layout.addWidget(character_label)
        name_layout.addStretch()
        
        # 血量显示
        hp_layout = QHBoxLayout()
        hp_label = QLabel("血量:")
        hp_label.setFont(QFont("SimHei", 10))
        
        self.hp_bar = QProgressBar()
        self.hp_bar.setMaximum(self.player.max_hp)
        self.hp_bar.setValue(self.player.hp)
        self.hp_bar.setFormat(f"{self.player.hp}/{self.player.max_hp}")
        self.hp_bar.setStyleSheet("""
            QProgressBar {
                border: 2px solid #8B4513;
                border-radius: 5px;
                text-align: center;
            }
            QProgressBar::chunk {
                background-color: #DC143C;
                border-radius: 3px;
            }
        """)
        
        hp_layout.addWidget(hp_label)
        hp_layout.addWidget(self.hp_bar)
        
        # 手牌数量
        hand_label = QLabel(f"手牌: {len(self.player.hand_cards)}张")
        hand_label.setFont(QFont("SimHei", 10))
        
        # 装备区域
        equipment_label = QLabel("装备区")
        equipment_label.setFont(QFont("SimHei", 10))
        
        self.equipment_layout = QHBoxLayout()
        self.update_equipment_display()

        # 判定区域
        judgment_label = QLabel("判定区")
        judgment_label.setFont(QFont("SimHei", 10))
        self.judgment_layout = QHBoxLayout()
        self.update_judgment_display()
        
        layout.addLayout(name_layout)
        layout.addLayout(hp_layout)
        layout.addWidget(hand_label)
        layout.addWidget(equipment_label)
        layout.addLayout(self.equipment_layout)
        layout.addWidget(judgment_label)
        layout.addLayout(self.judgment_layout)
        layout.addStretch()
        
        self.setLayout(layout)
        self.update_style()
        
    def update_style(self):
        """更新样式"""
        if self.is_current:
            self.setStyleSheet("""
                QFrame {
                    background-color: #F0E68C;
                    border: 3px solid #DAA520;
                    border-radius: 10px;
                }
            """)
        else:
            self.setStyleSheet("""
                QFrame {
                    background-color: #F5F5DC;
                    border: 2px solid #8B4513;
                    border-radius: 10px;
                }
            """)
            
    def update_equipment_display(self):
        """更新装备显示"""
        # 清除现有装备显示
        for i in reversed(range(self.equipment_layout.count())):
            self.equipment_layout.itemAt(i).widget().setParent(None)
            
        # 显示装备（对齐Player模型：weapon/defense/attack_horse/defense_horse）
        equipment_slots = [
            ("武器", getattr(self.player, "weapon", None)),
            ("防具", getattr(self.player, "defense", None)),
            ("+1坐骑", getattr(self.player, "defense_horse", None)),
            ("-1坐骑", getattr(self.player, "attack_horse", None)),
        ]
        for slot_name, equipment in equipment_slots:
            if equipment:
                eq_widget = CardWidget(equipment, selectable=False)
                eq_widget.setFixedSize(60, 90)
                self.equipment_layout.addWidget(eq_widget)
            else:
                placeholder = QLabel(slot_name)
                placeholder.setFixedSize(60, 90)
                placeholder.setAlignment(Qt.AlignCenter)
                placeholder.setStyleSheet("""
                    QLabel {
                        border: 1px dashed #8B4513;
                        border-radius: 5px;
                        color: #A9A9A9;
                        font-size: 10px;
                    }
                """)
                self.equipment_layout.addWidget(placeholder)

    def update_judgment_display(self):
        """更新判定区显示"""
        # 清除现有判定显示
        for i in reversed(range(self.judgment_layout.count())):
            self.judgment_layout.itemAt(i).widget().setParent(None)
        # 判定区卡牌
        judgments = getattr(self.player, "judgment_area", []) or []
        if judgments:
            for card in judgments:
                j_widget = CardWidget(card, selectable=False)
                j_widget.setFixedSize(50, 75)
                self.judgment_layout.addWidget(j_widget)
        else:
            placeholder = QLabel("无判定牌")
            placeholder.setFixedSize(80, 30)
            placeholder.setAlignment(Qt.AlignCenter)
            placeholder.setStyleSheet("""
                QLabel {
                    border: 1px dashed #696969;
                    border-radius: 5px;
                    color: #A9A9A9;
                    font-size: 10px;
                }
            """)
            self.judgment_layout.addWidget(placeholder)
                
    def update_player_info(self, player: Player):
        """更新玩家信息"""
        self.player = player
        self.hp_bar.setValue(player.hp)
        self.hp_bar.setFormat(f"{player.hp}/{player.max_hp}")
        self.update_equipment_display()
        self.update_judgment_display()


class GameLogWidget(QTextEdit):
    """游戏日志组件"""
    
    def __init__(self):
        super().__init__()
        self.setReadOnly(True)
        self.setMaximumHeight(200)
        self.setFont(QFont("Consolas", 9))
        self.setStyleSheet("""
            QTextEdit {
                background-color: #FFFEF7;
                border: 2px solid #8B4513;
                border-radius: 5px;
                padding: 5px;
            }
        """)
        
    def add_log(self, message: str, log_type: str = "info"):
        """添加日志消息"""
        colors = {
            "info": "#000000",
            "action": "#0000FF",
            "damage": "#FF0000",
            "heal": "#00AA00",
            "system": "#800080"
        }
        
        color = colors.get(log_type, "#000000")
        self.append(f'<span style="color: {color};">{message}</span>')
        
        # 自动滚动到底部
        scrollbar = self.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())


class ActionButtonsWidget(QFrame):
    """动作按钮组件"""
    
    action_triggered = pyqtSignal(str)  # 动作触发信号
    
    def __init__(self):
        super().__init__()
        self.init_ui()
        
    def init_ui(self):
        """初始化动作按钮UI"""
        layout = QHBoxLayout()
        
        # 出牌按钮
        self.play_card_btn = QPushButton("出牌")
        self.play_card_btn.setFont(QFont("SimHei", 12))
        self.play_card_btn.clicked.connect(lambda: self.action_triggered.emit("play_card"))
        
        # 结束回合按钮
        self.end_turn_btn = QPushButton("结束回合")
        self.end_turn_btn.setFont(QFont("SimHei", 12))
        self.end_turn_btn.clicked.connect(lambda: self.action_triggered.emit("end_turn"))
        
        # 使用技能按钮
        self.use_skill_btn = QPushButton("使用技能")
        self.use_skill_btn.setFont(QFont("SimHei", 12))
        self.use_skill_btn.clicked.connect(lambda: self.action_triggered.emit("use_skill"))
        
        # 设置按钮样式
        button_style = """
            QPushButton {
                background-color: rgba(240, 230, 140, 210);
                border: 2px solid #DAA520;
                border-radius: 8px;
                padding: 8px 16px;
                color: #8B4513;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: rgba(255, 215, 0, 220);
            }
            QPushButton:pressed {
                background-color: rgba(218, 165, 32, 230);
            }
            QPushButton:disabled {
                background-color: rgba(211, 211, 211, 180);
                color: #A9A9A9;
                border-color: #A9A9A9;
            }
        """
        
        self.play_card_btn.setStyleSheet(button_style)
        self.end_turn_btn.setStyleSheet(button_style)
        self.use_skill_btn.setStyleSheet(button_style)
        
        layout.addWidget(self.play_card_btn)
        layout.addWidget(self.use_skill_btn)
        layout.addStretch()
        layout.addWidget(self.end_turn_btn)
        
        self.setLayout(layout)
        
    def set_buttons_enabled(self, enabled: bool):
        """设置按钮启用状态"""
        self.play_card_btn.setEnabled(enabled)
        self.end_turn_btn.setEnabled(enabled)
        self.use_skill_btn.setEnabled(enabled)


class Game1vs1Widget(QWidget):
    """1vs1游戏主界面"""
    # 事件桥接信号：在UI线程安全地处理游戏事件
    event_signal = pyqtSignal(str, object)
    
    back_to_menu = pyqtSignal()  # 返回菜单信号
    
    def __init__(self, ai_manager=None):
        super().__init__()
        self.setObjectName("Game1vs1Widget")
        self.game = None
        self.game_thread = None
        self.ai_manager = ai_manager  # AI管理器
        self.player_widgets = {}
        self.hand_card_widgets = []
        # 为历史代码兼容提供别名，避免属性拼写差异导致的异常
        # 统一返回同一列表对象，避免重绑造成引用失效
        
        self.selected_cards = []
        self.human_player = None
        self.player_info_panel = None
        self._player_layout = None
        self.deck_label = None
        self.discard_label = None
        self.init_ui()
        # 连接事件桥接信号到处理槽
        self.event_signal.connect(self.on_event_received)
        # 不在初始化时自动开始游戏

    @property
    def hand_cards_widgets(self):
        return self.hand_card_widgets
        
    def set_ai_manager(self, ai_manager):
        """设置AI管理器"""
        self.ai_manager = ai_manager
        
    def init_ui(self):
        """初始化游戏界面"""
        main_layout = QVBoxLayout()
        
        # 顶部工具栏
        toolbar_layout = QHBoxLayout()
        
        back_btn = QPushButton("返回主菜单")
        back_btn.setFont(QFont("SimHei", 10))
        back_btn.clicked.connect(self.back_to_menu.emit)
        back_btn.setStyleSheet("""
            QPushButton {
                background-color: #CD853F;
                border: 2px solid #8B4513;
                border-radius: 5px;
                padding: 5px 10px;
                color: black;
            }
            QPushButton:hover {
                background-color: #A0522D;
            }
        """)
        
        new_game_btn = QPushButton("新游戏")
        new_game_btn.setFont(QFont("SimHei", 10))
        new_game_btn.clicked.connect(self.start_new_game)
        new_game_btn.setStyleSheet("""
            QPushButton {
                background-color: #32CD32;
                border: 2px solid #228B22;
                border-radius: 5px;
                padding: 5px 10px;
                color: black;
            }
            QPushButton:hover {
                background-color: #228B22;
            }
        """)
        
        toolbar_layout.addWidget(back_btn)
        toolbar_layout.addWidget(new_game_btn)
        toolbar_layout.addStretch()
        
        # 游戏状态标签
        self.status_label = QLabel("准备开始游戏...")
        self.status_label.setFont(QFont("SimHei", 12, QFont.Bold))
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setStyleSheet("color: #8B4513; margin: 10px;")
        
        # 创建主游戏区域
        game_splitter = QSplitter(Qt.Horizontal)
        
        # 左侧：对手信息和游戏日志
        left_widget = QWidget()
        left_layout = QVBoxLayout()
        
        # 对手信息
        opponent_group = QGroupBox("对手信息")
        opponent_group.setFont(QFont("SimHei", 10, QFont.Bold))
        opponent_layout = QVBoxLayout()
        
        self.opponent_widget = QLabel("等待对手加入...")
        self.opponent_widget.setAlignment(Qt.AlignCenter)
        self.opponent_widget.setMinimumHeight(150)
        self.opponent_widget.setStyleSheet("""
            QLabel {
                border: 2px dashed #8B4513;
                border-radius: 10px;
                color: #A9A9A9;
                font-size: 14px;
            }
        """)
        
        opponent_layout.addWidget(self.opponent_widget)
        opponent_group.setLayout(opponent_layout)
        
        # 游戏日志
        log_group = QGroupBox("游戏日志")
        log_group.setFont(QFont("SimHei", 10, QFont.Bold))
        log_layout = QVBoxLayout()
        
        self.game_log = GameLogWidget()
        log_layout.addWidget(self.game_log)
        log_group.setLayout(log_layout)
        
        # 左侧布局稍后添加组件（先定义game_area与player_group）
        left_widget.setLayout(left_layout)
        
        # 右侧：游戏主区域
        right_widget = QWidget()
        right_layout = QVBoxLayout()
        
        # 游戏区域（牌堆、弃牌堆等）
        game_area = QFrame()
        game_area.setFrameStyle(QFrame.Box)
        game_area.setLineWidth(2)
        game_area.setMinimumHeight(200)
        game_area.setStyleSheet("""
            QFrame {
                background-color: rgba(245, 245, 220, 200);
                border: 2px solid #8B4513;
                border-radius: 10px;
            }
        """)
        
        game_area_layout = QGridLayout()
        
        # 牌堆
        self.deck_label = QLabel("牌堆\n剩余: 104张")
        self.deck_label.setAlignment(Qt.AlignCenter)
        self.deck_label.setFixedSize(80, 120)
        self.deck_label.setStyleSheet("""
            QLabel {
                background-color: rgba(139, 69, 19, 220);
                color: black;
                border: 2px solid #654321;
                border-radius: 8px;
                font-weight: bold;
            }
        """)

        # 弃牌堆
        self.discard_label = QLabel("弃牌堆\n0张")
        self.discard_label.setAlignment(Qt.AlignCenter)
        self.discard_label.setFixedSize(80, 120)
        self.discard_label.setStyleSheet("""
            QLabel {
                background-color: rgba(169, 169, 169, 220);
                color: black;
                border: 2px solid #696969;
                border-radius: 8px;
                font-weight: bold;
            }
        """)

        game_area_layout.addWidget(self.deck_label, 0, 0)
        game_area_layout.addWidget(self.discard_label, 0, 1)
        game_area_layout.setAlignment(Qt.AlignCenter)
        game_area.setLayout(game_area_layout)
        
        # 玩家信息和手牌区域
        player_group = QGroupBox("我的信息")
        player_group.setFont(QFont("SimHei", 10, QFont.Bold))
        player_layout = QVBoxLayout()
        # 保存引用以便后续插入详细信息面板
        self._player_layout = player_layout
        
        # 玩家信息
        self.player_widget = QLabel("等待游戏开始...")
        self.player_widget.setAlignment(Qt.AlignCenter)
        self.player_widget.setMinimumHeight(150)
        self.player_widget.setStyleSheet("""
            QLabel {
                border: 2px dashed #8B4513;
                border-radius: 10px;
                color: #A9A9A9;
                font-size: 14px;
            }
        """)
        
        # 手牌区域
        hand_cards_group = QGroupBox("手牌")
        hand_cards_group.setFont(QFont("SimHei", 9))
        hand_cards_layout = QVBoxLayout()
        
        self.hand_cards_scroll = QScrollArea()
        self.hand_cards_scroll.setWidgetResizable(True)
        self.hand_cards_scroll.setMaximumHeight(140)
        self.hand_cards_scroll.setStyleSheet("""
            QScrollArea {
                border: 1px solid #8B4513;
                border-radius: 5px;
                background-color: rgba(255, 254, 247, 180);
            }
        """)
        
        self.hand_cards_widget = QWidget()
        self.hand_cards_layout = QHBoxLayout()
        self.hand_cards_layout.setAlignment(Qt.AlignLeft)
        self.hand_cards_widget.setLayout(self.hand_cards_layout)
        self.hand_cards_scroll.setWidget(self.hand_cards_widget)
        
        hand_cards_layout.addWidget(self.hand_cards_scroll)
        hand_cards_group.setLayout(hand_cards_layout)
        
        # 动作按钮
        self.action_buttons = ActionButtonsWidget()
        self.action_buttons.action_triggered.connect(self.handle_action)
        # 初始禁用，待进入玩家的出牌阶段再启用
        self.action_buttons.set_buttons_enabled(False)
        
        player_layout.addWidget(self.player_widget)
        player_layout.addWidget(hand_cards_group)
        player_layout.addWidget(self.action_buttons)
        player_group.setLayout(player_layout)
        
        # 右侧改为显示对手信息 + 游戏日志
        right_layout.addWidget(opponent_group)
        right_layout.addWidget(log_group)
        # 在定义完成后，将组件加入左侧布局
        left_layout.addWidget(game_area)
        left_layout.addWidget(player_group)
        right_widget.setLayout(right_layout)
        
        # 添加到分割器
        game_splitter.addWidget(left_widget)
        game_splitter.addWidget(right_widget)
        game_splitter.setSizes([500, 500])  # 设置初始比例为左右均衡
        
        # 组装主布局
        main_layout.addLayout(toolbar_layout)
        main_layout.addWidget(self.status_label)
        main_layout.addWidget(game_splitter)
        
        self.setLayout(main_layout)
        
        # 设置背景与整体半透明主题，适配参考图片
        try:
            project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
            bg_path = os.path.join(project_root, "data", "5591740407797_.pic.jpg")
        except Exception:
            bg_path = ""

        self.setStyleSheet(f"""
            QWidget#Game1vs1Widget {{
                border-image: url('{bg_path}') 0 0 0 0 stretch stretch;
            }}
            QGroupBox {{
                background-color: rgba(255, 248, 220, 210);
                font-weight: bold;
                border: 2px solid #8B4513;
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 12px;
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 12px;
                padding: 0 6px 0 6px;
                color: #8B4513;
            }}
            QLabel {{
                color: #2f2f2f;
            }}
            QScrollArea {{
                border: 1px solid #8B4513;
                border-radius: 6px;
                background-color: rgba(255, 254, 247, 180);
            }}
        """)
        
    def init_game(self):
        """初始化游戏"""
        try:
            # 这里可以初始化游戏逻辑
            self.game_log.add_log("游戏界面初始化完成", "system")
            self.game_log.add_log("点击'新游戏'开始1vs1对战", "info")
            self.status_label.setText("点击'新游戏'开始对战")
        except Exception as e:
            self.game_log.add_log(f"游戏初始化失败: {str(e)}", "system")
            
    def start_new_game(self):
        """开始新游戏"""
        # 显示玩家选择对话框
        dialog = PlayerSelectionDialog(self, self.ai_manager)
        if dialog.exec_() != QDialog.Accepted:
            return
            
        # 获取游戏设置
        settings = dialog.get_game_settings()
        
        self.game_log.add_log("开始新的1vs1游戏", "system")
        self.status_label.setText("游戏进行中...")
        
        try:
            # 导入游戏核心模块
            from app.core.events.event_system import EventManager, EventType
            
            # 创建事件管理器和游戏实例
            event_manager = EventManager()
            self.register_event_listeners(event_manager)
            self.game = Game(event_manager)
            
            # 获取选择的武将
            player1_character = settings['player1_character']
            player2_character = settings['player2_character']
            player2_type = settings['player2_type']
            ai_difficulty = settings['ai_difficulty']
            
            # 添加玩家1到游戏
            player1 = Player(player1_character, is_ai=False)
            self.game.add_player(player1)
            self.game_log.add_log(f"玩家1选择: {player1_character.name} ({player1_character.kingdom})", "info")
            # 设置真人玩家引用并初始化信息显示
            self.human_player = player1
            self.update_player_info_text()
            self.update_hand_cards_display()

            # 在开始新局时插入详细信息面板（装备区与判定区）
            try:
                # 若已存在旧面板，移除
                if self.player_info_panel:
                    try:
                        self._player_layout.removeWidget(self.player_info_panel)
                        self.player_info_panel.setParent(None)
                    except Exception:
                        pass
                    self.player_info_panel = None
                # 首次插入时移除占位标签
                if self.player_widget and self.player_widget.parent() is not None:
                    try:
                        self._player_layout.removeWidget(self.player_widget)
                        self.player_widget.setParent(None)
                    except Exception:
                        pass
                # 创建并插入面板到布局顶部
                self.player_info_panel = PlayerInfoWidget(player=self.human_player)
                self._player_layout.insertWidget(0, self.player_info_panel)
            except Exception as _e:
                self.game_log.add_log(f"玩家信息面板初始化异常: {_e}", "system")
            
            # 添加玩家2到游戏
            if player2_type == "ai":
                # 创建AI玩家
                player2 = Player(player2_character, is_ai=True, ai_difficulty=ai_difficulty)
                
                # 设置AI智能体
                if self.ai_manager and self.ai_manager.is_initialized:
                    ai_agent = self.ai_manager.create_ai_player(player2_character)
                    if ai_agent:
                        player2.ai_agent = ai_agent
                        self.game_log.add_log(f"AI玩家选择: {player2_character.name} ({player2_character.kingdom}) - 难度: {ai_difficulty}", "info")
                    else:
                        self.game_log.add_log("AI玩家创建失败，使用简单AI", "system")
                else:
                    # 使用简单AI
                    self.game_log.add_log(f"简单AI选择: {player2_character.name} ({player2_character.kingdom}) - 难度: {ai_difficulty}", "info")
                
                self.game.add_player(player2)
                    
                # 更新对手信息显示
                self.opponent_widget.setText(f"AI对手\n{player2_character.name}\n({player2_character.kingdom})\n难度: {ai_difficulty}")
                self.opponent_widget.setStyleSheet("""
                    QLabel {
                        border: 2px solid #228B22;
                        border-radius: 10px;
                        color: #228B22;
                        font-size: 14px;
                        font-weight: bold;
                    }
                """)
            else:
                # 创建真人玩家
                player2 = Player(player2_character, is_ai=False)
                self.game.add_player(player2)
                self.game_log.add_log(f"玩家2选择: {player2_character.name} ({player2_character.kingdom})", "info")
                
                # 更新对手信息显示
                self.opponent_widget.setText(f"真人对手\n{player2_character.name}\n({player2_character.kingdom})\n等待连接...")
                self.opponent_widget.setStyleSheet("""
                    QLabel {
                        border: 2px solid #4169E1;
                        border-radius: 10px;
                        color: #4169E1;
                        font-size: 14px;
                        font-weight: bold;
                    }
                """)
            
            # 启动游戏：在后台线程运行，并启用测试模式以避免交互阻塞
            try:
                # 若已有线程在运行，先请求停止并等待其结束
                if self.game_thread and self.game_thread.isRunning():
                    self.game_log.add_log("检测到已有游戏线程，正在请求停止...", "info")
                    try:
                        if self.game and hasattr(self.game, "request_stop"):
                            self.game.request_stop()
                    except Exception:
                        pass
                    self.game_thread.wait(2000)

                class GameRunnerThread(QThread):
                    def __init__(self, game, test_mode=False, parent=None):
                        super().__init__(parent)
                        self._game = game
                        self._test_mode = test_mode
                    def run(self):
                        try:
                            self._game.start_game(test_mode=self._test_mode)
                        except Exception as e:
                            print(f"Game thread error: {e}")

                # 恢复为UI驱动模式（非测试），以验证停止逻辑
                self.game_thread = GameRunnerThread(self.game, test_mode=False, parent=self)
                self.game_thread.finished.connect(self.on_game_finished)
                self.game_thread.start()
                self.game_log.add_log("游戏开始！双方开始对战（后台运行）", "action")
            except Exception as e:
                raise e
            
        except Exception as e:
            self.game_log.add_log(f"游戏启动失败: {str(e)}", "system")
            QMessageBox.critical(self, "错误", f"游戏启动失败: {str(e)}")

    def on_game_finished(self):
        """游戏线程结束回调"""
        self.status_label.setText("游戏已结束")
        self.game_log.add_log("游戏结束，感谢游玩！", "system")

    def closeEvent(self, event):
        """窗口关闭事件：确保后台游戏线程被安全停止"""
        try:
            if hasattr(self, 'game_thread') and self.game_thread and self.game_thread.isRunning():
                # 优先请求游戏停止
                try:
                    if self.game:
                        self.game.request_stop()
                        self.game_log.add_log("请求停止游戏循环...", "system")
                except Exception:
                    pass
                # 等待线程优雅退出
                self.game_thread.wait(1500)
                # 若仍在运行则强制终止，避免QThread销毁异常
                if self.game_thread.isRunning():
                    try:
                        self.game_log.add_log("强制终止游戏线程...", "system")
                    except Exception:
                        pass
                    self.game_thread.terminate()
                    self.game_thread.wait(500)
        except Exception:
            pass
        super().closeEvent(event)

    def register_event_listeners(self, event_manager):
        """订阅事件，并通过信号桥接到UI线程"""
        from app.core.events.event_system import EventType

        def make_listener(evt_type: str):
            def listener(event_data):
                # 将事件转发到UI线程
                self.event_signal.emit(evt_type, event_data)
            return listener

        for evt in [
            EventType.GAME_START,
            EventType.DRAW_CARD,
            EventType.DISCARD_CARD,
            EventType.PLAY_CARD,
            EventType.USE_SKILL,
            EventType.PHASE_CHANGE,
            EventType.TAKE_DAMAGE,
            EventType.PLAYER_DEATH,
            EventType.GAME_END,
        ]:
            event_manager.register_listener(evt, make_listener(evt.value))

    @pyqtSlot(str, object)
    def on_event_received(self, event_type: str, event_data: object):
        """统一事件处理入口，更新UI显示与日志"""
        try:
            # 日志与状态
            if event_type == "game_start":
                self.status_label.setText("游戏进行中...")
                self.game_log.add_log("游戏开始", "system")
                # 初始化牌堆显示
                if self.game and self.deck_label:
                    self.deck_label.setText(f"牌堆\n剩余: {len(self.game.deck.cards)}张")
                if self.game and self.discard_label:
                    self.discard_label.setText(f"弃牌堆\n{len(self.game.deck.discard_pile)}张")
                # 初始刷新玩家信息与手牌
                self.update_player_info_text()
                self.update_hand_cards_display()
                # 开局默认禁用动作按钮，等待阶段切换到玩家的出牌阶段
                if self.action_buttons:
                    self.action_buttons.set_buttons_enabled(False)

            elif event_type == "draw_card":
                player = event_data.get("player")
                count = event_data.get("count")
                if player:
                    self.game_log.add_log(f"{player.character.name} 摸牌 {count} 张", "info")
                if self.game and self.deck_label:
                    self.deck_label.setText(f"牌堆\n剩余: {len(self.game.deck.cards)}张")
                if player is self.human_player:
                    self.update_hand_cards_display()
                    self.update_player_info_text()

            elif event_type == "discard_card":
                player = event_data.get("player")
                card = event_data.get("card")
                if player and card:
                    self.game_log.add_log(f"{player.character.name} 弃置 {card.name}", "action")
                if self.game and self.discard_label:
                    self.discard_label.setText(f"弃牌堆\n{len(self.game.deck.discard_pile)}张")
                if player is self.human_player:
                    self.update_hand_cards_display()
                    self.update_player_info_text()

            elif event_type == "play_card":
                player = event_data.get("player")
                card = event_data.get("card")
                target = event_data.get("target")
                is_response = event_data.get("is_response", False)
                response_type = event_data.get("response_type")
                if player and card:
                    if is_response:
                        msg = f"{player.character.name} 响应：使用 {card.name}"
                        if response_type:
                            msg += f"（{response_type}）"
                    else:
                        msg = f"{player.character.name} 使用 {card.name}"
                    if target:
                        msg += f" -> {target.character.name}"
                    self.game_log.add_log(msg, "action")
                if player is self.human_player:
                    self.update_hand_cards_display()
                    self.update_player_info_text()

            elif event_type == "use_skill":
                player = event_data.get("player")
                skill = event_data.get("skill")
                if player and skill:
                    self.game_log.add_log(f"{player.character.name} 触发技能【{skill}】", "action")

            elif event_type == "phase_change":
                phase = event_data.get("phase")
                player = event_data.get("player")
                if phase:
                    phase_map = {
                        "judgment": "判定阶段",
                        "play": "出牌阶段",
                        "discard": "弃牌阶段",
                    }
                    phase_text = phase_map.get(phase, str(phase))
                    if player:
                        self.status_label.setText(f"{player.character.name} 的{phase_text}")
                    else:
                        self.status_label.setText(f"当前阶段: {phase_text}")
                    # 仅当为真人玩家且处于出牌阶段时启用动作按钮
                    if self.action_buttons:
                        is_human_turn = (player is self.human_player)
                        self.action_buttons.set_buttons_enabled(is_human_turn and phase == "play")

            elif event_type == "take_damage":
                player = event_data.get("player")
                damage = event_data.get("damage")
                if player and damage is not None:
                    self.game_log.add_log(f"{player.character.name} 受到 {damage} 点伤害", "damage")
                if player is self.human_player:
                    self.update_player_info_text()

            elif event_type == "player_death":
                player = event_data.get("player")
                if player:
                    self.game_log.add_log(f"{player.character.name} 死亡", "system")
                    try:
                        # 弹窗提示是否重新开局
                        msg = QMessageBox(self)
                        msg.setWindowTitle("本局结束")
                        msg.setText(f"{player.character.name} 已阵亡。是否重新开一局？")
                        msg.setIcon(QMessageBox.Question)
                        restart_btn = msg.addButton("重新开局", QMessageBox.AcceptRole)
                        back_btn = msg.addButton("返回菜单", QMessageBox.RejectRole)
                        msg.exec_()
                        if msg.clickedButton() is restart_btn:
                            # 请求停止当前游戏，加速结束
                            try:
                                if self.game and hasattr(self.game, "request_stop"):
                                    self.game.request_stop()
                            except Exception:
                                pass
                            # 开始新游戏（内部会等待线程结束）
                            self.start_new_game()
                        elif msg.clickedButton() is back_btn:
                            # 返回主菜单
                            try:
                                self.back_to_menu.emit()
                            except Exception:
                                pass
                    except Exception as _e:
                        self.game_log.add_log(f"重开局提示弹窗异常: {_e}", "system")

            elif event_type == "game_end":
                winner = event_data.get("winner")
                if winner:
                    self.game_log.add_log(f"胜者: {winner.character.name}", "system")
                else:
                    self.game_log.add_log("平局", "system")
                self.status_label.setText("游戏已结束")
                if self.action_buttons:
                    self.action_buttons.set_buttons_enabled(False)
        except Exception as e:
            # 避免事件处理导致UI崩溃
            self.game_log.add_log(f"事件处理异常: {e}", "system")
        
    @pyqtSlot(str)
    def handle_action(self, action: str):
        """处理玩家动作"""
        if action == "play_card":
            if not self.game or not self.human_player:
                QMessageBox.information(self, "提示", "游戏尚未开始或玩家未就绪！")
                return

            if self.selected_cards:
                # 逐张处理选中的卡牌（当前按顺序逐一使用）
                for card in list(self.selected_cards):
                    try:
                        # 防止 UI 线程阻塞，尽量简化响应流程
                        # 先从手牌中移除（装备牌由 Player.use_card 处理）
                        if getattr(card, 'type', None) and getattr(card.type, 'value', None) == "装备牌":
                            self.human_player.use_card(card)
                            # 装备牌不进弃牌堆，但可记录动作
                            self.game_log.add_log(f"装备 {card.name}", "action")
                            # 触发使用卡牌事件到 UI
                            target = self.game.get_opponent(self.human_player)
                            self.game.event_manager.trigger("play_card", {"player": self.human_player, "card": card, "target": target, "is_response": False})
                        else:
                            # 非装备牌：移除 -> 触发事件 -> 执行效果 -> 进入弃牌堆
                            if card in self.human_player.hand_cards:
                                self.human_player.hand_cards.remove(card)
                            target = self.game.get_opponent(self.human_player)
                            # 触发使用事件（用于 UI 刷新）
                            self.game.event_manager.trigger("play_card", {"player": self.human_player, "card": card, "target": target, "is_response": False})
                            # 执行卡牌效果（在测试模式下快速处理响应，避免阻塞）
                            card_action = self.game.create_card_action(card)
                            try:
                                # 对需要响应的卡牌，走测试模式简化响应
                                if hasattr(card, 'name') and card.name in ["杀", "决斗", "南蛮入侵", "万箭齐发"]:
                                    card_action.handle_response(self.game, self.human_player, test_mode=True)
                                else:
                                    card_action.apply_effect(self.game, self.human_player)
                            except Exception as e:
                                # 效果执行异常时写日志但不中断流程
                                self.game_log.add_log(f"卡牌效果执行异常: {getattr(card, 'name', str(card))} - {str(e)}", "system")
                            # 进入弃牌堆并触发弃牌事件
                            if getattr(card, 'type', None) and getattr(card.type, 'value', None) != "装备牌":
                                self.game.deck.discard(card)
                                self.game.event_manager.trigger("discard_card", {"player": self.human_player, "card": card})

                        # 从选择列表移除该卡
                        if card in self.selected_cards:
                            self.selected_cards.remove(card)
                    finally:
                        # 每张牌处理后刷新一次显示，保持 UI 顺畅
                        self.update_hand_cards_display()
                        self.update_player_info_text()
                
            else:
                QMessageBox.information(self, "提示", "请先选择要出的牌！")
                
        elif action == "end_turn":
            # UI请求结束当前出牌阶段，通知Game并禁用按钮，等待阶段切换
            try:
                if not self.game or not self.human_player:
                    QMessageBox.information(self, "提示", "游戏尚未开始或玩家未就绪！")
                    return
                # 记录日志并请求结束回合
                self.game_log.add_log("结束回合", "action")
                self.game.request_end_turn()
                # 立即禁用动作按钮，避免重复点击
                if self.action_buttons:
                    self.action_buttons.set_buttons_enabled(False)
            except Exception as e:
                self.game_log.add_log(f"结束回合请求异常: {e}", "system")
            
        elif action == "use_skill":
            # 选择并触发角色的一个主动技能（示例：仁德、制衡等在出牌阶段）
            try:
                if not self.game or not self.human_player or not self.human_player.character:
                    QMessageBox.information(self, "提示", "游戏或玩家未就绪，无法使用技能！")
                    return

                character = self.human_player.character
                skills = getattr(character, 'skills', []) or []
                if not skills:
                    QMessageBox.information(self, "提示", "当前武将没有可用技能！")
                    return

                # 简化交互：若只有一个技能则直接尝试触发；多个技能时弹窗选择
                selected_skill = None
                if len(skills) == 1:
                    selected_skill = skills[0]
                else:
                    # 使用简单选择对话框
                    dlg = QDialog(self)
                    dlg.setWindowTitle("选择技能")
                    v = QVBoxLayout(dlg)
                    label = QLabel("请选择要使用的技能：")
                    v.addWidget(label)
                    combo = QComboBox()
                    for s in skills:
                        combo.addItem(s)
                    v.addWidget(combo)
                    btns = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
                    v.addWidget(btns)
                    btns.accepted.connect(dlg.accept)
                    btns.rejected.connect(dlg.reject)
                    if dlg.exec_() == QDialog.Accepted:
                        selected_skill = combo.currentText()
                    else:
                        return

                if not selected_skill:
                    return

                # 记录日志并触发技能事件（供UI刷新）
                self.game_log.add_log(f"使用技能【{selected_skill}】", "action")
                self.game.event_manager.trigger("use_skill", {"player": self.human_player, "skill": selected_skill})

                # 优先尝试通过角色API触发（部分角色已实现具体技能逻辑）
                used = False
                try:
                    if hasattr(character, 'use_skill'):
                        used = bool(character.use_skill(selected_skill, self.game, self.human_player))
                except Exception:
                    used = False

                # 如果角色API未处理，再尝试全局SkillManager触发（主动技能通常在出牌阶段）
                if not used and hasattr(self.game, 'skill_manager'):
                    try:
                        # 这里将事件类型标为"phase_change"，便于如仁德/制衡这类在出牌阶段的技能通过条件判断
                        used = bool(self.game.skill_manager.trigger_skill(selected_skill, self.game, self.human_player, event_type="phase_change", phase="play"))
                    except Exception:
                        used = False

                if not used:
                    QMessageBox.information(self, "提示", f"技能【{selected_skill}】当前无法发动或未实现。")
                else:
                    # 成功触发后刷新手牌与信息（若技能影响这些状态）
                    self.update_hand_cards_display()
                    self.update_player_info_text()
            except Exception as e:
                self.game_log.add_log(f"使用技能异常: {e}", "system")
            
    def update_hand_cards_display(self):
        """更新手牌显示"""
        # 清除现有手牌显示
        for widget in self.hand_card_widgets:
            widget.setParent(None)
        self.hand_card_widgets.clear()
        while self.hand_cards_layout.count():
            item = self.hand_cards_layout.takeAt(0)
            w = item.widget()
            if w:
                w.setParent(None)
        
        if not self.human_player:
            return
        
        if not self.human_player.hand_cards:
            placeholder = QLabel("暂无手牌")
            placeholder.setAlignment(Qt.AlignCenter)
            placeholder.setStyleSheet("color: #A9A9A9;")
            self.hand_cards_layout.addWidget(placeholder)
            return
        
        for card in self.human_player.hand_cards:
            cw = CardWidget(card, selectable=True)
            cw.card_clicked.connect(self.on_card_clicked)
            self.hand_card_widgets.append(cw)
            self.hand_cards_layout.addWidget(cw)

    def update_player_info_text(self):
        """更新玩家信息文本（姓名、阵营、血量、手牌数量）"""
        if not self.human_player or not self.human_player.character:
            # 若仍使用占位标签
            if isinstance(self.player_widget, QLabel):
                self.player_widget.setText("等待游戏开始...")
            return
        name = self.human_player.character.name
        kingdom = getattr(self.human_player.character, 'kingdom', '')
        hp = getattr(self.human_player, 'hp', None)
        max_hp = getattr(self.human_player.character, 'max_hp', None)
        hand_count = len(self.human_player.hand_cards)
        hp_text = f"{hp}/{max_hp}" if hp is not None and max_hp is not None else str(hp or '')
        if isinstance(self.player_widget, QLabel):
            self.player_widget.setText(f"真人玩家\n{name}\n({kingdom})\n血量: {hp_text}\n手牌: {hand_count}张")
        # 同步详细信息面板（装备区与判定区）
        if self.player_info_panel:
            try:
                self.player_info_panel.update_player_info(self.human_player)
            except Exception:
                pass
        
    @pyqtSlot(object)
    def on_card_clicked(self, card: Card):
        """处理卡牌点击"""
        if card in self.selected_cards:
            self.selected_cards.remove(card)
        else:
            self.selected_cards.append(card)
            
        self.game_log.add_log(f"{'选中' if card in self.selected_cards else '取消选中'}卡牌: {card.name}", "info")