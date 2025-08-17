"""
N8N Back API - HTML内容解析REST API服务
提供HTML内容解析功能的HTTP REST API
"""
import logging
from typing import List, Optional
from datetime import date, datetime
from fastapi import FastAPI, Depends, HTTPException, status, Form, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, HTMLResponse

from models import (
    ApiResponse,
    ResponseCode
)

# 导入新的手机卡相关模块
from database import init_database, create_tables, check_database_health
from card_models import MobileCardListRequest, MobileCardListResponse
from template_service import template_service
from config import get_api_settings, initialize_settings

# 导入事件记录相关模块
from event_log_decorator import user_event_log
from event_models import EventType

# 导入缓存相关模块
from cache_decorators import api_cache
from cache_manager import cache_manager

# card_service 将在数据库初始化后导入
mobile_card_service = None

# 按钮服务将在数据库初始化后导入
button_service = None

def get_mobile_card_service():
    """获取手机卡服务实例，如果未初始化则自动初始化"""
    global mobile_card_service

    if mobile_card_service is None:
        try:
            logger.info("手机卡服务未初始化，正在自动初始化...")

            # 确保数据库已初始化
            from database import SessionLocal
            if SessionLocal is None:
                logger.info("数据库未初始化，正在初始化数据库...")
                init_database()
                create_tables()

            # 导入并初始化服务
            from card_service import mobile_card_service as _service
            mobile_card_service = _service
            logger.info("手机卡服务自动初始化完成")

        except Exception as e:
            logger.error(f"手机卡服务初始化失败: {str(e)}")
            raise RuntimeError(f"手机卡服务初始化失败: {str(e)}")

    return mobile_card_service


def get_button_service():
    """获取按钮服务实例，如果未初始化则自动初始化"""
    global button_service

    if button_service is None:
         # 导入并初始化按钮服务
            from button_service import ButtonService
            button_service = ButtonService()

    return button_service

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 创建FastAPI应用
app = FastAPI(
    title="N8N Back API",
    description="HTML内容解析和手机卡数据管理REST API服务",
    version="2.0.0",
)

# 添加CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生产环境中应该限制具体域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)



# 手机卡数据管理API接口
def mobile_card_auth_dependency(request: Request):
    """手机卡API专用认证依赖"""
    api_token = request.headers.get("API-TOKEN-KEY")
    if not api_token or api_token != get_api_settings().token_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=ApiResponse(
                code=ResponseCode.UNAUTHORIZED,
                data=None,
                message="API认证失败，请检查API-TOKEN-KEY"
            ).model_dump()
        )
    return True


@app.post("/card-api/save/mobile-cards", response_model=MobileCardListResponse)
async def save_mobile_cards(
    cards_data: List[dict],
    _: bool = Depends(mobile_card_auth_dependency)
):
    """
    保存手机卡数据接口

    Args:
        cards_data: 手机卡数据列表（JSON数组）
        _: 认证依赖

    Returns:
        MobileCardListResponse: 保存结果响应
    """
    try:
        logger.info(f"接收到 {len(cards_data)} 条手机卡数据")

        # 验证数据格式并转换为Pydantic模型
        validated_cards = []
        for i, card_data in enumerate(cards_data):
            try:
                # 处理字段映射
                if 'id' in card_data:
                    card_data['card_id'] = card_data.pop('id')
                if 'productName' in card_data:
                    card_data['product_name'] = card_data.pop('productName')

                validated_card = {
                    'source': card_data.get('source', ''),
                    'id': card_data.get('card_id', ''),
                    'productName': card_data.get('product_name', ''),
                    'yys': card_data.get('yys', ''),
                    'monthly_rent': card_data.get('monthly_rent', ''),
                    'general_flow': card_data.get('general_flow', ''),
                    'call_times': card_data.get('call_times', ''),
                    'age_range': card_data.get('age_range', ''),
                    'ka_origin': card_data.get('ka_origin'),
                    'disable_area': card_data.get('disable_area'),
                    'rebate_money': card_data.get('rebate_money'),
                    'top_detail': card_data.get('top_detail'),
                    'data_time': card_data.get('data_time'),
                    'point': card_data.get('point'),
                    'params': card_data.get('params')
                }
                validated_cards.append(validated_card)
            except Exception as e:
                logger.error(f"数据验证失败，第 {i+1} 条记录: {str(e)}")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=ApiResponse(
                        code=ResponseCode.BAD_REQUEST,
                        data=None,
                        message=f"数据格式错误，第 {i+1} 条记录: {str(e)}"
                    ).model_dump()
                ) 

        # 转换为MobileCardData对象
        from card_models import MobileCardData
        mobile_cards = [MobileCardData(**card) for card in validated_cards]

        # 保存数据 
        card_service = get_mobile_card_service()
        saved_count = card_service.save_mobile_cards(mobile_cards)

        logger.info(f"成功保存 {saved_count} 条手机卡数据")

        return MobileCardListResponse(
            code=ResponseCode.SUCCESS,
            data=[],
            message=f"成功保存 {saved_count} 条手机卡数据",
            total=saved_count
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"保存手机卡数据失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=ApiResponse(
                code=ResponseCode.INTERNAL_ERROR,
                data=None,
                message=f"保存数据失败: {str(e)}"
            ).model_dump()
        )


