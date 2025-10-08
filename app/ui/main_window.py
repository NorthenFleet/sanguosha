#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
三国杀游戏主窗口
支持多种游戏模式的选择和切换
"""

import sys
import os
from PyQt5.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                             QPushButton, QLabel, QFrame, QStackedWidget,
                             QMenuBar, QStatusBar, QMessageBox, QApplication,
                             QGridLayout, QGroupBox, QComboBox, QSpinBox)
from PyQt5.QtCore import Qt, pyqtSignal, QTimer, pyqtSlot
from PyQt5.QtWidgets import QAction
from PyQt5.QtGui import QFont, QPixmap, QIcon, QPalette, QColor

# 导入游戏相关模块
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

# 导入游戏界面组件
try:
    from app.ui.game_1vs1_widget import Game1vs1Widget
except ImportError:
    Game1vs1Widget = None

class GameModeSelector(QWidget):
    """游戏模式选择器"""
    
    mode_selected = pyqtSignal(str)  # 模式选择信号
    
    def __init__(self):
        super().__init__()
        self.ai_manager = None  # AI管理器
        self.init_ui()
        
    def init_ui(self):
        """初始化UI"""
        layout = QVBoxLayout()
        
        # 标题
        title = QLabel("三国杀")
        title.setAlignment(Qt.AlignCenter)
        title.setFont(QFont("SimHei", 32, QFont.Bold))
        title.setStyleSheet("color: #8B4513; margin: 20px;")
        
        # 副标题
        subtitle = QLabel("选择游戏模式")
        subtitle.setAlignment(Qt.AlignCenter)
        subtitle.setFont(QFont("SimHei", 16))
        subtitle.setStyleSheet("color: #654321; margin-bottom: 30px;")
        
        # 游戏模式按钮
        modes_layout = QVBoxLayout()
        modes_layout.setSpacing(15)
        
        # 1vs1模式
        vs1_btn = self.create_mode_button(
            "1 vs 1 对战",
            "经典双人对战模式\n快速上手，策略对决",
            "1vs1"
        )
        
        # 国战模式（暂未实现）
        guozhan_btn = self.create_mode_button(
            "国战模式",
            "四大势力混战\n身份隐藏，合纵连横",
            "guozhan",
            enabled=False
        )
        
        # 统帅三军模式（暂未实现）
        commander_btn = self.create_mode_button(
            "统帅三军",
            "大型团战模式\n指挥军团，征战沙场",
            "commander",
            enabled=False
        )
        
        modes_layout.addWidget(vs1_btn)
        modes_layout.addWidget(guozhan_btn)
        modes_layout.addWidget(commander_btn)
        
        # 设置按钮
        settings_btn = QPushButton("游戏设置")
        settings_btn.setFont(QFont("SimHei", 12))
        settings_btn.setStyleSheet("""
            QPushButton {
                background-color: #F5DEB3;
                border: 2px solid #8B4513;
                border-radius: 8px;
                padding: 8px 16px;
                color: #8B4513;
            }
            QPushButton:hover {
                background-color: #DEB887;
            }
        """)
        settings_btn.clicked.connect(self.show_settings)
        
        # 退出按钮
        exit_btn = QPushButton("退出游戏")
        exit_btn.setFont(QFont("SimHei", 12))
        exit_btn.setStyleSheet("""
            QPushButton {
                background-color: #CD853F;
                border: 2px solid #8B4513;
                border-radius: 8px;
                padding: 8px 16px;
                color: black;
            }
            QPushButton:hover {
                background-color: #A0522D;
            }
        """)
        exit_btn.clicked.connect(self.exit_game)
        
        # 布局组装
        layout.addWidget(title)
        layout.addWidget(subtitle)
        layout.addLayout(modes_layout)
        layout.addStretch()
        
        bottom_layout = QHBoxLayout()
        bottom_layout.addWidget(settings_btn)
        bottom_layout.addStretch()
        bottom_layout.addWidget(exit_btn)
        
        layout.addLayout(bottom_layout)
        self.setLayout(layout)
        
        # 设置背景
        self.setStyleSheet("""
            QWidget {
                background-color: #FFF8DC;
            }
        """)
        
    def create_mode_button(self, title: str, description: str, mode: str, enabled: bool = True) -> QPushButton:
        """创建游戏模式按钮"""
        btn = QPushButton()
        btn.setFixedHeight(100)
        btn.setFont(QFont("SimHei", 14, QFont.Bold))
        
        # 设置按钮文本
        btn_text = f"{title}\n{description}"
        if not enabled:
            btn_text += "\n(即将推出)"
        btn.setText(btn_text)
        
        # 设置样式
        if enabled:
            btn.setStyleSheet("""
                QPushButton {
                    background-color: #F0E68C;
                    border: 3px solid #DAA520;
                    border-radius: 15px;
                    padding: 10px;
                    color: #8B4513;
                    text-align: center;
                }
                QPushButton:hover {
                    background-color: #FFD700;
                    border-color: #B8860B;
                }
                QPushButton:pressed {
                    background-color: #DAA520;
                }
            """)
            btn.clicked.connect(lambda: self.mode_selected.emit(mode))
        else:
            btn.setStyleSheet("""
                QPushButton {
                    background-color: #D3D3D3;
                    border: 3px solid #A9A9A9;
                    border-radius: 15px;
                    padding: 10px;
                    color: #696969;
                    text-align: center;
                }
            """)
            btn.setEnabled(False)
            
        return btn
        
    def show_coming_soon(self, mode_name: str):
        """显示即将推出提示"""
        QMessageBox.information(
            self, 
            "即将推出", 
            f"{mode_name}正在开发中，敬请期待！\n\n目前可以体验1vs1对战模式。"
        )
        
    def show_settings(self):
        """显示设置对话框"""
        QMessageBox.information(self, "设置", "设置功能开发中...")
        
    def exit_game(self):
        """退出游戏"""
        reply = QMessageBox.question(
            self, 
            '退出游戏', 
            '确定要退出游戏吗？',
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            QApplication.quit()
        
    def get_game_settings(self):
        """获取游戏设置"""
        settings = {
            'difficulty': self.difficulty_combo.currentText(),
            'turn_time': self.time_spin.value()
        }
        
        # 添加AI设置
        if self.ai_manager and self.ai_manager.is_initialized:
            settings['ai_enabled'] = True
            settings['ai_agent'] = self.ai_manager.get_ai_agent()
        else:
            settings['ai_enabled'] = False
            settings['ai_agent'] = None
            
        return settings
    
    def set_ai_manager(self, ai_manager):
        """设置AI管理器"""
        self.ai_manager = ai_manager
        
        # 如果AI可用，可以在界面上显示AI状态
        if self.ai_manager and self.ai_manager.is_initialized:
            # 这里可以添加AI状态指示器
            pass


class MainWindow(QMainWindow):
    """主窗口类"""
    
    def __init__(self):
        super().__init__()
        self.current_mode = None
        self.game_widgets = {}
        self.ai_manager = None  # AI管理器
        self.init_ui()
        
    def init_ui(self):
        """初始化主窗口UI"""
        self.setWindowTitle("三国杀 - 策略卡牌游戏")
        self.setGeometry(100, 100, 1400, 900)
        
        # 设置窗口图标（如果有的话）
        # self.setWindowIcon(QIcon("icon.png"))
        
        # 创建中央部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 创建堆叠部件用于切换不同界面
        self.stacked_widget = QStackedWidget()
        
        # 创建模式选择器
        self.mode_selector = GameModeSelector()
        self.mode_selector.mode_selected.connect(self.switch_to_mode)
        self.stacked_widget.addWidget(self.mode_selector)
        
        # 设置布局
        layout = QVBoxLayout()
        layout.addWidget(self.stacked_widget)
        central_widget.setLayout(layout)
        
        # 创建菜单栏
        self.create_menu_bar()
        
        # 创建状态栏
        self.create_status_bar()
        
        # 设置窗口样式
        self.setStyleSheet("""
            QMainWindow {
                background-color: #FFF8DC;
            }
            QMenuBar {
                background-color: #F5DEB3;
                border-bottom: 2px solid #8B4513;
                font-family: "SimHei";
                font-size: 12px;
            }
            QMenuBar::item {
                background-color: transparent;
                padding: 8px 16px;
            }
            QMenuBar::item:selected {
                background-color: #DEB887;
            }
            QStatusBar {
                background-color: #F5DEB3;
                border-top: 2px solid #8B4513;
                font-family: "SimHei";
            }
        """)
        
    def create_menu_bar(self):
        """创建菜单栏"""
        menubar = self.menuBar()
        
        # 游戏菜单
        game_menu = menubar.addMenu('游戏')
        
        new_game_action = game_menu.addAction('新游戏')
        new_game_action.setShortcut('Ctrl+N')
        new_game_action.triggered.connect(self.new_game)
        
        game_menu.addSeparator()
        
        back_to_menu_action = game_menu.addAction('返回主菜单')
        back_to_menu_action.setShortcut('Ctrl+M')
        back_to_menu_action.triggered.connect(self.back_to_menu)
        
        game_menu.addSeparator()
        
        exit_action = game_menu.addAction('退出')
        exit_action.setShortcut('Ctrl+Q')
        exit_action.triggered.connect(self.close)
        
        # 设置菜单
        settings_menu = menubar.addMenu('设置')
        
        preferences_action = settings_menu.addAction('偏好设置')
        preferences_action.triggered.connect(self.show_preferences)
        
        # 帮助菜单
        help_menu = menubar.addMenu('帮助')
        
        rules_action = help_menu.addAction('游戏规则')
        rules_action.triggered.connect(self.show_rules)
        
        about_action = help_menu.addAction('关于')
        about_action.triggered.connect(self.show_about)
        
    def create_status_bar(self):
        """创建状态栏"""
        self.status_bar = self.statusBar()
        self.status_bar.showMessage("欢迎来到三国杀！请选择游戏模式开始游戏。")
        
    def switch_to_mode(self, mode: str):
        """切换到指定游戏模式"""
        self.current_mode = mode
        
        if mode == "1vs1":
            self.status_bar.showMessage("正在启动1vs1对战模式...")
            
            # 创建1vs1游戏界面
            if Game1vs1Widget and "1vs1" not in self.game_widgets:
                # 传递AI管理器到游戏界面
                game_widget = Game1vs1Widget(ai_manager=self.ai_manager)
                game_widget.back_to_menu.connect(self.back_to_menu)
                self.game_widgets["1vs1"] = game_widget
                self.stacked_widget.addWidget(game_widget)
            elif "1vs1" in self.game_widgets:
                # 如果已存在，确保AI管理器是最新的
                self.game_widgets["1vs1"].set_ai_manager(self.ai_manager)
            
            if "1vs1" in self.game_widgets:
                self.stacked_widget.setCurrentWidget(self.game_widgets["1vs1"])
                if self.ai_manager and self.ai_manager.is_initialized:
                    self.status_bar.showMessage("1vs1对战模式已启动 (AI已就绪)")
                else:
                    self.status_bar.showMessage("1vs1对战模式已启动")
            else:
                QMessageBox.warning(self, "错误", "无法加载1vs1游戏界面，请检查相关文件是否存在。")
                self.status_bar.showMessage("1vs1模式加载失败")
            
        elif mode == "guozhan":
            self.status_bar.showMessage("国战模式开发中...")
            
        elif mode == "commander":
            self.status_bar.showMessage("统帅三军模式开发中...")
            
    def back_to_menu(self):
        """返回主菜单"""
        # 在切换前停止当前模式的游戏线程，避免残留线程导致销毁异常
        self._stop_current_mode_thread()
        self.stacked_widget.setCurrentWidget(self.mode_selector)
        self.current_mode = None
        self.status_bar.showMessage("已返回主菜单")
        
    def new_game(self):
        """开始新游戏"""
        if self.current_mode:
            reply = QMessageBox.question(
                self, 
                '新游戏', 
                '确定要开始新游戏吗？当前进度将会丢失。',
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            
            if reply == QMessageBox.Yes:
                # 重新创建游戏界面
                if self.current_mode in self.game_widgets:
                    old_widget = self.game_widgets[self.current_mode]
                    # 停止并清理旧界面的游戏线程
                    self._stop_game_thread(old_widget)
                    self.stacked_widget.removeWidget(old_widget)
                    old_widget.deleteLater()
                    del self.game_widgets[self.current_mode]
                
                self.switch_to_mode(self.current_mode)
        else:
            QMessageBox.information(self, "提示", "请先选择游戏模式！")
            
    def show_preferences(self):
        """显示偏好设置"""
        QMessageBox.information(self, "偏好设置", "偏好设置功能开发中...")
        
    def show_rules(self):
        """显示游戏规则"""
        rules_text = """
        三国杀游戏规则简介：
        
        1. 游戏目标：消灭对手，成为最后的胜利者
        
        2. 基本流程：
           - 摸牌阶段：从牌堆摸取2张牌
           - 出牌阶段：可以使用手牌进行攻击、防御等操作
           - 弃牌阶段：手牌数量超过血量时需要弃牌
           - 结束阶段：回合结束
        
        3. 卡牌类型：
           - 基本牌：杀、闪、桃等
           - 锦囊牌：具有特殊效果的策略卡牌
           - 装备牌：武器、防具、坐骑等
        
        4. 角色技能：每个角色都有独特的技能
        
        更多详细规则请参考游戏内帮助。
        """
        
        QMessageBox.information(self, "游戏规则", rules_text)
        
    def show_about(self):
        """显示关于信息"""
        about_text = """
        三国杀 v1.0
        
        一款基于三国题材的策略卡牌游戏
        
        开发团队：AI助手
        技术栈：Python + PyQt5
        
        感谢您的游玩！
        """
        
        QMessageBox.about(self, "关于三国杀", about_text)
        
    def closeEvent(self, event):
        """窗口关闭事件"""
        reply = QMessageBox.question(
            self, 
            '退出游戏', 
            '确定要退出游戏吗？',
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            # 在窗口关闭前，尝试优雅停止所有模式的游戏线程
            try:
                self._stop_current_mode_thread()
            except Exception:
                pass
            event.accept()
        else:
            event.ignore()

    def _stop_current_mode_thread(self):
        """停止当前模式下的游戏线程（如果存在）。"""
        if self.current_mode and self.current_mode in self.game_widgets:
            widget = self.game_widgets[self.current_mode]
            self._stop_game_thread(widget)

    def _stop_game_thread(self, widget):
        """请求停止并等待指定游戏界面中的后台线程。"""
        try:
            if hasattr(widget, 'game_thread') and widget.game_thread:
                # 如果线程在运行，先请求停止游戏循环
                if hasattr(widget, 'game') and widget.game:
                    try:
                        widget.game.request_stop()
                    except Exception:
                        pass
                # 等待线程优雅退出
                try:
                    if widget.game_thread.isRunning():
                        widget.game_thread.wait(1500)
                except Exception:
                    pass
                # 如果仍在运行则尝试强制终止，避免QThread销毁异常
                try:
                    if widget.game_thread.isRunning():
                        widget.game_thread.terminate()
                        widget.game_thread.wait(500)
                except Exception:
                    pass
        except Exception:
            pass
    
    def set_ai_manager(self, ai_manager):
        """设置AI管理器"""
        self.ai_manager = ai_manager
        # 将AI管理器传递给模式选择器
        if hasattr(self.mode_selector, 'set_ai_manager'):
            self.mode_selector.set_ai_manager(ai_manager)
        
        # 更新状态栏显示AI状态
        if self.ai_manager and self.ai_manager.is_initialized:
            self.statusBar().showMessage("AI系统已就绪")
        else:
            self.statusBar().showMessage("AI系统未启用")
    
    def get_ai_manager(self):
        """获取AI管理器"""
        return self.ai_manager


def main():
    """主函数"""
    app = QApplication(sys.argv)
    
    # 设置应用程序信息
    app.setApplicationName("三国杀")
    app.setApplicationVersion("1.0")
    app.setOrganizationName("AI Game Studio")
    
    # 创建并显示主窗口
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()