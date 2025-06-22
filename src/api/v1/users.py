# -*- coding: utf-8 -*-
"""
用户API控制器 v1
"""
import logging
from flask import Blueprint, request, g, session
from ...core.service_registry import get_user_service
from ...core.response import ResponseBuilder, ResponseHelper
from ...core.exceptions import ValidationError, AuthenticationError
from ..version_control import api_version
from ...utils.validators import validate_json, AdminLoginRequest, AdminCreateRequest, PasswordChangeRequest

logger = logging.getLogger(__name__)

users_bp = Blueprint('users', __name__)


@users_bp.route('/admin/login', methods=['POST'])
@api_version()
@validate_json(AdminLoginRequest)
def admin_login():
    """管理员登录"""
    try:
        data = request.get_json()
        
        user_service = get_user_service()
        user_info = user_service.authenticate_admin(
            username=data['username'],
            password=data['password']
        )
        
        if not user_info:
            raise AuthenticationError("登录失败")
        
        # 设置会话
        session['admin_user'] = user_info
        session['admin_token'] = f"admin_{user_info['id']}"
        session.permanent = True
        
        # 记录登录日志
        logger.info(f"管理员登录成功: {user_info['username']} (ID: {user_info['id']})")
        
        response = ResponseBuilder.success(
            data={
                'user': user_info,
                'token': session['admin_token']
            },
            message="登录成功"
        )
        
        response.set_meta('login_time', request.json.get('timestamp') if request.json else None)
        
        return response.to_json_response()
        
    except Exception as e:
        logger.error(f"管理员登录失败: {e}")
        return ResponseHelper.handle_exception(e)


@users_bp.route('/admin/logout', methods=['POST'])
@api_version()
def admin_logout():
    """管理员登出"""
    try:
        user_info = session.get('admin_user')
        
        if user_info:
            logger.info(f"管理员登出: {user_info['username']} (ID: {user_info['id']})")
        
        # 清除会话
        session.clear()
        
        response = ResponseBuilder.success(message="登出成功")
        return response.to_json_response()
        
    except Exception as e:
        logger.error(f"管理员登出失败: {e}")
        return ResponseHelper.handle_exception(e)


@users_bp.route('/admin/profile', methods=['GET'])
@api_version()
def get_admin_profile():
    """获取管理员个人信息"""
    try:
        # 检查认证
        if 'admin_user' not in session:
            raise AuthenticationError("未登录")
        
        user_info = session['admin_user']
        user_id = user_info['id']
        
        # 从服务获取最新用户信息
        user_service = get_user_service()
        current_user = user_service.get_admin_user(user_id)
        
        if not current_user:
            raise AuthenticationError("用户不存在或已被禁用")
        
        response = ResponseBuilder.success(data=current_user)
        return response.to_json_response()
        
    except Exception as e:
        logger.error(f"获取管理员个人信息失败: {e}")
        return ResponseHelper.handle_exception(e)


@users_bp.route('/admin/profile', methods=['PUT'])
@api_version()
def update_admin_profile():
    """更新管理员个人信息"""
    try:
        # 检查认证
        if 'admin_user' not in session:
            raise AuthenticationError("未登录")
        
        user_info = session['admin_user']
        user_id = user_info['id']
        
        data = request.get_json()
        if not data:
            raise ValidationError("请求数据不能为空")
        
        # 只允许更新特定字段
        allowed_fields = ['email', 'full_name']
        update_data = {k: v for k, v in data.items() if k in allowed_fields}
        
        if not update_data:
            raise ValidationError("没有可更新的字段")
        
        user_service = get_user_service()
        success = user_service.update_admin_user(
            user_id=user_id,
            user_data=update_data,
            operator=user_info['username']
        )
        
        if not success:
            raise ValidationError("更新失败")
        
        # 获取更新后的用户信息
        updated_user = user_service.get_admin_user(user_id)
        
        # 更新会话中的用户信息
        session['admin_user'] = updated_user
        
        response = ResponseBuilder.success(
            data=updated_user,
            message="个人信息更新成功"
        )
        
        return response.to_json_response()
        
    except Exception as e:
        logger.error(f"更新管理员个人信息失败: {e}")
        return ResponseHelper.handle_exception(e)


@users_bp.route('/admin/password', methods=['PUT'])
@api_version()
@validate_json(PasswordChangeRequest)
def change_admin_password():
    """修改管理员密码"""
    try:
        # 检查认证
        if 'admin_user' not in session:
            raise AuthenticationError("未登录")
        
        user_info = session['admin_user']
        user_id = user_info['id']
        
        data = request.get_json()
        
        user_service = get_user_service()
        success = user_service.change_password(
            user_id=user_id,
            old_password=data['old_password'],
            new_password=data['new_password']
        )
        
        if not success:
            raise ValidationError("密码修改失败")
        
        logger.info(f"管理员密码修改成功: {user_info['username']} (ID: {user_id})")
        
        response = ResponseBuilder.success(message="密码修改成功")
        return response.to_json_response()
        
    except Exception as e:
        logger.error(f"修改管理员密码失败: {e}")
        return ResponseHelper.handle_exception(e)


