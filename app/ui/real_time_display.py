#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
实时卡牌数量显示系统
提供动态更新的游戏状态监控和Web界面支持
"""

import json
import time
import threading
from typing import Dict, List, Optional, Callable
from datetime import datetime
from ...models.deck import EnhancedDeck
from ...models.card import Card
from .card_display import CardDisplayManager, GameDisplayInterface

class RealTimeCardMonitor:
    """实时卡牌监控器"""
    
    def __init__(self, deck: EnhancedDeck, update_interval: float = 1.0):
        self.deck = deck
        self.display_manager = CardDisplayManager(deck)
        self.update_interval = update_interval
        self.is_monitoring = False
        self.monitor_thread = None
        self.callbacks = []  # 状态更新回调函数
        self.history = []    # 状态历史记录
        self.max_history = 100
        
    def add_callback(self, callback: Callable[[Dict], None]):
        """添加状态更新回调函数"""
        self.callbacks.append(callback)
    
    def remove_callback(self, callback: Callable[[Dict], None]):
        """移除状态更新回调函数"""
        if callback in self.callbacks:
            self.callbacks.remove(callback)
    
    def start_monitoring(self):
        """开始实时监控"""
        if not self.is_monitoring:
            self.is_monitoring = True
            self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
            self.monitor_thread.start()
            print("🔄 实时卡牌监控已启动")
    
    def stop_monitoring(self):
        """停止实时监控"""
        self.is_monitoring = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=2.0)
        print("⏹️  实时卡牌监控已停止")
    
    def _monitor_loop(self):
        """监控循环"""
        while self.is_monitoring:
            try:
                # 获取当前状态
                current_status = self._get_enhanced_status()
                
                # 记录历史
                self._record_history(current_status)
                
                # 调用回调函数
                for callback in self.callbacks:
                    try:
                        callback(current_status)
                    except Exception as e:
                        print(f"回调函数执行错误: {e}")
                
                time.sleep(self.update_interval)
                
            except Exception as e:
                print(f"监控循环错误: {e}")
                time.sleep(self.update_interval)
    
    def _get_enhanced_status(self) -> Dict:
        """获取增强的状态信息"""
        base_status = self.display_manager.get_real_time_status()
        
        # 添加时间戳和额外信息
        enhanced_status = {
            **base_status,
            'timestamp': datetime.now().isoformat(),
            'monitoring_active': self.is_monitoring,
            'deck_efficiency': self._calculate_deck_efficiency(),
            'card_flow_rate': self._calculate_card_flow_rate(),
            'warnings': self.display_manager.get_warning_messages()
        }
        
        return enhanced_status
    
    def _calculate_deck_efficiency(self) -> float:
        """计算牌堆效率（可用卡牌比例）"""
        total = self.deck.get_total_cards_count()
        available = self.deck.get_draw_pile_count() + self.deck.get_discard_pile_count()
        return (available / total * 100) if total > 0 else 0
    
    def _calculate_card_flow_rate(self) -> float:
        """计算卡牌流动率（基于历史数据）"""
        if len(self.history) < 2:
            return 0.0
        
        recent_changes = 0
        for i in range(1, min(6, len(self.history))):
            prev_total = self.history[-i-1]['draw_pile'] + self.history[-i-1]['discard_pile']
            curr_total = self.history[-i]['draw_pile'] + self.history[-i]['discard_pile']
            recent_changes += abs(prev_total - curr_total)
        
        return recent_changes / min(5, len(self.history) - 1)
    
    def _record_history(self, status: Dict):
        """记录状态历史"""
        self.history.append(status)
        if len(self.history) > self.max_history:
            self.history.pop(0)
    
    def get_status_history(self, count: int = 10) -> List[Dict]:
        """获取状态历史"""
        return self.history[-count:] if count > 0 else self.history
    
    def get_current_status(self) -> Dict:
        """获取当前状态"""
        return self._get_enhanced_status()

class WebDisplayGenerator:
    """Web显示生成器 - 生成HTML/CSS/JS代码"""
    
    def __init__(self, monitor: RealTimeCardMonitor):
        self.monitor = monitor
    
    def generate_html_dashboard(self) -> str:
        """生成HTML仪表板"""
        html_template = """
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>三国杀卡牌监控仪表板</title>
    <style>
        {css_styles}
    </style>
