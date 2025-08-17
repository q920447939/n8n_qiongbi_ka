"""
用户事件记录装饰器
提供简洁的注解方式来记录用户事件，支持同步和异步函数
"""
import asyncio
import time
import inspect
import logging
from functools import wraps
from typing import Dict, Any, Optional, Callable, Union
from datetime import datetime
try:
    from fastapi import Request
except ImportError:
    Request = None
from event_models import UserEventLogCreate, EventType, EventStatus, EventLogConfig
from event_log_strategy import EventLogStrategy
from event_log_strategy_factory import EventLogStrategyFactory
from event_log_config import get_config_manager

logger = logging.getLogger(__name__)


class EventLogDecorator:
    """事件记录装饰器类"""
    
    def __init__(self):
        self.config_manager = get_config_manager()
        self._strategy_cache: Dict[str, EventLogStrategy] = {}
    
    def get_strategy(self, strategy_name: Optional[str] = None) -> EventLogStrategy:
        """
        获取事件记录策略实例
        
        Args:
            strategy_name: 策略名称，如果为None则使用默认策略
            
        Returns:
            EventLogStrategy: 策略实例
        """
        if strategy_name is None:
            # 使用默认策略配置
            default_config = self.config_manager.get_default_strategy_config()
            cache_key = f"default_{hash(str(default_config))}"
            
            if cache_key not in self._strategy_cache:
                self._strategy_cache[cache_key] = EventLogStrategyFactory.create_from_config(default_config)
            
            return self._strategy_cache[cache_key]
        else:
            # 使用指定策略
            if strategy_name not in self._strategy_cache:
                strategy_config = self.config_manager.get_strategy_config(strategy_name)
                self._strategy_cache[strategy_name] = EventLogStrategyFactory.create_strategy(
                    strategy_name, strategy_config
                )
            
            return self._strategy_cache[strategy_name]
    
    def extract_request_info(self, *args, **kwargs) -> Dict[str, Any]:
        """
        从函数参数中提取请求信息
        
        Args:
            *args: 位置参数
            **kwargs: 关键字参数
            
        Returns:
            Dict[str, Any]: 请求信息
        """
        request_info = {}
        
        # 查找Request对象
        request = None
        if Request is not None:  # 只有在FastAPI可用时才检查
            for arg in args:
                if isinstance(arg, Request):
                    request = arg
                    break

            if not request:
                # 从kwargs中查找
                for value in kwargs.values():
                    if isinstance(value, Request):
                        request = value
                        break
        
        if request:
            # 提取请求信息
            request_info.update({
                'request_ip': self._get_client_ip(request),
                'user_agent': request.headers.get('user-agent'),
                'request_method': request.method,
                'request_path': str(request.url.path),
                'request_params': dict(request.query_params) if request.query_params else None,
            })
            
            # 尝试提取用户ID和会话ID
            request_info['user_id'] = self._extract_user_id(request)
            request_info['session_id'] = self._extract_session_id(request)
        
        return request_info
    
    def _get_client_ip(self, request: Request) -> Optional[str]:
        """获取客户端IP地址"""
        # 优先从X-Forwarded-For获取
        forwarded_for = request.headers.get('x-forwarded-for')
        if forwarded_for:
            return forwarded_for.split(',')[0].strip()
        
        # 从X-Real-IP获取
        real_ip = request.headers.get('x-real-ip')
        if real_ip:
            return real_ip
        
        # 从客户端地址获取
        if hasattr(request, 'client') and request.client:
            return request.client.host
        
        return None
    
    def _extract_user_id(self, request: Request) -> Optional[str]:
        """提取用户ID"""
        # 从请求头获取
        user_id = request.headers.get('x-user-id')
        if user_id:
            return user_id
        
        # 从查询参数获取
        user_id = request.query_params.get('user_id')
        if user_id:
            return user_id
        
        # 可以在这里添加更多的用户ID提取逻辑
        # 比如从JWT token中解析，从session中获取等
        
        return None
    
    def _extract_session_id(self, request: Request) -> Optional[str]:
        """提取会话ID"""
        # 从请求头获取
        session_id = request.headers.get('x-session-id')
        if session_id:
            return session_id
        
        # 从Cookie获取
        session_id = request.cookies.get('session_id')
        if session_id:
            return session_id
        
        return None
    
    def create_event_data(
        self,
        event_type: Union[str, EventType],
        event_name: str,
        request_info: Dict[str, Any],
        config: EventLogConfig,
        response_status: Optional[int] = None,
        response_time: Optional[float] = None,
        error_message: Optional[str] = None,
        custom_data: Optional[Dict[str, Any]] = None
    ) -> UserEventLogCreate:
        """
        创建事件数据
        
        Args:
            event_type: 事件类型
            event_name: 事件名称
            request_info: 请求信息
            config: 事件记录配置
            response_status: 响应状态码
            response_time: 响应时间
            error_message: 错误信息
            custom_data: 自定义数据
            
        Returns:
            UserEventLogCreate: 事件数据
        """
        # 确定事件状态
        if error_message:
            event_status = EventStatus.ERROR
        elif response_status and response_status >= 400:
            event_status = EventStatus.FAILED
        else:
            event_status = EventStatus.SUCCESS
        
        # 构建事件数据
        event_data = UserEventLogCreate(
            event_type=event_type,
            event_name=event_name,
            event_status=event_status,
            error_message=error_message
        )
        
        # 添加请求信息（根据配置）
        if config.include_request and request_info:
            if config.include_user_agent:
                event_data.user_agent = request_info.get('user_agent')
            
            event_data.user_id = request_info.get('user_id')
            event_data.session_id = request_info.get('session_id')
            event_data.request_ip = request_info.get('request_ip')
            event_data.request_method = request_info.get('request_method')
            event_data.request_path = request_info.get('request_path')
            
            if config.include_request_params:
                params = request_info.get('request_params')
                if params:
                    # 限制参数长度
                    params_str = str(params)
                    if len(params_str) > config.max_param_length:
                        params_str = params_str[:config.max_param_length] + "..."
                        params = {'_truncated': True, '_original_length': len(str(params)), '_data': params_str}
                    event_data.request_params = params
        
        # 添加响应信息（根据配置）
        if config.include_response:
            event_data.response_status = response_status
            event_data.response_time = response_time
        
        # 添加自定义数据
        if custom_data or config.custom_data:
            merged_custom_data = {}
            if config.custom_data:
                merged_custom_data.update(config.custom_data)
            if custom_data:
                merged_custom_data.update(custom_data)
            event_data.event_data = merged_custom_data
        
        return event_data
    
    async def log_event_async(
        self,
        strategy: EventLogStrategy,
        event_data: UserEventLogCreate,
        config: EventLogConfig
    ) -> None:
        """
        异步记录事件
        
        Args:
            strategy: 记录策略
            event_data: 事件数据
            config: 配置
        """
        try:
            if config.async_logging:
                # 异步记录，不阻塞主流程
                asyncio.create_task(strategy.log_event(event_data))
            else:
                # 同步记录
                await strategy.log_event(event_data)
        except Exception as e:
            logger.error(f"记录事件失败: {str(e)}")


