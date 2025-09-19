"""
路径处理工具模块

提供统一的路径处理方法，解决不同运行路径下的导入问题
"""
import os
import sys

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def setup_paths():
    """设置项目路径到系统路径中"""
    if PROJECT_ROOT not in sys.path:
        sys.path.insert(0, PROJECT_ROOT)


def get_absolute_path(*relative_paths):
    """
    获取相对于项目根目录的绝对路径
    
    :param relative_paths: 相对路径部分
    :return: 绝对路径
    """
    return os.path.join(PROJECT_ROOT, *relative_paths)


def import_module_from_root(module_path):
    """
    从项目根目录导入模块
    
    :param module_path: 模块路径，如 'app.models.game'
    :return: 导入的模块
    """
    setup_paths()
    __import__(module_path)
    return sys.modules[module_path]