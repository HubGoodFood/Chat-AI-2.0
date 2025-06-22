# -*- coding: utf-8 -*-
"""
库存API控制器 v1
"""
import logging
from flask import Blueprint, request, g
from ...core.service_registry import get_inventory_service
from ...core.response import ResponseBuilder, ResponseHelper
from ...core.exceptions import ValidationError, NotFoundError
from ...core.interfaces import PaginationParams
from ..version_control import api_version
from ...utils.validators import validate_json, StockUpdateRequest, StockAdjustRequest

logger = logging.getLogger(__name__)

inventory_bp = Blueprint('inventory', __name__)


@inventory_bp.route('/<int:product_id>/stock', methods=['GET'])
@api_version()
def get_stock(product_id: int):
    """获取产品库存信息"""
    try:
        inventory_service = get_inventory_service()
        stock_info = inventory_service.get_stock(product_id)
        
        if not stock_info:
            raise NotFoundError("产品不存在", resource_type="产品", resource_id=product_id)
        
        response = ResponseBuilder.success(data=stock_info)
        return response.to_json_response()
        
    except Exception as e:
        logger.error(f"获取库存信息失败 {product_id}: {e}")
        return ResponseHelper.handle_exception(e)


@inventory_bp.route('/<int:product_id>/stock', methods=['PUT'])
@api_version()
@validate_json(StockUpdateRequest)
def update_stock(product_id: int):
    """更新产品库存"""
    try:
        data = request.get_json()
        operator = getattr(g, 'current_user', {}).get('username', 'system')
        
        inventory_service = get_inventory_service()
        success = inventory_service.update_stock(
            product_id=product_id,
            new_stock=data['new_stock'],
            operator=operator,
            note=data.get('note')
        )
        
        if not success:
            raise NotFoundError("产品不存在", resource_type="产品", resource_id=product_id)
        
        # 获取更新后的库存信息
        stock_info = inventory_service.get_stock(product_id)
        
        response = ResponseBuilder.success(
            data=stock_info,
            message="库存更新成功"
        )
        
        return response.to_json_response()
        
    except Exception as e:
        logger.error(f"更新库存失败 {product_id}: {e}")
        return ResponseHelper.handle_exception(e)


@inventory_bp.route('/<int:product_id>/stock/adjust', methods=['POST'])
@api_version()
@validate_json(StockAdjustRequest)
def adjust_stock(product_id: int):
    """调整产品库存"""
    try:
        data = request.get_json()
        operator = getattr(g, 'current_user', {}).get('username', 'system')
        
        inventory_service = get_inventory_service()
        success = inventory_service.adjust_stock(
            product_id=product_id,
            quantity_change=data['quantity_change'],
            action=data['action'],
            operator=operator,
            note=data.get('note')
        )
        
        if not success:
            raise NotFoundError("产品不存在", resource_type="产品", resource_id=product_id)
        
        # 获取调整后的库存信息
        stock_info = inventory_service.get_stock(product_id)
        
        response = ResponseBuilder.success(
            data=stock_info,
            message="库存调整成功"
        )
        
        return response.to_json_response()
        
    except Exception as e:
        logger.error(f"调整库存失败 {product_id}: {e}")
        return ResponseHelper.handle_exception(e)


@inventory_bp.route('/<int:product_id>/history', methods=['GET'])
@api_version()
def get_stock_history(product_id: int):
    """获取库存历史"""
    try:
        # 分页参数
        page = int(request.args.get('page', 1))
        per_page = min(int(request.args.get('per_page', 20)), 100)
        
        pagination = PaginationParams(page=page, per_page=per_page)
        
        inventory_service = get_inventory_service()
        result = inventory_service.get_stock_history(product_id, pagination)
        
        response = ResponseBuilder.paginated(
            items=result.items,
            page=result.page,
            per_page=result.per_page,
            total=result.total
        )
        
        response.set_meta('product_id', product_id)
        
        return response.to_json_response()
        
    except ValueError as e:
        logger.warning(f"获取库存历史参数错误: {e}")
        return ResponseHelper.handle_exception(ValidationError(f"参数格式错误: {e}"))
    except Exception as e:
        logger.error(f"获取库存历史失败 {product_id}: {e}")
        return ResponseHelper.handle_exception(e)


@inventory_bp.route('/low-stock', methods=['GET'])
@api_version()
def get_low_stock_products():
    """获取低库存产品"""
    try:
        # 阈值倍数参数
        threshold_multiplier = float(request.args.get('threshold', 1.0))
        
        inventory_service = get_inventory_service()
        low_stock_products = inventory_service.get_low_stock_products(threshold_multiplier)
        
        response = ResponseBuilder.success(
            data=low_stock_products,
            message=f"找到 {len(low_stock_products)} 个低库存产品"
        )
        
        response.set_meta('threshold_multiplier', threshold_multiplier)
        response.set_meta('urgency_breakdown', {
            'critical': len([p for p in low_stock_products if p['urgency_level'] == 'critical']),
            'warning': len([p for p in low_stock_products if p['urgency_level'] == 'warning']),
            'low': len([p for p in low_stock_products if p['urgency_level'] == 'low'])
        })
        
        return response.to_json_response()
        
    except ValueError as e:
        logger.warning(f"获取低库存产品参数错误: {e}")
        return ResponseHelper.handle_exception(ValidationError(f"参数格式错误: {e}"))
    except Exception as e:
        logger.error(f"获取低库存产品失败: {e}")
        return ResponseHelper.handle_exception(e)


