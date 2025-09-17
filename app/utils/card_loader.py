#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
优化的卡牌加载系统
提供高性能的卡牌数据加载、缓存和管理功能
"""

import json
import time
import hashlib
import threading
from typing import Dict, List, Optional, Any, Tuple
from pathlib import Path
from functools import lru_cache
from concurrent.futures import ThreadPoolExecutor, as_completed
import logging

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class CardDataCache:
    """卡牌数据缓存管理器"""
    
    def __init__(self, max_size: int = 1000):
        self.cache = {}
        self.max_size = max_size
        self.access_times = {}
        self.lock = threading.RLock()
        
    def get(self, key: str) -> Optional[Any]:
        """获取缓存数据"""
        with self.lock:
            if key in self.cache:
                self.access_times[key] = time.time()
                return self.cache[key]
            return None
    
    def set(self, key: str, value: Any) -> None:
        """设置缓存数据"""
        with self.lock:
            if len(self.cache) >= self.max_size:
                self._evict_oldest()
            
            self.cache[key] = value
            self.access_times[key] = time.time()
    
    def _evict_oldest(self) -> None:
        """淘汰最旧的缓存项"""
        if not self.access_times:
            return
        
        oldest_key = min(self.access_times.keys(), 
                        key=lambda k: self.access_times[k])
        del self.cache[oldest_key]
        del self.access_times[oldest_key]
    
    def clear(self) -> None:
        """清空缓存"""
        with self.lock:
            self.cache.clear()
            self.access_times.clear()
    
    def get_stats(self) -> Dict[str, Any]:
        """获取缓存统计信息"""
        with self.lock:
            return {
                'size': len(self.cache),
                'max_size': self.max_size,
                'hit_rate': getattr(self, '_hit_count', 0) / max(getattr(self, '_total_requests', 1), 1),
                'keys': list(self.cache.keys())
            }

class OptimizedCardLoader:
    """优化的卡牌加载器"""
    
    def __init__(self, cards_file: str = None, enable_cache: bool = True):
        self.cards_file = cards_file or self._get_default_cards_file()
        self.cache = CardDataCache() if enable_cache else None
        self.file_hash = None
        self.last_modified = None
        self.loaded_cards = None
        self.lock = threading.RLock()
        self.load_stats = {
            'total_loads': 0,
            'cache_hits': 0,
            'load_times': [],
            'errors': []
        }
        
    def _get_default_cards_file(self) -> str:
        """获取默认卡牌文件路径"""
        current_dir = Path(__file__).parent
        return str(current_dir.parent / 'data' / 'cards.json')
    
    def _calculate_file_hash(self, file_path: str) -> str:
        """计算文件哈希值"""
        try:
            with open(file_path, 'rb') as f:
                content = f.read()
                return hashlib.md5(content).hexdigest()
        except Exception as e:
            logger.error(f"计算文件哈希失败: {e}")
            return ""
    
    def _get_file_modified_time(self, file_path: str) -> float:
        """获取文件修改时间"""
        try:
            return Path(file_path).stat().st_mtime
        except Exception:
            return 0
    
    def _should_reload(self) -> bool:
        """判断是否需要重新加载"""
        if not self.loaded_cards:
            return True
        
        current_hash = self._calculate_file_hash(self.cards_file)
        current_modified = self._get_file_modified_time(self.cards_file)
        
        return (current_hash != self.file_hash or 
                current_modified != self.last_modified)
    
    def load_cards(self, force_reload: bool = False) -> List[Dict[str, Any]]:
        """加载卡牌数据"""
        start_time = time.time()
        
        with self.lock:
            self.load_stats['total_loads'] += 1
            
            # 检查缓存
            if not force_reload and self.cache:
                cache_key = f"cards_{self.cards_file}"
                cached_data = self.cache.get(cache_key)
                if cached_data and not self._should_reload():
                    self.load_stats['cache_hits'] += 1
                    logger.info("从缓存加载卡牌数据")
                    return cached_data
            
            # 检查是否需要重新加载
            if not force_reload and not self._should_reload():
                if self.loaded_cards:
                    return self.loaded_cards
            
            try:
                # 加载文件
                logger.info(f"从文件加载卡牌数据: {self.cards_file}")
                cards_data = self._load_from_file()
                
                # 验证数据
                validated_cards = self._validate_cards_data(cards_data)
                
                # 预处理数据
                processed_cards = self._preprocess_cards(validated_cards)
                
                # 更新状态
                self.loaded_cards = processed_cards
                self.file_hash = self._calculate_file_hash(self.cards_file)
                self.last_modified = self._get_file_modified_time(self.cards_file)
                
                # 更新缓存
                if self.cache:
                    cache_key = f"cards_{self.cards_file}"
                    self.cache.set(cache_key, processed_cards)
                
                load_time = time.time() - start_time
                self.load_stats['load_times'].append(load_time)
                
                logger.info(f"卡牌数据加载完成，耗时 {load_time:.3f}s，共 {len(processed_cards)} 张卡牌")
                return processed_cards
                
            except Exception as e:
                error_msg = f"加载卡牌数据失败: {e}"
                logger.error(error_msg)
                self.load_stats['errors'].append(error_msg)
                raise
    
    def _load_from_file(self) -> List[Dict[str, Any]]:
        """从文件加载原始数据"""
        try:
            with open(self.cards_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
            if isinstance(data, dict) and 'cards' in data:
                return data['cards']
            elif isinstance(data, list):
                return data
            else:
                raise ValueError("无效的卡牌数据格式")
                
        except json.JSONDecodeError as e:
            raise ValueError(f"JSON格式错误: {e}")
        except FileNotFoundError:
            raise FileNotFoundError(f"卡牌文件不存在: {self.cards_file}")
    
    def _validate_cards_data(self, cards_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """验证卡牌数据"""
        validated_cards = []
        required_fields = ['name', 'type', 'suit']
        
        for i, card in enumerate(cards_data):
            try:
                # 检查必需字段
                missing_fields = [field for field in required_fields if field not in card]
                if missing_fields:
                    logger.warning(f"卡牌 {i} 缺少字段: {missing_fields}")
                    continue
                
                # 验证数据类型
                if not isinstance(card['name'], str) or not card['name'].strip():
                    logger.warning(f"卡牌 {i} 名称无效")
                    continue
                
                # 检查点数字段（支持number或rank）
                if 'number' not in card and 'rank' not in card:
                    logger.warning(f"卡牌 {i} 缺少点数字段")
                    continue
                
                number_value = card.get('number') or card.get('rank')
                if not isinstance(number_value, (int, str)):
                    logger.warning(f"卡牌 {i} 点数无效")
                    continue
                
                # 标准化数据
                normalized_card = self._normalize_card_data(card)
                validated_cards.append(normalized_card)
                
            except Exception as e:
                logger.warning(f"验证卡牌 {i} 时出错: {e}")
                continue
        
        logger.info(f"验证完成，有效卡牌: {len(validated_cards)}/{len(cards_data)}")
        return validated_cards
    
    def _normalize_card_data(self, card: Dict[str, Any]) -> Dict[str, Any]:
        """标准化卡牌数据"""
        normalized = card.copy()
        
        # 标准化花色
        suit_mapping = {
            '♠': 'spades', 'spades': 'spades', '黑桃': 'spades',
            '♥': 'hearts', 'hearts': 'hearts', '红桃': 'hearts',
            '♣': 'clubs', 'clubs': 'clubs', '梅花': 'clubs',
            '♦': 'diamonds', 'diamonds': 'diamonds', '方块': 'diamonds'
        }
        
        if card['suit'] in suit_mapping:
            normalized['suit'] = suit_mapping[card['suit']]
        
        # 标准化点数（支持number或rank字段）
        number_value = card.get('number') or card.get('rank', 1)
        if isinstance(number_value, str):
            number_mapping = {
                'A': 1, 'J': 11, 'Q': 12, 'K': 13,
                '1': 1, '11': 11, '12': 12, '13': 13
            }
            if number_value in number_mapping:
                normalized['number'] = number_mapping[number_value]
            else:
                try:
                    normalized['number'] = int(number_value)
                except ValueError:
                    normalized['number'] = 1
        else:
            normalized['number'] = int(number_value)
        
        # 添加默认字段
        normalized.setdefault('category', 'basic')
        normalized.setdefault('subtype', '')
        normalized.setdefault('effect', '')
        
        return normalized
    
    def _preprocess_cards(self, cards: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """预处理卡牌数据"""
        processed_cards = []
        
        for card in cards:
            processed_card = card.copy()
            
            # 添加计算字段
            processed_card['color'] = self._get_card_color(card['suit'])
            processed_card['is_red'] = processed_card['color'] == 'red'
            processed_card['is_black'] = processed_card['color'] == 'black'
            processed_card['display_name'] = self._get_display_name(card)
            processed_card['sort_key'] = self._get_sort_key(card)
            
            processed_cards.append(processed_card)
        
        # 按排序键排序
        processed_cards.sort(key=lambda x: x['sort_key'])
        
        return processed_cards
    
    def _get_card_color(self, suit: str) -> str:
        """获取卡牌颜色"""
        red_suits = ['hearts', 'diamonds', '红桃', '方块', '♥', '♦']
        return 'red' if suit in red_suits else 'black'
    
    def _get_display_name(self, card: Dict[str, Any]) -> str:
        """获取显示名称"""
        suit_symbols = {
            'spades': '♠', 'hearts': '♥', 'clubs': '♣', 'diamonds': '♦'
        }
        
        suit_symbol = suit_symbols.get(card['suit'], card['suit'])
        number_display = card['number']
        
        if number_display == 1:
            number_display = 'A'
        elif number_display == 11:
            number_display = 'J'
        elif number_display == 12:
            number_display = 'Q'
        elif number_display == 13:
            number_display = 'K'
        
        return f"{suit_symbol}{number_display} {card['name']}"
    
    def _get_sort_key(self, card: Dict[str, Any]) -> Tuple[str, int, str]:
        """获取排序键"""
        type_order = {'basic': 0, 'trick': 1, 'equipment': 2}
        suit_order = {'spades': 0, 'hearts': 1, 'clubs': 2, 'diamonds': 3}
        
        return (
            type_order.get(card.get('type', 'basic'), 99),
            suit_order.get(card['suit'], 99),
            card.get('number', card.get('rank', 1))
        )
    
    @lru_cache(maxsize=128)
    def get_cards_by_type(self, card_type: str) -> List[Dict[str, Any]]:
        """按类型获取卡牌（带缓存）"""
        cards = self.load_cards()
        return [card for card in cards if card.get('type') == card_type]
    
    @lru_cache(maxsize=128)
    def get_cards_by_suit(self, suit: str) -> List[Dict[str, Any]]:
        """按花色获取卡牌（带缓存）"""
        cards = self.load_cards()
        return [card for card in cards if card.get('suit') == suit]
    
    def get_cards_by_name(self, name: str) -> List[Dict[str, Any]]:
        """按名称获取卡牌"""
        cards = self.load_cards()
        return [card for card in cards if card.get('name') == name]
    
    def search_cards(self, **criteria) -> List[Dict[str, Any]]:
        """搜索卡牌"""
        cards = self.load_cards()
        results = []
        
        for card in cards:
            match = True
            for key, value in criteria.items():
                if key not in card or card[key] != value:
                    match = False
                    break
            if match:
                results.append(card)
        
        return results
    
    def get_load_stats(self) -> Dict[str, Any]:
        """获取加载统计信息"""
        stats = self.load_stats.copy()
        
        if stats['load_times']:
            stats['avg_load_time'] = sum(stats['load_times']) / len(stats['load_times'])
            stats['max_load_time'] = max(stats['load_times'])
            stats['min_load_time'] = min(stats['load_times'])
        else:
            stats['avg_load_time'] = 0
            stats['max_load_time'] = 0
            stats['min_load_time'] = 0
        
        if self.cache:
            stats['cache_stats'] = self.cache.get_stats()
        
        return stats
    
    def clear_cache(self) -> None:
        """清空缓存"""
        if self.cache:
            self.cache.clear()
        
        # 清空LRU缓存
        self.get_cards_by_type.cache_clear()
        self.get_cards_by_suit.cache_clear()
        
        logger.info("缓存已清空")

class AsyncCardLoader:
    """异步卡牌加载器"""
    
    def __init__(self, cards_file: str = None, max_workers: int = 4):
        self.loader = OptimizedCardLoader(cards_file)
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        self.futures = {}
    
    def load_cards_async(self, callback=None) -> str:
        """异步加载卡牌数据"""
        task_id = f"load_{int(time.time() * 1000)}"
        
        def load_task():
            try:
                cards = self.loader.load_cards()
                if callback:
                    callback(cards, None)
                return cards
            except Exception as e:
                if callback:
                    callback(None, e)
                raise
        
        future = self.executor.submit(load_task)
        self.futures[task_id] = future
        
        return task_id
    
    def get_result(self, task_id: str, timeout: float = None) -> List[Dict[str, Any]]:
        """获取异步加载结果"""
        if task_id not in self.futures:
            raise ValueError(f"任务ID不存在: {task_id}")
        
        future = self.futures[task_id]
        try:
            result = future.result(timeout=timeout)
            del self.futures[task_id]  # 清理完成的任务
            return result
        except Exception as e:
            del self.futures[task_id]  # 清理失败的任务
            raise
    
    def is_ready(self, task_id: str) -> bool:
        """检查任务是否完成"""
        if task_id not in self.futures:
            return False
        return self.futures[task_id].done()
    
    def cancel_task(self, task_id: str) -> bool:
        """取消任务"""
        if task_id not in self.futures:
            return False
        
        future = self.futures[task_id]
        cancelled = future.cancel()
        if cancelled:
            del self.futures[task_id]
        return cancelled
    
    def shutdown(self):
        """关闭异步加载器"""
        self.executor.shutdown(wait=True)

# 全局加载器实例
_global_loader = None
_loader_lock = threading.Lock()

def get_card_loader(cards_file: str = None) -> OptimizedCardLoader:
    """获取全局卡牌加载器实例"""
    global _global_loader
    
    with _loader_lock:
        if _global_loader is None or (cards_file and _global_loader.cards_file != cards_file):
            _global_loader = OptimizedCardLoader(cards_file)
        return _global_loader

def load_cards_optimized(cards_file: str = None, force_reload: bool = False) -> List[Dict[str, Any]]:
    """优化的卡牌加载函数"""
    loader = get_card_loader(cards_file)
    return loader.load_cards(force_reload=force_reload)

# 演示函数
def demo_optimized_loading():
    """演示优化的加载系统"""
    print("=== 优化卡牌加载系统演示 ===")
    
    # 创建加载器
    loader = OptimizedCardLoader()
    
    # 性能测试
    print("\n性能测试:")
    start_time = time.time()
    
    # 首次加载
    cards1 = loader.load_cards()
    first_load_time = time.time() - start_time
    print(f"首次加载: {first_load_time:.3f}s, {len(cards1)} 张卡牌")
    
    # 缓存加载
    start_time = time.time()
    cards2 = loader.load_cards()
    cache_load_time = time.time() - start_time
    print(f"缓存加载: {cache_load_time:.3f}s, {len(cards2)} 张卡牌")
    
    # 搜索测试
    print("\n搜索测试:")
    basic_cards = loader.get_cards_by_type('basic')
    print(f"基本牌: {len(basic_cards)} 张")
    
    spades_cards = loader.get_cards_by_suit('spades')
    print(f"黑桃牌: {len(spades_cards)} 张")
    
    # 统计信息
    print("\n加载统计:")
    stats = loader.get_load_stats()
    for key, value in stats.items():
        if key != 'errors' or value:
            print(f"  {key}: {value}")
    
    # 异步加载测试
    print("\n异步加载测试:")
    async_loader = AsyncCardLoader()
    
    def async_callback(cards, error):
        if error:
            print(f"异步加载失败: {error}")
        else:
            print(f"异步加载完成: {len(cards)} 张卡牌")
    
    task_id = async_loader.load_cards_async(callback=async_callback)
    print(f"异步任务已启动: {task_id}")
    
    # 等待结果
    try:
        result = async_loader.get_result(task_id, timeout=5.0)
        print(f"异步结果获取成功: {len(result)} 张卡牌")
    except Exception as e:
        print(f"异步结果获取失败: {e}")
    
    async_loader.shutdown()
    
    return loader

if __name__ == "__main__":
    demo_optimized_loading()