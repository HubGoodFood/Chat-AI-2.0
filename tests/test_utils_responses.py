# -*- coding: utf-8 -*-
"""
响应模块单元测试

测试src.utils.responses模块中的所有响应函数，
确保它们能够正确生成标准化的API响应格式。

测试覆盖：
1. 成功响应格式
2. 错误响应格式
3. 分页响应格式
4. 验证错误响应格式
5. 各种HTTP状态码响应
6. 便捷函数测试

设计原则：
- 完整的功能覆盖
- 边界条件测试
- 错误情况处理
- 响应格式验证
"""
import pytest
import json
from datetime import datetime
from unittest.mock import patch

# 导入被测试的模块
from src.utils.responses import (
    success_response,
    error_response,
    validation_error_response,
    paginated_response,
    created_response,
    no_content_response,
    unauthorized_response,
    forbidden_response,
    not_found_response,
    conflict_response,
    rate_limit_response,
    server_error_response,
    api_success,
    api_error,
    api_not_found,
    api_unauthorized,
    api_forbidden
)

# 导入测试工具
from .conftest import assert_response_format, assert_pagination_format


class TestSuccessResponse:
    """测试成功响应函数"""

    @pytest.mark.utils
    def test_success_response_basic(self, app):
        """测试基本成功响应"""
        with app.app_context():
            response, status_code = success_response()

            assert status_code == 200

            # 解析响应数据
            response_data = json.loads(response.get_data(as_text=True))

            # 验证响应格式
            assert_response_format(response_data, success=True)
            assert response_data['message'] == '操作成功'
            assert 'data' not in response_data  # 没有数据时不应该有data字段

    @pytest.mark.utils
    def test_success_response_with_data(self, app):
        """测试带数据的成功响应"""
        test_data = {'product_id': 123, 'name': '测试产品'}

        with app.app_context():
            response, status_code = success_response(test_data, '产品创建成功')

            assert status_code == 200

            response_data = json.loads(response.get_data(as_text=True))

            assert_response_format(response_data, success=True)
            assert response_data['message'] == '产品创建成功'
            assert response_data['data'] == test_data

    @pytest.mark.utils
    def test_success_response_custom_status(self, app):
        """测试自定义状态码的成功响应"""
        with app.app_context():
            response, status_code = success_response(
                {'id': 456},
                '资源创建成功',
                201
            )

            assert status_code == 201

            response_data = json.loads(response.get_data(as_text=True))
            assert_response_format(response_data, success=True)
            assert response_data['data']['id'] == 456

    @pytest.mark.utils
    def test_success_response_timestamp_format(self, app):
        """测试时间戳格式"""
        with app.app_context():
            response, status_code = success_response()

            response_data = json.loads(response.get_data(as_text=True))

            # 验证时间戳格式
            timestamp = response_data['timestamp']
            assert isinstance(timestamp, str)

            # 验证时间戳可以被解析
            parsed_time = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            assert isinstance(parsed_time, datetime)


class TestErrorResponse:
    """测试错误响应函数"""

    @pytest.mark.utils
    def test_error_response_basic(self, app):
        """测试基本错误响应"""
        with app.app_context():
            response, status_code = error_response('操作失败')

            assert status_code == 400

            response_data = json.loads(response.get_data(as_text=True))

            assert_response_format(response_data, success=False)
            assert response_data['error'] == '操作失败'

    @pytest.mark.utils
    def test_error_response_with_code(self, app):
        """测试带错误代码的错误响应"""
        with app.app_context():
            response, status_code = error_response(
                '产品不存在',
                404,
                'PRODUCT_NOT_FOUND'
            )

            assert status_code == 404

            response_data = json.loads(response.get_data(as_text=True))

            assert_response_format(response_data, success=False)
            assert response_data['error'] == '产品不存在'
            assert response_data['error_code'] == 'PRODUCT_NOT_FOUND'

    @pytest.mark.utils
    def test_error_response_with_details(self, app):
        """测试带详细信息的错误响应"""
        details = {'field': 'product_name', 'issue': '不能为空'}

        with app.app_context():
            response, status_code = error_response(
                '验证失败',
                400,
                'VALIDATION_ERROR',
                details
            )

            response_data = json.loads(response.get_data(as_text=True))

            assert_response_format(response_data, success=False)
            assert response_data['details'] == details


