# -*- coding: utf-8 -*-
"""
自定义异常类
"""


class BaseException(Exception):
    """基础异常类"""
    
    def __init__(self, message: str, error_code: str = None, details: dict = None):
        super().__init__(message)
        self.message = message
        self.error_code = error_code
        self.details = details or {}
    
    def to_dict(self) -> dict:
        """转换为字典格式"""
        return {
            'error': self.message,
            'error_code': self.error_code,
            'details': self.details
        }


class ValidationError(BaseException):
    """数据验证异常"""
    
    def __init__(self, message: str, field: str = None, value=None):
        super().__init__(message, 'VALIDATION_ERROR')
        self.field = field
        self.value = value
        if field:
            self.details['field'] = field
        if value is not None:
            self.details['value'] = str(value)


class AuthenticationError(BaseException):
    """认证异常"""
    
    def __init__(self, message: str = "认证失败"):
        super().__init__(message, 'AUTHENTICATION_ERROR')


class PermissionError(BaseException):
    """权限异常"""
    
    def __init__(self, message: str = "权限不足"):
        super().__init__(message, 'PERMISSION_ERROR')


class NotFoundError(BaseException):
    """资源不存在异常"""
    
    def __init__(self, message: str = "资源不存在", resource_type: str = None, resource_id=None):
        super().__init__(message, 'NOT_FOUND_ERROR')
        if resource_type:
            self.details['resource_type'] = resource_type
        if resource_id is not None:
            self.details['resource_id'] = str(resource_id)


class ConflictError(BaseException):
    """资源冲突异常"""
    
    def __init__(self, message: str = "资源冲突", conflicting_field: str = None):
        super().__init__(message, 'CONFLICT_ERROR')
        if conflicting_field:
            self.details['conflicting_field'] = conflicting_field


class ServiceError(BaseException):
    """服务异常"""
    
    def __init__(self, message: str = "服务错误", service_name: str = None):
        super().__init__(message, 'SERVICE_ERROR')
        if service_name:
            self.details['service_name'] = service_name


class ExternalServiceError(ServiceError):
    """外部服务异常"""
    
    def __init__(self, message: str = "外部服务错误", service_name: str = None, status_code: int = None):
        super().__init__(message, service_name)
        self.error_code = 'EXTERNAL_SERVICE_ERROR'
        if status_code:
            self.details['status_code'] = status_code


class RateLimitError(BaseException):
    """频率限制异常"""
    
    def __init__(self, message: str = "请求过于频繁", retry_after: int = None):
        super().__init__(message, 'RATE_LIMIT_ERROR')
        if retry_after:
            self.details['retry_after'] = retry_after


class ConfigurationError(BaseException):
    """配置异常"""
    
    def __init__(self, message: str = "配置错误", config_key: str = None):
        super().__init__(message, 'CONFIGURATION_ERROR')
        if config_key:
            self.details['config_key'] = config_key


class DatabaseError(ServiceError):
    """数据库异常"""
    
    def __init__(self, message: str = "数据库操作失败", operation: str = None):
        super().__init__(message, 'database')
        self.error_code = 'DATABASE_ERROR'
        if operation:
            self.details['operation'] = operation


class CacheError(ServiceError):
    """缓存异常"""
    
    def __init__(self, message: str = "缓存操作失败", operation: str = None):
        super().__init__(message, 'cache')
        self.error_code = 'CACHE_ERROR'
        if operation:
            self.details['operation'] = operation