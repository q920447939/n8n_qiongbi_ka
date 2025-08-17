"""
手机卡数据模型定义
"""
from datetime import datetime
from typing import List, Optional
from decimal import Decimal

from sqlalchemy import Column, Integer, String, Text, DECIMAL, DateTime, Index
from pydantic import BaseModel, Field

from database import Base


class MobileCardLatest(Base):
    """手机卡最新数据表"""
    __tablename__ = "mobile_cards_latest"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    source = Column(String(50), nullable=False, comment="数据源")
    card_id = Column(String(50), nullable=False, comment="卡片ID")
    product_name = Column(String(255), nullable=False, comment="产品名称")
    yys = Column(String(50), nullable=False, comment="运营商")
    monthly_rent = Column(String(50), nullable=False, comment="月租费用")
    general_flow = Column(String(50), nullable=False, comment="通用流量")
    call_times = Column(String(50), nullable=False, comment="通话时长")
    age_range = Column(String(50), nullable=False, comment="年龄范围")
    ka_origin = Column(String(255), nullable=True, comment="卡片归属")
    disable_area = Column(Text, nullable=True, comment="禁发区域")
    rebate_money = Column(DECIMAL(10, 2), nullable=True, comment="返佣金额")
    top_detail = Column(Text, nullable=True, comment="详细描述")
    point = Column(Integer, nullable=False, comment="分数")
    params = Column(Text, nullable=True, comment="额外参数")
    data_time = Column(DateTime, nullable=True, default=datetime.now, comment="数据时间")
    created_at = Column(DateTime, nullable=False, default=datetime.now, comment="创建时间")
        

    # 创建唯一索引
    __table_args__ = (
        Index('idx_source_card_id', 'source', 'card_id', unique=True),
        {'comment': '手机卡最新数据表'}
    )


class MobileCardHistory(Base):
    """手机卡历史数据表"""
    __tablename__ = "mobile_cards_history"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    source = Column(String(50), nullable=False, comment="数据源")
    latest_id = Column(Integer, nullable=False, comment="最新表ID")
    card_id = Column(String(50), nullable=False, comment="卡片ID")
    product_name = Column(String(255), nullable=False, comment="产品名称")
    yys = Column(String(50), nullable=False, comment="运营商")
    monthly_rent = Column(String(50), nullable=False, comment="月租费用")
    general_flow = Column(String(50), nullable=False, comment="通用流量")
    call_times = Column(String(50), nullable=False, comment="通话时长")
    age_range = Column(String(50), nullable=False, comment="年龄范围")
    ka_origin = Column(String(255), nullable=True, comment="卡片归属")
    disable_area = Column(Text, nullable=True, comment="禁发区域")
    rebate_money = Column(DECIMAL(10, 2), nullable=True, comment="返佣金额")
    top_detail = Column(Text, nullable=True, comment="详细描述")
    point = Column(Integer, nullable=False, comment="分数")
    params = Column(Text, nullable=True, comment="额外参数")
    created_at = Column(DateTime, nullable=False, comment="创建时间")
    data_time = Column(DateTime, nullable=False, comment="数据时间")
    
    # 创建日期索引
    __table_args__ = (
        Index('idx_created_date', 'created_at'),
        {'comment': '手机卡历史数据表'}
    )


# Pydantic模型用于API请求和响应
class MobileCardData(BaseModel):
    """手机卡数据模型"""
    source: str = Field(..., description="数据源")
    id: str = Field(..., description="卡片ID", alias="id")
    productName: str = Field(..., description="产品名称")
    yys: str = Field(..., description="运营商")
    monthly_rent: str = Field(..., description="月租费用")
    general_flow: str = Field(..., description="通用流量")
    call_times: str = Field(..., description="通话时长")
    age_range: str = Field(..., description="年龄范围")
    ka_origin: Optional[str] = Field(None, description="卡片归属")
    disable_area: Optional[str] = Field(None, description="禁发区域")
    rebate_money: Optional[Decimal] = Field(None, description="返佣金额")
    top_detail: Optional[str] = Field(None, description="详细描述")
    data_time: Optional[datetime] = Field(None, description="数据时间")
    point: Optional[int] = Field(None, description="分数")
    params: Optional[dict] = Field(None, description="额外参数")
    
    model_config = {"populate_by_name": True}


class MobileCardListRequest(BaseModel):
    """手机卡数据列表请求模型"""
    data: List[MobileCardData] = Field(..., description="手机卡数据列表")


class MobileCardResponse(BaseModel):
    """手机卡数据响应模型"""
    id: int
    source: str
    card_id: str
    product_name: str
    yys: str
    monthly_rent: str
    general_flow: str
    call_times: str
    age_range: str
    ka_origin: Optional[str]
    disable_area: Optional[str]
    rebate_money: Optional[Decimal]
    top_detail: Optional[str]
    point: int
    created_at: datetime
    data_time: datetime
    
    model_config = {"from_attributes": True}


class MobileCardListResponse(BaseModel):
    """手机卡数据列表响应模型"""
    code: str = Field(..., description="响应编码")
    data: List[MobileCardResponse] = Field(default_factory=list, description="手机卡数据列表")
    message: str = Field(..., description="响应描述")
    total: int = Field(default=0, description="总数量")
