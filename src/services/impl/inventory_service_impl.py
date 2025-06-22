# -*- coding: utf-8 -*-
"""
库存服务实现
"""
import logging
from typing import Dict, Any, Optional, List
from ...core.interfaces import IInventoryService, PaginationParams, PaginationResult
from ...core.exceptions import NotFoundError, ValidationError
from ...database.database_config import db_config
from ...repositories.product_repository import ProductRepository
from ...services.cache_service import cached, invalidate_product_cache

logger = logging.getLogger(__name__)


class InventoryServiceImpl(IInventoryService):
    """库存服务实现"""
    
    def __init__(self):
        self.cache_timeout = 300  # 5分钟缓存
    
    @cached(prefix="inventory:stock", timeout=300)
    def get_stock(self, product_id: int) -> Optional[Dict[str, Any]]:
        """获取库存信息"""
        try:
            with db_config.get_session() as session:
                repo = ProductRepository(session)
                product = repo.get_by_id(product_id)
                
                if not product:
                    return None
                
                return {
                    'product_id': product.id,
                    'product_name': product.product_name,
                    'current_stock': product.current_stock,
                    'min_stock_warning': product.min_stock_warning,
                    'is_low_stock': product.current_stock <= product.min_stock_warning,
                    'unit': product.unit,
                    'category': product.category,
                    'storage_area': product.storage_area,
                    'updated_at': product.updated_at.isoformat() if product.updated_at else None
                }
                
        except Exception as e:
            logger.error(f"获取库存信息失败 {product_id}: {e}")
            raise
    
    def update_stock(self, product_id: int, new_stock: int, operator: str, note: str = None) -> bool:
        """更新库存"""
        try:
            # 数据验证
            if new_stock < 0:
                raise ValidationError("库存数量不能为负数", field="new_stock", value=new_stock)
            
            with db_config.get_session() as session:
                repo = ProductRepository(session)
                
                # 检查产品是否存在
                product = repo.get_by_id(product_id)
                if not product:
                    raise NotFoundError("产品不存在", resource_type="产品", resource_id=product_id)
                
                # 更新库存
                success = repo.update_stock(product_id, new_stock, operator, note)
                session.commit()
                
                if success:
                    # 清除相关缓存
                    invalidate_product_cache(product_id)
                    
                    logger.info(f"更新库存成功 {product_id}: {product.current_stock} -> {new_stock} by {operator}")
                    return True
                
                return False
                
        except Exception as e:
            logger.error(f"更新库存失败 {product_id}: {e}")
            raise
    
    def adjust_stock(self, product_id: int, quantity_change: int, action: str, operator: str, note: str = None) -> bool:
        """调整库存"""
        try:
            # 数据验证
            if quantity_change == 0:
                raise ValidationError("调整数量不能为0", field="quantity_change", value=quantity_change)
            
            # 验证操作类型
            valid_actions = ['add', 'remove', 'adjust', 'count', 'loss', 'return']
            if action not in valid_actions:
                raise ValidationError(f"无效的操作类型: {action}", field="action", value=action)
            
            with db_config.get_session() as session:
                repo = ProductRepository(session)
                
                # 检查产品是否存在
                product = repo.get_by_id(product_id)
                if not product:
                    raise NotFoundError("产品不存在", resource_type="产品", resource_id=product_id)
                
                # 检查调整后库存是否为负数
                new_stock = product.current_stock + quantity_change
                if new_stock < 0:
                    raise ValidationError(
                        f"调整后库存不能为负数 (当前: {product.current_stock}, 调整: {quantity_change})",
                        field="quantity_change",
                        value=quantity_change
                    )
                
                # 调整库存
                success = repo.adjust_stock(product_id, quantity_change, action, operator, note)
                session.commit()
                
                if success:
                    # 清除相关缓存
                    invalidate_product_cache(product_id)
                    
                    logger.info(f"调整库存成功 {product_id}: {action} {quantity_change} by {operator}")
                    return True
                
                return False
                
        except Exception as e:
            logger.error(f"调整库存失败 {product_id}: {e}")
            raise
    
    @cached(prefix="inventory:history", timeout=600)
    def get_stock_history(self, product_id: int, pagination: PaginationParams) -> PaginationResult:
        """获取库存历史"""
        try:
            with db_config.get_session() as session:
                repo = ProductRepository(session)
                
                # 检查产品是否存在
                product = repo.get_by_id(product_id)
                if not product:
                    raise NotFoundError("产品不存在", resource_type="产品", resource_id=product_id)
                
                # 获取库存历史
                history = repo.get_stock_history(product_id, limit=pagination.per_page * 10)  # 获取更多数据用于分页
                
                # 手动分页
                total = len(history)
                start = pagination.offset
                end = start + pagination.per_page
                page_items = history[start:end]
                
                # 转换为字典格式
                items = []
                for record in page_items:
                    items.append({
                        'id': record.id,
                        'action': record.action,
                        'quantity_change': record.quantity_change,
                        'quantity_before': record.quantity_before,
                        'quantity_after': record.quantity_after,
                        'operator': record.operator,
                        'note': record.note,
                        'timestamp': record.timestamp.isoformat()
                    })
                
                return PaginationResult(
                    items=items,
                    total=total,
                    page=pagination.page,
                    per_page=pagination.per_page
                )
                
        except Exception as e:
            logger.error(f"获取库存历史失败 {product_id}: {e}")
            raise
    
    @cached(prefix="inventory:low_stock", timeout=300)
    def get_low_stock_products(self, threshold_multiplier: float = 1.0) -> List[Dict[str, Any]]:
        """获取低库存产品"""
        try:
            # 数据验证
            if threshold_multiplier <= 0:
                raise ValidationError("阈值倍数必须大于0", field="threshold_multiplier", value=threshold_multiplier)
            
            with db_config.get_session() as session:
                repo = ProductRepository(session)
                products = repo.get_low_stock_products(threshold_multiplier)
                
                result = []
                for product in products:
                    stock_ratio = product.current_stock / product.min_stock_warning if product.min_stock_warning > 0 else 0
                    urgency_level = 'critical' if stock_ratio <= 0.5 else 'warning' if stock_ratio <= 1.0 else 'low'
                    
                    result.append({
                        'product_id': product.id,
                        'product_name': product.product_name,
                        'current_stock': product.current_stock,
                        'min_stock_warning': product.min_stock_warning,
                        'stock_ratio': round(stock_ratio, 2),
                        'urgency_level': urgency_level,
                        'category': product.category,
                        'storage_area': product.storage_area,
                        'unit': product.unit,
                        'shortage': max(0, product.min_stock_warning - product.current_stock)
                    })
                
                # 按紧急程度排序
                urgency_order = {'critical': 0, 'warning': 1, 'low': 2}
                result.sort(key=lambda x: (urgency_order.get(x['urgency_level'], 3), x['stock_ratio']))
                
                return result
                
        except Exception as e:
            logger.error(f"获取低库存产品失败: {e}")
            raise
    
    def get_stock_statistics(self) -> Dict[str, Any]:
        """获取库存统计信息"""
        try:
            with db_config.get_session() as session:
                repo = ProductRepository(session)
                stats = repo.get_product_statistics()
                
                # 获取低库存产品数量（不同紧急级别）
                low_stock_products = self.get_low_stock_products()
                
                critical_count = len([p for p in low_stock_products if p['urgency_level'] == 'critical'])
                warning_count = len([p for p in low_stock_products if p['urgency_level'] == 'warning'])
                low_count = len([p for p in low_stock_products if p['urgency_level'] == 'low'])
                
                return {
                    **stats,
                    'low_stock_breakdown': {
                        'critical': critical_count,
                        'warning': warning_count,
                        'low': low_count,
                        'total': len(low_stock_products)
                    },
                    'stock_health_score': self._calculate_stock_health_score(stats, low_stock_products)
                }
                
        except Exception as e:
            logger.error(f"获取库存统计失败: {e}")
            raise
    
    def _calculate_stock_health_score(self, stats: Dict[str, Any], low_stock_products: List[Dict[str, Any]]) -> int:
        """计算库存健康评分（0-100）"""
        try:
            total_products = stats.get('total_products', 0)
            if total_products == 0:
                return 100
            
            # 计算各级别低库存比例
            critical_ratio = len([p for p in low_stock_products if p['urgency_level'] == 'critical']) / total_products
            warning_ratio = len([p for p in low_stock_products if p['urgency_level'] == 'warning']) / total_products
            low_ratio = len([p for p in low_stock_products if p['urgency_level'] == 'low']) / total_products
            
            # 计算健康评分
            score = 100
            score -= critical_ratio * 50  # 严重缺货扣50分
            score -= warning_ratio * 30   # 警告级别扣30分
            score -= low_ratio * 15       # 低库存扣15分
            
            return max(0, min(100, int(score)))
            
        except Exception as e:
            logger.error(f"计算库存健康评分失败: {e}")
            return 50  # 默认中等评分
    
    def batch_update_stock(self, updates: List[Dict[str, Any]], operator: str) -> Dict[str, Any]:
        """批量更新库存"""
        try:
            results = {
                'success_count': 0,
                'failed_count': 0,
                'errors': []
            }
            
            with db_config.get_session() as session:
                repo = ProductRepository(session)
                
                for update in updates:
                    try:
                        product_id = update.get('product_id')
                        new_stock = update.get('new_stock')
                        note = update.get('note', '批量更新')
                        
                        if not product_id or new_stock is None:
                            results['errors'].append({
                                'product_id': product_id,
                                'error': '缺少必要参数'
                            })
                            results['failed_count'] += 1
                            continue
                        
                        success = repo.update_stock(product_id, new_stock, operator, note)
                        if success:
                            results['success_count'] += 1
                        else:
                            results['errors'].append({
                                'product_id': product_id,
                                'error': '更新失败'
                            })
                            results['failed_count'] += 1
                            
                    except Exception as e:
                        results['errors'].append({
                            'product_id': update.get('product_id'),
                            'error': str(e)
                        })
                        results['failed_count'] += 1
                
                session.commit()
                
                # 清除所有产品缓存
                invalidate_product_cache()
                
                logger.info(f"批量更新库存完成: 成功 {results['success_count']}, 失败 {results['failed_count']}")
                return results
                
        except Exception as e:
            logger.error(f"批量更新库存失败: {e}")
            raise