</head>
<body>
    <div class="dashboard">
        <header>
            <h1>🃏 三国杀卡牌监控仪表板</h1>
            <div class="status-indicator" id="status-indicator">🔄 监控中</div>
        </header>
        
        <div class="main-content">
            <div class="card-stats">
                <div class="stat-card draw-pile">
                    <h3>📚 摸牌堆</h3>
                    <div class="stat-value" id="draw-pile-count">--</div>
                    <div class="stat-label">张卡牌</div>
                </div>
                
                <div class="stat-card discard-pile">
                    <h3>🗑️ 弃牌堆</h3>
                    <div class="stat-value" id="discard-pile-count">--</div>
                    <div class="stat-label">张卡牌</div>
                </div>
                
                <div class="stat-card removed-cards">
                    <h3>❌ 移出游戏</h3>
                    <div class="stat-value" id="removed-cards-count">--</div>
                    <div class="stat-label">张卡牌</div>
                </div>
                
                <div class="stat-card total-cards">
                    <h3>📊 总计</h3>
                    <div class="stat-value" id="total-cards-count">--</div>
                    <div class="stat-label">张卡牌</div>
                </div>
            </div>
            
            <div class="visual-section">
                <div class="deck-visual" id="deck-visual">
                    <div class="pile draw-pile-visual">
                        <div class="pile-label">摸牌堆</div>
                        <div class="pile-stack" id="draw-pile-stack"></div>
                    </div>
                    <div class="pile discard-pile-visual">
                        <div class="pile-label">弃牌堆</div>
                        <div class="pile-stack" id="discard-pile-stack"></div>
                    </div>
                </div>
            </div>
            
            <div class="info-section">
                <div class="current-cards">
                    <h3>🔝 当前卡牌</h3>
                    <div id="current-cards-info">--</div>
                </div>
                
                <div class="warnings">
                    <h3>⚠️ 系统提醒</h3>
                    <div id="warnings-list">无警告</div>
                </div>
            </div>
            
            <div class="chart-section">
                <h3>📈 卡牌数量趋势</h3>
                <canvas id="trend-chart" width="600" height="200"></canvas>
            </div>
        </div>
    </div>
    
    <script>
        {javascript_code}
    </script>
