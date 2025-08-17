"""
按钮URL生成策略具体实现
包含多种不同的URL生成策略
"""
import ast
import json
import re
import logging
from urllib.parse import urlencode, quote
from typing import Dict, Any
from jinja2 import TemplateError, Environment, select_autoescape
from button_strategy import ButtonUrlStrategy
from card_models import MobileCardHistory

logger = logging.getLogger(__name__)


class SimpleReplaceStrategy(ButtonUrlStrategy):
    """简单字符串替换策略"""
    
    def generate_url(self, template_url: str, card_data: MobileCardHistory, config: Dict[str, Any]) -> str:
        """使用简单的字符串替换生成URL"""
        url = template_url
        
        # 替换卡片数据字段
        replacements = {
            '{card_id}': str(card_data.card_id),
            '{product_name}': card_data.product_name,
            '{yys}': card_data.yys,
            '{source}': card_data.source,
            '{monthly_rent}': card_data.monthly_rent,
            '{general_flow}': card_data.general_flow,
            '{call_times}': card_data.call_times,
            '{age_range}': card_data.age_range,
        }
        
        # 添加配置中的自定义替换项
        if 'custom_params' in config:
            replacements.update(config['custom_params'])
        
        for placeholder, value in replacements.items():
            if value is not None:
                url = url.replace(placeholder, quote(str(value)))
        
        return url


class QueryParamStrategy(ButtonUrlStrategy):
    """查询参数策略"""
    
    def generate_url(self, template_url: str, card_data: MobileCardHistory, config: Dict[str, Any]) -> str:
        """将数据作为查询参数附加到URL"""
        base_url = template_url
        
        # 构建查询参数
        params = {
            'card_id': card_data.card_id,
            'product_name': card_data.product_name,
            'yys': card_data.yys,
            'source': card_data.source,
            'monthly_rent': card_data.monthly_rent,
            'general_flow': card_data.general_flow,
            'call_times': card_data.call_times,
            'age_range': card_data.age_range,
        }
        
        # 添加配置中的额外参数
        if 'extra_params' in config:
            params.update(config['extra_params'])
        
        # 过滤空值
        params = {k: v for k, v in params.items() if v is not None}
        
        # 构建最终URL
        if '?' in base_url:
            return f"{base_url}&{urlencode(params)}"
        else:
            return f"{base_url}?{urlencode(params)}"



class TemplateStrategy(ButtonUrlStrategy):
    """模板引擎策略（支持更复杂的模板语法）"""
    
    def generate_url(self, template_url: str, card_data: MobileCardHistory, config: Dict[str, Any]) -> str:
        """使用模板引擎生成URL"""
        # 构建模板变量上下文
        context = {
            'card': {
                'id': card_data.card_id,
                'product_name': card_data.product_name,
                'yys': card_data.yys,
                'source': card_data.source,
                'monthly_rent': card_data.monthly_rent,
                'general_flow': card_data.general_flow,
                'call_times': card_data.call_times,
                'age_range': card_data.age_range,
                'rebate_money': float(card_data.rebate_money) if card_data.rebate_money else 0,
            },
            'config': config.get('template_vars', {})
        }
        
        # 简单的模板替换（可以后续集成Jinja2等模板引擎）
        url = template_url
        
        # 支持 {{card.field}} 语法
        pattern = r'\{\{(\w+)\.(\w+)\}\}'
        matches = re.findall(pattern, url)
        
        for obj_name, field_name in matches:
            if obj_name in context and field_name in context[obj_name]:
                placeholder = f"{{{{{obj_name}.{field_name}}}}}"
                value = str(context[obj_name][field_name])
                url = url.replace(placeholder, quote(value))
        
        return url




class Jinja2TemplateStrategy(ButtonUrlStrategy):
    """基于Jinja2的高级模板策略

    支持Jinja2的所有语法特性：
    - 变量替换：{{ card.product_name }}
    - 条件判断：{% if card.monthly_rent > 50 %}高价套餐{% endif %}
    - 循环：{% for item in items %}{{ item }}{% endfor %}
    - 过滤器：{{ card.product_name | upper }}
    - 宏定义和继承等高级特性
    """

    def __init__(self):
        """初始化Jinja2环境"""
        # 创建Jinja2环境，启用自动转义以防止XSS攻击
        self.env = Environment(
            autoescape=select_autoescape(['html', 'xml'])
        )

        # 注册自定义过滤器
        self._register_custom_filters()

    def _register_custom_filters(self):
        """注册自定义过滤器"""

        def url_quote_filter(value):
            """URL编码过滤器"""
            return quote(str(value)) if value is not None else ''

        def format_price_filter(value):
            """价格格式化过滤器"""
            try:
                price = float(value) if value else 0
                return f"¥{price:.2f}"
            except (ValueError, TypeError):
                return "¥0.00"

        def format_flow_filter(value):
            """流量格式化过滤器"""
            if not value:
                return "0MB"

            # 如果已经包含单位，直接返回
            if any(unit in str(value).upper() for unit in ['MB', 'GB', 'TB']):
                return str(value)

            try:
                flow_mb = float(value)
                if flow_mb >= 1024:
                    return f"{flow_mb/1024:.1f}GB"
                else:
                    return f"{flow_mb:.0f}MB"
            except (ValueError, TypeError):
                return str(value)

        def safe_int_filter(value, default=0):
            """安全整数转换过滤器"""
            try:
                return int(value) if value is not None else default
            except (ValueError, TypeError):
                return default

        # 注册过滤器
        self.env.filters['url_quote'] = url_quote_filter
        self.env.filters['format_price'] = format_price_filter
        self.env.filters['format_flow'] = format_flow_filter
        self.env.filters['safe_int'] = safe_int_filter

    def generate_url(self, template_url: str, card_data: MobileCardHistory, config: Dict[str, Any]) -> str:
        """使用Jinja2模板引擎生成URL

        Args:
            template_url: Jinja2模板字符串
            card_data: 手机卡历史数据
            config: 配置参数

        Returns:
            str: 渲染后的URL

        Raises:
            TemplateError: 模板语法错误或渲染失败
        """
        try:
            # 创建模板对象
            template = self.env.from_string(template_url)

            # 构建模板上下文
            context = self._build_template_context(card_data, config)

            # 渲染模板
            rendered_url = template.render(**context)

            logger.debug(f"Jinja2模板渲染成功: {template_url} -> {rendered_url}")
            return rendered_url.strip()

        except TemplateError as e:
            logger.error(f"Jinja2模板渲染失败: {str(e)}, 模板: {template_url}")
            raise ValueError(f"模板渲染失败: {str(e)}")
        except Exception as e:
            logger.error(f"Jinja2策略执行异常: {str(e)}")
            raise

    def _build_template_context(self, card_data: MobileCardHistory, config: Dict[str, Any]) -> Dict[str, Any]:
        """构建模板上下文变量

        Args:
            card_data: 手机卡数据
            config: 配置参数

        Returns:
            Dict[str, Any]: 模板上下文
        """

        print("1111",type(card_data.params),card_data.params)

        # 构建完整上下文
        context = {
            'card_data': card_data,
            'card_data_params': ast.literal_eval(card_data.params) if card_data.params else {}
        }

        return context
