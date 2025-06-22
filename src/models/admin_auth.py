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
    """
    管理员认证类 - 果蔬客服系统的安全认证组件

    负责管理员账户的认证、会话管理、密码安全等功能。
    采用基于令牌的会话管理机制，确保后台管理系统的安全性。

    主要功能：
    - 用户认证：用户名密码验证、安全哈希存储
    - 会话管理：令牌生成、会话验证、自动超时
    - 密码管理：密码修改、安全哈希算法
    - 会话清理：过期会话自动清理机制

    安全特性：
    - 密码哈希：使用SHA256+盐值确保密码安全
    - 会话令牌：使用安全随机令牌，防止会话劫持
    - 自动超时：1小时无活动自动登出
    - 活动追踪：记录登录时间和最后活动时间

    Attributes:
        admin_file (str): 管理员账户数据文件路径
        sessions (Dict): 活跃会话存储字典
        session_timeout (int): 会话超时时间（秒）
    """

    def __init__(self):
        """
        初始化管理员认证系统

        设置文件路径、会话存储和超时配置。
        如果管理员配置文件不存在，会自动创建默认管理员账户。

        默认管理员账户：
        - 用户名：admin
        - 密码：admin123
        - 建议首次登录后立即修改密码
        """
        # 核心配置
        self.admin_file = 'data/admin.json'  # 管理员账户数据文件
        self.sessions = {}  # 内存中存储活跃会话（重启后会清空）
        self.session_timeout = 3600  # 会话超时时间：1小时（3600秒）

        # 确保管理员配置文件存在
        self._ensure_admin_file()

    def _ensure_admin_file(self):
        """
        确保管理员配置文件存在，如果不存在则创建默认账户

        创建默认管理员账户的目的是确保系统首次部署时能够正常访问。
        默认账户信息会被安全地哈希存储，包含创建时间等元数据。

        默认账户配置：
        - 用户名：admin
        - 密码：admin123（已哈希存储）
        - 创建时间：当前时间
        - 最后登录：null（首次登录时更新）

        Note:
            生产环境中应该立即修改默认密码以确保安全性
        """
        if not os.path.exists(self.admin_file):
            # 创建默认管理员账户数据结构
            default_admin = {
                "admins": {
                    "admin": {
                        "username": "admin",
                        "password_hash": self._hash_password("admin123"),  # 默认密码的哈希值
                        "created_at": datetime.now().isoformat(),  # 账户创建时间
                        "last_login": None  # 最后登录时间（首次登录时更新）
                    }
                }
            }

            # 确保数据目录存在
            os.makedirs(os.path.dirname(self.admin_file), exist_ok=True)

            # 保存默认管理员配置到文件
            with open(self.admin_file, 'w', encoding='utf-8') as f:
                json.dump(default_admin, f, ensure_ascii=False, indent=2)

            logger.info("默认管理员账户创建成功 (用户名: admin, 密码: admin123)")

    def _hash_password(self, password: str) -> str:
        """
        使用SHA256算法对密码进行安全哈希

        采用密码+盐值的方式增强安全性，防止彩虹表攻击。
        盐值是固定的字符串，在实际生产环境中建议使用随机盐值。

        Args:
            password (str): 原始密码明文

        Returns:
            str: SHA256哈希后的密码字符串

        Security Note:
            - 使用固定盐值简化了实现，但降低了安全性
            - 生产环境建议为每个用户使用独立的随机盐值
            - 考虑使用更强的哈希算法如bcrypt或Argon2
        """
        salt = "fruit_vegetable_admin_2024"  # 固定盐值（生产环境建议使用随机盐值）
        return hashlib.sha256((password + salt).encode()).hexdigest()
    
    def login(self, username: str, password: str) -> Optional[str]:
        """
        管理员登录验证

        验证用户名和密码，成功后生成安全的会话令牌。
        同时更新用户的最后登录时间，用于审计和统计。

        登录流程：
        1. 加载管理员账户数据
        2. 验证用户名是否存在
        3. 验证密码哈希是否匹配
        4. 生成安全的会话令牌
        5. 创建会话记录
        6. 更新最后登录时间

        Args:
            username (str): 管理员用户名
            password (str): 密码明文

        Returns:
            Optional[str]: 成功时返回会话令牌，失败时返回None

        Example:
            >>> auth = AdminAuth()
            >>> token = auth.login("admin", "admin123")
            >>> if token:
            ...     print("登录成功")
            ... else:
            ...     print("登录失败")

        Security Note:
            - 会话令牌使用cryptographically secure的随机生成
            - 令牌长度为32字节，URL安全编码
            - 所有登录尝试都会被记录到日志中
        """
        try:
            # 加载管理员账户数据
            with open(self.admin_file, 'r', encoding='utf-8') as f:
                admin_data = json.load(f)

            # 检查用户名是否存在
            if username in admin_data['admins']:
                admin = admin_data['admins'][username]

                # 验证密码哈希
                if admin['password_hash'] == self._hash_password(password):
                    # 生成安全的会话令牌（32字节，URL安全）
                    session_token = secrets.token_urlsafe(32)

                    # 创建会话记录
                    self.sessions[session_token] = {
                        'username': username,  # 用户名
                        'login_time': datetime.now(),  # 登录时间
                        'last_activity': datetime.now()  # 最后活动时间
                    }

                    # 更新用户的最后登录时间（用于审计）
                    admin['last_login'] = datetime.now().isoformat()
                    with open(self.admin_file, 'w', encoding='utf-8') as f:
                        json.dump(admin_data, f, ensure_ascii=False, indent=2)

                    logger.info(f"管理员 {username} 登录成功")
                    return session_token
                else:
                    logger.warning(f"管理员 {username} 密码错误")
            else:
                logger.warning(f"不存在的用户名: {username}")

            return None

        except Exception as e:
            logger.error(f"登录过程中发生错误: {e}")
            return None

    def verify_session(self, session_token: str) -> bool:
        """
        验证会话令牌的有效性

        检查会话是否存在、是否超时，并更新最后活动时间。
        这是所有需要认证的操作的入口点。

        验证流程：
        1. 检查令牌是否存在
        2. 检查会话是否超时
        3. 更新最后活动时间
        4. 清理过期会话

        Args:
            session_token (str): 会话令牌

        Returns:
            bool: 会话有效返回True，无效返回False

        Example:
            >>> auth = AdminAuth()
            >>> token = auth.login("admin", "admin123")
            >>> is_valid = auth.verify_session(token)
            >>> print(f"会话有效: {is_valid}")

        Note:
            - 每次验证都会更新最后活动时间，重置超时计时器
            - 超时的会话会被自动删除，释放内存
            - 验证失败的原因包括：令牌不存在、会话超时
        """
        # 检查令牌是否存在
        if not session_token or session_token not in self.sessions:
            return False

        session = self.sessions[session_token]
        now = datetime.now()

        # 检查会话是否超时（计算秒数差）
        time_diff = (now - session['last_activity']).total_seconds()
        if time_diff > self.session_timeout:
            # 会话超时，删除会话记录
            del self.sessions[session_token]
            logger.info(f"会话超时，已清理: {session['username']}")
            return False

        # 更新最后活动时间（重置超时计时器）
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
