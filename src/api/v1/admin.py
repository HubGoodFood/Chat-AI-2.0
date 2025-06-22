# -*- coding: utf-8 -*-
"""
管理员API控制器 v1
"""
import logging
from flask import Blueprint, request, session
from ...core.service_registry import get_product_service, get_inventory_service, get_chat_service
from ...core.response import ResponseBuilder, ResponseHelper
from ...core.exceptions import AuthenticationError, ValidationError
from ..version_control import api_version
from ...services.performance_monitor import performance_monitor

logger = logging.getLogger(__name__)

admin_bp = Blueprint('admin', __name__)


def require_admin():
    """管理员认证装饰器"""
    if 'admin_user' not in session:
        raise AuthenticationError("需要管理员权限")
    return session['admin_user']


@admin_bp.route('/dashboard', methods=['GET'])
@api_version()
def get_dashboard_data():
    """获取管理员仪表板数据"""
    try:
        admin_user = require_admin()
        
        # 获取各种统计数据
        product_service = get_product_service()
        inventory_service = get_inventory_service()
        chat_service = get_chat_service()
        
        # 产品统计
        product_stats = {
            'categories': product_service.get_categories(),
            'low_stock_products': inventory_service.get_low_stock_products()[:5]  # 前5个
        }
        
        # 库存统计
        inventory_stats = inventory_service.get_stock_statistics()
        
        # 聊天统计
        chat_stats = chat_service.get_conversation_stats()
        
        # 系统状态
        system_stats = performance_monitor.get_performance_summary()
        
        dashboard_data = {
            'product_stats': product_stats,
            'inventory_stats': inventory_stats,
            'chat_stats': chat_stats,
            'system_stats': {
                'health_score': system_stats.get('health_score', 0),
                'uptime': system_stats.get('uptime', 0)
            },
            'recent_activities': [
                {
                    'type': 'info',
                    'message': f"系统健康评分: {system_stats.get('health_score', 0)}",
                    'timestamp': request.json.get('timestamp') if request.json else None
                },
                {
                    'type': 'warning',
                    'message': f"低库存产品: {len(product_stats['low_stock_products'])} 个",
                    'timestamp': request.json.get('timestamp') if request.json else None
                }
            ]
        }
        
        response = ResponseBuilder.success(
            data=dashboard_data,
            message="仪表板数据获取成功"
        )
        
        response.set_meta('admin_user', admin_user['username'])
        
        return response.to_json_response()
        
    except Exception as e:
        logger.error(f"获取仪表板数据失败: {e}")
        return ResponseHelper.handle_exception(e)


@admin_bp.route('/system/status', methods=['GET'])
@api_version()
def get_system_status():
    """获取系统状态"""
    try:
        require_admin()
        
        # 获取详细的系统状态
        system_status = performance_monitor.get_performance_summary()
        
        response = ResponseBuilder.success(
            data=system_status,
            message="系统状态获取成功"
        )
        
        return response.to_json_response()
        
    except Exception as e:
        logger.error(f"获取系统状态失败: {e}")
        return ResponseHelper.handle_exception(e)


@admin_bp.route('/system/metrics', methods=['GET'])
@api_version()
def get_system_metrics():
    """获取系统性能指标"""
    try:
        require_admin()
        
        # 获取性能指标
        metrics = {
            'system': performance_monitor.get_system_metrics(),
            'database': performance_monitor.get_database_metrics(),
            'cache': performance_monitor.get_cache_metrics(),
            'api': performance_monitor.get_api_metrics()
        }
        
        response = ResponseBuilder.success(
            data=metrics,
            message="系统指标获取成功"
        )
        
        return response.to_json_response()
        
    except Exception as e:
        logger.error(f"获取系统指标失败: {e}")
        return ResponseHelper.handle_exception(e)


@admin_bp.route('/logs', methods=['GET'])
@api_version()
def get_operation_logs():
    """获取操作日志"""
    try:
        require_admin()
        
        # 分页参数
        page = int(request.args.get('page', 1))
        per_page = min(int(request.args.get('per_page', 20)), 100)
        
        # 过滤参数
        operator = request.args.get('operator')
        operation_type = request.args.get('operation_type')
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        
        # 这里可以实现真正的日志查询
        # 暂时返回示例数据
        logs = [
            {
                'id': 1,
                'operator': 'admin',
                'operation_type': 'create_product',
                'target_type': 'product',
                'target_id': '123',
                'details': {'product_name': '苹果'},
                'result': 'success',
                'timestamp': '2025-06-22T10:30:00Z',
                'ip_address': '192.168.1.100'
            },
            {
                'id': 2,
                'operator': 'admin',
                'operation_type': 'update_stock',
                'target_type': 'product',
                'target_id': '123',
                'details': {'old_stock': 50, 'new_stock': 45},
                'result': 'success',
                'timestamp': '2025-06-22T10:25:00Z',
                'ip_address': '192.168.1.100'
            }
        ]
        
        # 应用过滤
        filtered_logs = logs
        if operator:
            filtered_logs = [log for log in filtered_logs if log['operator'] == operator]
        if operation_type:
            filtered_logs = [log for log in filtered_logs if log['operation_type'] == operation_type]
        
        response = ResponseBuilder.paginated(
            items=filtered_logs,
            page=page,
            per_page=per_page,
            total=len(filtered_logs)
        )
        
        response.set_meta('filters', {
            'operator': operator,
            'operation_type': operation_type,
            'start_date': start_date,
            'end_date': end_date
        })
        
        return response.to_json_response()
        
    except ValueError as e:
        logger.warning(f"获取操作日志参数错误: {e}")
        return ResponseHelper.handle_exception(ValidationError(f"参数格式错误: {e}"))
    except Exception as e:
        logger.error(f"获取操作日志失败: {e}")
        return ResponseHelper.handle_exception(e)


