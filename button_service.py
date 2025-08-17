"""
按钮服务层
整合策略模式和配置管理，提供按钮相关的业务逻辑
"""
import logging
from typing import List, Dict, Any, Optional
from card_models import MobileCardHistory
from database import get_db_session
from button_config_manager import ButtonConfigManager
from button_strategy_factory import ButtonStrategyFactory

logger = logging.getLogger(__name__)


class ButtonService:
    """按钮服务"""
    
    def __init__(self):
        self.config_manager = ButtonConfigManager()
        logger.info("按钮服务初始化完成")
    
    def get_buttons_by_card_id(self, card_id: int) -> List[Dict[str, Any]]:
        """
        根据卡片ID获取按钮配置

        Args:
            card_id: 卡片ID

        Returns:
            List[Dict]: 按钮配置列表，格式: [{"text": "按钮文字", "url": "跳转URL"}]
        """
        try:
            # 在会话内完成所有操作
            with get_db_session() as session:
                # 1. 根据card_id查询历史表获取卡片数据
                card = session.query(MobileCardHistory).filter(
                    MobileCardHistory.latest_id == card_id
                ).first()


                logger.debug(f"找到卡片数据: ID={card.id}, source={card.source}, product_name={card.product_name}")

                # 2. 根据source字段获取运营商按钮配置
                operator = card.source
                logger.info(f"为卡片ID {card_id} (运营商: {operator}) 获取按钮配置")

                button_configs = self.config_manager.get_operator_buttons(operator)

                # 3. 使用策略模式生成最终按钮
                buttons = []
                for config in button_configs:
                    try:
                        button = self._generate_button(config, card)
                        buttons.append(button)
                        logger.debug(f"成功生成按钮: {button['text']}")
                    except Exception as e:
                        logger.error(f"生成按钮失败: {str(e)}, 配置: {config}")
                        continue


                logger.info(f"成功为卡片ID {card_id} 生成 {len(buttons)} 个按钮")
                return buttons

        except Exception as e:
            logger.error(f"获取按钮配置失败: {str(e)}")
    

    
    def _generate_button(self, config: Dict[str, Any], card_data: MobileCardHistory) -> Dict[str, Any]:
        """
        生成单个按钮
        
        Args:
            config: 按钮配置
            card_data: 卡片数据
            
        Returns:
            Dict: 按钮数据，格式: {"text": "按钮文字", "url": "跳转URL"}
        """
        strategy_name = config.get('strategy', 'simple_replace')
        
        # 创建策略实例
        strategy = ButtonStrategyFactory.create_strategy(strategy_name)
        
        # 生成最终URL
        final_url = strategy.generate_url(
            template_url=config['template_url'],
            card_data=card_data,
            config=config.get('config', {})
        )
        
        return {
            'text': config['text'],
            'url': final_url
        }
