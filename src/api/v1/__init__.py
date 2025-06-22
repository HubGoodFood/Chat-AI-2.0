# -*- coding: utf-8 -*-
"""
API v1 包
"""
from flask import Blueprint
from ..version_control import create_versioned_blueprint

# 创建 v1 版本的主Blueprint
api_v1_bp = create_versioned_blueprint('api', __name__, 'v1')

# 导入所有v1路由模块
from . import products
from . import inventory 
from . import users
from . import chat
from . import admin

# 注册子Blueprint
api_v1_bp.register_blueprint(products.products_bp, url_prefix='/products')
api_v1_bp.register_blueprint(inventory.inventory_bp, url_prefix='/inventory')
api_v1_bp.register_blueprint(users.users_bp, url_prefix='/users')
api_v1_bp.register_blueprint(chat.chat_bp, url_prefix='/chat')
api_v1_bp.register_blueprint(admin.admin_bp, url_prefix='/admin')

__all__ = ['api_v1_bp']