# -*- coding: utf-8 -*-
"""
标准化响应模块 - 提供统一的API响应格式

这个模块提供了一套标准化的API响应格式，确保整个应用的响应一致性。
包含成功响应、错误响应、分页响应等常用格式。

设计原则：
1. 统一的响应结构
2. 明确的错误代码
3. 详细的类型注解
4. 完整的文档说明

使用示例：
    from src.utils.responses import success_response, error_response

    # 成功响应
    return success_response({'product_id': 123}, '产品创建成功')

    # 错误响应
    return error_response('产品不存在', 404, 'PRODUCT_NOT_FOUND')
"""
from flask import jsonify
from typing import Any, Dict, List, Optional, Union
from datetime import datetime
import math


def success_response(
    data: Any = None,
    message: str = "操作成功",
    status_code: int = 200
) -> tuple:
    """
    标准成功响应格式

    这是所有成功操作的标准响应格式，确保前端能够统一处理成功响应。

    Args:
        data: 响应数据，可以是任何可序列化的对象（字典、列表、字符串等）
        message: 成功消息，用于向用户显示操作结果
        status_code: HTTP状态码，默认200（OK）

    Returns:
        tuple: (Flask响应对象, HTTP状态码)

    响应格式：
        {
            "success": true,
            "message": "操作成功",
            "data": {...},
            "timestamp": "2025-06-22T01:38:00.000Z"
        }

    Example:
        # 简单成功响应
        return success_response()

        # 带数据的成功响应
        return success_response({'product_id': 123}, '产品创建成功')

        # 自定义状态码
        return success_response({'user': user_data}, '用户注册成功', 201)
    """
    response = {
        'success': True,
        'message': message,
        'timestamp': datetime.utcnow().isoformat()
    }

    # 只有当data不为None时才添加data字段，避免不必要的null值
    if data is not None:
        response['data'] = data

    return jsonify(response), status_code


def error_response(
    error_message: str,
    status_code: int = 400,
    error_code: str = None,
    details: Dict = None
) -> tuple:
    """
    标准错误响应格式

    这是所有错误情况的标准响应格式，提供详细的错误信息供前端处理。

    Args:
        error_message: 用户友好的错误消息，应该是中文描述
        status_code: HTTP状态码，默认400（Bad Request）
        error_code: 机器可读的错误代码，用于前端程序化处理
        details: 额外的错误详情，如验证失败的具体字段信息

    Returns:
        tuple: (Flask响应对象, HTTP状态码)

    响应格式：
        {
            "success": false,
            "error": "错误消息",
            "error_code": "ERROR_CODE",
            "details": {...},
            "timestamp": "2025-06-22T01:38:00.000Z"
        }

    Example:
        # 简单错误响应
        return error_response('操作失败')

        # 带错误代码的响应
        return error_response('产品不存在', 404, 'PRODUCT_NOT_FOUND')

        # 带详细信息的响应
        return error_response('验证失败', 400, 'VALIDATION_ERROR',
                            {'field': 'product_name', 'issue': '不能为空'})
    """
    response = {
        'success': False,
        'error': error_message,
        'timestamp': datetime.utcnow().isoformat()
    }

    # 添加错误代码，便于前端程序化处理
    if error_code:
        response['error_code'] = error_code

    # 添加详细错误信息
    if details:
        response['details'] = details

    return jsonify(response), status_code


def validation_error_response(
    validation_errors: Union[str, List[str], Dict],
    status_code: int = 400
) -> tuple:
    """
    数据验证错误响应格式

    专门用于处理数据验证失败的情况，能够处理多种格式的验证错误信息。

    Args:
        validation_errors: 验证错误信息，支持多种格式：
            - str: 单个错误消息
            - List[str]: 多个错误消息列表
            - Dict: 字段名到错误消息的映射
        status_code: HTTP状态码，默认400

    Returns:
        tuple: (Flask响应对象, HTTP状态码)

    Example:
        # 单个错误
        return validation_error_response('产品名称不能为空')

        # 多个错误
        return validation_error_response(['产品名称不能为空', '价格必须大于0'])

        # 字段映射错误
        return validation_error_response({
            'product_name': '不能为空',
            'price': '必须大于0'
        })
    """
    # 根据不同的输入格式处理错误消息
    if isinstance(validation_errors, str):
        error_message = validation_errors
    elif isinstance(validation_errors, list):
        error_message = '; '.join(validation_errors)
    elif isinstance(validation_errors, dict):
        error_list = []
        for field, errors in validation_errors.items():
            if isinstance(errors, list):
                # 处理字段有多个错误的情况
                error_list.extend([f"{field}: {error}" for error in errors])
            else:
                error_list.append(f"{field}: {errors}")
        error_message = '; '.join(error_list)
    else:
        error_message = '数据验证失败'

    return error_response(
        error_message=f'数据验证失败: {error_message}',
        status_code=status_code,
        error_code='VALIDATION_ERROR'
    )


