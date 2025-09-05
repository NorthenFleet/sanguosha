"""
三国杀图像识别测试脚本
"""
import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from recongnize import CardRecognizer

def test_recognize():
    """测试图像识别功能"""
    print("开始测试图像识别功能...")
    
    # 创建识别器
    recognizer = CardRecognizer("images")
    
    # 测试准确率
    results, accuracy = recognizer.test_accuracy()
    
    print(f"\n识别结果:")
    for result in results[:10]:  # 只显示前10个结果
        print(f"  图像: {result['image']}, 实际: {result['actual']}, 预测: {result['predicted']}, 得分: {result['score']:.2f}, 正确: {result['correct']}")
    
    print(f"\n总体准确率: {accuracy:.2%}")

if __name__ == "__main__":
    test_recognize()