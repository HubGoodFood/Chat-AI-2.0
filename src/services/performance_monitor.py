# -*- coding: utf-8 -*-
"""
性能监控服务
"""
import time
import psutil
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from functools import wraps
from collections import defaultdict, deque
from threading import Lock
from ..database.database_config import db_config
from .cache_service import cache_service

logger = logging.getLogger(__name__)


class PerformanceMonitor:
    """性能监控器"""
    
    def __init__(self):
        self.metrics = defaultdict(lambda: deque(maxlen=1000))  # 保留最近1000条记录
        self.lock = Lock()
        self.start_time = datetime.utcnow()
        
        # API调用统计
        self.api_stats = defaultdict(lambda: {
            'count': 0,
            'total_time': 0,
            'avg_time': 0,
            'min_time': float('inf'),
            'max_time': 0,
            'errors': 0,
            'last_called': None
        })
    
    def record_metric(self, name: str, value: float, tags: Dict[str, str] = None):
        """记录性能指标"""
        with self.lock:
            timestamp = datetime.utcnow()
            self.metrics[name].append({
                'value': value,
                'timestamp': timestamp,
                'tags': tags or {}
            })
    
    def record_api_call(self, endpoint: str, duration: float, success: bool = True):
        """记录API调用"""
        with self.lock:
            stats = self.api_stats[endpoint]
            stats['count'] += 1
            stats['total_time'] += duration
            stats['avg_time'] = stats['total_time'] / stats['count']
            stats['min_time'] = min(stats['min_time'], duration)
            stats['max_time'] = max(stats['max_time'], duration)
            stats['last_called'] = datetime.utcnow()
            
            if not success:
                stats['errors'] += 1
    
    def get_system_metrics(self) -> Dict[str, Any]:
        """获取系统性能指标"""
        try:
            # CPU使用率
            cpu_percent = psutil.cpu_percent(interval=1)
            
            # 内存使用
            memory = psutil.virtual_memory()
            
            # 磁盘使用
            disk = psutil.disk_usage('/')
            
            # 进程信息
            process = psutil.Process()
            process_memory = process.memory_info()
            
            return {
                'cpu': {
                    'percent': cpu_percent,
                    'count': psutil.cpu_count()
                },
                'memory': {
                    'total': memory.total,
                    'available': memory.available,
                    'percent': memory.percent,
                    'used': memory.used
                },
                'disk': {
                    'total': disk.total,
                    'used': disk.used,
                    'free': disk.free,
                    'percent': (disk.used / disk.total) * 100
                },
                'process': {
                    'memory_rss': process_memory.rss,
                    'memory_vms': process_memory.vms,
                    'cpu_percent': process.cpu_percent(),
                    'num_threads': process.num_threads(),
                    'create_time': process.create_time()
                },
                'timestamp': datetime.utcnow().isoformat()
            }
        except Exception as e:
            logger.error(f"获取系统指标失败: {e}")
            return {}
    
    def get_database_metrics(self) -> Dict[str, Any]:
        """获取数据库性能指标"""
        try:
            conn_info = db_config.get_connection_info()
            health = db_config.health_check()
            
            # 获取连接池信息
            pool_info = {}
            if db_config.engine and hasattr(db_config.engine, 'pool'):
                pool = db_config.engine.pool
                pool_info = {
                    'size': getattr(pool, 'size', lambda: 0)(),
                    'checked_in': getattr(pool, 'checkedin', lambda: 0)(),
                    'checked_out': getattr(pool, 'checkedout', lambda: 0)(),
                    'overflow': getattr(pool, 'overflow', lambda: 0)(),
                    'invalid': getattr(pool, 'invalid', lambda: 0)()
                }
            
            return {
                'health': health,
                'connection_info': conn_info,
                'pool': pool_info,
                'timestamp': datetime.utcnow().isoformat()
            }
        except Exception as e:
            logger.error(f"获取数据库指标失败: {e}")
            return {'health': False, 'error': str(e)}
    
    def get_cache_metrics(self) -> Dict[str, Any]:
        """获取缓存性能指标"""
        try:
            cache_stats = cache_service.get_stats()
            return {
                **cache_stats,
                'timestamp': datetime.utcnow().isoformat()
            }
        except Exception as e:
            logger.error(f"获取缓存指标失败: {e}")
            return {'error': str(e)}
    
    def get_api_metrics(self) -> Dict[str, Any]:
        """获取API性能指标"""
        with self.lock:
            # 转换为可序列化的格式
            api_metrics = {}
            for endpoint, stats in self.api_stats.items():
                api_metrics[endpoint] = {
                    **stats,
                    'last_called': stats['last_called'].isoformat() if stats['last_called'] else None,
                    'error_rate': stats['errors'] / stats['count'] if stats['count'] > 0 else 0
                }
            
            return {
                'endpoints': api_metrics,
                'total_requests': sum(stats['count'] for stats in self.api_stats.values()),
                'total_errors': sum(stats['errors'] for stats in self.api_stats.values()),
                'uptime_seconds': (datetime.utcnow() - self.start_time).total_seconds(),
                'timestamp': datetime.utcnow().isoformat()
            }
    
    def get_custom_metrics(self, metric_name: str = None, 
                          since: datetime = None) -> Dict[str, Any]:
        """获取自定义指标"""
        with self.lock:
            if metric_name:
                metrics = {metric_name: list(self.metrics[metric_name])}
            else:
                metrics = {name: list(values) for name, values in self.metrics.items()}
            
            # 时间过滤
            if since:
                filtered_metrics = {}
                for name, values in metrics.items():
                    filtered_values = [
                        v for v in values 
                        if v['timestamp'] >= since
                    ]
                    filtered_metrics[name] = filtered_values
                metrics = filtered_metrics
            
            return {
                'metrics': metrics,
                'timestamp': datetime.utcnow().isoformat()
            }
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """获取性能摘要"""
        try:
            system = self.get_system_metrics()
            database = self.get_database_metrics()
            cache = self.get_cache_metrics()
            api = self.get_api_metrics()
            
            # 计算健康评分
            health_score = self._calculate_health_score(system, database, cache, api)
            
            return {
                'health_score': health_score,
                'system': system,
                'database': database,
                'cache': cache,
                'api': api,
                'uptime': (datetime.utcnow() - self.start_time).total_seconds(),
                'timestamp': datetime.utcnow().isoformat()
            }
        except Exception as e:
            logger.error(f"获取性能摘要失败: {e}")
            return {'error': str(e)}
    
    def _calculate_health_score(self, system: Dict, database: Dict, 
                               cache: Dict, api: Dict) -> int:
        """计算系统健康评分（0-100）"""
        score = 100
        
        # CPU使用率评分
        if system.get('cpu', {}).get('percent', 0) > 80:
            score -= 20
        elif system.get('cpu', {}).get('percent', 0) > 60:
            score -= 10
        
        # 内存使用率评分
        memory_percent = system.get('memory', {}).get('percent', 0)
        if memory_percent > 90:
            score -= 25
        elif memory_percent > 70:
            score -= 15
        
        # 磁盘使用率评分
        disk_percent = system.get('disk', {}).get('percent', 0)
        if disk_percent > 90:
            score -= 15
        elif disk_percent > 80:
            score -= 10
        
        # 数据库健康评分
        if not database.get('health', False):
            score -= 30
        
        # 缓存状态评分
        if cache.get('type') == 'memory':  # Redis不可用时使用内存缓存
            score -= 10
        
        # API错误率评分
        total_requests = api.get('total_requests', 0)
        total_errors = api.get('total_errors', 0)
        if total_requests > 0:
            error_rate = total_errors / total_requests
            if error_rate > 0.1:  # 10%错误率
                score -= 20
            elif error_rate > 0.05:  # 5%错误率
                score -= 10
        
        return max(0, min(100, score))
    
    def cleanup_old_metrics(self, days: int = 7):
        """清理旧的性能指标"""
        cutoff_time = datetime.utcnow() - timedelta(days=days)
        
        with self.lock:
            for metric_name, values in self.metrics.items():
                # 过滤掉旧数据
                new_values = deque(
                    [v for v in values if v['timestamp'] > cutoff_time],
                    maxlen=values.maxlen
                )
                self.metrics[metric_name] = new_values
        
        logger.info(f"已清理{days}天前的性能指标")


# 全局性能监控实例
performance_monitor = PerformanceMonitor()


def monitor_performance(endpoint_name: str = None):
    """性能监控装饰器"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            success = True
            
            try:
                result = func(*args, **kwargs)
                return result
            except Exception as e:
                success = False
                raise
            finally:
                duration = time.time() - start_time
                endpoint = endpoint_name or func.__name__
                
                # 记录API调用
                performance_monitor.record_api_call(endpoint, duration, success)
                
                # 记录响应时间
                performance_monitor.record_metric(
                    f'response_time.{endpoint}',
                    duration,
                    {'endpoint': endpoint, 'success': str(success)}
                )
        
        return wrapper
    return decorator


def record_business_metric(metric_name: str, value: float, tags: Dict[str, str] = None):
    """记录业务指标的便利函数"""
    performance_monitor.record_metric(metric_name, value, tags)