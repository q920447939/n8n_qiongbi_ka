"""
按钮URL生成策略接口定义
使用策略模式实现不同运营商的URL生成逻辑解耦
"""
from abc import ABC, abstractmethod
from typing import Dict, Any
from card_models import MobileCardHistory


class ButtonUrlStrategy(ABC):
    """按钮URL生成策略接口"""
    
    @abstractmethod
    def generate_url(self, template_url: str, card_data: MobileCardHistory, config: Dict[str, Any]) -> str:
        """
        生成最终的跳转URL
        
        Args:
            template_url: 模板URL
            card_data: 手机卡历史数据
            config: 运营商特定配置
            
        Returns:
            str: 格式化后的最终URL
        """
        pass
