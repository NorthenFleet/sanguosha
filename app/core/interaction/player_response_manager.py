"""
玩家响应管理器
处理多玩家按顺序响应的逻辑，包括响应时间窗口、优先级处理等
"""
from typing import Dict, List, Any, Optional, Callable, Tuple
from dataclasses import dataclass
from enum import Enum
import time
import asyncio
import threading
from concurrent.futures import ThreadPoolExecutor, Future
from ..events.multi_player_event_system import GameEvent, EventResponse, ResponseType, EventPriority

class ResponseWindowState(Enum):
    """响应窗口状态"""
    CLOSED = "closed"
    OPENING = "opening"
    OPEN = "open"
    COLLECTING = "collecting"
    PROCESSING = "processing"
    CLOSING = "closing"

@dataclass
class ResponseWindow:
    """响应窗口"""
    window_id: str
    event: GameEvent
    eligible_players: List[str]
    response_order: List[str]
    timeout_seconds: float
    state: ResponseWindowState
    collected_responses: List[EventResponse]
    start_time: float
    end_time: Optional[float] = None

@dataclass
class PlayerResponseRequest:
    """玩家响应请求"""
    request_id: str
    player_id: str
    event: GameEvent
    available_options: List[Dict[str, Any]]
    timeout_seconds: float
    callback: Optional[Callable] = None

