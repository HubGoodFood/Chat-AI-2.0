# -*- coding: utf-8 -*-
"""
Redis缓存服务
"""
import json
import logging
import hashlib
from typing import Any, Optional, Dict, List, Callable
from functools import wraps
import redis
import os
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class CacheService:
    """Redis缓存服务"""
    
    def __init__(self):
        self.redis_client = None
        self.memory_cache = {}  # 内存缓存降级
        self.cache_enabled = True
        self.memory_fallback = False
        self.default_timeout = 300  # 5分钟默认过期时间
        self._setup_redis()
    
    def _setup_redis(self):
        """设置Redis连接"""
        try:
            redis_url = os.environ.get('REDIS_URL', 'redis://localhost:6379/0')
            self.redis_client = redis.from_url(
                redis_url,
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5,
                retry_on_timeout=True,
                health_check_interval=30
            )
            
            # 测试连接
            self.redis_client.ping()
            logger.info("Redis缓存连接成功")
            
        except Exception as e:
            logger.warning(f"Redis连接失败，使用内存缓存: {e}")
            self.redis_client = None
            self.memory_fallback = True
    
    def _generate_key(self, prefix: str, *args, **kwargs) -> str:
        """生成缓存键"""
        # 创建包含所有参数的字符串
        key_parts = [prefix]
        
        # 添加位置参数
        for arg in args:
            if isinstance(arg, (dict, list)):
                key_parts.append(json.dumps(arg, sort_keys=True))
            else:
                key_parts.append(str(arg))
        
        # 添加关键字参数
        if kwargs:
            sorted_kwargs = sorted(kwargs.items())
            key_parts.append(json.dumps(sorted_kwargs))
        
        # 创建哈希以避免键名过长
        key_string = ":".join(key_parts)
        if len(key_string) > 200:
            key_hash = hashlib.md5(key_string.encode()).hexdigest()
            return f"{prefix}:hash:{key_hash}"
        
        return key_string
    
    def get(self, key: str) -> Any:
        """获取缓存值"""
        try:
            if self.redis_client and not self.memory_fallback:
                value = self.redis_client.get(key)
                if value is not None:
                    return json.loads(value)
            else:
                # 内存缓存
                cache_item = self.memory_cache.get(key)
                if cache_item:
                    if cache_item['expires'] > datetime.utcnow():
                        return cache_item['value']
                    else:
                        # 过期删除
                        del self.memory_cache[key]
            
            return None
            
        except Exception as e:
            logger.error(f"获取缓存失败 {key}: {e}")
            return None
    
    def set(self, key: str, value: Any, timeout: Optional[int] = None) -> bool:
        """设置缓存值"""
        try:
            if timeout is None:
                timeout = self.default_timeout
            
            serialized_value = json.dumps(value, ensure_ascii=False)
            
            if self.redis_client and not self.memory_fallback:
                return self.redis_client.setex(key, timeout, serialized_value)
            else:
                # 内存缓存
                expires = datetime.utcnow() + timedelta(seconds=timeout)
                self.memory_cache[key] = {
                    'value': value,
                    'expires': expires
                }
                
                # 清理过期的内存缓存
                self._cleanup_memory_cache()
                return True
                
        except Exception as e:
            logger.error(f"设置缓存失败 {key}: {e}")
            return False
    
    def delete(self, key: str) -> bool:
        """删除缓存"""
        try:
            if self.redis_client and not self.memory_fallback:
                return bool(self.redis_client.delete(key))
            else:
                if key in self.memory_cache:
                    del self.memory_cache[key]
                    return True
                return False
                
        except Exception as e:
            logger.error(f"删除缓存失败 {key}: {e}")
            return False
    
    def clear_pattern(self, pattern: str) -> int:
        """清除匹配模式的缓存"""
        try:
            if self.redis_client and not self.memory_fallback:
                keys = self.redis_client.keys(pattern)
                if keys:
                    return self.redis_client.delete(*keys)
                return 0
            else:
                # 内存缓存模式匹配
                import fnmatch
                matched_keys = [
                    key for key in self.memory_cache.keys()
                    if fnmatch.fnmatch(key, pattern)
                ]
                for key in matched_keys:
                    del self.memory_cache[key]
                return len(matched_keys)
                
        except Exception as e:
            logger.error(f"清除缓存模式失败 {pattern}: {e}")
            return 0
    
    def _cleanup_memory_cache(self):
        """清理过期的内存缓存"""
        current_time = datetime.utcnow()
        expired_keys = [
            key for key, item in self.memory_cache.items()
            if item['expires'] <= current_time
        ]
        for key in expired_keys:
            del self.memory_cache[key]
    
    def get_stats(self) -> Dict[str, Any]:
        """获取缓存统计信息"""
        try:
            if self.redis_client and not self.memory_fallback:
                info = self.redis_client.info()
                return {
                    'type': 'redis',
                    'connected': True,
                    'memory_usage': info.get('used_memory_human', 'N/A'),
                    'total_keys': info.get('db0', {}).get('keys', 0),
                    'hits': info.get('keyspace_hits', 0),
                    'misses': info.get('keyspace_misses', 0)
                }
            else:
                self._cleanup_memory_cache()
                return {
                    'type': 'memory',
                    'connected': False,
                    'total_keys': len(self.memory_cache),
                    'memory_fallback': True
                }
                
        except Exception as e:
            logger.error(f"获取缓存统计失败: {e}")
            return {'type': 'unknown', 'error': str(e)}


