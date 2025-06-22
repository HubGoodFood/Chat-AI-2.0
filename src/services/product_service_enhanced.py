# -*- coding: utf-8 -*-
"""
增强的产品服务 - 使用数据库仓库模式和Redis缓存
"""
import logging
from typing import List, Dict, Any, Optional, Tuple
from flask import current_app
from ..database.database_config import db_config
from ..repositories.product_repository import ProductRepository
from ..database.models import Product
from .cache_service import cached, cache_invalidate, CacheKeys, invalidate_product_cache

logger = logging.getLogger(__name__)


class ProductServiceEnhanced:
    """增强的产品服务"""
    
    def __init__(self):
        self.cache_timeout = 300  # 5分钟缓存
    
    def _get_repository(self) -> ProductRepository:
        """获取产品仓库实例"""
        session = db_config.get_session_factory()()
        return ProductRepository(session)
    
    @cached(prefix="product:search", timeout=300)
    def search_products(self, 
                       query: str = None,
                       category: str = None,
                       storage_area: str = None,
                       low_stock_only: bool = False,
                       page: int = 1,
                       per_page: int = 20) -> Dict[str, Any]:
        """搜索产品（支持分页）"""
        try:
            with db_config.get_session() as session:
                repo = ProductRepository(session)
                
                # 构建过滤条件
                filters = {
                    'status': 'active'
                }
                
                if category:
                    filters['category'] = category
                
                if storage_area:
                    filters['storage_area'] = storage_area
                
                if low_stock_only:
                    # 使用查询方法而不是过滤器
                    products = repo.get_low_stock_products()
                    
                    # 手动分页
                    total = len(products)
                    start = (page - 1) * per_page
                    end = start + per_page
                    items = products[start:end]
                    
                    return {
                        'products': [self._product_to_dict(p) for p in items],
                        'total': total,
                        'page': page,
                        'per_page': per_page,
                        'pages': (total + per_page - 1) // per_page,
                        'has_prev': page > 1,
                        'has_next': page * per_page < total
                    }
                else:
                    # 使用仓库搜索方法
                    products = repo.search_products(
                        query=query,
                        category=category,
                        storage_area=storage_area,
                        limit=per_page,
                        offset=(page - 1) * per_page
                    )
                    
                    # 获取总数
                    total_query_filters = filters.copy()
                    if query:
                        # 对于文本搜索，需要特殊处理总数计算
                        all_products = repo.search_products(
                            query=query,
                            category=category,
                            storage_area=storage_area
                        )
                        total = len(all_products)
                    else:
                        total = repo.count(**total_query_filters)
                    
                    return {
                        'products': [self._product_to_dict(p) for p in products],
                        'total': total,
                        'page': page,
                        'per_page': per_page,
                        'pages': (total + per_page - 1) // per_page,
                        'has_prev': page > 1,
                        'has_next': page * per_page < total
                    }
                    
        except Exception as e:
            logger.error(f"搜索产品失败: {e}")
            raise
    
    @cached(prefix="product:id", timeout=600)
    def get_product_by_id(self, product_id: int) -> Optional[Dict[str, Any]]:
        """根据ID获取产品"""
        try:
            with db_config.get_session() as session:
                repo = ProductRepository(session)
                product = repo.get_by_id(product_id)
                return self._product_to_dict(product) if product else None
        except Exception as e:
            logger.error(f"获取产品失败: {e}")
            raise
    
    @cached(prefix="product:barcode", timeout=600)
    def get_product_by_barcode(self, barcode: str) -> Optional[Dict[str, Any]]:
        """根据条码获取产品"""
        try:
            with db_config.get_session() as session:
                repo = ProductRepository(session)
                product = repo.get_by_barcode(barcode)
                return self._product_to_dict(product) if product else None
        except Exception as e:
            logger.error(f"根据条码获取产品失败: {e}")
            raise
    
    @cache_invalidate("product:*")
    def create_product(self, product_data: Dict[str, Any], operator: str) -> Dict[str, Any]:
        """创建新产品"""
        try:
            with db_config.get_session() as session:
                repo = ProductRepository(session)
                
                # 检查产品名称是否已存在
                existing = repo.find_one_by(product_name=product_data['product_name'])
                if existing:
                    raise ValueError(f"产品名称已存在: {product_data['product_name']}")
                
                # 检查条码是否已存在
                if product_data.get('barcode'):
                    existing_barcode = repo.get_by_barcode(product_data['barcode'])
                    if existing_barcode:
                        raise ValueError(f"条码已存在: {product_data['barcode']}")
                
                # 创建产品
                product = repo.create(**product_data)
                
                # 如果有初始库存，记录库存历史
                if product.current_stock > 0:
                    repo.adjust_stock(
                        product_id=product.id,
                        quantity_change=product.current_stock,
                        action='initial_stock',
                        operator=operator,
                        note='新产品初始库存'
                    )
                
                session.commit()
                return self._product_to_dict(product)
                
        except Exception as e:
            logger.error(f"创建产品失败: {e}")
            raise
    
    @cache_invalidate("product:*")
    def update_product(self, product_id: int, product_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """更新产品信息"""
        try:
            with db_config.get_session() as session:
                repo = ProductRepository(session)
                
                # 检查产品是否存在
                existing = repo.get_by_id(product_id)
                if not existing:
                    return None
                
                # 检查产品名称冲突
                if 'product_name' in product_data:
                    name_conflict = repo.find_one_by(product_name=product_data['product_name'])
                    if name_conflict and name_conflict.id != product_id:
                        raise ValueError(f"产品名称已存在: {product_data['product_name']}")
                
                # 检查条码冲突
                if 'barcode' in product_data and product_data['barcode']:
                    barcode_conflict = repo.get_by_barcode(product_data['barcode'])
                    if barcode_conflict and barcode_conflict.id != product_id:
                        raise ValueError(f"条码已存在: {product_data['barcode']}")
                
                # 更新产品
                product = repo.update(product_id, **product_data)
                session.commit()
                return self._product_to_dict(product)
                
        except Exception as e:
            logger.error(f"更新产品失败: {e}")
            raise
    
    def delete_product(self, product_id: int) -> bool:
        """删除产品（软删除）"""
        try:
            with db_config.get_session() as session:
                repo = ProductRepository(session)
                success = repo.update(product_id, status='deleted')
                session.commit()
                return success is not None
        except Exception as e:
            logger.error(f"删除产品失败: {e}")
            raise
    
    def update_stock(self, product_id: int, new_stock: int, operator: str, note: str = None) -> bool:
        """更新产品库存"""
        try:
            with db_config.get_session() as session:
                repo = ProductRepository(session)
                success = repo.update_stock(product_id, new_stock, operator, note)
                session.commit()
                # 清除相关缓存
                if success:
                    invalidate_product_cache(product_id)
                return success
        except Exception as e:
            logger.error(f"更新库存失败: {e}")
            raise
    
    def adjust_stock(self, product_id: int, quantity_change: int, 
                    action: str, operator: str, note: str = None) -> bool:
        """调整库存（增加或减少）"""
        try:
            with db_config.get_session() as session:
                repo = ProductRepository(session)
                success = repo.adjust_stock(product_id, quantity_change, action, operator, note)
                session.commit()
                # 清除相关缓存
                if success:
                    invalidate_product_cache(product_id)
                return success
        except Exception as e:
            logger.error(f"调整库存失败: {e}")
            raise
    
    @cached(prefix="stock:history", timeout=600)
    def get_stock_history(self, product_id: int, limit: int = 50) -> List[Dict[str, Any]]:
        """获取库存历史"""
        try:
            with db_config.get_session() as session:
                repo = ProductRepository(session)
                history = repo.get_stock_history(product_id, limit)
                return [
                    {
                        'id': h.id,
                        'action': h.action,
                        'quantity_change': h.quantity_change,
                        'quantity_before': h.quantity_before,
                        'quantity_after': h.quantity_after,
                        'operator': h.operator,
                        'note': h.note,
                        'timestamp': h.timestamp.isoformat()
                    }
                    for h in history
                ]
        except Exception as e:
            logger.error(f"获取库存历史失败: {e}")
            raise
    
    @cached(prefix="product:categories", timeout=600)
    def get_categories(self) -> List[Dict[str, Any]]:
        """获取所有产品分类"""
        try:
            with db_config.get_session() as session:
                repo = ProductRepository(session)
                return repo.get_categories()
        except Exception as e:
            logger.error(f"获取分类失败: {e}")
            raise
    
    @cached(prefix="product:storage_areas", timeout=600)
    def get_storage_areas(self) -> List[Dict[str, Any]]:
        """获取所有存储区域"""
        try:
            with db_config.get_session() as session:
                repo = ProductRepository(session)
                return repo.get_storage_areas()
        except Exception as e:
            logger.error(f"获取存储区域失败: {e}")
            raise
    
    @cached(prefix="product:low_stock", timeout=300)
    def get_low_stock_products(self, threshold_multiplier: float = 1.0) -> List[Dict[str, Any]]:
        """获取低库存产品"""
        try:
            with db_config.get_session() as session:
                repo = ProductRepository(session)
                products = repo.get_low_stock_products(threshold_multiplier)
                return [self._product_to_dict(p) for p in products]
        except Exception as e:
            logger.error(f"获取低库存产品失败: {e}")
            raise
    
    @cached(prefix="product:statistics", timeout=300)
    def get_product_statistics(self) -> Dict[str, Any]:
        """获取产品统计信息"""
        try:
            with db_config.get_session() as session:
                repo = ProductRepository(session)
                return repo.get_product_statistics()
        except Exception as e:
            logger.error(f"获取产品统计失败: {e}")
            raise
    
    def batch_update_category(self, product_ids: List[int], new_category: str) -> int:
        """批量更新产品分类"""
        try:
            with db_config.get_session() as session:
                repo = ProductRepository(session)
                count = repo.batch_update_category(product_ids, new_category)
                session.commit()
                return count
        except Exception as e:
            logger.error(f"批量更新分类失败: {e}")
            raise
    
    def batch_update_storage_area(self, product_ids: List[int], new_storage_area: str) -> int:
        """批量更新存储区域"""
        try:
            with db_config.get_session() as session:
                repo = ProductRepository(session)
                count = repo.batch_update_storage_area(product_ids, new_storage_area)
                session.commit()
                return count
        except Exception as e:
            logger.error(f"批量更新存储区域失败: {e}")
            raise
    
    def _product_to_dict(self, product: Product) -> Dict[str, Any]:
        """将产品模型转换为字典"""
        if not product:
            return None
        
        return product.to_dict()


# 全局产品服务实例
product_service_enhanced = ProductServiceEnhanced()