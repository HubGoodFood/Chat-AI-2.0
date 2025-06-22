# -*- coding: utf-8 -*-
"""
全局错误处理器模块 - 提供统一的异常处理机制

这个模块提供了Flask应用的全局错误处理器，能够捕获和处理各种类型的异常，
并返回标准化的错误响应。

主要功能：
1. 注册全局错误处理器
2. 处理自定义异常类
3. 处理标准Python异常
4. 记录错误日志
5. 返回标准化错误响应

设计原则：
- 统一的错误响应格式
- 详细的错误日志记录
- 安全的错误信息暴露
- 用户友好的错误消息

使用示例：
    from src.utils.error_handlers import register_error_handlers

    app = Flask(__name__)
    register_error_handlers(app)
"""
from flask import Flask, jsonify, request
from werkzeug.exceptions import HTTPException
import logging
import traceback
from typing import Tuple, Any

# 导入自定义异常类
from src.core.exceptions import (
    BaseException as CustomBaseException,
    ValidationError,
    AuthenticationError,
    PermissionError,
    NotFoundError,
    ConflictError,
    ServiceError,
    ExternalServiceError,
    RateLimitError,
    ConfigurationError,
    DatabaseError,
    CacheError
)

# 导入响应工具
from .responses import (
    error_response,
    validation_error_response,
    unauthorized_response,
    forbidden_response,
    not_found_response,
    conflict_response,
    rate_limit_response,
    server_error_response
)

from .logger_config import get_logger

logger = get_logger('error_handlers')


