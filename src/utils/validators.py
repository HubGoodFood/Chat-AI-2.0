# -*- coding: utf-8 -*-
"""
请求验证器
"""
import logging
from typing import Dict, Any, Optional, Type
from pydantic import BaseModel, Field, validator
from flask import request
from functools import wraps
import bleach
from ..core.exceptions import ValidationError

logger = logging.getLogger(__name__)


class ValidationMiddleware:
    """验证中间件"""
    
    def __init__(self, app=None):
        self.app = app
        if app:
            self.init_app(app)
    
    def init_app(self, app):
        """初始化应用"""
        app.before_request(self.before_request)
    
    def before_request(self):
        """请求前验证"""
        # 验证Content-Type
        if request.method in ['POST', 'PUT', 'PATCH'] and request.path.startswith('/api/'):
            if request.content_type and 'application/json' not in request.content_type:
                raise ValidationError("Content-Type必须是application/json")


def validate_json(model_class: Type[BaseModel]):
    """JSON数据验证装饰器"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                data = request.get_json()
                if data is None:
                    raise ValidationError("请求体不能为空")
                
                # 使用Pydantic模型验证
                validated_data = model_class(**data)
                
                # 替换request中的JSON数据为验证后的数据
                request._cached_json = validated_data.dict()
                
                return func(*args, **kwargs)
                
            except ValidationError:
                raise
            except Exception as e:
                logger.error(f"数据验证失败: {e}")
                raise ValidationError(f"数据验证失败: {str(e)}")
        
        return wrapper
    return decorator


# 基础验证模型
class BaseRequest(BaseModel):
    """基础请求模型"""
    
    @validator('*', pre=True)
    def sanitize_strings(cls, value):
        """清理字符串输入"""
        if isinstance(value, str):
            # 移除HTML标签
            cleaned = bleach.clean(value, tags=[], strip=True)
            return cleaned.strip()
        return value


class ChatMessageRequest(BaseRequest):
    """聊天消息请求模型"""
    message: str = Field(..., min_length=1, max_length=1000, description="消息内容")
    session_id: Optional[str] = Field(None, max_length=100, description="会话ID")
    context: Optional[Dict[str, Any]] = Field(default_factory=dict, description="上下文信息")


class ProductCreateRequest(BaseRequest):
    """产品创建请求模型"""
    product_name: str = Field(..., min_length=1, max_length=100, description="产品名称")
    category: str = Field(..., min_length=1, max_length=50, description="产品分类")
    price: float = Field(..., ge=0, description="价格")
    unit: str = Field(default="个", max_length=20, description="单位")
    current_stock: int = Field(default=0, ge=0, description="当前库存")
    min_stock_warning: int = Field(default=10, ge=0, description="最低库存警告")
    specification: Optional[str] = Field(None, max_length=200, description="规格")
    description: Optional[str] = Field(None, max_length=500, description="描述")
    keywords: Optional[str] = Field(None, max_length=200, description="关键词")
    storage_area: str = Field(default="A1", max_length=20, description="存储区域")
    barcode: Optional[str] = Field(None, max_length=50, description="条码")


class ProductUpdateRequest(BaseRequest):
    """产品更新请求模型"""
    product_name: Optional[str] = Field(None, min_length=1, max_length=100, description="产品名称")
    category: Optional[str] = Field(None, min_length=1, max_length=50, description="产品分类")
    price: Optional[float] = Field(None, ge=0, description="价格")
    unit: Optional[str] = Field(None, max_length=20, description="单位")
    min_stock_warning: Optional[int] = Field(None, ge=0, description="最低库存警告")
    specification: Optional[str] = Field(None, max_length=200, description="规格")
    description: Optional[str] = Field(None, max_length=500, description="描述")
    keywords: Optional[str] = Field(None, max_length=200, description="关键词")
    storage_area: Optional[str] = Field(None, max_length=20, description="存储区域")
    barcode: Optional[str] = Field(None, max_length=50, description="条码")


class StockUpdateRequest(BaseRequest):
    """库存更新请求模型"""
    new_stock: int = Field(..., ge=0, description="新库存数量")
    note: Optional[str] = Field(None, max_length=200, description="备注")


class StockAdjustRequest(BaseRequest):
    """库存调整请求模型"""
    quantity_change: int = Field(..., description="数量变化")
    action: str = Field(..., description="操作类型")
    note: Optional[str] = Field(None, max_length=200, description="备注")


class AdminLoginRequest(BaseRequest):
    """管理员登录请求模型"""
    username: str = Field(..., min_length=3, max_length=50, description="用户名")
    password: str = Field(..., min_length=1, description="密码")


class AdminCreateRequest(BaseRequest):
    """管理员创建请求模型"""
    username: str = Field(..., min_length=3, max_length=50, description="用户名")
    password: str = Field(..., min_length=8, max_length=100, description="密码")
    email: Optional[str] = Field(None, max_length=100, description="邮箱")
    full_name: Optional[str] = Field(None, max_length=100, description="全名")
    is_super_admin: bool = Field(default=False, description="是否为超级管理员")


class PasswordChangeRequest(BaseRequest):
    """密码修改请求模型"""
    old_password: str = Field(..., min_length=1, description="原密码")
    new_password: str = Field(..., min_length=8, max_length=100, description="新密码")