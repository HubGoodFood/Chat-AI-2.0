# -*- coding: utf-8 -*-
"""
服务接口定义
"""
from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass


@dataclass
class PaginationParams:
    """分页参数"""
    page: int = 1
    per_page: int = 20
    
    def __post_init__(self):
        self.page = max(1, self.page)
        self.per_page = min(max(1, self.per_page), 100)
    
    @property
    def offset(self) -> int:
        return (self.page - 1) * self.per_page


@dataclass
class PaginationResult:
    """分页结果"""
    items: List[Any]
    total: int
    page: int
    per_page: int
    
    @property
    def pages(self) -> int:
        return (self.total + self.per_page - 1) // self.per_page
    
    @property
    def has_prev(self) -> bool:
        return self.page > 1
    
    @property
    def has_next(self) -> bool:
        return self.page < self.pages


class IProductService(ABC):
    """产品服务接口"""
    
    @abstractmethod
    def get_product(self, product_id: int) -> Optional[Dict[str, Any]]:
        """获取产品详情"""
        pass
    
    @abstractmethod
    def get_product_by_barcode(self, barcode: str) -> Optional[Dict[str, Any]]:
        """根据条码获取产品"""
        pass
    
    @abstractmethod
    def search_products(self, query: str = None, **filters) -> PaginationResult:
        """搜索产品"""
        pass
    
    @abstractmethod
    def create_product(self, product_data: Dict[str, Any], operator: str) -> int:
        """创建产品"""
        pass
    
    @abstractmethod
    def update_product(self, product_id: int, product_data: Dict[str, Any], operator: str) -> bool:
        """更新产品"""
        pass
    
    @abstractmethod
    def delete_product(self, product_id: int, operator: str) -> bool:
        """删除产品"""
        pass
    
    @abstractmethod
    def get_categories(self) -> List[Dict[str, Any]]:
        """获取产品分类"""
        pass


class IInventoryService(ABC):
    """库存服务接口"""
    
    @abstractmethod
    def get_stock(self, product_id: int) -> Optional[Dict[str, Any]]:
        """获取库存信息"""
        pass
    
    @abstractmethod
    def update_stock(self, product_id: int, new_stock: int, operator: str, note: str = None) -> bool:
        """更新库存"""
        pass
    
    @abstractmethod
    def adjust_stock(self, product_id: int, quantity_change: int, action: str, operator: str, note: str = None) -> bool:
        """调整库存"""
        pass
    
    @abstractmethod
    def get_stock_history(self, product_id: int, pagination: PaginationParams) -> PaginationResult:
        """获取库存历史"""
        pass
    
    @abstractmethod
    def get_low_stock_products(self, threshold_multiplier: float = 1.0) -> List[Dict[str, Any]]:
        """获取低库存产品"""
        pass


class IUserService(ABC):
    """用户服务接口"""
    
    @abstractmethod
    def authenticate_admin(self, username: str, password: str) -> Optional[Dict[str, Any]]:
        """管理员认证"""
        pass
    
    @abstractmethod
    def get_admin_user(self, user_id: int) -> Optional[Dict[str, Any]]:
        """获取管理员用户"""
        pass
    
    @abstractmethod
    def create_admin_user(self, user_data: Dict[str, Any], creator: str) -> int:
        """创建管理员用户"""
        pass
    
    @abstractmethod
    def update_admin_user(self, user_id: int, user_data: Dict[str, Any], operator: str) -> bool:
        """更新管理员用户"""
        pass
    
    @abstractmethod
    def change_password(self, user_id: int, old_password: str, new_password: str) -> bool:
        """修改密码"""
        pass