class PlayerResponseManager:
    """玩家响应管理器"""
    
    def __init__(self, 
                 players: List[str],
                 default_timeout: float = 30.0,
                 max_concurrent_windows: int = 3):
        self.players = players
        self.default_timeout = default_timeout
        self.max_concurrent_windows = max_concurrent_windows
        
        # 响应窗口管理
        self.active_windows: Dict[str, ResponseWindow] = {}
        self.window_queue: List[ResponseWindow] = []
        
        # 玩家响应处理
        self.player_response_handlers: Dict[str, Callable] = {}
        self.player_timeouts: Dict[str, float] = {}
        
        # 异步处理
        self.executor = ThreadPoolExecutor(max_workers=len(players))
        self.response_futures: Dict[str, Future] = {}
        
        # 响应统计
        self.response_stats: Dict[str, Dict[str, Any]] = {}
        
        # 初始化玩家统计
        for player_id in players:
            self.response_stats[player_id] = {
                'total_requests': 0,
                'successful_responses': 0,
                'timeouts': 0,
                'average_response_time': 0.0
            }
    
    def register_player_handler(self, player_id: str, handler: Callable):
        """注册玩家响应处理器"""
        self.player_response_handlers[player_id] = handler
    
    def set_player_timeout(self, player_id: str, timeout_seconds: float):
        """设置玩家响应超时时间"""
        self.player_timeouts[player_id] = timeout_seconds
    
    def open_response_window(self, 
                           event: GameEvent,
                           eligible_players: Optional[List[str]] = None,
                           timeout_seconds: Optional[float] = None) -> ResponseWindow:
        """开启响应窗口"""
        
        # 确定有资格响应的玩家
        if eligible_players is None:
            eligible_players = event.target_player_ids.copy()
            # 如果没有指定目标，则所有玩家都可以响应
            if not eligible_players:
                eligible_players = self.players.copy()
        
        # 确定响应顺序（从事件源玩家的下家开始逆时针）
        response_order = self._get_response_order(event.source_player_id, eligible_players)
        
        # 创建响应窗口
        window = ResponseWindow(
            window_id=f"window_{event.event_id}_{int(time.time() * 1000)}",
            event=event,
            eligible_players=eligible_players,
            response_order=response_order,
            timeout_seconds=timeout_seconds or self.default_timeout,
            state=ResponseWindowState.OPENING,
            collected_responses=[],
            start_time=time.time()
        )
        
        # 检查是否可以立即处理
        if len(self.active_windows) < self.max_concurrent_windows:
            self.active_windows[window.window_id] = window
            self._process_response_window(window)
        else:
            # 加入队列等待处理
            self.window_queue.append(window)
            print(f"响应窗口 {window.window_id} 加入等待队列")
        
        return window
    
    def _process_response_window(self, window: ResponseWindow):
        """处理响应窗口"""
        print(f"开始处理响应窗口: {window.window_id}")
        window.state = ResponseWindowState.OPEN
        
        # 为每个玩家创建响应请求
        response_requests = []
        
        for player_id in window.response_order:
            if player_id not in self.player_response_handlers:
                continue
            
            # 获取玩家的响应选项
            handler = self.player_response_handlers[player_id]
            try:
                available_options = handler.get_response_options(window.event)
            except Exception as e:
                print(f"获取玩家 {player_id} 响应选项时出错: {e}")
                available_options = []
            
            if available_options:
                # 创建响应请求
                request = PlayerResponseRequest(
                    request_id=f"req_{window.window_id}_{player_id}",
                    player_id=player_id,
                    event=window.event,
                    available_options=available_options,
                    timeout_seconds=self.player_timeouts.get(player_id, window.timeout_seconds)
                )
                response_requests.append(request)
        
        # 按优先级处理响应
        self._process_responses_by_priority(window, response_requests)
    
    def _process_responses_by_priority(self, window: ResponseWindow, requests: List[PlayerResponseRequest]):
        """按优先级处理响应"""
        window.state = ResponseWindowState.COLLECTING
        
        # 按优先级分组请求
        priority_groups = self._group_requests_by_priority(requests)
        
        # 按优先级顺序处理
        for priority in sorted(priority_groups.keys(), key=lambda x: x.value):
            group_requests = priority_groups[priority]
            
            print(f"处理优先级 {priority.name} 的响应 ({len(group_requests)} 个请求)")
            
            # 在同一优先级内按玩家顺序处理
            ordered_requests = self._order_requests_by_player_sequence(group_requests, window.response_order)
            
            # 处理这个优先级组的响应
            group_responses = self._collect_priority_group_responses(window, ordered_requests)
            
            # 检查是否有终止响应链的响应
            for response in group_responses:
                window.collected_responses.append(response)
                if self._response_terminates_chain(response):
                    print(f"响应 {response.response_id} 终止了响应链")
                    self._close_response_window(window)
                    return
        
        # 所有优先级处理完毕，关闭窗口
        self._close_response_window(window)
    
    def _group_requests_by_priority(self, requests: List[PlayerResponseRequest]) -> Dict[EventPriority, List[PlayerResponseRequest]]:
        """按优先级分组请求"""
        priority_groups = {}
        
        for request in requests:
            # 获取请求的最高优先级
            max_priority = EventPriority.LOWEST
            for option in request.available_options:
                option_priority = EventPriority(option.get('priority', EventPriority.NORMAL.value))
                if option_priority.value < max_priority.value:
                    max_priority = option_priority
            
            if max_priority not in priority_groups:
                priority_groups[max_priority] = []
            priority_groups[max_priority].append(request)
        
        return priority_groups
    
    def _order_requests_by_player_sequence(self, requests: List[PlayerResponseRequest], player_order: List[str]) -> List[PlayerResponseRequest]:
        """按玩家顺序排列请求"""
        ordered_requests = []
        
        for player_id in player_order:
            for request in requests:
                if request.player_id == player_id:
                    ordered_requests.append(request)
                    break
        
        return ordered_requests
    
    def _collect_priority_group_responses(self, window: ResponseWindow, requests: List[PlayerResponseRequest]) -> List[EventResponse]:
        """收集优先级组的响应"""
        responses = []
        
        for request in requests:
            try:
                # 请求玩家响应
                response = self._request_player_response(request)
                if response:
                    responses.append(response)
                    
                    # 更新统计信息
                    self._update_response_stats(request.player_id, True, time.time() - window.start_time)
                else:
                    # 超时或无响应
                    self._update_response_stats(request.player_id, False, request.timeout_seconds)
                    
            except Exception as e:
                print(f"处理玩家 {request.player_id} 响应时出错: {e}")
                self._update_response_stats(request.player_id, False, request.timeout_seconds)
        
        return responses
    
    def _request_player_response(self, request: PlayerResponseRequest) -> Optional[EventResponse]:
        """请求玩家响应"""
        player_id = request.player_id
        
        if player_id not in self.player_response_handlers:
            return None
        
        handler = self.player_response_handlers[player_id]
        
        # 更新统计
        self.response_stats[player_id]['total_requests'] += 1
        
        try:
            # 模拟玩家选择（实际实现中应该是异步等待玩家输入）
            selected_option = self._simulate_player_choice(request)
            
            if selected_option:
                # 执行响应
                response = handler.execute_response(request.event, selected_option['data'])
                return response
            
        except Exception as e:
            print(f"执行玩家 {player_id} 响应时出错: {e}")
        
        return None
    
    def _simulate_player_choice(self, request: PlayerResponseRequest) -> Optional[Dict[str, Any]]:
        """模拟玩家选择（实际实现中应该替换为真实的玩家交互）"""
        # 这里简化处理，选择第一个可用选项
        if request.available_options:
            # 优先选择高优先级的选项
            best_option = min(request.available_options, 
                            key=lambda x: EventPriority(x.get('priority', EventPriority.NORMAL.value)).value)
            
            # 模拟思考时间
            import random
            think_time = random.uniform(0.5, 2.0)
            time.sleep(think_time)
            
            return best_option
        
        return None
    
    def _response_terminates_chain(self, response: EventResponse) -> bool:
        """检查响应是否终止响应链"""
        terminating_actions = ['counter', 'cancel', 'redirect', 'nullify']
        action_type = response.action_data.get('action_type', '')
        
        # 检查是否是终止性动作
        if action_type in terminating_actions:
            return True
        
        # 检查卡牌名称
        card = response.action_data.get('card')
        if card and hasattr(card, 'name'):
            terminating_cards = ['无懈可击', '闪']
            if card.name in terminating_cards:
                return True
        
        return False
    
    def _close_response_window(self, window: ResponseWindow):
        """关闭响应窗口"""
        window.state = ResponseWindowState.CLOSING
        window.end_time = time.time()
        
        print(f"关闭响应窗口 {window.window_id}，收集到 {len(window.collected_responses)} 个响应")
        
        # 从活跃窗口中移除
        if window.window_id in self.active_windows:
            del self.active_windows[window.window_id]
        
        # 处理队列中的下一个窗口
        if self.window_queue and len(self.active_windows) < self.max_concurrent_windows:
            next_window = self.window_queue.pop(0)
            self.active_windows[next_window.window_id] = next_window
            self._process_response_window(next_window)
        
        window.state = ResponseWindowState.CLOSED
    
    def _get_response_order(self, source_player_id: str, eligible_players: List[str]) -> List[str]:
        """获取响应顺序"""
        try:
            source_index = self.players.index(source_player_id)
        except ValueError:
            # 如果源玩家不在列表中，从第一个玩家开始
            source_index = 0
        
        # 从源玩家的下家开始，按逆时针顺序
        order = []
        for i in range(1, len(self.players)):
            next_index = (source_index + i) % len(self.players)
            next_player = self.players[next_index]
            if next_player in eligible_players:
                order.append(next_player)
        
        return order
    
    def _update_response_stats(self, player_id: str, success: bool, response_time: float):
        """更新响应统计信息"""
        stats = self.response_stats[player_id]
        
        if success:
            stats['successful_responses'] += 1
            # 更新平均响应时间
            total_successful = stats['successful_responses']
            current_avg = stats['average_response_time']
            stats['average_response_time'] = (current_avg * (total_successful - 1) + response_time) / total_successful
        else:
            stats['timeouts'] += 1
    
    def get_response_stats(self, player_id: Optional[str] = None) -> Dict[str, Any]:
        """获取响应统计信息"""
        if player_id:
            return self.response_stats.get(player_id, {})
        return self.response_stats.copy()
    
    def get_active_windows(self) -> List[ResponseWindow]:
        """获取当前活跃的响应窗口"""
        return list(self.active_windows.values())
    
    def get_window_queue_length(self) -> int:
        """获取等待队列长度"""
        return len(self.window_queue)
    
    def force_close_window(self, window_id: str) -> bool:
        """强制关闭响应窗口"""
        if window_id in self.active_windows:
            window = self.active_windows[window_id]
            self._close_response_window(window)
            return True
        return False
    
    def clear_all_windows(self):
        """清空所有响应窗口"""
        # 关闭所有活跃窗口
        for window in list(self.active_windows.values()):
            self._close_response_window(window)
        
        # 清空队列
        self.window_queue.clear()
    
    def shutdown(self):
        """关闭响应管理器"""
        self.clear_all_windows()
        self.executor.shutdown(wait=True)

