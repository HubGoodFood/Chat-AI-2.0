# -*- coding: utf-8 -*-
"""
性能数据收集器 - 收集和分析系统性能指标

这个模块负责收集AI客服系统的各种性能指标，包括：
1. 响应时间统计
2. 缓存性能分析
3. 系统资源监控
4. 用户体验指标

适合编程初学者学习：
- 了解性能监控的重要性
- 学习如何收集和分析性能数据
- 理解性能优化的量化方法
- 掌握系统监控的基本概念
"""

import time
import threading
from collections import deque, defaultdict
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from src.models.operation_logger import operation_logger


class PerformanceCollector:
    """
    性能数据收集器
    
    这个类负责收集和分析AI客服系统的性能数据，
    为性能优化提供数据支持。
    
    主要功能：
    1. 响应时间统计：记录和分析API响应时间
    2. 缓存性能监控：跟踪缓存命中率和效果
    3. 系统资源监控：监控CPU、内存等资源使用
    4. 性能趋势分析：分析性能变化趋势
    """
    
    def __init__(self, max_records: int = 1000):
        """
        初始化性能收集器
        
        Args:
            max_records (int): 最大记录数量，防止内存泄漏
        """
        self.max_records = max_records
        
        # 响应时间记录（使用deque实现固定大小的环形缓冲区）
        self.response_times = deque(maxlen=max_records)
        
        # 缓存性能记录
        self.cache_stats = {
            'total_requests': 0,
            'cache_hits': 0,
            'cache_misses': 0,
            'exact_matches': 0,
            'similarity_matches': 0
        }
        
        # 按时间段统计的性能数据
        self.hourly_stats = defaultdict(lambda: {
            'requests': 0,
            'total_response_time': 0,
            'cache_hits': 0,
            'errors': 0
        })
        
        # 错误统计
        self.error_stats = defaultdict(int)
        
        # 用户体验指标
        self.user_experience = {
            'fast_responses': 0,      # 快速响应（<3秒）
            'normal_responses': 0,    # 正常响应（3-8秒）
            'slow_responses': 0,      # 慢速响应（>8秒）
            'timeout_responses': 0    # 超时响应
        }
        
        # 线程锁，确保数据一致性
        self._lock = threading.Lock()
        
        operation_logger.info("性能数据收集器初始化完成")
    
    def record_response_time(self, response_time: float, is_cache_hit: bool = False, 
                           cache_type: str = None) -> None:
        """
        记录响应时间
        
        这是性能监控的核心方法，记录每次API调用的响应时间。
        通过分析这些数据，我们可以了解系统的性能表现。
        
        Args:
            response_time (float): 响应时间（毫秒）
            is_cache_hit (bool): 是否命中缓存
            cache_type (str): 缓存类型（'exact', 'similarity', None）
        """
        with self._lock:
            try:
                # 记录响应时间
                timestamp = time.time()
                self.response_times.append({
                    'timestamp': timestamp,
                    'response_time': response_time,
                    'is_cache_hit': is_cache_hit,
                    'cache_type': cache_type
                })
                
                # 更新缓存统计
                self.cache_stats['total_requests'] += 1
                if is_cache_hit:
                    self.cache_stats['cache_hits'] += 1
                    if cache_type == 'exact':
                        self.cache_stats['exact_matches'] += 1
                    elif cache_type == 'similarity':
                        self.cache_stats['similarity_matches'] += 1
                else:
                    self.cache_stats['cache_misses'] += 1
                
                # 更新用户体验指标
                if response_time < 3000:
                    self.user_experience['fast_responses'] += 1
                elif response_time < 8000:
                    self.user_experience['normal_responses'] += 1
                elif response_time < 30000:
                    self.user_experience['slow_responses'] += 1
                else:
                    self.user_experience['timeout_responses'] += 1
                
                # 更新小时统计
                hour_key = datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H')
                self.hourly_stats[hour_key]['requests'] += 1
                self.hourly_stats[hour_key]['total_response_time'] += response_time
                if is_cache_hit:
                    self.hourly_stats[hour_key]['cache_hits'] += 1
                
                operation_logger.debug(f"记录响应时间: {response_time:.0f}ms, 缓存命中: {is_cache_hit}")
                
            except Exception as e:
                operation_logger.error(f"记录响应时间失败: {e}")
    
    def record_error(self, error_type: str, error_message: str = None) -> None:
        """
        记录错误信息
        
        Args:
            error_type (str): 错误类型
            error_message (str): 错误消息
        """
        with self._lock:
            try:
                self.error_stats[error_type] += 1
                
                # 更新小时统计
                hour_key = datetime.now().strftime('%Y-%m-%d %H')
                self.hourly_stats[hour_key]['errors'] += 1
                
                operation_logger.warning(f"记录错误: {error_type} - {error_message}")
                
            except Exception as e:
                operation_logger.error(f"记录错误失败: {e}")
    
    def get_performance_summary(self) -> Dict:
        """
        获取性能摘要
        
        返回系统性能的整体概况，包括响应时间统计、
        缓存性能、用户体验指标等。
        
        Returns:
            Dict: 性能摘要数据
        """
        with self._lock:
            try:
                # 计算响应时间统计
                response_times_list = [r['response_time'] for r in self.response_times]
                
                if response_times_list:
                    avg_response_time = sum(response_times_list) / len(response_times_list)
                    min_response_time = min(response_times_list)
                    max_response_time = max(response_times_list)
                    
                    # 计算百分位数
                    sorted_times = sorted(response_times_list)
                    p50 = sorted_times[len(sorted_times) // 2] if sorted_times else 0
                    p95_index = int(len(sorted_times) * 0.95)
                    p95 = sorted_times[p95_index] if sorted_times else 0
                else:
                    avg_response_time = min_response_time = max_response_time = p50 = p95 = 0
                
                # 计算缓存命中率
                total_requests = self.cache_stats['total_requests']
                hit_rate = (self.cache_stats['cache_hits'] / total_requests * 100) if total_requests > 0 else 0
                
                # 计算用户体验分数（0-100）
                total_responses = sum(self.user_experience.values())
                if total_responses > 0:
                    ux_score = (
                        self.user_experience['fast_responses'] * 100 +
                        self.user_experience['normal_responses'] * 70 +
                        self.user_experience['slow_responses'] * 30 +
                        self.user_experience['timeout_responses'] * 0
                    ) / total_responses
                else:
                    ux_score = 0
                
                return {
                    'response_time_stats': {
                        'average': round(avg_response_time, 2),
                        'minimum': round(min_response_time, 2),
                        'maximum': round(max_response_time, 2),
                        'p50': round(p50, 2),
                        'p95': round(p95, 2),
                        'total_samples': len(response_times_list)
                    },
                    'cache_performance': {
                        'total_requests': total_requests,
                        'cache_hits': self.cache_stats['cache_hits'],
                        'cache_misses': self.cache_stats['cache_misses'],
                        'hit_rate_percentage': round(hit_rate, 2),
                        'exact_matches': self.cache_stats['exact_matches'],
                        'similarity_matches': self.cache_stats['similarity_matches']
                    },
                    'user_experience': {
                        'score': round(ux_score, 1),
                        'fast_responses': self.user_experience['fast_responses'],
                        'normal_responses': self.user_experience['normal_responses'],
                        'slow_responses': self.user_experience['slow_responses'],
                        'timeout_responses': self.user_experience['timeout_responses']
                    },
                    'error_stats': dict(self.error_stats),
                    'timestamp': datetime.now().isoformat()
                }
                
            except Exception as e:
                operation_logger.error(f"获取性能摘要失败: {e}")
                return {}
    
    def get_hourly_trends(self, hours: int = 24) -> List[Dict]:
        """
        获取小时趋势数据
        
        Args:
            hours (int): 获取最近几小时的数据
            
        Returns:
            List[Dict]: 小时趋势数据
        """
        with self._lock:
            try:
                trends = []
                now = datetime.now()
                
                for i in range(hours):
                    hour_time = now - timedelta(hours=i)
                    hour_key = hour_time.strftime('%Y-%m-%d %H')
                    
                    stats = self.hourly_stats.get(hour_key, {
                        'requests': 0,
                        'total_response_time': 0,
                        'cache_hits': 0,
                        'errors': 0
                    })
                    
                    avg_response_time = (stats['total_response_time'] / stats['requests']) if stats['requests'] > 0 else 0
                    hit_rate = (stats['cache_hits'] / stats['requests'] * 100) if stats['requests'] > 0 else 0
                    
                    trends.append({
                        'hour': hour_key,
                        'timestamp': hour_time.isoformat(),
                        'requests': stats['requests'],
                        'avg_response_time': round(avg_response_time, 2),
                        'cache_hit_rate': round(hit_rate, 2),
                        'errors': stats['errors']
                    })
                
                return list(reversed(trends))  # 按时间正序返回
                
            except Exception as e:
                operation_logger.error(f"获取小时趋势失败: {e}")
                return []
    
    def get_performance_recommendations(self) -> List[str]:
        """
        获取性能优化建议
        
        基于收集的性能数据，提供具体的优化建议。
        
        Returns:
            List[str]: 优化建议列表
        """
        recommendations = []
        
        try:
            summary = self.get_performance_summary()
            
            # 响应时间建议
            avg_time = summary['response_time_stats']['average']
            if avg_time > 8000:
                recommendations.append("平均响应时间过长，建议优化LLM API调用或增加缓存策略")
            elif avg_time > 5000:
                recommendations.append("响应时间偏长，可考虑优化数据库查询或增加预缓存")
            
            # 缓存建议
            hit_rate = summary['cache_performance']['hit_rate_percentage']
            if hit_rate < 30:
                recommendations.append("缓存命中率较低，建议调整相似度阈值或增加常见问题预缓存")
            elif hit_rate < 60:
                recommendations.append("缓存效果良好，可考虑优化相似匹配算法提升命中率")
            
            # 用户体验建议
            ux_score = summary['user_experience']['score']
            if ux_score < 60:
                recommendations.append("用户体验分数较低，建议重点优化响应速度")
            elif ux_score < 80:
                recommendations.append("用户体验良好，可进一步优化慢速响应的比例")
            
            # 错误率建议
            total_requests = summary['cache_performance']['total_requests']
            total_errors = sum(summary['error_stats'].values())
            if total_requests > 0:
                error_rate = (total_errors / total_requests) * 100
                if error_rate > 5:
                    recommendations.append("错误率较高，建议检查系统稳定性和错误处理机制")
            
            if not recommendations:
                recommendations.append("系统性能表现良好，继续保持当前优化策略")
            
        except Exception as e:
            operation_logger.error(f"生成性能建议失败: {e}")
            recommendations.append("无法生成性能建议，请检查系统状态")
        
        return recommendations
    
    def reset_stats(self) -> None:
        """
        重置统计数据
        
        清空所有收集的性能数据，用于重新开始统计。
        """
        with self._lock:
            try:
                self.response_times.clear()
                self.cache_stats = {
                    'total_requests': 0,
                    'cache_hits': 0,
                    'cache_misses': 0,
                    'exact_matches': 0,
                    'similarity_matches': 0
                }
                self.hourly_stats.clear()
                self.error_stats.clear()
                self.user_experience = {
                    'fast_responses': 0,
                    'normal_responses': 0,
                    'slow_responses': 0,
                    'timeout_responses': 0
                }
                
                operation_logger.info("性能统计数据已重置")
                
            except Exception as e:
                operation_logger.error(f"重置统计数据失败: {e}")


# 创建全局性能收集器实例
performance_collector = PerformanceCollector()
