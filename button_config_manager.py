"""
按钮配置管理器
负责加载和管理JSON格式的按钮配置
"""
import json
import os
import logging
from typing import Dict, List, Any, Optional
from pathlib import Path

logger = logging.getLogger(__name__)


class ButtonConfigManager:
    """按钮配置管理器"""
    
    def __init__(self, config_file: str = "config/button_config.json"):
        self.config_file = Path(config_file)
        self._config_cache: Optional[Dict[str, Any]] = None
        self._load_config()
    
    def _load_config(self):
        """加载配置文件"""
        try:
            if self.config_file.exists():
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    self._config_cache = json.load(f)
                    logger.info(f"成功加载按钮配置文件: {self.config_file}")
            else:
                logger.warning(f"配置文件不存在: {self.config_file}，创建默认配置")
        except json.JSONDecodeError as e:
            logger.error(f"配置文件JSON格式错误: {str(e)}")
        except Exception as e:
            logger.error(f"加载按钮配置失败: {str(e)}")


    def get_operator_buttons(self, operator: str) -> List[Dict[str, Any]]:
        """
        获取指定运营商的按钮配置
        
        Args:
            operator: 运营商名称
            
        Returns:
            List[Dict]: 按钮配置列表
        """
        
        operators = self._config_cache.get("operators", {})
        
        buttons = operators[operator].get("buttons", [])
        logger.debug(f"找到运营商 {operator} 的 {len(buttons)} 个按钮配置")
        return buttons

