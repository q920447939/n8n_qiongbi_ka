
"""
手机卡数据业务逻辑服务
"""
import logging
from datetime import datetime, date
from typing import List, Optional

from sqlalchemy.orm import Session
from sqlalchemy import func, and_

from cache_decorators import api_cache
from database import get_db_session
from card_models import (
    MobileCardLatest, 
    MobileCardHistory, 
    MobileCardData,
    MobileCardResponse
)

logger = logging.getLogger(__name__)


class MobileCardService:
    """手机卡数据服务"""
    
    def save_mobile_cards(self, cards_data: List[MobileCardData]) -> int:
        """
        保存手机卡数据
        1. 将当前最新数据备份到历史表
        2. 清空最新表
        3. 插入新数据到最新表
        
        Args:
            cards_data: 手机卡数据列表
            
        Returns:
            int: 保存的记录数量
        """
        try:
            with get_db_session() as session:
                current_time = datetime.now()
                
                # 先删除历史数据（防止重复）
                data_time = cards_data[0].data_time
                session.query(MobileCardHistory).filter(
                    func.date(MobileCardHistory.data_time) == func.date(data_time)
                ).delete()
                
                # 2. 清空最新表
                session.query(MobileCardLatest).delete()
                logger.info("已清空最新数据表")
                
                # 3. 插入新数据到最新表
                new_cards = []
                for card_data in cards_data:
                    new_card = MobileCardLatest(
                        source=card_data.source,
                        card_id=card_data.id,
                        product_name=card_data.productName,
                        yys=card_data.yys,
                        monthly_rent=card_data.monthly_rent,
                        general_flow=card_data.general_flow,
                        call_times=card_data.call_times,
                        age_range=card_data.age_range,
                        ka_origin=card_data.ka_origin,
                        disable_area=card_data.disable_area,
                        rebate_money=card_data.rebate_money,
                        top_detail=card_data.top_detail,
                        point=card_data.point,
                        params= '{}' if card_data.params is None else str(card_data.params),
                        created_at=current_time,
                        data_time=card_data.data_time,
                    )
                    new_cards.append(new_card)
                
                session.add_all(new_cards)
                session.flush()  # 执行SQL但不提交事务，ID会立即回填
                
                # 同时将数据复制一份插入到历史表
                history_cards = [] 
                for card_data in new_cards:  # 注意：这里应该使用new_cards而不是cards_data
                    history_card = MobileCardHistory(
                        source=card_data.source,
                        card_id=card_data.card_id,
                        latest_id=card_data.id,
                        product_name=card_data.product_name,
                        yys=card_data.yys,
                        monthly_rent=card_data.monthly_rent,
                        general_flow=card_data.general_flow,
                        call_times=card_data.call_times,
                        age_range=card_data.age_range,
                        ka_origin=card_data.ka_origin,
                        disable_area=card_data.disable_area,
                        rebate_money=card_data.rebate_money,
                        top_detail=card_data.top_detail,
                        point=card_data.point,
                        params=card_data.params,
                        created_at=card_data.created_at,
                        data_time=card_data.data_time,
                    )
                    history_cards.append(history_card)
                
                session.add_all(history_cards)
                session.commit()  # 最终提交所有更改
                logger.info(f"已同时备份 {len(history_cards)} 条数据到历史表")
                
                logger.info(f"成功保存 {len(new_cards)} 条手机卡数据")
                return len(new_cards)
                
        except Exception as e:
            logger.error(f"保存手机卡数据失败: {str(e)}")
            raise
    
    @api_cache("card_list", key_func=lambda date_param=None: f"card_list_latest")
    def get_latest_cards(self) -> List[MobileCardResponse]:
        """获取最新的手机卡数据"""
        try:
            with get_db_session() as session:
                cards = session.query(MobileCardLatest).order_by(
                    MobileCardLatest.data_time.desc()
                ).all()
                
                result = [MobileCardResponse.model_validate(card) for card in cards]
                logger.info(f"查询到 {len(result)} 条最新手机卡数据")
                return result
                
        except Exception as e:
            logger.error(f"查询最新手机卡数据失败: {str(e)}")
            raise
    
    def get_history_cards(self, target_date: date) -> List[MobileCardResponse]:
        """获取指定日期的历史手机卡数据"""
        try:
            with get_db_session() as session:
                cards = session.query(MobileCardHistory).filter(
                    func.date(MobileCardHistory.created_at) == target_date
                ).order_by(MobileCardHistory.created_at.desc()).all()
                
                # 转换为响应模型
                result = []
                for card in cards:
                    response = MobileCardResponse(
                        id=card.id,
                        source=card.source,
                        card_id=card.card_id,
                        product_name=card.product_name,
                        yys=card.yys,
                        monthly_rent=card.monthly_rent,
                        general_flow=card.general_flow,
                        call_times=card.call_times,
                        age_range=card.age_range,
                        ka_origin=card.ka_origin,
                        disable_area=card.disable_area,
                        rebate_money=card.rebate_money,
                        top_detail=card.top_detail,
                        created_at=card.created_at
                    )
                    result.append(response)
                
                logger.info(f"查询到 {len(result)} 条 {target_date} 的历史手机卡数据")
                return result
                
        except Exception as e:
            logger.error(f"查询历史手机卡数据失败: {str(e)}")
            raise


# 全局服务实例
mobile_card_service = MobileCardService()



