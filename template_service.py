"""
HTML模板渲染服务
"""
import logging
from datetime import datetime
import os
from typing import List
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape

from card_models import MobileCardResponse
from itertools import groupby
from operator import itemgetter

logger = logging.getLogger(__name__)


class TemplateService:
    """HTML模板渲染服务"""
    
    def __init__(self):
        # 设置模板目录
        template_dir = Path(__file__).parent / "templates"
        
        # 创建Jinja2环境
        self.env = Environment(
            loader=FileSystemLoader(template_dir),
            autoescape=select_autoescape(['html', 'xml'])
        )
        
        logger.info(f"模板服务初始化完成，模板目录: {template_dir}")
    
    def render_card_list(self, cards,total_visits,daily_orders: List[MobileCardResponse]) -> str:
        """
        渲染手机卡列表HTML
        
        Args:
            cards: 手机卡数据列表
            
        Returns:
            str: 渲染后的HTML内容
        """
        try:
            # 获取模板
            template = self.env.get_template('index.html')
            
            # 分组
            

            # 准备模板数据
            template_data = {
                'all_data': sorted(cards, key=lambda item: item.point, reverse=True),
                'yidong_data': sorted(list(filter(lambda x:str(x.yys)  == str('移动') or str(x.yys)  == str('中国移动') ,cards)), key=lambda item: item.point, reverse=True),
                'union_data': sorted(list(filter(lambda x:str(x.yys)  == str('联通') or str(x.yys)  == str('中国联通') ,cards)), key=lambda item: item.point, reverse=True),
                'telecom_data': sorted(list(filter(lambda x:str(x.yys)  == str('电信') or str(x.yys)  == str('中国电信') ,cards)), key=lambda item: item.point, reverse=True),
                'broadcast_data': sorted(list(filter(lambda x:str(x.yys)  == str('广电') or str(x.yys)  == str('中国广电') ,cards)), key=lambda item: item.point, reverse=True),
                'update_time': cards[0].data_time.strftime('%Y年%m月%d日') if cards else datetime.now().strftime('%Y年%m月%d日'),
                'total_count': len(cards),
                "domain": os.getenv('domain', 'localhost'),
                "total_visits": total_visits,
                "daily_orders": daily_orders
            }
            # 渲染HTML
            html_content = template.render(**template_data)
            
            logger.info(f"成功渲染手机卡列表HTML，包含 {len(cards)} 张卡片")
            return html_content
            
        except Exception as e:
            logger.error(f"渲染HTML模板失败: {str(e)}")
            raise RuntimeError(f"渲染HTML模板失败: {str(e)}")
    
    def get_operator_logo_path(self, operator: str) -> str:
        """
        根据运营商名称获取logo路径
        
        Args:
            operator: 运营商名称
            
        Returns:
            str: logo文件路径
        """
        operator_mapping = {
            '中国移动': 'china-mobile.svg',
            '中国联通': 'china-unicom.svg', 
            '中国电信': 'china-telecom.svg',
            '广电': 'china-broadcast.svg'
        }
        
        return operator_mapping.get(operator, 'default-operator.svg')
    
    def get_operator_css_class(self, operator: str) -> str:
        """
        根据运营商名称获取CSS类名
        
        Args:
            operator: 运营商名称
            
        Returns:
            str: CSS类名
        """
        operator_mapping = {
            '中国移动': 'mobile',
            '中国联通': 'unicom',
            '中国电信': 'telecom',
            '广电': 'broadcast'
        }
        
        return operator_mapping.get(operator, 'default')


# 全局模板服务实例
template_service = TemplateService()
