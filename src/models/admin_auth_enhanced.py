# -*- coding: utf-8 -*-
"""
增强的管理员认证模块
"""
import json
import os
from datetime import datetime
from typing import Optional, Dict
from flask import request
from ..utils.logger_config import get_logger
from ..utils.security_config_enhanced import security_config
from ..utils.session_manager import session_manager

# 初始化日志记录器
logger = get_logger('admin_auth_enhanced')


class AdminAuthEnhanced:
    """增强的管理员认证类"""
    
    def __init__(self):
        self.admin_file = 'data/admin.json'
        self._ensure_admin_file()
    
    def _ensure_admin_file(self):
        """确保管理员文件存在"""
        os.makedirs(os.path.dirname(self.admin_file), exist_ok=True)
        
        if not os.path.exists(self.admin_file):
            # 创建默认管理员账户，使用强密码哈希
            password_hash, salt = security_config.hash_password("admin123")
            
            default_admin = {
                "admins": {
                    "admin": {
                        "username": "admin",
                        "password_hash": password_hash,
                        "salt": salt,
                        "created_at": datetime.now().isoformat(),
                        "last_login": None,
                        "password_changed": False,  # 标记需要修改默认密码
                        "login_attempts": 0,
                        "last_attempt": None,
                        "locked_until": None
                    }
                }
            }
            
            with open(self.admin_file, 'w', encoding='utf-8') as f:
                json.dump(default_admin, f, ensure_ascii=False, indent=2)
            
            logger.info("创建默认管理员账户: admin/admin123")
            logger.warning("请在生产环境中立即修改默认密码！")
    
    def login(self, username: str, password: str) -> Optional[str]:
        """管理员登录（增强版）"""
        try:
            # 获取请求信息
            ip_address = request.remote_addr if request else 'unknown'
            user_agent = request.headers.get('User-Agent', '') if request else ''
            
            # 加载管理员数据
            with open(self.admin_file, 'r', encoding='utf-8') as f:
                admin_data = json.load(f)
            
            # 检查用户是否存在
            if username not in admin_data.get('admins', {}):
                logger.warning(f"登录失败 - 用户不存在: {username}@{ip_address}")
                return None
            
            user_data = admin_data['admins'][username]
            
            # 检查账户是否被锁定
            if self._is_account_locked(user_data):
                logger.warning(f"登录失败 - 账户被锁定: {username}@{ip_address}")
                return None
            
            # 验证密码
            stored_hash = user_data['password_hash']
            salt = user_data.get('salt')
            
            if salt:
                # 新版本的密码验证
                is_valid = security_config.verify_password(password, stored_hash, salt)
            else:
                # 兼容旧版本的密码验证
                old_hash = self._legacy_hash_password(password)
                is_valid = stored_hash == old_hash
                
                # 如果验证通过，升级到新的密码格式
                if is_valid:
                    new_hash, new_salt = security_config.hash_password(password)
                    user_data['password_hash'] = new_hash
                    user_data['salt'] = new_salt
                    self._save_admin_data(admin_data)
                    logger.info(f"升级用户密码格式: {username}")
            
            if is_valid:
                # 登录成功
                session_id = session_manager.create_admin_session(
                    username, ip_address, user_agent
                )
                
                if session_id:
                    # 更新用户登录信息
                    user_data['last_login'] = datetime.now().isoformat()
                    user_data['login_attempts'] = 0
                    user_data['last_attempt'] = None
                    user_data['locked_until'] = None
                    self._save_admin_data(admin_data)
                    
                    logger.info(f"管理员登录成功: {username}@{ip_address}")
                    
                    # 检查是否需要修改默认密码
                    if not user_data.get('password_changed', True):
                        logger.warning(f"管理员使用默认密码: {username}")
                    
                    return session_id
                else:
                    logger.error(f"创建会话失败: {username}@{ip_address}")
                    return None
            else:
                # 登录失败
                self._record_failed_attempt(admin_data, username)
                logger.warning(f"管理员登录失败 - 密码错误: {username}@{ip_address}")
                return None
                
        except Exception as e:
            logger.error(f"管理员登录异常: {e}")
            return None
    
    def verify_session(self, session_id: str) -> bool:
        """验证会话"""
        try:
            session_data = session_manager.verify_admin_session(session_id)
            return session_data is not None
        except Exception as e:
            logger.error(f"验证会话异常: {e}")
            return False
    
    def get_session_info(self, session_id: str) -> Optional[Dict]:
        """获取会话信息"""
        try:
            return session_manager.verify_admin_session(session_id, update_activity=False)
        except Exception as e:
            logger.error(f"获取会话信息异常: {e}")
            return None
    
    def logout(self, session_id: str) -> bool:
        """管理员登出"""
        try:
            result = session_manager.delete_admin_session(session_id)
            if result:
                logger.info(f"管理员登出成功: {session_id}")
            return result
        except Exception as e:
            logger.error(f"管理员登出异常: {e}")
            return False
    
    def change_password(self, username: str, old_password: str, new_password: str) -> bool:
        """修改密码"""
        try:
            # 加载管理员数据
            with open(self.admin_file, 'r', encoding='utf-8') as f:
                admin_data = json.load(f)
            
            # 检查用户是否存在
            if username not in admin_data.get('admins', {}):
                logger.warning(f"修改密码失败 - 用户不存在: {username}")
                return False
            
            user_data = admin_data['admins'][username]
            
            # 验证旧密码
            stored_hash = user_data['password_hash']
            salt = user_data.get('salt')
            
            if salt:
                is_valid = security_config.verify_password(old_password, stored_hash, salt)
            else:
                # 兼容旧版本
                old_hash = self._legacy_hash_password(old_password)
                is_valid = stored_hash == old_hash
            
            if not is_valid:
                logger.warning(f"修改密码失败 - 旧密码错误: {username}")
                return False
            
            # 设置新密码
            new_hash, new_salt = security_config.hash_password(new_password)
            user_data['password_hash'] = new_hash
            user_data['salt'] = new_salt
            user_data['password_changed'] = True
            user_data['password_updated_at'] = datetime.now().isoformat()
            
            # 保存数据
            self._save_admin_data(admin_data)
            
            logger.info(f"密码修改成功: {username}")
            return True
            
        except Exception as e:
            logger.error(f"修改密码异常: {e}")
            return False
    
    def create_admin(self, username: str, password: str, creator: str) -> bool:
        """创建新管理员"""
        try:
            # 加载管理员数据
            with open(self.admin_file, 'r', encoding='utf-8') as f:
                admin_data = json.load(f)
            
            # 检查用户是否已存在
            if username in admin_data.get('admins', {}):
                logger.warning(f"创建管理员失败 - 用户已存在: {username}")
                return False
            
            # 创建新用户
            password_hash, salt = security_config.hash_password(password)
            
            admin_data['admins'][username] = {
                "username": username,
                "password_hash": password_hash,
                "salt": salt,
                "created_at": datetime.now().isoformat(),
                "created_by": creator,
                "last_login": None,
                "password_changed": True,
                "login_attempts": 0,
                "last_attempt": None,
                "locked_until": None
            }
            
            # 保存数据
            self._save_admin_data(admin_data)
            
            logger.info(f"创建管理员成功: {username} (创建者: {creator})")
            return True
            
        except Exception as e:
            logger.error(f"创建管理员异常: {e}")
            return False
    
    def delete_admin(self, username: str, deleter: str) -> bool:
        """删除管理员"""
        try:
            # 加载管理员数据
            with open(self.admin_file, 'r', encoding='utf-8') as f:
                admin_data = json.load(f)
            
            # 检查用户是否存在
            if username not in admin_data.get('admins', {}):
                logger.warning(f"删除管理员失败 - 用户不存在: {username}")
                return False
            
            # 不能删除自己
            if username == deleter:
                logger.warning(f"删除管理员失败 - 不能删除自己: {username}")
                return False
            
            # 不能删除最后一个管理员
            if len(admin_data['admins']) <= 1:
                logger.warning(f"删除管理员失败 - 不能删除最后一个管理员: {username}")
                return False
            
            # 删除用户
            del admin_data['admins'][username]
            
            # 保存数据
            self._save_admin_data(admin_data)
            
            logger.info(f"删除管理员成功: {username} (删除者: {deleter})")
            return True
            
        except Exception as e:
            logger.error(f"删除管理员异常: {e}")
            return False
    
    def get_admin_list(self) -> list:
        """获取管理员列表"""
        try:
            with open(self.admin_file, 'r', encoding='utf-8') as f:
                admin_data = json.load(f)
            
            admin_list = []
            for username, user_data in admin_data.get('admins', {}).items():
                admin_list.append({
                    'username': username,
                    'created_at': user_data.get('created_at'),
                    'last_login': user_data.get('last_login'),
                    'password_changed': user_data.get('password_changed', True),
                    'is_locked': self._is_account_locked(user_data)
                })
            
            return admin_list
            
        except Exception as e:
            logger.error(f"获取管理员列表异常: {e}")
            return []
    
    def _is_account_locked(self, user_data: Dict) -> bool:
        """检查账户是否被锁定"""
        try:
            locked_until = user_data.get('locked_until')
            if not locked_until:
                return False
            
            lock_time = datetime.fromisoformat(locked_until)
            return datetime.now() < lock_time
            
        except Exception:
            return False
    
    def _record_failed_attempt(self, admin_data: Dict, username: str):
        """记录失败尝试"""
        try:
            user_data = admin_data['admins'][username]
            user_data['login_attempts'] = user_data.get('login_attempts', 0) + 1
            user_data['last_attempt'] = datetime.now().isoformat()
            
            # 如果失败次数过多，锁定账户
            max_attempts = 5
            lock_minutes = 15
            
            if user_data['login_attempts'] >= max_attempts:
                lock_until = datetime.now() + timedelta(minutes=lock_minutes)
                user_data['locked_until'] = lock_until.isoformat()
                logger.warning(f"账户被锁定 {lock_minutes} 分钟: {username}")
            
            self._save_admin_data(admin_data)
            
        except Exception as e:
            logger.error(f"记录失败尝试异常: {e}")
    
    def _save_admin_data(self, admin_data: Dict):
        """保存管理员数据"""
        try:
            with open(self.admin_file, 'w', encoding='utf-8') as f:
                json.dump(admin_data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"保存管理员数据异常: {e}")
            raise
    
    def _legacy_hash_password(self, password: str) -> str:
        """兼容旧版本的密码哈希"""
        import hashlib
        salt = "fruit_vegetable_admin_2024"
        return hashlib.sha256((password + salt).encode()).hexdigest()
    
    def cleanup_sessions(self) -> int:
        """清理过期会话"""
        try:
            return session_manager.cleanup_expired_sessions()
        except Exception as e:
            logger.error(f"清理会话异常: {e}")
            return 0
    
    def get_session_stats(self) -> Dict:
        """获取会话统计"""
        try:
            return session_manager.get_session_stats()
        except Exception as e:
            logger.error(f"获取会话统计异常: {e}")
            return {'admin_sessions': 0, 'conversation_sessions': 0, 'total_sessions': 0}