</body>
</html>
        """
        
        css_styles = self._generate_css()
        javascript_code = self._generate_javascript()
        
        return html_template.format(
            css_styles=css_styles,
            javascript_code=javascript_code
        )
    
    def _generate_css(self) -> str:
        """生成CSS样式"""
        return """
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Arial', sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            color: #333;
        }
        
        .dashboard {
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
        }
        
        header {
            text-align: center;
            margin-bottom: 30px;
            color: white;
        }
        
        header h1 {
            font-size: 2.5em;
            margin-bottom: 10px;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
        }
        
        .status-indicator {
            display: inline-block;
            padding: 8px 16px;
            background: rgba(255,255,255,0.2);
            border-radius: 20px;
            font-weight: bold;
        }
        
        .card-stats {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        
        .stat-card {
            background: white;
            border-radius: 15px;
            padding: 20px;
            text-align: center;
            box-shadow: 0 8px 25px rgba(0,0,0,0.1);
            transition: transform 0.3s ease;
        }
        
        .stat-card:hover {
            transform: translateY(-5px);
        }
        
        .stat-card h3 {
            color: #666;
            margin-bottom: 10px;
            font-size: 1.1em;
        }
        
        .stat-value {
            font-size: 3em;
            font-weight: bold;
            color: #4a90e2;
            margin-bottom: 5px;
        }
        
        .stat-label {
            color: #999;
            font-size: 0.9em;
        }
        
        .visual-section {
            background: white;
            border-radius: 15px;
            padding: 30px;
            margin-bottom: 30px;
            box-shadow: 0 8px 25px rgba(0,0,0,0.1);
        }
        
        .deck-visual {
            display: flex;
            justify-content: space-around;
            align-items: flex-end;
            height: 200px;
        }
        
        .pile {
            text-align: center;
        }
        
        .pile-label {
            font-weight: bold;
            margin-bottom: 10px;
            color: #666;
        }
        
        .pile-stack {
            width: 80px;
            height: 120px;
            border: 3px solid #ddd;
            border-radius: 10px;
            position: relative;
            background: #f9f9f9;
        }
        
        .info-section {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 20px;
            margin-bottom: 30px;
        }
        
        .current-cards, .warnings {
            background: white;
            border-radius: 15px;
            padding: 20px;
            box-shadow: 0 8px 25px rgba(0,0,0,0.1);
        }
        
        .current-cards h3, .warnings h3 {
            color: #666;
            margin-bottom: 15px;
        }
        
        .chart-section {
            background: white;
            border-radius: 15px;
            padding: 30px;
            box-shadow: 0 8px 25px rgba(0,0,0,0.1);
        }
        
        .chart-section h3 {
            color: #666;
            margin-bottom: 20px;
            text-align: center;
        }
        
        #trend-chart {
            width: 100%;
            height: 200px;
            border: 1px solid #eee;
            border-radius: 10px;
        }
        
        .warning-item {
            padding: 8px 12px;
            margin: 5px 0;
            background: #fff3cd;
            border: 1px solid #ffeaa7;
            border-radius: 5px;
            color: #856404;
        }
        """
    
    def _generate_javascript(self) -> str:
        """生成JavaScript代码"""
        return """
        class CardDashboard {
            constructor() {
                this.isActive = true;
                this.updateInterval = 2000; // 2秒更新一次
                this.historyData = [];
                this.maxHistory = 50;
                this.chart = null;
                
                this.initChart();
                this.startUpdating();
            }
            
            async fetchStatus() {
                // 模拟数据获取 - 实际应用中应该从服务器获取
                return {
                    draw_pile: Math.floor(Math.random() * 50) + 10,
                    discard_pile: Math.floor(Math.random() * 20),
                    removed_cards: Math.floor(Math.random() * 5),
                    total_cards: 65,
                    top_card: '红桃5 杀',
                    discard_top: '黑桃8 闪',
                    warnings: Math.random() > 0.7 ? ['⚠️ 摸牌堆卡牌不足'] : [],
                    timestamp: new Date().toISOString()
                };
            }
            
            updateDisplay(status) {
                // 更新数字显示
                document.getElementById('draw-pile-count').textContent = status.draw_pile;
                document.getElementById('discard-pile-count').textContent = status.discard_pile;
                document.getElementById('removed-cards-count').textContent = status.removed_cards;
                document.getElementById('total-cards-count').textContent = status.total_cards;
                
                // 更新当前卡牌信息
                const currentCardsInfo = document.getElementById('current-cards-info');
                currentCardsInfo.innerHTML = `
                    <div>摸牌堆顶: ${status.top_card || '无'}</div>
                    <div>弃牌堆顶: ${status.discard_top || '无'}</div>
                `;
                
                // 更新警告信息
                const warningsList = document.getElementById('warnings-list');
                if (status.warnings && status.warnings.length > 0) {
                    warningsList.innerHTML = status.warnings
                        .map(warning => `<div class="warning-item">${warning}</div>`)
                        .join('');
                } else {
                    warningsList.textContent = '无警告';
                }
                
                // 更新可视化牌堆
                this.updatePileVisual('draw-pile-stack', status.draw_pile);
                this.updatePileVisual('discard-pile-stack', status.discard_pile);
                
                // 记录历史数据
                this.recordHistory(status);
                
                // 更新图表
                this.updateChart();
            }
            
            updatePileVisual(elementId, count) {
                const element = document.getElementById(elementId);
                const height = Math.min(count * 2, 100); // 最大高度100px
                const opacity = Math.min(count / 30, 1); // 根据数量调整透明度
                
                element.style.background = `linear-gradient(to top, 
                    rgba(74, 144, 226, ${opacity}) 0%, 
                    rgba(74, 144, 226, ${opacity * 0.7}) ${height}%, 
                    #f9f9f9 ${height}%)`;
            }
            
            recordHistory(status) {
                this.historyData.push({
                    timestamp: new Date(),
                    draw_pile: status.draw_pile,
                    discard_pile: status.discard_pile,
                    total_available: status.draw_pile + status.discard_pile
                });
                
                if (this.historyData.length > this.maxHistory) {
                    this.historyData.shift();
                }
            }
            
            initChart() {
                const canvas = document.getElementById('trend-chart');
                this.chart = canvas.getContext('2d');
            }
            
            updateChart() {
                if (!this.chart || this.historyData.length < 2) return;
                
                const canvas = this.chart.canvas;
                const width = canvas.width;
                const height = canvas.height;
                
                // 清空画布
                this.chart.clearRect(0, 0, width, height);
                
                // 绘制网格
                this.chart.strokeStyle = '#eee';
                this.chart.lineWidth = 1;
                for (let i = 0; i <= 10; i++) {
                    const y = (height / 10) * i;
                    this.chart.beginPath();
                    this.chart.moveTo(0, y);
                    this.chart.lineTo(width, y);
                    this.chart.stroke();
                }
                
                // 绘制数据线
                if (this.historyData.length > 1) {
                    const maxValue = Math.max(...this.historyData.map(d => d.total_available));
                    const stepX = width / (this.historyData.length - 1);
                    
                    // 摸牌堆线
                    this.chart.strokeStyle = '#4a90e2';
                    this.chart.lineWidth = 2;
                    this.chart.beginPath();
                    this.historyData.forEach((data, index) => {
                        const x = index * stepX;
                        const y = height - (data.draw_pile / maxValue) * height;
                        if (index === 0) {
                            this.chart.moveTo(x, y);
                        } else {
                            this.chart.lineTo(x, y);
                        }
                    });
                    this.chart.stroke();
                    
                    // 弃牌堆线
                    this.chart.strokeStyle = '#e74c3c';
                    this.chart.beginPath();
                    this.historyData.forEach((data, index) => {
                        const x = index * stepX;
                        const y = height - (data.discard_pile / maxValue) * height;
                        if (index === 0) {
                            this.chart.moveTo(x, y);
                        } else {
                            this.chart.lineTo(x, y);
                        }
                    });
                    this.chart.stroke();
                }
            }
            
            async startUpdating() {
                while (this.isActive) {
                    try {
                        const status = await this.fetchStatus();
                        this.updateDisplay(status);
                    } catch (error) {
                        console.error('更新状态失败:', error);
                    }
                    
                    await new Promise(resolve => setTimeout(resolve, this.updateInterval));
                }
            }
            
            stop() {
                this.isActive = false;
            }
        }
        
        // 启动仪表板
        document.addEventListener('DOMContentLoaded', () => {
            window.cardDashboard = new CardDashboard();
        });
        
        // 页面卸载时停止更新
        window.addEventListener('beforeunload', () => {
            if (window.cardDashboard) {
                window.cardDashboard.stop();
            }
        });
        """
    
    def save_dashboard_file(self, filename: str = "card_dashboard.html") -> str:
        """保存仪表板HTML文件"""
        html_content = self.generate_html_dashboard()
        
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        return filename

class ConsoleRealTimeDisplay:
    """控制台实时显示"""
    
    def __init__(self, monitor: RealTimeCardMonitor):
        self.monitor = monitor
        self.is_displaying = False
        self.display_thread = None
        
    def start_console_display(self):
        """开始控制台实时显示"""
        if not self.is_displaying:
            self.is_displaying = True
            self.display_thread = threading.Thread(target=self._display_loop, daemon=True)
            self.display_thread.start()
            print("🖥️  控制台实时显示已启动")
    
    def stop_console_display(self):
        """停止控制台实时显示"""
        self.is_displaying = False
        if self.display_thread:
            self.display_thread.join(timeout=2.0)
    
    def _display_loop(self):
        """显示循环"""
        while self.is_displaying:
            try:
                # 清屏（在支持的终端中）
                import os
                os.system('clear' if os.name == 'posix' else 'cls')
                
                # 显示当前状态
                status = self.monitor.get_current_status()
                self._print_status_dashboard(status)
                
                time.sleep(2.0)  # 每2秒更新一次
                
            except Exception as e:
                print(f"显示循环错误: {e}")
                time.sleep(2.0)
    
    def _print_status_dashboard(self, status: Dict):
        """打印状态仪表板"""
        print("\n" + "="*60)
        print("🃏 三国杀卡牌实时监控 🃏")
        print("="*60)
        
        # 基本状态
        print(f"\n📊 卡牌状态 [{status['timestamp'][:19]}]")
        print(f"   📚 摸牌堆: {status['draw_pile']:3d} 张")
        print(f"   🗑️  弃牌堆: {status['discard_pile']:3d} 张")
        print(f"   ❌ 移出游戏: {status['removed_cards']:3d} 张")
        print(f"   📈 总计: {status['total_cards']:3d} 张")
        
        # 效率指标
        print(f"\n📈 系统指标")
        print(f"   🎯 牌堆效率: {status['deck_efficiency']:.1f}%")
        print(f"   🔄 流动率: {status['card_flow_rate']:.1f}")
        
        # 当前卡牌
        if status.get('top_card'):
            print(f"\n🔝 当前卡牌")
            print(f"   摸牌堆顶: {status['top_card']}")
        if status.get('discard_top'):
            print(f"   弃牌堆顶: {status['discard_top']}")
        
        # 警告信息
        if status.get('warnings'):
            print(f"\n⚠️  系统提醒")
            for warning in status['warnings']:
                print(f"   {warning}")
        
        # ASCII可视化
        self._print_ascii_bars(status)
        
        print("\n" + "="*60)
        print("按 Ctrl+C 停止监控")
    
    def _print_ascii_bars(self, status: Dict):
        """打印ASCII条形图"""
        print(f"\n📊 可视化")
        
        max_width = 40
        total = status['total_cards']
        
        if total > 0:
            draw_width = int((status['draw_pile'] / total) * max_width)
            discard_width = int((status['discard_pile'] / total) * max_width)
            
            print(f"   摸牌堆 {'█' * draw_width:<{max_width}} {status['draw_pile']}")
            print(f"   弃牌堆 {'░' * discard_width:<{max_width}} {status['discard_pile']}")

# 演示函数
def demo_real_time_display():
    """演示实时显示系统"""
    print("=== 实时卡牌显示系统演示 ===")
    
    # 创建组件
    from ...models.deck import EnhancedDeck
    deck = EnhancedDeck()
    monitor = RealTimeCardMonitor(deck, update_interval=0.5)
    
    # 添加状态更新回调
    def status_callback(status):
        print(f"状态更新: 摸牌堆 {status['draw_pile']}, 弃牌堆 {status['discard_pile']}")
    
    monitor.add_callback(status_callback)
    
    # 启动监控
    monitor.start_monitoring()
    
    # 生成Web仪表板
    web_generator = WebDisplayGenerator(monitor)
    dashboard_file = web_generator.save_dashboard_file()
    print(f"Web仪表板已保存到: {dashboard_file}")
    
    # 模拟一些卡牌操作
    print("\n模拟卡牌操作...")
    for i in range(10):
        cards = deck.draw_cards(2)
        if cards:
            deck.discard_card(cards[0])
        time.sleep(1)
    
    # 停止监控
    monitor.stop_monitoring()
    
    return monitor, web_generator

if __name__ == "__main__":
    demo_real_time_display()