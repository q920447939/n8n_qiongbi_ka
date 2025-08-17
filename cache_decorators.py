"""
缓存装饰器
提供便捷的缓存功能装饰器
"""
import logging
import hashlib
import json
import functools
import inspect
from typing import Callable, Any, Optional, Union
from cache_manager import cache_manager
from cache_config import cache_config_manager

logger = logging.getLogger(__name__)


def _generate_cache_key(func_name: str, args: tuple, kwargs: dict, key_func: Optional[Callable] = None) -> str:
    """生成缓存键
    
    Args:
        func_name: 函数名
        args: 位置参数
        kwargs: 关键字参数
        key_func: 自定义键生成函数
        
    Returns:
        str: 缓存键
    """
    if key_func:
        try:
            # 使用自定义键生成函数
            custom_key = key_func(*args, **kwargs)
            return f"{func_name}:{custom_key}"
        except Exception as e:
            logger.warning(f"自定义键生成函数失败: {str(e)}, 使用默认方式")
    
    # 默认键生成方式
    try:
        # 处理参数，确保可序列化
        serializable_args = []
        for arg in args:
            if hasattr(arg, '__dict__'):
                # 对象类型，尝试序列化其属性
                serializable_args.append(str(arg))
            else:
                serializable_args.append(arg)
        
        serializable_kwargs = {}
        for k, v in kwargs.items():
            if hasattr(v, '__dict__'):
                serializable_kwargs[k] = str(v)
            else:
                serializable_kwargs[k] = v
        
        # 创建键内容
        key_content = {
            'func': func_name,
            'args': serializable_args,
            'kwargs': serializable_kwargs
        }
        
        # 序列化并生成哈希
        key_str = json.dumps(key_content, sort_keys=True, ensure_ascii=False)
        key_hash = hashlib.md5(key_str.encode('utf-8')).hexdigest()
        
        return f"{func_name}:{key_hash}"
    
    except Exception as e:
        logger.warning(f"生成缓存键失败: {str(e)}, 使用简单键")
        return f"{func_name}:simple_key"


def api_cache(cache_name: str, key_func: Optional[Callable] = None):
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            # 检查缓存是否启用
            if not cache_config_manager.is_cache_enabled(cache_name):
                logger.debug(f"缓存 {cache_name} 未启用，直接执行函数")
                return await func(*args, **kwargs)
            
            # 获取缓存实例
            cache = cache_manager.get_cache(cache_name)
            if cache is None:
                logger.debug(f"缓存 {cache_name} 不可用，直接执行函数")
                return await func(*args, **kwargs)
            
            # 生成缓存键
            cache_key = _generate_cache_key(func.__name__, args, kwargs, key_func)
            
            # 尝试从缓存获取
            cache_lock = cache_manager.get_cache_lock(cache_name)
            with cache_lock:
                if cache_key in cache:
                    cache_manager.record_hit(cache_name)
                    logger.debug(f"缓存命中: {cache_name}:{cache_key}")
                    return cache[cache_key]
            
            # 缓存未命中，执行函数
            cache_manager.record_miss(cache_name)
            logger.debug(f"缓存未命中: {cache_name}:{cache_key}")
            
            try:
                result = await func(*args, **kwargs)
                
                # 将结果存入缓存
                with cache_lock:
                    cache[cache_key] = result
                
                logger.debug(f"结果已缓存: {cache_name}:{cache_key}")
                return result
            
            except Exception as e:
                logger.error(f"函数执行失败: {str(e)}")
                raise
        
        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            # 检查缓存是否启用
            if not cache_config_manager.is_cache_enabled(cache_name):
                logger.debug(f"缓存 {cache_name} 未启用，直接执行函数")
                return func(*args, **kwargs)
            
            # 获取缓存实例
            cache = cache_manager.get_cache(cache_name)
            if cache is None:
                logger.debug(f"缓存 {cache_name} 不可用，直接执行函数")
                return func(*args, **kwargs)
            
            # 生成缓存键
            cache_key = _generate_cache_key(func.__name__, args, kwargs, key_func)
            
            # 尝试从缓存获取
            cache_lock = cache_manager.get_cache_lock(cache_name)
            with cache_lock:
                if cache_key in cache:
                    cache_manager.record_hit(cache_name)
                    logger.debug(f"缓存命中: {cache_name}:{cache_key}")
                    return cache[cache_key]
            
            # 缓存未命中，执行函数
            cache_manager.record_miss(cache_name)
            logger.debug(f"缓存未命中: {cache_name}:{cache_key}")
            
            try:
                result = func(*args, **kwargs)
                
                # 将结果存入缓存
                with cache_lock:
                    cache[cache_key] = result
                
                logger.debug(f"结果已缓存: {cache_name}:{cache_key}")
                return result
            
            except Exception as e:
                logger.error(f"函数执行失败: {str(e)}")
                raise
        
        # 根据函数类型返回对应的包装器
        if inspect.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator


def cache_clear_key(cache_name: str, key_pattern: str):
    """清理指定缓存的特定键模式
    
    Args:
        cache_name: 缓存名称
        key_pattern: 键模式（支持*通配符）
    """
    return cache_manager.clear_cache_by_pattern(key_pattern)


def cache_clear_all():
    """清理所有缓存"""
    return cache_manager.clear_cache()


def cache_clear(cache_name: str):
    """清理指定缓存"""
    return cache_manager.clear_cache(cache_name)