@users_bp.route('/admin', methods=['POST'])
@api_version()
@validate_json(AdminCreateRequest)
def create_admin_user():
    """创建管理员用户"""
    try:
        # 检查认证
        if 'admin_user' not in session:
            raise AuthenticationError("未登录")
        
        current_user = session['admin_user']
        
        # 检查权限（只有超级管理员可以创建用户）
        if not current_user.get('is_super_admin'):
            raise ValidationError("权限不足，只有超级管理员可以创建用户")
        
        data = request.get_json()
        
        user_service = get_user_service()
        user_id = user_service.create_admin_user(
            user_data=data,
            creator=current_user['username']
        )
        
        # 获取创建的用户信息
        new_user = user_service.get_admin_user(user_id)
        
        logger.info(f"创建管理员用户成功: {data['username']} (ID: {user_id}) by {current_user['username']}")
        
        response = ResponseBuilder.success(
            data=new_user,
            message="管理员用户创建成功"
        )
        
        response.set_meta('user_id', user_id)
        
        return response.to_json_response(201)
        
    except Exception as e:
        logger.error(f"创建管理员用户失败: {e}")
        return ResponseHelper.handle_exception(e)


@users_bp.route('/admin/<int:user_id>', methods=['GET'])
@api_version()
def get_admin_user(user_id: int):
    """获取管理员用户信息"""
    try:
        # 检查认证
        if 'admin_user' not in session:
            raise AuthenticationError("未登录")
        
        current_user = session['admin_user']
        
        # 只能查看自己的信息，或者超级管理员可以查看所有用户
        if current_user['id'] != user_id and not current_user.get('is_super_admin'):
            raise ValidationError("权限不足")
        
        user_service = get_user_service()
        user_info = user_service.get_admin_user(user_id)
        
        if not user_info:
            raise ValidationError("用户不存在", field="user_id")
        
        response = ResponseBuilder.success(data=user_info)
        return response.to_json_response()
        
    except Exception as e:
        logger.error(f"获取管理员用户信息失败 {user_id}: {e}")
        return ResponseHelper.handle_exception(e)


@users_bp.route('/admin/<int:user_id>', methods=['PUT'])
@api_version()
def update_admin_user(user_id: int):
    """更新管理员用户信息"""
    try:
        # 检查认证
        if 'admin_user' not in session:
            raise AuthenticationError("未登录")
        
        current_user = session['admin_user']
        
        # 检查权限
        if not current_user.get('is_super_admin'):
            raise ValidationError("权限不足，只有超级管理员可以更新用户信息")
        
        data = request.get_json()
        if not data:
            raise ValidationError("请求数据不能为空")
        
        # 不允许更新的字段
        forbidden_fields = ['id', 'created_at', 'created_by']
        for field in forbidden_fields:
            if field in data:
                del data[field]
        
        user_service = get_user_service()
        success = user_service.update_admin_user(
            user_id=user_id,
            user_data=data,
            operator=current_user['username']
        )
        
        if not success:
            raise ValidationError("用户不存在或更新失败")
        
        # 获取更新后的用户信息
        updated_user = user_service.get_admin_user(user_id)
        
        logger.info(f"更新管理员用户成功: {user_id} by {current_user['username']}")
        
        response = ResponseBuilder.success(
            data=updated_user,
            message="用户信息更新成功"
        )
        
        return response.to_json_response()
        
    except Exception as e:
        logger.error(f"更新管理员用户失败 {user_id}: {e}")
        return ResponseHelper.handle_exception(e)


@users_bp.route('/admin/session', methods=['GET'])
@api_version()
def check_admin_session():
    """检查管理员会话状态"""
    try:
        if 'admin_user' in session and 'admin_token' in session:
            user_info = session['admin_user']
            
            # 验证用户是否仍然有效
            user_service = get_user_service()
            current_user = user_service.get_admin_user(user_info['id'])
            
            if current_user:
                response = ResponseBuilder.success(
                    data={
                        'authenticated': True,
                        'user': current_user,
                        'token': session['admin_token']
                    },
                    message="会话有效"
                )
            else:
                # 用户不存在或已禁用，清除会话
                session.clear()
                response = ResponseBuilder.success(
                    data={'authenticated': False},
                    message="会话无效"
                )
        else:
            response = ResponseBuilder.success(
                data={'authenticated': False},
                message="未登录"
            )
        
        return response.to_json_response()
        
    except Exception as e:
        logger.error(f"检查管理员会话失败: {e}")
        return ResponseHelper.handle_exception(e)