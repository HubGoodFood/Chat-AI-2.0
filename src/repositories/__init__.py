# -*- coding: utf-8 -*-
"""
仓库模式包初始化
"""
from .base_repository import BaseRepository
from .product_repository import ProductRepository

__all__ = [
    'BaseRepository',
    'ProductRepository'
]