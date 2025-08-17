"""
按钮策略工厂
负责创建和管理不同的URL生成策略
"""
import logging
from typing import Dict, Type, List
from button_strategy import ButtonUrlStrategy
from button_strategies import SimpleReplaceStrategy, QueryParamStrategy, TemplateStrategy, Jinja2TemplateStrategy

logger = logging.getLogger(__name__)


class ButtonStrategyFactory:
    """按钮策略工厂"""
    
    _strategies: Dict[str, Type[ButtonUrlStrategy]] = {
        'simple_replace': SimpleReplaceStrategy,
        'query_param': QueryParamStrategy,
        'template': TemplateStrategy,
        'jinja2_template': Jinja2TemplateStrategy,
    }
    
    @classmethod
    def create_strategy(cls, strategy_name: str) -> ButtonUrlStrategy:
        """
        创建策略实例
        
        Args:
            strategy_name: 策略名称
            
        Returns:
            ButtonUrlStrategy: 策略实例
            
        Raises:
            ValueError: 当策略不存在时
        """
        if strategy_name not in cls._strategies:
            available = ', '.join(cls._strategies.keys())
            logger.error(f"未知的策略: {strategy_name}. 可用策略: {available}")
            raise ValueError(f"未知的策略: {strategy_name}. 可用策略: {available}")
        
        try:
            strategy_instance = cls._strategies[strategy_name]()
            logger.debug(f"成功创建策略实例: {strategy_name}")
            return strategy_instance
        except Exception as e:
            logger.error(f"创建策略实例失败: {strategy_name}, 错误: {str(e)}")
            raise
    
    @classmethod
    def register_strategy(cls, strategy_name: str, strategy_class: Type[ButtonUrlStrategy]):
        """
        注册新策略
        
        Args:
            strategy_name: 策略名称
            strategy_class: 策略类
        """
        if not issubclass(strategy_class, ButtonUrlStrategy):
            raise ValueError(f"策略类必须继承自 ButtonUrlStrategy")
        
        cls._strategies[strategy_name] = strategy_class
        logger.info(f"成功注册新策略: {strategy_name}")
    
    @classmethod
    def get_available_strategies(cls) -> List[str]:
        """获取所有可用策略名称"""
        return list(cls._strategies.keys())
    
    @classmethod
    def validate_strategy_exists(cls, strategy_name: str) -> bool:
        """
        验证策略是否存在
        
        Args:
            strategy_name: 策略名称
            
        Returns:
            bool: 策略是否存在
        """
        return strategy_name in cls._strategies
    
    @classmethod
    def get_strategy_info(cls) -> Dict[str, str]:
        """
        获取所有策略的信息
        
        Returns:
            Dict[str, str]: 策略名称到描述的映射
        """
        info = {}
        for name, strategy_class in cls._strategies.items():
            try:
                instance = strategy_class()
                info[name] = instance.__class__.__doc__ or "无描述"
            except Exception as e:
                info[name] = f"获取信息失败: {str(e)}"
        
        return info
