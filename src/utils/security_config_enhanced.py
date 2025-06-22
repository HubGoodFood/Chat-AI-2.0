# -*- coding: utf-8 -*-
"""
增强的安全配置模块
"""
import os
import secrets
import hashlib
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from flask import Flask
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_cors import CORS


class SecurityConfig:
    """增强的安全配置类"""
    
    def __init__(self):
        self.session_timeout = int(os.environ.get('SESSION_TIMEOUT', '3600'))  # 1小时
        self.max_login_attempts = int(os.environ.get('MAX_LOGIN_ATTEMPTS', '5'))
        self.login_attempt_timeout = int(os.environ.get('LOGIN_ATTEMPT_TIMEOUT', '300'))  # 5分钟
        self.failed_attempts = {}  # 失败登录尝试记录
    
    def init_app(self, app: Flask):
        """初始化Flask应用的安全配置"""
        # 1. 设置安全的SECRET_KEY
        self._setup_secret_key(app)
        
        # 2. 设置安全的会话配置
        self._setup_session_config(app)
        
        # 3. 设置CORS
        self._setup_cors(app)
        
        # 4. 设置速率限制
        self._setup_rate_limiting(app)
        
        # 5. 设置安全头
        self._setup_security_headers(app)
    
    def _setup_secret_key(self, app: Flask):
        """设置安全的密钥"""
        secret_key = os.environ.get('SECRET_KEY')
        
        if not secret_key:
            if app.config.get('FLASK_ENV') == 'production':
                raise ValueError("生产环境必须设置SECRET_KEY环境变量")
            else:
                # 开发环境生成临时密钥
                secret_key = secrets.token_urlsafe(32)
                print(f"[WARNING] 开发环境使用临时密钥，生产环境请设置SECRET_KEY环境变量")
        
        # 验证密钥强度
        if len(secret_key) < 32:
            raise ValueError("SECRET_KEY长度必须至少32个字符")
        
        app.secret_key = secret_key
    
    def _setup_session_config(self, app: Flask):
        """设置安全的会话配置"""
        # 会话安全配置
        app.config['SESSION_COOKIE_SECURE'] = os.environ.get('FLASK_ENV') == 'production'
        app.config['SESSION_COOKIE_HTTPONLY'] = True
        app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
        app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(seconds=self.session_timeout)
        
        # 会话加密
        app.config['SESSION_COOKIE_NAME'] = 'fruit_ai_session'
    
    def _setup_cors(self, app: Flask):
        """设置CORS配置"""
        # 生产环境限制来源域名
        if os.environ.get('FLASK_ENV') == 'production':
            allowed_origins = os.environ.get('ALLOWED_ORIGINS', '').split(',')
            if not allowed_origins or allowed_origins == ['']:
                allowed_origins = []  # 空列表表示禁用CORS
        else:
            allowed_origins = ["*"]  # 开发环境允许所有来源

        CORS(app,
             origins=allowed_origins,
             supports_credentials=True,
             methods=['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'],
             allow_headers=['Content-Type', 'Authorization'])
    
    def _setup_rate_limiting(self, app: Flask):
        """设置速率限制"""
        try:
            # 默认使用内存存储，避免Redis连接问题
            limiter = Limiter(
                key_func=get_remote_address,
                default_limits=["1000 per hour", "100 per minute"]
            )
            limiter.init_app(app)

            app.limiter = limiter
            print("[INFO] 速率限制初始化成功 (内存存储)")

        except Exception as e:
            print(f"[WARNING] 速率限制初始化失败: {e}")
            # 如果连内存存储都失败，则跳过速率限制
            app.limiter = None
    
    def _setup_security_headers(self, app: Flask):
        """设置安全头"""
        @app.after_request
        def add_security_headers(response):
            # 防止XSS攻击
            response.headers['X-Content-Type-Options'] = 'nosniff'
            response.headers['X-Frame-Options'] = 'DENY'
            response.headers['X-XSS-Protection'] = '1; mode=block'
            
            # 内容安全策略
            csp = "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'"
            response.headers['Content-Security-Policy'] = csp
            
            # HSTS (仅在HTTPS下)
            if app.config.get('SESSION_COOKIE_SECURE'):
                response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
            
            return response
    
    def check_login_attempts(self, username: str, ip_address: str) -> bool:
        """检查登录尝试次数"""
        key = f"{username}:{ip_address}"
        current_time = datetime.utcnow()
        
        if key in self.failed_attempts:
            attempts_data = self.failed_attempts[key]
            
            # 检查是否在锁定期内
            if attempts_data['locked_until'] and current_time < attempts_data['locked_until']:
                return False
            
            # 重置过期的尝试记录
            if current_time - attempts_data['last_attempt'] > timedelta(minutes=10):
                del self.failed_attempts[key]
                return True
        
        return True
    
    def record_failed_login(self, username: str, ip_address: str):
        """记录失败的登录尝试"""
        key = f"{username}:{ip_address}"
        current_time = datetime.utcnow()
        
        if key not in self.failed_attempts:
            self.failed_attempts[key] = {
                'count': 0,
                'first_attempt': current_time,
                'last_attempt': current_time,
                'locked_until': None
            }
        
        attempts_data = self.failed_attempts[key]
        attempts_data['count'] += 1
        attempts_data['last_attempt'] = current_time
        
        # 如果超过最大尝试次数，锁定账户
        if attempts_data['count'] >= self.max_login_attempts:
            attempts_data['locked_until'] = current_time + timedelta(seconds=self.login_attempt_timeout)
    
    def reset_login_attempts(self, username: str, ip_address: str):
        """重置登录尝试记录（成功登录后）"""
        key = f"{username}:{ip_address}"
        if key in self.failed_attempts:
            del self.failed_attempts[key]
    
    def generate_secure_token(self, length: int = 32) -> str:
        """生成安全的令牌"""
        return secrets.token_urlsafe(length)
    
    def hash_password(self, password: str, salt: Optional[str] = None) -> tuple[str, str]:
        """安全的密码哈希"""
        if not salt:
            salt = secrets.token_hex(16)
        
        # 使用PBKDF2进行密码哈希
        password_hash = hashlib.pbkdf2_hmac(
            'sha256',
            password.encode('utf-8'),
            salt.encode('utf-8'),
            100000  # 迭代次数
        ).hex()
        
        return password_hash, salt
    
    def verify_password(self, password: str, stored_hash: str, salt: str) -> bool:
        """验证密码"""
        computed_hash, _ = self.hash_password(password, salt)
        return secrets.compare_digest(computed_hash, stored_hash)


