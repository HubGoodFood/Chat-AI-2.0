# -*- coding: utf-8 -*-
"""
产品仓库实现
"""
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func, desc, asc
from .base_repository import BaseRepository
from ..database.models import Product, StockHistory
import logging

logger = logging.getLogger(__name__)


class ProductRepository(BaseRepository[Product]):
    """产品仓库"""
    
    def __init__(self, session: Session):
        super().__init__(session, Product)
    
    def search_products(self, 
                       query: str = None,
                       category: str = None,
                       storage_area: str = None,
                       status: str = 'active',
                       low_stock_only: bool = False,
                       limit: int = 50,
                       offset: int = 0) -> List[Product]:
        """搜索产品"""
        try:
            db_query = self.session.query(Product)
            
            # 状态过滤
            if status:
                db_query = db_query.filter(Product.status == status)
            
            # 分类过滤
            if category:
                db_query = db_query.filter(Product.category == category)
            
            # 存储区域过滤
            if storage_area:
                db_query = db_query.filter(Product.storage_area == storage_area)
            
            # 低库存过滤
            if low_stock_only:
                db_query = db_query.filter(Product.current_stock <= Product.min_stock_warning)
            
            # 文本搜索
            if query and query.strip():
                search_filter = or_(
                    Product.product_name.like(f"%{query}%"),
                    Product.keywords.like(f"%{query}%"),
                    Product.description.like(f"%{query}%"),
                    Product.barcode.like(f"%{query}%")
                )
                db_query = db_query.filter(search_filter)
            
            # 排序和分页
            db_query = db_query.order_by(Product.product_name)
            if offset:
                db_query = db_query.offset(offset)
            if limit:
                db_query = db_query.limit(limit)
            
            return db_query.all()
            
        except Exception as e:
            logger.error(f"搜索产品失败: {e}")
            raise
    
    def get_by_barcode(self, barcode: str) -> Optional[Product]:
        """根据条码获取产品"""
        try:
            return self.session.query(Product).filter(Product.barcode == barcode).first()
        except Exception as e:
            logger.error(f"根据条码查询产品失败: {e}")
            raise
    
    def get_by_category(self, category: str) -> List[Product]:
        """获取指定分类的产品"""
        try:
            return self.session.query(Product).filter(
                and_(Product.category == category, Product.status == 'active')
            ).order_by(Product.product_name).all()
        except Exception as e:
            logger.error(f"获取分类产品失败: {e}")
            raise
    
    def get_low_stock_products(self, threshold_multiplier: float = 1.0) -> List[Product]:
        """获取低库存产品"""
        try:
            return self.session.query(Product).filter(
                and_(
                    Product.current_stock <= Product.min_stock_warning * threshold_multiplier,
                    Product.status == 'active'
                )
            ).order_by(desc(Product.min_stock_warning - Product.current_stock)).all()
        except Exception as e:
            logger.error(f"获取低库存产品失败: {e}")
            raise
    
    def get_categories(self) -> List[Dict[str, Any]]:
        """获取所有产品分类统计"""
        try:
            result = self.session.query(
                Product.category,
                func.count(Product.id).label('count'),
                func.sum(Product.current_stock).label('total_stock')
            ).filter(Product.status == 'active').group_by(Product.category).all()
            
            return [
                {
                    'category': row.category,
                    'count': row.count,
                    'total_stock': row.total_stock or 0
                }
                for row in result
            ]
        except Exception as e:
            logger.error(f"获取分类统计失败: {e}")
            raise
    
    def get_storage_areas(self) -> List[Dict[str, Any]]:
        """获取存储区域统计"""
        try:
            result = self.session.query(
                Product.storage_area,
                func.count(Product.id).label('count'),
                func.sum(Product.current_stock).label('total_stock')
            ).filter(Product.status == 'active').group_by(Product.storage_area).all()
            
            return [
                {
                    'storage_area': row.storage_area,
                    'count': row.count,
                    'total_stock': row.total_stock or 0
                }
                for row in result
            ]
        except Exception as e:
            logger.error(f"获取存储区域统计失败: {e}")
            raise
    
    def update_stock(self, product_id: int, new_stock: int, operator: str, note: str = None) -> bool:
        """更新库存并记录历史"""
        try:
            product = self.get_by_id(product_id)
            if not product:
                return False
            
            old_stock = product.current_stock
            product.current_stock = new_stock
            
            # 记录库存历史
            stock_history = StockHistory(
                product_id=product_id,
                action='manual_update',
                quantity_change=new_stock - old_stock,
                quantity_before=old_stock,
                quantity_after=new_stock,
                operator=operator,
                note=note
            )
            self.session.add(stock_history)
            self.session.flush()
            
            return True
        except Exception as e:
            logger.error(f"更新库存失败: {e}")
            raise
    
    def adjust_stock(self, product_id: int, quantity_change: int, 
                    action: str, operator: str, note: str = None) -> bool:
        """调整库存（增加或减少）"""
        try:
            product = self.get_by_id(product_id)
            if not product:
                return False
            
            old_stock = product.current_stock
            new_stock = max(0, old_stock + quantity_change)
            product.current_stock = new_stock
            
            # 记录库存历史
            stock_history = StockHistory(
                product_id=product_id,
                action=action,
                quantity_change=quantity_change,
                quantity_before=old_stock,
                quantity_after=new_stock,
                operator=operator,
                note=note
            )
            self.session.add(stock_history)
            self.session.flush()
            
            return True
        except Exception as e:
            logger.error(f"调整库存失败: {e}")
            raise
    
    def get_stock_history(self, product_id: int, limit: int = 50) -> List[StockHistory]:
        """获取产品库存历史"""
        try:
            return self.session.query(StockHistory).filter(
                StockHistory.product_id == product_id
            ).order_by(desc(StockHistory.timestamp)).limit(limit).all()
        except Exception as e:
            logger.error(f"获取库存历史失败: {e}")
            raise
    
    def batch_update_category(self, product_ids: List[int], new_category: str) -> int:
        """批量更新产品分类"""
        try:
            count = self.session.query(Product).filter(
                Product.id.in_(product_ids)
            ).update({'category': new_category}, synchronize_session=False)
            self.session.flush()
            return count
        except Exception as e:
            logger.error(f"批量更新分类失败: {e}")
            raise
    
    def batch_update_storage_area(self, product_ids: List[int], new_storage_area: str) -> int:
        """批量更新存储区域"""
        try:
            count = self.session.query(Product).filter(
                Product.id.in_(product_ids)
            ).update({'storage_area': new_storage_area}, synchronize_session=False)
            self.session.flush()
            return count
        except Exception as e:
            logger.error(f"批量更新存储区域失败: {e}")
            raise
    
    def get_product_statistics(self) -> Dict[str, Any]:
        """获取产品统计信息"""
        try:
            total_products = self.session.query(func.count(Product.id)).filter(
                Product.status == 'active'
            ).scalar()
            
            total_stock = self.session.query(func.sum(Product.current_stock)).filter(
                Product.status == 'active'
            ).scalar() or 0
            
            low_stock_count = self.session.query(func.count(Product.id)).filter(
                and_(
                    Product.current_stock <= Product.min_stock_warning,
                    Product.status == 'active'
                )
            ).scalar()
            
            categories_count = self.session.query(func.count(func.distinct(Product.category))).filter(
                Product.status == 'active'
            ).scalar()
            
            return {
                'total_products': total_products,
                'total_stock': total_stock,
                'low_stock_count': low_stock_count,
                'categories_count': categories_count,
                'average_stock': total_stock / total_products if total_products > 0 else 0
            }
        except Exception as e:
            logger.error(f"获取产品统计失败: {e}")
            raise