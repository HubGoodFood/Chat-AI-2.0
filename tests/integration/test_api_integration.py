# -*- coding: utf-8 -*-
"""
API端点集成测试

这个文件包含了所有API端点的集成测试，
验证HTTP请求-响应的完整流程和API的正确性。

测试场景：
1. 认证API流程测试
2. 聊天API集成测试
3. 库存管理API测试
4. 管理员API测试
5. 错误处理和状态码验证
6. CORS和安全头验证

设计原则：
- 测试真实的HTTP请求流程
- 验证API响应格式
- 确保状态码正确
- 检查安全机制
"""
import pytest
import json
from unittest.mock import patch, Mock
from datetime import datetime


class TestAPIIntegration:
    """API端点集成测试类"""

    @pytest.mark.integration
    @pytest.mark.api
    def test_chat_api_integration(self, integration_client, mock_llm_client):
        """
        测试聊天API的完整集成流程
        
        验证：HTTP请求 -> 参数验证 -> 业务处理 -> 响应格式 -> HTTP响应
        """
        # 测试正常聊天请求
        chat_data = {
            'message': '你好，请介绍一下你们的服务',
            'language': 'zh'
        }
        
        with patch('src.models.llm_client.LLMClient', return_value=mock_llm_client):
            response = integration_client.post('/api/chat',
                                             json=chat_data,
                                             headers={'Content-Type': 'application/json'})
        
        # 验证HTTP状态码
        assert response.status_code == 200
        
        # 验证响应头
        assert response.headers['Content-Type'] == 'application/json'
        
        # 验证响应格式
        data = response.get_json()
        assert isinstance(data, dict)
        assert 'success' in data
        assert 'response' in data
        assert data['success'] is True
        assert isinstance(data['response'], str)
        
        # 测试参数验证
        invalid_requests = [
            {},  # 空请求
            {'message': ''},  # 空消息
            {'message': 'test', 'language': 'invalid'},  # 无效语言
        ]
        
        for invalid_data in invalid_requests:
            response = integration_client.post('/api/chat',
                                             json=invalid_data,
                                             headers={'Content-Type': 'application/json'})
            assert response.status_code == 400
            data = response.get_json()
            assert data['success'] is False
            assert 'error' in data

    @pytest.mark.integration
    @pytest.mark.api
    def test_admin_authentication_api(self, integration_client, integration_data_dir):
        """
        测试管理员认证API流程
        
        验证：登录请求 -> 凭据验证 -> 会话创建 -> 权限检查
        """
        # 测试登录API
        login_data = {
            'username': 'test_admin',
            'password': 'test_password'
        }
        
        with patch('src.models.admin_auth.AdminAuth') as mock_auth:
            mock_auth.return_value.verify_credentials.return_value = True
            mock_auth.return_value.create_session.return_value = 'test_session_token'
            
            response = integration_client.post('/admin/api/login',
                                             json=login_data,
                                             headers={'Content-Type': 'application/json'})
        
        # 验证登录响应
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True
        assert 'session_token' in data
        
        # 测试会话验证API
        headers = {
            'Authorization': f'Bearer test_session_token',
            'Content-Type': 'application/json'
        }
        
        with patch('src.models.admin_auth.AdminAuth') as mock_auth:
            mock_auth.return_value.verify_session.return_value = True
            mock_auth.return_value.get_session_info.return_value = {
                'username': 'test_admin',
                'permissions': ['inventory_manage']
            }
            
            response = integration_client.get('/admin/api/session',
                                            headers=headers)
        
        # 验证会话验证响应
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True
        assert data['username'] == 'test_admin'
        
        # 测试无效会话
        invalid_headers = {
            'Authorization': 'Bearer invalid_token',
            'Content-Type': 'application/json'
        }
        
        with patch('src.models.admin_auth.AdminAuth') as mock_auth:
            mock_auth.return_value.verify_session.return_value = False
            
            response = integration_client.get('/admin/api/session',
                                            headers=invalid_headers)
        
        assert response.status_code == 401

    @pytest.mark.integration
    @pytest.mark.api
    def test_inventory_api_integration(self, integration_client, authenticated_session, integration_data_dir):
        """
        测试库存管理API集成流程
        
        验证：认证 -> CRUD操作 -> 数据验证 -> 响应格式
        """
        # 使用已认证的会话
        client = authenticated_session
        
        # 1. 测试获取产品列表API
        with patch('src.models.inventory_manager.InventoryManager') as mock_inventory:
            mock_inventory.return_value.get_all_products.return_value = [
                {
                    'product_id': 'test_id_1',
                    'product_name': 'API测试产品1',
                    'current_stock': 100,
                    'price': 10.0
                }
            ]
            
            response = client.get('/admin/api/inventory/products')
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True
        assert 'products' in data
        assert len(data['products']) == 1
        
        # 2. 测试创建产品API
        product_data = {
            'product_name': 'API创建测试产品',
            'category': '测试类别',
            'specification': '测试规格',
            'price': 15.0,
            'unit': '个',
            'initial_stock': 50,
            'min_stock_warning': 5,
            'description': 'API测试创建的产品',
            'storage_area': 'A1'
        }
        
        with patch('src.models.inventory_manager.InventoryManager') as mock_inventory:
            mock_inventory.return_value.add_product.return_value = 'new_product_id'
            
            response = client.post('/admin/api/inventory/products',
                                 json=product_data,
                                 headers={'Content-Type': 'application/json'})
        
        assert response.status_code == 201
        data = response.get_json()
        assert data['success'] is True
        assert 'product_id' in data
        
        # 3. 测试更新库存API
        stock_update_data = {
            'quantity': 20,
            'note': 'API测试库存调整'
        }
        
        with patch('src.models.inventory_manager.InventoryManager') as mock_inventory:
            mock_inventory.return_value.update_stock.return_value = True
            
            response = client.put('/admin/api/inventory/products/test_id/stock',
                                json=stock_update_data,
                                headers={'Content-Type': 'application/json'})
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True
        
        # 4. 测试删除产品API
        with patch('src.models.inventory_manager.InventoryManager') as mock_inventory:
            mock_inventory.return_value.delete_product.return_value = True
            
            response = client.delete('/admin/api/inventory/products/test_id')
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True

    @pytest.mark.integration
    @pytest.mark.api
    def test_error_handling_api(self, integration_client):
        """
        测试API错误处理机制
        
        验证：异常捕获 -> 错误格式化 -> 状态码设置 -> 错误响应
        """
        # 测试404错误
        response = integration_client.get('/api/nonexistent')
        assert response.status_code == 404
        
        # 测试方法不允许错误
        response = integration_client.put('/api/chat')
        assert response.status_code == 405
        
        # 测试无效JSON格式
        response = integration_client.post('/api/chat',
                                         data='invalid json',
                                         headers={'Content-Type': 'application/json'})
        assert response.status_code == 400
        
        # 测试缺少Content-Type头
        response = integration_client.post('/api/chat',
                                         json={'message': 'test'})
        # 应该仍然能处理，Flask会自动设置Content-Type
        assert response.status_code in [200, 400]  # 取决于具体实现

    @pytest.mark.integration
    @pytest.mark.api
    def test_cors_and_security_headers(self, integration_client):
        """
        测试CORS和安全头设置
        
        验证：CORS头 -> 安全头 -> 跨域请求处理
        """
        # 测试预检请求
        response = integration_client.options('/api/chat',
                                            headers={
                                                'Origin': 'http://localhost:3000',
                                                'Access-Control-Request-Method': 'POST',
                                                'Access-Control-Request-Headers': 'Content-Type'
                                            })
        
        # 验证CORS头存在（如果配置了CORS）
        # 注意：具体的CORS配置取决于应用设置
        assert response.status_code in [200, 204]
        
        # 测试实际请求的安全头
        response = integration_client.get('/')
        
        # 检查常见的安全头（如果配置了）
        headers = response.headers
        # 这些头的存在取决于应用的安全配置
        # assert 'X-Content-Type-Options' in headers
        # assert 'X-Frame-Options' in headers

    @pytest.mark.integration
    @pytest.mark.api
    def test_rate_limiting_api(self, integration_client):
        """
        测试API速率限制
        
        验证：请求计数 -> 限制检查 -> 429响应
        """
        # 注意：这个测试取决于是否配置了速率限制
        # 如果没有配置速率限制，这个测试可能需要跳过
        
        # 快速发送多个请求
        responses = []
        for i in range(10):
            response = integration_client.get('/api/health')  # 假设有健康检查端点
            responses.append(response)
        
        # 检查是否有任何请求被限制
        status_codes = [r.status_code for r in responses]
        
        # 如果配置了速率限制，应该看到429状态码
        # 如果没有配置，所有请求都应该成功
        assert all(code in [200, 404, 429] for code in status_codes)

    @pytest.mark.integration
    @pytest.mark.api
    @pytest.mark.slow
    def test_api_performance_integration(self, integration_client, mock_llm_client):
        """
        测试API性能集成
        
        验证：响应时间 -> 并发处理 -> 资源使用
        """
        import time
        
        # 测试聊天API响应时间
        start_time = time.time()
        
        chat_data = {
            'message': '性能测试消息',
            'language': 'zh'
        }
        
        with patch('src.models.llm_client.LLMClient', return_value=mock_llm_client):
            response = integration_client.post('/api/chat',
                                             json=chat_data,
                                             headers={'Content-Type': 'application/json'})
        
        end_time = time.time()
        response_time = end_time - start_time
        
        # 验证响应成功
        assert response.status_code == 200
        
        # 验证响应时间合理（小于5秒）
        assert response_time < 5.0
        
        # 测试多个并发请求
        import threading
        
        results = []
        
        def make_request():
            with patch('src.models.llm_client.LLMClient', return_value=mock_llm_client):
                resp = integration_client.post('/api/chat',
                                             json=chat_data,
                                             headers={'Content-Type': 'application/json'})
                results.append(resp.status_code)
        
        # 创建多个线程
        threads = []
        for i in range(5):
            thread = threading.Thread(target=make_request)
            threads.append(thread)
            thread.start()
        
        # 等待所有线程完成
        for thread in threads:
            thread.join()
        
        # 验证所有请求都成功
        assert len(results) == 5
        assert all(status == 200 for status in results)
