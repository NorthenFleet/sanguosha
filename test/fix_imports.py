#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
批量修复测试文件的导入路径问题
"""

import os
import glob

def fix_test_file_imports():
    """修复测试文件的导入路径"""
    test_dir = os.path.dirname(os.path.abspath(__file__))
    test_files = glob.glob(os.path.join(test_dir, "test_*.py"))
    
    import_fix = """import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

"""
    
    for test_file in test_files:
        if test_file.endswith("test_game_flow.py"):
            continue  # 已经修复过了
            
        with open(test_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 检查是否已经有路径修复代码
        if "sys.path.append" in content:
            continue
            
        # 找到第一个from app.开头的导入语句
        lines = content.split('\n')
        insert_index = 0
        
        for i, line in enumerate(lines):
            if line.strip().startswith('from app.') or line.strip().startswith('import app.'):
                insert_index = i
                break
        
        # 插入路径修复代码
        if insert_index > 0:
            lines.insert(insert_index, import_fix.rstrip())
            new_content = '\n'.join(lines)
            
            with open(test_file, 'w', encoding='utf-8') as f:
                f.write(new_content)
            
            print(f"已修复: {os.path.basename(test_file)}")

if __name__ == "__main__":
    fix_test_file_imports()
    print("所有测试文件导入路径修复完成!")