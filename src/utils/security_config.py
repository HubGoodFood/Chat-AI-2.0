"""
安全配置模块 - 统一管理应用安全设置
"""
import os
import re
from flask import request, jsonify
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_cors import CORS
from typing import Dict, List, Optional


class SecurityConfig:
    """安全配置管理类"""
    
    def __init__(self, app=None):
        self.app = app
        self.limiter = None
        self.cors = None
        
        # 安全配置参数
        self.rate_limit_default = os.environ.get('RATE_LIMIT_DEFAULT', '60/minute')
        self.rate_limit_admin = os.environ.get('RATE_LIMIT_ADMIN', '30/minute')
        self.rate_limit_api = os.environ.get('RATE_LIMIT_API', '100/minute')
        
        # CORS配置
        self.cors_origins = self._parse_cors_origins()
        self.cors_methods = ['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS']
        self.cors_headers = ['Content-Type', 'Authorization', 'X-Requested-With']
        
        # 请求验证配置
        self.max_content_length = int(os.environ.get('MAX_CONTENT_LENGTH', '16777216'))  # 16MB
        self.max_json_payload_size = int(os.environ.get('MAX_JSON_PAYLOAD_SIZE', '1048576'))  # 1MB
        
        if app:
            self.init_app(app)
    
    def _parse_cors_origins(self) -> List[str]:
        """解析CORS允许的来源"""
        origins_str = os.environ.get('CORS_ORIGINS', 'http://localhost:5000,http://127.0.0.1:5000')
        
        # 避免使用通配符*，提供具体的域名列表
        if origins_str == '*':
            print("警告：CORS配置使用通配符，建议在生产环境中指定具体域名")
            return ['*']
        
        origins = [origin.strip() for origin in origins_str.split(',') if origin.strip()]
        return origins if origins else ['http://localhost:5000']
    
    def init_app(self, app):
        """初始化Flask应用的安全配置"""
        self.app = app
        
        # 配置请求大小限制
        app.config['MAX_CONTENT_LENGTH'] = self.max_content_length
        
        # 初始化速率限制器
        self._init_rate_limiter(app)
        
        # 初始化CORS
        self._init_cors(app)
        
        # 注册安全中间件
        self._register_security_middleware(app)

        print("安全配置初始化完成")
    
    def _init_rate_limiter(self, app):
        """初始化速率限制器"""
        try:
            self.limiter = Limiter(
                app=app,
                key_func=get_remote_address,
                default_limits=[self.rate_limit_default],
                storage_uri="memory://",  # 使用内存存储，生产环境建议使用Redis
                strategy="fixed-window"
            )
            print(f"速率限制器配置成功 - 默认限制: {self.rate_limit_default}")
        except Exception as e:
            print(f"速率限制器初始化失败: {e}")
    
    def _init_cors(self, app):
        """初始化CORS配置"""
        try:
            self.cors = CORS(
                app,
                origins=self.cors_origins,
                methods=self.cors_methods,
                allow_headers=self.cors_headers,
                supports_credentials=True,
                max_age=3600  # 预检请求缓存1小时
            )
            print(f"CORS配置成功 - 允许来源: {self.cors_origins}")
        except Exception as e:
            print(f"CORS初始化失败: {e}")
    
    def _register_security_middleware(self, app):
        """注册安全中间件"""
        
        @app.before_request
        def security_headers():
            """添加安全响应头"""
            # 检查请求大小
            if request.content_length and request.content_length > self.max_content_length:
                return jsonify({
                    'success': False,
                    'error': '请求数据过大'
                }), 413
            
            # 检查JSON负载大小
            if request.is_json and request.content_length:
                if request.content_length > self.max_json_payload_size:
                    return jsonify({
                        'success': False,
                        'error': 'JSON数据过大'
                    }), 413
        
        @app.after_request
        def add_security_headers(response):
            """添加安全响应头"""
            # 防止点击劫持
            response.headers['X-Frame-Options'] = 'DENY'
            
            # 防止MIME类型嗅探
            response.headers['X-Content-Type-Options'] = 'nosniff'
            
            # XSS保护
            response.headers['X-XSS-Protection'] = '1; mode=block'
            
            # 引用策略
            response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
            
            # 内容安全策略（基础版本）
            response.headers['Content-Security-Policy'] = (
                "default-src 'self'; "
                "script-src 'self' 'unsafe-inline'; "
                "style-src 'self' 'unsafe-inline'; "
                "img-src 'self' data: https:; "
                "font-src 'self' https:; "
                "connect-src 'self'"
            )
            
            return response
    
    def validate_input(self, data: str, max_length: int = 1000, 
                      allow_html: bool = False) -> tuple[bool, str]:
        """
        输入验证和清理
        
        Args:
            data: 输入数据
            max_length: 最大长度
            allow_html: 是否允许HTML标签
            
        Returns:
            (is_valid, cleaned_data)
        """
        if not data:
            return True, ""
        
        # 长度检查
        if len(data) > max_length:
            return False, "输入数据过长"
        
        # 基本的恶意内容检测
        malicious_patterns = [
            r'<script[^>]*>.*?</script>',  # 脚本标签
            r'javascript:',               # JavaScript协议
            r'on\w+\s*=',                # 事件处理器
            r'eval\s*\(',                # eval函数
            r'expression\s*\(',          # CSS表达式
        ]
        
        for pattern in malicious_patterns:
            if re.search(pattern, data, re.IGNORECASE):
                return False, "检测到潜在的恶意内容"
        
        # HTML标签清理
        if not allow_html:
            # 移除HTML标签
            cleaned_data = re.sub(r'<[^>]+>', '', data)
        else:
            cleaned_data = data
        
        # 基本的SQL注入检测
        sql_patterns = [
            r'\b(union|select|insert|update|delete|drop|create|alter)\b',
            r'[\'";]',  # 引号和分号
            r'--',      # SQL注释
            r'/\*.*?\*/',  # 多行注释
        ]
        
        for pattern in sql_patterns:
            if re.search(pattern, cleaned_data, re.IGNORECASE):
                return False, "检测到潜在的SQL注入"
        
        return True, cleaned_data.strip()
    
    def is_admin_request(self, request_path: str) -> bool:
        """检查是否为管理员请求"""
        admin_patterns = [
            r'^/admin/',
            r'^/api/admin/',
        ]
        
        for pattern in admin_patterns:
            if re.match(pattern, request_path):
                return True
        return False
    
    def get_rate_limit_for_endpoint(self, endpoint: str) -> str:
        """根据端点获取相应的速率限制"""
        if self.is_admin_request(endpoint):
            return self.rate_limit_admin
        elif endpoint.startswith('/api/'):
            return self.rate_limit_api
        else:
            return self.rate_limit_default


# 全局安全配置实例
security_config = SecurityConfig()


def require_valid_input(max_length: int = 1000, allow_html: bool = False):
    """输入验证装饰器"""
    def decorator(f):
        def wrapper(*args, **kwargs):
            if request.is_json:
                data = request.get_json()
                if isinstance(data, dict):
                    for key, value in data.items():
                        if isinstance(value, str):
                            is_valid, result = security_config.validate_input(
                                value, max_length, allow_html
                            )
                            if not is_valid:
                                return jsonify({
                                    'success': False,
                                    'error': f'输入验证失败: {result}'
                                }), 400
            
            return f(*args, **kwargs)
        
        wrapper.__name__ = f.__name__
        return wrapper
    return decorator
