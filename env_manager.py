"""
环境配置管理模块
支持通过启动参数控制加载不同环境的.env文件
"""
import os
import argparse
import logging
from pathlib import Path
from typing import Optional, List
from dotenv import load_dotenv

logger = logging.getLogger(__name__)


class EnvironmentManager:
    """环境配置管理器"""
    
    # 支持的环境类型
    SUPPORTED_ENVIRONMENTS = ['dev', 'test', 'prod', 'local']
    
    # 默认环境文件名
    DEFAULT_ENV_FILE = '.env'
    
    def __init__(self, project_root: Optional[str] = None):
        """
        初始化环境管理器
        
        Args:
            project_root: 项目根目录路径，默认为当前工作目录
        """
        self.project_root = Path(project_root or os.getcwd())
        self.current_env = None
        self.loaded_files = []
        
    def parse_arguments(self) -> argparse.Namespace:
        """
        解析命令行参数
        
        Returns:
            argparse.Namespace: 解析后的参数
        """
        parser = argparse.ArgumentParser(
            description='N8N Back API - 支持多环境配置的REST API服务',
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog="""
环境配置示例:
  python main.py                    # 使用默认环境(.env)
  python main.py --env dev          # 使用开发环境(.env.dev)
  python main.py --env prod         # 使用生产环境(.env.prod)
  python main.py --env-file custom.env  # 使用自定义环境文件
  
支持的环境类型: dev, test, prod, local
            """
        )
        
        # 环境参数组（互斥）
        env_group = parser.add_mutually_exclusive_group()
        env_group.add_argument(
            '--env', 
            choices=self.SUPPORTED_ENVIRONMENTS,
            help='指定环境类型 (dev/test/prod/local)'
        )
        env_group.add_argument(
            '--env-file',
            type=str,
            help='指定自定义环境配置文件路径'
        )
        
        # 其他启动参数
        parser.add_argument(
            '--host',
            default='0.0.0.0',
            help='服务器监听地址 (默认: 0.0.0.0)'
        )
        parser.add_argument(
            '--port',
            type=int,
            default=8100,
            help='服务器监听端口 (默认: 8100)'
        )
        parser.add_argument(
            '--reload',
            action='store_true',
            help='启用热重载模式 (开发环境推荐)'
        )
        parser.add_argument(
            '--log-level',
            choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
            help='日志级别 (会覆盖环境配置中的LOG_LEVEL)'
        )
        
        return parser.parse_args()
    
    def get_env_file_path(self, env_name: Optional[str] = None, custom_file: Optional[str] = None) -> List[str]:
        """
        获取环境配置文件路径列表（按优先级排序）
        
        Args:
            env_name: 环境名称
            custom_file: 自定义环境文件路径
            
        Returns:
            List[str]: 环境文件路径列表，按优先级从高到低排序
        """
        env_files = []
        
        # 1. 自定义环境文件（最高优先级）
        if custom_file:
            if os.path.isabs(custom_file):
                env_files.append(custom_file)
            else:
                env_files.append(str(self.project_root / custom_file))
        
        # 2. .env.local（本地开发配置，不提交到版本控制）
        local_env = self.project_root / '.env.local'
        if local_env.exists():
            env_files.append(str(local_env))
        
        # 3. 指定环境的配置文件
        if env_name:
            env_file = self.project_root / f'.env.{env_name}'
            if env_file.exists():
                env_files.append(str(env_file))
            else:
                logger.warning(f"指定的环境配置文件不存在: {env_file}")
        
        # 4. 默认环境配置文件（最低优先级）
        default_env = self.project_root / self.DEFAULT_ENV_FILE
        if default_env.exists():
            env_files.append(str(default_env))
        
        return env_files
    
    def load_environment(self, env_name: Optional[str] = None, custom_file: Optional[str] = None) -> bool:
        """
        加载环境配置
        
        Args:
            env_name: 环境名称
            custom_file: 自定义环境文件路径
            
        Returns:
            bool: 是否成功加载至少一个配置文件
        """
        env_files = self.get_env_file_path(env_name, custom_file)
        
        if not env_files:
            logger.error("未找到任何环境配置文件")
            return False
        
        # 按优先级加载配置文件（后加载的会覆盖先加载的）
        loaded_count = 0
        for env_file in reversed(env_files):  # 反向加载，确保优先级高的覆盖优先级低的
            if os.path.exists(env_file):
                try:
                    load_dotenv(env_file, override=True)
                    self.loaded_files.append(env_file)
                    loaded_count += 1
                    logger.info(f"成功加载环境配置: {env_file}")
                except Exception as e:
                    logger.error(f"加载环境配置失败 {env_file}: {str(e)}")
        
        if loaded_count > 0:
            self.current_env = env_name or 'default'
            logger.info(f"环境配置加载完成，当前环境: {self.current_env}")
            logger.info(f"已加载配置文件: {', '.join(self.loaded_files)}")
            return True
        else:
            logger.error("所有环境配置文件加载失败")
            return False
    
    def get_current_environment(self) -> str:
        """
        获取当前环境名称
        
        Returns:
            str: 当前环境名称
        """
        return self.current_env or 'unknown'
    
    def get_loaded_files(self) -> List[str]:
        """
        获取已加载的配置文件列表
        
        Returns:
            List[str]: 已加载的配置文件路径列表
        """
        return self.loaded_files.copy()


# 全局环境管理器实例
env_manager = EnvironmentManager()


def initialize_environment() -> argparse.Namespace:
    """
    初始化环境配置
    
    Returns:
        argparse.Namespace: 解析后的命令行参数
    """
    # 解析命令行参数
    args = env_manager.parse_arguments()
    
    # 加载环境配置
    success = env_manager.load_environment(
        env_name=args.env,
        custom_file=args.env_file
    )
    
    if not success:
        logger.error("环境配置加载失败，程序退出")
        exit(1)
    
    # 如果命令行指定了日志级别，则覆盖环境配置
    if args.log_level:
        os.environ['LOG_LEVEL'] = args.log_level
        logger.info(f"日志级别已通过命令行参数设置为: {args.log_level}")
    
    return args