@inventory_bp.route('/statistics', methods=['GET'])
@api_version()
def get_inventory_statistics():
    """获取库存统计信息"""
    try:
        inventory_service = get_inventory_service()
        stats = inventory_service.get_stock_statistics()
        
        response = ResponseBuilder.success(data=stats)
        return response.to_json_response()
        
    except Exception as e:
        logger.error(f"获取库存统计失败: {e}")
        return ResponseHelper.handle_exception(e)


@inventory_bp.route('/batch-update', methods=['POST'])
@api_version()
def batch_update_stock():
    """批量更新库存"""
    try:
        data = request.get_json()
        
        if not isinstance(data, dict) or 'updates' not in data:
            raise ValidationError("请求格式错误，需要updates数组")
        
        updates = data['updates']
        if not isinstance(updates, list):
            raise ValidationError("updates必须是数组")
        
        # 验证每个更新项
        for i, update in enumerate(updates):
            if not isinstance(update, dict):
                raise ValidationError(f"更新项 {i} 格式错误")
            
            if 'product_id' not in update or 'new_stock' not in update:
                raise ValidationError(f"更新项 {i} 缺少必要字段")
            
            try:
                update['product_id'] = int(update['product_id'])
                update['new_stock'] = int(update['new_stock'])
            except (ValueError, TypeError):
                raise ValidationError(f"更新项 {i} 数据类型错误")
        
        operator = getattr(g, 'current_user', {}).get('username', 'system')
        
        inventory_service = get_inventory_service()
        results = inventory_service.batch_update_stock(updates, operator)
        
        message = f"批量更新完成：成功 {results['success_count']} 个，失败 {results['failed_count']} 个"
        response = ResponseBuilder.success(data=results, message=message)
        
        return response.to_json_response()
        
    except Exception as e:
        logger.error(f"批量更新库存失败: {e}")
        return ResponseHelper.handle_exception(e)


@inventory_bp.route('/count-tasks', methods=['GET'])
@api_version()
def get_count_tasks():
    """获取盘点任务列表"""
    try:
        # 分页参数
        page = int(request.args.get('page', 1))
        per_page = min(int(request.args.get('per_page', 20)), 100)
        
        # 状态过滤
        status = request.args.get('status')
        
        # 这里可以扩展为真正的盘点任务管理
        # 暂时返回示例数据
        tasks = [
            {
                'id': 1,
                'name': '月度盘点',
                'status': 'completed',
                'created_at': '2025-06-01T00:00:00Z',
                'completed_at': '2025-06-02T12:00:00Z',
                'operator': 'admin',
                'products_count': 150,
                'discrepancies_count': 5
            },
            {
                'id': 2,
                'name': '低库存产品盘点',
                'status': 'in_progress',
                'created_at': '2025-06-20T09:00:00Z',
                'operator': 'admin',
                'products_count': 25,
                'progress': 60
            }
        ]
        
        filtered_tasks = [task for task in tasks if not status or task['status'] == status]
        
        response = ResponseBuilder.paginated(
            items=filtered_tasks,
            page=page,
            per_page=per_page,
            total=len(filtered_tasks)
        )
        
        return response.to_json_response()
        
    except ValueError as e:
        logger.warning(f"获取盘点任务参数错误: {e}")
        return ResponseHelper.handle_exception(ValidationError(f"参数格式错误: {e}"))
    except Exception as e:
        logger.error(f"获取盘点任务失败: {e}")
        return ResponseHelper.handle_exception(e)


@inventory_bp.route('/alerts', methods=['GET'])
@api_version()
def get_inventory_alerts():
    """获取库存预警信息"""
    try:
        inventory_service = get_inventory_service()
        
        # 获取低库存产品
        low_stock_products = inventory_service.get_low_stock_products()
        
        # 构建预警信息
        alerts = []
        
        for product in low_stock_products:
            if product['urgency_level'] == 'critical':
                alert_type = 'danger'
                message = f"{product['product_name']} 严重缺货"
            elif product['urgency_level'] == 'warning':
                alert_type = 'warning'
                message = f"{product['product_name']} 库存不足"
            else:
                alert_type = 'info'
                message = f"{product['product_name']} 库存偏低"
            
            alerts.append({
                'type': alert_type,
                'message': message,
                'product_id': product['product_id'],
                'product_name': product['product_name'],
                'current_stock': product['current_stock'],
                'min_stock_warning': product['min_stock_warning'],
                'urgency_level': product['urgency_level']
            })
        
        response = ResponseBuilder.success(
            data=alerts,
            message=f"共有 {len(alerts)} 个库存预警"
        )
        
        response.set_meta('alert_summary', {
            'total': len(alerts),
            'critical': len([a for a in alerts if a['type'] == 'danger']),
            'warning': len([a for a in alerts if a['type'] == 'warning']),
            'info': len([a for a in alerts if a['type'] == 'info'])
        })
        
        return response.to_json_response()
        
    except Exception as e:
        logger.error(f"获取库存预警失败: {e}")
        return ResponseHelper.handle_exception(e)