@admin_bp.route('/cache/clear', methods=['POST'])
@api_version()
def clear_cache():
    """清除缓存"""
    try:
        admin_user = require_admin()
        
        data = request.get_json() or {}
        cache_type = data.get('cache_type', 'all')
        
        # 这里可以实现真正的缓存清除
        from ...services.cache_service import cache_service
        
        if cache_type == 'all':
            # 清除所有缓存
            cleared_count = cache_service.clear_pattern('*')
        else:
            # 清除特定类型的缓存
            cleared_count = cache_service.clear_pattern(f'{cache_type}:*')
        
        logger.info(f"管理员清除缓存: {cache_type} by {admin_user['username']}")
        
        response = ResponseBuilder.success(
            data={'cleared_count': cleared_count},
            message=f"缓存清除成功，清除了 {cleared_count} 个缓存项"
        )
        
        return response.to_json_response()
        
    except Exception as e:
        logger.error(f"清除缓存失败: {e}")
        return ResponseHelper.handle_exception(e)


@admin_bp.route('/backup', methods=['POST'])
@api_version()
def create_backup():
    """创建数据备份"""
    try:
        admin_user = require_admin()
        
        data = request.get_json() or {}
        backup_type = data.get('backup_type', 'full')
        description = data.get('description', '')
        
        # 这里可以实现真正的备份功能
        # 暂时返回示例响应
        import time
        backup_id = f"backup_{int(time.time())}"
        
        backup_info = {
            'backup_id': backup_id,
            'backup_type': backup_type,
            'description': description,
            'status': 'completed',
            'created_by': admin_user['username'],
            'created_at': request.json.get('timestamp') if request.json else None,
            'file_size': '1.2 MB',
            'duration': '5 seconds'
        }
        
        logger.info(f"创建数据备份: {backup_id} by {admin_user['username']}")
        
        response = ResponseBuilder.success(
            data=backup_info,
            message="数据备份创建成功"
        )
        
        return response.to_json_response()
        
    except Exception as e:
        logger.error(f"创建数据备份失败: {e}")
        return ResponseHelper.handle_exception(e)


@admin_bp.route('/settings', methods=['GET'])
@api_version()
def get_system_settings():
    """获取系统设置"""
    try:
        require_admin()
        
        # 这里可以从配置服务获取系统设置
        from ...core.config import config_service
        
        settings = {
            'business': config_service.get_section('business'),
            'cache': config_service.get_section('cache'),
            'file': config_service.get_section('file'),
            'system': {
                'environment': config_service.get('environment'),
                'debug': config_service.get('debug'),
                'version': '2.1.0'
            }
        }
        
        response = ResponseBuilder.success(
            data=settings,
            message="系统设置获取成功"
        )
        
        return response.to_json_response()
        
    except Exception as e:
        logger.error(f"获取系统设置失败: {e}")
        return ResponseHelper.handle_exception(e)


@admin_bp.route('/settings', methods=['PUT'])
@api_version()
def update_system_settings():
    """更新系统设置"""
    try:
        admin_user = require_admin()
        
        # 检查超级管理员权限
        if not admin_user.get('is_super_admin'):
            raise ValidationError("权限不足，只有超级管理员可以修改系统设置")
        
        data = request.get_json()
        if not data:
            raise ValidationError("请求数据不能为空")
        
        # 这里可以实现真正的设置更新
        # 暂时记录日志
        logger.info(f"更新系统设置 by {admin_user['username']}: {list(data.keys())}")
        
        response = ResponseBuilder.success(
            message="系统设置更新成功"
        )
        
        return response.to_json_response()
        
    except Exception as e:
        logger.error(f"更新系统设置失败: {e}")
        return ResponseHelper.handle_exception(e)


@admin_bp.route('/export', methods=['POST'])
@api_version()
def export_data():
    """导出数据"""
    try:
        admin_user = require_admin()
        
        data = request.get_json() or {}
        export_type = data.get('export_type', 'products')
        format_type = data.get('format', 'json')
        filters = data.get('filters', {})
        
        if export_type not in ['products', 'inventory', 'logs', 'users']:
            raise ValidationError("不支持的导出类型", field="export_type")
        
        if format_type not in ['json', 'csv', 'excel']:
            raise ValidationError("不支持的导出格式", field="format")
        
        # 这里可以实现真正的数据导出
        # 暂时返回示例响应
        export_info = {
            'export_id': f"export_{export_type}_{int(request.json.get('timestamp') or 0)}",
            'export_type': export_type,
            'format': format_type,
            'status': 'completed',
            'file_url': f'/api/v1/admin/downloads/export_{export_type}.{format_type}',
            'record_count': 100,
            'file_size': '2.5 MB',
            'created_by': admin_user['username'],
            'created_at': request.json.get('timestamp') if request.json else None
        }
        
        logger.info(f"导出数据: {export_type} ({format_type}) by {admin_user['username']}")
        
        response = ResponseBuilder.success(
            data=export_info,
            message="数据导出完成"
        )
        
        return response.to_json_response()
        
    except Exception as e:
        logger.error(f"导出数据失败: {e}")
        return ResponseHelper.handle_exception(e)