class TestValidationErrorResponse:
    """测试验证错误响应函数"""

    @pytest.mark.utils
    def test_validation_error_string(self, app):
        """测试字符串格式的验证错误"""
        with app.app_context():
            response, status_code = validation_error_response('产品名称不能为空')

            assert status_code == 400

            response_data = json.loads(response.get_data(as_text=True))

            assert_response_format(response_data, success=False)
            assert '产品名称不能为空' in response_data['error']
            assert response_data['error_code'] == 'VALIDATION_ERROR'

    @pytest.mark.utils
    def test_validation_error_list(self, app):
        """测试列表格式的验证错误"""
        errors = ['产品名称不能为空', '价格必须大于0']

        with app.app_context():
            response, status_code = validation_error_response(errors)

            response_data = json.loads(response.get_data(as_text=True))

            assert_response_format(response_data, success=False)
            assert '产品名称不能为空' in response_data['error']
            assert '价格必须大于0' in response_data['error']

    @pytest.mark.utils
    def test_validation_error_dict(self, app):
        """测试字典格式的验证错误"""
        errors = {
            'product_name': '不能为空',
            'price': '必须大于0'
        }

        with app.app_context():
            response, status_code = validation_error_response(errors)

            response_data = json.loads(response.get_data(as_text=True))

            assert_response_format(response_data, success=False)
            assert 'product_name: 不能为空' in response_data['error']
            assert 'price: 必须大于0' in response_data['error']


class TestPaginatedResponse:
    """测试分页响应函数"""

    @pytest.mark.utils
    def test_paginated_response_basic(self, app):
        """测试基本分页响应"""
        items = [{'id': 1, 'name': '产品1'}, {'id': 2, 'name': '产品2'}]

        with app.app_context():
            response, status_code = paginated_response(
                items=items,
                total=100,
                page=1,
                per_page=20
            )

            assert status_code == 200

            response_data = json.loads(response.get_data(as_text=True))

            assert_pagination_format(response_data)

            data = response_data['data']
            assert data['items'] == items

            pagination = data['pagination']
            assert pagination['total'] == 100
            assert pagination['page'] == 1
            assert pagination['per_page'] == 20
            assert pagination['total_pages'] == 5
            assert pagination['has_next'] == True
            assert pagination['has_prev'] == False

    @pytest.mark.utils
    def test_paginated_response_middle_page(self, app):
        """测试中间页的分页响应"""
        items = [{'id': 21, 'name': '产品21'}]

        with app.app_context():
            response, status_code = paginated_response(
                items=items,
                total=100,
                page=3,
                per_page=20
            )

            response_data = json.loads(response.get_data(as_text=True))
            pagination = response_data['data']['pagination']

            assert pagination['has_next'] == True
            assert pagination['has_prev'] == True
            assert pagination['next_page'] == 4
            assert pagination['prev_page'] == 2

    @pytest.mark.utils
    def test_paginated_response_last_page(self, app):
        """测试最后一页的分页响应"""
        items = [{'id': 100, 'name': '产品100'}]

        with app.app_context():
            response, status_code = paginated_response(
                items=items,
                total=100,
                page=5,
                per_page=20
            )

            response_data = json.loads(response.get_data(as_text=True))
            pagination = response_data['data']['pagination']

            assert pagination['has_next'] == False
            assert pagination['has_prev'] == True
            assert 'next_page' not in pagination
            assert pagination['prev_page'] == 4


class TestSpecialResponses:
    """测试特殊响应函数"""

    @pytest.mark.utils
    def test_created_response(self, app):
        """测试创建响应"""
        data = {'product': {'name': '新产品'}}

        with app.app_context():
            response, status_code = created_response(data, '产品创建成功', 123)

            assert status_code == 201

            response_data = json.loads(response.get_data(as_text=True))

            assert_response_format(response_data, success=True)
            assert response_data['message'] == '产品创建成功'
            assert response_data['data']['id'] == 123
            assert response_data['data']['product']['name'] == '新产品'

    @pytest.mark.utils
    def test_no_content_response(self, app):
        """测试无内容响应"""
        with app.app_context():
            response, status_code = no_content_response('删除成功')

            assert status_code == 204

            response_data = json.loads(response.get_data(as_text=True))
            assert_response_format(response_data, success=True)
            assert response_data['message'] == '删除成功'

    @pytest.mark.utils
    def test_unauthorized_response(self, app):
        """测试未授权响应"""
        with app.app_context():
            response, status_code = unauthorized_response('需要登录')

            assert status_code == 401

            response_data = json.loads(response.get_data(as_text=True))
            assert_response_format(response_data, success=False)
            assert response_data['error'] == '需要登录'
            assert response_data['error_code'] == 'UNAUTHORIZED'

    @pytest.mark.utils
    def test_forbidden_response(self, app):
        """测试权限不足响应"""
        with app.app_context():
            response, status_code = forbidden_response('权限不足')

            assert status_code == 403

            response_data = json.loads(response.get_data(as_text=True))
            assert_response_format(response_data, success=False)
            assert response_data['error'] == '权限不足'
            assert response_data['error_code'] == 'FORBIDDEN'

    @pytest.mark.utils
    def test_not_found_response(self, app):
        """测试资源不存在响应"""
        with app.app_context():
            response, status_code = not_found_response('产品', 123)

            assert status_code == 404

            response_data = json.loads(response.get_data(as_text=True))
            assert_response_format(response_data, success=False)
            assert '产品(ID: 123)不存在' in response_data['error']
            assert response_data['error_code'] == 'NOT_FOUND'

    @pytest.mark.utils
    def test_conflict_response(self, app):
        """测试资源冲突响应"""
        details = {'existing_id': 456}

        with app.app_context():
            response, status_code = conflict_response('产品名称已存在', details)

            assert status_code == 409

            response_data = json.loads(response.get_data(as_text=True))
            assert_response_format(response_data, success=False)
            assert response_data['error'] == '产品名称已存在'
            assert response_data['error_code'] == 'CONFLICT'
            assert response_data['details'] == details

    @pytest.mark.utils
    def test_rate_limit_response(self, app):
        """测试速率限制响应"""
        with app.app_context():
            response, status_code = rate_limit_response('请求过多', 60)

            assert status_code == 429

            response_data = json.loads(response.get_data(as_text=True))
            assert_response_format(response_data, success=False)
            assert response_data['error'] == '请求过多'
            assert response_data['error_code'] == 'RATE_LIMIT_EXCEEDED'
            assert response_data['details']['retry_after'] == 60

    @pytest.mark.utils
    def test_server_error_response(self, app):
        """测试服务器错误响应"""
        with app.app_context():
            response, status_code = server_error_response('内部错误', 'ERR123')

            assert status_code == 500

            response_data = json.loads(response.get_data(as_text=True))
            assert_response_format(response_data, success=False)
            assert response_data['error'] == '内部错误'
            assert response_data['error_code'] == 'INTERNAL_ERROR'
            assert response_data['details']['error_id'] == 'ERR123'