def register_error_handlers(app: Flask) -> None:
    """
    注册全局错误处理器

    这个函数会为Flask应用注册所有必要的错误处理器，
    确保应用能够优雅地处理各种异常情况。

    Args:
        app: Flask应用实例

    Example:
        app = Flask(__name__)
        register_error_handlers(app)
    """

    @app.errorhandler(ValidationError)
    def handle_validation_error(error: ValidationError) -> Tuple[Any, int]:
        """
        处理数据验证错误

        当数据验证失败时，返回详细的验证错误信息。
        """
        logger.warning(f"数据验证错误: {error.message} | 字段: {error.field} | 值: {error.value}")

        # 构建详细的验证错误信息
        if error.field:
            validation_errors = {error.field: error.message}
        else:
            validation_errors = error.message

        return validation_error_response(validation_errors)


    @app.errorhandler(AuthenticationError)
    def handle_authentication_error(error: AuthenticationError) -> Tuple[Any, int]:
        """
        处理认证错误

        当用户认证失败时，返回未授权响应。
        """
        logger.warning(f"认证错误: {error.message} | IP: {request.remote_addr}")
        return unauthorized_response(error.message)


    @app.errorhandler(PermissionError)
    def handle_permission_error(error: PermissionError) -> Tuple[Any, int]:
        """
        处理权限错误

        当用户权限不足时，返回禁止访问响应。
        """
        logger.warning(f"权限错误: {error.message} | IP: {request.remote_addr}")
        return forbidden_response(error.message)


    @app.errorhandler(NotFoundError)
    def handle_not_found_error(error: NotFoundError) -> Tuple[Any, int]:
        """
        处理资源不存在错误

        当请求的资源不存在时，返回404响应。
        """
        logger.info(f"资源不存在: {error.message} | 详情: {error.details}")

        resource_type = error.details.get('resource_type', '资源')
        resource_id = error.details.get('resource_id')

        return not_found_response(resource_type, resource_id)


    @app.errorhandler(ConflictError)
    def handle_conflict_error(error: ConflictError) -> Tuple[Any, int]:
        """
        处理资源冲突错误

        当资源冲突时（如重复创建），返回409响应。
        """
        logger.warning(f"资源冲突: {error.message} | 详情: {error.details}")
        return conflict_response(error.message, error.details)


    @app.errorhandler(RateLimitError)
    def handle_rate_limit_error(error: RateLimitError) -> Tuple[Any, int]:
        """
        处理频率限制错误

        当请求频率过高时，返回429响应。
        """
        logger.warning(f"频率限制: {error.message} | IP: {request.remote_addr}")
        retry_after = error.details.get('retry_after')
        return rate_limit_response(error.message, retry_after)


    @app.errorhandler(DatabaseError)
    def handle_database_error(error: DatabaseError) -> Tuple[Any, int]:
        """
        处理数据库错误

        当数据库操作失败时，返回服务器错误响应。
        """
        logger.error(f"数据库错误: {error.message} | 操作: {error.details.get('operation', 'unknown')}")

        # 对用户隐藏具体的数据库错误信息
        return server_error_response("数据操作失败，请稍后重试")


    @app.errorhandler(CacheError)
    def handle_cache_error(error: CacheError) -> Tuple[Any, int]:
        """
        处理缓存错误

        当缓存操作失败时，记录错误但不影响主要功能。
        """
        logger.warning(f"缓存错误: {error.message} | 操作: {error.details.get('operation', 'unknown')}")

        # 缓存错误通常不应该影响主要功能，返回通用错误
        return server_error_response("服务暂时不可用，请稍后重试")


    @app.errorhandler(ExternalServiceError)
    def handle_external_service_error(error: ExternalServiceError) -> Tuple[Any, int]:
        """
        处理外部服务错误

        当外部服务调用失败时，返回服务器错误响应。
        """
        service_name = error.details.get('service_name', '外部服务')
        status_code = error.details.get('status_code', 'unknown')

        logger.error(f"外部服务错误: {error.message} | 服务: {service_name} | 状态码: {status_code}")

        return server_error_response(f"{service_name}暂时不可用，请稍后重试")


    @app.errorhandler(ServiceError)
    def handle_service_error(error: ServiceError) -> Tuple[Any, int]:
        """
        处理通用服务错误

        当业务逻辑出现错误时，返回服务器错误响应。
        """
        service_name = error.details.get('service_name', '服务')
        logger.error(f"服务错误: {error.message} | 服务: {service_name}")

        return server_error_response(error.message)


    @app.errorhandler(ConfigurationError)
    def handle_configuration_error(error: ConfigurationError) -> Tuple[Any, int]:
        """
        处理配置错误

        当配置错误时，返回服务器错误响应。
        """
        config_key = error.details.get('config_key', 'unknown')
        logger.error(f"配置错误: {error.message} | 配置项: {config_key}")

        return server_error_response("系统配置错误，请联系管理员")


    @app.errorhandler(CustomBaseException)
    def handle_custom_base_exception(error: CustomBaseException) -> Tuple[Any, int]:
        """
        处理自定义基础异常

        这是所有自定义异常的兜底处理器。
        """
        logger.error(f"自定义异常: {error.message} | 错误代码: {error.error_code} | 详情: {error.details}")

        return error_response(
            error_message=error.message,
            status_code=500,
            error_code=error.error_code,
            details=error.details
        )


    # 处理标准Python异常
    @app.errorhandler(ValueError)
    def handle_value_error(error: ValueError) -> Tuple[Any, int]:
        """
        处理值错误

        当传入的值不符合预期时，返回400错误。
        """
        logger.warning(f"值错误: {str(error)} | 端点: {request.endpoint}")
        return error_response(
            error_message=f"参数值错误: {str(error)}",
            status_code=400,
            error_code='VALUE_ERROR'
        )


    @app.errorhandler(TypeError)
    def handle_type_error(error: TypeError) -> Tuple[Any, int]:
        """
        处理类型错误

        当类型不匹配时，返回400错误。
        """
        logger.warning(f"类型错误: {str(error)} | 端点: {request.endpoint}")
        return error_response(
            error_message="参数类型错误",
            status_code=400,
            error_code='TYPE_ERROR'
        )


    @app.errorhandler(KeyError)
    def handle_key_error(error: KeyError) -> Tuple[Any, int]:
        """
        处理键错误

        当访问不存在的键时，返回400错误。
        """
        logger.warning(f"键错误: {str(error)} | 端点: {request.endpoint}")
        return error_response(
            error_message=f"缺少必需的参数: {str(error)}",
            status_code=400,
            error_code='KEY_ERROR'
        )


    @app.errorhandler(FileNotFoundError)
    def handle_file_not_found_error(error: FileNotFoundError) -> Tuple[Any, int]:
        """
        处理文件不存在错误

        当访问的文件不存在时，返回404错误。
        """
        logger.warning(f"文件不存在: {str(error)}")
        return not_found_response("文件")


    @app.errorhandler(PermissionError)
    def handle_permission_error_builtin(error: PermissionError) -> Tuple[Any, int]:
        """
        处理内置权限错误

        当文件或系统权限不足时，返回403错误。
        """
        logger.error(f"系统权限错误: {str(error)}")
        return forbidden_response("系统权限不足")


    # 处理HTTP异常
    @app.errorhandler(400)
    def handle_bad_request(error) -> Tuple[Any, int]:
        """处理400错误"""
        logger.warning(f"400错误: {request.url} | IP: {request.remote_addr}")
        return error_response(
            error_message="请求格式错误",
            status_code=400,
            error_code='BAD_REQUEST'
        )


    @app.errorhandler(401)
    def handle_unauthorized(error) -> Tuple[Any, int]:
        """处理401错误"""
        logger.warning(f"401错误: {request.url} | IP: {request.remote_addr}")
        return unauthorized_response("需要身份验证")


    @app.errorhandler(403)
    def handle_forbidden(error) -> Tuple[Any, int]:
        """处理403错误"""
        logger.warning(f"403错误: {request.url} | IP: {request.remote_addr}")
        return forbidden_response("访问被禁止")


    @app.errorhandler(404)
    def handle_not_found(error) -> Tuple[Any, int]:
        """处理404错误"""
        logger.info(f"404错误: {request.url} | IP: {request.remote_addr}")
        return not_found_response("页面或资源")


    @app.errorhandler(405)
    def handle_method_not_allowed(error) -> Tuple[Any, int]:
        """处理405错误"""
        logger.warning(f"405错误: {request.method} {request.url}")
        return error_response(
            error_message=f"不支持的请求方法: {request.method}",
            status_code=405,
            error_code='METHOD_NOT_ALLOWED'
        )


    @app.errorhandler(413)
    def handle_payload_too_large(error) -> Tuple[Any, int]:
        """处理413错误（请求体过大）"""
        logger.warning(f"413错误: 请求体过大 | IP: {request.remote_addr}")
        return error_response(
            error_message="请求体过大",
            status_code=413,
            error_code='PAYLOAD_TOO_LARGE'
        )


    @app.errorhandler(429)
    def handle_too_many_requests(error) -> Tuple[Any, int]:
        """处理429错误（请求过多）"""
        logger.warning(f"429错误: 请求过多 | IP: {request.remote_addr}")
        return rate_limit_response()


    @app.errorhandler(500)
    def handle_internal_server_error(error) -> Tuple[Any, int]:
        """处理500错误"""
        logger.error(f"500错误: {str(error)} | URL: {request.url}", exc_info=True)
        return server_error_response()


    @app.errorhandler(502)
    def handle_bad_gateway(error) -> Tuple[Any, int]:
        """处理502错误"""
        logger.error(f"502错误: 网关错误 | URL: {request.url}")
        return server_error_response("网关错误，请稍后重试")


    @app.errorhandler(503)
    def handle_service_unavailable(error) -> Tuple[Any, int]:
        """处理503错误"""
        logger.error(f"503错误: 服务不可用 | URL: {request.url}")
        return server_error_response("服务暂时不可用，请稍后重试")


    # 通用异常处理器（兜底）
    @app.errorhandler(Exception)
    def handle_unexpected_error(error: Exception) -> Tuple[Any, int]:
        """
        处理未预期的异常

        这是最后的兜底处理器，捕获所有未被其他处理器处理的异常。
        """
        # 记录完整的错误堆栈
        logger.error(f"未预期的异常: {str(error)} | 类型: {type(error).__name__} | URL: {request.url}",
                    exc_info=True)

        # 在开发环境下可以返回详细错误信息，生产环境下返回通用错误
        if app.debug:
            return error_response(
                error_message=f"未预期的错误: {str(error)}",
                status_code=500,
                error_code='UNEXPECTED_ERROR',
                details={'error_type': type(error).__name__}
            )
        else:
            return server_error_response("服务器内部错误，请稍后重试")


