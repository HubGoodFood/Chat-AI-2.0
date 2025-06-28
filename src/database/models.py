# -*- coding: utf-8 -*-
"""
数据库模型定义 - SQLAlchemy ORM模型
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, Text, Boolean, ForeignKey, Index
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
import uuid

Base = declarative_base()


class Product(Base):
    """产品模型"""
    __tablename__ = 'products'
    
    id = Column(Integer, primary_key=True)
    product_name = Column(String(100), nullable=False, index=True)
    category = Column(String(50), nullable=False, index=True)
    specification = Column(String(50))
    price = Column(Float, nullable=False)
    unit = Column(String(20), nullable=False)
    current_stock = Column(Integer, default=0, index=True)
    min_stock_warning = Column(Integer, default=10)
    description = Column(Text)
    keywords = Column(String(200))
    barcode = Column(String(20), unique=True, index=True)
    barcode_image = Column(String(200))
    storage_area = Column(String(10), index=True)
    status = Column(String(20), default='active', index=True)
    
    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 关系
    stock_histories = relationship("StockHistory", back_populates="product", cascade="all, delete-orphan")
    count_items = relationship("CountItem", back_populates="product")
    
    # 复合索引
    __table_args__ = (
        Index('idx_product_category_status', 'category', 'status'),
        Index('idx_product_stock_warning', 'current_stock', 'min_stock_warning'),
        Index('idx_product_name_search', 'product_name', 'keywords'),
    )
    
    def __repr__(self):
        return f'<Product {self.product_name}>'
    
    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'product_name': self.product_name,
            'category': self.category,
            'specification': self.specification,
            'price': self.price,
            'unit': self.unit,
            'current_stock': self.current_stock,
            'min_stock_warning': self.min_stock_warning,
            'description': self.description,
            'keywords': self.keywords,
            'barcode': self.barcode,
            'barcode_image': self.barcode_image,
            'storage_area': self.storage_area,
            'status': self.status,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


class StockHistory(Base):
    """库存历史记录模型"""
    __tablename__ = 'stock_history'
    
    id = Column(Integer, primary_key=True)
    product_id = Column(Integer, ForeignKey('products.id'), nullable=False, index=True)
    action = Column(String(50), nullable=False, index=True)
    quantity_change = Column(Integer, nullable=False)
    quantity_before = Column(Integer, nullable=False)
    quantity_after = Column(Integer, nullable=False)
    operator = Column(String(50), nullable=False, index=True)
    note = Column(Text)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    
    # 关系
    product = relationship("Product", back_populates="stock_histories")
    
    # 复合索引
    __table_args__ = (
        Index('idx_stock_history_product_time', 'product_id', 'timestamp'),
        Index('idx_stock_history_operator_time', 'operator', 'timestamp'),
    )
    
    def __repr__(self):
        return f'<StockHistory {self.product_id}: {self.action}>'


class CountTask(Base):
    """库存盘点任务模型"""
    __tablename__ = 'count_tasks'
    
    id = Column(String(50), primary_key=True, default=lambda: f"COUNT_{uuid.uuid4().hex[:8].upper()}")
    operator = Column(String(50), nullable=False, index=True)
    status = Column(String(20), default='in_progress', index=True)  # in_progress, completed, cancelled
    note = Column(Text)
    
    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    completed_at = Column(DateTime, index=True)
    
    # 关系
    count_items = relationship("CountItem", back_populates="count_task", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f'<CountTask {self.id}: {self.status}>'


class CountItem(Base):
    """盘点项目模型"""
    __tablename__ = 'count_items'
    
    id = Column(Integer, primary_key=True)
    count_task_id = Column(String(50), ForeignKey('count_tasks.id'), nullable=False, index=True)
    product_id = Column(Integer, ForeignKey('products.id'), nullable=False, index=True)
    system_quantity = Column(Integer, nullable=False)  # 系统库存数量
    actual_quantity = Column(Integer)  # 实际盘点数量
    difference = Column(Integer)  # 差异数量
    note = Column(Text)
    counted_at = Column(DateTime)
    
    # 关系
    count_task = relationship("CountTask", back_populates="count_items")
    product = relationship("Product", back_populates="count_items")
    
    # 复合索引
    __table_args__ = (
        Index('idx_count_item_task_product', 'count_task_id', 'product_id'),
    )
    
    def __repr__(self):
        return f'<CountItem {self.count_task_id}: {self.product_id}>'


class Comparison(Base):
    """库存对比分析模型"""
    __tablename__ = 'comparisons'
    
    id = Column(String(50), primary_key=True, default=lambda: f"CMP_{uuid.uuid4().hex[:8].upper()}")
    comparison_type = Column(String(20), nullable=False, index=True)  # weekly, manual, auto
    current_count_id = Column(String(50), ForeignKey('count_tasks.id'), nullable=False)
    previous_count_id = Column(String(50), ForeignKey('count_tasks.id'), nullable=False)
    operator = Column(String(50), nullable=False, index=True)
    
    # 统计数据
    total_products = Column(Integer, default=0)
    changed_products = Column(Integer, default=0)
    increased_products = Column(Integer, default=0)
    decreased_products = Column(Integer, default=0)
    new_products = Column(Integer, default=0)
    removed_products = Column(Integer, default=0)
    
    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    
    # 关系
    current_count = relationship("CountTask", foreign_keys=[current_count_id])
    previous_count = relationship("CountTask", foreign_keys=[previous_count_id])
    comparison_items = relationship("ComparisonItem", back_populates="comparison", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f'<Comparison {self.id}: {self.comparison_type}>'


class ComparisonItem(Base):
    """对比项目详情模型"""
    __tablename__ = 'comparison_items'
    
    id = Column(Integer, primary_key=True)
    comparison_id = Column(String(50), ForeignKey('comparisons.id'), nullable=False, index=True)
    product_id = Column(Integer, ForeignKey('products.id'), nullable=False, index=True)
    previous_quantity = Column(Integer)
    current_quantity = Column(Integer)
    quantity_change = Column(Integer)
    change_type = Column(String(20))  # increased, decreased, new, removed, unchanged
    
    # 关系
    comparison = relationship("Comparison", back_populates="comparison_items")
    product = relationship("Product")
    
    # 复合索引
    __table_args__ = (
        Index('idx_comparison_item_comparison_product', 'comparison_id', 'product_id'),
        Index('idx_comparison_item_change_type', 'change_type'),
    )
    
    def __repr__(self):
        return f'<ComparisonItem {self.comparison_id}: {self.product_id}>'


class Feedback(Base):
    """客户反馈模型"""
    __tablename__ = 'feedback'
    
    id = Column(String(50), primary_key=True, default=lambda: f"FB_{uuid.uuid4().hex[:8].upper()}")
    product_name = Column(String(100), nullable=False, index=True)
    customer_wechat_name = Column(String(50), nullable=False)
    customer_group_number = Column(String(50), nullable=False)
    customer_phone = Column(String(20))
    payment_status = Column(String(20), nullable=False, index=True)
    feedback_type = Column(String(50), nullable=False, index=True)
    feedback_content = Column(Text, nullable=False)
    order_amount = Column(Float)
    
    # 处理信息
    processing_status = Column(String(20), default='pending', index=True)  # pending, processing, resolved, closed
    processor = Column(String(50), index=True)
    processing_notes = Column(Text)
    processed_at = Column(DateTime)
    
    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 复合索引
    __table_args__ = (
        Index('idx_feedback_type_status', 'feedback_type', 'processing_status'),
        Index('idx_feedback_customer', 'customer_wechat_name', 'customer_group_number'),
        Index('idx_feedback_created', 'created_at'),
    )
    
    def __repr__(self):
        return f'<Feedback {self.id}: {self.feedback_type}>'


class StorageArea(Base):
    """存储区域模型"""
    __tablename__ = 'storage_areas'
    
    area_id = Column(String(10), primary_key=True)
    area_name = Column(String(50), nullable=False)
    description = Column(String(200))
    capacity = Column(Integer, default=1000)
    status = Column(String(20), default='active', index=True)
    
    # 操作信息
    created_by = Column(String(50), nullable=False)
    updated_by = Column(String(50))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<StorageArea {self.area_id}: {self.area_name}>'


class PickupLocation(Base):
    """取货点模型"""
    __tablename__ = 'pickup_locations'
    
    location_id = Column(String(20), primary_key=True)
    location_name = Column(String(100), nullable=False)
    address = Column(String(200), nullable=False)
    phone = Column(String(20))
    contact_person = Column(String(50))
    business_hours = Column(String(100))
    description = Column(String(500))
    status = Column(String(20), default='active', index=True)
    
    # 操作信息
    created_by = Column(String(50), nullable=False)
    updated_by = Column(String(50))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<PickupLocation {self.location_id}: {self.location_name}>'


class OperationLog(Base):
    """操作日志模型"""
    __tablename__ = 'operation_logs'
    
    id = Column(Integer, primary_key=True)
    operator = Column(String(50), nullable=False, index=True)
    operation_type = Column(String(50), nullable=False, index=True)
    target_type = Column(String(50), nullable=False, index=True)
    target_id = Column(String(50), nullable=False)
    details = Column(Text)  # JSON格式的详细信息
    result = Column(String(20), nullable=False, index=True)  # success, failed
    ip_address = Column(String(45))
    user_agent = Column(String(500))
    
    # 时间戳
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    
    # 复合索引
    __table_args__ = (
        Index('idx_operation_log_operator_time', 'operator', 'timestamp'),
        Index('idx_operation_log_type_time', 'operation_type', 'timestamp'),
        Index('idx_operation_log_target', 'target_type', 'target_id'),
    )
    
    def __repr__(self):
        return f'<OperationLog {self.operator}: {self.operation_type}>'


class Policy(Base):
    """平台政策模型"""
    __tablename__ = 'policies'

    id = Column(Integer, primary_key=True)
    policy_type = Column(String(50), nullable=False, index=True)  # 政策类型
    title = Column(String(200), nullable=False)  # 政策标题
    content = Column(Text, nullable=False)  # 政策内容（富文本HTML）
    version = Column(String(20), nullable=False, default='1.0')  # 版本号
    status = Column(String(20), default='draft', index=True)  # draft, active, archived

    # 元数据
    summary = Column(String(500))  # 政策摘要
    keywords = Column(String(200))  # 关键词，用于搜索

    # 操作信息
    created_by = Column(String(50), nullable=False, index=True)
    updated_by = Column(String(50))
    published_by = Column(String(50))

    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    published_at = Column(DateTime, index=True)

    # 复合索引
    __table_args__ = (
        Index('idx_policy_type_status', 'policy_type', 'status'),
        Index('idx_policy_created', 'created_at'),
        Index('idx_policy_published', 'published_at'),
    )

    def __repr__(self):
        return f'<Policy {self.policy_type}: {self.title}>'

    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'policy_type': self.policy_type,
            'title': self.title,
            'content': self.content,
            'version': self.version,
            'status': self.status,
            'summary': self.summary,
            'keywords': self.keywords,
            'created_by': self.created_by,
            'updated_by': self.updated_by,
            'published_by': self.published_by,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'published_at': self.published_at.isoformat() if self.published_at else None
        }


class AdminUser(Base):
    """管理员用户模型"""
    __tablename__ = 'admin_users'

    id = Column(Integer, primary_key=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    password_hash = Column(String(128), nullable=False)
    salt = Column(String(32), nullable=False)
    email = Column(String(100), unique=True)
    full_name = Column(String(100))
    is_active = Column(Boolean, default=True, index=True)
    is_super_admin = Column(Boolean, default=False)

    # 密码相关
    password_changed = Column(Boolean, default=False)
    password_updated_at = Column(DateTime)
    login_attempts = Column(Integer, default=0)
    last_attempt_at = Column(DateTime)
    locked_until = Column(DateTime)

    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_login_at = Column(DateTime)
    last_login_ip = Column(String(45))

    # 创建信息
    created_by = Column(String(50))

    def __repr__(self):
        return f'<AdminUser {self.username}>'

    def to_dict(self):
        """转换为字典（不包含敏感信息）"""
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'full_name': self.full_name,
            'is_active': self.is_active,
            'is_super_admin': self.is_super_admin,
            'password_changed': self.password_changed,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'last_login_at': self.last_login_at.isoformat() if self.last_login_at else None
        }