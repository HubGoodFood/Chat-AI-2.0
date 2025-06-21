# -*- coding: utf-8 -*-
"""
AI客服系统 - 统一日志配置模块
提供专业的日志管理功能，替换系统中的print语句
"""

import logging
import logging.handlers
import os
import sys
from datetime import datetime
from typing import Optional


class LoggerConfig:
    """日志配置管理器"""
    
    def __init__(self):
        self.log_dir = "logs"
        self.log_level = self._get_log_level()
        self.loggers = {}
        self._ensure_log_directory()
        self._setup_root_logger()
    
    def _get_log_level(self) -> int:
        """根据环境变量获取日志级别"""
        level_str = os.environ.get('LOG_LEVEL', 'INFO').upper()
        level_map = {
            'DEBUG': logging.DEBUG,
            'INFO': logging.INFO,
            'WARNING': logging.WARNING,
            'ERROR': logging.ERROR,
            'CRITICAL': logging.CRITICAL
        }
        return level_map.get(level_str, logging.INFO)
    
    def _ensure_log_directory(self):
        """确保日志目录存在"""
        try:
            os.makedirs(self.log_dir, exist_ok=True)
        except Exception as e:
            print(f"创建日志目录失败: {e}")
    
    def _setup_root_logger(self):
        """设置根日志记录器"""
        # 清除现有的处理器
        root_logger = logging.getLogger()
        for handler in root_logger.handlers[:]:
            root_logger.removeHandler(handler)
        
        # 设置根日志级别
        root_logger.setLevel(self.log_level)
    
    def get_logger(self, name: str) -> logging.Logger:
        """
        获取指定名称的日志记录器
        
        Args:
            name: 日志记录器名称，通常使用模块名
            
        Returns:
            logging.Logger: 配置好的日志记录器
        """
        if name in self.loggers:
            return self.loggers[name]
        
        logger = logging.getLogger(name)
        logger.setLevel(self.log_level)
        
        # 避免重复添加处理器
        if not logger.handlers:
            # 控制台处理器
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setLevel(self.log_level)
            console_formatter = logging.Formatter(
                '%(asctime)s [%(levelname)s] %(name)s: %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
            console_handler.setFormatter(console_formatter)
            logger.addHandler(console_handler)
            
            # 文件处理器（仅在生产环境或明确要求时启用）
            if self._should_enable_file_logging():
                file_handler = self._create_file_handler(name)
                if file_handler:
                    logger.addHandler(file_handler)
        
        # 防止日志向上传播到根记录器
        logger.propagate = False
        
        self.loggers[name] = logger
        return logger
    
    def _should_enable_file_logging(self) -> bool:
        """判断是否应该启用文件日志"""
        # 生产环境或明确设置了文件日志
        return (os.environ.get('FLASK_ENV') == 'production' or 
                os.environ.get('ENABLE_FILE_LOGGING', '').lower() == 'true')
    
    def _create_file_handler(self, logger_name: str) -> Optional[logging.Handler]:
        """创建文件处理器"""
        try:
            # 按日期和模块名创建日志文件
            today = datetime.now().strftime('%Y-%m-%d')
            log_filename = f"{logger_name}_{today}.log"
            log_filepath = os.path.join(self.log_dir, log_filename)
            
            # 使用RotatingFileHandler避免文件过大
            file_handler = logging.handlers.RotatingFileHandler(
                log_filepath,
                maxBytes=10*1024*1024,  # 10MB
                backupCount=5,
                encoding='utf-8'
            )
            file_handler.setLevel(self.log_level)
            
            file_formatter = logging.Formatter(
                '%(asctime)s [%(levelname)s] %(name)s:%(lineno)d - %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
            file_handler.setFormatter(file_formatter)
            
            return file_handler
            
        except Exception as e:
            print(f"创建文件日志处理器失败: {e}")
            return None
    
    def set_level(self, level: str):
        """动态设置日志级别"""
        level_map = {
            'DEBUG': logging.DEBUG,
            'INFO': logging.INFO,
            'WARNING': logging.WARNING,
            'ERROR': logging.ERROR,
            'CRITICAL': logging.CRITICAL
        }
        
        if level.upper() in level_map:
            self.log_level = level_map[level.upper()]
            
            # 更新所有已创建的logger
            for logger in self.loggers.values():
                logger.setLevel(self.log_level)
                for handler in logger.handlers:
                    handler.setLevel(self.log_level)


# 全局日志配置实例
_logger_config = LoggerConfig()


def get_logger(name: str = None) -> logging.Logger:
    """
    便捷函数：获取日志记录器
    
    Args:
        name: 日志记录器名称，如果为None则使用调用模块的名称
        
    Returns:
        logging.Logger: 配置好的日志记录器
    """
    if name is None:
        # 自动获取调用模块的名称
        import inspect
        frame = inspect.currentframe().f_back
        name = frame.f_globals.get('__name__', 'unknown')
    
    return _logger_config.get_logger(name)


def set_log_level(level: str):
    """便捷函数：设置全局日志级别"""
    _logger_config.set_level(level)


# 为了向后兼容，提供一些常用的日志函数
def log_info(message: str, logger_name: str = 'system'):
    """记录信息级别日志"""
    get_logger(logger_name).info(message)


def log_warning(message: str, logger_name: str = 'system'):
    """记录警告级别日志"""
    get_logger(logger_name).warning(message)


def log_error(message: str, logger_name: str = 'system'):
    """记录错误级别日志"""
    get_logger(logger_name).error(message)


def log_debug(message: str, logger_name: str = 'system'):
    """记录调试级别日志"""
    get_logger(logger_name).debug(message)


# 安全的打印函数，处理编码问题
def safe_print(message: str, level: str = 'INFO', logger_name: str = 'system'):
    """
    安全的打印函数，自动处理编码问题
    
    Args:
        message: 要输出的消息
        level: 日志级别
        logger_name: 日志记录器名称
    """
    try:
        logger = get_logger(logger_name)
        level_map = {
            'DEBUG': logger.debug,
            'INFO': logger.info,
            'WARNING': logger.warning,
            'ERROR': logger.error,
            'CRITICAL': logger.critical
        }
        
        log_func = level_map.get(level.upper(), logger.info)
        log_func(message)
        
    except UnicodeEncodeError:
        # 如果遇到编码问题，使用基本的print输出
        try:
            safe_message = message.encode('ascii', errors='ignore').decode('ascii')
            print(f"[{level}] {safe_message}")
        except Exception:
            print(f"[{level}] [编码错误] 消息长度: {len(message)}")
    except Exception as e:
        print(f"日志输出失败: {e}")


if __name__ == "__main__":
    # 测试日志配置
    test_logger = get_logger('test')
    test_logger.debug("这是调试信息")
    test_logger.info("这是信息日志")
    test_logger.warning("这是警告信息")
    test_logger.error("这是错误信息")
    test_logger.critical("这是严重错误信息")
