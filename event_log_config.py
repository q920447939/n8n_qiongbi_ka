"""
事件记录配置管理
负责管理事件记录系统的配置，支持动态配置和环境变量
"""
import os
import json
import logging
from typing import Dict, Any, Optional, List
from pathlib import Path
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class EventLogSettings:
    """事件记录系统设置"""

    def __init__(self):
        # 基础设置
        self.enabled = os.getenv("EVENT_LOG_ENABLED", "true").lower() == "true"
        self.default_strategy = os.getenv("EVENT_LOG_DEFAULT_STRATEGY", "database_log")
        self.async_logging = os.getenv("EVENT_LOG_ASYNC_LOGGING", "true").lower() == "true"

        # 数据库设置
        self.db_table_name = os.getenv("EVENT_LOG_DB_TABLE_NAME", "user_event_logs")
        self.db_batch_size = int(os.getenv("EVENT_LOG_DB_BATCH_SIZE", "100"))

        # 文件设置
        self.file_log_path = os.getenv("EVENT_LOG_FILE_LOG_PATH", "logs/events.log")
        self.file_log_format = os.getenv("EVENT_LOG_FILE_LOG_FORMAT", "json")
        self.file_max_size = int(os.getenv("EVENT_LOG_FILE_MAX_SIZE", str(100 * 1024 * 1024)))

        # 远程设置
        self.remote_endpoint = os.getenv("EVENT_LOG_REMOTE_ENDPOINT")
        self.remote_api_key = os.getenv("EVENT_LOG_REMOTE_API_KEY")
        self.remote_timeout = int(os.getenv("EVENT_LOG_REMOTE_TIMEOUT", "30"))

        # 过滤设置
        allowed_types_str = os.getenv("EVENT_LOG_ALLOWED_EVENT_TYPES")
        self.allowed_event_types = allowed_types_str.split(",") if allowed_types_str else None

        excluded_names_str = os.getenv("EVENT_LOG_EXCLUDED_EVENT_NAMES", "")
        self.excluded_event_names = excluded_names_str.split(",") if excluded_names_str else []

        # 性能设置
        self.max_queue_size = int(os.getenv("EVENT_LOG_MAX_QUEUE_SIZE", "1000"))
        self.flush_interval = int(os.getenv("EVENT_LOG_FLUSH_INTERVAL", "5"))

    def model_dump(self):
        """兼容pydantic的model_dump方法"""
        return {
            "enabled": self.enabled,
            "default_strategy": self.default_strategy,
            "async_logging": self.async_logging,
            "db_table_name": self.db_table_name,
            "db_batch_size": self.db_batch_size,
            "file_log_path": self.file_log_path,
            "file_log_format": self.file_log_format,
            "file_max_size": self.file_max_size,
            "remote_endpoint": self.remote_endpoint,
            "remote_api_key": self.remote_api_key,
            "remote_timeout": self.remote_timeout,
            "allowed_event_types": self.allowed_event_types,
            "excluded_event_names": self.excluded_event_names,
            "max_queue_size": self.max_queue_size,
            "flush_interval": self.flush_interval,
        }


