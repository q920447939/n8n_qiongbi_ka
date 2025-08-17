"""
缓存配置管理
定义各接口的缓存策略和参数
"""
import os
from typing import Dict, Any
from dataclasses import dataclass


@dataclass
class CacheConfig:
    """缓存配置类"""
    cache_type: str = "TTL"  # 缓存类型：TTL, LRU
    maxsize: int = 128       # 最大缓存条目数
    ttl: int = 300          # 生存时间（秒）
    enabled: bool = True     # 是否启用缓存


class CacheConfigManager:
    """缓存配置管理器"""
    
    def __init__(self):
        self._configs = self._load_default_configs()
        self._load_env_configs()
    
    def _load_default_configs(self) -> Dict[str, CacheConfig]:
        """加载默认缓存配置"""
        return {
            # 卡片列表页面缓存配置
            "card_list": CacheConfig(
                cache_type="TTL",
                maxsize=100,
                ttl=300,  # 5分钟，数据更新不频繁
                enabled=True
            ),
            
            # 订单按钮配置缓存
            "order_buttons": CacheConfig(
                cache_type="TTL",
                maxsize=1000,
                ttl=1800,  # 30分钟，按钮配置相对固定
                enabled=True
            )
        }
    
    def _load_env_configs(self):
        """从环境变量加载配置覆盖"""
        # 全局缓存开关
        global_enabled = os.getenv('CACHE_ENABLED', 'true').lower() == 'true'
        
        for cache_name, config in self._configs.items():
            # 更新启用状态
            config.enabled = global_enabled and os.getenv(
                f'CACHE_{cache_name.upper()}_ENABLED', 'true'
            ).lower() == 'true'
            
            # 更新TTL
            ttl_env = os.getenv(f'CACHE_{cache_name.upper()}_TTL')
            if ttl_env:
                try:
                    config.ttl = int(ttl_env)
                except ValueError:
                    pass
            
            # 更新maxsize
            maxsize_env = os.getenv(f'CACHE_{cache_name.upper()}_MAXSIZE')
            if maxsize_env:
                try:
                    config.maxsize = int(maxsize_env)
                except ValueError:
                    pass
    
    def get_config(self, cache_name: str) -> CacheConfig:
        """获取指定缓存的配置"""
        return self._configs.get(cache_name, CacheConfig())
    
    def is_cache_enabled(self, cache_name: str) -> bool:
        """检查指定缓存是否启用"""
        config = self.get_config(cache_name)
        return config.enabled
    
    def get_all_cache_names(self) -> list[str]:
        """获取所有缓存名称"""
        return list(self._configs.keys())
    
    def reload_config(self):
        """重新加载配置"""
        self._configs = self._load_default_configs()
        self._load_env_configs()


# 全局配置管理器实例
cache_config_manager = CacheConfigManager()
