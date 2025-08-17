"""
数据库连接和会话管理
"""
import logging
from contextlib import contextmanager
from typing import Generator

from sqlalchemy import create_engine, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.exc import SQLAlchemyError

from config import get_database_url, get_database_config

# 配置日志
logger = logging.getLogger(__name__)

# 创建基础模型类
Base = declarative_base()

# 全局引擎和会话工厂
engine = None
SessionLocal = None


def init_database():
    """初始化数据库连接"""
    global engine, SessionLocal
    
    try:
        # 创建数据库引擎
        database_url = get_database_url()
        database_config = get_database_config()
        
        logger.info(f"正在连接数据库: {database_url.split('@')[1]}")  # 隐藏密码
        
        engine = create_engine(database_url, **database_config)
        
        # 测试连接
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
            logger.info("数据库连接测试成功")
        
        # 创建会话工厂
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        
        logger.info("数据库初始化完成")
        
    except SQLAlchemyError as e:
        logger.error(f"数据库连接失败: {str(e)}")
        raise RuntimeError(f"数据库连接失败: {str(e)}")
    except Exception as e:
        logger.error(f"数据库初始化失败: {str(e)}")
        raise RuntimeError(f"数据库初始化失败: {str(e)}")


def create_tables():
    """创建数据库表"""
    try:
        logger.info("正在创建数据库表...")
        Base.metadata.create_all(bind=engine)
        logger.info("数据库表创建完成")
    except SQLAlchemyError as e:
        logger.error(f"创建数据库表失败: {str(e)}")
        raise RuntimeError(f"创建数据库表失败: {str(e)}")


@contextmanager
def get_db_session() -> Generator[Session, None, None]:
    """获取数据库会话上下文管理器"""
    global SessionLocal

    if SessionLocal is None:
        logger.warning("数据库未初始化，尝试自动初始化...")
        try:
            init_database()
            logger.info("数据库自动初始化成功")
        except Exception as e:
            logger.error(f"数据库自动初始化失败: {str(e)}")
            raise RuntimeError(f"数据库未初始化且自动初始化失败: {str(e)}")

    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception as e:
        session.rollback()
        logger.error(f"数据库操作失败: {str(e)}")
        raise
    finally:
        session.close()


def get_db() -> Generator[Session, None, None]:
    """FastAPI依赖注入用的数据库会话获取器"""
    with get_db_session() as session:
        yield session


def close_database():
    """关闭数据库连接"""
    global engine
    if engine:
        engine.dispose()
        logger.info("数据库连接已关闭")


# 数据库健康检查
def check_database_health() -> bool:
    """检查数据库连接健康状态"""
    try:
        with get_db_session() as session:
            session.execute(text("SELECT 1"))
            return True
    except Exception as e:
        logger.error(f"数据库健康检查失败: {str(e)}")
        return False
