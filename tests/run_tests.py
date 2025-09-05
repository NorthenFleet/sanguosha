"""
三国杀1v1测试运行器

此脚本用于自动化运行所有测试，使用测试模式避免用户输入。
"""
import subprocess
import sys
import os

def run_test_script(script_name: str) -> tuple[int, str, str]:
    """运行测试脚本并返回结果"""
    try:
        # 使用python命令运行脚本
        result = subprocess.run(
            [sys.executable, script_name],
            capture_output=True,
            text=True,
            timeout=30,  # 设置超时时间为30秒
            cwd=os.path.dirname(os.path.abspath(__file__))
        )
        return result.returncode, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return -1, "", "测试脚本运行超时"
    except Exception as e:
        return -1, "", f"运行测试脚本时出错: {str(e)}"

def main():
    """主函数"""
    print("三国杀1v1测试运行器")
    print("=" * 30)
    
    # 定义要运行的测试脚本
    test_scripts = [
        "test_script.py",
        "test_game_flow.py",
        "test_all_skills.py"
    ]
    
    # 运行每个测试脚本
    for script in test_scripts:
        print(f"\n运行测试脚本: {script}")
        print("-" * 30)
        
        # 检查脚本文件是否存在
        script_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), script)
        if not os.path.exists(script_path):
            print(f"错误: 测试脚本 {script} 不存在")
            continue
        
        # 运行测试脚本
        returncode, stdout, stderr = run_test_script(script_path)
        
        # 输出结果
        if returncode == 0:
            print("测试脚本运行成功")
            if stdout:
                print("输出:")
                print(stdout)
        else:
            print(f"测试脚本运行失败 (返回码: {returncode})")
            if stderr:
                print("错误信息:")
                print(stderr)
            if stdout:
                print("输出:")
                print(stdout)
    
    print("\n所有测试运行完成。")

if __name__ == "__main__":
    main()