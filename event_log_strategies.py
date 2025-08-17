"""
具体的事件记录策略实现
包括数据库记录、文件记录、远程记录等策略
"""
import json
import asyncio
import aiofiles
from datetime import datetime
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
import logging

from event_log_strategy import EventLogStrategy
from event_models import UserEventLogCreate, UserEventLog
from database import get_db_session

logger = logging.getLogger(__name__)


class DatabaseLogStrategy(EventLogStrategy):
    """数据库事件记录策略"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        self.table_name = self.get_config('table_name', 'user_event_logs')
        self.batch_size = self.get_config('batch_size', 100)
    
    async def log_event(self, event_data: UserEventLogCreate) -> bool:
        """记录单个事件到数据库"""
        if not self.should_log_event(event_data):
            return False
        
        try:
            # 使用异步方式执行数据库操作
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(None, self._sync_log_event, event_data)
        except Exception as e:
            await self.handle_error(e, event_data)
            return False
    
    def _sync_log_event(self, event_data: UserEventLogCreate) -> bool:
        """同步方式记录单个事件"""
        try:
            with get_db_session() as session:
                # 创建数据库记录
                db_event = UserEventLog(**event_data.model_dump(exclude_none=True))
                session.add(db_event)
                session.commit()
                
                self.logger.debug(f"成功记录事件到数据库: {event_data.event_name}")
                return True
        except SQLAlchemyError as e:
            self.logger.error(f"数据库记录事件失败: {str(e)}")
            return False
    
    async def log_events_batch(self, events: List[UserEventLogCreate]) -> int:
        """批量记录事件到数据库"""
        if not events:
            return 0
        
        # 过滤需要记录的事件
        filtered_events = [event for event in events if self.should_log_event(event)]
        if not filtered_events:
            return 0
        
        try:
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(None, self._sync_log_events_batch, filtered_events)
        except Exception as e:
            self.logger.error(f"批量记录事件失败: {str(e)}")
            return 0
    
    def _sync_log_events_batch(self, events: List[UserEventLogCreate]) -> int:
        """同步方式批量记录事件"""
        success_count = 0
        
        try:
            with get_db_session() as session:
                # 分批处理
                for i in range(0, len(events), self.batch_size):
                    batch = events[i:i + self.batch_size]
                    
                    # 创建数据库记录
                    db_events = [
                        UserEventLog(**event.model_dump(exclude_none=True))
                        for event in batch
                    ]
                    
                    session.add_all(db_events)
                    session.commit()
                    success_count += len(batch)
                    
                    self.logger.debug(f"批量记录 {len(batch)} 个事件到数据库")
        
        except SQLAlchemyError as e:
            self.logger.error(f"批量数据库记录失败: {str(e)}")
        
        return success_count
    
    def get_strategy_name(self) -> str:
        return "database_log"
    
    def validate_config(self, config: Dict[str, Any]) -> bool:
        """验证数据库策略配置"""
        # 检查必要的配置项
        return True
    
    async def health_check(self) -> bool:
        """检查数据库连接健康状态"""
        try:
            with get_db_session() as session:
                session.execute("SELECT 1")
                return True
        except Exception:
            return False


class FileLogStrategy(EventLogStrategy):
    """文件事件记录策略"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        self.log_file = self.get_config('log_file', 'events.log')
        self.log_format = self.get_config('log_format', 'json')  # json 或 text
        self.max_file_size = self.get_config('max_file_size', 100 * 1024 * 1024)  # 100MB
        self.backup_count = self.get_config('backup_count', 5)
    
    async def log_event(self, event_data: UserEventLogCreate) -> bool:
        """记录单个事件到文件"""
        if not self.should_log_event(event_data):
            return False
        
        try:
            log_entry = self._format_log_entry(event_data)
            
            async with aiofiles.open(self.log_file, 'a', encoding='utf-8') as f:
                await f.write(log_entry + '\n')
            
            self.logger.debug(f"成功记录事件到文件: {event_data.event_name}")
            return True
        except Exception as e:
            await self.handle_error(e, event_data)
            return False
    
    async def log_events_batch(self, events: List[UserEventLogCreate]) -> int:
        """批量记录事件到文件"""
        if not events:
            return 0
        
        # 过滤需要记录的事件
        filtered_events = [event for event in events if self.should_log_event(event)]
        if not filtered_events:
            return 0
        
        try:
            log_entries = [self._format_log_entry(event) for event in filtered_events]
            
            async with aiofiles.open(self.log_file, 'a', encoding='utf-8') as f:
                await f.write('\n'.join(log_entries) + '\n')
            
            self.logger.debug(f"批量记录 {len(filtered_events)} 个事件到文件")
            return len(filtered_events)
        except Exception as e:
            self.logger.error(f"批量文件记录失败: {str(e)}")
            return 0
    
    def _format_log_entry(self, event_data: UserEventLogCreate) -> str:
        """格式化日志条目"""
        if self.log_format == 'json':
            # JSON格式
            data = self.format_event_data(event_data)
            data['timestamp'] = datetime.now().isoformat()
            return json.dumps(data, ensure_ascii=False)
        else:
            # 文本格式
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            return (
                f"[{timestamp}] {event_data.event_type} - {event_data.event_name} "
                f"- Status: {event_data.event_status} - IP: {event_data.request_ip or 'N/A'}"
            )
    
    def get_strategy_name(self) -> str:
        return "file_log"
    
    def validate_config(self, config: Dict[str, Any]) -> bool:
        """验证文件策略配置"""
        log_file = config.get('log_file')
        if not log_file:
            return False
        
        # 检查文件路径是否可写
        try:
            import os
            log_dir = os.path.dirname(log_file)
            if log_dir and not os.path.exists(log_dir):
                os.makedirs(log_dir, exist_ok=True)
            return True
        except Exception:
            return False


