#!/usr/bin/env python3
"""
三国杀游戏快速启动脚本
提供简化的启动方式
"""

import sys
import subprocess
from pathlib import Path

def main():
    """主函数"""
    if len(sys.argv) == 1:
        # 默认启动GUI模式
        print("启动三国杀游戏 (GUI模式)...")
        subprocess.run([sys.executable, "main_launcher.py", "--mode", "gui"])
    elif len(sys.argv) == 2:
        mode = sys.argv[1].lower()
        if mode in ["gui", "console", "web", "train"]:
            print(f"启动三国杀游戏 ({mode}模式)...")
            subprocess.run([sys.executable, "main_launcher.py", "--mode", mode])
        elif mode in ["help", "-h", "--help"]:
            print_help()
        else:
            print(f"未知模式: {mode}")
            print_help()
    else:
        # 传递所有参数给main_launcher.py
        subprocess.run([sys.executable, "main_launcher.py"] + sys.argv[1:])

def print_help():
    """打印帮助信息"""
    print("""
三国杀游戏启动器

快速启动:
  python start.py          # 启动GUI模式
  python start.py gui      # 启动GUI模式
  python start.py console  # 启动控制台模式
  python start.py web      # 启动Web服务器
  python start.py train    # 启动AI训练

完整参数支持:
  python start.py --mode gui --no-ai --debug
  
更多选项请使用:
  python main_launcher.py --help
""")

if __name__ == "__main__":
    main()