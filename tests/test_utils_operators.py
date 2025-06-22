# -*- coding: utf-8 -*-
"""
操作员工具模块单元测试

测试src.utils.operators模块中的所有操作员相关函数，
确保它们能够正确获取和管理操作员信息。

测试覆盖：
1. 操作员信息获取
2. 操作员认证状态检查
3. 操作员权限获取
4. 操作员活动日志记录
5. 操作员显示名称格式化
6. 便捷函数测试

设计原则：
- 完整的功能覆盖
- 模拟外部依赖
- 错误情况处理
- 边界条件测试
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime
from flask import g, session

# 导入被测试的模块
from src.utils.operators import (
    get_current_operator,
    get_operator_info,
    is_operator_authenticated,
    get_operator_permissions,
    log_operator_activity,
    format_operator_display,
    current_operator,
    operator_info,
    is_authenticated
)


class TestGetCurrentOperator:
    """测试获取当前操作员函数"""

    @pytest.mark.utils
    def test_get_current_operator_from_g(self, app):
        """测试从Flask g对象获取操作员信息"""
        with app.app_context():
            with app.test_request_context():
                # 设置g对象中的操作员信息
                g.current_admin = 'test_admin_from_g'

                result = get_current_operator()
                assert result == 'test_admin_from_g'

    @pytest.mark.utils
    def test_get_current_operator_from_session(self, app, mock_admin_auth):
        """测试从session获取操作员信息"""
        with app.app_context():
            with app.test_request_context():
                # 清除g对象
                if hasattr(g, 'current_admin'):
                    delattr(g, 'current_admin')

                # 设置session
                session['admin_token'] = 'test_token'

                # 模拟AdminAuth
                with patch('src.utils.operators.AdminAuth') as mock_auth_class:
                    mock_auth_class.return_value = mock_admin_auth

                    result = get_current_operator()
                    assert result == 'test_admin'

                    # 验证缓存到g对象
                    assert g.current_admin == 'test_admin'

    @pytest.mark.utils
    def test_get_current_operator_no_session(self, app):
        """测试没有session时的默认返回"""
        with app.app_context():
            with app.test_request_context():
                # 清除g对象和session
                if hasattr(g, 'current_admin'):
                    delattr(g, 'current_admin')
                session.clear()

                result = get_current_operator()
                assert result == '未知用户'

    @pytest.mark.utils
    def test_get_current_operator_auth_error(self, app):
        """测试认证错误时的处理"""
        with app.app_context():
            with app.test_request_context():
                session['admin_token'] = 'invalid_token'

                # 模拟认证失败
                with patch('src.utils.operators.AdminAuth') as mock_auth_class:
                    mock_auth = Mock()
                    mock_auth.get_session_info.side_effect = Exception('认证失败')
                    mock_auth_class.return_value = mock_auth

                    result = get_current_operator()
                    assert result == '未知用户'


class TestGetOperatorInfo:
    """测试获取操作员详细信息函数"""

    @pytest.mark.utils
    def test_get_operator_info_complete(self, app, mock_admin_auth):
        """测试获取完整操作员信息"""
        with app.app_context():
            with app.test_request_context('/test', headers={'User-Agent': 'Test Browser'}):
                session['admin_token'] = 'test_token'

                with patch('src.utils.operators.AdminAuth') as mock_auth_class:
                    mock_auth_class.return_value = mock_admin_auth

                    result = get_operator_info()

                    # 验证基础信息
                    assert result['username'] == 'test_admin'
                    assert 'ip_address' in result
                    assert result['user_agent'] == 'Test Browser'
                    assert 'timestamp' in result

                    # 验证会话信息
                    assert result['session_id'] == 'test_token'
                    assert 'login_time' in result
                    assert 'permissions' in result

    @pytest.mark.utils
    def test_get_operator_info_no_session(self, app):
        """测试没有session时的操作员信息"""
        with app.app_context():
            with app.test_request_context():
                session.clear()

                result = get_operator_info()

                assert result['username'] == '未知用户'
                assert 'ip_address' in result
                assert 'timestamp' in result
                assert 'session_id' not in result

    @pytest.mark.utils
    def test_get_operator_info_error_handling(self, app):
        """测试错误处理"""
        with app.app_context():
            with app.test_request_context():
                session['admin_token'] = 'test_token'

                # 模拟获取会话信息失败
                with patch('src.utils.operators.AdminAuth') as mock_auth_class:
                    mock_auth = Mock()
                    mock_auth.get_session_info.side_effect = Exception('获取失败')
                    mock_auth_class.return_value = mock_auth

                    result = get_operator_info()

                    # 应该返回基础信息，但包含错误
                    assert 'username' in result
                    assert 'error' in result


class TestIsOperatorAuthenticated:
    """测试操作员认证状态检查函数"""

    @pytest.mark.utils
    def test_is_operator_authenticated_true(self, app, mock_admin_auth):
        """测试认证成功的情况"""
        with app.app_context():
            with app.test_request_context():
                session['admin_token'] = 'valid_token'

                with patch('src.utils.operators.AdminAuth') as mock_auth_class:
                    mock_auth_class.return_value = mock_admin_auth

                    result = is_operator_authenticated()
                    assert result == True

    @pytest.mark.utils
    def test_is_operator_authenticated_no_token(self, app):
        """测试没有token的情况"""
        with app.app_context():
            with app.test_request_context():
                session.clear()

                result = is_operator_authenticated()
                assert result == False

    @pytest.mark.utils
    def test_is_operator_authenticated_invalid_token(self, app):
        """测试无效token的情况"""
        with app.app_context():
            with app.test_request_context():
                session['admin_token'] = 'invalid_token'

                with patch('src.utils.operators.AdminAuth') as mock_auth_class:
                    mock_auth = Mock()
                    mock_auth.verify_session.return_value = False
                    mock_auth_class.return_value = mock_auth

                    result = is_operator_authenticated()
                    assert result == False

    @pytest.mark.utils
    def test_is_operator_authenticated_error(self, app):
        """测试认证过程中出错的情况"""
        with app.app_context():
            with app.test_request_context():
                session['admin_token'] = 'test_token'

                with patch('src.utils.operators.AdminAuth') as mock_auth_class:
                    mock_auth_class.side_effect = Exception('认证错误')

                    result = is_operator_authenticated()
                    assert result == False


class TestGetOperatorPermissions:
    """测试获取操作员权限函数"""

    @pytest.mark.utils
    def test_get_operator_permissions_success(self, app, mock_admin_auth):
        """测试成功获取权限"""
        with app.app_context():
            with app.test_request_context():
                session['admin_token'] = 'test_token'

                with patch('src.utils.operators.AdminAuth') as mock_auth_class:
                    mock_auth_class.return_value = mock_admin_auth

                    result = get_operator_permissions()
                    assert result == ['inventory_manage', 'user_manage']

    @pytest.mark.utils
    def test_get_operator_permissions_empty(self, app):
        """测试获取权限失败时返回空列表"""
        with app.app_context():
            with app.test_request_context():
                session.clear()

                result = get_operator_permissions()
                assert result == []

    @pytest.mark.utils
    def test_get_operator_permissions_error(self, app):
        """测试获取权限时出错"""
        with app.app_context():
            with app.test_request_context():
                session['admin_token'] = 'test_token'

                with patch('src.utils.operators.get_operator_info') as mock_get_info:
                    mock_get_info.side_effect = Exception('获取信息失败')

                    result = get_operator_permissions()
                    assert result == []


class TestLogOperatorActivity:
    """测试操作员活动日志记录函数"""

    @pytest.mark.utils
    def test_log_operator_activity_success(self, app, mock_admin_auth):
        """测试成功记录操作员活动"""
        with app.app_context():
            with app.test_request_context():
                session['admin_token'] = 'test_token'

                with patch('src.utils.operators.AdminAuth') as mock_auth_class:
                    mock_auth_class.return_value = mock_admin_auth

                    with patch('src.utils.operators.log_admin_operation') as mock_log:
                        result = log_operator_activity(
                            'create_product',
                            '创建新产品',
                            {'product_id': 123}
                        )

                        assert result == True
                        mock_log.assert_called_once()

                        # 验证调用参数
                        call_args = mock_log.call_args
                        assert call_args[1]['operator'] == 'test_admin'
                        assert call_args[1]['operation_type'] == 'create_product'
                        assert call_args[1]['result'] == 'success'

    @pytest.mark.utils
    def test_log_operator_activity_error(self, app):
        """测试记录活动时出错"""
        with app.app_context():
            with app.test_request_context():
                with patch('src.utils.operators.log_admin_operation') as mock_log:
                    mock_log.side_effect = Exception('记录失败')

                    result = log_operator_activity('test_action', '测试操作')
                    assert result == False

    @pytest.mark.utils
    def test_log_operator_activity_with_details(self, app, mock_admin_auth):
        """测试带详细信息的活动记录"""
        with app.app_context():
            with app.test_request_context():
                session['admin_token'] = 'test_token'

                with patch('src.utils.operators.AdminAuth') as mock_auth_class:
                    mock_auth_class.return_value = mock_admin_auth

                    with patch('src.utils.operators.log_admin_operation') as mock_log:
                        details = {'product_id': 456, 'product_name': '测试产品'}

                        result = log_operator_activity(
                            'update_product',
                            '更新产品信息',
                            details
                        )

                        assert result == True

                        # 验证详细信息被包含
                        call_args = mock_log.call_args
                        log_details = call_args[1]['details']
                        assert log_details['product_id'] == 456
                        assert log_details['product_name'] == '测试产品'


class TestFormatOperatorDisplay:
    """测试操作员显示名称格式化函数"""

    @pytest.mark.utils
    def test_format_operator_display_with_name(self, app):
        """测试格式化指定的操作员名称"""
        with app.app_context():
            result = format_operator_display('张三')
            assert result == '张三'

    @pytest.mark.utils
    def test_format_operator_display_unknown_user(self, app):
        """测试格式化未知用户"""
        with app.app_context():
            result = format_operator_display('未知用户')
            assert result == '系统管理员'

            result = format_operator_display('unknown')
            assert result == '系统管理员'

            result = format_operator_display('')
            assert result == '系统管理员'

    @pytest.mark.utils
    def test_format_operator_display_current_operator(self, app, mock_admin_auth):
        """测试格式化当前操作员"""
        with app.app_context():
            with app.test_request_context():
                session['admin_token'] = 'test_token'

                with patch('src.utils.operators.AdminAuth') as mock_auth_class:
                    mock_auth_class.return_value = mock_admin_auth

                    result = format_operator_display()
                    assert result == 'test_admin'

    @pytest.mark.utils
    def test_format_operator_display_no_current_operator(self, app):
        """测试没有当前操作员时的格式化"""
        with app.app_context():
            with app.test_request_context():
                session.clear()

                result = format_operator_display()
                assert result == '系统管理员'


class TestConvenienceFunctions:
    """测试便捷函数"""

    @pytest.mark.utils
    def test_current_operator_alias(self, app, mock_admin_auth):
        """测试current_operator别名函数"""
        with app.app_context():
            with app.test_request_context():
                session['admin_token'] = 'test_token'

                with patch('src.utils.operators.AdminAuth') as mock_auth_class:
                    mock_auth_class.return_value = mock_admin_auth

                    result = current_operator()
                    assert result == 'test_admin'

                    # 验证与原函数结果一致
                    assert result == get_current_operator()

    @pytest.mark.utils
    def test_operator_info_alias(self, app, mock_admin_auth):
        """测试operator_info别名函数"""
        with app.app_context():
            with app.test_request_context():
                session['admin_token'] = 'test_token'

                with patch('src.utils.operators.AdminAuth') as mock_auth_class:
                    mock_auth_class.return_value = mock_admin_auth

                    result = operator_info()
                    assert result['username'] == 'test_admin'

                    # 验证与原函数结果一致
                    assert result == get_operator_info()

    @pytest.mark.utils
    def test_is_authenticated_alias(self, app, mock_admin_auth):
        """测试is_authenticated别名函数"""
        with app.app_context():
            with app.test_request_context():
                session['admin_token'] = 'test_token'

                with patch('src.utils.operators.AdminAuth') as mock_auth_class:
                    mock_auth_class.return_value = mock_admin_auth

                    result = is_authenticated()
                    assert result == True

                    # 验证与原函数结果一致
                    assert result == is_operator_authenticated()


class TestEdgeCases:
    """测试边界情况"""

    @pytest.mark.utils
    def test_multiple_calls_caching(self, app, mock_admin_auth):
        """测试多次调用时的缓存行为"""
        with app.app_context():
            with app.test_request_context():
                session['admin_token'] = 'test_token'

                with patch('src.utils.operators.AdminAuth') as mock_auth_class:
                    mock_auth_class.return_value = mock_admin_auth

                    # 第一次调用
                    result1 = get_current_operator()
                    assert result1 == 'test_admin'

                    # 第二次调用应该使用缓存
                    result2 = get_current_operator()
                    assert result2 == 'test_admin'

                    # 验证AdminAuth只被调用一次
                    assert mock_auth_class.call_count == 1

    @pytest.mark.utils
    def test_session_info_none_handling(self, app):
        """测试session_info为None的处理"""
        with app.app_context():
            with app.test_request_context():
                session['admin_token'] = 'test_token'

                with patch('src.utils.operators.AdminAuth') as mock_auth_class:
                    mock_auth = Mock()
                    mock_auth.get_session_info.return_value = None
                    mock_auth_class.return_value = mock_auth

                    result = get_current_operator()
                    assert result == '未知用户'

    @pytest.mark.utils
    def test_session_info_invalid_format(self, app):
        """测试session_info格式无效的处理"""
        with app.app_context():
            with app.test_request_context():
                session['admin_token'] = 'test_token'

                with patch('src.utils.operators.AdminAuth') as mock_auth_class:
                    mock_auth = Mock()
                    mock_auth.get_session_info.return_value = 'invalid_format'  # 不是字典
                    mock_auth_class.return_value = mock_auth

                    result = get_current_operator()
                    assert result == '未知用户'

    @pytest.mark.utils
    def test_no_request_context(self, app):
        """测试没有请求上下文时的处理"""
        with app.app_context():
            # 不使用test_request_context
            result = get_operator_info()

            # 应该能正常处理，但IP和User-Agent为unknown
            assert result['username'] == '未知用户'
            assert result['ip_address'] == 'unknown'
            assert result['user_agent'] == 'unknown'