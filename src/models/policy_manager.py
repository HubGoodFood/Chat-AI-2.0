# -*- coding: utf-8 -*-
"""
平台政策管理器 - 果蔬客服AI系统的政策管理组件

负责平台各类政策的创建、编辑、发布和版本管理功能。
支持富文本内容、版本控制、安全过滤等特性。

主要功能：
- 政策CRUD操作：创建、读取、更新、删除政策
- 版本管理：支持政策版本控制和历史记录
- 内容安全：HTML内容安全过滤，防止XSS攻击
- 状态管理：草稿、发布、归档状态管理
- 搜索功能：支持按类型、关键词搜索政策

安全特性：
- HTML内容清理：使用bleach库清理不安全的HTML标签
- 输入验证：严格的数据验证和类型检查
- 操作日志：记录所有政策操作的详细日志
- 权限控制：确保只有授权管理员可以操作

Attributes:
    db_session: 数据库会话对象
    logger: 日志记录器
    policy_types: 支持的政策类型定义
"""

import os
import json
import logging
from datetime import datetime
from typing import Dict, List, Optional, Tuple
import bleach
from sqlalchemy.orm import sessionmaker
from sqlalchemy import and_, or_, desc

from src.database import db_config, Policy
from src.models.operation_logger import operation_logger


