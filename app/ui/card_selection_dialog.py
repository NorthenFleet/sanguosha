#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
卡牌选择对话框
用于各种需要选择卡牌的场景，如技能使用、目标选择等
"""

import sys
import os
from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QGridLayout,
                             QPushButton, QLabel, QFrame, QScrollArea,
                             QButtonGroup, QCheckBox, QRadioButton, QGroupBox,
                             QDialogButtonBox, QMessageBox, QSpinBox, QComboBox)
from PyQt5.QtCore import Qt, pyqtSignal, QSize
from PyQt5.QtGui import QFont, QPixmap, QIcon
from typing import List, Dict, Optional, Callable

# 导入游戏相关模块
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from app.models.card import Card
from app.models.player import Player


class SelectableCardWidget(QFrame):
    """可选择的卡牌组件"""
    
    selection_changed = pyqtSignal(object, bool)  # 卡牌, 是否选中
    
    def __init__(self, card: Card, selectable: bool = True, multi_select: bool = True):
        super().__init__()
        self.card = card
        self.selectable = selectable
        self.multi_select = multi_select
        self.selected = False
        self.init_ui()
        
    def init_ui(self):
        """初始化卡牌UI"""
        self.setFixedSize(100, 140)
        self.setFrameStyle(QFrame.Box)
        self.setLineWidth(2)
        
        layout = QVBoxLayout()
        layout.setContentsMargins(8, 8, 8, 8)
        
        # 选择框
        if self.selectable:
            if self.multi_select:
                self.select_checkbox = QCheckBox()
            else:
                self.select_checkbox = QRadioButton()
            self.select_checkbox.stateChanged.connect(self.on_selection_changed)
            layout.addWidget(self.select_checkbox)
        
        # 卡牌名称
        name_label = QLabel(self.card.name)
        name_label.setFont(QFont("SimHei", 9, QFont.Bold))
        name_label.setAlignment(Qt.AlignCenter)
        name_label.setWordWrap(True)
        
        # 卡牌花色和点数
        suit_point = QLabel(f"{self.card.suit} {self.card.point}")
        suit_point.setFont(QFont("SimHei", 8))
        suit_point.setAlignment(Qt.AlignCenter)
        
        # 卡牌类型
        type_label = QLabel(self.card.card_type)
        type_label.setFont(QFont("SimHei", 7))
        type_label.setAlignment(Qt.AlignCenter)
        
        # 卡牌描述（如果有）
        if hasattr(self.card, 'description') and self.card.description:
            desc_label = QLabel(self.card.description[:20] + "..." if len(self.card.description) > 20 else self.card.description)
            desc_label.setFont(QFont("SimHei", 6))
            desc_label.setAlignment(Qt.AlignCenter)
            desc_label.setWordWrap(True)
            layout.addWidget(desc_label)
        
        layout.addWidget(name_label)
        layout.addWidget(suit_point)
        layout.addStretch()
        layout.addWidget(type_label)
        
        self.setLayout(layout)
        self.update_style()
        
    def update_style(self):
        """更新卡牌样式"""
        if not self.selectable:
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
        elif self.selected:
            self.setStyleSheet("""
                QFrame {
                    background-color: #FFD700;
                    border: 3px solid #FF6347;
                    border-radius: 8px;
                }
                QLabel {
                    color: #8B4513;
                    font-weight: bold;
                }
            """)
        else:
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
            
    def on_selection_changed(self, state):
        """选择状态改变"""
        self.selected = bool(state)
        self.update_style()
        self.selection_changed.emit(self.card, self.selected)
        
    def set_selected(self, selected: bool):
        """设置选中状态"""
        if self.selectable:
            self.select_checkbox.setChecked(selected)


class PlayerSelectionWidget(QFrame):
    """玩家选择组件"""
    
    selection_changed = pyqtSignal(object, bool)  # 玩家, 是否选中
    
    def __init__(self, player: Player, selectable: bool = True, multi_select: bool = False):
        super().__init__()
        self.player = player
        self.selectable = selectable
        self.multi_select = multi_select
        self.selected = False
        self.init_ui()
        
    def init_ui(self):
        """初始化玩家选择UI"""
        self.setFixedSize(200, 120)
        self.setFrameStyle(QFrame.Box)
        self.setLineWidth(2)
        
        layout = QVBoxLayout()
        layout.setContentsMargins(10, 10, 10, 10)
        
        # 选择框
        if self.selectable:
            if self.multi_select:
                self.select_checkbox = QCheckBox()
            else:
                self.select_checkbox = QRadioButton()
            self.select_checkbox.stateChanged.connect(self.on_selection_changed)
            layout.addWidget(self.select_checkbox)
        
        # 玩家信息
        name_layout = QHBoxLayout()
        name_label = QLabel(self.player.name)
        name_label.setFont(QFont("SimHei", 12, QFont.Bold))
        
        character_label = QLabel(f"({self.player.character.name})" if self.player.character else "")
        character_label.setFont(QFont("SimHei", 10))
        
        name_layout.addWidget(name_label)
        name_layout.addWidget(character_label)
        name_layout.addStretch()
        
        # 血量信息
        hp_label = QLabel(f"血量: {self.player.hp}/{self.player.max_hp}")
        hp_label.setFont(QFont("SimHei", 10))
        
        # 手牌数量
        hand_label = QLabel(f"手牌: {len(self.player.hand_cards)}张")
        hand_label.setFont(QFont("SimHei", 10))
        
        layout.addLayout(name_layout)
        layout.addWidget(hp_label)
        layout.addWidget(hand_label)
        layout.addStretch()
        
        self.setLayout(layout)
        self.update_style()
        
    def update_style(self):
        """更新样式"""
        if not self.selectable:
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
        elif self.selected:
            self.setStyleSheet("""
                QFrame {
                    background-color: #FFB6C1;
                    border: 3px solid #FF1493;
                    border-radius: 8px;
                }
                QLabel {
                    color: #8B0000;
                    font-weight: bold;
                }
            """)
        else:
            self.setStyleSheet("""
                QFrame {
                    background-color: #F0F8FF;
                    border: 2px solid #4169E1;
                    border-radius: 8px;
                }
                QFrame:hover {
                    background-color: #E6F3FF;
                    border-color: #1E90FF;
                }
                QLabel {
                    color: #191970;
                }
            """)
            
    def on_selection_changed(self, state):
        """选择状态改变"""
        self.selected = bool(state)
        self.update_style()
        self.selection_changed.emit(self.player, self.selected)
        
    def set_selected(self, selected: bool):
        """设置选中状态"""
        if self.selectable:
            self.select_checkbox.setChecked(selected)


class CardSelectionDialog(QDialog):
    """卡牌选择对话框"""
    
    def __init__(self, title: str = "选择卡牌", 
                 cards: List[Card] = None,
                 players: List[Player] = None,
                 min_select: int = 0,
                 max_select: int = 1,
                 multi_select: bool = False,
                 show_players: bool = False,
                 instruction: str = "",
                 parent=None):
        super().__init__(parent)
        
        self.title = title
        self.cards = cards or []
        self.players = players or []
        self.min_select = min_select
        self.max_select = max_select
        self.multi_select = multi_select
        self.show_players = show_players
        self.instruction = instruction
        
        self.selected_cards = []
        self.selected_players = []
        self.card_widgets = []
        self.player_widgets = []
        
        self.init_ui()
        self.setup_connections()
        
    def init_ui(self):
        """初始化对话框UI"""
        self.setWindowTitle(self.title)
        self.setModal(True)
        self.resize(800, 600)
        
        layout = QVBoxLayout()
        
        # 说明文字
        if self.instruction:
            instruction_label = QLabel(self.instruction)
            instruction_label.setFont(QFont("SimHei", 12))
            instruction_label.setAlignment(Qt.AlignCenter)
            instruction_label.setWordWrap(True)
            instruction_label.setStyleSheet("""
                QLabel {
                    background-color: #FFFACD;
                    border: 2px solid #DAA520;
                    border-radius: 8px;
                    padding: 10px;
                    margin: 10px;
                    color: #8B4513;
                }
            """)
            layout.addWidget(instruction_label)
        
        # 选择计数器
        counter_layout = QHBoxLayout()
        
        self.counter_label = QLabel(f"已选择: 0")
        self.counter_label.setFont(QFont("SimHei", 11, QFont.Bold))
        
        if self.max_select > 1:
            limit_label = QLabel(f"(最多选择 {self.max_select} 项)")
            limit_label.setFont(QFont("SimHei", 10))
            limit_label.setStyleSheet("color: #666666;")
            counter_layout.addWidget(limit_label)
        
        counter_layout.addWidget(self.counter_label)
        counter_layout.addStretch()
        
        layout.addLayout(counter_layout)
        
        # 创建滚动区域
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setMinimumHeight(400)
        
        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout()
        
        # 卡牌选择区域
        if self.cards:
            cards_group = QGroupBox("选择卡牌")
            cards_group.setFont(QFont("SimHei", 11, QFont.Bold))
            cards_layout = QGridLayout()
            
            cols = 6  # 每行显示6张卡牌
            for i, card in enumerate(self.cards):
                row = i // cols
                col = i % cols
                
                card_widget = SelectableCardWidget(
                    card, 
                    selectable=True, 
                    multi_select=self.multi_select
                )
                card_widget.selection_changed.connect(self.on_card_selection_changed)
                self.card_widgets.append(card_widget)
                
                cards_layout.addWidget(card_widget, row, col)
            
            cards_group.setLayout(cards_layout)
            scroll_layout.addWidget(cards_group)
        
        # 玩家选择区域
        if self.show_players and self.players:
            players_group = QGroupBox("选择目标玩家")
            players_group.setFont(QFont("SimHei", 11, QFont.Bold))
            players_layout = QGridLayout()
            
            cols = 3  # 每行显示3个玩家
            for i, player in enumerate(self.players):
                row = i // cols
                col = i % cols
                
                player_widget = PlayerSelectionWidget(
                    player,
                    selectable=True,
                    multi_select=self.multi_select
                )
                player_widget.selection_changed.connect(self.on_player_selection_changed)
                self.player_widgets.append(player_widget)
                
                players_layout.addWidget(player_widget, row, col)
            
            players_group.setLayout(players_layout)
            scroll_layout.addWidget(players_group)
        
        scroll_widget.setLayout(scroll_layout)
        scroll_area.setWidget(scroll_widget)
        layout.addWidget(scroll_area)
        
        # 按钮区域
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.button(QDialogButtonBox.Ok).setText("确定")
        button_box.button(QDialogButtonBox.Cancel).setText("取消")
        button_box.button(QDialogButtonBox.Ok).setFont(QFont("SimHei", 10))
        button_box.button(QDialogButtonBox.Cancel).setFont(QFont("SimHei", 10))
        
        # 设置按钮样式
        button_box.setStyleSheet("""
            QPushButton {
                background-color: #F0E68C;
                border: 2px solid #DAA520;
                border-radius: 5px;
                padding: 8px 16px;
                color: #8B4513;
                font-weight: bold;
                min-width: 80px;
            }
            QPushButton:hover {
                background-color: #FFD700;
            }
            QPushButton:pressed {
                background-color: #DAA520;
            }
        """)
        
        self.ok_button = button_box.button(QDialogButtonBox.Ok)
        self.ok_button.setEnabled(self.min_select == 0)
        
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        
        layout.addWidget(button_box)
        self.setLayout(layout)
        
        # 设置对话框样式
        self.setStyleSheet("""
            QDialog {
                background-color: #FFF8DC;
            }
            QGroupBox {
                font-weight: bold;
                border: 2px solid #8B4513;
                border-radius: 8px;
                margin-top: 15px;
                padding-top: 15px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 15px;
                padding: 0 8px 0 8px;
                background-color: #FFF8DC;
            }
        """)
        
    def setup_connections(self):
        """设置信号连接"""
        # 如果是单选模式，需要设置按钮组
        if not self.multi_select:
            if self.card_widgets:
                self.card_button_group = QButtonGroup()
                for widget in self.card_widgets:
                    if hasattr(widget, 'select_checkbox'):
                        self.card_button_group.addButton(widget.select_checkbox)
            
            if self.player_widgets:
                self.player_button_group = QButtonGroup()
                for widget in self.player_widgets:
                    if hasattr(widget, 'select_checkbox'):
                        self.player_button_group.addButton(widget.select_checkbox)
    
    def on_card_selection_changed(self, card: Card, selected: bool):
        """卡牌选择状态改变"""
        if selected:
            if card not in self.selected_cards:
                # 检查是否超过最大选择数量
                if len(self.selected_cards) >= self.max_select:
                    # 如果是单选，清除之前的选择
                    if self.max_select == 1:
                        for widget in self.card_widgets:
                            if widget.card != card and widget.selected:
                                widget.set_selected(False)
                        self.selected_cards.clear()
                    else:
                        # 多选时提示已达上限
                        QMessageBox.warning(self, "提示", f"最多只能选择 {self.max_select} 张卡牌！")
                        # 取消当前选择
                        for widget in self.card_widgets:
                            if widget.card == card:
                                widget.set_selected(False)
                        return
                
                self.selected_cards.append(card)
        else:
            if card in self.selected_cards:
                self.selected_cards.remove(card)
        
        self.update_counter()
    
    def on_player_selection_changed(self, player: Player, selected: bool):
        """玩家选择状态改变"""
        if selected:
            if player not in self.selected_players:
                # 检查是否超过最大选择数量
                if len(self.selected_players) >= self.max_select:
                    # 如果是单选，清除之前的选择
                    if self.max_select == 1:
                        for widget in self.player_widgets:
                            if widget.player != player and widget.selected:
                                widget.set_selected(False)
                        self.selected_players.clear()
                    else:
                        # 多选时提示已达上限
                        QMessageBox.warning(self, "提示", f"最多只能选择 {self.max_select} 个目标！")
                        # 取消当前选择
                        for widget in self.player_widgets:
                            if widget.player == player:
                                widget.set_selected(False)
                        return
                
                self.selected_players.append(player)
        else:
            if player in self.selected_players:
                self.selected_players.remove(player)
        
        self.update_counter()
    
    def update_counter(self):
        """更新选择计数器"""
        total_selected = len(self.selected_cards) + len(self.selected_players)
        self.counter_label.setText(f"已选择: {total_selected}")
        
        # 更新确定按钮状态
        self.ok_button.setEnabled(
            total_selected >= self.min_select and total_selected <= self.max_select
        )
    
    def get_selected_cards(self) -> List[Card]:
        """获取选中的卡牌"""
        return self.selected_cards.copy()
    
    def get_selected_players(self) -> List[Player]:
        """获取选中的玩家"""
        return self.selected_players.copy()
    
    @staticmethod
    def select_cards(cards: List[Card], 
                    title: str = "选择卡牌",
                    instruction: str = "",
                    min_select: int = 1,
                    max_select: int = 1,
                    parent=None) -> Optional[List[Card]]:
        """静态方法：选择卡牌"""
        dialog = CardSelectionDialog(
            title=title,
            cards=cards,
            min_select=min_select,
            max_select=max_select,
            multi_select=(max_select > 1),
            instruction=instruction,
            parent=parent
        )
        
        if dialog.exec_() == QDialog.Accepted:
            return dialog.get_selected_cards()
        return None
    
    @staticmethod
    def select_players(players: List[Player],
                      title: str = "选择目标",
                      instruction: str = "",
                      min_select: int = 1,
                      max_select: int = 1,
                      parent=None) -> Optional[List[Player]]:
        """静态方法：选择玩家"""
        dialog = CardSelectionDialog(
            title=title,
            players=players,
            min_select=min_select,
            max_select=max_select,
            multi_select=(max_select > 1),
            show_players=True,
            instruction=instruction,
            parent=parent
        )
        
        if dialog.exec_() == QDialog.Accepted:
            return dialog.get_selected_players()
        return None
    
    @staticmethod
    def select_cards_and_players(cards: List[Card],
                                players: List[Player],
                                title: str = "选择卡牌和目标",
                                instruction: str = "",
                                min_select: int = 1,
                                max_select: int = 2,
                                parent=None) -> tuple:
        """静态方法：同时选择卡牌和玩家"""
        dialog = CardSelectionDialog(
            title=title,
            cards=cards,
            players=players,
            min_select=min_select,
            max_select=max_select,
            multi_select=True,
            show_players=True,
            instruction=instruction,
            parent=parent
        )
        
        if dialog.exec_() == QDialog.Accepted:
            return dialog.get_selected_cards(), dialog.get_selected_players()
        return None, None