@app.get("/card", response_class=HTMLResponse)
async def view_mobile_cards():
    try:
        # 查询最新数据
        cards = get_mobile_card_service().get_latest_cards()
        logger.info(f"查询最新数据，共 {len(cards)} 条")

        # 渲染HTML
        html_content = template_service.render_card_list(cards,0,0)

        return HTMLResponse(content=html_content, status_code=200)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"查询手机卡数据失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=ApiResponse(
                code=ResponseCode.INTERNAL_ERROR,
                data=None,
                message=f"查询数据失败"
            ).model_dump()
        )


@app.get("/card/api/order-buttons")
@api_cache("order_buttons", key_func=lambda card_id=None: f"order_buttons_{card_id}")
async def get_order_buttons(card_id: Optional[int] = Query(None, description="卡片ID")):
    """
    获取立即办理按钮配置接口

    Args:
        card_id: 卡片ID（可选，如果提供则返回该卡片对应的按钮）

    Returns:
        ApiResponse: 按钮配置列表
    """
    try:
        logger.info(f"根据卡片ID {card_id} 获取按钮配置")
        service = get_button_service()
        buttons = service.get_buttons_by_card_id(card_id)
        return ApiResponse(
            code=ResponseCode.SUCCESS,
            data=buttons,
            message="获取按钮配置成功"
        )

    except Exception as e:
        logger.error(f"获取按钮配置失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=ApiResponse(
                code=ResponseCode.INTERNAL_ERROR,
                data=None,
                message=f"获取按钮配置失败"
            ).model_dump()
        )


@app.get("/health")
async def health_check():
    """
    健康检查端点
    用于Docker容器健康检查和负载均衡器检查
    """
    try:
        # 检查数据库连接
        health_status = check_database_health()
        
        if health_status:
            return {
                "status": "healthy",
                "timestamp": datetime.now().isoformat(),
                "database": "connected",
                "service": "n8n_qiongbi_ka"
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail={
                    "status": "unhealthy",
                    "timestamp": datetime.now().isoformat(),
                    "database": "disconnected",
                    "service": "n8n_qiongbi_ka"
                }
            )
    except Exception as e:
        logger.error(f"健康检查失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "status": "unhealthy",
                "timestamp": datetime.now().isoformat(),
                "error": str(e),
                "service": "n8n_qiongbi_ka"
            }
        )


def main():
    """主函数 - 启动服务器"""
    import uvicorn
    from env_manager import initialize_environment, env_manager

    # 初始化环境配置
    logger.info("正在初始化环境配置...")
    args = initialize_environment()

    # 显示环境信息
    logger.info(f"当前环境: {env_manager.get_current_environment()}")
    logger.info(f"已加载配置文件: {', '.join(env_manager.get_loaded_files())}")

    # 初始化配置实例（在环境配置加载后）
    logger.info("正在初始化配置实例...")
    initialize_settings()
    logger.info("配置实例初始化完成")

    # 初始化数据库
    try:
        logger.info("正在初始化数据库...")

        # 确保事件记录模型被导入，以便创建表
        from event_models import UserEventLog
        init_database()
        create_tables()
        logger.info("数据库初始化完成")

        # 初始化按钮服务
        from button_service import ButtonService
        global button_service
        button_service = ButtonService()
        logger.info("按钮服务初始化完成")


    except Exception as e:
        logger.error(f"数据库初始化失败: {str(e)}")
        logger.error("应用启动失败，请检查数据库配置")
        exit(1)

    # 根据命令行参数启动服务器
    logger.info(f"启动N8N Back API服务... (环境: {env_manager.get_current_environment()})")
    uvicorn.run(
        "main:app",
        host=args.host,
        port=args.port,
        reload=args.reload,
        log_level=args.log_level.lower() if args.log_level else "info"
    )


if __name__ == "__main__":
    main()