class IChatService(ABC):
    """聊天服务接口"""
    
    @abstractmethod
    def process_message(self, message: str, session_id: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """处理用户消息"""
        pass
    
    @abstractmethod
    def get_conversation_history(self, session_id: str, limit: int = 20) -> List[Dict[str, Any]]:
        """获取对话历史"""
        pass
    
    @abstractmethod
    def clear_conversation(self, session_id: str) -> bool:
        """清除对话历史"""
        pass
    
    @abstractmethod
    def get_conversation_stats(self) -> Dict[str, Any]:
        """获取对话统计"""
        pass


class ISearchService(ABC):
    """搜索服务接口"""
    
    @abstractmethod
    def search(self, query: str, **filters) -> PaginationResult:
        """执行搜索"""
        pass
    
    @abstractmethod
    def get_suggestions(self, query: str, limit: int = 10) -> List[str]:
        """获取搜索建议"""
        pass
    
    @abstractmethod
    def get_facets(self) -> Dict[str, List[Dict[str, Any]]]:
        """获取搜索聚合信息"""
        pass
    
    @abstractmethod
    def index_product(self, product: Dict[str, Any]) -> bool:
        """索引产品"""
        pass
    
    @abstractmethod
    def remove_product(self, product_id: int) -> bool:
        """从索引中移除产品"""
        pass


class ICacheService(ABC):
    """缓存服务接口"""
    
    @abstractmethod
    def get(self, key: str) -> Any:
        """获取缓存"""
        pass
    
    @abstractmethod
    def set(self, key: str, value: Any, timeout: Optional[int] = None) -> bool:
        """设置缓存"""
        pass
    
    @abstractmethod
    def delete(self, key: str) -> bool:
        """删除缓存"""
        pass
    
    @abstractmethod
    def clear_pattern(self, pattern: str) -> int:
        """清除匹配模式的缓存"""
        pass
    
    @abstractmethod
    def get_stats(self) -> Dict[str, Any]:
        """获取缓存统计"""
        pass


class IConfigService(ABC):
    """配置服务接口"""
    
    @abstractmethod
    def get(self, key: str, default: Any = None) -> Any:
        """获取配置值"""
        pass
    
    @abstractmethod
    def get_section(self, section: str) -> Dict[str, Any]:
        """获取配置节"""
        pass
    
    @abstractmethod
    def set(self, key: str, value: Any) -> bool:
        """设置配置值"""
        pass
    
    @abstractmethod
    def reload(self) -> bool:
        """重新加载配置"""
        pass
    
    @abstractmethod
    def validate(self) -> Dict[str, Any]:
        """验证配置"""
        pass


class INotificationService(ABC):
    """通知服务接口"""
    
    @abstractmethod
    def send_notification(self, notification_type: str, recipients: List[str], data: Dict[str, Any]) -> bool:
        """发送通知"""
        pass
    
    @abstractmethod
    def send_email(self, to: List[str], subject: str, body: str, html_body: str = None) -> bool:
        """发送邮件"""
        pass
    
    @abstractmethod
    def send_sms(self, to: List[str], message: str) -> bool:
        """发送短信"""
        pass


class IAuditService(ABC):
    """审计日志服务接口"""
    
    @abstractmethod
    def log_operation(self, operator: str, operation_type: str, target_type: str, 
                     target_id: str, details: Dict[str, Any] = None) -> bool:
        """记录操作日志"""
        pass
    
    @abstractmethod
    def get_audit_logs(self, filters: Dict[str, Any], pagination: PaginationParams) -> PaginationResult:
        """获取审计日志"""
        pass
    
    @abstractmethod
    def get_operation_stats(self, start_date: str = None, end_date: str = None) -> Dict[str, Any]:
        """获取操作统计"""
        pass


class IFileService(ABC):
    """文件服务接口"""
    
    @abstractmethod
    def upload_file(self, file_data: bytes, filename: str, content_type: str = None) -> str:
        """上传文件"""
        pass
    
    @abstractmethod
    def get_file(self, file_id: str) -> Tuple[bytes, str, str]:
        """获取文件 (data, filename, content_type)"""
        pass
    
    @abstractmethod
    def delete_file(self, file_id: str) -> bool:
        """删除文件"""
        pass
    
    @abstractmethod
    def generate_presigned_url(self, file_id: str, expires_in: int = 3600) -> str:
        """生成预签名URL"""
        pass