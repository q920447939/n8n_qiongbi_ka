"""
数据模型定义
定义API请求、响应和业务数据的Pydantic模型
"""
from typing import List, Optional, Any
from pydantic import BaseModel, Field


class HtmlContentRequest(BaseModel):
    """HTML内容解析请求模型"""
    html_content: str = Field(..., description="待解析的HTML内容")


class ApiResponse(BaseModel):
    """统一API响应格式"""
    code: str = Field(..., description="响应编码")
    data: Any = Field(None, description="具体响应数据")
    message: str = Field(..., description="响应描述")


class ProductListResponse(ApiResponse):
    """产品列表响应模型"""
    data: List[dict] = Field(default_factory=list, description="产品信息列表（扁平化结构）")


# 响应编码常量
class ResponseCode:
    """响应编码常量"""
    SUCCESS = "200"
    BAD_REQUEST = "400"
    UNAUTHORIZED = "401"
    INTERNAL_ERROR = "500"


# 响应消息常量
class ResponseMessage:
    """响应消息常量"""
    SUCCESS = "操作成功"
    INVALID_REQUEST = "请求参数无效"
    UNAUTHORIZED = "认证失败"
    HTML_PARSE_ERROR = "HTML解析失败"
    INTERNAL_ERROR = "服务器内部错误"
