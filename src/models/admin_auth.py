# -*- coding: utf-8 -*-
"""
管理员认证模块
"""
import hashlib
import secrets
import json
import os
from datetime import datetime, timedelta
from typing import Optional, Dict
from ..utils.logger_config import get_logger

# 初始化日志记录器
logger = get_logger('admin_auth')


class AdminAuth:
    def __init__(self):
        self.admin_file = 'data/admin.json'
        self.sessions = {}  # 存储活跃会话
        self.session_timeout = 3600  # 1小时超时
        self._ensure_admin_file()
    
    def _ensure_admin_file(self):
        """确保管理员配置文件存在"""
        if not os.path.exists(self.admin_file):
            # 创建默认管理员账户
            default_admin = {
                "admins": {
                    "admin": {
                        "username": "admin",
                        "password_hash": self._hash_password("admin123"),
                        "created_at": datetime.now().isoformat(),
                        "last_login": None
                    }
                }
            }
            os.makedirs(os.path.dirname(self.admin_file), exist_ok=True)
            with open(self.admin_file, 'w', encoding='utf-8') as f:
                json.dump(default_admin, f, ensure_ascii=False, indent=2)
    
    def _hash_password(self, password: str) -> str:
        """密码哈希"""
        salt = "fruit_vegetable_admin_2024"
        return hashlib.sha256((password + salt).encode()).hexdigest()
    
    def login(self, username: str, password: str) -> Optional[str]:
        """管理员登录"""
        try:
            with open(self.admin_file, 'r', encoding='utf-8') as f:
                admin_data = json.load(f)
            
            if username in admin_data['admins']:
                admin = admin_data['admins'][username]
                if admin['password_hash'] == self._hash_password(password):
                    # 生成会话token
                    session_token = secrets.token_urlsafe(32)
                    self.sessions[session_token] = {
                        'username': username,
                        'login_time': datetime.now(),
                        'last_activity': datetime.now()
                    }
                    
                    # 更新最后登录时间
                    admin['last_login'] = datetime.now().isoformat()
                    with open(self.admin_file, 'w', encoding='utf-8') as f:
                        json.dump(admin_data, f, ensure_ascii=False, indent=2)
                    
                    return session_token
            
            return None
        except Exception as e:
            logger.error(f"登录错误: {e}")
            return None
    
    def verify_session(self, session_token: str) -> bool:
        """验证会话有效性"""
        if not session_token or session_token not in self.sessions:
            return False
        
        session = self.sessions[session_token]
        now = datetime.now()
        
        # 检查会话是否超时
        if (now - session['last_activity']).seconds > self.session_timeout:
            del self.sessions[session_token]
            return False
        
        # 更新最后活动时间
        session['last_activity'] = now
        return True
    
    def logout(self, session_token: str) -> bool:
        """管理员登出"""
        if session_token in self.sessions:
            del self.sessions[session_token]
            return True
        return False
    
    def get_session_info(self, session_token: str) -> Optional[Dict]:
        """获取会话信息"""
        if self.verify_session(session_token):
            return self.sessions[session_token]
        return None
    
    def change_password(self, username: str, old_password: str, new_password: str) -> bool:
        """修改密码"""
        try:
            with open(self.admin_file, 'r', encoding='utf-8') as f:
                admin_data = json.load(f)
            
            if username in admin_data['admins']:
                admin = admin_data['admins'][username]
                if admin['password_hash'] == self._hash_password(old_password):
                    admin['password_hash'] = self._hash_password(new_password)
                    
                    with open(self.admin_file, 'w', encoding='utf-8') as f:
                        json.dump(admin_data, f, ensure_ascii=False, indent=2)
                    
                    return True
            
            return False
        except Exception as e:
            logger.error(f"修改密码错误: {e}")
            return False
    
    def cleanup_expired_sessions(self):
        """清理过期会话"""
        now = datetime.now()
        expired_tokens = []
        
        for token, session in self.sessions.items():
            if (now - session['last_activity']).seconds > self.session_timeout:
                expired_tokens.append(token)
        
        for token in expired_tokens:
            del self.sessions[token]
