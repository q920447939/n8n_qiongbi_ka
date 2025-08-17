"""
用户事件记录数据模型
定义事件记录的数据结构，包括数据库模型和Pydantic模型
"""
from datetime import datetime
from typing import Optional, Dict, Any
from sqlalchemy import Column, Integer, String, Text, DateTime, Float, JSON

from pydantic import BaseModel, Field, ConfigDict
from enum import Enum

# 导入现有的SQLAlchemy基类
from database import Base


class EventType(str, Enum):
    """事件类型枚举"""
    API_CALL = "api_call"           # API调用事件
    PAGE_VIEW = "page_view"         # 页面访问事件
    USER_ACTION = "user_action"     # 用户操作事件
    SYSTEM_EVENT = "system_event"   # 系统事件


class EventStatus(str, Enum):
    """事件状态枚举"""
    SUCCESS = "success"             # 成功
    FAILED = "failed"               # 失败
    ERROR = "error"                 # 错误


class UserEventLog(Base):
    """用户事件记录数据库模型"""
    __tablename__ = "user_event_logs"
    
    id = Column(Integer, primary_key=True, autoincrement=True, comment="主键ID")
    event_type = Column(String(50), nullable=False, index=True, comment="事件类型")
    event_name = Column(String(200), nullable=False, comment="事件名称")
    event_status = Column(String(20), nullable=False, default=EventStatus.SUCCESS, comment="事件状态")
    
    # 用户相关信息
    user_id = Column(String(100), nullable=True, index=True, comment="用户ID")
    session_id = Column(String(200), nullable=True, index=True, comment="会话ID")
    
    # 请求相关信息
    request_ip = Column(String(45), nullable=True, comment="请求IP地址")
    user_agent = Column(Text, nullable=True, comment="用户代理字符串")
    request_method = Column(String(10), nullable=True, comment="HTTP请求方法")
    request_path = Column(String(500), nullable=True, comment="请求路径")
    request_params = Column(JSON, nullable=True, comment="请求参数(JSON格式)")
    
    # 响应相关信息
    response_status = Column(Integer, nullable=True, comment="HTTP响应状态码")
    response_time = Column(Float, nullable=True, comment="响应时间(毫秒)")
    
    # 事件附加数据
    event_data = Column(JSON, nullable=True, comment="事件附加数据(JSON格式)")
    error_message = Column(Text, nullable=True, comment="错误信息")
    
    # 时间戳
    created_at = Column(DateTime, nullable=False, default=datetime.now, index=True, comment="创建时间")
    
    def __repr__(self):
        return f"<UserEventLog(id={self.id}, event_type={self.event_type}, event_name={self.event_name})>"


class UserEventLogCreate(BaseModel):
    """创建用户事件记录的Pydantic模型"""
    model_config = ConfigDict(use_enum_values=True)
    
    event_type: EventType = Field(..., description="事件类型")
    event_name: str = Field(..., max_length=200, description="事件名称")
    event_status: EventStatus = Field(default=EventStatus.SUCCESS, description="事件状态")
    
    # 用户相关信息
    user_id: Optional[str] = Field(None, max_length=100, description="用户ID")
    session_id: Optional[str] = Field(None, max_length=200, description="会话ID")
    
    # 请求相关信息
    request_ip: Optional[str] = Field(None, max_length=45, description="请求IP地址")
    user_agent: Optional[str] = Field(None, description="用户代理字符串")
    request_method: Optional[str] = Field(None, max_length=10, description="HTTP请求方法")
    request_path: Optional[str] = Field(None, max_length=500, description="请求路径")
    request_params: Optional[Dict[str, Any]] = Field(None, description="请求参数")
    
    # 响应相关信息
    response_status: Optional[int] = Field(None, description="HTTP响应状态码")
    response_time: Optional[float] = Field(None, description="响应时间(毫秒)")
    
    # 事件附加数据
    event_data: Optional[Dict[str, Any]] = Field(None, description="事件附加数据")
    error_message: Optional[str] = Field(None, description="错误信息")


class UserEventLogResponse(BaseModel):
    """用户事件记录响应模型"""
    model_config = ConfigDict(from_attributes=True, use_enum_values=True)
    
    id: int
    event_type: str
    event_name: str
    event_status: str
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    request_ip: Optional[str] = None
    user_agent: Optional[str] = None
    request_method: Optional[str] = None
    request_path: Optional[str] = None
    request_params: Optional[Dict[str, Any]] = None
    response_status: Optional[int] = None
    response_time: Optional[float] = None
    event_data: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    created_at: datetime


class EventLogConfig(BaseModel):
    """事件记录配置模型"""
    enabled: bool = Field(default=True, description="是否启用事件记录")
    include_request: bool = Field(default=True, description="是否包含请求信息")
    include_response: bool = Field(default=False, description="是否包含响应信息")
    include_user_agent: bool = Field(default=True, description="是否包含用户代理信息")
    include_request_params: bool = Field(default=False, description="是否包含请求参数")
    max_param_length: int = Field(default=1000, description="请求参数最大长度")
    custom_data: Optional[Dict[str, Any]] = Field(None, description="自定义数据")
    async_logging: bool = Field(default=True, description="是否异步记录")


class EventLogBatch(BaseModel):
    """批量事件记录模型"""
    events: list[UserEventLogCreate] = Field(..., description="事件列表")
    batch_id: Optional[str] = Field(None, description="批次ID")
