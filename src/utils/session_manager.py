# -*- coding: utf-8 -*-
"""
增强的会话管理模块
"""
import json
import uuid
import hashlib
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
import redis
from .logger_config import get_logger

logger = get_logger('session_manager')


class SessionManager:
    """增强的会话管理器"""
    
    def __init__(self, redis_url: str = None):
        self.session_timeout = 3600  # 1小时
        self.max_sessions_per_user = 5
        self.conversation_timeout = 1800  # 30分钟对话超时
        self.max_conversation_history = 20
        
        # 初始化Redis连接
        self.redis_client = self._init_redis_connection(redis_url)
        self.use_redis = self.redis_client is not None
        
        # 降级到内存存储
        if not self.use_redis:
            logger.warning("Redis不可用，使用内存存储（重启后会丢失数据）")
            self.memory_sessions = {}
            self.memory_conversations = {}
    
    def _init_redis_connection(self, redis_url: str) -> Optional[redis.Redis]:
        """初始化Redis连接"""
        try:
            import os
            redis_url = redis_url or os.environ.get('REDIS_URL', 'redis://localhost:6379/0')
            
            client = redis.from_url(redis_url, decode_responses=True)
            # 测试连接
            client.ping()
            logger.info("Redis连接成功")
            return client
            
        except Exception as e:
            logger.warning(f"Redis连接失败: {e}")
            return None
    
    def create_admin_session(self, username: str, ip_address: str, 
                           user_agent: str = '') -> str:
        """创建管理员会话"""
        try:
            session_id = str(uuid.uuid4())
            current_time = datetime.utcnow()
            
            session_data = {
                'username': username,
                'ip_address': ip_address,
                'user_agent': user_agent,
                'created_at': current_time.isoformat(),
                'last_activity': current_time.isoformat(),
                'session_type': 'admin'
            }
            
            if self.use_redis:
                # 清理旧会话
                self._cleanup_old_user_sessions(username)
                
                # 存储会话
                session_key = f"admin_session:{session_id}"
                user_sessions_key = f"admin_user_sessions:{username}"
                
                # 设置会话数据
                self.redis_client.setex(
                    session_key, 
                    self.session_timeout, 
                    json.dumps(session_data)
                )
                
                # 添加到用户会话集合
                self.redis_client.sadd(user_sessions_key, session_id)
                self.redis_client.expire(user_sessions_key, self.session_timeout)
                
            else:
                # 内存存储
                self.memory_sessions[session_id] = {
                    **session_data,
                    'expires_at': current_time + timedelta(seconds=self.session_timeout)
                }
            
            logger.info(f"管理员会话创建成功: {username}@{ip_address}")
            return session_id
            
        except Exception as e:
            logger.error(f"创建管理员会话失败: {e}")
            return None
    
    def verify_admin_session(self, session_id: str, update_activity: bool = True) -> Optional[Dict]:
        """验证管理员会话"""
        try:
            if not session_id:
                return None
            
            if self.use_redis:
                session_key = f"admin_session:{session_id}"
                session_data_str = self.redis_client.get(session_key)
                
                if not session_data_str:
                    return None
                
                session_data = json.loads(session_data_str)
                
                # 更新最后活动时间
                if update_activity:
                    session_data['last_activity'] = datetime.utcnow().isoformat()
                    self.redis_client.setex(
                        session_key,
                        self.session_timeout,
                        json.dumps(session_data)
                    )
                
                return session_data
                
            else:
                # 内存存储验证
                if session_id in self.memory_sessions:
                    session_data = self.memory_sessions[session_id]
                    
                    # 检查是否过期
                    if datetime.utcnow() > session_data['expires_at']:
                        del self.memory_sessions[session_id]
                        return None
                    
                    # 更新最后活动时间
                    if update_activity:
                        session_data['last_activity'] = datetime.utcnow().isoformat()
                        session_data['expires_at'] = datetime.utcnow() + timedelta(seconds=self.session_timeout)
                    
                    return session_data
                
                return None
            
        except Exception as e:
            logger.error(f"验证管理员会话失败: {e}")
            return None
    
    def delete_admin_session(self, session_id: str) -> bool:
        """删除管理员会话"""
        try:
            if not session_id:
                return False
            
            if self.use_redis:
                # 获取会话数据以获得用户名
                session_key = f"admin_session:{session_id}"
                session_data_str = self.redis_client.get(session_key)
                
                if session_data_str:
                    session_data = json.loads(session_data_str)
                    username = session_data.get('username')
                    
                    # 删除会话
                    self.redis_client.delete(session_key)
                    
                    # 从用户会话集合中移除
                    if username:
                        user_sessions_key = f"admin_user_sessions:{username}"
                        self.redis_client.srem(user_sessions_key, session_id)
                    
                    logger.info(f"管理员会话删除成功: {session_id}")
                    return True
                
            else:
                # 内存存储删除
                if session_id in self.memory_sessions:
                    del self.memory_sessions[session_id]
                    logger.info(f"管理员会话删除成功: {session_id}")
                    return True
            
            return False
            
        except Exception as e:
            logger.error(f"删除管理员会话失败: {e}")
            return False
    
    def create_conversation_session(self) -> str:
        """创建客服对话会话"""
        try:
            session_id = str(uuid.uuid4())
            current_time = datetime.utcnow()
            
            conversation_data = {
                'created_at': current_time.isoformat(),
                'last_activity': current_time.isoformat(),
                'message_count': 0,
                'session_type': 'conversation'
            }
            
            if self.use_redis:
                session_key = f"conversation_session:{session_id}"
                self.redis_client.setex(
                    session_key,
                    self.conversation_timeout,
                    json.dumps(conversation_data)
                )
                
                # 初始化对话历史
                history_key = f"conversation_history:{session_id}"
                self.redis_client.setex(history_key, self.conversation_timeout, json.dumps([]))
                
            else:
                # 内存存储
                self.memory_conversations[session_id] = {
                    **conversation_data,
                    'history': [],
                    'expires_at': current_time + timedelta(seconds=self.conversation_timeout)
                }
            
            logger.info(f"对话会话创建成功: {session_id}")
            return session_id
            
        except Exception as e:
            logger.error(f"创建对话会话失败: {e}")
            return None
    
    def get_conversation_history(self, session_id: str) -> List[Dict]:
        """获取对话历史"""
        try:
            if not session_id:
                return []
            
            if self.use_redis:
                # 验证会话是否存在
                session_key = f"conversation_session:{session_id}"
                if not self.redis_client.exists(session_key):
                    return []
                
                # 获取对话历史
                history_key = f"conversation_history:{session_id}"
                history_str = self.redis_client.get(history_key)
                
                if history_str:
                    return json.loads(history_str)
                else:
                    # 初始化空历史
                    self.redis_client.setex(history_key, self.conversation_timeout, json.dumps([]))
                    return []
                
            else:
                # 内存存储
                if session_id in self.memory_conversations:
                    conversation = self.memory_conversations[session_id]
                    
                    # 检查是否过期
                    if datetime.utcnow() > conversation['expires_at']:
                        del self.memory_conversations[session_id]
                        return []
                    
                    return conversation.get('history', [])
                
                return []
            
        except Exception as e:
            logger.error(f"获取对话历史失败: {e}")
            return []
    
    def add_conversation_message(self, session_id: str, role: str, content: str) -> bool:
        """添加对话消息"""
        try:
            if not session_id or not role or not content:
                return False
            
            current_time = datetime.utcnow()
            message = {
                'role': role,
                'content': content,
                'timestamp': current_time.isoformat()
            }
            
            if self.use_redis:
                # 获取当前历史
                history = self.get_conversation_history(session_id)
                history.append(message)
                
                # 限制历史长度
                if len(history) > self.max_conversation_history:
                    history = history[-self.max_conversation_history:]
                
                # 更新历史
                history_key = f"conversation_history:{session_id}"
                self.redis_client.setex(
                    history_key,
                    self.conversation_timeout,
                    json.dumps(history)
                )
                
                # 更新会话信息
                session_key = f"conversation_session:{session_id}"
                session_data_str = self.redis_client.get(session_key)
                if session_data_str:
                    session_data = json.loads(session_data_str)
                    session_data['last_activity'] = current_time.isoformat()
                    session_data['message_count'] = session_data.get('message_count', 0) + 1
                    
                    self.redis_client.setex(
                        session_key,
                        self.conversation_timeout,
                        json.dumps(session_data)
                    )
                
            else:
                # 内存存储
                if session_id in self.memory_conversations:
                    conversation = self.memory_conversations[session_id]
                    
                    # 检查是否过期
                    if datetime.utcnow() > conversation['expires_at']:
                        del self.memory_conversations[session_id]
                        return False
                    
                    # 添加消息
                    conversation['history'].append(message)
                    
                    # 限制历史长度
                    if len(conversation['history']) > self.max_conversation_history:
                        conversation['history'] = conversation['history'][-self.max_conversation_history:]
                    
                    # 更新会话信息
                    conversation['last_activity'] = current_time.isoformat()
                    conversation['message_count'] = conversation.get('message_count', 0) + 1
                    conversation['expires_at'] = current_time + timedelta(seconds=self.conversation_timeout)
                
                else:
                    # 会话不存在，创建新会话
                    self.memory_conversations[session_id] = {
                        'created_at': current_time.isoformat(),
                        'last_activity': current_time.isoformat(),
                        'message_count': 1,
                        'session_type': 'conversation',
                        'history': [message],
                        'expires_at': current_time + timedelta(seconds=self.conversation_timeout)
                    }
            
            return True
            
        except Exception as e:
            logger.error(f"添加对话消息失败: {e}")
            return False
    
    def cleanup_expired_sessions(self) -> int:
        """清理过期会话"""
        try:
            cleaned_count = 0
            
            if not self.use_redis:
                # 内存存储清理
                current_time = datetime.utcnow()
                
                # 清理管理员会话
                expired_sessions = [
                    sid for sid, data in self.memory_sessions.items()
                    if current_time > data['expires_at']
                ]
                for sid in expired_sessions:
                    del self.memory_sessions[sid]
                    cleaned_count += 1
                
                # 清理对话会话
                expired_conversations = [
                    sid for sid, data in self.memory_conversations.items()
                    if current_time > data['expires_at']
                ]
                for sid in expired_conversations:
                    del self.memory_conversations[sid]
                    cleaned_count += 1
                
                if cleaned_count > 0:
                    logger.info(f"清理了 {cleaned_count} 个过期会话")
            
            return cleaned_count
            
        except Exception as e:
            logger.error(f"清理过期会话失败: {e}")
            return 0
    
    def _cleanup_old_user_sessions(self, username: str):
        """清理用户的旧会话"""
        try:
            if not self.use_redis:
                return
            
            user_sessions_key = f"admin_user_sessions:{username}"
            session_ids = self.redis_client.smembers(user_sessions_key)
            
            if len(session_ids) >= self.max_sessions_per_user:
                # 获取最旧的会话
                sessions_with_time = []
                for sid in session_ids:
                    session_key = f"admin_session:{sid}"
                    session_data_str = self.redis_client.get(session_key)
                    if session_data_str:
                        session_data = json.loads(session_data_str)
                        created_at = datetime.fromisoformat(session_data['created_at'])
                        sessions_with_time.append((sid, created_at))
                
                # 按创建时间排序，删除最旧的
                sessions_with_time.sort(key=lambda x: x[1])
                sessions_to_delete = sessions_with_time[:-self.max_sessions_per_user + 1]
                
                for sid, _ in sessions_to_delete:
                    self.delete_admin_session(sid)
                    
        except Exception as e:
            logger.error(f"清理用户旧会话失败: {e}")
    
    def get_session_stats(self) -> Dict[str, int]:
        """获取会话统计信息"""
        try:
            stats = {
                'admin_sessions': 0,
                'conversation_sessions': 0,
                'total_sessions': 0
            }
            
            if self.use_redis:
                # Redis统计
                admin_pattern = "admin_session:*"
                conversation_pattern = "conversation_session:*"
                
                stats['admin_sessions'] = len(list(self.redis_client.scan_iter(match=admin_pattern)))
                stats['conversation_sessions'] = len(list(self.redis_client.scan_iter(match=conversation_pattern)))
                
            else:
                # 内存统计
                stats['admin_sessions'] = len(self.memory_sessions)
                stats['conversation_sessions'] = len(self.memory_conversations)
            
            stats['total_sessions'] = stats['admin_sessions'] + stats['conversation_sessions']
            return stats
            
        except Exception as e:
            logger.error(f"获取会话统计失败: {e}")
            return {'admin_sessions': 0, 'conversation_sessions': 0, 'total_sessions': 0}


# 全局会话管理器实例
session_manager = SessionManager()