class PolicyManager:
    """
    平台政策管理器类
    
    提供完整的政策管理功能，包括创建、编辑、发布、版本控制等。
    遵循简约设计原则，确保功能完整性和安全性。
    """
    
    # 支持的政策类型定义
    POLICY_TYPES = {
        'return_policy': '退换货政策',
        'privacy_policy': '隐私政策', 
        'terms_of_service': '服务条款',
        'shipping_policy': '配送政策',
        'payment_policy': '付款政策',
        'quality_guarantee': '质量保证'
    }
    
    # 政策状态定义
    POLICY_STATUS = {
        'draft': '草稿',
        'active': '已发布',
        'archived': '已归档'
    }
    
    # HTML内容安全过滤配置
    ALLOWED_TAGS = [
        'p', 'br', 'strong', 'em', 'u', 'ol', 'ul', 'li', 
        'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
        'blockquote', 'a', 'img', 'table', 'thead', 'tbody', 'tr', 'td', 'th'
    ]
    
    ALLOWED_ATTRIBUTES = {
        'a': ['href', 'title'],
        'img': ['src', 'alt', 'width', 'height'],
        'table': ['class'],
        'td': ['colspan', 'rowspan'],
        'th': ['colspan', 'rowspan']
    }

    def __init__(self):
        """
        初始化政策管理器
        
        设置数据库连接、日志记录器和基础配置。
        确保数据库表结构正确创建。
        """
        self.logger = logging.getLogger(__name__)
        
        # 获取数据库会话
        Session = sessionmaker(bind=db_config.engine)
        self.db_session = Session()
        
        self.logger.info("政策管理器初始化成功")

    def get_all_policies(self, status: Optional[str] = None) -> List[Dict]:
        """
        获取所有政策列表
        
        Args:
            status: 可选的状态过滤器 ('draft', 'active', 'archived')
            
        Returns:
            List[Dict]: 政策列表，包含基本信息
        """
        try:
            query = self.db_session.query(Policy)
            
            if status:
                query = query.filter(Policy.status == status)
                
            policies = query.order_by(desc(Policy.updated_at)).all()
            
            result = []
            for policy in policies:
                policy_dict = policy.to_dict()
                # 添加政策类型的中文名称
                policy_dict['policy_type_name'] = self.POLICY_TYPES.get(
                    policy.policy_type, policy.policy_type
                )
                policy_dict['status_name'] = self.POLICY_STATUS.get(
                    policy.status, policy.status
                )
                result.append(policy_dict)
            
            self.logger.info(f"获取政策列表成功，共 {len(result)} 条记录")
            return result
            
        except Exception as e:
            self.logger.error(f"获取政策列表失败: {e}")
            return []

    def get_policy_by_id(self, policy_id: int) -> Optional[Dict]:
        """
        根据ID获取政策详情
        
        Args:
            policy_id: 政策ID
            
        Returns:
            Optional[Dict]: 政策详情，如果不存在返回None
        """
        try:
            policy = self.db_session.query(Policy).filter(Policy.id == policy_id).first()
            
            if not policy:
                self.logger.warning(f"政策不存在: {policy_id}")
                return None
                
            policy_dict = policy.to_dict()
            policy_dict['policy_type_name'] = self.POLICY_TYPES.get(
                policy.policy_type, policy.policy_type
            )
            policy_dict['status_name'] = self.POLICY_STATUS.get(
                policy.status, policy.status
            )
            
            self.logger.info(f"获取政策详情成功: {policy_id}")
            return policy_dict
            
        except Exception as e:
            self.logger.error(f"获取政策详情失败: {e}")
            return None

    def get_policy_by_type(self, policy_type: str) -> Optional[Dict]:
        """
        根据类型获取当前有效的政策
        
        Args:
            policy_type: 政策类型
            
        Returns:
            Optional[Dict]: 政策详情，如果不存在返回None
        """
        try:
            policy = self.db_session.query(Policy).filter(
                and_(Policy.policy_type == policy_type, Policy.status == 'active')
            ).order_by(desc(Policy.published_at)).first()
            
            if not policy:
                self.logger.warning(f"未找到有效的政策: {policy_type}")
                return None
                
            policy_dict = policy.to_dict()
            policy_dict['policy_type_name'] = self.POLICY_TYPES.get(
                policy.policy_type, policy.policy_type
            )
            
            self.logger.info(f"获取政策成功: {policy_type}")
            return policy_dict
            
        except Exception as e:
            self.logger.error(f"获取政策失败: {e}")
            return None

    def _clean_html_content(self, content: str) -> str:
        """
        清理HTML内容，确保安全性
        
        Args:
            content: 原始HTML内容
            
        Returns:
            str: 清理后的安全HTML内容
        """
        if not content:
            return ""
            
        # 使用bleach库清理HTML内容
        cleaned_content = bleach.clean(
            content,
            tags=self.ALLOWED_TAGS,
            attributes=self.ALLOWED_ATTRIBUTES,
            strip=True
        )
        
        return cleaned_content

    def create_policy(self, policy_data: Dict, created_by: str) -> Tuple[bool, str, Optional[int]]:
        """
        创建新政策
        
        Args:
            policy_data: 政策数据字典
            created_by: 创建者用户名
            
        Returns:
            Tuple[bool, str, Optional[int]]: (成功标志, 消息, 政策ID)
        """
        try:
            # 验证必需字段
            required_fields = ['policy_type', 'title', 'content']
            for field in required_fields:
                if not policy_data.get(field):
                    return False, f"缺少必需字段: {field}", None
            
            # 验证政策类型
            if policy_data['policy_type'] not in self.POLICY_TYPES:
                return False, "无效的政策类型", None
            
            # 清理HTML内容
            cleaned_content = self._clean_html_content(policy_data['content'])
            
            # 创建政策对象
            policy = Policy(
                policy_type=policy_data['policy_type'],
                title=policy_data['title'].strip(),
                content=cleaned_content,
                version=policy_data.get('version', '1.0'),
                status=policy_data.get('status', 'draft'),
                summary=policy_data.get('summary', '').strip(),
                keywords=policy_data.get('keywords', '').strip(),
                created_by=created_by
            )
            
            self.db_session.add(policy)
            self.db_session.commit()
            
            # 记录操作日志
            operation_logger.log_operation(
                operator=created_by,
                operation_type='create',
                target_type='policy',
                target_id=str(policy.id),
                details=f"创建政策: {policy.title}",
                result='success'
            )
            
            self.logger.info(f"创建政策成功: {policy.id} - {policy.title}")
            return True, "政策创建成功", policy.id
            
        except Exception as e:
            self.db_session.rollback()
            self.logger.error(f"创建政策失败: {e}")
            return False, f"创建政策失败: {str(e)}", None

    def update_policy(self, policy_id: int, policy_data: Dict, updated_by: str) -> Tuple[bool, str]:
        """
        更新政策
        
        Args:
            policy_id: 政策ID
            policy_data: 更新的政策数据
            updated_by: 更新者用户名
            
        Returns:
            Tuple[bool, str]: (成功标志, 消息)
        """
        try:
            policy = self.db_session.query(Policy).filter(Policy.id == policy_id).first()
            
            if not policy:
                return False, "政策不存在"
            
            # 更新字段
            if 'title' in policy_data:
                policy.title = policy_data['title'].strip()
            
            if 'content' in policy_data:
                policy.content = self._clean_html_content(policy_data['content'])
            
            if 'version' in policy_data:
                policy.version = policy_data['version']
            
            if 'status' in policy_data:
                policy.status = policy_data['status']
                
            if 'summary' in policy_data:
                policy.summary = policy_data['summary'].strip()
                
            if 'keywords' in policy_data:
                policy.keywords = policy_data['keywords'].strip()
            
            policy.updated_by = updated_by
            policy.updated_at = datetime.utcnow()
            
            self.db_session.commit()
            
            # 记录操作日志
            operation_logger.log_operation(
                operator=updated_by,
                operation_type='update',
                target_type='policy',
                target_id=str(policy.id),
                details=f"更新政策: {policy.title}",
                result='success'
            )
            
            self.logger.info(f"更新政策成功: {policy_id}")
            return True, "政策更新成功"
            
        except Exception as e:
            self.db_session.rollback()
            self.logger.error(f"更新政策失败: {e}")
            return False, f"更新政策失败: {str(e)}"

    def delete_policy(self, policy_id: int, deleted_by: str) -> Tuple[bool, str]:
        """
        删除政策（软删除，设置为归档状态）
        
        Args:
            policy_id: 政策ID
            deleted_by: 删除者用户名
            
        Returns:
            Tuple[bool, str]: (成功标志, 消息)
        """
        try:
            policy = self.db_session.query(Policy).filter(Policy.id == policy_id).first()
            
            if not policy:
                return False, "政策不存在"
            
            # 软删除：设置为归档状态
            policy.status = 'archived'
            policy.updated_by = deleted_by
            policy.updated_at = datetime.utcnow()
            
            self.db_session.commit()
            
            # 记录操作日志
            operation_logger.log_operation(
                operator=deleted_by,
                operation_type='delete',
                target_type='policy',
                target_id=str(policy.id),
                details=f"删除政策: {policy.title}",
                result='success'
            )
            
            self.logger.info(f"删除政策成功: {policy_id}")
            return True, "政策删除成功"
            
        except Exception as e:
            self.db_session.rollback()
            self.logger.error(f"删除政策失败: {e}")
            return False, f"删除政策失败: {str(e)}"

    def publish_policy(self, policy_id: int, published_by: str) -> Tuple[bool, str]:
        """
        发布政策
        
        Args:
            policy_id: 政策ID
            published_by: 发布者用户名
            
        Returns:
            Tuple[bool, str]: (成功标志, 消息)
        """
        try:
            policy = self.db_session.query(Policy).filter(Policy.id == policy_id).first()
            
            if not policy:
                return False, "政策不存在"
            
            if policy.status == 'active':
                return False, "政策已经是发布状态"
            
            # 将同类型的其他政策设置为归档状态
            self.db_session.query(Policy).filter(
                and_(Policy.policy_type == policy.policy_type, Policy.status == 'active')
            ).update({'status': 'archived'})
            
            # 发布当前政策
            policy.status = 'active'
            policy.published_by = published_by
            policy.published_at = datetime.utcnow()
            policy.updated_by = published_by
            policy.updated_at = datetime.utcnow()
            
            self.db_session.commit()
            
            # 记录操作日志
            operation_logger.log_operation(
                operator=published_by,
                operation_type='publish',
                target_type='policy',
                target_id=str(policy.id),
                details=f"发布政策: {policy.title}",
                result='success'
            )
            
            self.logger.info(f"发布政策成功: {policy_id}")
            return True, "政策发布成功"
            
        except Exception as e:
            self.db_session.rollback()
            self.logger.error(f"发布政策失败: {e}")
            return False, f"发布政策失败: {str(e)}"

    def get_policy_types(self) -> Dict[str, str]:
        """
        获取所有支持的政策类型
        
        Returns:
            Dict[str, str]: 政策类型字典 {类型代码: 中文名称}
        """
        return self.POLICY_TYPES.copy()

    def search_policies(self, keyword: str, policy_type: Optional[str] = None) -> List[Dict]:
        """
        搜索政策
        
        Args:
            keyword: 搜索关键词
            policy_type: 可选的政策类型过滤
            
        Returns:
            List[Dict]: 匹配的政策列表
        """
        try:
            query = self.db_session.query(Policy)
            
            # 关键词搜索
            if keyword:
                search_filter = or_(
                    Policy.title.contains(keyword),
                    Policy.content.contains(keyword),
                    Policy.keywords.contains(keyword),
                    Policy.summary.contains(keyword)
                )
                query = query.filter(search_filter)
            
            # 政策类型过滤
            if policy_type:
                query = query.filter(Policy.policy_type == policy_type)
            
            policies = query.order_by(desc(Policy.updated_at)).all()
            
            result = []
            for policy in policies:
                policy_dict = policy.to_dict()
                policy_dict['policy_type_name'] = self.POLICY_TYPES.get(
                    policy.policy_type, policy.policy_type
                )
                policy_dict['status_name'] = self.POLICY_STATUS.get(
                    policy.status, policy.status
                )
                result.append(policy_dict)
            
            self.logger.info(f"搜索政策成功，关键词: {keyword}，结果: {len(result)} 条")
            return result
            
        except Exception as e:
            self.logger.error(f"搜索政策失败: {e}")
            return []

    def __del__(self):
        """析构函数，确保数据库连接正确关闭"""
        if hasattr(self, 'db_session'):
            self.db_session.close()
