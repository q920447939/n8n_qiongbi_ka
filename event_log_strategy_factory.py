"""
事件记录策略工厂
负责创建和管理不同的事件记录策略实例
"""
import logging
from typing import Dict, Type, List, Optional, Any
from event_log_strategy import EventLogStrategy, CompositeEventLogStrategy
from event_log_strategies import DatabaseLogStrategy, FileLogStrategy, RemoteLogStrategy

logger = logging.getLogger(__name__)


class EventLogStrategyFactory:
    """事件记录策略工厂"""
    
    # 注册的策略类型
    _strategies: Dict[str, Type[EventLogStrategy]] = {
        'database_log': DatabaseLogStrategy,
        'file_log': FileLogStrategy,
        'remote_log': RemoteLogStrategy,
    }
    
    # 策略实例缓存
    _strategy_cache: Dict[str, EventLogStrategy] = {}
    
    @classmethod
    def register_strategy(cls, strategy_name: str, strategy_class: Type[EventLogStrategy]) -> None:
        """
        注册新的策略类型
        
        Args:
            strategy_name: 策略名称
            strategy_class: 策略类
        """
        if not issubclass(strategy_class, EventLogStrategy):
            raise ValueError(f"策略类必须继承自EventLogStrategy: {strategy_class}")
        
        cls._strategies[strategy_name] = strategy_class
        logger.info(f"注册事件记录策略: {strategy_name}")
    
    @classmethod
    def create_strategy(cls, strategy_name: str, config: Optional[Dict[str, Any]] = None) -> EventLogStrategy:
        """
        创建策略实例
        
        Args:
            strategy_name: 策略名称
            config: 策略配置
            
        Returns:
            EventLogStrategy: 策略实例
            
        Raises:
            ValueError: 当策略不存在时
        """
        if strategy_name not in cls._strategies:
            available = ', '.join(cls._strategies.keys())
            logger.error(f"未知的事件记录策略: {strategy_name}. 可用策略: {available}")
            raise ValueError(f"未知的事件记录策略: {strategy_name}. 可用策略: {available}")
        
        try:
            # 创建策略实例
            strategy_class = cls._strategies[strategy_name]
            strategy_instance = strategy_class(config)
            
            # 验证配置
            if config and not strategy_instance.validate_config(config):
                logger.warning(f"策略配置验证失败: {strategy_name}")
            
            logger.debug(f"成功创建事件记录策略实例: {strategy_name}")
            return strategy_instance
            
        except Exception as e:
            logger.error(f"创建事件记录策略实例失败: {strategy_name}, 错误: {str(e)}")
            raise
    
    @classmethod
    def create_cached_strategy(cls, strategy_name: str, config: Optional[Dict[str, Any]] = None) -> EventLogStrategy:
        """
        创建缓存的策略实例（单例模式）
        
        Args:
            strategy_name: 策略名称
            config: 策略配置
            
        Returns:
            EventLogStrategy: 策略实例
        """
        cache_key = f"{strategy_name}_{hash(str(config))}"
        
        if cache_key not in cls._strategy_cache:
            cls._strategy_cache[cache_key] = cls.create_strategy(strategy_name, config)
        
        return cls._strategy_cache[cache_key]
    
    @classmethod
    def create_composite_strategy(cls, strategy_configs: List[Dict[str, Any]]) -> CompositeEventLogStrategy:
        """
        创建组合策略实例
        
        Args:
            strategy_configs: 策略配置列表，每个配置包含 'name' 和 'config' 字段
            
        Returns:
            CompositeEventLogStrategy: 组合策略实例
            
        Example:
            strategy_configs = [
                {'name': 'database_log', 'config': {'table_name': 'events'}},
                {'name': 'file_log', 'config': {'log_file': 'events.log'}}
            ]
        """
        strategies = []
        
        for strategy_config in strategy_configs:
            strategy_name = strategy_config.get('name')
            config = strategy_config.get('config', {})
            
            if not strategy_name:
                logger.warning("策略配置缺少name字段，跳过")
                continue
            
            try:
                strategy = cls.create_strategy(strategy_name, config)
                strategies.append(strategy)
            except Exception as e:
                logger.error(f"创建组合策略中的子策略失败: {strategy_name}, 错误: {str(e)}")
                # 继续创建其他策略，不因为一个策略失败而整体失败
        
        if not strategies:
            raise ValueError("组合策略中没有有效的子策略")
        
        return CompositeEventLogStrategy(strategies)
    
    @classmethod
    def create_from_config(cls, config: Dict[str, Any]) -> EventLogStrategy:
        """
        从配置字典创建策略实例
        
        Args:
            config: 完整的策略配置
            
        Returns:
            EventLogStrategy: 策略实例
            
        Example:
            config = {
                'type': 'database_log',  # 单一策略
                'config': {'table_name': 'events'}
            }
            
            或者
            
            config = {
                'type': 'composite',  # 组合策略
                'strategies': [
                    {'name': 'database_log', 'config': {'table_name': 'events'}},
                    {'name': 'file_log', 'config': {'log_file': 'events.log'}}
                ]
            }
        """
        strategy_type = config.get('type')
        
        if not strategy_type:
            raise ValueError("配置中缺少type字段")
        
        if strategy_type == 'composite':
            # 组合策略
            strategy_configs = config.get('strategies', [])
            return cls.create_composite_strategy(strategy_configs)
        else:
            # 单一策略
            strategy_config = config.get('config', {})
            return cls.create_strategy(strategy_type, strategy_config)
    
    @classmethod
    def get_available_strategies(cls) -> List[str]:
        """
        获取所有可用的策略名称
        
        Returns:
            List[str]: 策略名称列表
        """
        return list(cls._strategies.keys())
    
    @classmethod
    def clear_cache(cls) -> None:
        """清空策略缓存"""
        cls._strategy_cache.clear()
        logger.info("事件记录策略缓存已清空")
    
    @classmethod
    async def health_check_all(cls) -> Dict[str, bool]:
        """
        检查所有缓存策略的健康状态
        
        Returns:
            Dict[str, bool]: 策略名称到健康状态的映射
        """
        health_status = {}
        
        for cache_key, strategy in cls._strategy_cache.items():
            try:
                is_healthy = await strategy.health_check()
                health_status[cache_key] = is_healthy
            except Exception as e:
                logger.error(f"策略健康检查失败: {cache_key}, 错误: {str(e)}")
                health_status[cache_key] = False
        
        return health_status
    
    @classmethod
    def get_strategy_info(cls, strategy_name: str) -> Dict[str, Any]:
        """
        获取策略信息
        
        Args:
            strategy_name: 策略名称
            
        Returns:
            Dict[str, Any]: 策略信息
        """
        if strategy_name not in cls._strategies:
            raise ValueError(f"未知的策略: {strategy_name}")
        
        strategy_class = cls._strategies[strategy_name]
        
        return {
            'name': strategy_name,
            'class': strategy_class.__name__,
            'module': strategy_class.__module__,
            'doc': strategy_class.__doc__ or "无描述",
        }
    
    @classmethod
    def list_all_strategies_info(cls) -> List[Dict[str, Any]]:
        """
        列出所有策略的信息
        
        Returns:
            List[Dict[str, Any]]: 策略信息列表
        """
        return [cls.get_strategy_info(name) for name in cls._strategies.keys()]


# 预定义的常用策略配置
PREDEFINED_CONFIGS = {
    'default_database': {
        'type': 'database_log',
        'config': {
            'table_name': 'user_event_logs',
            'batch_size': 100
        }
    },
    'default_file': {
        'type': 'file_log',
        'config': {
            'log_file': 'logs/events.log',
            'log_format': 'json',
            'max_file_size': 100 * 1024 * 1024  # 100MB
        }
    },
    'default_composite': {
        'type': 'composite',
        'strategies': [
            {'name': 'database_log', 'config': {'table_name': 'user_event_logs'}},
            {'name': 'file_log', 'config': {'log_file': 'logs/events.log', 'log_format': 'json'}}
        ]
    }
}


def get_predefined_strategy(config_name: str) -> EventLogStrategy:
    """
    获取预定义的策略实例
    
    Args:
        config_name: 预定义配置名称
        
    Returns:
        EventLogStrategy: 策略实例
    """
    if config_name not in PREDEFINED_CONFIGS:
        available = ', '.join(PREDEFINED_CONFIGS.keys())
        raise ValueError(f"未知的预定义配置: {config_name}. 可用配置: {available}")
    
    config = PREDEFINED_CONFIGS[config_name]
    return EventLogStrategyFactory.create_from_config(config)
