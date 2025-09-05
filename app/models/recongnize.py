import cv2
import numpy as np
from pathlib import Path
import matplotlib.pyplot as plt

class CardRecognizer:
    def __init__(self, image_folder):
        """初始化识别器并建立参考数据库"""
        self.image_folder = Path(image_folder)
        self.reference_db = {}
        self.build_reference_database()
        
    def build_reference_database(self):
        """构建参考图像特征数据库"""
        print(f"正在构建参考数据库...")
        
        for img_path in self.image_folder.glob("*.png"):
            # 提取基本名称（处理带数字后缀的变体）
            base_name = img_path.stem
            if base_name.endswith('1'):
                base_name = base_name[:-1]
                
            # 加载图像并计算特征
            img = cv2.imread(str(img_path))
            if img is None:
                print(f"无法读取图像: {img_path}")
                continue
                
            # 提取多种特征
            features = self.extract_features(img)
            
            # 存储到数据库
            if base_name not in self.reference_db:
                self.reference_db[base_name] = []
            self.reference_db[base_name].append((img_path.stem, features))
            
        print(f"参考数据库构建完成，包含 {len(self.reference_db)} 个角色")
    
    def extract_features(self, img):
        """提取图像特征"""
        features = {}
        
        # 1. 颜色直方图 (HSV空间)
        hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
        h_bins, s_bins, v_bins = 30, 32, 32
        hist_hsv = cv2.calcHist([hsv], [0, 1, 2], None, [h_bins, s_bins, v_bins], 
                              [0, 180, 0, 256, 0, 256])
        cv2.normalize(hist_hsv, hist_hsv, 0, 1, cv2.NORM_MINMAX)
        features['hist_hsv'] = hist_hsv
        
        # 2. 边缘方向直方图 (类HOG特征)
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        sobelx = cv2.Sobel(gray, cv2.CV_64F, 1, 0, ksize=3)
        sobely = cv2.Sobel(gray, cv2.CV_64F, 0, 1, ksize=3)
        magnitude = cv2.magnitude(sobelx, sobely)
        angle = cv2.phase(sobelx, sobely, angleInDegrees=True)
        
        # 将角度量化为8个方向
        bins = np.array([0, 45, 90, 135, 180, 225, 270, 315, 360])
        hist_edge = np.zeros(8)
        
        for i in range(8):
            mask = np.logical_and(angle >= bins[i], angle < bins[i+1])
            hist_edge[i] = np.sum(magnitude[mask])
        
        # 归一化
        if np.sum(hist_edge) > 0:
            hist_edge = hist_edge / np.sum(hist_edge)
        features['hist_edge'] = hist_edge
        
        # 3. 区域直方图 (将图像分为4个区域)
        h, w = img.shape[:2]
        regions = [(0, 0, w//2, h//2),      # 左上
                  (w//2, 0, w, h//2),      # 右上
                  (0, h//2, w//2, h),      # 左下
                  (w//2, h//2, w, h)]      # 右下
        
        region_hists = []
        for x1, y1, x2, y2 in regions:
            roi = hsv[y1:y2, x1:x2]
            hist = cv2.calcHist([roi], [0, 1], None, [h_bins, s_bins], [0, 180, 0, 256])
            cv2.normalize(hist, hist, 0, 1, cv2.NORM_MINMAX)
            region_hists.append(hist)
        
        features['region_hists'] = region_hists
        
        return features
    
    def compare_features(self, feat1, feat2):
        """比较两组特征返回相似度得分"""
        # 1. 颜色直方图相似度
        hsv_score = cv2.compareHist(feat1['hist_hsv'], feat2['hist_hsv'], cv2.HISTCMP_CORREL)
        
        # 2. 边缘方向直方图相似度
        edge_score = 1 - np.sum(np.abs(feat1['hist_edge'] - feat2['hist_edge'])) / 2
        
        # 3. 区域直方图相似度
        region_scores = []
        for i in range(len(feat1['region_hists'])):
            score = cv2.compareHist(feat1['region_hists'][i], 
                                   feat2['region_hists'][i], 
                                   cv2.HISTCMP_CORREL)
            region_scores.append(score)
        region_avg_score = sum(region_scores) / len(region_scores)
        
        # 加权组合得分 (权重可根据实际效果调整)
        combined_score = 0.5 * hsv_score + 0.3 * edge_score + 0.2 * region_avg_score
        
        return combined_score
    
    def identify_image(self, img_path, threshold=0.7):
        """识别给定图像"""
        # 加载图像
        if isinstance(img_path, str):
            img_path = Path(img_path)
            
        img = cv2.imread(str(img_path))
        if img is None:
            return "无法读取图像", None, 0
            
        # 提取特征
        features = self.extract_features(img)
        
        best_match = None
        best_score = -1
        best_character = None
        
        # 与参考数据库比较
        for character, variants in self.reference_db.items():
            for variant_name, variant_features in variants:
                score = self.compare_features(features, variant_features)
                if score > best_score:
                    best_score = score
                    best_match = variant_name
                    best_character = character
        
        if best_score < threshold:
            return "未知", None, best_score
            
        return best_character, best_match, best_score
    
    def test_accuracy(self):
        """测试识别准确率"""
        correct = 0
        total = 0
        results = []
        
        for img_path in self.image_folder.glob("*.png"):
            # 提取实际角色名
            actual_name = img_path.stem
            if actual_name.endswith('1'):
                actual_name = actual_name[:-1]
                
            # 识别
            character, variant, score = self.identify_image(img_path)
            
            # 记录结果
            is_correct = (character == actual_name)
            if is_correct:
                correct += 1
            total += 1
            
            results.append({
                'image': img_path.name,
                'actual': actual_name,
                'predicted': character,
                'score': score,
                'correct': is_correct
            })
            
        accuracy = correct / total if total > 0 else 0
        print(f"准确率: {accuracy:.2%} ({correct}/{total})")
        
        return results, accuracy