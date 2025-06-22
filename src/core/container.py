# -*- coding: utf-8 -*-
"""
依赖注入容器
"""
import logging
from typing import Dict, Type, Any, TypeVar, Callable, Optional
from functools import wraps
import inspect

logger = logging.getLogger(__name__)

T = TypeVar('T')


class DIContainer:
    """依赖注入容器"""
    
    def __init__(self):
        self._services: Dict[str, Any] = {}
        self._factories: Dict[str, Callable] = {}
        self._singletons: Dict[str, Any] = {}
        self._interfaces: Dict[Type, str] = {}
        self._configurations: Dict[str, Dict[str, Any]] = {}
    
    def register_singleton(self, interface: Type[T], implementation: Type[T], name: str = None) -> 'DIContainer':
        """注册单例服务"""
        service_name = name or self._get_service_name(interface)
        self._interfaces[interface] = service_name
        
        def factory():
            if service_name not in self._singletons:
                instance = self._create_instance(implementation)
                self._singletons[service_name] = instance
                logger.debug(f"创建单例服务: {service_name}")
            return self._singletons[service_name]
        
        self._factories[service_name] = factory
        return self
    
    def register_transient(self, interface: Type[T], implementation: Type[T], name: str = None) -> 'DIContainer':
        """注册瞬态服务"""
        service_name = name or self._get_service_name(interface)
        self._interfaces[interface] = service_name
        
        def factory():
            instance = self._create_instance(implementation)
            logger.debug(f"创建瞬态服务: {service_name}")
            return instance
        
        self._factories[service_name] = factory
        return self
    
    def register_instance(self, interface: Type[T], instance: T, name: str = None) -> 'DIContainer':
        """注册实例"""
        service_name = name or self._get_service_name(interface)
        self._interfaces[interface] = service_name
        self._singletons[service_name] = instance
        
        def factory():
            return self._singletons[service_name]
        
        self._factories[service_name] = factory
        logger.debug(f"注册服务实例: {service_name}")
        return self
    
    def register_factory(self, interface: Type[T], factory: Callable[[], T], name: str = None) -> 'DIContainer':
        """注册工厂方法"""
        service_name = name or self._get_service_name(interface)
        self._interfaces[interface] = service_name
        self._factories[service_name] = factory
        logger.debug(f"注册服务工厂: {service_name}")
        return self
    
    def configure(self, service_name: str, **config) -> 'DIContainer':
        """配置服务"""
        self._configurations[service_name] = config
        return self
    
    def resolve(self, interface: Type[T]) -> T:
        """解析服务"""
        if interface in self._interfaces:
            service_name = self._interfaces[interface]
            if service_name in self._factories:
                return self._factories[service_name]()
        
        # 尝试直接实例化
        try:
            return self._create_instance(interface)
        except Exception as e:
            raise RuntimeError(f"无法解析服务 {interface.__name__}: {e}")
    
    def resolve_by_name(self, name: str) -> Any:
        """根据名称解析服务"""
        if name in self._factories:
            return self._factories[name]()
        raise RuntimeError(f"未找到服务: {name}")
    
    def _create_instance(self, cls: Type[T]) -> T:
        """创建实例"""
        # 获取构造函数参数
        sig = inspect.signature(cls.__init__)
        params = {}
        
        for param_name, param in sig.parameters.items():
            if param_name == 'self':
                continue
            
            # 尝试从容器解析依赖
            if param.annotation != inspect.Parameter.empty:
                try:
                    params[param_name] = self.resolve(param.annotation)
                except RuntimeError:
                    # 如果无法解析，检查是否有默认值
                    if param.default != inspect.Parameter.empty:
                        params[param_name] = param.default
                    else:
                        # 检查配置
                        service_name = self._get_service_name(cls)
                        if service_name in self._configurations:
                            config = self._configurations[service_name]
                            if param_name in config:
                                params[param_name] = config[param_name]
                            else:
                                raise RuntimeError(f"无法解析参数 {param_name} for {cls.__name__}")
                        else:
                            raise RuntimeError(f"无法解析参数 {param_name} for {cls.__name__}")
            elif param.default == inspect.Parameter.empty:
                raise RuntimeError(f"无法解析参数 {param_name} for {cls.__name__}")
        
        return cls(**params)
    
    def _get_service_name(self, interface: Type) -> str:
        """获取服务名称"""
        return interface.__name__.lower().replace('i', '', 1) if interface.__name__.startswith('I') else interface.__name__.lower()
    
    def get_registered_services(self) -> Dict[str, str]:
        """获取已注册的服务列表"""
        return {
            interface.__name__: service_name 
            for interface, service_name in self._interfaces.items()
        }
    
    def clear(self):
        """清空容器"""
        self._services.clear()
        self._factories.clear()
        self._singletons.clear()
        self._interfaces.clear()
        self._configurations.clear()
        logger.debug("依赖注入容器已清空")


def inject(interface: Type[T]) -> Callable:
    """依赖注入装饰器"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # 注入依赖到函数参数
            sig = inspect.signature(func)
            bound_args = sig.bind_partial(*args, **kwargs)
            
            for param_name, param in sig.parameters.items():
                if param_name not in bound_args.arguments:
                    if param.annotation == interface:
                        service = container.resolve(interface)
                        bound_args.arguments[param_name] = service
            
            return func(*bound_args.args, **bound_args.kwargs)
        return wrapper
    return decorator


def service_factory(interface: Type[T]):
    """服务工厂装饰器"""
    def decorator(func: Callable[[], T]):
        container.register_factory(interface, func)
        return func
    return decorator


def singleton(interface: Type[T]):
    """单例服务装饰器"""
    def decorator(cls: Type[T]):
        container.register_singleton(interface, cls)
        return cls
    return decorator


def transient(interface: Type[T]):
    """瞬态服务装饰器"""
    def decorator(cls: Type[T]):
        container.register_transient(interface, cls)
        return cls
    return decorator


# 全局依赖注入容器实例
container = DIContainer()


class ServiceLocator:
    """服务定位器（备用方案）"""
    
    @staticmethod
    def get_service(interface: Type[T]) -> T:
        """获取服务"""
        return container.resolve(interface)
    
    @staticmethod
    def get_service_by_name(name: str) -> Any:
        """根据名称获取服务"""
        return container.resolve_by_name(name)


# 便利函数
def get_service(interface: Type[T]) -> T:
    """获取服务的便利函数"""
    return container.resolve(interface)