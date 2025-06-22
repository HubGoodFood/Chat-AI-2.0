# -*- coding: utf-8 -*-
"""
API版本控制系统
"""
import logging
from typing import Dict, Any, Optional, Callable
from flask import Blueprint, request, jsonify, g
from functools import wraps
from ..core.response import ResponseBuilder
from ..core.exceptions import ValidationError

logger = logging.getLogger(__name__)


class APIVersionManager:
    """API版本管理器"""
    
    def __init__(self):
        self.supported_versions = {'v1': '1.0.0'}
        self.default_version = 'v1'
        self.deprecated_versions = set()
        self.version_blueprints: Dict[str, Blueprint] = {}
    
    def register_version(self, version: str, blueprint: Blueprint, version_number: str = None):
        """注册API版本"""
        self.version_blueprints[version] = blueprint
        if version_number:
            self.supported_versions[version] = version_number
        logger.info(f"注册API版本: {version} ({version_number or 'unknown'})")
    
    def deprecate_version(self, version: str):
        """标记版本为已弃用"""
        if version in self.supported_versions:
            self.deprecated_versions.add(version)
            logger.info(f"API版本已弃用: {version}")
    
    def get_version_from_request(self) -> str:
        """从请求中获取API版本"""
        # 优先级：URL路径 > Header > 查询参数 > 默认版本
        
        # 1. 从URL路径获取 /api/v1/...
        path_parts = request.path.split('/')
        if len(path_parts) >= 3 and path_parts[1] == 'api' and path_parts[2].startswith('v'):
            version = path_parts[2]
            if version in self.supported_versions:
                return version
        
        # 2. 从Header获取
        version = request.headers.get('API-Version')
        if version and version in self.supported_versions:
            return version
        
        # 3. 从查询参数获取
        version = request.args.get('version')
        if version and version in self.supported_versions:
            return version
        
        # 4. 返回默认版本
        return self.default_version
    
    def validate_version(self, version: str) -> bool:
        """验证版本是否支持"""
        return version in self.supported_versions
    
    def is_deprecated(self, version: str) -> bool:
        """检查版本是否已弃用"""
        return version in self.deprecated_versions
    
    def get_version_info(self) -> Dict[str, Any]:
        """获取版本信息"""
        return {
            'supported_versions': self.supported_versions,
            'default_version': self.default_version,
            'deprecated_versions': list(self.deprecated_versions)
        }


# 全局版本管理器实例
version_manager = APIVersionManager()


def api_version(required_version: str = None):
    """API版本控制装饰器"""
    def decorator(func: Callable):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # 获取请求的API版本
            requested_version = version_manager.get_version_from_request()
            
            # 验证版本
            if not version_manager.validate_version(requested_version):
                response = ResponseBuilder.error(
                    message=f"不支持的API版本: {requested_version}",
                    error_code="UNSUPPORTED_API_VERSION",
                    status_code=400
                )
                response.set_meta('supported_versions', list(version_manager.supported_versions.keys()))
                return response.to_json_response(400)
            
            # 检查是否为必需版本
            if required_version and requested_version != required_version:
                response = ResponseBuilder.error(
                    message=f"此端点需要API版本 {required_version}，当前版本: {requested_version}",
                    error_code="INCOMPATIBLE_API_VERSION",
                    status_code=400
                )
                return response.to_json_response(400)
            
            # 设置版本信息到请求上下文
            g.api_version = requested_version
            g.api_version_number = version_manager.supported_versions.get(requested_version)
            
            # 检查是否为弃用版本
            if version_manager.is_deprecated(requested_version):
                logger.warning(f"使用已弃用的API版本: {requested_version}")
                # 在响应头中添加弃用警告（在实际响应中处理）
            
            return func(*args, **kwargs)
        
        return wrapper
    return decorator


def version_aware_response(response_data: Any, status_code: int = 200):
    """版本感知的响应"""
    response = jsonify(response_data)
    response.status_code = status_code
    
    # 添加版本信息到响应头
    if hasattr(g, 'api_version'):
        response.headers['API-Version'] = g.api_version
        response.headers['API-Version-Number'] = g.api_version_number or 'unknown'
        
        # 如果是弃用版本，添加警告头
        if version_manager.is_deprecated(g.api_version):
            response.headers['Warning'] = f'299 - "API version {g.api_version} is deprecated"'
    
    return response


def create_versioned_blueprint(name: str, import_name: str, version: str, **kwargs) -> Blueprint:
    """创建版本化的Blueprint"""
    url_prefix = kwargs.pop('url_prefix', f'/api/{version}')
    blueprint = Blueprint(f"{name}_{version}", import_name, url_prefix=url_prefix, **kwargs)
    
    # 注册到版本管理器
    version_manager.register_version(version, blueprint)
    
    return blueprint


class APIVersionMiddleware:
    """API版本中间件"""
    
    def __init__(self, app=None):
        self.app = app
        if app:
            self.init_app(app)
    
    def init_app(self, app):
        """初始化应用"""
        app.before_request(self.before_request)
        app.after_request(self.after_request)
    
    def before_request(self):
        """请求前处理"""
        # 设置API版本信息
        if request.path.startswith('/api/'):
            version = version_manager.get_version_from_request()
            g.api_version = version
            g.api_version_number = version_manager.supported_versions.get(version)
    
    def after_request(self, response):
        """请求后处理"""
        # 添加版本信息到响应头
        if hasattr(g, 'api_version') and request.path.startswith('/api/'):
            response.headers['API-Version'] = g.api_version
            response.headers['API-Version-Number'] = g.api_version_number or 'unknown'
            
            # 弃用版本警告
            if version_manager.is_deprecated(g.api_version):
                response.headers['Warning'] = f'299 - "API version {g.api_version} is deprecated"'
            
            # 添加支持的版本信息
            response.headers['API-Supported-Versions'] = ','.join(version_manager.supported_versions.keys())
        
        return response


def get_current_api_version() -> Optional[str]:
    """获取当前请求的API版本"""
    return getattr(g, 'api_version', None)


def get_current_version_number() -> Optional[str]:
    """获取当前API版本号"""
    return getattr(g, 'api_version_number', None)


def require_api_version(version: str):
    """要求特定API版本的装饰器"""
    return api_version(required_version=version)


# 便利函数
def register_api_blueprint(app, blueprint: Blueprint, version: str, version_number: str = None):
    """注册API Blueprint"""
    app.register_blueprint(blueprint)
    version_manager.register_version(version, blueprint, version_number)
    logger.info(f"注册API Blueprint: {blueprint.name} (版本: {version})")