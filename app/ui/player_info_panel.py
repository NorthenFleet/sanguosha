#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
玩家信息显示面板
提供详细的玩家状态、技能、装备等信息显示
"""

import sys
import os
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
                             QPushButton, QLabel, QFrame, QScrollArea,
                             QProgressBar, QGroupBox, QListWidget, QListWidgetItem,
                             QTextEdit, QTabWidget, QTableWidget, QTableWidgetItem,
                             QHeaderView, QSplitter, QToolTip)
from PyQt5.QtCore import Qt, pyqtSignal, QTimer, QPoint, QSize
from PyQt5.QtGui import QFont, QPixmap, QIcon, QPalette, QColor, QPainter, QBrush
from typing import Dict, List, Optional, Any

# 导入游戏相关模块
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from app.models.player import Player
from app.models.character import Character
from app.models.card import Card


class SkillWidget(QFrame):
    """技能显示组件"""
    
    skill_activated = pyqtSignal(str)  # 技能激活信号
    
    def __init__(self, skill_name: str, skill_description: str, 
                 skill_type: str = "主动", usable: bool = True):
        super().__init__()
        self.skill_name = skill_name
        self.skill_description = skill_description
        self.skill_type = skill_type
        self.usable = usable
        self.init_ui()
        
    def init_ui(self):
        """初始化技能UI"""
        self.setFrameStyle(QFrame.Box)
        self.setLineWidth(1)
        self.setFixedHeight(80)
        
        layout = QVBoxLayout()
        layout.setContentsMargins(8, 5, 8, 5)
        
        # 技能名称和类型
        header_layout = QHBoxLayout()
        
        name_label = QLabel(self.skill_name)
        name_label.setFont(QFont("SimHei", 10, QFont.Bold))
        
        type_label = QLabel(f"[{self.skill_type}]")
        type_label.setFont(QFont("SimHei", 8))
        type_label.setStyleSheet("color: #666666;")
        
        header_layout.addWidget(name_label)
        header_layout.addWidget(type_label)
        header_layout.addStretch()
        
        # 技能描述
        desc_label = QLabel(self.skill_description)
        desc_label.setFont(QFont("SimHei", 8))
        desc_label.setWordWrap(True)
        desc_label.setAlignment(Qt.AlignTop)
        
        layout.addLayout(header_layout)
        layout.addWidget(desc_label)
        
        self.setLayout(layout)
        self.update_style()
        
    def update_style(self):
        """更新技能样式"""
        if self.usable:
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
            """)
        else:
            self.setStyleSheet("""
                QFrame {
                    background-color: #F5F5F5;
                    border: 2px solid #D3D3D3;
                    border-radius: 8px;
                }
            """)
            
    def mousePressEvent(self, event):
        """鼠标点击事件"""
        if self.usable and event.button() == Qt.LeftButton:
            self.skill_activated.emit(self.skill_name)
            
    def set_usable(self, usable: bool):
        """设置技能可用状态"""
        self.usable = usable
        self.update_style()