# 全局缓存服务实例
cache_service = CacheService()


def cached(prefix: str, timeout: Optional[int] = None, 
          key_func: Optional[Callable] = None):
    """缓存装饰器"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            if not cache_service.cache_enabled:
                return func(*args, **kwargs)
            
            # 生成缓存键
            if key_func:
                cache_key = key_func(*args, **kwargs)
            else:
                cache_key = cache_service._generate_key(prefix, *args, **kwargs)
            
            # 尝试获取缓存
            cached_result = cache_service.get(cache_key)
            if cached_result is not None:
                logger.debug(f"缓存命中: {cache_key}")
                return cached_result
            
            # 执行函数并缓存结果
            result = func(*args, **kwargs)
            if result is not None:
                cache_service.set(cache_key, result, timeout)
                logger.debug(f"缓存设置: {cache_key}")
            
            return result
        
        return wrapper
    return decorator


def cache_invalidate(pattern: str):
    """缓存失效装饰器"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            result = func(*args, **kwargs)
            # 执行成功后清除相关缓存
            if result:
                cache_service.clear_pattern(pattern)
                logger.debug(f"缓存失效: {pattern}")
            return result
        return wrapper
    return decorator


class CacheKeys:
    """缓存键常量"""
    
    # 产品相关
    PRODUCT_BY_ID = "product:id:{}"
    PRODUCT_BY_BARCODE = "product:barcode:{}"
    PRODUCT_SEARCH = "product:search"
    PRODUCT_CATEGORIES = "product:categories"
    PRODUCT_STORAGE_AREAS = "product:storage_areas"
    PRODUCT_LOW_STOCK = "product:low_stock"
    PRODUCT_STATISTICS = "product:statistics"
    
    # 库存相关
    STOCK_HISTORY = "stock:history:{}"
    
    # 用户相关
    ADMIN_USER = "admin:user:{}"
    USER_SESSION = "session:user:{}"
    
    # 反馈相关
    FEEDBACK_LIST = "feedback:list"
    
    # 系统相关
    SYSTEM_CONFIG = "system:config"
    API_RATE_LIMIT = "rate_limit:{}:{}"


def invalidate_product_cache(product_id: Optional[int] = None):
    """使产品相关缓存失效"""
    patterns = [
        "product:search*",
        "product:categories*",
        "product:storage_areas*",
        "product:low_stock*",
        "product:statistics*"
    ]
    
    if product_id:
        patterns.extend([
            f"product:id:{product_id}",
            f"stock:history:{product_id}"
        ])
    
    for pattern in patterns:
        cache_service.clear_pattern(pattern)