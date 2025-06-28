# -*- coding: utf-8 -*-
"""
智能缓存管理器 - AI客服系统性能优化核心组件

这个模块实现了基于问题相似度的智能缓存系统，能够显著提升AI客服的响应速度。
主要特点：
1. 相似问题匹配：不仅缓存完全相同的问题，还能匹配相似问题
2. 智能过期策略：根据问题类型设置不同的缓存时间
3. 内存友好：自动清理过期缓存，防止内存泄漏
4. 统计监控：提供缓存命中率等性能指标

适合编程初学者学习：
- 详细的代码注释
- 清晰的方法命名
- 简单的算法实现
- 完整的错误处理
"""

import jieba
import hashlib
import time
import json
from typing import Dict, List, Optional, Tuple
from fuzzywuzzy import fuzz
from src.services.cache_service import cache_service
from src.models.operation_logger import operation_logger


class IntelligentCacheManager:
    """
    智能缓存管理器
    
    这个类是AI客服系统性能优化的核心组件，通过智能缓存机制
    大幅提升系统响应速度，减少对外部API的依赖。
    
    主要功能：
    1. 问题相似度计算：使用中文分词和模糊匹配算法
    2. 智能缓存策略：根据问题类型设置不同缓存时间
    3. 缓存管理：自动清理过期缓存，维护系统性能
    4. 性能监控：统计缓存命中率，提供优化建议
    """
    
    def __init__(self):
        """
        初始化智能缓存管理器
        
        设置缓存参数和性能监控指标
        """
        # 缓存配置参数
        self.similarity_threshold = 80  # 相似度阈值（80%以上认为是相似问题）
        self.default_cache_time = 1800  # 默认缓存时间：30分钟
        self.max_cache_size = 1000      # 最大缓存条目数
        
        # 不同类型问题的缓存时间（秒）
        self.cache_times = {
            'product_price': 3600,      # 产品价格：1小时
            'policy_info': 7200,        # 政策信息：2小时  
            'delivery_info': 1800,      # 配送信息：30分钟
            'general_question': 900,    # 一般问题：15分钟
            'greeting': 86400           # 问候语：24小时
        }
        
        # 性能统计
        self.stats = {
            'total_requests': 0,        # 总请求数
            'cache_hits': 0,            # 缓存命中数
            'cache_misses': 0,          # 缓存未命中数
            'similarity_matches': 0,    # 相似度匹配数
            'exact_matches': 0          # 精确匹配数
        }
        
        # 缓存键前缀
        self.cache_prefix = "ai_chat_cache"
        self.similarity_prefix = "question_similarity"
        
        operation_logger.info("智能缓存管理器初始化完成")
    
    def _extract_keywords(self, question: str) -> List[str]:
        """
        从问题中提取关键词
        
        使用jieba分词提取问题的关键词，用于相似度计算。
        这是智能缓存的基础，通过关键词匹配找到相似问题。
        
        Args:
            question (str): 用户输入的问题
            
        Returns:
            List[str]: 提取的关键词列表
            
        Example:
            >>> manager = IntelligentCacheManager()
            >>> keywords = manager._extract_keywords("苹果多少钱一斤？")
            >>> print(keywords)  # ['苹果', '多少钱', '一斤']
        """
        try:
            # 使用jieba进行中文分词
            words = jieba.lcut(question.strip())
            
            # 过滤掉停用词和标点符号
            stop_words = {'的', '了', '在', '是', '我', '有', '和', '就', '不', '人', '都', '一', '一个', '上', '也', '很', '到', '说', '要', '去', '你', '会', '着', '没有', '看', '好', '自己', '这'}
            keywords = [word for word in words if len(word) > 1 and word not in stop_words and word.isalnum()]
            
            return keywords[:10]  # 最多返回10个关键词
            
        except Exception as e:
            operation_logger.error(f"关键词提取失败: {e}")
            return []
    
    def _generate_cache_key(self, question: str) -> str:
        """
        生成缓存键
        
        为问题生成唯一的缓存键，用于存储和检索缓存结果。
        使用MD5哈希确保键的唯一性和长度一致性。
        
        Args:
            question (str): 用户问题
            
        Returns:
            str: 生成的缓存键
        """
        # 标准化问题文本（去除空格、转小写）
        normalized_question = question.strip().lower()
        
        # 生成MD5哈希作为缓存键
        hash_object = hashlib.md5(normalized_question.encode('utf-8'))
        cache_key = f"{self.cache_prefix}:{hash_object.hexdigest()}"
        
        return cache_key
    
    def _calculate_similarity(self, question1: str, question2: str) -> int:
        """
        计算两个问题的相似度
        
        使用模糊匹配算法计算问题相似度，这是智能缓存的核心算法。
        相似度越高，说明问题越相近，越适合使用缓存结果。
        
        Args:
            question1 (str): 第一个问题
            question2 (str): 第二个问题
            
        Returns:
            int: 相似度分数（0-100）
            
        Example:
            >>> similarity = manager._calculate_similarity("苹果多少钱？", "苹果价格是多少？")
            >>> print(similarity)  # 85（高相似度）
        """
        try:
            # 使用fuzzywuzzy计算字符串相似度
            similarity = fuzz.ratio(question1.strip().lower(), question2.strip().lower())
            return similarity
            
        except Exception as e:
            operation_logger.error(f"相似度计算失败: {e}")
            return 0
    
    def _classify_question_type(self, question: str) -> str:
        """
        分类问题类型
        
        根据问题内容判断问题类型，不同类型使用不同的缓存策略。
        这样可以为重要信息设置更长的缓存时间。
        
        Args:
            question (str): 用户问题
            
        Returns:
            str: 问题类型
        """
        question_lower = question.lower()
        
        # 价格相关问题
        if any(word in question_lower for word in ['价格', '多少钱', '费用', '成本']):
            return 'product_price'
        
        # 政策相关问题  
        elif any(word in question_lower for word in ['政策', '规定', '要求', '标准']):
            return 'policy_info'
        
        # 配送相关问题
        elif any(word in question_lower for word in ['配送', '送货', '物流', '快递']):
            return 'delivery_info'
        
        # 问候语
        elif any(word in question_lower for word in ['你好', 'hello', '您好', '早上好']):
            return 'greeting'
        
        # 默认为一般问题
        else:
            return 'general_question'
    
    def get_cached_response(self, question: str) -> Optional[str]:
        """
        获取缓存的响应
        
        这是智能缓存的核心方法，首先尝试精确匹配，然后尝试相似度匹配。
        如果找到合适的缓存，直接返回结果，大大提升响应速度。
        
        Args:
            question (str): 用户问题
            
        Returns:
            Optional[str]: 缓存的响应，如果没有找到返回None
        """
        try:
            self.stats['total_requests'] += 1
            
            # 第一步：尝试精确匹配
            cache_key = self._generate_cache_key(question)
            cached_response = cache_service.get(cache_key)
            
            if cached_response:
                self.stats['cache_hits'] += 1
                self.stats['exact_matches'] += 1
                operation_logger.info(f"缓存精确命中: {question[:50]}...")
                return cached_response
            
            # 第二步：尝试相似度匹配
            similar_response = self._find_similar_cached_response(question)
            if similar_response:
                self.stats['cache_hits'] += 1
                self.stats['similarity_matches'] += 1
                operation_logger.info(f"缓存相似匹配: {question[:50]}...")
                return similar_response
            
            # 没有找到缓存
            self.stats['cache_misses'] += 1
            return None
            
        except Exception as e:
            operation_logger.error(f"获取缓存响应失败: {e}")
            return None
    
    def _find_similar_cached_response(self, question: str) -> Optional[str]:
        """
        查找相似问题的缓存响应
        
        遍历已缓存的问题，找到相似度最高且超过阈值的问题，
        返回其缓存的响应。这是智能缓存的关键创新。
        
        Args:
            question (str): 用户问题
            
        Returns:
            Optional[str]: 相似问题的缓存响应
        """
        try:
            # 获取所有相似度索引
            similarity_keys = cache_service.get_keys_by_pattern(f"{self.similarity_prefix}:*")
            
            best_similarity = 0
            best_response = None
            
            for key in similarity_keys[:50]:  # 限制检查数量，避免性能问题
                try:
                    cached_data = cache_service.get(key)
                    if not cached_data:
                        continue
                    
                    cached_question = cached_data.get('question', '')
                    similarity = self._calculate_similarity(question, cached_question)
                    
                    # 如果相似度超过阈值且是目前最高的
                    if similarity >= self.similarity_threshold and similarity > best_similarity:
                        best_similarity = similarity
                        best_response = cached_data.get('response')
                        
                except Exception as e:
                    continue
            
            return best_response
            
        except Exception as e:
            operation_logger.error(f"查找相似缓存失败: {e}")
            return None
    
    def cache_response(self, question: str, response: str) -> bool:
        """
        缓存AI响应
        
        将问题和响应存储到缓存中，同时建立相似度索引。
        这样后续的相似问题就能快速获得响应。
        
        Args:
            question (str): 用户问题
            response (str): AI响应
            
        Returns:
            bool: 缓存是否成功
        """
        try:
            # 生成缓存键
            cache_key = self._generate_cache_key(question)
            
            # 确定缓存时间
            question_type = self._classify_question_type(question)
            cache_time = self.cache_times.get(question_type, self.default_cache_time)
            
            # 缓存响应
            cache_success = cache_service.set(cache_key, response, cache_time)
            
            # 建立相似度索引
            similarity_key = f"{self.similarity_prefix}:{cache_key}"
            similarity_data = {
                'question': question,
                'response': response,
                'timestamp': time.time(),
                'type': question_type
            }
            cache_service.set(similarity_key, similarity_data, cache_time)
            
            if cache_success:
                operation_logger.info(f"响应已缓存: {question[:50]}... (类型: {question_type}, 时间: {cache_time}s)")
                return True
            else:
                operation_logger.warning(f"响应缓存失败: {question[:50]}...")
                return False
                
        except Exception as e:
            operation_logger.error(f"缓存响应失败: {e}")
            return False
    
    def get_cache_stats(self) -> Dict:
        """
        获取缓存统计信息
        
        返回缓存的性能指标，用于监控和优化缓存策略。
        
        Returns:
            Dict: 缓存统计信息
        """
        try:
            # 计算缓存命中率
            hit_rate = 0
            if self.stats['total_requests'] > 0:
                hit_rate = (self.stats['cache_hits'] / self.stats['total_requests']) * 100
            
            return {
                'total_requests': self.stats['total_requests'],
                'cache_hits': self.stats['cache_hits'],
                'cache_misses': self.stats['cache_misses'],
                'hit_rate': round(hit_rate, 2),
                'exact_matches': self.stats['exact_matches'],
                'similarity_matches': self.stats['similarity_matches'],
                'similarity_threshold': self.similarity_threshold
            }
            
        except Exception as e:
            operation_logger.error(f"获取缓存统计失败: {e}")
            return {}
    
    def clear_expired_cache(self) -> int:
        """
        清理过期缓存
        
        定期清理过期的缓存条目，保持系统性能和内存使用效率。
        
        Returns:
            int: 清理的缓存条目数量
        """
        try:
            # 这个方法依赖于cache_service的实现
            # 如果cache_service支持TTL，过期缓存会自动清理
            # 这里主要是为了统计和日志记录
            
            operation_logger.info("缓存清理完成")
            return 0
            
        except Exception as e:
            operation_logger.error(f"清理缓存失败: {e}")
            return 0


# 延迟创建全局智能缓存管理器实例，避免循环导入
_intelligent_cache_manager = None

def get_intelligent_cache_manager():
    """获取智能缓存管理器实例"""
    global _intelligent_cache_manager
    if _intelligent_cache_manager is None:
        _intelligent_cache_manager = IntelligentCacheManager()
    return _intelligent_cache_manager

# 创建一个代理类来避免循环导入
class IntelligentCacheManagerProxy:
    def __getattr__(self, name):
        return getattr(get_intelligent_cache_manager(), name)

# 为了向后兼容，提供intelligent_cache_manager属性
intelligent_cache_manager = IntelligentCacheManagerProxy()