# 全局安全配置实例
security_config = SecurityConfig()


def validate_file_upload(file, allowed_extensions: set, max_size: int = 5242880) -> tuple[bool, str]:
    """验证文件上传"""
    if not file or file.filename == '':
        return False, "没有选择文件"
    
    # 检查文件扩展名
    if '.' not in file.filename:
        return False, "文件没有扩展名"
    
    ext = file.filename.rsplit('.', 1)[1].lower()
    if ext not in allowed_extensions:
        return False, f"不支持的文件类型，仅支持: {', '.join(allowed_extensions)}"
    
    # 检查文件大小
    file_size = len(file.read())
    file.seek(0)  # 重置文件指针
    
    if file_size > max_size:
        return False, f"文件大小超过限制 ({max_size / 1024 / 1024:.1f}MB)"
    
    return True, "文件验证通过"


def sanitize_filename(filename: str) -> str:
    """清理文件名"""
    import re
    from werkzeug.utils import secure_filename
    
    # 移除路径分隔符和特殊字符
    filename = secure_filename(filename)
    
    # 移除Unicode字符（如果需要）
    filename = re.sub(r'[^\w\-_\.]', '', filename)
    
    # 限制长度
    if len(filename) > 100:
        name, ext = filename.rsplit('.', 1) if '.' in filename else (filename, '')
        filename = name[:95] + ('.' + ext if ext else '')
    
    return filename