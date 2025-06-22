# -*- coding: utf-8 -*-
"""
增强的搜索服务 - 支持全文搜索和智能匹配
"""
import logging
import re
import jieba
from typing import List, Dict, Any, Optional, Tuple
from rapidfuzz import fuzz, process
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func, text
from ..database.database_config import db_config
from ..database.models import Product
from .cache_service import cached

logger = logging.getLogger(__name__)


class SearchService:
    """增强的搜索服务"""
    
    def __init__(self):
        self.fuzzy_threshold = 70  # 模糊匹配阈值
        self.max_suggestions = 10  # 最大建议数量
        
        # 初始化中文分词
        jieba.initialize()
    
    @cached(prefix="search:products", timeout=300)
    def search_products_advanced(self, 
                                query: str,
                                category: str = None,
                                storage_area: str = None,
                                price_range: Tuple[float, float] = None,
                                stock_range: Tuple[int, int] = None,
                                sort_by: str = 'relevance',
                                page: int = 1,
                                per_page: int = 20) -> Dict[str, Any]:
        """高级产品搜索"""
        try:
            with db_config.get_session() as session:
                # 构建基础查询
                db_query = session.query(Product).filter(Product.status == 'active')
                
                # 分类过滤
                if category:
                    db_query = db_query.filter(Product.category == category)
                
                # 存储区域过滤
                if storage_area:
                    db_query = db_query.filter(Product.storage_area == storage_area)
                
                # 价格范围过滤
                if price_range:
                    min_price, max_price = price_range
                    if min_price is not None:
                        db_query = db_query.filter(Product.price >= min_price)
                    if max_price is not None:
                        db_query = db_query.filter(Product.price <= max_price)
                
                # 库存范围过滤
                if stock_range:
                    min_stock, max_stock = stock_range
                    if min_stock is not None:
                        db_query = db_query.filter(Product.current_stock >= min_stock)
                    if max_stock is not None:
                        db_query = db_query.filter(Product.current_stock <= max_stock)
                
                # 文本搜索
                if query and query.strip():
                    search_results = self._search_by_text(session, query.strip(), db_query)
                else:
                    # 无搜索词时获取所有匹配的产品
                    search_results = [(product, 100) for product in db_query.all()]
                
                # 排序
                if sort_by == 'price_asc':
                    search_results.sort(key=lambda x: x[0].price)
                elif sort_by == 'price_desc':
                    search_results.sort(key=lambda x: x[0].price, reverse=True)
                elif sort_by == 'stock_asc':
                    search_results.sort(key=lambda x: x[0].current_stock)
                elif sort_by == 'stock_desc':
                    search_results.sort(key=lambda x: x[0].current_stock, reverse=True)
                elif sort_by == 'name':
                    search_results.sort(key=lambda x: x[0].product_name)
                else:  # relevance (默认)
                    search_results.sort(key=lambda x: x[1], reverse=True)
                
                # 分页
                total = len(search_results)
                start = (page - 1) * per_page
                end = start + per_page
                page_results = search_results[start:end]
                
                # 转换为字典格式
                products = []
                for product, score in page_results:
                    product_dict = product.to_dict()
                    product_dict['search_score'] = score
                    products.append(product_dict)
                
                return {
                    'products': products,
                    'total': total,
                    'page': page,
                    'per_page': per_page,
                    'pages': (total + per_page - 1) // per_page,
                    'has_prev': page > 1,
                    'has_next': page * per_page < total,
                    'search_stats': {
                        'query': query,
                        'exact_matches': len([r for r in search_results if r[1] >= 95]),
                        'fuzzy_matches': len([r for r in search_results if 70 <= r[1] < 95]),
                        'partial_matches': len([r for r in search_results if r[1] < 70])
                    }
                }
                
        except Exception as e:
            logger.error(f"高级搜索失败: {e}")
            raise
    
    def _search_by_text(self, session: Session, query: str, base_query) -> List[Tuple[Product, int]]:
        """基于文本的搜索"""
        results = []
        products = base_query.all()
        
        # 预处理查询词
        processed_query = self._preprocess_query(query)
        query_tokens = self._tokenize(processed_query)
        
        for product in products:
            score = self._calculate_product_score(product, query, query_tokens)
            if score > 0:
                results.append((product, score))
        
        return results
    
    def _preprocess_query(self, query: str) -> str:
        """预处理查询词"""
        # 移除特殊字符，保留中文、英文、数字
        query = re.sub(r'[^\u4e00-\u9fff\w\s]', ' ', query)
        # 去除多余空格
        query = re.sub(r'\s+', ' ', query.strip())
        return query
    
    def _tokenize(self, text: str) -> List[str]:
        """分词"""
        if not text:
            return []
        
        # 中文分词
        tokens = list(jieba.cut(text))
        # 过滤短词和停用词
        tokens = [token.strip() for token in tokens if len(token.strip()) > 1]
        return tokens
    
    def _calculate_product_score(self, product: Product, query: str, query_tokens: List[str]) -> int:
        """计算产品匹配分数"""
        max_score = 0
        
        # 搜索字段和权重
        search_fields = [
            (product.product_name, 100),      # 产品名称权重最高
            (product.keywords or '', 80),     # 关键词次高
            (product.description or '', 60),  # 描述中等
            (product.barcode or '', 90),      # 条码很高
            (product.category, 50),           # 分类较低
            (product.specification or '', 40) # 规格最低
        ]
        
        for field_value, weight in search_fields:
            if not field_value:
                continue
            
            # 精确匹配
            if query.lower() in field_value.lower():
                score = weight
                if query.lower() == field_value.lower():
                    score = weight  # 完全匹配
                else:
                    score = int(weight * 0.8)  # 包含匹配
                max_score = max(max_score, score)
                continue
            
            # 模糊匹配
            fuzzy_score = fuzz.partial_ratio(query.lower(), field_value.lower())
            if fuzzy_score >= self.fuzzy_threshold:
                score = int(weight * fuzzy_score / 100 * 0.7)  # 模糊匹配折扣
                max_score = max(max_score, score)
            
            # 分词匹配
            field_tokens = self._tokenize(field_value)
            token_matches = 0
            for query_token in query_tokens:
                for field_token in field_tokens:
                    if query_token.lower() in field_token.lower():
                        token_matches += 1
                        break
            
            if token_matches > 0:
                token_score = int(weight * (token_matches / len(query_tokens)) * 0.6)
                max_score = max(max_score, token_score)
        
        return max_score
    
    def get_search_suggestions(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """获取搜索建议"""
        try:
            if not query or len(query.strip()) < 2:
                return []
            
            with db_config.get_session() as session:
                # 获取所有活跃产品的名称和关键词
                products = session.query(Product).filter(Product.status == 'active').all()
                
                suggestions = set()
                
                # 收集候选词
                candidates = []
                for product in products:
                    candidates.append(product.product_name)
                    if product.keywords:
                        candidates.extend(product.keywords.split(','))
                    if product.category:
                        candidates.append(product.category)
                
                # 模糊匹配
                matches = process.extract(query, candidates, limit=limit*2, scorer=fuzz.partial_ratio)
                
                for match_text, score in matches:
                    if score >= 60:  # 降低建议阈值
                        suggestions.add(match_text.strip())
                
                # 转换为结果格式
                result = []
                for suggestion in list(suggestions)[:limit]:
                    result.append({
                        'text': suggestion,
                        'type': 'suggestion'
                    })
                
                return result
                
        except Exception as e:
            logger.error(f"获取搜索建议失败: {e}")
            return []
    
    @cached(prefix="search:categories", timeout=600)
    def get_category_facets(self) -> List[Dict[str, Any]]:
        """获取分类聚合信息"""
        try:
            with db_config.get_session() as session:
                result = session.query(
                    Product.category,
                    func.count(Product.id).label('count'),
                    func.avg(Product.price).label('avg_price'),
                    func.min(Product.price).label('min_price'),
                    func.max(Product.price).label('max_price')
                ).filter(Product.status == 'active').group_by(Product.category).all()
                
                return [
                    {
                        'category': row.category,
                        'count': row.count,
                        'avg_price': round(float(row.avg_price), 2) if row.avg_price else 0,
                        'min_price': float(row.min_price),
                        'max_price': float(row.max_price)
                    }
                    for row in result
                ]
        except Exception as e:
            logger.error(f"获取分类聚合失败: {e}")
            return []
    
    @cached(prefix="search:price_ranges", timeout=600)
    def get_price_ranges(self) -> Dict[str, Any]:
        """获取价格区间统计"""
        try:
            with db_config.get_session() as session:
                result = session.query(
                    func.min(Product.price).label('min_price'),
                    func.max(Product.price).label('max_price'),
                    func.avg(Product.price).label('avg_price'),
                    func.count(Product.id).label('total_count')
                ).filter(Product.status == 'active').first()
                
                if not result or not result.min_price:
                    return {}
                
                min_price = float(result.min_price)
                max_price = float(result.max_price)
                
                # 生成价格区间
                ranges = []
                if max_price > min_price:
                    step = (max_price - min_price) / 5
                    for i in range(5):
                        range_min = min_price + i * step
                        range_max = min_price + (i + 1) * step
                        
                        count = session.query(func.count(Product.id)).filter(
                            and_(
                                Product.status == 'active',
                                Product.price >= range_min,
                                Product.price < range_max if i < 4 else Product.price <= range_max
                            )
                        ).scalar()
                        
                        ranges.append({
                            'min': round(range_min, 2),
                            'max': round(range_max, 2),
                            'count': count,
                            'label': f"¥{range_min:.0f} - ¥{range_max:.0f}"
                        })
                
                return {
                    'min_price': min_price,
                    'max_price': max_price,
                    'avg_price': round(float(result.avg_price), 2),
                    'total_count': result.total_count,
                    'ranges': ranges
                }
                
        except Exception as e:
            logger.error(f"获取价格区间失败: {e}")
            return {}
    
    def search_similar_products(self, product_id: int, limit: int = 5) -> List[Dict[str, Any]]:
        """搜索相似产品"""
        try:
            with db_config.get_session() as session:
                # 获取基准产品
                base_product = session.query(Product).filter(
                    and_(Product.id == product_id, Product.status == 'active')
                ).first()
                
                if not base_product:
                    return []
                
                # 搜索相似产品
                similar_products = session.query(Product).filter(
                    and_(
                        Product.id != product_id,
                        Product.status == 'active',
                        or_(
                            Product.category == base_product.category,
                            Product.keywords.like(f"%{base_product.keywords}%") if base_product.keywords else False
                        )
                    )
                ).limit(limit * 2).all()  # 获取更多候选
                
                # 计算相似度并排序
                scored_products = []
                for product in similar_products:
                    score = self._calculate_similarity_score(base_product, product)
                    if score > 30:  # 最低相似度阈值
                        scored_products.append((product, score))
                
                # 按相似度排序并返回
                scored_products.sort(key=lambda x: x[1], reverse=True)
                
                return [
                    {
                        **product.to_dict(),
                        'similarity_score': score
                    }
                    for product, score in scored_products[:limit]
                ]
                
        except Exception as e:
            logger.error(f"搜索相似产品失败: {e}")
            return []
    
    def _calculate_similarity_score(self, product1: Product, product2: Product) -> int:
        """计算产品相似度分数"""
        score = 0
        
        # 分类相同加分
        if product1.category == product2.category:
            score += 40
        
        # 价格相近加分
        if product1.price and product2.price:
            price_diff = abs(product1.price - product2.price)
            max_price = max(product1.price, product2.price)
            if max_price > 0:
                price_similarity = 1 - (price_diff / max_price)
                score += int(price_similarity * 20)
        
        # 名称相似度
        if product1.product_name and product2.product_name:
            name_similarity = fuzz.ratio(product1.product_name, product2.product_name)
            score += int(name_similarity * 0.3)
        
        # 关键词相似度
        if product1.keywords and product2.keywords:
            keyword_similarity = fuzz.ratio(product1.keywords, product2.keywords)
            score += int(keyword_similarity * 0.2)
        
        return min(score, 100)  # 最高100分


# 全局搜索服务实例
search_service = SearchService()