class RemoteLogStrategy(EventLogStrategy):
    """远程事件记录策略"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        self.endpoint_url = self.get_config('endpoint_url')
        self.api_key = self.get_config('api_key')
        self.timeout = self.get_config('timeout', 30)
        self.retry_count = self.get_config('retry_count', 3)
    
    async def log_event(self, event_data: UserEventLogCreate) -> bool:
        """记录单个事件到远程服务"""
        if not self.should_log_event(event_data):
            return False
        
        if not self.endpoint_url:
            self.logger.error("远程记录策略缺少endpoint_url配置")
            return False
        
        try:
            import aiohttp
            
            data = self.format_event_data(event_data)
            headers = {'Content-Type': 'application/json'}
            
            if self.api_key:
                headers['Authorization'] = f'Bearer {self.api_key}'
            
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=self.timeout)) as session:
                for attempt in range(self.retry_count):
                    try:
                        async with session.post(self.endpoint_url, json=data, headers=headers) as response:
                            if response.status == 200:
                                self.logger.debug(f"成功记录事件到远程服务: {event_data.event_name}")
                                return True
                            else:
                                self.logger.warning(f"远程记录返回状态码: {response.status}")
                    except Exception as e:
                        if attempt == self.retry_count - 1:
                            raise e
                        await asyncio.sleep(2 ** attempt)  # 指数退避
            
            return False
        except Exception as e:
            await self.handle_error(e, event_data)
            return False
    
    async def log_events_batch(self, events: List[UserEventLogCreate]) -> int:
        """批量记录事件到远程服务"""
        if not events:
            return 0
        
        # 过滤需要记录的事件
        filtered_events = [event for event in events if self.should_log_event(event)]
        if not filtered_events:
            return 0
        
        if not self.endpoint_url:
            self.logger.error("远程记录策略缺少endpoint_url配置")
            return 0
        
        try:
            import aiohttp
            
            data = {
                'events': [self.format_event_data(event) for event in filtered_events],
                'batch_id': f"batch_{datetime.now().timestamp()}"
            }
            
            headers = {'Content-Type': 'application/json'}
            if self.api_key:
                headers['Authorization'] = f'Bearer {self.api_key}'
            
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=self.timeout)) as session:
                async with session.post(f"{self.endpoint_url}/batch", json=data, headers=headers) as response:
                    if response.status == 200:
                        self.logger.debug(f"批量记录 {len(filtered_events)} 个事件到远程服务")
                        return len(filtered_events)
                    else:
                        self.logger.warning(f"远程批量记录返回状态码: {response.status}")
                        return 0
        except Exception as e:
            self.logger.error(f"批量远程记录失败: {str(e)}")
            return 0
    
    def get_strategy_name(self) -> str:
        return "remote_log"
    
    def validate_config(self, config: Dict[str, Any]) -> bool:
        """验证远程策略配置"""
        return bool(config.get('endpoint_url'))
    
    async def health_check(self) -> bool:
        """检查远程服务健康状态"""
        if not self.endpoint_url:
            return False
        
        try:
            import aiohttp
            
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=5)) as session:
                async with session.get(f"{self.endpoint_url}/health") as response:
                    return response.status == 200
        except Exception:
            return False