class TestConvenienceFunctions:
    """测试便捷函数"""

    @pytest.mark.utils
    def test_api_success(self, app):
        """测试API成功便捷函数"""
        with app.app_context():
            response, status_code = api_success({'test': 'data'}, '测试成功')

            assert status_code == 200
            response_data = json.loads(response.get_data(as_text=True))
            assert_response_format(response_data, success=True)
            assert response_data['data']['test'] == 'data'

    @pytest.mark.utils
    def test_api_error(self, app):
        """测试API错误便捷函数"""
        with app.app_context():
            response, status_code = api_error('测试错误', 'TEST_ERROR')

            assert status_code == 400
            response_data = json.loads(response.get_data(as_text=True))
            assert_response_format(response_data, success=False)
            assert response_data['error_code'] == 'TEST_ERROR'

    @pytest.mark.utils
    def test_api_not_found(self, app):
        """测试API资源不存在便捷函数"""
        with app.app_context():
            response, status_code = api_not_found('测试资源', 999)

            assert status_code == 404
            response_data = json.loads(response.get_data(as_text=True))
            assert_response_format(response_data, success=False)
            assert '测试资源(ID: 999)不存在' in response_data['error']

    @pytest.mark.utils
    def test_api_unauthorized(self, app):
        """测试API未授权便捷函数"""
        with app.app_context():
            response, status_code = api_unauthorized('需要认证')

            assert status_code == 401
            response_data = json.loads(response.get_data(as_text=True))
            assert_response_format(response_data, success=False)
            assert response_data['error'] == '需要认证'

    @pytest.mark.utils
    def test_api_forbidden(self, app):
        """测试API权限不足便捷函数"""
        with app.app_context():
            response, status_code = api_forbidden('访问被拒绝')

            assert status_code == 403
            response_data = json.loads(response.get_data(as_text=True))
            assert_response_format(response_data, success=False)
            assert response_data['error'] == '访问被拒绝'


class TestEdgeCases:
    """测试边界情况"""

    @pytest.mark.utils
    def test_empty_data_handling(self, app):
        """测试空数据处理"""
        with app.app_context():
            # 测试空字符串
            response, _ = success_response('', '空字符串测试')
            response_data = json.loads(response.get_data(as_text=True))
            assert response_data['data'] == ''

            # 测试空列表
            response, _ = success_response([], '空列表测试')
            response_data = json.loads(response.get_data(as_text=True))
            assert response_data['data'] == []

            # 测试空字典
            response, _ = success_response({}, '空字典测试')
            response_data = json.loads(response.get_data(as_text=True))
            assert response_data['data'] == {}

    @pytest.mark.utils
    def test_zero_pagination(self, app):
        """测试零分页情况"""
        with app.app_context():
            response, status_code = paginated_response(
                items=[],
                total=0,
                page=1,
                per_page=20
            )

            response_data = json.loads(response.get_data(as_text=True))
            pagination = response_data['data']['pagination']

            assert pagination['total'] == 0
            assert pagination['total_pages'] == 0
            assert pagination['has_next'] == False
            assert pagination['has_prev'] == False

    @pytest.mark.utils
    def test_large_page_numbers(self, app):
        """测试大页码处理"""
        with app.app_context():
            response, status_code = paginated_response(
                items=[],
                total=100,
                page=999,  # 超出范围的页码
                per_page=20
            )

            response_data = json.loads(response.get_data(as_text=True))
            pagination = response_data['data']['pagination']

            # 应该正确计算总页数
            assert pagination['total_pages'] == 5
            assert pagination['has_next'] == False
            assert pagination['has_prev'] == True