#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
玩家选择对话框
用于在游戏开始前选择第二个玩家类型（真人或AI）
"""

import sys
import os
from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QGridLayout,
                             QPushButton, QLabel, QFrame, QGroupBox, 
                             QRadioButton, QButtonGroup, QComboBox,
                             QDialogButtonBox, QMessageBox, QSpacerItem,
                             QSizePolicy)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont, QPixmap, QIcon

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from app.models.character import Character


class PlayerSelectionDialog(QDialog):
    """玩家选择对话框"""
    
    def __init__(self, parent=None, ai_manager=None):
        super().__init__(parent)
        self.ai_manager = ai_manager
        self.player1_character = None
        self.player2_character = None
        self.player2_type = "human"  # "human" 或 "ai"
        self.ai_difficulty = "normal"  # "easy", "normal", "hard"
        
        # 可选武将列表
        self.available_characters = [
            Character("曹操", "魏", 4, ["奸雄"]),
            Character("刘备", "蜀", 4, ["仁德"]),
            Character("孙权", "吴", 4, ["制衡"]),
            Character("关羽", "蜀", 4, ["武圣"]),
            Character("张飞", "蜀", 4, ["咆哮"]),
            Character("赵云", "蜀", 4, ["龙胆"]),
            Character("诸葛亮", "蜀", 3, ["观星", "空城"]),
            Character("周瑜", "吴", 3, ["英姿", "反间"]),
            Character("吕布", "群", 4, ["无双"]),
            Character("貂蝉", "群", 3, ["离间", "闭月"]),
        ]
        
        self.init_ui()
        
    def init_ui(self):
        """初始化界面"""
        self.setWindowTitle("玩家设置")
        self.setFixedSize(600, 500)
        self.setModal(True)
        
        # 主布局
        main_layout = QVBoxLayout()
        
        # 标题
        title_label = QLabel("1vs1对战设置")
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setFont(QFont("SimHei", 16, QFont.Bold))
        title_label.setStyleSheet("""
            QLabel {
                color: #8B4513;
                margin: 10px;
                padding: 10px;
            }
        """)
        main_layout.addWidget(title_label)
        
        # 先创建按钮（在其他组件之前）
        self.create_buttons()
        
        # 玩家1设置
        player1_group = self.create_player1_group()
        main_layout.addWidget(player1_group)
        
        # 玩家2设置
        player2_group = self.create_player2_group()
        main_layout.addWidget(player2_group)
        
        # 添加按钮到布局
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        button_layout.addWidget(self.start_button)
        button_layout.addWidget(self.cancel_button)
        main_layout.addLayout(button_layout)

        self.setLayout(main_layout)
        
        # 设置整体样式
        self.setStyleSheet("""
            QDialog {
                background-color: #FFF8DC;
            }
            QGroupBox {
                font-weight: bold;
                border: 2px solid #8B4513;
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 15px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 15px;
                padding: 0 8px 0 8px;
                color: #8B4513;
            }
        """)
        
    def create_buttons(self):
        """创建按钮"""
        self.start_button = QPushButton("开始游戏")
        self.start_button.setFont(QFont("SimHei", 12, QFont.Bold))
        self.start_button.setFixedSize(120, 40)
        self.start_button.setStyleSheet("""
            QPushButton {
                background-color: #228B22;
                color: white;
                border: none;
                border-radius: 8px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #32CD32;
            }
            QPushButton:pressed {
                background-color: #006400;
            }
        """)
        self.start_button.clicked.connect(self.start_game)
        
        self.cancel_button = QPushButton("取消")
        self.cancel_button.setFont(QFont("SimHei", 12))
        self.cancel_button.setFixedSize(120, 40)
        self.cancel_button.setStyleSheet("""
            QPushButton {
                background-color: #DC143C;
                color: white;
                border: none;
                border-radius: 8px;
            }
            QPushButton:hover {
                background-color: #FF6347;
            }
            QPushButton:pressed {
                background-color: #B22222;
            }
        """)
        self.cancel_button.clicked.connect(self.reject)
        
    def create_player1_group(self):
        """创建玩家1设置组"""
        group = QGroupBox("玩家1 (您)")
        group.setFont(QFont("SimHei", 12, QFont.Bold))
        
        layout = QVBoxLayout()
        
        # 武将选择
        character_layout = QHBoxLayout()
        character_label = QLabel("选择武将:")
        character_label.setFont(QFont("SimHei", 10))
        
        self.player1_character_combo = QComboBox()
        self.player1_character_combo.setFont(QFont("SimHei", 10))
        for char in self.available_characters:
            self.player1_character_combo.addItem(f"{char.name} ({char.kingdom}) - {char.hp}血", char)
        
        character_layout.addWidget(character_label)
        character_layout.addWidget(self.player1_character_combo)
        character_layout.addStretch()
        
        layout.addLayout(character_layout)
        group.setLayout(layout)
        
        return group
        
    def create_player2_group(self):
        """创建玩家2设置组"""
        group = QGroupBox("玩家2 (对手)")
        group.setFont(QFont("SimHei", 12, QFont.Bold))
        
        layout = QVBoxLayout()
        
        # 玩家类型选择
        type_layout = QHBoxLayout()
        type_label = QLabel("对手类型:")
        type_label.setFont(QFont("SimHei", 10))
        
        self.player_type_group = QButtonGroup()
        
        self.human_radio = QRadioButton("真人玩家")
        self.human_radio.setFont(QFont("SimHei", 10))
        self.human_radio.setChecked(True)
        self.human_radio.toggled.connect(self.on_player_type_changed)
        
        self.ai_radio = QRadioButton("AI玩家")
        self.ai_radio.setFont(QFont("SimHei", 10))
        self.ai_radio.toggled.connect(self.on_player_type_changed)
        
        self.player_type_group.addButton(self.human_radio)
        self.player_type_group.addButton(self.ai_radio)
        
        type_layout.addWidget(type_label)
        type_layout.addWidget(self.human_radio)
        type_layout.addWidget(self.ai_radio)
        type_layout.addStretch()
        
        layout.addLayout(type_layout)
        
        # AI难度选择（初始隐藏）
        self.ai_settings_frame = QFrame()
        ai_settings_layout = QHBoxLayout()
        
        difficulty_label = QLabel("AI难度:")
        difficulty_label.setFont(QFont("SimHei", 10))
        
        self.ai_difficulty_combo = QComboBox()
        self.ai_difficulty_combo.setFont(QFont("SimHei", 10))
        self.ai_difficulty_combo.addItem("简单", "easy")
        self.ai_difficulty_combo.addItem("普通", "normal")
        self.ai_difficulty_combo.addItem("困难", "hard")
        self.ai_difficulty_combo.setCurrentIndex(1)  # 默认普通难度
        
        ai_settings_layout.addWidget(difficulty_label)
        ai_settings_layout.addWidget(self.ai_difficulty_combo)
        ai_settings_layout.addStretch()
        
        self.ai_settings_frame.setLayout(ai_settings_layout)
        self.ai_settings_frame.setVisible(False)
        
        layout.addWidget(self.ai_settings_frame)
        
        # 武将选择
        character_layout = QHBoxLayout()
        character_label = QLabel("选择武将:")
        character_label.setFont(QFont("SimHei", 10))
        
        self.player2_character_combo = QComboBox()
        self.player2_character_combo.setFont(QFont("SimHei", 10))
        for char in self.available_characters:
            self.player2_character_combo.addItem(f"{char.name} ({char.kingdom}) - {char.hp}血", char)
        
        # 默认选择不同的武将
        if len(self.available_characters) > 1:
            self.player2_character_combo.setCurrentIndex(1)
        
        character_layout.addWidget(character_label)
        character_layout.addWidget(self.player2_character_combo)
        character_layout.addStretch()
        
        layout.addLayout(character_layout)
        
        # AI状态提示
        self.ai_status_label = QLabel()
        self.ai_status_label.setFont(QFont("SimHei", 9))
        self.update_ai_status()
        layout.addWidget(self.ai_status_label)
        
        group.setLayout(layout)
        return group
        
    def on_player_type_changed(self):
        """玩家类型改变时的处理"""
        if self.ai_radio.isChecked():
            self.player2_type = "ai"
            self.ai_settings_frame.setVisible(True)
        else:
            self.player2_type = "human"
            self.ai_settings_frame.setVisible(False)
            
        self.update_ai_status()
        
    def update_ai_status(self):
        """更新AI状态显示"""
        if self.player2_type == "ai":
            if self.ai_manager and self.ai_manager.is_initialized:
                self.ai_status_label.setText("✓ AI系统已就绪")
                self.ai_status_label.setStyleSheet("color: green;")
                self.start_button.setEnabled(True)
            else:
                self.ai_status_label.setText("⚠ AI系统未初始化，将使用简单AI")
                self.ai_status_label.setStyleSheet("color: orange;")
                self.start_button.setEnabled(True)
        else:
            self.ai_status_label.setText("等待第二个玩家加入...")
            self.ai_status_label.setStyleSheet("color: blue;")
            self.start_button.setEnabled(True)
            
    def start_game(self):
        """开始游戏"""
        # 获取选择的武将
        self.player1_character = self.player1_character_combo.currentData()
        self.player2_character = self.player2_character_combo.currentData()
        
        # 检查是否选择了相同的武将
        if self.player1_character.name == self.player2_character.name:
            QMessageBox.warning(self, "警告", "两个玩家不能选择相同的武将！")
            return
            
        # 获取AI难度
        if self.player2_type == "ai":
            self.ai_difficulty = self.ai_difficulty_combo.currentData()
            
        # 接受对话框
        self.accept()
        
    def get_game_settings(self):
        """获取游戏设置"""
        return {
            'player1_character': self.player1_character,
            'player2_character': self.player2_character,
            'player2_type': self.player2_type,
            'ai_difficulty': self.ai_difficulty if self.player2_type == "ai" else None
        }