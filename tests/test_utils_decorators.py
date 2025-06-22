# -*- coding: utf-8 -*-
"""
装饰器模块单元测试

测试src.utils.decorators模块中的所有装饰器函数，
确保它们能够正确处理认证、验证、错误处理等功能。

测试覆盖：
1. 管理员认证装饰器
2. JSON数据验证装饰器
3. 错误处理装饰器
4. 操作日志装饰器
5. 速率限制装饰器
6. 文件上传验证装饰器

设计原则：
- 完整的功能覆盖
- 模拟外部依赖
- 错误情况处理
- 装饰器行为验证
"""
import pytest
import json
from unittest.mock import Mock, patch, MagicMock
from flask import Flask, request, session, g
from werkzeug.datastructures import FileStorage
import io

# 导入被测试的模块
from src.utils.decorators import (
    require_admin_auth,
    validate_json,
    handle_errors,
    log_operation,
    rate_limit,
    validate_file_upload
)


class TestRequireAdminAuth:
    """测试管理员认证装饰器"""

    @pytest.mark.utils
    def test_require_admin_auth_success(self, app, mock_admin_auth):
        """测试认证成功的情况"""
        with app.app_context():
            with app.test_request_context():
                session['admin_token'] = 'valid_token'

                @require_admin_auth
                def test_view():
                    return {'message': '成功访问'}

                with patch('src.utils.decorators.AdminAuth') as mock_auth_class:
                    mock_auth_class.return_value = mock_admin_auth

                    result = test_view()
                    assert result == {'message': '成功访问'}

                    # 验证g对象中设置了当前管理员
                    assert hasattr(g, 'current_admin')
                    assert g.current_admin == 'test_admin'

    @pytest.mark.utils
    def test_require_admin_auth_no_token(self, app):
        """测试没有token的情况"""
        with app.app_context():
            with app.test_request_context():
                session.clear()

                @require_admin_auth
                def test_view():
                    return {'message': '成功访问'}

                response, status_code = test_view()

                assert status_code == 401
                response_data = json.loads(response.get_data(as_text=True))
                assert response_data['success'] == False
                assert '未授权' in response_data['error']

    @pytest.mark.utils
    def test_require_admin_auth_invalid_token(self, app):
        """测试无效token的情况"""
        with app.app_context():
            with app.test_request_context():
                session['admin_token'] = 'invalid_token'

                @require_admin_auth
                def test_view():
                    return {'message': '成功访问'}

                with patch('src.utils.decorators.AdminAuth') as mock_auth_class:
                    mock_auth = Mock()
                    mock_auth.verify_session.return_value = False
                    mock_auth_class.return_value = mock_auth

                    response, status_code = test_view()

                    assert status_code == 401
                    response_data = json.loads(response.get_data(as_text=True))
                    assert response_data['success'] == False

    @pytest.mark.utils
    def test_require_admin_auth_exception(self, app):
        """测试认证过程中出现异常"""
        with app.app_context():
            with app.test_request_context():
                session['admin_token'] = 'test_token'

                @require_admin_auth
                def test_view():
                    return {'message': '成功访问'}

                with patch('src.utils.decorators.AdminAuth') as mock_auth_class:
                    mock_auth_class.side_effect = Exception('认证服务错误')

                    response, status_code = test_view()

                    assert status_code == 500
                    response_data = json.loads(response.get_data(as_text=True))
                    assert response_data['success'] == False


class TestValidateJson:
    """测试JSON数据验证装饰器"""

    def create_test_schema(self):
        """创建测试用的验证模式"""
        class TestSchema:
            def __init__(self):
                self.required_fields = ['name', 'price']
                self.field_types = {
                    'name': str,
                    'price': (int, float),
                    'description': str
                }

            def validate(self, data):
                errors = []

                # 检查必需字段
                for field in self.required_fields:
                    if field not in data:
                        errors.append(f'{field}是必需的')

                # 检查字段类型
                for field, expected_type in self.field_types.items():
                    if field in data:
                        if not isinstance(data[field], expected_type):
                            errors.append(f'{field}类型错误')

                if errors:
                    raise ValueError('; '.join(errors))

                return data

        return TestSchema()

    @pytest.mark.utils
    def test_validate_json_success(self, app):
        """测试JSON验证成功的情况"""
        schema = self.create_test_schema()

        with app.app_context():
            with app.test_request_context(
                '/test',
                method='POST',
                data=json.dumps({'name': '测试产品', 'price': 10.5}),
                content_type='application/json'
            ):
                @validate_json(schema)
                def test_view(validated_data):
                    return {'received': validated_data}

                result = test_view()
                assert result['received']['name'] == '测试产品'
                assert result['received']['price'] == 10.5

    @pytest.mark.utils
    def test_validate_json_missing_field(self, app):
        """测试缺少必需字段的情况"""
        schema = self.create_test_schema()

        with app.app_context():
            with app.test_request_context(
                '/test',
                method='POST',
                data=json.dumps({'name': '测试产品'}),  # 缺少price字段
                content_type='application/json'
            ):
                @validate_json(schema)
                def test_view(validated_data):
                    return {'received': validated_data}

                response, status_code = test_view()

                assert status_code == 400
                response_data = json.loads(response.get_data(as_text=True))
                assert response_data['success'] == False
                assert 'price是必需的' in response_data['error']

    @pytest.mark.utils
    def test_validate_json_invalid_type(self, app):
        """测试字段类型错误的情况"""
        schema = self.create_test_schema()

        with app.app_context():
            with app.test_request_context(
                '/test',
                method='POST',
                data=json.dumps({'name': '测试产品', 'price': 'invalid_price'}),
                content_type='application/json'
            ):
                @validate_json(schema)
                def test_view(validated_data):
                    return {'received': validated_data}

                response, status_code = test_view()

                assert status_code == 400
                response_data = json.loads(response.get_data(as_text=True))
                assert response_data['success'] == False
                assert 'price类型错误' in response_data['error']

    @pytest.mark.utils
    def test_validate_json_invalid_json(self, app):
        """测试无效JSON格式的情况"""
        schema = self.create_test_schema()

        with app.app_context():
            with app.test_request_context(
                '/test',
                method='POST',
                data='invalid json',
                content_type='application/json'
            ):
                @validate_json(schema)
                def test_view(validated_data):
                    return {'received': validated_data}

                response, status_code = test_view()

                assert status_code == 400
                response_data = json.loads(response.get_data(as_text=True))
                assert response_data['success'] == False
                assert 'JSON格式错误' in response_data['error']

    @pytest.mark.utils
    def test_validate_json_no_content_type(self, app):
        """测试没有正确Content-Type的情况"""
        schema = self.create_test_schema()

        with app.app_context():
            with app.test_request_context(
                '/test',
                method='POST',
                data=json.dumps({'name': '测试产品', 'price': 10.5})
                # 没有设置content_type
            ):
                @validate_json(schema)
                def test_view(validated_data):
                    return {'received': validated_data}

                response, status_code = test_view()

                assert status_code == 400
                response_data = json.loads(response.get_data(as_text=True))
                assert response_data['success'] == False