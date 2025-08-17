"""
缓存管理器
统一管理所有缓存实例，提供缓存操作和统计功能
"""
import logging
import threading
import time
from typing import Dict, Any, Optional, List
from cache_config import cache_config_manager, CacheConfig

logger = logging.getLogger(__name__)


class SimpleTTLCache:
    """简单的TTL缓存实现"""

    def __init__(self, maxsize: int = 128, ttl: int = 300):
        self.maxsize = maxsize
        self.ttl = ttl
        self._cache = {}
        self._timestamps = {}
        self._lock = threading.Lock()

    def _is_expired(self, key):
        """检查键是否过期"""
        if key not in self._timestamps:
            return True
        return time.time() - self._timestamps[key] > self.ttl

    def _cleanup_expired(self):
        """清理过期的键"""
        current_time = time.time()
        expired_keys = [
            key for key, timestamp in self._timestamps.items()
            if current_time - timestamp > self.ttl
        ]
        for key in expired_keys:
            self._cache.pop(key, None)
            self._timestamps.pop(key, None)

    def __contains__(self, key):
        """检查键是否存在且未过期"""
        with self._lock:
            if key not in self._cache:
                return False
            if self._is_expired(key):
                self._cache.pop(key, None)
                self._timestamps.pop(key, None)
                return False
            return True

    def __getitem__(self, key):
        """获取缓存值"""
        with self._lock:
            if key not in self._cache or self._is_expired(key):
                raise KeyError(key)
            return self._cache[key]

    def __setitem__(self, key, value):
        """设置缓存值"""
        with self._lock:
            # 如果缓存已满，删除最旧的项
            if len(self._cache) >= self.maxsize and key not in self._cache:
                oldest_key = min(self._timestamps.keys(), key=self._timestamps.get)
                self._cache.pop(oldest_key, None)
                self._timestamps.pop(oldest_key, None)

            self._cache[key] = value
            self._timestamps[key] = time.time()

    def get(self, key, default=None):
        """获取缓存值，如果不存在返回默认值"""
        try:
            return self[key]
        except KeyError:
            return default

    def clear(self):
        """清空缓存"""
        with self._lock:
            self._cache.clear()
            self._timestamps.clear()

    def keys(self):
        """获取所有有效的键"""
        with self._lock:
            self._cleanup_expired()
            return list(self._cache.keys())

    def __len__(self):
        """获取缓存大小"""
        with self._lock:
            self._cleanup_expired()
            return len(self._cache)


class SimpleLRUCache:
    """简单的LRU缓存实现"""

    def __init__(self, maxsize: int = 128):
        self.maxsize = maxsize
        self._cache = {}
        self._access_order = []
        self._lock = threading.Lock()

    def __contains__(self, key):
        return key in self._cache

    def __getitem__(self, key):
        with self._lock:
            if key not in self._cache:
                raise KeyError(key)
            # 更新访问顺序
            self._access_order.remove(key)
            self._access_order.append(key)
            return self._cache[key]

    def __setitem__(self, key, value):
        with self._lock:
            if key in self._cache:
                # 更新现有键
                self._access_order.remove(key)
            elif len(self._cache) >= self.maxsize:
                # 删除最少使用的项
                lru_key = self._access_order.pop(0)
                del self._cache[lru_key]

            self._cache[key] = value
            self._access_order.append(key)

    def get(self, key, default=None):
        try:
            return self[key]
        except KeyError:
            return default

    def clear(self):
        with self._lock:
            self._cache.clear()
            self._access_order.clear()

    def keys(self):
        return list(self._cache.keys())

    def __len__(self):
        return len(self._cache)


class CacheStats:
    """缓存统计信息"""
    
    def __init__(self):
        self.hits = 0
        self.misses = 0
        self.created_at = time.time()
    
    @property
    def hit_rate(self) -> float:
        """缓存命中率"""
        total = self.hits + self.misses
        return self.hits / total if total > 0 else 0.0
    
    def record_hit(self):
        """记录缓存命中"""
        self.hits += 1
    
    def record_miss(self):
        """记录缓存未命中"""
        self.misses += 1
    
    def reset(self):
        """重置统计"""
        self.hits = 0
        self.misses = 0
        self.created_at = time.time()
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            'hits': self.hits,
            'misses': self.misses,
            'hit_rate': round(self.hit_rate, 4),
            'total_requests': self.hits + self.misses,
            'created_at': self.created_at,
            'uptime_seconds': round(time.time() - self.created_at, 2)
        }


