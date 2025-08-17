"""
事件记录策略接口定义
使用策略模式实现不同事件记录方式的解耦
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
import logging
from event_models import UserEventLogCreate, EventLogConfig

logger = logging.getLogger(__name__)


class EventLogStrategy(ABC):
    """事件记录策略抽象基类"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        初始化策略
        
        Args:
            config: 策略配置参数
        """
        self.config = config or {}
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
    
    @abstractmethod
    async def log_event(self, event_data: UserEventLogCreate) -> bool:
        """
        记录单个事件
        
        Args:
            event_data: 事件数据
            
        Returns:
            bool: 记录是否成功
        """
        pass
    
    @abstractmethod
    async def log_events_batch(self, events: List[UserEventLogCreate]) -> int:
        """
        批量记录事件
        
        Args:
            events: 事件数据列表
            
        Returns:
            int: 成功记录的事件数量
        """
        pass
    
    @abstractmethod
    def get_strategy_name(self) -> str:
        """获取策略名称"""
        pass
    
    def validate_config(self, config: Dict[str, Any]) -> bool:
        """
        验证配置是否有效
        
        Args:
            config: 配置字典
            
        Returns:
            bool: 配置是否有效
        """
        return True  # 默认实现，子类可以重写
    
    def is_enabled(self) -> bool:
        """
        检查策略是否启用
        
        Returns:
            bool: 策略是否启用
        """
        return self.config.get('enabled', True)
    
    async def health_check(self) -> bool:
        """
        健康检查
        
        Returns:
            bool: 策略是否健康
        """
        return True  # 默认实现，子类可以重写
    
    def get_config(self, key: str, default: Any = None) -> Any:
        """
        获取配置值
        
        Args:
            key: 配置键
            default: 默认值
            
        Returns:
            Any: 配置值
        """
        return self.config.get(key, default)
    
    def format_event_data(self, event_data: UserEventLogCreate) -> Dict[str, Any]:
        """
        格式化事件数据
        
        Args:
            event_data: 原始事件数据
            
        Returns:
            Dict: 格式化后的事件数据
        """
        # 转换为字典格式
        data = event_data.model_dump(exclude_none=True)
        
        # 添加策略特定的格式化逻辑
        if hasattr(self, '_format_custom_data'):
            data = self._format_custom_data(data)
        
        return data
    
    def should_log_event(self, event_data: UserEventLogCreate) -> bool:
        """
        判断是否应该记录该事件
        
        Args:
            event_data: 事件数据
            
        Returns:
            bool: 是否应该记录
        """
        # 检查策略是否启用
        if not self.is_enabled():
            return False
        
        # 检查事件类型过滤
        allowed_types = self.config.get('allowed_event_types')
        if allowed_types and event_data.event_type not in allowed_types:
            return False
        
        # 检查事件名称过滤
        excluded_names = self.config.get('excluded_event_names', [])
        if event_data.event_name in excluded_names:
            return False
        
        return True
    
    async def handle_error(self, error: Exception, event_data: UserEventLogCreate) -> None:
        """
        处理记录错误
        
        Args:
            error: 异常对象
            event_data: 事件数据
        """
        self.logger.error(
            f"事件记录失败 - 策略: {self.get_strategy_name()}, "
            f"事件: {event_data.event_name}, 错误: {str(error)}"
        )
        
        # 可以在这里实现错误恢复逻辑，如重试、降级等
        if self.config.get('enable_fallback', False):
            await self._fallback_log(event_data, error)
    
    async def _fallback_log(self, event_data: UserEventLogCreate, error: Exception) -> None:
        """
        降级记录方法
        
        Args:
            event_data: 事件数据
            error: 原始错误
        """
        # 默认降级到日志记录
        self.logger.warning(
            f"降级记录事件: {event_data.event_name}, "
            f"原始错误: {str(error)}"
        )


class CompositeEventLogStrategy(EventLogStrategy):
    """组合事件记录策略 - 支持同时使用多种策略"""
    
    def __init__(self, strategies: List[EventLogStrategy], config: Optional[Dict[str, Any]] = None):
        """
        初始化组合策略
        
        Args:
            strategies: 策略列表
            config: 配置参数
        """
        super().__init__(config)
        self.strategies = strategies
    
    async def log_event(self, event_data: UserEventLogCreate) -> bool:
        """记录单个事件到所有策略"""
        success_count = 0
        
        for strategy in self.strategies:
            try:
                if await strategy.log_event(event_data):
                    success_count += 1
            except Exception as e:
                await strategy.handle_error(e, event_data)
        
        # 如果至少有一个策略成功，则认为成功
        return success_count > 0
    
    async def log_events_batch(self, events: List[UserEventLogCreate]) -> int:
        """批量记录事件到所有策略"""
        total_success = 0
        
        for strategy in self.strategies:
            try:
                success_count = await strategy.log_events_batch(events)
                total_success = max(total_success, success_count)
            except Exception as e:
                self.logger.error(f"批量记录失败 - 策略: {strategy.get_strategy_name()}, 错误: {str(e)}")
        
        return total_success
    
    def get_strategy_name(self) -> str:
        """获取组合策略名称"""
        strategy_names = [s.get_strategy_name() for s in self.strategies]
        return f"composite({','.join(strategy_names)})"
    
    async def health_check(self) -> bool:
        """检查所有策略的健康状态"""
        for strategy in self.strategies:
            if not await strategy.health_check():
                return False
        return True
