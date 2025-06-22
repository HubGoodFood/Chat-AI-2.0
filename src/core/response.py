# -*- coding: utf-8 -*-
"""
标准化API响应系统
"""
import logging
from typing import Any, Dict, List, Optional, Union
from datetime import datetime
from flask import jsonify, request
from .exceptions import BaseException as CustomBaseException

logger = logging.getLogger(__name__)


class APIResponse:
    """API响应构建器"""
    
    def __init__(self, success: bool = True, message: str = None):
        self.success = success
        self.message = message
        self.data = None
        self.errors = []
        self.meta = {}
        self.timestamp = datetime.utcnow().isoformat()
        self.request_id = getattr(request, 'id', None) if request else None
    
    def set_data(self, data: Any) -> 'APIResponse':
        """设置响应数据"""
        self.data = data
        return self
    
    def set_message(self, message: str) -> 'APIResponse':
        """设置响应消息"""
        self.message = message
        return self
    
    def add_error(self, error: Union[str, Dict[str, Any]]) -> 'APIResponse':
        """添加错误信息"""
        if isinstance(error, str):
            self.errors.append({'message': error})
        else:
            self.errors.append(error)
        self.success = False
        return self
    
    def set_meta(self, key: str, value: Any) -> 'APIResponse':
        """设置元数据"""
        self.meta[key] = value
        return self
    
    def set_pagination(self, page: int, per_page: int, total: int, pages: int = None) -> 'APIResponse':
        """设置分页信息"""
        if pages is None:
            pages = (total + per_page - 1) // per_page
        
        self.meta['pagination'] = {
            'page': page,
            'per_page': per_page,
            'total': total,
            'pages': pages,
            'has_prev': page > 1,
            'has_next': page < pages
        }
        return self
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        response = {
            'success': self.success,
            'timestamp': self.timestamp
        }
        
        if self.message:
            response['message'] = self.message
        
        if self.data is not None:
            response['data'] = self.data
        
        if self.errors:
            response['errors'] = self.errors
        
        if self.meta:
            response['meta'] = self.meta
        
        if self.request_id:
            response['request_id'] = self.request_id
        
        return response
    
    def to_json_response(self, status_code: int = 200):
        """转换为Flask JSON响应"""
        return jsonify(self.to_dict()), status_code


class ResponseBuilder:
    """响应构建器"""
    
    @staticmethod
    def success(data: Any = None, message: str = None, meta: Dict[str, Any] = None) -> APIResponse:
        """成功响应"""
        response = APIResponse(success=True, message=message)
        if data is not None:
            response.set_data(data)
        if meta:
            for key, value in meta.items():
                response.set_meta(key, value)
        return response
    
    @staticmethod
    def error(message: str, errors: List[Union[str, Dict]] = None, 
             error_code: str = None, status_code: int = 400) -> APIResponse:
        """错误响应"""
        response = APIResponse(success=False, message=message)
        
        if errors:
            for error in errors:
                response.add_error(error)
        
        if error_code:
            response.set_meta('error_code', error_code)
        
        response.set_meta('status_code', status_code)
        return response
    
    @staticmethod
    def validation_error(field: str, message: str, value: Any = None) -> APIResponse:
        """验证错误响应"""
        error_detail = {
            'field': field,
            'message': message
        }
        if value is not None:
            error_detail['value'] = str(value)
        
        return ResponseBuilder.error(
            message="数据验证失败",
            errors=[error_detail],
            error_code="VALIDATION_ERROR",
            status_code=400
        )
    
    @staticmethod
    def not_found(resource_type: str = "资源", resource_id: Any = None) -> APIResponse:
        """资源不存在响应"""
        message = f"{resource_type}不存在"
        if resource_id:
            message += f" (ID: {resource_id})"
        
        response = ResponseBuilder.error(
            message=message,
            error_code="NOT_FOUND",
            status_code=404
        )
        
        if resource_id:
            response.set_meta('resource_id', str(resource_id))
        
        return response
    
    @staticmethod
    def unauthorized(message: str = "认证失败") -> APIResponse:
        """未授权响应"""
        return ResponseBuilder.error(
            message=message,
            error_code="UNAUTHORIZED",
            status_code=401
        )
    
    @staticmethod
    def forbidden(message: str = "权限不足") -> APIResponse:
        """禁止访问响应"""
        return ResponseBuilder.error(
            message=message,
            error_code="FORBIDDEN",
            status_code=403
        )
    
    @staticmethod
    def conflict(message: str = "资源冲突", conflicting_field: str = None) -> APIResponse:
        """资源冲突响应"""
        response = ResponseBuilder.error(
            message=message,
            error_code="CONFLICT",
            status_code=409
        )
        
        if conflicting_field:
            response.set_meta('conflicting_field', conflicting_field)
        
        return response
    
    @staticmethod
    def internal_error(message: str = "服务器内部错误") -> APIResponse:
        """内部错误响应"""
        return ResponseBuilder.error(
            message=message,
            error_code="INTERNAL_ERROR",
            status_code=500
        )
    
    @staticmethod
    def service_unavailable(message: str = "服务暂时不可用") -> APIResponse:
        """服务不可用响应"""
        return ResponseBuilder.error(
            message=message,
            error_code="SERVICE_UNAVAILABLE",
            status_code=503
        )
    
    @staticmethod
    def rate_limit_exceeded(retry_after: int = None) -> APIResponse:
        """频率限制响应"""
        response = ResponseBuilder.error(
            message="请求过于频繁，请稍后重试",
            error_code="RATE_LIMIT_EXCEEDED",
            status_code=429
        )
        
        if retry_after:
            response.set_meta('retry_after', retry_after)
        
        return response
    
    @staticmethod
    def paginated(items: List[Any], page: int, per_page: int, total: int,
                 message: str = None) -> APIResponse:
        """分页响应"""
        response = ResponseBuilder.success(data=items, message=message)
        response.set_pagination(page, per_page, total)
        return response
    
    @staticmethod
    def from_exception(exception: Exception) -> APIResponse:
        """从异常创建响应"""
        if isinstance(exception, CustomBaseException):
            return ResponseBuilder.error(
                message=exception.message,
                error_code=exception.error_code,
                status_code=getattr(exception, 'status_code', 500)
            )
        else:
            logger.error(f"未处理的异常: {str(exception)}", exc_info=True)
            return ResponseBuilder.internal_error()


