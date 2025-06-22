# -*- coding: utf-8 -*-
"""
操作员工具模块 - 提供操作员信息获取和管理功能

这个模块提供了统一的操作员信息获取接口，避免在各个路由中重复编写相同的逻辑。
主要功能包括：
1. 获取当前登录的管理员信息
2. 验证操作员权限
3. 记录操作员活动

设计原则：
- 统一的接口设计
- 安全的信息获取
- 详细的错误处理
- 完整的日志记录

使用示例：
    from src.utils.operators import get_current_operator, get_operator_info

    # 获取当前操作员名称
    operator = get_current_operator()

    # 获取详细操作员信息
    operator_info = get_operator_info()
"""
from flask import session, g, request
from typing import Dict, Optional, Any
from datetime import datetime
from .logger_config import get_logger

logger = get_logger('operators')


def get_current_operator() -> str:
    """
    获取当前操作员信息

    这是最常用的函数，用于获取当前登录管理员的用户名。
    会按照优先级顺序尝试不同的方式获取操作员信息。

    Returns:
        str: 操作员用户名，如果无法获取则返回默认值

    优先级顺序：
        1. Flask g对象中的current_admin（由认证装饰器设置）
        2. 通过session中的admin_token查询
        3. 返回默认值

    Example:
        operator = get_current_operator()
        print(f"当前操作员: {operator}")
    """
    try:
        # 优先从Flask g对象获取（由认证装饰器设置）
        if hasattr(g, 'current_admin') and g.current_admin:
            return g.current_admin

        # 从session获取admin_token并查询用户信息
        admin_token = session.get('admin_token')
        if admin_token:
            try:
                from src.models.admin_auth import AdminAuth
                admin_auth = AdminAuth()
                session_info = admin_auth.get_session_info(admin_token)

                if session_info and isinstance(session_info, dict):
                    username = session_info.get('username', '管理员')
                    # 缓存到g对象中，避免重复查询
                    g.current_admin = username
                    return username

            except Exception as e:
                logger.warning(f"通过token获取操作员信息失败: {e}")

        # 如果都无法获取，返回默认值
        return '未知用户'

    except Exception as e:
        logger.error(f"获取当前操作员信息时发生错误: {e}")
        return '未知用户'


def get_operator_info() -> Dict[str, Any]:
    """
    获取详细的操作员信息

    返回包含操作员详细信息的字典，用于需要更多操作员信息的场景。

    Returns:
        Dict[str, Any]: 包含操作员详细信息的字典

    返回字段：
        - username: 用户名
        - login_time: 登录时间
        - last_activity: 最后活动时间
        - ip_address: IP地址
        - user_agent: 用户代理
        - session_id: 会话ID
        - permissions: 权限列表（如果有的话）

    Example:
        info = get_operator_info()
        print(f"操作员: {info['username']}, 登录时间: {info['login_time']}")
    """
    try:
        # 基础信息
        operator_info = {
            'username': get_current_operator(),
            'ip_address': request.remote_addr if request else 'unknown',
            'user_agent': request.headers.get('User-Agent', 'unknown') if request else 'unknown',
            'timestamp': datetime.utcnow().isoformat()
        }

        # 尝试获取会话详细信息
        admin_token = session.get('admin_token')
        if admin_token:
            try:
                from src.models.admin_auth import AdminAuth
                admin_auth = AdminAuth()
                session_info = admin_auth.get_session_info(admin_token)

                if session_info and isinstance(session_info, dict):
                    # 添加会话信息
                    operator_info.update({
                        'session_id': admin_token,
                        'login_time': session_info.get('login_time'),
                        'last_activity': session_info.get('last_activity'),
                        'permissions': session_info.get('permissions', [])
                    })

            except Exception as e:
                logger.warning(f"获取会话详细信息失败: {e}")

        return operator_info

    except Exception as e:
        logger.error(f"获取操作员详细信息时发生错误: {e}")
        return {
            'username': '未知用户',
            'ip_address': 'unknown',
            'user_agent': 'unknown',
            'timestamp': datetime.utcnow().isoformat(),
            'error': str(e)
        }


def is_operator_authenticated() -> bool:
    """
    检查当前操作员是否已认证

    Returns:
        bool: True表示已认证，False表示未认证

    Example:
        if is_operator_authenticated():
            print("操作员已认证")
        else:
            print("需要登录")
    """
    try:
        admin_token = session.get('admin_token')
        if not admin_token:
            return False

        # 验证token有效性
        from src.models.admin_auth import AdminAuth
        admin_auth = AdminAuth()
        return admin_auth.verify_session(admin_token)

    except Exception as e:
        logger.warning(f"验证操作员认证状态失败: {e}")
        return False


def get_operator_permissions() -> list:
    """
    获取当前操作员的权限列表

    Returns:
        list: 权限列表，如果无法获取则返回空列表

    Example:
        permissions = get_operator_permissions()
        if 'inventory_manage' in permissions:
            print("有库存管理权限")
    """
    try:
        operator_info = get_operator_info()
        return operator_info.get('permissions', [])

    except Exception as e:
        logger.warning(f"获取操作员权限失败: {e}")
        return []


def log_operator_activity(
    activity_type: str,
    description: str,
    details: Dict = None
) -> bool:
    """
    记录操作员活动日志

    Args:
        activity_type: 活动类型（如 'login', 'logout', 'create_product'等）
        description: 活动描述
        details: 额外的活动详情

    Returns:
        bool: True表示记录成功，False表示记录失败

    Example:
        log_operator_activity(
            'create_product',
            '创建新产品',
            {'product_id': 123, 'product_name': '苹果'}
        )
    """
    try:
        from src.models.operation_logger import log_admin_operation

        operator = get_current_operator()
        operator_info = get_operator_info()

        # 构建日志详情
        log_details = {
            'activity_type': activity_type,
            'description': description,
            'operator_info': operator_info,
            'timestamp': datetime.utcnow().isoformat()
        }

        # 添加额外详情
        if details:
            log_details.update(details)

        # 记录日志
        log_admin_operation(
            operator=operator,
            operation_type=activity_type,
            target_type='system',
            target_id='activity',
            details=log_details,
            result='success'
        )

        return True

    except Exception as e:
        logger.error(f"记录操作员活动失败: {e}")
        return False


def format_operator_display(operator_name: str = None) -> str:
    """
    格式化操作员显示名称

    Args:
        operator_name: 操作员名称，如果不提供则获取当前操作员

    Returns:
        str: 格式化后的显示名称

    Example:
        display_name = format_operator_display()
        print(f"操作员: {display_name}")
    """
    if operator_name is None:
        operator_name = get_current_operator()

    # 如果是默认值，返回更友好的显示
    if operator_name in ['未知用户', 'unknown', '']:
        return '系统管理员'

    return operator_name


# 便捷函数
def current_operator():
    """get_current_operator的简化别名"""
    return get_current_operator()


def operator_info():
    """get_operator_info的简化别名"""
    return get_operator_info()


def is_authenticated():
    """is_operator_authenticated的简化别名"""
    return is_operator_authenticated()