# -*- coding: utf-8 -*-
"""
核心架构层
"""
from .container import container
from .interfaces import *
from .exceptions import *

__all__ = [
    'container',
    'IProductService',
    'IInventoryService', 
    'IUserService',
    'IChatService',
    'ISearchService',
    'ICacheService',
    'IConfigService',
    'BaseException',
    'ValidationError',
    'AuthenticationError',
    'PermissionError',
    'NotFoundError',
    'ConflictError',
    'ServiceError'
]