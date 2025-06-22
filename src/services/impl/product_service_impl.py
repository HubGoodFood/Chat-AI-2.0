# -*- coding: utf-8 -*-
"""
产品服务实现
"""
import logging
from typing import Dict, Any, Optional
from ...core.interfaces import IProductService, PaginationParams, PaginationResult
from ...core.exceptions import NotFoundError, ConflictError, ValidationError
from ...database.database_config import db_config
from ...repositories.product_repository import ProductRepository
from ...services.cache_service import cached, invalidate_product_cache
from ...services.search_service import search_service

logger = logging.getLogger(__name__)


class ProductServiceImpl(IProductService):
    """产品服务实现"""
    
    def __init__(self):
        self.cache_timeout = 600  # 10分钟缓存
    
    @cached(prefix="product:detail", timeout=600)
    def get_product(self, product_id: int) -> Optional[Dict[str, Any]]:
        """获取产品详情"""
        try:
            with db_config.get_session() as session:
                repo = ProductRepository(session)
                product = repo.get_by_id(product_id)
                
                if not product:
                    return None
                
                return product.to_dict()
                
        except Exception as e:
            logger.error(f"获取产品详情失败 {product_id}: {e}")
            raise
    
    @cached(prefix="product:barcode", timeout=600)
    def get_product_by_barcode(self, barcode: str) -> Optional[Dict[str, Any]]:
        """根据条码获取产品"""
        if not barcode or not barcode.strip():
            raise ValidationError("条码不能为空", field="barcode")
        
        try:
            with db_config.get_session() as session:
                repo = ProductRepository(session)
                product = repo.get_by_barcode(barcode.strip())
                
                if not product:
                    return None
                
                return product.to_dict()
                
        except Exception as e:
            logger.error(f"根据条码获取产品失败 {barcode}: {e}")
            raise
    
    def search_products(self, query: str = None, **filters) -> PaginationResult:
        """搜索产品"""
        try:
            # 从filters中提取分页参数
            pagination = PaginationParams(
                page=filters.pop('page', 1),
                per_page=filters.pop('per_page', 20)
            )
            
            # 使用增强搜索服务
            if query:
                result = search_service.search_products_advanced(
                    query=query,
                    category=filters.get('category'),
                    storage_area=filters.get('storage_area'),
                    price_range=filters.get('price_range'),
                    stock_range=filters.get('stock_range'),
                    sort_by=filters.get('sort_by', 'relevance'),
                    page=pagination.page,
                    per_page=pagination.per_page
                )
                
                return PaginationResult(
                    items=result['products'],
                    total=result['total'],
                    page=result['page'],
                    per_page=result['per_page']
                )
            else:
                # 无搜索词时使用数据库查询
                with db_config.get_session() as session:
                    repo = ProductRepository(session)
                    
                    # 构建查询过滤器
                    query_filters = {'status': 'active'}
                    if filters.get('category'):
                        query_filters['category'] = filters['category']
                    if filters.get('storage_area'):
                        query_filters['storage_area'] = filters['storage_area']
                    
                    # 分页查询
                    result = repo.paginate(
                        page=pagination.page,
                        per_page=pagination.per_page,
                        **query_filters
                    )
                    
                    return PaginationResult(
                        items=[item.to_dict() for item in result['items']],
                        total=result['total'],
                        page=result['page'],
                        per_page=result['per_page']
                    )
                    
        except Exception as e:
            logger.error(f"搜索产品失败: {e}")
            raise
    
    def create_product(self, product_data: Dict[str, Any], operator: str) -> int:
        """创建产品"""
        try:
            # 数据验证
            self._validate_product_data(product_data)
            
            with db_config.get_session() as session:
                repo = ProductRepository(session)
                
                # 检查产品名称是否已存在
                existing = repo.find_one_by(product_name=product_data['product_name'])
                if existing:
                    raise ConflictError(
                        f"产品名称已存在: {product_data['product_name']}",
                        conflicting_field="product_name"
                    )
                
                # 检查条码是否已存在
                if product_data.get('barcode'):
                    existing_barcode = repo.get_by_barcode(product_data['barcode'])
                    if existing_barcode:
                        raise ConflictError(
                            f"条码已存在: {product_data['barcode']}",
                            conflicting_field="barcode"
                        )
                
                # 设置默认值
                product_data.setdefault('status', 'active')
                product_data.setdefault('current_stock', 0)
                product_data.setdefault('min_stock_warning', 10)
                
                # 创建产品
                product = repo.create(**product_data)
                session.commit()
                
                # 生成条码（如果没有提供）
                if not product_data.get('barcode'):
                    self._generate_barcode(product.id, product_data['product_name'])
                
                # 索引到搜索引擎
                search_service.index_product(product.to_dict())
                
                # 清除相关缓存
                invalidate_product_cache()
                
                logger.info(f"创建产品成功 {product.id}: {product_data['product_name']} by {operator}")
                return product.id
                
        except Exception as e:
            logger.error(f"创建产品失败: {e}")
            raise
    
    def update_product(self, product_id: int, product_data: Dict[str, Any], operator: str) -> bool:
        """更新产品"""
        try:
            # 数据验证
            self._validate_product_data(product_data, is_update=True)
            
            with db_config.get_session() as session:
                repo = ProductRepository(session)
                
                # 检查产品是否存在
                existing = repo.get_by_id(product_id)
                if not existing:
                    raise NotFoundError("产品不存在", resource_type="产品", resource_id=product_id)
                
                # 检查产品名称冲突
                if 'product_name' in product_data:
                    name_conflict = repo.find_one_by(product_name=product_data['product_name'])
                    if name_conflict and name_conflict.id != product_id:
                        raise ConflictError(
                            f"产品名称已存在: {product_data['product_name']}",
                            conflicting_field="product_name"
                        )
                
                # 检查条码冲突
                if 'barcode' in product_data and product_data['barcode']:
                    barcode_conflict = repo.get_by_barcode(product_data['barcode'])
                    if barcode_conflict and barcode_conflict.id != product_id:
                        raise ConflictError(
                            f"条码已存在: {product_data['barcode']}",
                            conflicting_field="barcode"
                        )
                
                # 更新产品
                updated_product = repo.update(product_id, **product_data)
                session.commit()
                
                if updated_product:
                    # 更新搜索索引
                    search_service.index_product(updated_product.to_dict())
                    
                    # 清除相关缓存
                    invalidate_product_cache(product_id)
                    
                    logger.info(f"更新产品成功 {product_id} by {operator}")
                    return True
                
                return False
                
        except Exception as e:
            logger.error(f"更新产品失败 {product_id}: {e}")
            raise
    
    def delete_product(self, product_id: int, operator: str) -> bool:
        """删除产品（软删除）"""
        try:
            with db_config.get_session() as session:
                repo = ProductRepository(session)
                
                # 检查产品是否存在
                existing = repo.get_by_id(product_id)
                if not existing:
                    raise NotFoundError("产品不存在", resource_type="产品", resource_id=product_id)
                
                # 软删除
                success = repo.update(product_id, status='deleted')
                session.commit()
                
                if success:
                    # 从搜索索引中移除
                    search_service.remove_product(product_id)
                    
                    # 清除相关缓存
                    invalidate_product_cache(product_id)
                    
                    logger.info(f"删除产品成功 {product_id} by {operator}")
                    return True
                
                return False
                
        except Exception as e:
            logger.error(f"删除产品失败 {product_id}: {e}")
            raise
    
    @cached(prefix="product:categories", timeout=600)
    def get_categories(self) -> list:
        """获取产品分类"""
        try:
            with db_config.get_session() as session:
                repo = ProductRepository(session)
                return repo.get_categories()
                
        except Exception as e:
            logger.error(f"获取产品分类失败: {e}")
            raise
    
    def _validate_product_data(self, product_data: Dict[str, Any], is_update: bool = False):
        """验证产品数据"""
        if not is_update:
            # 创建时必须有产品名称
            if not product_data.get('product_name'):
                raise ValidationError("产品名称不能为空", field="product_name")
        
        # 验证产品名称长度
        if 'product_name' in product_data:
            name = product_data['product_name'].strip()
            if not name:
                raise ValidationError("产品名称不能为空", field="product_name")
            if len(name) > 100:
                raise ValidationError("产品名称长度不能超过100个字符", field="product_name")
            product_data['product_name'] = name
        
        # 验证价格
        if 'price' in product_data:
            try:
                price = float(product_data['price'])
                if price < 0:
                    raise ValidationError("价格不能为负数", field="price", value=price)
                product_data['price'] = price
            except (ValueError, TypeError):
                raise ValidationError("价格格式不正确", field="price", value=product_data['price'])
        
        # 验证库存
        if 'current_stock' in product_data:
            try:
                stock = int(product_data['current_stock'])
                if stock < 0:
                    raise ValidationError("库存不能为负数", field="current_stock", value=stock)
                product_data['current_stock'] = stock
            except (ValueError, TypeError):
                raise ValidationError("库存格式不正确", field="current_stock", value=product_data['current_stock'])
        
        # 验证最低库存警告
        if 'min_stock_warning' in product_data:
            try:
                warning = int(product_data['min_stock_warning'])
                if warning < 0:
                    raise ValidationError("最低库存警告不能为负数", field="min_stock_warning", value=warning)
                product_data['min_stock_warning'] = warning
            except (ValueError, TypeError):
                raise ValidationError("最低库存警告格式不正确", field="min_stock_warning", value=product_data['min_stock_warning'])
        
        # 验证分类
        if 'category' in product_data and product_data['category']:
            category = product_data['category'].strip()
            if len(category) > 50:
                raise ValidationError("分类名称长度不能超过50个字符", field="category")
            product_data['category'] = category
        
        # 验证单位
        if 'unit' in product_data and product_data['unit']:
            unit = product_data['unit'].strip()
            if len(unit) > 20:
                raise ValidationError("单位长度不能超过20个字符", field="unit")
            product_data['unit'] = unit
    
    def _generate_barcode(self, product_id: int, product_name: str):
        """生成条码"""
        try:
            # 简单的条码生成逻辑：88 + 产品ID（补0到10位）
            barcode = f"88{product_id:010d}"
            
            with db_config.get_session() as session:
                repo = ProductRepository(session)
                repo.update(product_id, barcode=barcode)
                session.commit()
                
            logger.info(f"为产品 {product_id} 生成条码: {barcode}")
            
        except Exception as e:
            logger.error(f"生成条码失败 {product_id}: {e}")
            # 条码生成失败不影响产品创建