# 全局装饰器实例
_decorator_instance = EventLogDecorator()


def user_event_log(
    event_type: Union[str, EventType] = EventType.API_CALL,
    event_name: str = "",
    strategy: Optional[str] = None,
    config: Optional[Dict[str, Any]] = None
):

    def decorator(func: Callable) -> Callable:
        # 解析配置
        event_config = EventLogConfig(**(config or {}))
        
        # 如果没有提供事件名称，使用函数名
        final_event_name = event_name or func.__name__
        
        if inspect.iscoroutinefunction(func):
            # 异步函数装饰器
            @wraps(func)
            async def async_wrapper(*args, **kwargs):
                # 检查是否启用事件记录
                if not _decorator_instance.config_manager.is_enabled() or not event_config.enabled:
                    return await func(*args, **kwargs)
                
                start_time = time.time()
                request_info = _decorator_instance.extract_request_info(*args, **kwargs)
                response_status = None
                error_message = None
                
                try:
                    # 执行原函数
                    result = await func(*args, **kwargs)
                    
                    # 尝试从结果中提取状态码
                    if hasattr(result, 'status_code'):
                        response_status = result.status_code
                    elif isinstance(result, dict) and 'code' in result:
                        response_status = result['code']
                    
                    return result
                    
                except Exception as e:
                    error_message = str(e)
                    response_status = 500
                    raise
                    
                finally:
                    # 记录事件
                    try:
                        response_time = (time.time() - start_time) * 1000  # 转换为毫秒
                        
                        event_data = _decorator_instance.create_event_data(
                            event_type=event_type,
                            event_name=final_event_name,
                            request_info=request_info,
                            config=event_config,
                            response_status=response_status,
                            response_time=response_time,
                            error_message=error_message
                        )
                        
                        strategy_instance = _decorator_instance.get_strategy(strategy)
                        await _decorator_instance.log_event_async(strategy_instance, event_data, event_config)
                        
                    except Exception as log_error:
                        logger.error(f"事件记录装饰器内部错误: {str(log_error)}")
            
            return async_wrapper
        
        else:
            # 同步函数装饰器
            @wraps(func)
            def sync_wrapper(*args, **kwargs):
                # 检查是否启用事件记录
                if not _decorator_instance.config_manager.is_enabled() or not event_config.enabled:
                    return func(*args, **kwargs)
                
                start_time = time.time()
                request_info = _decorator_instance.extract_request_info(*args, **kwargs)
                response_status = None
                error_message = None
                
                try:
                    # 执行原函数
                    result = func(*args, **kwargs)
                    
                    # 尝试从结果中提取状态码
                    if hasattr(result, 'status_code'):
                        response_status = result.status_code
                    elif isinstance(result, dict) and 'code' in result:
                        response_status = result['code']
                    
                    return result
                    
                except Exception as e:
                    error_message = str(e)
                    response_status = 500
                    raise
                    
                finally:
                    # 记录事件
                    try:
                        response_time = (time.time() - start_time) * 1000  # 转换为毫秒
                        
                        event_data = _decorator_instance.create_event_data(
                            event_type=event_type,
                            event_name=final_event_name,
                            request_info=request_info,
                            config=event_config,
                            response_status=response_status,
                            response_time=response_time,
                            error_message=error_message
                        )
                        
                        strategy_instance = _decorator_instance.get_strategy(strategy)
                        
                        # 对于同步函数，如果配置为异步记录，则创建异步任务
                        if event_config.async_logging:
                            try:
                                loop = asyncio.get_event_loop()
                                loop.create_task(strategy_instance.log_event(event_data))
                            except RuntimeError:
                                # 如果没有事件循环，则同步记录
                                asyncio.run(strategy_instance.log_event(event_data))
                        else:
                            # 同步记录
                            asyncio.run(strategy_instance.log_event(event_data))
                        
                    except Exception as log_error:
                        logger.error(f"事件记录装饰器内部错误: {str(log_error)}")
            
            return sync_wrapper
    
    return decorator