class CacheManager:
    """缓存管理器 - 单例模式"""
    
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if hasattr(self, '_initialized'):
            return
        
        self._caches: Dict[str, Any] = {}
        self._cache_locks: Dict[str, threading.Lock] = {}
        self._stats: Dict[str, CacheStats] = {}
        self._initialized = True
        logger.info("缓存管理器初始化完成")
    
    def _create_cache(self, cache_name: str, config: CacheConfig):
        """创建缓存实例"""
        if config.cache_type == "TTL":
            cache = SimpleTTLCache(maxsize=config.maxsize, ttl=config.ttl)
        elif config.cache_type == "LRU":
            cache = SimpleLRUCache(maxsize=config.maxsize)
        else:
            raise ValueError(f"不支持的缓存类型: {config.cache_type}")

        self._caches[cache_name] = cache
        self._cache_locks[cache_name] = threading.Lock()
        self._stats[cache_name] = CacheStats()

        logger.info(f"创建缓存实例: {cache_name}, 类型: {config.cache_type}, "
                   f"大小: {config.maxsize}, TTL: {config.ttl if config.cache_type == 'TTL' else 'N/A'}")
    
    def get_cache(self, cache_name: str):
        """获取缓存实例"""
        if cache_name not in self._caches:
            config = cache_config_manager.get_config(cache_name)
            if config.enabled:
                self._create_cache(cache_name, config)
            else:
                return None
        
        return self._caches.get(cache_name)
    
    def get_cache_lock(self, cache_name: str) -> threading.Lock:
        """获取缓存锁"""
        if cache_name not in self._cache_locks:
            self.get_cache(cache_name)  # 确保缓存和锁都被创建
        return self._cache_locks.get(cache_name, threading.Lock())
    
    def get_stats(self, cache_name: str) -> Optional[CacheStats]:
        """获取缓存统计信息"""
        return self._stats.get(cache_name)
    
    def record_hit(self, cache_name: str):
        """记录缓存命中"""
        if cache_name in self._stats:
            self._stats[cache_name].record_hit()
    
    def record_miss(self, cache_name: str):
        """记录缓存未命中"""
        if cache_name in self._stats:
            self._stats[cache_name].record_miss()
    
    def clear_cache(self, cache_name: Optional[str] = None) -> Dict[str, Any]:
        """清理缓存
        
        Args:
            cache_name: 缓存名称，为None时清理所有缓存
            
        Returns:
            Dict: 清理结果
        """
        result = {
            'success': True,
            'cleared_caches': [],
            'errors': []
        }
        
        try:
            if cache_name:
                # 清理指定缓存
                if cache_name in self._caches:
                    with self.get_cache_lock(cache_name):
                        self._caches[cache_name].clear()
                        if cache_name in self._stats:
                            self._stats[cache_name].reset()
                    result['cleared_caches'].append(cache_name)
                    logger.info(f"已清理缓存: {cache_name}")
                else:
                    result['errors'].append(f"缓存不存在: {cache_name}")
            else:
                # 清理所有缓存
                for name in list(self._caches.keys()):
                    try:
                        with self.get_cache_lock(name):
                            self._caches[name].clear()
                            if name in self._stats:
                                self._stats[name].reset()
                        result['cleared_caches'].append(name)
                    except Exception as e:
                        result['errors'].append(f"清理缓存 {name} 失败: {str(e)}")
                
                logger.info(f"已清理所有缓存，共 {len(result['cleared_caches'])} 个")
        
        except Exception as e:
            result['success'] = False
            result['errors'].append(f"清理缓存失败: {str(e)}")
            logger.error(f"清理缓存失败: {str(e)}")
        
        return result
    


# 全局缓存管理器实例
cache_manager = CacheManager()