class EquipmentSlotWidget(QFrame):
    """装备槽组件"""
    
    equipment_clicked = pyqtSignal(str, object)  # 装备类型, 装备卡牌
    
    def __init__(self, slot_type: str, equipment: Card = None):
        super().__init__()
        self.slot_type = slot_type
        self.equipment = equipment
        self.init_ui()
        
    def init_ui(self):
        """初始化装备槽UI"""
        self.setFixedSize(100, 120)
        self.setFrameStyle(QFrame.Box)
        self.setLineWidth(2)
        
        layout = QVBoxLayout()
        layout.setContentsMargins(5, 5, 5, 5)
        
        # 装备槽类型标签
        type_label = QLabel(self.slot_type)
        type_label.setFont(QFont("SimHei", 8, QFont.Bold))
        type_label.setAlignment(Qt.AlignCenter)
        
        if self.equipment:
            # 装备名称
            name_label = QLabel(self.equipment.name)
            name_label.setFont(QFont("SimHei", 9, QFont.Bold))
            name_label.setAlignment(Qt.AlignCenter)
            name_label.setWordWrap(True)
            
            # 装备效果
            if hasattr(self.equipment, 'effect') and self.equipment.effect:
                effect_label = QLabel(self.equipment.effect[:15] + "..." if len(self.equipment.effect) > 15 else self.equipment.effect)
                effect_label.setFont(QFont("SimHei", 7))
                effect_label.setAlignment(Qt.AlignCenter)
                effect_label.setWordWrap(True)
                layout.addWidget(effect_label)
            
            layout.addWidget(name_label)
        else:
            # 空装备槽
            empty_label = QLabel("无装备")
            empty_label.setFont(QFont("SimHei", 8))
            empty_label.setAlignment(Qt.AlignCenter)
            empty_label.setStyleSheet("color: #A9A9A9;")
            layout.addWidget(empty_label)
        
        layout.insertWidget(0, type_label)
        layout.addStretch()
        
        self.setLayout(layout)
        self.update_style()
        
    def update_style(self):
        """更新装备槽样式"""
        if self.equipment:
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
            """)
        else:
            self.setStyleSheet("""
                QFrame {
                    background-color: #F8F8FF;
                    border: 2px dashed #D3D3D3;
                    border-radius: 8px;
                }
            """)
            
    def mousePressEvent(self, event):
        """鼠标点击事件"""
        if event.button() == Qt.LeftButton:
            self.equipment_clicked.emit(self.slot_type, self.equipment)
            
    def set_equipment(self, equipment: Card):
        """设置装备"""
        self.equipment = equipment
        # 重新初始化UI
        for i in reversed(range(self.layout().count())):
            self.layout().itemAt(i).widget().setParent(None)
        self.init_ui()


class StatusEffectWidget(QFrame):
    """状态效果组件"""
    
    def __init__(self, effect_name: str, effect_description: str, 
                 duration: int = -1, effect_type: str = "buff"):
        super().__init__()
        self.effect_name = effect_name
        self.effect_description = effect_description
        self.duration = duration
        self.effect_type = effect_type
        self.init_ui()
        
    def init_ui(self):
        """初始化状态效果UI"""
        self.setFixedSize(80, 60)
        self.setFrameStyle(QFrame.Box)
        self.setLineWidth(1)
        
        layout = QVBoxLayout()
        layout.setContentsMargins(3, 3, 3, 3)
        
        # 效果名称
        name_label = QLabel(self.effect_name)
        name_label.setFont(QFont("SimHei", 8, QFont.Bold))
        name_label.setAlignment(Qt.AlignCenter)
        
        # 持续时间
        if self.duration > 0:
            duration_label = QLabel(f"{self.duration}回合")
            duration_label.setFont(QFont("SimHei", 7))
            duration_label.setAlignment(Qt.AlignCenter)
            layout.addWidget(duration_label)
        
        layout.addWidget(name_label)
        layout.addStretch()
        
        self.setLayout(layout)
        self.update_style()
        
        # 设置工具提示
        self.setToolTip(self.effect_description)
        
    def update_style(self):
        """更新状态效果样式"""
        if self.effect_type == "buff":
            self.setStyleSheet("""
                QFrame {
                    background-color: #90EE90;
                    border: 2px solid #32CD32;
                    border-radius: 5px;
                }
            """)
        elif self.effect_type == "debuff":
            self.setStyleSheet("""
                QFrame {
                    background-color: #FFB6C1;
                    border: 2px solid #FF69B4;
                    border-radius: 5px;
                }
            """)
        else:
            self.setStyleSheet("""
                QFrame {
                    background-color: #F0E68C;
                    border: 2px solid #DAA520;
                    border-radius: 5px;
                }
            """)


class PlayerInfoPanel(QWidget):
    """玩家信息面板"""
    
    skill_used = pyqtSignal(str)  # 技能使用信号
    equipment_clicked = pyqtSignal(str, object)  # 装备点击信号
    
    def __init__(self, player: Player = None, detailed: bool = True):
        super().__init__()
        self.player = player
        self.detailed = detailed
        self.skill_widgets = []
        self.equipment_widgets = {}
        self.status_widgets = []
        self.init_ui()
        
    def init_ui(self):
        """初始化玩家信息面板UI"""
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(10, 10, 10, 10)
        
        if not self.player:
            # 空状态显示
            empty_label = QLabel("暂无玩家信息")
            empty_label.setAlignment(Qt.AlignCenter)
            empty_label.setFont(QFont("SimHei", 14))
            empty_label.setStyleSheet("color: #A9A9A9;")
            main_layout.addWidget(empty_label)
            self.setLayout(main_layout)
            return
        
        # 玩家基本信息
        self.create_basic_info_section(main_layout)
        
        if self.detailed:
            # 创建标签页
            tab_widget = QTabWidget()
            tab_widget.setFont(QFont("SimHei", 10))
            
            # 技能标签页
            skills_tab = self.create_skills_tab()
            tab_widget.addTab(skills_tab, "技能")
            
            # 装备标签页
            equipment_tab = self.create_equipment_tab()
            tab_widget.addTab(equipment_tab, "装备")
            
            # 状态标签页
            status_tab = self.create_status_tab()
            tab_widget.addTab(status_tab, "状态")
            
            # 历史标签页
            history_tab = self.create_history_tab()
            tab_widget.addTab(history_tab, "历史")
            
            main_layout.addWidget(tab_widget)
        
        self.setLayout(main_layout)
        
        # 设置面板样式
        self.setStyleSheet("""
            QWidget {
                background-color: #FFF8DC;
            }
            QTabWidget::pane {
                border: 2px solid #8B4513;
                border-radius: 5px;
                background-color: #FFFEF7;
            }
            QTabWidget::tab-bar {
                alignment: center;
            }
            QTabBar::tab {
                background-color: #F5F5DC;
                border: 2px solid #8B4513;
                border-bottom: none;
                border-radius: 5px 5px 0 0;
                padding: 8px 16px;
                margin-right: 2px;
            }
            QTabBar::tab:selected {
                background-color: #FFFEF7;
                border-bottom: 2px solid #FFFEF7;
            }
            QTabBar::tab:hover {
                background-color: #FFFACD;
            }
        """)
        
    def create_basic_info_section(self, parent_layout):
        """创建基本信息区域"""
        basic_info_frame = QFrame()
        basic_info_frame.setFrameStyle(QFrame.Box)
        basic_info_frame.setLineWidth(2)
        basic_info_frame.setStyleSheet("""
            QFrame {
                background-color: #F0F8FF;
                border: 2px solid #4169E1;
                border-radius: 10px;
                padding: 10px;
            }
        """)
        
        layout = QVBoxLayout()
        
        # 玩家名称和角色
        name_layout = QHBoxLayout()
        
        name_label = QLabel(self.player.name)
        name_label.setFont(QFont("SimHei", 16, QFont.Bold))
        
        character_label = QLabel(f"({self.player.character.name})" if self.player.character else "(无角色)")
        character_label.setFont(QFont("SimHei", 12))
        character_label.setStyleSheet("color: #666666;")
        
        name_layout.addWidget(name_label)
        name_layout.addWidget(character_label)
        name_layout.addStretch()
        
        # 血量显示
        hp_layout = QHBoxLayout()
        
        hp_label = QLabel("血量:")
        hp_label.setFont(QFont("SimHei", 12))
        
        self.hp_bar = QProgressBar()
        self.hp_bar.setMaximum(self.player.max_hp)
        self.hp_bar.setValue(self.player.hp)
        self.hp_bar.setFormat(f"{self.player.hp}/{self.player.max_hp}")
        self.hp_bar.setStyleSheet("""
            QProgressBar {
                border: 2px solid #8B4513;
                border-radius: 8px;
                text-align: center;
                font-weight: bold;
                height: 25px;
            }
            QProgressBar::chunk {
                background-color: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #FF6B6B, stop:0.5 #FF8E8E, stop:1 #FFB1B1);
                border-radius: 6px;
            }
        """)
        
        hp_layout.addWidget(hp_label)
        hp_layout.addWidget(self.hp_bar, 1)
        
        # 其他信息
        info_layout = QGridLayout()
        
        # 手牌数量
        hand_label = QLabel("手牌:")
        hand_value = QLabel(f"{len(self.player.hand_cards)}张")
        hand_value.setFont(QFont("SimHei", 11, QFont.Bold))
        
        # 体力值（如果与血量不同）
        if hasattr(self.player, 'stamina') and self.player.stamina != self.player.hp:
            stamina_label = QLabel("体力:")
            stamina_value = QLabel(f"{self.player.stamina}")
            stamina_value.setFont(QFont("SimHei", 11, QFont.Bold))
            info_layout.addWidget(stamina_label, 0, 2)
            info_layout.addWidget(stamina_value, 0, 3)
        
        # 攻击范围
        if hasattr(self.player, 'attack_range'):
            range_label = QLabel("攻击范围:")
            range_value = QLabel(f"{self.player.attack_range}")
            range_value.setFont(QFont("SimHei", 11, QFont.Bold))
            info_layout.addWidget(range_label, 1, 0)
            info_layout.addWidget(range_value, 1, 1)
        
        info_layout.addWidget(hand_label, 0, 0)
        info_layout.addWidget(hand_value, 0, 1)
        
        layout.addLayout(name_layout)
        layout.addLayout(hp_layout)
        layout.addLayout(info_layout)
        
        basic_info_frame.setLayout(layout)
        parent_layout.addWidget(basic_info_frame)
        
    def create_skills_tab(self):
        """创建技能标签页"""
        skills_widget = QWidget()
        layout = QVBoxLayout()
        
        # 技能列表
        skills_scroll = QScrollArea()
        skills_scroll.setWidgetResizable(True)
        
        skills_content = QWidget()
        skills_layout = QVBoxLayout()
        
        # 添加角色技能
        if self.player.character and hasattr(self.player.character, 'skills'):
            for skill_name, skill_info in self.player.character.skills.items():
                skill_widget = SkillWidget(
                    skill_name=skill_name,
                    skill_description=skill_info.get('description', ''),
                    skill_type=skill_info.get('type', '主动'),
                    usable=skill_info.get('usable', True)
                )
                skill_widget.skill_activated.connect(self.skill_used.emit)
                self.skill_widgets.append(skill_widget)
                skills_layout.addWidget(skill_widget)
        
        # 如果没有技能
        if not self.skill_widgets:
            no_skills_label = QLabel("该角色暂无特殊技能")
            no_skills_label.setAlignment(Qt.AlignCenter)
            no_skills_label.setFont(QFont("SimHei", 12))
            no_skills_label.setStyleSheet("color: #A9A9A9; padding: 20px;")
            skills_layout.addWidget(no_skills_label)
        
        skills_layout.addStretch()
        skills_content.setLayout(skills_layout)
        skills_scroll.setWidget(skills_content)
        
        layout.addWidget(skills_scroll)
        skills_widget.setLayout(layout)
        
        return skills_widget
        
    def create_equipment_tab(self):
        """创建装备标签页"""
        equipment_widget = QWidget()
        layout = QVBoxLayout()
        
        # 装备区域
        equipment_layout = QGridLayout()
        
        # 装备槽类型
        equipment_types = [
            ("武器", "weapon_equipment"),
            ("防具", "armor_equipment"), 
            ("坐骑", "mount_equipment"),
            ("宝物", "treasure_equipment")
        ]
        
        for i, (slot_name, slot_attr) in enumerate(equipment_types):
            equipment = getattr(self.player, slot_attr, None)
            slot_widget = EquipmentSlotWidget(slot_name, equipment)
            slot_widget.equipment_clicked.connect(self.equipment_clicked.emit)
            self.equipment_widgets[slot_attr] = slot_widget
            
            row = i // 2
            col = i % 2
            equipment_layout.addWidget(slot_widget, row, col)
        
        # 装备效果说明
        effect_group = QGroupBox("装备效果")
        effect_group.setFont(QFont("SimHei", 10, QFont.Bold))
        effect_layout = QVBoxLayout()
        
        self.equipment_effects_text = QTextEdit()
        self.equipment_effects_text.setReadOnly(True)
        self.equipment_effects_text.setMaximumHeight(100)
        self.equipment_effects_text.setFont(QFont("SimHei", 9))
        self.update_equipment_effects()
        
        effect_layout.addWidget(self.equipment_effects_text)
        effect_group.setLayout(effect_layout)
        
        layout.addLayout(equipment_layout)
        layout.addWidget(effect_group)
        layout.addStretch()
        
        equipment_widget.setLayout(layout)
        return equipment_widget
        
    def create_status_tab(self):
        """创建状态标签页"""
        status_widget = QWidget()
        layout = QVBoxLayout()
        
        # 状态效果区域
        status_scroll = QScrollArea()
        status_scroll.setWidgetResizable(True)
        status_scroll.setMaximumHeight(200)
        
        status_content = QWidget()
        status_layout = QHBoxLayout()
        status_layout.setAlignment(Qt.AlignLeft)
        
        # 添加状态效果（示例）
        if hasattr(self.player, 'status_effects'):
            for effect_name, effect_info in self.player.status_effects.items():
                status_effect = StatusEffectWidget(
                    effect_name=effect_name,
                    effect_description=effect_info.get('description', ''),
                    duration=effect_info.get('duration', -1),
                    effect_type=effect_info.get('type', 'neutral')
                )
                self.status_widgets.append(status_effect)
                status_layout.addWidget(status_effect)
        
        if not self.status_widgets:
            no_status_label = QLabel("当前无状态效果")
            no_status_label.setAlignment(Qt.AlignCenter)
            no_status_label.setFont(QFont("SimHei", 12))
            no_status_label.setStyleSheet("color: #A9A9A9; padding: 20px;")
            status_layout.addWidget(no_status_label)
        
        status_content.setLayout(status_layout)
        status_scroll.setWidget(status_content)
        
        # 状态统计
        stats_group = QGroupBox("状态统计")
        stats_group.setFont(QFont("SimHei", 10, QFont.Bold))
        stats_layout = QGridLayout()
        
        # 各种统计信息
        stats_info = [
            ("出牌次数", getattr(self.player, 'cards_played', 0)),
            ("造成伤害", getattr(self.player, 'damage_dealt', 0)),
            ("受到伤害", getattr(self.player, 'damage_taken', 0)),
            ("回复血量", getattr(self.player, 'hp_recovered', 0))
        ]
        
        for i, (stat_name, stat_value) in enumerate(stats_info):
            name_label = QLabel(f"{stat_name}:")
            value_label = QLabel(str(stat_value))
            value_label.setFont(QFont("SimHei", 10, QFont.Bold))
            
            row = i // 2
            col = (i % 2) * 2
            stats_layout.addWidget(name_label, row, col)
            stats_layout.addWidget(value_label, row, col + 1)
        
        stats_group.setLayout(stats_layout)
        
        layout.addWidget(status_scroll)
        layout.addWidget(stats_group)
        layout.addStretch()
        
        status_widget.setLayout(layout)
        return status_widget
        
    def create_history_tab(self):
        """创建历史标签页"""
        history_widget = QWidget()
        layout = QVBoxLayout()
        
        # 操作历史
        history_text = QTextEdit()
        history_text.setReadOnly(True)
        history_text.setFont(QFont("Consolas", 9))
        
        # 添加示例历史记录
        if hasattr(self.player, 'action_history'):
            for action in self.player.action_history:
                history_text.append(action)
        else:
            history_text.append("暂无操作历史")
        
        layout.addWidget(history_text)
        history_widget.setLayout(layout)
        
        return history_widget
        
    def update_equipment_effects(self):
        """更新装备效果显示"""
        effects = []
        
        equipment_attrs = ["weapon_equipment", "armor_equipment", "mount_equipment", "treasure_equipment"]
        for attr in equipment_attrs:
            equipment = getattr(self.player, attr, None)
            if equipment and hasattr(equipment, 'effect'):
                effects.append(f"• {equipment.name}: {equipment.effect}")
        
        if effects:
            self.equipment_effects_text.setPlainText("\n".join(effects))
        else:
            self.equipment_effects_text.setPlainText("当前无装备效果")
            
    def update_player_info(self, player: Player):
        """更新玩家信息"""
        self.player = player
        
        # 更新血量
        if hasattr(self, 'hp_bar'):
            self.hp_bar.setMaximum(player.max_hp)
            self.hp_bar.setValue(player.hp)
            self.hp_bar.setFormat(f"{player.hp}/{player.max_hp}")
        
        # 更新装备
        self.update_equipment_effects()
        
        # 重新初始化UI（如果需要）
        # self.init_ui()
        
    def set_current_player(self, is_current: bool):
        """设置是否为当前玩家"""
        if is_current:
            self.setStyleSheet(self.styleSheet() + """
                QWidget {
                    border: 3px solid #FFD700;
                }
            """)
        else:
            # 移除当前玩家样式
            style = self.styleSheet()
            style = style.replace("border: 3px solid #FFD700;", "")
            self.setStyleSheet(style)