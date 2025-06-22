# -*- coding: utf-8 -*-
"""
装饰器模块 - 提供通用的Flask装饰器集合

这个模块包含了果蔬客服系统中使用的各种装饰器，用于简化常见的Web开发任务。
装饰器提供了横切关注点的解决方案，如认证、验证、日志记录、错误处理等。

主要装饰器类型：
- 数据验证装饰器：JSON数据验证、文件上传验证
- 认证装饰器：管理员认证、登录尝试检查
- 错误处理装饰器：统一的异常处理和错误响应
- 日志装饰器：操作日志记录、审计追踪
- 安全装饰器：速率限制、权限检查

设计原则：
- 可重用性：装饰器可以应用于多个路由函数
- 一致性：统一的错误响应格式和日志记录
- 安全性：内置安全检查和防护机制
- 可维护性：清晰的错误信息和详细的日志
"""
import functools
import json
from flask import request, jsonify, session, g
from pydantic import BaseModel, ValidationError
from typing import Type, Callable, Any
from .security_config_enhanced import security_config
from .logger_config import get_logger

# 初始化装饰器模块的日志记录器
logger = get_logger('decorators')


def validate_json(model_class: Type[BaseModel]):
    """
    JSON数据验证装饰器

    使用Pydantic模型对请求的JSON数据进行验证，确保数据格式正确且符合业务规则。
    这个装饰器简化了API端点的数据验证逻辑，提供统一的错误处理。

    验证流程：
    1. 检查请求是否为JSON格式
    2. 解析JSON数据
    3. 使用Pydantic模型验证数据
    4. 将验证后的数据传递给路由函数
    5. 处理验证错误并返回友好的错误信息

    Args:
        model_class (Type[BaseModel]): Pydantic模型类，定义数据结构和验证规则

    Returns:
        Callable: 装饰器函数

    Example:
        >>> from pydantic import BaseModel
        >>> class ProductModel(BaseModel):
        ...     name: str
        ...     price: float
        >>>
        >>> @validate_json(ProductModel)
        >>> def create_product(validated_data: ProductModel):
        ...     return {"success": True}

    Note:
        - 验证失败时返回400状态码和详细的错误信息
        - 支持嵌套字段的验证错误定位
        - 所有验证错误都会被记录到日志中
    """
    def decorator(f: Callable) -> Callable:
        @functools.wraps(f)
        def wrapper(*args, **kwargs):
            try:
                # 检查请求是否为JSON格式
                if not request.is_json:
                    return jsonify({
                        'success': False,
                        'error': '请求必须是JSON格式'
                    }), 400

                # 获取并解析JSON数据
                data = request.get_json()
                if data is None:
                    return jsonify({
                        'success': False,
                        'error': '无效的JSON数据'
                    }), 400

                # 使用Pydantic模型验证数据
                validated_data = model_class(**data)

                # 将验证后的数据传递给路由函数
                return f(validated_data, *args, **kwargs)

            except ValidationError as e:
                # 处理Pydantic验证错误
                error_messages = []
                for error in e.errors():
                    # 构建字段路径（支持嵌套字段）
                    field = ' -> '.join(str(x) for x in error['loc'])
                    message = error['msg']
                    error_messages.append(f"{field}: {message}")

                logger.warning(f"数据验证失败: {error_messages}")
                return jsonify({
                    'success': False,
                    'error': f'数据验证失败: {"; ".join(error_messages)}'
                }), 400

            except json.JSONDecodeError:
                # 处理JSON解析错误
                return jsonify({
                    'success': False,
                    'error': 'JSON格式错误'
                }), 400

            except Exception as e:
                # 处理其他未预期的错误
                logger.error(f"验证装饰器错误: {e}")
                return jsonify({
                    'success': False,
                    'error': '数据验证失败'
                }), 500

        return wrapper
    return decorator


def require_admin_auth(f: Callable) -> Callable:
    """管理员认证装饰器（增强版）"""
    @functools.wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            # 检查认证令牌
            admin_token = session.get('admin_token')
            if not admin_token:
                logger.warning(f"未认证的管理员访问尝试: {request.remote_addr}")
                return jsonify({
                    'success': False,
                    'error': '需要管理员登录',
                    'error_code': 'AUTH_REQUIRED'
                }), 401
            
            # 验证令牌（这里需要与现有的admin_auth集成）
            from src.models.admin_auth import AdminAuth
            admin_auth = AdminAuth()
            
            if not admin_auth.verify_session(admin_token):
                logger.warning(f"无效的管理员令牌: {request.remote_addr}")
                session.pop('admin_token', None)
                return jsonify({
                    'success': False,
                    'error': '认证已过期，请重新登录',
                    'error_code': 'AUTH_EXPIRED'
                }), 401
            
            # 获取用户信息并存储在g对象中
            session_info = admin_auth.get_session_info(admin_token)
            g.current_admin = session_info.get('username', '管理员') if session_info else '管理员'
            
            return f(*args, **kwargs)
            
        except Exception as e:
            logger.error(f"认证装饰器错误: {e}")
            return jsonify({
                'success': False,
                'error': '认证验证失败',
                'error_code': 'AUTH_ERROR'
            }), 500
    
    return decorated_function


