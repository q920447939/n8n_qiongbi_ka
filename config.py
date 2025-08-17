"""
配置管理模块
使用pydantic管理应用配置
"""
import os
from typing import Optional
from urllib.parse import quote_plus
from pydantic import BaseModel, Field
# dotenv 导入已移至 env_manager.py

# 环境配置由env_manager统一管理，不在此处直接加载
# load_dotenv() 调用已移至 env_manager.py


class DatabaseSettings(BaseModel):
    """数据库配置"""
    host: str = Field(default="localhost", description="MySQL主机地址")
    port: int = Field(default=3306, description="MySQL端口")
    username: str = Field(default="root", description="MySQL用户名")
    password: str = Field(default="", description="MySQL密码")
    database: str = Field(default="n8n_mobile_cards", description="数据库名称")

    # 连接池配置
    pool_size: int = Field(default=10, description="连接池大小")
    max_overflow: int = Field(default=20, description="连接池最大溢出")
    pool_timeout: int = Field(default=30, description="连接池超时时间(秒)")
    pool_recycle: int = Field(default=3600, description="连接回收时间(秒)")

    def __init__(self, **kwargs):
        # 从环境变量读取配置，支持类型转换和错误处理
        env_data = {
            'host': os.getenv('DB_HOST', 'localhost'),
            'port': self._safe_int_convert(os.getenv('DB_PORT', '3306'), 3306),
            'username': os.getenv('DB_USERNAME', 'root'),
            'password': os.getenv('DB_PASSWORD', ''),
            'database': os.getenv('DB_DATABASE', 'n8n_mobile_cards'),
            'pool_size': self._safe_int_convert(os.getenv('DB_POOL_SIZE', '10'), 10),
            'max_overflow': self._safe_int_convert(os.getenv('DB_MAX_OVERFLOW', '20'), 20),
            'pool_timeout': self._safe_int_convert(os.getenv('DB_POOL_TIMEOUT', '30'), 30),
            'pool_recycle': self._safe_int_convert(os.getenv('DB_POOL_RECYCLE', '3600'), 3600),
        }
        env_data.update(kwargs)
        super().__init__(**env_data)

    @staticmethod
    def _safe_int_convert(value: str, default: int) -> int:
        """安全的整数转换，避免类型错误"""
        try:
            return int(value) if value else default
        except (ValueError, TypeError):
            return default


class APISettings(BaseModel):
    """API配置"""
    token_key: str = Field(description="API认证Token")

    def __init__(self, **kwargs):
        env_data = {
            'token_key': os.getenv('API_TOKEN_KEY', ''),
        }
        env_data.update(kwargs)
        super().__init__(**env_data)


class OrderButtonConfig(BaseModel):
    """立即办理按钮配置"""
    text: str = Field(description="按钮文字")
    url: str = Field(description="跳转URL")


class AppSettings(BaseModel):
    """应用配置"""
    debug: bool = Field(default=False, description="调试模式")
    log_level: str = Field(default="INFO", description="日志级别")

    def __init__(self, **kwargs):
        env_data = {
            'debug': self._safe_bool_convert(os.getenv('DEBUG', 'false')),
            'log_level': os.getenv('LOG_LEVEL', 'INFO'),
        }
        env_data.update(kwargs)
        super().__init__(**env_data)

    @staticmethod
    def _safe_bool_convert(value: str) -> bool:
        """安全的布尔值转换"""
        if not value:
            return False
        return value.lower() in ('true', '1', 'yes', 'on')


class OrderButtonSettings(BaseModel):
    """立即办理按钮配置管理"""

    def get_order_buttons(self) -> list[OrderButtonConfig]:
        """获取配置的按钮列表"""
        buttons = []

        # 最多支持3个按钮
        for i in range(1, 4):
            text = os.getenv(f'ORDER_BUTTON_{i}_TEXT', '').strip()
            url = os.getenv(f'ORDER_BUTTON_{i}_URL', '').strip()

            # 只有当文字和URL都不为空时才添加按钮
            if text and url:
                buttons.append(OrderButtonConfig(text=text, url=url))

        return buttons


# 全局配置实例（延迟初始化）
db_settings = None
api_settings = None
app_settings = None
order_button_settings = None


def initialize_settings():
    """初始化全局配置实例"""
    global db_settings, api_settings, app_settings, order_button_settings

    db_settings = DatabaseSettings()
    api_settings = APISettings()
    app_settings = AppSettings()
    order_button_settings = OrderButtonSettings()


def get_db_settings() -> DatabaseSettings:
    """获取数据库配置实例"""
    global db_settings
    if db_settings is None:
        initialize_settings()
    return db_settings


def get_api_settings() -> APISettings:
    """获取API配置实例"""
    global api_settings
    if api_settings is None:
        initialize_settings()
    return api_settings


def get_app_settings() -> AppSettings:
    """获取应用配置实例"""
    global app_settings
    if app_settings is None:
        initialize_settings()
    return app_settings


def get_order_button_settings() -> OrderButtonSettings:
    """获取按钮配置实例"""
    global order_button_settings
    if order_button_settings is None:
        initialize_settings()
    return order_button_settings


def get_database_url() -> str:
    """获取数据库连接URL"""
    db_config = get_db_settings()
    # 对用户名和密码进行URL编码，处理特殊字符
    encoded_username = quote_plus(db_config.username)
    encoded_password = quote_plus(db_config.password)

    return (
        f"mysql+pymysql://{encoded_username}:{encoded_password}"
        f"@{db_config.host}:{db_config.port}/{db_config.database}"
        f"?charset=utf8mb4"
    )


def get_database_config() -> dict:
    """获取数据库连接配置"""
    db_config = get_db_settings()
    app_config = get_app_settings()

    return {
        "pool_size": db_config.pool_size,
        "max_overflow": db_config.max_overflow,
        "pool_timeout": db_config.pool_timeout,
        "pool_recycle": db_config.pool_recycle,
        "pool_pre_ping": True,  # 连接前检查
        "echo": app_config.debug,  # 调试模式下打印SQL
    }

