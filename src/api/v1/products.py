# -*- coding: utf-8 -*-
"""
产品API控制器 v1
"""
import logging
from flask import Blueprint, request, g
from ...core.service_registry import get_product_service
from ...core.response import ResponseBuilder, ResponseHelper
from ...core.exceptions import ValidationError, NotFoundError
from ...core.interfaces import PaginationParams
from ..version_control import api_version
from ...utils.validators import validate_json, ProductCreateRequest, ProductUpdateRequest, ProductSearchRequest

logger = logging.getLogger(__name__)

products_bp = Blueprint('products', __name__)


@products_bp.route('', methods=['GET'])
@api_version()
def search_products():
    """搜索产品"""
    try:
        # 解析查询参数
        query = request.args.get('q', '').strip()
        category = request.args.get('category', '').strip() or None
        storage_area = request.args.get('storage_area', '').strip() or None
        sort_by = request.args.get('sort_by', 'relevance')
        
        # 价格范围
        min_price = request.args.get('min_price')
        max_price = request.args.get('max_price')
        price_range = None
        if min_price is not None or max_price is not None:
            price_range = (
                float(min_price) if min_price else None,
                float(max_price) if max_price else None
            )
        
        # 库存范围
        min_stock = request.args.get('min_stock')
        max_stock = request.args.get('max_stock')
        stock_range = None
        if min_stock is not None or max_stock is not None:
            stock_range = (
                int(min_stock) if min_stock else None,
                int(max_stock) if max_stock else None
            )
        
        # 分页参数
        page = int(request.args.get('page', 1))
        per_page = min(int(request.args.get('per_page', 20)), 100)
        
        # 调用服务
        product_service = get_product_service()
        result = product_service.search_products(
            query=query if query else None,
            category=category,
            storage_area=storage_area,
            price_range=price_range,
            stock_range=stock_range,
            sort_by=sort_by,
            page=page,
            per_page=per_page
        )
        
        response = ResponseBuilder.paginated(
            items=result.items,
            page=result.page,
            per_page=result.per_page,
            total=result.total
        )
        
        # 添加搜索元数据
        response.set_meta('search_query', query)
        response.set_meta('filters', {
            'category': category,
            'storage_area': storage_area,
            'price_range': price_range,
            'stock_range': stock_range,
            'sort_by': sort_by
        })
        
        return response.to_json_response()
        
    except (ValueError, TypeError) as e:
        logger.warning(f"搜索产品参数错误: {e}")
        return ResponseHelper.handle_exception(ValidationError(f"参数格式错误: {e}"))
    except Exception as e:
        logger.error(f"搜索产品失败: {e}")
        return ResponseHelper.handle_exception(e)


@products_bp.route('/<int:product_id>', methods=['GET'])
@api_version()
def get_product(product_id: int):
    """获取产品详情"""
    try:
        product_service = get_product_service()
        product = product_service.get_product(product_id)
        
        if not product:
            raise NotFoundError("产品不存在", resource_type="产品", resource_id=product_id)
        
        response = ResponseBuilder.success(data=product)
        return response.to_json_response()
        
    except Exception as e:
        logger.error(f"获取产品详情失败 {product_id}: {e}")
        return ResponseHelper.handle_exception(e)


@products_bp.route('/barcode/<barcode>', methods=['GET'])
@api_version()
def get_product_by_barcode(barcode: str):
    """根据条码获取产品"""
    try:
        product_service = get_product_service()
        product = product_service.get_product_by_barcode(barcode)
        
        if not product:
            raise NotFoundError("产品不存在", resource_type="产品")
        
        response = ResponseBuilder.success(data=product)
        return response.to_json_response()
        
    except Exception as e:
        logger.error(f"根据条码获取产品失败 {barcode}: {e}")
        return ResponseHelper.handle_exception(e)


@products_bp.route('', methods=['POST'])
@api_version()
@validate_json(ProductCreateRequest)
def create_product():
    """创建产品"""
    try:
        data = request.get_json()
        operator = getattr(g, 'current_user', {}).get('username', 'system')
        
        product_service = get_product_service()
        product_id = product_service.create_product(data, operator)
        
        # 获取创建的产品详情
        product = product_service.get_product(product_id)
        
        response = ResponseBuilder.success(
            data=product,
            message="产品创建成功"
        )
        response.set_meta('product_id', product_id)
        
        return response.to_json_response(201)
        
    except Exception as e:
        logger.error(f"创建产品失败: {e}")
        return ResponseHelper.handle_exception(e)


