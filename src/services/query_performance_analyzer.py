# -*- coding: utf-8 -*-
"""
查询性能分析器 - 监控和优化数据库查询性能

这个模块专门用于分析和优化数据库查询性能，提供：
1. 查询时间监控
2. 慢查询检测
3. 查询计划分析
4. 性能优化建议

适合编程初学者学习：
- 了解数据库查询性能监控的重要性
- 学习如何识别和优化慢查询
- 理解查询计划和索引的作用
- 掌握数据库性能调优的基本方法
"""

import time
import threading
from collections import defaultdict, deque
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from contextlib import contextmanager

from ..models.operation_logger import operation_logger


class QueryPerformanceAnalyzer:
    """
    查询性能分析器
    
    这个类负责监控数据库查询性能，识别慢查询，
    并提供性能优化建议。
    
    主要功能：
    1. 查询时间监控：记录每个查询的执行时间
    2. 慢查询检测：识别执行时间过长的查询
    3. 查询统计：分析查询模式和频率
    4. 性能建议：基于分析结果提供优化建议
    """
    
    def __init__(self, slow_query_threshold: float = 1000.0):
        """
        初始化查询性能分析器
        
        Args:
            slow_query_threshold (float): 慢查询阈值（毫秒）
        """
        self.slow_query_threshold = slow_query_threshold
        
        # 查询统计数据
        self.query_stats = defaultdict(lambda: {
            'count': 0,
            'total_time': 0,
            'min_time': float('inf'),
            'max_time': 0,
            'avg_time': 0,
            'slow_queries': 0
        })
        
        # 慢查询记录（最近100条）
        self.slow_queries = deque(maxlen=100)
        
        # 查询历史记录（最近1000条）
        self.query_history = deque(maxlen=1000)
        
        # 线程锁
        self._lock = threading.Lock()
        
        operation_logger.info(f"查询性能分析器初始化完成，慢查询阈值: {slow_query_threshold}ms")
    
    @contextmanager
    def monitor_query(self, query_type: str, query_description: str = ""):
        """
        查询监控上下文管理器
        
        使用方法：
        with analyzer.monitor_query('product_search', '搜索苹果'):
            # 执行数据库查询
            results = session.query(Product).filter(...).all()
        
        Args:
            query_type (str): 查询类型（如：product_search, policy_search等）
            query_description (str): 查询描述
        """
        start_time = time.time()
        query_info = {
            'type': query_type,
            'description': query_description,
            'start_time': start_time,
            'timestamp': datetime.now()
        }
        
        try:
            yield query_info
        except Exception as e:
            query_info['error'] = str(e)
            raise
        finally:
            end_time = time.time()
            execution_time = (end_time - start_time) * 1000  # 转换为毫秒
            
            query_info.update({
                'end_time': end_time,
                'execution_time_ms': execution_time,
                'success': 'error' not in query_info
            })
            
            self._record_query_performance(query_info)
    
    def _record_query_performance(self, query_info: Dict[str, Any]) -> None:
        """
        记录查询性能数据
        
        Args:
            query_info (Dict): 查询信息
        """
        with self._lock:
            try:
                query_type = query_info['type']
                execution_time = query_info['execution_time_ms']
                
                # 更新查询统计
                stats = self.query_stats[query_type]
                stats['count'] += 1
                stats['total_time'] += execution_time
                stats['min_time'] = min(stats['min_time'], execution_time)
                stats['max_time'] = max(stats['max_time'], execution_time)
                stats['avg_time'] = stats['total_time'] / stats['count']
                
                # 检查是否为慢查询
                if execution_time >= self.slow_query_threshold:
                    stats['slow_queries'] += 1
                    self.slow_queries.append({
                        'type': query_type,
                        'description': query_info.get('description', ''),
                        'execution_time_ms': execution_time,
                        'timestamp': query_info['timestamp'],
                        'error': query_info.get('error')
                    })
                    
                    operation_logger.warning(
                        f"慢查询检测: {query_type} - {execution_time:.0f}ms - {query_info.get('description', '')}"
                    )
                
                # 记录查询历史
                self.query_history.append({
                    'type': query_type,
                    'execution_time_ms': execution_time,
                    'timestamp': query_info['timestamp'],
                    'success': query_info['success']
                })
                
                operation_logger.debug(
                    f"查询性能记录: {query_type} - {execution_time:.0f}ms"
                )
                
            except Exception as e:
                operation_logger.error(f"记录查询性能失败: {e}")
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """
        获取性能摘要
        
        Returns:
            Dict: 性能摘要数据
        """
        with self._lock:
            try:
                summary = {
                    'total_queries': sum(stats['count'] for stats in self.query_stats.values()),
                    'total_slow_queries': sum(stats['slow_queries'] for stats in self.query_stats.values()),
                    'slow_query_threshold_ms': self.slow_query_threshold,
                    'query_types': {}
                }
                
                # 计算总体慢查询率
                if summary['total_queries'] > 0:
                    summary['slow_query_rate'] = (summary['total_slow_queries'] / summary['total_queries']) * 100
                else:
                    summary['slow_query_rate'] = 0
                
                # 各类型查询统计
                for query_type, stats in self.query_stats.items():
                    if stats['count'] > 0:
                        slow_rate = (stats['slow_queries'] / stats['count']) * 100
                        summary['query_types'][query_type] = {
                            'count': stats['count'],
                            'avg_time_ms': round(stats['avg_time'], 2),
                            'min_time_ms': round(stats['min_time'], 2),
                            'max_time_ms': round(stats['max_time'], 2),
                            'slow_queries': stats['slow_queries'],
                            'slow_query_rate': round(slow_rate, 2)
                        }
                
                return summary
                
            except Exception as e:
                operation_logger.error(f"获取性能摘要失败: {e}")
                return {}
    
    def get_slow_queries(self, limit: int = 20) -> List[Dict]:
        """
        获取慢查询列表
        
        Args:
            limit (int): 返回数量限制
            
        Returns:
            List[Dict]: 慢查询列表
        """
        with self._lock:
            try:
                # 按时间倒序返回最近的慢查询
                recent_slow_queries = list(self.slow_queries)[-limit:]
                recent_slow_queries.reverse()
                
                return [
                    {
                        'type': query['type'],
                        'description': query['description'],
                        'execution_time_ms': query['execution_time_ms'],
                        'timestamp': query['timestamp'].isoformat(),
                        'has_error': 'error' in query and query['error'] is not None
                    }
                    for query in recent_slow_queries
                ]
                
            except Exception as e:
                operation_logger.error(f"获取慢查询列表失败: {e}")
                return []
    
    def get_query_trends(self, hours: int = 24) -> List[Dict]:
        """
        获取查询趋势数据
        
        Args:
            hours (int): 获取最近几小时的数据
            
        Returns:
            List[Dict]: 查询趋势数据
        """
        with self._lock:
            try:
                now = datetime.now()
                cutoff_time = now - timedelta(hours=hours)
                
                # 按小时分组统计
                hourly_stats = defaultdict(lambda: {
                    'total_queries': 0,
                    'slow_queries': 0,
                    'total_time': 0,
                    'avg_time': 0
                })
                
                for query in self.query_history:
                    if query['timestamp'] >= cutoff_time:
                        hour_key = query['timestamp'].strftime('%Y-%m-%d %H:00')
                        stats = hourly_stats[hour_key]
                        
                        stats['total_queries'] += 1
                        stats['total_time'] += query['execution_time_ms']
                        
                        if query['execution_time_ms'] >= self.slow_query_threshold:
                            stats['slow_queries'] += 1
                
                # 计算平均时间
                for stats in hourly_stats.values():
                    if stats['total_queries'] > 0:
                        stats['avg_time'] = stats['total_time'] / stats['total_queries']
                
                # 转换为列表并排序
                trends = []
                for hour_key, stats in hourly_stats.items():
                    trends.append({
                        'hour': hour_key,
                        'total_queries': stats['total_queries'],
                        'slow_queries': stats['slow_queries'],
                        'avg_time_ms': round(stats['avg_time'], 2),
                        'slow_query_rate': round((stats['slow_queries'] / stats['total_queries']) * 100, 2) if stats['total_queries'] > 0 else 0
                    })
                
                trends.sort(key=lambda x: x['hour'])
                return trends
                
            except Exception as e:
                operation_logger.error(f"获取查询趋势失败: {e}")
                return []
    
    def get_optimization_recommendations(self) -> List[str]:
        """
        获取性能优化建议
        
        Returns:
            List[str]: 优化建议列表
        """
        try:
            recommendations = []
            summary = self.get_performance_summary()
            
            # 总体慢查询率建议
            slow_rate = summary.get('slow_query_rate', 0)
            if slow_rate > 20:
                recommendations.append(f"慢查询率过高 ({slow_rate:.1f}%)，建议检查数据库索引和查询优化")
            elif slow_rate > 10:
                recommendations.append(f"慢查询率偏高 ({slow_rate:.1f}%)，建议优化常见查询")
            
            # 各类型查询建议
            for query_type, stats in summary.get('query_types', {}).items():
                avg_time = stats['avg_time_ms']
                slow_rate = stats['slow_query_rate']
                
                if avg_time > 2000:  # 平均时间超过2秒
                    recommendations.append(f"{query_type} 查询平均时间过长 ({avg_time:.0f}ms)，建议优化查询逻辑")
                
                if slow_rate > 30:  # 慢查询率超过30%
                    recommendations.append(f"{query_type} 慢查询率过高 ({slow_rate:.1f}%)，建议添加索引或优化查询条件")
            
            # 通用优化建议
            if summary.get('total_queries', 0) > 100:
                if not recommendations:
                    recommendations.append("查询性能良好，建议继续监控并定期优化")
                
                recommendations.extend([
                    "建议定期分析查询计划，确保索引被正确使用",
                    "考虑为常见查询添加缓存机制",
                    "监控数据库连接池使用情况"
                ])
            
            if not recommendations:
                recommendations.append("暂无足够数据生成优化建议，请继续使用系统")
            
            return recommendations
            
        except Exception as e:
            operation_logger.error(f"生成优化建议失败: {e}")
            return ["无法生成优化建议，请检查系统状态"]
    
    def reset_statistics(self) -> None:
        """
        重置统计数据
        """
        with self._lock:
            try:
                self.query_stats.clear()
                self.slow_queries.clear()
                self.query_history.clear()
                
                operation_logger.info("查询性能统计数据已重置")
                
            except Exception as e:
                operation_logger.error(f"重置统计数据失败: {e}")
    
    def export_performance_data(self) -> Dict[str, Any]:
        """
        导出性能数据
        
        Returns:
            Dict: 完整的性能数据
        """
        with self._lock:
            try:
                return {
                    'summary': self.get_performance_summary(),
                    'slow_queries': self.get_slow_queries(50),
                    'trends': self.get_query_trends(48),  # 48小时趋势
                    'recommendations': self.get_optimization_recommendations(),
                    'export_timestamp': datetime.now().isoformat(),
                    'slow_query_threshold_ms': self.slow_query_threshold
                }
                
            except Exception as e:
                operation_logger.error(f"导出性能数据失败: {e}")
                return {}


# 创建全局查询性能分析器实例
query_performance_analyzer = QueryPerformanceAnalyzer()