class ResponseHelper:
    """响应辅助工具"""
    
    @staticmethod
    def handle_exception(exception: Exception):
        """处理异常并返回标准响应"""
        if isinstance(exception, CustomBaseException):
            status_code = 400
            
            # 根据异常类型确定HTTP状态码
            if 'AUTHENTICATION' in exception.error_code:
                status_code = 401
            elif 'PERMISSION' in exception.error_code:
                status_code = 403
            elif 'NOT_FOUND' in exception.error_code:
                status_code = 404
            elif 'CONFLICT' in exception.error_code:
                status_code = 409
            elif 'SERVICE' in exception.error_code or 'INTERNAL' in exception.error_code:
                status_code = 500
            
            response = ResponseBuilder.error(
                message=exception.message,
                error_code=exception.error_code,
                status_code=status_code
            )
            
            # 添加异常详情（如果有）
            if exception.details:
                response.set_meta('details', exception.details)
            
            return response.to_json_response(status_code)
        
        else:
            # 未知异常
            logger.error(f"未处理的异常: {str(exception)}", exc_info=True)
            response = ResponseBuilder.internal_error()
            return response.to_json_response(500)
    
    @staticmethod
    def success_created(data: Any = None, message: str = "创建成功") -> tuple:
        """创建成功响应"""
        response = ResponseBuilder.success(data=data, message=message)
        return response.to_json_response(201)
    
    @staticmethod
    def success_updated(data: Any = None, message: str = "更新成功") -> tuple:
        """更新成功响应"""
        response = ResponseBuilder.success(data=data, message=message)
        return response.to_json_response(200)
    
    @staticmethod
    def success_deleted(message: str = "删除成功") -> tuple:
        """删除成功响应"""
        response = ResponseBuilder.success(message=message)
        return response.to_json_response(200)


# 便利函数
def success_response(data: Any = None, message: str = None, **kwargs):
    """成功响应便利函数"""
    response = ResponseBuilder.success(data=data, message=message)
    if kwargs:
        for key, value in kwargs.items():
            response.set_meta(key, value)
    return response.to_json_response()


def error_response(message: str, status_code: int = 400, **kwargs):
    """错误响应便利函数"""
    response = ResponseBuilder.error(message=message, status_code=status_code)
    if kwargs:
        for key, value in kwargs.items():
            response.set_meta(key, value)
    return response.to_json_response(status_code)


def paginated_response(items: List[Any], page: int, per_page: int, total: int, **kwargs):
    """分页响应便利函数"""
    response = ResponseBuilder.paginated(items, page, per_page, total)
    if kwargs:
        for key, value in kwargs.items():
            response.set_meta(key, value)
    return response.to_json_response()