class EventLogConfigManager:
    """事件记录配置管理器"""
    
    def __init__(self, config_file: Optional[str] = None):
        """
        初始化配置管理器
        
        Args:
            config_file: 配置文件路径
        """
        self.config_file = config_file or "config/event_log_config.json"
        self.settings = EventLogSettings()
        self._config_cache: Dict[str, Any] = {}
        self._load_config()
    
    def _load_config(self) -> None:
        """加载配置文件"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    file_config = json.load(f)
                    self._config_cache.update(file_config)
                    logger.info(f"成功加载事件记录配置文件: {self.config_file}")
            else:
                logger.info(f"配置文件不存在，使用默认配置: {self.config_file}")
        except Exception as e:
            logger.error(f"加载配置文件失败: {str(e)}")
    
    def get_strategy_config(self, strategy_name: str) -> Dict[str, Any]:
        """
        获取策略配置
        
        Args:
            strategy_name: 策略名称
            
        Returns:
            Dict[str, Any]: 策略配置
        """
        # 从缓存中获取策略配置
        strategies_config = self._config_cache.get('strategies', {})
        strategy_config = strategies_config.get(strategy_name, {})
        
        # 合并默认配置
        if strategy_name == 'database_log':
            default_config = {
                'enabled': self.settings.enabled,
                'table_name': self.settings.db_table_name,
                'batch_size': self.settings.db_batch_size,
            }
        elif strategy_name == 'file_log':
            default_config = {
                'enabled': self.settings.enabled,
                'log_file': self.settings.file_log_path,
                'log_format': self.settings.file_log_format,
                'max_file_size': self.settings.file_max_size,
            }
        elif strategy_name == 'remote_log':
            default_config = {
                'enabled': self.settings.enabled and bool(self.settings.remote_endpoint),
                'endpoint_url': self.settings.remote_endpoint,
                'api_key': self.settings.remote_api_key,
                'timeout': self.settings.remote_timeout,
            }
        else:
            default_config = {'enabled': self.settings.enabled}
        
        # 合并配置
        merged_config = {**default_config, **strategy_config}
        
        # 添加通用过滤配置
        if self.settings.allowed_event_types:
            merged_config['allowed_event_types'] = self.settings.allowed_event_types
        if self.settings.excluded_event_names:
            merged_config['excluded_event_names'] = self.settings.excluded_event_names
        
        return merged_config
    
    def get_default_strategy_config(self) -> Dict[str, Any]:
        """
        获取默认策略配置
        
        Returns:
            Dict[str, Any]: 默认策略配置
        """
        default_strategy = self._config_cache.get('default_strategy', self.settings.default_strategy)
        
        if default_strategy == 'composite':
            # 组合策略配置
            return {
                'type': 'composite',
                'strategies': self._config_cache.get('composite_strategies', [
                    {'name': 'database_log', 'config': self.get_strategy_config('database_log')},
                    {'name': 'file_log', 'config': self.get_strategy_config('file_log')}
                ])
            }
        else:
            # 单一策略配置
            return {
                'type': default_strategy,
                'config': self.get_strategy_config(default_strategy)
            }
    
    def is_enabled(self) -> bool:
        """
        检查事件记录是否启用
        
        Returns:
            bool: 是否启用
        """
        return self._config_cache.get('enabled', self.settings.enabled)
    
    def is_async_logging_enabled(self) -> bool:
        """
        检查是否启用异步记录
        
        Returns:
            bool: 是否启用异步记录
        """
        return self._config_cache.get('async_logging', self.settings.async_logging)
    
    def get_queue_config(self) -> Dict[str, Any]:
        """
        获取队列配置
        
        Returns:
            Dict[str, Any]: 队列配置
        """
        return {
            'max_size': self._config_cache.get('max_queue_size', self.settings.max_queue_size),
            'flush_interval': self._config_cache.get('flush_interval', self.settings.flush_interval),
        }
    
    def update_config(self, config: Dict[str, Any]) -> None:
        """
        更新配置
        
        Args:
            config: 新的配置
        """
        self._config_cache.update(config)
        logger.info("事件记录配置已更新")
    
    def save_config(self) -> None:
        """保存配置到文件"""
        try:
            # 确保目录存在
            config_dir = os.path.dirname(self.config_file)
            if config_dir:
                os.makedirs(config_dir, exist_ok=True)
            
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self._config_cache, f, indent=2, ensure_ascii=False)
            
            logger.info(f"配置已保存到文件: {self.config_file}")
        except Exception as e:
            logger.error(f"保存配置文件失败: {str(e)}")
    
    def reload_config(self) -> None:
        """重新加载配置"""
        self._config_cache.clear()
        self.settings = EventLogSettings()
        self._load_config()
        logger.info("事件记录配置已重新加载")
    
    def get_all_config(self) -> Dict[str, Any]:
        """
        获取所有配置
        
        Returns:
            Dict[str, Any]: 所有配置
        """
        return {
            'settings': self.settings.model_dump(),
            'file_config': self._config_cache,
            'merged_config': {
                'enabled': self.is_enabled(),
                'async_logging': self.is_async_logging_enabled(),
                'default_strategy': self.get_default_strategy_config(),
                'queue_config': self.get_queue_config(),
            }
        }
    
    def validate_config(self) -> List[str]:
        """
        验证配置
        
        Returns:
            List[str]: 验证错误列表
        """
        errors = []
        
        # 检查默认策略
        default_strategy = self._config_cache.get('default_strategy', self.settings.default_strategy)
        if default_strategy not in ['database_log', 'file_log', 'remote_log', 'composite']:
            errors.append(f"无效的默认策略: {default_strategy}")
        
        # 检查文件路径
        if self.settings.file_log_path:
            log_dir = os.path.dirname(self.settings.file_log_path)
            if log_dir and not os.access(log_dir, os.W_OK):
                try:
                    os.makedirs(log_dir, exist_ok=True)
                except Exception:
                    errors.append(f"无法创建日志目录: {log_dir}")
        
        # 检查远程配置
        if default_strategy == 'remote_log' or 'remote_log' in str(self._config_cache):
            if not self.settings.remote_endpoint:
                errors.append("远程记录策略缺少endpoint配置")
        
        return errors


# 全局配置管理器实例
_config_manager: Optional[EventLogConfigManager] = None


def get_config_manager() -> EventLogConfigManager:
    """
    获取全局配置管理器实例
    
    Returns:
        EventLogConfigManager: 配置管理器实例
    """
    global _config_manager
    if _config_manager is None:
        _config_manager = EventLogConfigManager()
    return _config_manager


def init_config_manager(config_file: Optional[str] = None) -> EventLogConfigManager:
    """
    初始化配置管理器
    
    Args:
        config_file: 配置文件路径
        
    Returns:
        EventLogConfigManager: 配置管理器实例
    """
    global _config_manager
    _config_manager = EventLogConfigManager(config_file)
    return _config_manager

