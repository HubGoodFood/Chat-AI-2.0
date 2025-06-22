# -*- coding: utf-8 -*-
"""
数据库配置和连接管理
"""
import os
import logging
from typing import Optional
from contextlib import contextmanager
from sqlalchemy import create_engine, pool
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.engine import Engine
from sqlalchemy.pool import StaticPool
from .models import Base

logger = logging.getLogger(__name__)


class DatabaseConfig:
    """数据库配置管理"""
    
    def __init__(self):
        self.database_url = self._get_database_url()
        self.engine: Optional[Engine] = None
        self.SessionLocal: Optional[sessionmaker] = None
        self._setup_engine()
    
    def _get_database_url(self) -> str:
        """获取数据库连接URL"""
        # 优先使用环境变量
        db_url = os.environ.get('DATABASE_URL')
        if db_url:
            return db_url
        
        # 开发环境默认使用SQLite
        if os.environ.get('FLASK_ENV') == 'production':
            # 生产环境建议使用PostgreSQL
            pg_host = os.environ.get('POSTGRES_HOST', 'localhost')
            pg_port = os.environ.get('POSTGRES_PORT', '5432')
            pg_db = os.environ.get('POSTGRES_DB', 'chat_ai')
            pg_user = os.environ.get('POSTGRES_USER', 'postgres')
            pg_password = os.environ.get('POSTGRES_PASSWORD', '')
            
            if pg_password:
                return f"postgresql://{pg_user}:{pg_password}@{pg_host}:{pg_port}/{pg_db}"
            else:
                logger.warning("生产环境未配置PostgreSQL，使用SQLite")
        
        # 默认SQLite
        db_path = os.path.join(os.getcwd(), 'data', 'chat_ai.db')
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        return f"sqlite:///{db_path}"
    
    def _setup_engine(self):
        """设置数据库引擎"""
        try:
            if self.database_url.startswith('sqlite'):
                # SQLite配置
                self.engine = create_engine(
                    self.database_url,
                    poolclass=StaticPool,
                    connect_args={
                        "check_same_thread": False,
                        "timeout": 20
                    },
                    echo=os.environ.get('SQL_DEBUG', 'false').lower() == 'true'
                )
            else:
                # PostgreSQL配置
                self.engine = create_engine(
                    self.database_url,
                    poolclass=pool.QueuePool,
                    pool_size=10,
                    max_overflow=20,
                    pool_pre_ping=True,
                    pool_recycle=3600,
                    echo=os.environ.get('SQL_DEBUG', 'false').lower() == 'true'
                )
            
            # 创建会话工厂
            self.SessionLocal = sessionmaker(
                autocommit=False,
                autoflush=False,
                bind=self.engine
            )
            
            logger.info(f"数据库引擎初始化成功: {self.database_url}")
            
        except Exception as e:
            logger.error(f"数据库引擎初始化失败: {e}")
            raise
    
    def create_tables(self):
        """创建数据库表"""
        try:
            Base.metadata.create_all(bind=self.engine)
            logger.info("数据库表创建成功")
        except Exception as e:
            logger.error(f"数据库表创建失败: {e}")
            raise
    
    def drop_tables(self):
        """删除所有表（慎用）"""
        try:
            Base.metadata.drop_all(bind=self.engine)
            logger.warning("所有数据库表已删除")
        except Exception as e:
            logger.error(f"数据库表删除失败: {e}")
            raise
    
    @contextmanager
    def get_session(self):
        """获取数据库会话（上下文管理器）"""
        if not self.SessionLocal:
            raise RuntimeError("数据库未初始化")
        
        session = self.SessionLocal()
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            logger.error(f"数据库操作失败: {e}")
            raise
        finally:
            session.close()
    
    def get_session_factory(self) -> sessionmaker:
        """获取会话工厂"""
        if not self.SessionLocal:
            raise RuntimeError("数据库未初始化")
        return self.SessionLocal
    
    def health_check(self) -> bool:
        """数据库健康检查"""
        try:
            with self.get_session() as session:
                session.execute("SELECT 1")
            return True
        except Exception as e:
            logger.error(f"数据库健康检查失败: {e}")
            return False
    
    def get_connection_info(self) -> dict:
        """获取连接信息"""
        return {
            'database_url': self.database_url.replace(
                self.database_url.split('@')[0].split('//')[-1], 
                '***'
            ) if '@' in self.database_url else self.database_url,
            'engine_info': str(self.engine.url) if self.engine else None,
            'pool_size': getattr(self.engine.pool, 'size', None) if self.engine else None,
            'checked_out': getattr(self.engine.pool, 'checkedout', None) if self.engine else None
        }


# 全局数据库实例
db_config = DatabaseConfig()


def get_db_session() -> Session:
    """获取数据库会话（依赖注入使用）"""
    session = db_config.SessionLocal()
    try:
        return session
    except Exception:
        session.close()
        raise


def init_database():
    """初始化数据库"""
    try:
        db_config.create_tables()
        logger.info("数据库初始化完成")
        return True
    except Exception as e:
        logger.error(f"数据库初始化失败: {e}")
        return False


def close_database():
    """关闭数据库连接"""
    try:
        if db_config.engine:
            db_config.engine.dispose()
            logger.info("数据库连接已关闭")
    except Exception as e:
        logger.error(f"关闭数据库连接失败: {e}")