def create_error_response_for_exception(exception: Exception) -> Tuple[Any, int]:
    """
    为异常创建错误响应的工具函数

    这个函数可以在代码中手动调用，为特定异常创建标准化的错误响应。

    Args:
        exception: 要处理的异常

    Returns:
        tuple: (响应JSON, 状态码)

    Example:
        try:
            # 一些可能出错的操作
            pass
        except ValueError as e:
            return create_error_response_for_exception(e)
    """
    if isinstance(exception, CustomBaseException):
        return error_response(
            error_message=exception.message,
            status_code=500,
            error_code=exception.error_code,
            details=exception.details
        )
    elif isinstance(exception, ValueError):
        return error_response(
            error_message=f"参数值错误: {str(exception)}",
            status_code=400,
            error_code='VALUE_ERROR'
        )
    elif isinstance(exception, TypeError):
        return error_response(
            error_message="参数类型错误",
            status_code=400,
            error_code='TYPE_ERROR'
        )
    elif isinstance(exception, KeyError):
        return error_response(
            error_message=f"缺少必需的参数: {str(exception)}",
            status_code=400,
            error_code='KEY_ERROR'
        )
    elif isinstance(exception, FileNotFoundError):
        return not_found_response("文件")
    else:
        logger.error(f"未知异常类型: {type(exception).__name__} | 消息: {str(exception)}")
        return server_error_response("服务器内部错误")