class ResponseWindowManager:
    """响应窗口管理器"""
    
    def __init__(self, response_manager: PlayerResponseManager):
        self.response_manager = response_manager
        self.window_history: List[ResponseWindow] = []
        self.window_callbacks: Dict[str, List[Callable]] = {}
    
    def register_window_callback(self, window_id: str, callback: Callable):
        """注册窗口回调"""
        if window_id not in self.window_callbacks:
            self.window_callbacks[window_id] = []
        self.window_callbacks[window_id].append(callback)
    
    def create_response_window(self, 
                             event: GameEvent,
                             eligible_players: Optional[List[str]] = None,
                             timeout_seconds: Optional[float] = None,
                             callbacks: Optional[List[Callable]] = None) -> ResponseWindow:
        """创建响应窗口"""
        
        window = self.response_manager.open_response_window(
            event, eligible_players, timeout_seconds
        )
        
        # 注册回调
        if callbacks:
            for callback in callbacks:
                self.register_window_callback(window.window_id, callback)
        
        return window
    
    def wait_for_window_completion(self, window: ResponseWindow, timeout: Optional[float] = None) -> List[EventResponse]:
        """等待窗口完成"""
        start_time = time.time()
        
        while window.state != ResponseWindowState.CLOSED:
            if timeout and (time.time() - start_time) > timeout:
                # 超时，强制关闭窗口
                self.response_manager.force_close_window(window.window_id)
                break
            
            time.sleep(0.1)  # 短暂等待
        
        # 记录到历史
        self.window_history.append(window)
        
        # 调用回调
        if window.window_id in self.window_callbacks:
            for callback in self.window_callbacks[window.window_id]:
                try:
                    callback(window)
                except Exception as e:
                    print(f"执行窗口回调时出错: {e}")
        
        return window.collected_responses
    
    def get_window_history(self) -> List[ResponseWindow]:
        """获取窗口历史"""
        return self.window_history.copy()
    
    def clear_history(self):
        """清空历史记录"""
        self.window_history.clear()
        self.window_callbacks.clear()