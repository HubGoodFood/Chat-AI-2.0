# -*- coding: utf-8 -*-
"""
数据库化数据处理器 - 优化知识检索性能

这个模块将知识检索从文件系统迁移到数据库，大幅提升查询性能。
主要优化：
1. 使用数据库索引替代线性搜索
2. 实现查询结果缓存
3. 支持复杂的搜索条件组合
4. 提供性能监控和统计

适合编程初学者学习：
- 了解数据库查询优化的重要性
- 学习如何使用SQLAlchemy进行高效查询
- 理解索引对查询性能的影响
- 掌握缓存在数据库优化中的作用
"""

import time
import jieba
from typing import List, Dict, Optional, Tuple
from sqlalchemy import text, or_, and_, func
from sqlalchemy.orm import Session
from fuzzywuzzy import fuzz

from ..database.database_config import db_config
from ..database.models import Product
from ..services.cache_service import cache_service
from ..models.operation_logger import operation_logger
from ..services.performance_collector import performance_collector


class DatabaseDataProcessor:
    """
    数据库化数据处理器
    
    这个类将知识检索从文件系统迁移到数据库，提供高性能的产品搜索功能。
    通过使用数据库索引、查询优化和缓存机制，大幅提升搜索性能。
    
    主要特性：
    1. 基于数据库的高效搜索：利用索引和SQL优化
    2. 智能缓存机制：缓存常见搜索结果
    3. 多维度搜索：支持名称、关键词、分类等多种搜索
    4. 性能监控：记录查询时间和缓存命中率
    """
    
    def __init__(self):
        """
        初始化数据库数据处理器
        """
        self.policy_data = None
        self.policy_keywords = {}

        # 兼容性属性：为了与原DataProcessor保持兼容
        self.products_df = None  # 数据库处理器不使用DataFrame，但保持兼容性

        # 搜索权重配置
        self.search_weights = {
            'exact_name_match': 100,      # 产品名称精确匹配
            'partial_name_match': 80,     # 产品名称部分匹配
            'keyword_match': 60,          # 关键词匹配
            'category_match': 40,         # 分类匹配
            'description_match': 20,      # 描述匹配
            'fuzzy_match_threshold': 70   # 模糊匹配阈值
        }

        # 初始化政策数据（保持与原版兼容）
        self._load_policy_data()

        operation_logger.info("数据库化数据处理器初始化完成")

    def load_data(self):
        """
        加载数据（兼容性方法）

        数据库处理器不需要显式加载数据，因为数据已经在数据库中。
        这个方法是为了与原DataProcessor保持兼容性。
        """
        operation_logger.info("数据库处理器：数据已在数据库中，无需加载")
        pass
    
    def _load_policy_data(self):
        """
        加载政策数据
        
        保持与原DataProcessor的政策处理兼容性
        """
        try:
            import json
            with open('data/policy.json', 'r', encoding='utf-8') as f:
                self.policy_data = json.load(f)
            
            # 建立政策关键词索引
            self._build_policy_keywords()
            
            operation_logger.info("政策数据加载成功")
            
        except Exception as e:
            operation_logger.error(f"政策数据加载失败: {e}")
            # 使用默认政策数据
            self.policy_data = {"sections": {}}
    
    def _build_policy_keywords(self):
        """建立政策关键词索引"""
        policy_mapping = {
            'mission': ['使命', '理念', '介绍', '关于我们', '拼台'],
            'group_rules': ['群规', '规则', '禁止', '违规', '管理'],
            'product_quality': ['质量', '品质', '退款', '换货', '问题', '保证'],
            'delivery': ['配送', '送货', '运费', '起送', '免费配送', '外围'],
            'payment': ['付款', '支付', 'venmo', '现金', '备注', '手续费'],
            'pickup': ['取货', '自取', 'malden', 'chinatown', '取货点'],
            'after_sale': ['售后', '退款', '更换', '质量问题', '反馈'],
            'community': ['社区', '拼友', '互助', '感恩', '建议']
        }
        
        for section, keywords in policy_mapping.items():
            self.policy_keywords[section] = keywords
    
    def search_products(self, query: str, limit: int = 5) -> List[Dict]:
        """
        🚀 优化的产品搜索方法
        
        使用数据库查询替代文件系统搜索，大幅提升性能。
        利用数据库索引和SQL优化，支持复杂的搜索条件。
        
        Args:
            query (str): 搜索查询字符串
            limit (int): 返回结果数量限制
            
        Returns:
            List[Dict]: 搜索结果列表，按相关性排序
            
        Example:
            >>> processor = DatabaseDataProcessor()
            >>> results = processor.search_products("苹果")
            >>> print(f"找到 {len(results)} 个相关产品")
        """
        if not query or not query.strip():
            return []
        
        # 🚀 检查缓存
        cache_key = f"db_product_search:{query.strip()}:{limit}"
        cached_result = cache_service.get(cache_key)
        if cached_result:
            operation_logger.debug(f"产品搜索缓存命中: {query[:20]}...")
            return cached_result
        
        # 🚀 记录查询开始时间
        start_time = time.time()
        
        try:
            with db_config.get_session() as session:
                # 🚀 使用数据库查询进行高效搜索
                results = self._execute_database_search(session, query.strip(), limit)
                
                # 🚀 记录查询性能
                query_time = (time.time() - start_time) * 1000
                performance_collector.record_response_time(query_time, False, None)
                operation_logger.debug(f"数据库产品搜索完成: {query[:20]}... 耗时: {query_time:.0f}ms")
                
                # 🚀 缓存搜索结果
                cache_service.set(cache_key, results, timeout=300)  # 5分钟缓存
                
                return results
                
        except Exception as e:
            query_time = (time.time() - start_time) * 1000
            performance_collector.record_error('database_search_error', str(e))
            operation_logger.error(f"数据库产品搜索失败: {e}")
            
            # 🚀 降级到空结果（保持系统稳定性）
            return []
    
    def _execute_database_search(self, session: Session, query: str, limit: int) -> List[Dict]:
        """
        执行数据库搜索查询
        
        这是搜索优化的核心方法，使用SQL查询和索引来提升性能。
        
        Args:
            session (Session): 数据库会话
            query (str): 搜索查询
            limit (int): 结果限制
            
        Returns:
            List[Dict]: 搜索结果
        """
        # 🚀 使用jieba分词提取关键词
        keywords = [kw.strip() for kw in jieba.lcut(query.lower()) if len(kw.strip()) > 1]
        
        if not keywords:
            return []
        
        # 🚀 构建高效的数据库查询
        search_conditions = []
        
        # 精确名称匹配（最高权重）
        for keyword in keywords:
            search_conditions.append(
                (Product.product_name.ilike(f'%{keyword}%'), self.search_weights['exact_name_match'])
            )
        
        # 关键词匹配
        for keyword in keywords:
            search_conditions.append(
                (Product.keywords.ilike(f'%{keyword}%'), self.search_weights['keyword_match'])
            )
        
        # 分类匹配
        for keyword in keywords:
            search_conditions.append(
                (Product.category.ilike(f'%{keyword}%'), self.search_weights['category_match'])
            )
        
        # 描述匹配
        for keyword in keywords:
            search_conditions.append(
                (Product.description.ilike(f'%{keyword}%'), self.search_weights['description_match'])
            )
        
        # 🚀 执行优化的数据库查询
        # 使用UNION ALL合并多个查询条件，利用索引优化
        base_query = session.query(Product).filter(Product.status == 'active')

        # 构建OR条件进行搜索
        or_conditions = []
        for condition, weight in search_conditions:
            or_conditions.append(condition)

        if or_conditions:
            products = base_query.filter(or_(*or_conditions)).limit(limit * 2).all()  # 获取更多结果用于排序
        else:
            products = []
        
        # 🚀 计算相关性分数并排序
        scored_results = []
        for product in products:
            score = self._calculate_relevance_score(product, keywords)
            if score > 0:
                product_dict = {
                    'name': product.product_name,
                    'specification': product.specification or '',
                    'price': float(product.price),
                    'unit': product.unit,
                    'category': product.category,
                    'keywords': product.keywords or '',
                    'taste': '',  # 兼容性字段
                    'origin': '',  # 兼容性字段
                    'benefits': '',  # 兼容性字段
                    'suitable_for': '',  # 兼容性字段
                    'score': score,
                    'description': product.description or ''
                }
                scored_results.append(product_dict)
        
        # 🚀 按分数排序并返回限定数量的结果
        scored_results.sort(key=lambda x: x['score'], reverse=True)
        return scored_results[:limit]
    
    def _calculate_relevance_score(self, product: Product, keywords: List[str]) -> float:
        """
        计算产品与搜索关键词的相关性分数
        
        Args:
            product (Product): 产品对象
            keywords (List[str]): 搜索关键词列表
            
        Returns:
            float: 相关性分数
        """
        total_score = 0
        
        product_name = (product.product_name or '').lower()
        product_keywords = (product.keywords or '').lower()
        product_category = (product.category or '').lower()
        product_description = (product.description or '').lower()
        
        for keyword in keywords:
            keyword_lower = keyword.lower()
            
            # 产品名称匹配
            if keyword_lower == product_name:
                total_score += self.search_weights['exact_name_match']
            elif keyword_lower in product_name:
                total_score += self.search_weights['partial_name_match']
            else:
                # 模糊匹配
                fuzzy_score = fuzz.partial_ratio(keyword_lower, product_name)
                if fuzzy_score >= self.search_weights['fuzzy_match_threshold']:
                    total_score += (fuzzy_score / 100) * self.search_weights['partial_name_match']
            
            # 关键词匹配
            if keyword_lower in product_keywords:
                total_score += self.search_weights['keyword_match']
            
            # 分类匹配
            if keyword_lower in product_category:
                total_score += self.search_weights['category_match']
            
            # 描述匹配
            if keyword_lower in product_description:
                total_score += self.search_weights['description_match']
        
        return total_score
    
    def search_policies(self, query: str) -> List[Dict]:
        """
        搜索政策信息（保持与原版兼容）
        
        Args:
            query (str): 搜索查询
            
        Returns:
            List[Dict]: 政策搜索结果
        """
        if self.policy_data is None:
            return []
        
        # 🚀 检查缓存
        cache_key = f"policy_search:{query.strip()}"
        cached_result = cache_service.get(cache_key)
        if cached_result:
            return cached_result
        
        query_keywords = jieba.lcut(query.lower())
        results = []
        
        for section_name, keywords in self.policy_keywords.items():
            score = 0
            
            # 关键词匹配
            for qk in query_keywords:
                for pk in keywords:
                    if qk == pk or qk in pk or pk in qk:
                        score += 10
                    elif fuzz.ratio(qk, pk) > 70:
                        score += 5
            
            if score > 0:
                section_content = self.policy_data['sections'].get(section_name, {})
                policy_info = {
                    'section': section_name,
                    'content': section_content,
                    'score': score
                }
                results.append(policy_info)
        
        # 按分数排序
        results.sort(key=lambda x: x['score'], reverse=True)
        
        # 🚀 缓存结果
        cache_service.set(cache_key, results, timeout=600)  # 10分钟缓存
        
        return results
    
    def get_product_by_name(self, name: str) -> Optional[Dict]:
        """
        根据产品名称获取详细信息（数据库版本）
        
        Args:
            name (str): 产品名称
            
        Returns:
            Optional[Dict]: 产品信息字典
        """
        if not name or not name.strip():
            return None
        
        # 🚀 检查缓存
        cache_key = f"product_by_name:{name.strip()}"
        cached_result = cache_service.get(cache_key)
        if cached_result:
            return cached_result
        
        try:
            with db_config.get_session() as session:
                # 🚀 使用数据库查询
                product = session.query(Product).filter(
                    and_(
                        Product.product_name.ilike(f'%{name.strip()}%'),
                        Product.status == 'active'
                    )
                ).first()
                
                if product:
                    result = {
                        'name': product.product_name,
                        'specification': product.specification or '',
                        'price': float(product.price),
                        'unit': product.unit,
                        'category': product.category,
                        'keywords': product.keywords or '',
                        'taste': '',  # 兼容性字段
                        'origin': '',  # 兼容性字段
                        'benefits': '',  # 兼容性字段
                        'suitable_for': '',  # 兼容性字段
                        'description': product.description or ''
                    }
                    
                    # 🚀 缓存结果
                    cache_service.set(cache_key, result, timeout=600)
                    return result
                
        except Exception as e:
            operation_logger.error(f"根据名称获取产品失败: {e}")
        
        return None
    
    def get_all_categories(self) -> List[str]:
        """
        获取所有产品分类（数据库版本）
        
        Returns:
            List[str]: 分类列表
        """
        # 🚀 检查缓存
        cache_key = "all_categories"
        cached_result = cache_service.get(cache_key)
        if cached_result:
            return cached_result
        
        try:
            with db_config.get_session() as session:
                # 🚀 使用数据库查询获取所有分类
                categories = session.query(Product.category).filter(
                    Product.status == 'active'
                ).distinct().all()
                
                result = [cat[0] for cat in categories if cat[0]]
                
                # 🚀 缓存结果
                cache_service.set(cache_key, result, timeout=1800)  # 30分钟缓存
                return result
                
        except Exception as e:
            operation_logger.error(f"获取分类列表失败: {e}")
            return []
    
    def get_products_by_category(self, category: str) -> List[Dict]:
        """
        根据分类获取产品（数据库版本）
        
        Args:
            category (str): 产品分类
            
        Returns:
            List[Dict]: 产品列表
        """
        if not category:
            return []
        
        # 🚀 检查缓存
        cache_key = f"products_by_category:{category}"
        cached_result = cache_service.get(cache_key)
        if cached_result:
            return cached_result
        
        try:
            with db_config.get_session() as session:
                # 🚀 使用数据库查询
                products = session.query(Product).filter(
                    and_(
                        Product.category == category,
                        Product.status == 'active'
                    )
                ).order_by(Product.product_name).all()
                
                result = []
                for product in products:
                    product_dict = {
                        'name': product.product_name,
                        'specification': product.specification or '',
                        'price': float(product.price),
                        'unit': product.unit,
                        'category': product.category,
                        'keywords': product.keywords or '',
                        'taste': '',  # 兼容性字段
                        'origin': '',  # 兼容性字段
                        'benefits': '',  # 兼容性字段
                        'suitable_for': ''  # 兼容性字段
                    }
                    result.append(product_dict)
                
                # 🚀 缓存结果
                cache_service.set(cache_key, result, timeout=600)  # 10分钟缓存
                return result
                
        except Exception as e:
            operation_logger.error(f"根据分类获取产品失败: {e}")
            return []

    def get_all_product_names(self) -> List[str]:
        """
        获取所有产品名称（兼容性方法）

        为了与原DataProcessor的extract_product_names方法兼容，
        提供获取所有产品名称的功能。

        Returns:
            List[str]: 所有产品名称列表
        """
        # 🚀 检查缓存
        cache_key = "all_product_names"
        cached_result = cache_service.get(cache_key)
        if cached_result:
            return cached_result

        try:
            with db_config.get_session() as session:
                # 🚀 使用数据库查询获取所有产品名称
                product_names = session.query(Product.product_name).filter(
                    Product.status == 'active'
                ).all()

                result = [name[0] for name in product_names if name[0]]

                # 🚀 缓存结果
                cache_service.set(cache_key, result, timeout=1800)  # 30分钟缓存
                return result

        except Exception as e:
            operation_logger.error(f"获取产品名称列表失败: {e}")
            return []