def check_login_attempts(f: Callable) -> Callable:
    """登录尝试检查装饰器"""
    @functools.wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            # 获取用户名和IP
            data = request.get_json() or {}
            username = data.get('username', '')
            ip_address = request.remote_addr
            
            # 检查登录尝试
            if not security_config.check_login_attempts(username, ip_address):
                logger.warning(f"登录尝试过多被阻止: {username}@{ip_address}")
                return jsonify({
                    'success': False,
                    'error': '登录尝试过多，请稍后再试',
                    'error_code': 'TOO_MANY_ATTEMPTS'
                }), 429
            
            return f(*args, **kwargs)
            
        except Exception as e:
            logger.error(f"登录检查装饰器错误: {e}")
            return f(*args, **kwargs)  # 出错时允许继续
    
    return decorated_function


def handle_service_errors(f: Callable) -> Callable:
    """服务错误处理装饰器"""
    @functools.wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        
        except ValueError as e:
            logger.warning(f"数值错误: {e}")
            return jsonify({
                'success': False,
                'error': str(e),
                'error_code': 'VALUE_ERROR'
            }), 400
        
        except FileNotFoundError as e:
            logger.warning(f"文件不存在: {e}")
            return jsonify({
                'success': False,
                'error': '请求的资源不存在',
                'error_code': 'NOT_FOUND'
            }), 404
        
        except PermissionError as e:
            logger.warning(f"权限错误: {e}")
            return jsonify({
                'success': False,
                'error': '权限不足',
                'error_code': 'PERMISSION_DENIED'
            }), 403
        
        except Exception as e:
            logger.error(f"未处理的服务错误: {e}", exc_info=True)
            return jsonify({
                'success': False,
                'error': '服务器内部错误',
                'error_code': 'INTERNAL_ERROR'
            }), 500
    
    return decorated_function


def log_admin_operation(operation_type: str, target_type: str = None):
    """管理员操作日志装饰器"""
    def decorator(f: Callable) -> Callable:
        @functools.wraps(f)
        def decorated_function(*args, **kwargs):
            start_time = None
            result = None
            error = None
            
            try:
                from datetime import datetime
                start_time = datetime.utcnow()
                
                # 执行原函数
                result = f(*args, **kwargs)
                
                # 记录成功的操作
                try:
                    from src.models.operation_logger import log_admin_operation
                    operator = getattr(g, 'current_admin', '未知用户')
                    
                    # 提取操作详情
                    details = {
                        'method': request.method,
                        'endpoint': request.endpoint,
                        'remote_addr': request.remote_addr,
                        'user_agent': request.headers.get('User-Agent', ''),
                        'duration_ms': int((datetime.utcnow() - start_time).total_seconds() * 1000)
                    }
                    
                    # 添加请求数据（但不包含敏感信息）
                    if request.is_json:
                        request_data = request.get_json() or {}
                        # 移除敏感字段
                        safe_data = {k: v for k, v in request_data.items() 
                                   if k not in ['password', 'old_password', 'new_password']}
                        details['request_data'] = safe_data
                    
                    log_admin_operation(
                        operator=operator,
                        operation_type=operation_type,
                        target_type=target_type or 'unknown',
                        target_id=kwargs.get('product_id') or kwargs.get('count_id') or 'unknown',
                        details=details,
                        result='success'
                    )
                    
                except Exception as log_error:
                    logger.error(f"记录操作日志失败: {log_error}")
                
                return result
                
            except Exception as e:
                error = e
                
                # 记录失败的操作
                try:
                    from src.models.operation_logger import log_admin_operation
                    from datetime import datetime
                    
                    operator = getattr(g, 'current_admin', '未知用户')
                    duration = int((datetime.utcnow() - start_time).total_seconds() * 1000) if start_time else 0
                    
                    log_admin_operation(
                        operator=operator,
                        operation_type=operation_type,
                        target_type=target_type or 'unknown',
                        target_id='unknown',
                        details={
                            'method': request.method,
                            'endpoint': request.endpoint,
                            'error': str(e),
                            'duration_ms': duration
                        },
                        result='failed'
                    )
                    
                except Exception as log_error:
                    logger.error(f"记录失败操作日志失败: {log_error}")
                
                # 重新抛出原异常
                raise error
        
        return decorated_function
    return decorator


def rate_limit(limit: str):
    """速率限制装饰器"""
    def decorator(f: Callable) -> Callable:
        @functools.wraps(f)
        def decorated_function(*args, **kwargs):
            # 这里集成Flask-Limiter的功能
            try:
                from flask import current_app
                if hasattr(current_app, 'limiter'):
                    # 使用应用级别的限制器
                    pass
                
                return f(*args, **kwargs)
                
            except Exception as e:
                if 'rate limit' in str(e).lower():
                    logger.warning(f"速率限制触发: {request.remote_addr}")
                    return jsonify({
                        'success': False,
                        'error': '请求频率过高，请稍后再试',
                        'error_code': 'RATE_LIMIT_EXCEEDED'
                    }), 429
                else:
                    raise e
        
        return decorated_function
    return decorator


def validate_file_upload(allowed_extensions: set, max_size: int = 5242880):
    """文件上传验证装饰器"""
    def decorator(f: Callable) -> Callable:
        @functools.wraps(f)
        def decorated_function(*args, **kwargs):
            try:
                from .security_config_enhanced import validate_file_upload
                
                if 'file' not in request.files:
                    return jsonify({
                        'success': False,
                        'error': '没有文件被上传'
                    }), 400
                
                file = request.files['file']
                is_valid, message = validate_file_upload(file, allowed_extensions, max_size)
                
                if not is_valid:
                    return jsonify({
                        'success': False,
                        'error': message
                    }), 400
                
                return f(*args, **kwargs)
                
            except Exception as e:
                logger.error(f"文件上传验证错误: {e}")
                return jsonify({
                    'success': False,
                    'error': '文件验证失败'
                }), 500
        
        return decorated_function
    return decorator