@products_bp.route('/<int:product_id>', methods=['PUT'])
@api_version()
@validate_json(ProductUpdateRequest)
def update_product(product_id: int):
    """更新产品"""
    try:
        data = request.get_json()
        operator = getattr(g, 'current_user', {}).get('username', 'system')
        
        product_service = get_product_service()
        success = product_service.update_product(product_id, data, operator)
        
        if not success:
            raise NotFoundError("产品不存在", resource_type="产品", resource_id=product_id)
        
        # 获取更新后的产品详情
        product = product_service.get_product(product_id)
        
        response = ResponseBuilder.success(
            data=product,
            message="产品更新成功"
        )
        
        return response.to_json_response()
        
    except Exception as e:
        logger.error(f"更新产品失败 {product_id}: {e}")
        return ResponseHelper.handle_exception(e)


@products_bp.route('/<int:product_id>', methods=['DELETE'])
@api_version()
def delete_product(product_id: int):
    """删除产品"""
    try:
        operator = getattr(g, 'current_user', {}).get('username', 'system')
        
        product_service = get_product_service()
        success = product_service.delete_product(product_id, operator)
        
        if not success:
            raise NotFoundError("产品不存在", resource_type="产品", resource_id=product_id)
        
        response = ResponseBuilder.success(message="产品删除成功")
        return response.to_json_response()
        
    except Exception as e:
        logger.error(f"删除产品失败 {product_id}: {e}")
        return ResponseHelper.handle_exception(e)


@products_bp.route('/categories', methods=['GET'])
@api_version()
def get_categories():
    """获取产品分类"""
    try:
        product_service = get_product_service()
        categories = product_service.get_categories()
        
        response = ResponseBuilder.success(data=categories)
        return response.to_json_response()
        
    except Exception as e:
        logger.error(f"获取产品分类失败: {e}")
        return ResponseHelper.handle_exception(e)


@products_bp.route('/batch', methods=['POST'])
@api_version()
def batch_create_products():
    """批量创建产品"""
    try:
        data = request.get_json()
        
        if not isinstance(data, dict) or 'products' not in data:
            raise ValidationError("请求格式错误，需要products数组")
        
        products_data = data['products']
        if not isinstance(products_data, list):
            raise ValidationError("products必须是数组")
        
        operator = getattr(g, 'current_user', {}).get('username', 'system')
        product_service = get_product_service()
        
        results = {
            'success_count': 0,
            'failed_count': 0,
            'created_products': [],
            'errors': []
        }
        
        for i, product_data in enumerate(products_data):
            try:
                product_id = product_service.create_product(product_data, operator)
                product = product_service.get_product(product_id)
                results['created_products'].append(product)
                results['success_count'] += 1
                
            except Exception as e:
                results['errors'].append({
                    'index': i,
                    'product_name': product_data.get('product_name', 'unknown'),
                    'error': str(e)
                })
                results['failed_count'] += 1
        
        message = f"批量创建完成：成功 {results['success_count']} 个，失败 {results['failed_count']} 个"
        response = ResponseBuilder.success(data=results, message=message)
        
        return response.to_json_response()
        
    except Exception as e:
        logger.error(f"批量创建产品失败: {e}")
        return ResponseHelper.handle_exception(e)


@products_bp.route('/export', methods=['GET'])
@api_version()
def export_products():
    """导出产品数据"""
    try:
        # 获取查询参数
        format_type = request.args.get('format', 'json').lower()
        category = request.args.get('category')
        
        if format_type not in ['json', 'csv']:
            raise ValidationError("不支持的导出格式", field="format")
        
        # 搜索产品（不分页，获取所有）
        product_service = get_product_service()
        result = product_service.search_products(
            category=category,
            per_page=10000  # 大数值获取所有产品
        )
        
        if format_type == 'json':
            response = ResponseBuilder.success(
                data={
                    'products': result.items,
                    'total': result.total,
                    'exported_at': request.json.get('timestamp') if request.json else None
                },
                message=f"成功导出 {result.total} 个产品"
            )
            return response.to_json_response()
        
        else:  # CSV format
            # 这里可以实现CSV导出逻辑
            # 为简化，暂时返回JSON格式提示
            response = ResponseBuilder.success(
                data={'message': 'CSV导出功能正在开发中，请使用JSON格式'}
            )
            return response.to_json_response()
        
    except Exception as e:
        logger.error(f"导出产品数据失败: {e}")
        return ResponseHelper.handle_exception(e)