def paginated_response(
    items: List[Any],
    total: int,
    page: int,
    per_page: int,
    message: str = "查询成功"
) -> tuple:
    """
    分页响应格式

    用于返回分页数据的标准格式，包含数据项和分页信息。

    Args:
        items: 当前页的数据项列表
        total: 总记录数
        page: 当前页码（从1开始）
        per_page: 每页记录数
        message: 成功消息

    Returns:
        tuple: (Flask响应对象, HTTP状态码)

    响应格式：
        {
            "success": true,
            "message": "查询成功",
            "data": {
                "items": [...],
                "pagination": {
                    "total": 150,
                    "page": 2,
                    "per_page": 20,
                    "total_pages": 8,
                    "has_next": true,
                    "has_prev": true,
                    "next_page": 3,
                    "prev_page": 1
                }
            },
            "timestamp": "2025-06-22T01:38:00.000Z"
        }

    Example:
        return paginated_response(products, 150, 2, 20, '产品列表获取成功')
    """
    # 计算分页信息
    total_pages = math.ceil(total / per_page) if per_page > 0 else 0
    has_next = page < total_pages
    has_prev = page > 1

    pagination_info = {
        'total': total,
        'page': page,
        'per_page': per_page,
        'total_pages': total_pages,
        'has_next': has_next,
        'has_prev': has_prev
    }

    # 添加导航链接信息，便于前端实现分页导航
    if has_next:
        pagination_info['next_page'] = page + 1
    if has_prev:
        pagination_info['prev_page'] = page - 1

    data = {
        'items': items,
        'pagination': pagination_info
    }

    return success_response(data, message)


def created_response(
    data: Any = None,
    message: str = "创建成功",
    resource_id: Union[str, int] = None
) -> tuple:
    """
    资源创建成功响应格式

    专门用于资源创建操作的响应，返回201状态码。

    Args:
        data: 创建的资源数据
        message: 成功消息
        resource_id: 新创建资源的ID

    Returns:
        tuple: (Flask响应对象, HTTP状态码)

    Example:
        return created_response({'product': product_data}, '产品创建成功', product_id)
    """
    response_data = data or {}

    # 如果提供了资源ID，将其添加到响应数据中
    if resource_id is not None:
        if isinstance(response_data, dict):
            response_data['id'] = resource_id
        else:
            response_data = {'id': resource_id, 'data': response_data}

    return success_response(response_data, message, 201)


def no_content_response(message: str = "操作成功") -> tuple:
    """
    无内容响应格式（通常用于删除操作）

    Args:
        message: 成功消息

    Returns:
        tuple: (Flask响应对象, HTTP状态码)

    Example:
        return no_content_response('产品删除成功')
    """
    return success_response(message=message, status_code=204)


def unauthorized_response(message: str = "未授权访问") -> tuple:
    """
    未授权访问响应格式

    Args:
        message: 错误消息

    Returns:
        tuple: (Flask响应对象, HTTP状态码)
    """
    return error_response(
        error_message=message,
        status_code=401,
        error_code='UNAUTHORIZED'
    )


def forbidden_response(message: str = "权限不足") -> tuple:
    """
    权限不足响应格式

    Args:
        message: 错误消息

    Returns:
        tuple: (Flask响应对象, HTTP状态码)
    """
    return error_response(
        error_message=message,
        status_code=403,
        error_code='FORBIDDEN'
    )


def not_found_response(
    resource_type: str = "资源",
    resource_id: Union[str, int] = None
) -> tuple:
    """
    资源不存在响应格式

    Args:
        resource_type: 资源类型名称
        resource_id: 资源ID

    Returns:
        tuple: (Flask响应对象, HTTP状态码)

    Example:
        return not_found_response('产品', product_id)
    """
    if resource_id:
        message = f"{resource_type}(ID: {resource_id})不存在"
    else:
        message = f"{resource_type}不存在"

    return error_response(
        error_message=message,
        status_code=404,
        error_code='NOT_FOUND'
    )


def conflict_response(
    message: str = "资源冲突",
    details: Dict = None
) -> tuple:
    """
    资源冲突响应格式（如重复创建）

    Args:
        message: 错误消息
        details: 冲突详情

    Returns:
        tuple: (Flask响应对象, HTTP状态码)

    Example:
        return conflict_response('产品名称已存在', {'existing_id': 123})
    """
    return error_response(
        error_message=message,
        status_code=409,
        error_code='CONFLICT',
        details=details
    )


def rate_limit_response(
    message: str = "请求频率过高，请稍后再试",
    retry_after: int = None
) -> tuple:
    """
    速率限制响应格式

    Args:
        message: 错误消息
        retry_after: 建议重试间隔（秒）

    Returns:
        tuple: (Flask响应对象, HTTP状态码)
    """
    details = {}
    if retry_after:
        details['retry_after'] = retry_after

    return error_response(
        error_message=message,
        status_code=429,
        error_code='RATE_LIMIT_EXCEEDED',
        details=details if details else None
    )


def server_error_response(
    message: str = "服务器内部错误",
    error_id: str = None
) -> tuple:
    """
    服务器错误响应格式

    Args:
        message: 错误消息
        error_id: 错误追踪ID

    Returns:
        tuple: (Flask响应对象, HTTP状态码)
    """
    details = {}
    if error_id:
        details['error_id'] = error_id

    return error_response(
        error_message=message,
        status_code=500,
        error_code='INTERNAL_ERROR',
        details=details if details else None
    )


# 便捷函数，用于快速创建常用响应
def api_success(data=None, message="操作成功"):
    """API成功响应的便捷函数"""
    return success_response(data, message)


def api_error(message, code=None):
    """API错误响应的便捷函数"""
    return error_response(message, error_code=code)


def api_not_found(resource="资源", resource_id=None):
    """API资源不存在响应的便捷函数"""
    return not_found_response(resource, resource_id)


def api_unauthorized(message="需要登录"):
    """API未授权响应的便捷函数"""
    return unauthorized_response(message)


def api_forbidden(message="权限不足"):
    """API权限不足响应的便捷函数"""
    return forbidden_response(message)