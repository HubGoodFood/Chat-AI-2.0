# -*- coding: utf-8 -*-
"""
用户服务实现
"""
import logging
import hashlib
import secrets
from typing import Dict, Any, Optional
from ...core.interfaces import IUserService
from ...core.exceptions import AuthenticationError, NotFoundError, ValidationError, ConflictError
from ...database.database_config import db_config
from ...database.models import AdminUser
from ...services.cache_service import cached

logger = logging.getLogger(__name__)


class UserServiceImpl(IUserService):
    """用户服务实现"""
    
    def __init__(self):
        self.password_iterations = 100000  # PBKDF2迭代次数
        self.cache_timeout = 300  # 5分钟缓存
    
    def authenticate_admin(self, username: str, password: str) -> Optional[Dict[str, Any]]:
        """管理员认证"""
        try:
            # 数据验证
            if not username or not username.strip():
                raise ValidationError("用户名不能为空", field="username")
            
            if not password:
                raise ValidationError("密码不能为空", field="password")
            
            username = username.strip()
            
            with db_config.get_session() as session:
                # 查找用户
                admin_user = session.query(AdminUser).filter(
                    AdminUser.username == username,
                    AdminUser.is_active == True
                ).first()
                
                if not admin_user:
                    logger.warning(f"认证失败: 用户不存在或已禁用 {username}")
                    raise AuthenticationError("用户名或密码错误")
                
                # 验证密码
                if not self._verify_password(password, admin_user.password_hash, admin_user.salt):
                    logger.warning(f"认证失败: 密码错误 {username}")
                    raise AuthenticationError("用户名或密码错误")
                
                # 更新最后登录时间
                from datetime import datetime
                admin_user.last_login = datetime.utcnow()
                admin_user.login_count = (admin_user.login_count or 0) + 1
                session.commit()
                
                logger.info(f"管理员认证成功: {username}")
                
                return {
                    'id': admin_user.id,
                    'username': admin_user.username,
                    'email': admin_user.email,
                    'full_name': admin_user.full_name,
                    'is_super_admin': admin_user.is_super_admin,
                    'last_login': admin_user.last_login.isoformat() if admin_user.last_login else None,
                    'login_count': admin_user.login_count
                }
                
        except (ValidationError, AuthenticationError):
            raise
        except Exception as e:
            logger.error(f"管理员认证异常 {username}: {e}")
            raise AuthenticationError("认证服务暂时不可用")
    
    @cached(prefix="user:admin", timeout=300)
    def get_admin_user(self, user_id: int) -> Optional[Dict[str, Any]]:
        """获取管理员用户"""
        try:
            with db_config.get_session() as session:
                admin_user = session.query(AdminUser).filter(
                    AdminUser.id == user_id,
                    AdminUser.is_active == True
                ).first()
                
                if not admin_user:
                    return None
                
                return {
                    'id': admin_user.id,
                    'username': admin_user.username,
                    'email': admin_user.email,
                    'full_name': admin_user.full_name,
                    'is_super_admin': admin_user.is_super_admin,
                    'password_changed': admin_user.password_changed,
                    'created_at': admin_user.created_at.isoformat() if admin_user.created_at else None,
                    'last_login': admin_user.last_login.isoformat() if admin_user.last_login else None,
                    'login_count': admin_user.login_count or 0
                }
                
        except Exception as e:
            logger.error(f"获取管理员用户失败 {user_id}: {e}")
            raise
    
    def create_admin_user(self, user_data: Dict[str, Any], creator: str) -> int:
        """创建管理员用户"""
        try:
            # 数据验证
            self._validate_admin_user_data(user_data)
            
            with db_config.get_session() as session:
                # 检查用户名是否已存在
                existing_username = session.query(AdminUser).filter(
                    AdminUser.username == user_data['username']
                ).first()
                
                if existing_username:
                    raise ConflictError(
                        f"用户名已存在: {user_data['username']}",
                        conflicting_field="username"
                    )
                
                # 检查邮箱是否已存在
                if user_data.get('email'):
                    existing_email = session.query(AdminUser).filter(
                        AdminUser.email == user_data['email']
                    ).first()
                    
                    if existing_email:
                        raise ConflictError(
                            f"邮箱已存在: {user_data['email']}",
                            conflicting_field="email"
                        )
                
                # 生成密码哈希
                salt = secrets.token_hex(16)
                password_hash = self._hash_password(user_data['password'], salt)
                
                # 创建用户
                admin_user = AdminUser(
                    username=user_data['username'],
                    password_hash=password_hash,
                    salt=salt,
                    email=user_data.get('email', ''),
                    full_name=user_data.get('full_name', user_data['username']),
                    is_super_admin=user_data.get('is_super_admin', False),
                    is_active=True,
                    password_changed=False,
                    created_by=creator
                )
                
                session.add(admin_user)
                session.commit()
                
                logger.info(f"创建管理员用户成功 {admin_user.id}: {user_data['username']} by {creator}")
                return admin_user.id
                
        except (ValidationError, ConflictError):
            raise
        except Exception as e:
            logger.error(f"创建管理员用户失败: {e}")
            raise
    
    def update_admin_user(self, user_id: int, user_data: Dict[str, Any], operator: str) -> bool:
        """更新管理员用户"""
        try:
            # 数据验证
            self._validate_admin_user_data(user_data, is_update=True)
            
            with db_config.get_session() as session:
                # 检查用户是否存在
                admin_user = session.query(AdminUser).filter(AdminUser.id == user_id).first()
                if not admin_user:
                    raise NotFoundError("管理员用户不存在", resource_type="管理员用户", resource_id=user_id)
                
                # 检查用户名冲突
                if 'username' in user_data:
                    existing_username = session.query(AdminUser).filter(
                        AdminUser.username == user_data['username'],
                        AdminUser.id != user_id
                    ).first()
                    
                    if existing_username:
                        raise ConflictError(
                            f"用户名已存在: {user_data['username']}",
                            conflicting_field="username"
                        )
                
                # 检查邮箱冲突
                if 'email' in user_data and user_data['email']:
                    existing_email = session.query(AdminUser).filter(
                        AdminUser.email == user_data['email'],
                        AdminUser.id != user_id
                    ).first()
                    
                    if existing_email:
                        raise ConflictError(
                            f"邮箱已存在: {user_data['email']}",
                            conflicting_field="email"
                        )
                
                # 更新用户信息
                for key, value in user_data.items():
                    if key == 'password':
                        # 更新密码
                        salt = secrets.token_hex(16)
                        password_hash = self._hash_password(value, salt)
                        admin_user.password_hash = password_hash
                        admin_user.salt = salt
                        admin_user.password_changed = True
                    elif hasattr(admin_user, key):
                        setattr(admin_user, key, value)
                
                session.commit()
                
                logger.info(f"更新管理员用户成功 {user_id} by {operator}")
                return True
                
        except (ValidationError, ConflictError, NotFoundError):
            raise
        except Exception as e:
            logger.error(f"更新管理员用户失败 {user_id}: {e}")
            raise
    
    def change_password(self, user_id: int, old_password: str, new_password: str) -> bool:
        """修改密码"""
        try:
            # 数据验证
            if not old_password:
                raise ValidationError("原密码不能为空", field="old_password")
            
            if not new_password:
                raise ValidationError("新密码不能为空", field="new_password")
            
            self._validate_password(new_password)
            
            with db_config.get_session() as session:
                # 检查用户是否存在
                admin_user = session.query(AdminUser).filter(
                    AdminUser.id == user_id,
                    AdminUser.is_active == True
                ).first()
                
                if not admin_user:
                    raise NotFoundError("管理员用户不存在", resource_type="管理员用户", resource_id=user_id)
                
                # 验证原密码
                if not self._verify_password(old_password, admin_user.password_hash, admin_user.salt):
                    raise AuthenticationError("原密码错误")
                
                # 检查新密码是否与原密码相同
                if self._verify_password(new_password, admin_user.password_hash, admin_user.salt):
                    raise ValidationError("新密码不能与原密码相同", field="new_password")
                
                # 更新密码
                salt = secrets.token_hex(16)
                password_hash = self._hash_password(new_password, salt)
                admin_user.password_hash = password_hash
                admin_user.salt = salt
                admin_user.password_changed = True
                
                session.commit()
                
                logger.info(f"管理员用户修改密码成功 {user_id}")
                return True
                
        except (ValidationError, AuthenticationError, NotFoundError):
            raise
        except Exception as e:
            logger.error(f"修改密码失败 {user_id}: {e}")
            raise
    
    def _validate_admin_user_data(self, user_data: Dict[str, Any], is_update: bool = False):
        """验证管理员用户数据"""
        if not is_update:
            # 创建时必须有用户名和密码
            if not user_data.get('username'):
                raise ValidationError("用户名不能为空", field="username")
            
            if not user_data.get('password'):
                raise ValidationError("密码不能为空", field="password")
        
        # 验证用户名
        if 'username' in user_data:
            username = user_data['username'].strip()
            if not username:
                raise ValidationError("用户名不能为空", field="username")
            
            if len(username) < 3:
                raise ValidationError("用户名长度不能少于3个字符", field="username")
            
            if len(username) > 50:
                raise ValidationError("用户名长度不能超过50个字符", field="username")
            
            # 用户名只能包含字母、数字、下划线
            if not username.replace('_', '').isalnum():
                raise ValidationError("用户名只能包含字母、数字和下划线", field="username")
            
            user_data['username'] = username
        
        # 验证密码
        if 'password' in user_data:
            self._validate_password(user_data['password'])
        
        # 验证邮箱
        if 'email' in user_data and user_data['email']:
            email = user_data['email'].strip()
            if '@' not in email or '.' not in email:
                raise ValidationError("邮箱格式不正确", field="email")
            
            if len(email) > 100:
                raise ValidationError("邮箱长度不能超过100个字符", field="email")
            
            user_data['email'] = email
        
        # 验证全名
        if 'full_name' in user_data and user_data['full_name']:
            full_name = user_data['full_name'].strip()
            if len(full_name) > 100:
                raise ValidationError("全名长度不能超过100个字符", field="full_name")
            
            user_data['full_name'] = full_name
    
    def _validate_password(self, password: str):
        """验证密码强度"""
        if len(password) < 8:
            raise ValidationError("密码长度不能少于8个字符", field="password")
        
        if len(password) > 100:
            raise ValidationError("密码长度不能超过100个字符", field="password")
        
        # 检查是否包含数字
        if not any(c.isdigit() for c in password):
            raise ValidationError("密码必须包含至少一个数字", field="password")
        
        # 检查是否包含字母
        if not any(c.isalpha() for c in password):
            raise ValidationError("密码必须包含至少一个字母", field="password")
    
    def _hash_password(self, password: str, salt: str) -> str:
        """生成密码哈希"""
        return hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), self.password_iterations).hex()
    
    def _verify_password(self, password: str, password_hash: str, salt: str) -> bool:
        """验证密码"""
        try:
            computed_hash = self._hash_password(password, salt)
            return computed_hash == password_hash
        except Exception:
            return False