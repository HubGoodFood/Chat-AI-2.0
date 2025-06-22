# -*- coding: utf-8 -*-
"""
服务注册配置
"""
import logging
from .container import container
from .interfaces import (
    IProductService, IInventoryService, IUserService, IChatService,
    ISearchService, ICacheService, IConfigService
)
from .config import config_service
from ..services.impl.product_service_impl import ProductServiceImpl
from ..services.impl.inventory_service_impl import InventoryServiceImpl
from ..services.impl.user_service_impl import UserServiceImpl
from ..services.impl.chat_service_impl import ChatServiceImpl
from ..services.search_service import search_service
from ..services.cache_service import cache_service

logger = logging.getLogger(__name__)


def register_services():
    """注册所有服务到依赖注入容器"""
    try:
        # 注册配置服务
        container.register_instance(IConfigService, config_service)
        
        # 注册缓存服务
        container.register_instance(ICacheService, cache_service)
        
        # 注册搜索服务
        container.register_instance(ISearchService, search_service)
        
        # 注册业务服务（单例模式）
        container.register_singleton(IProductService, ProductServiceImpl)
        container.register_singleton(IInventoryService, InventoryServiceImpl)
        container.register_singleton(IUserService, UserServiceImpl)
        container.register_singleton(IChatService, ChatServiceImpl)
        
        logger.info("服务注册完成")
        
        # 打印已注册的服务
        registered_services = container.get_registered_services()
        logger.debug(f"已注册服务: {registered_services}")
        
    except Exception as e:
        logger.error(f"服务注册失败: {e}")
        raise


def get_service(interface_type):
    """获取服务实例的便利函数"""
    try:
        return container.resolve(interface_type)
    except Exception as e:
        logger.error(f"获取服务失败 {interface_type.__name__}: {e}")
        raise


# 服务快捷访问
def get_product_service() -> IProductService:
    """获取产品服务"""
    return get_service(IProductService)


def get_inventory_service() -> IInventoryService:
    """获取库存服务"""
    return get_service(IInventoryService)


def get_user_service() -> IUserService:
    """获取用户服务"""
    return get_service(IUserService)


def get_chat_service() -> IChatService:
    """获取聊天服务"""
    return get_service(IChatService)


def get_search_service() -> ISearchService:
    """获取搜索服务"""
    return get_service(ISearchService)


def get_cache_service() -> ICacheService:
    """获取缓存服务"""
    return get_service(ICacheService)


def get_config_service() -> IConfigService:
    """获取配置服务"""
    return get_service(IConfigService)