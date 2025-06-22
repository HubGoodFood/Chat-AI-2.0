# -*- coding: utf-8 -*-
"""
管理员功能集成测试

这个文件包含了管理员系统的端到端集成测试，
验证管理员认证、权限控制、操作日志等完整业务流程。

测试场景：
1. 管理员登录和会话管理
2. 权限验证和访问控制
3. 管理员操作工作流
4. 操作日志记录
5. 数据导出功能
6. 安全机制验证

设计原则：
- 测试完整的管理员工作流
- 验证安全机制有效性
- 确保权限控制正确
- 检查操作审计完整
"""
import pytest
import json
import os
from unittest.mock import patch, Mock
from datetime import datetime, timedelta

# 项目模块导入
from src.models.admin_auth import AdminAuth
from src.models.operation_logger import OperationLogger
from src.models.data_exporter import DataExporter


class TestAdminIntegration:
    """管理员功能集成测试类"""

    @pytest.mark.integration
    @pytest.mark.auth
    def test_admin_login_workflow(self, integration_client, integration_data_dir):
        """
        测试管理员登录完整工作流
        
        验证：登录页面 -> 凭据验证 -> 会话创建 -> 重定向到控制台
        """
        # 1. 测试登录页面访问
        response = integration_client.get('/admin/login')
        assert response.status_code == 200
        assert b'login' in response.data.lower() or b'username' in response.data.lower()
        
        # 2. 测试有效登录
        login_data = {
            'username': 'test_admin',
            'password': 'test_password'
        }
        
        with patch('src.models.admin_auth.AdminAuth') as mock_auth:
            mock_auth.return_value.verify_credentials.return_value = True
            mock_auth.return_value.create_session.return_value = 'valid_session_token'
            
            response = integration_client.post('/admin/login',
                                             data=login_data,
                                             follow_redirects=True)
        
        # 验证登录成功重定向
        assert response.status_code == 200
        
        # 3. 测试无效登录
        invalid_login_data = {
            'username': 'invalid_user',
            'password': 'wrong_password'
        }
        
        with patch('src.models.admin_auth.AdminAuth') as mock_auth:
            mock_auth.return_value.verify_credentials.return_value = False
            
            response = integration_client.post('/admin/login',
                                             data=invalid_login_data,
                                             follow_redirects=True)
        
        # 验证登录失败处理
        assert response.status_code == 200
        # 应该返回到登录页面或显示错误信息

    @pytest.mark.integration
    @pytest.mark.auth
    def test_session_management_workflow(self, integration_client, integration_data_dir):
        """
        测试会话管理工作流
        
        验证：会话创建 -> 会话验证 -> 会话更新 -> 会话过期 -> 会话销毁
        """
        # 1. 创建会话
        with patch('src.models.admin_auth.AdminAuth') as mock_auth:
            mock_auth.return_value.verify_credentials.return_value = True
            mock_auth.return_value.create_session.return_value = 'test_session_123'
            
            login_data = {'username': 'test_admin', 'password': 'test_password'}
            response = integration_client.post('/admin/login', data=login_data)
        
        # 2. 验证会话有效性
        with integration_client.session_transaction() as sess:
            sess['admin_session'] = 'test_session_123'
            sess['admin_username'] = 'test_admin'
        
        with patch('src.models.admin_auth.AdminAuth') as mock_auth:
            mock_auth.return_value.verify_session.return_value = True
            mock_auth.return_value.get_session_info.return_value = {
                'username': 'test_admin',
                'login_time': datetime.utcnow().isoformat(),
                'last_activity': datetime.utcnow().isoformat(),
                'permissions': ['inventory_manage']
            }
            
            response = integration_client.get('/admin/dashboard')
        
        # 验证已认证用户可以访问控制台
        assert response.status_code == 200
        
        # 3. 测试会话过期
        with patch('src.models.admin_auth.AdminAuth') as mock_auth:
            mock_auth.return_value.verify_session.return_value = False
            
            response = integration_client.get('/admin/dashboard')
        
        # 验证过期会话被重定向到登录页面
        assert response.status_code in [302, 401]
        
        # 4. 测试登出
        with patch('src.models.admin_auth.AdminAuth') as mock_auth:
            mock_auth.return_value.destroy_session.return_value = True
            
            response = integration_client.post('/admin/logout', follow_redirects=True)
        
        assert response.status_code == 200

    @pytest.mark.integration
    @pytest.mark.auth
    def test_permission_control_workflow(self, integration_client, integration_data_dir):
        """
        测试权限控制工作流
        
        验证：权限检查 -> 访问控制 -> 操作限制 -> 权限拒绝处理
        """
        # 设置有限权限的管理员会话
        with integration_client.session_transaction() as sess:
            sess['admin_session'] = 'limited_session'
            sess['admin_username'] = 'limited_admin'
        
        # 1. 测试有权限的操作
        with patch('src.models.admin_auth.AdminAuth') as mock_auth:
            mock_auth.return_value.verify_session.return_value = True
            mock_auth.return_value.get_session_info.return_value = {
                'username': 'limited_admin',
                'permissions': ['inventory_view']  # 只有查看权限
            }
            
            response = integration_client.get('/admin/inventory/products')
        
        # 验证有权限的操作可以执行
        assert response.status_code == 200
        
        # 2. 测试无权限的操作
        with patch('src.models.admin_auth.AdminAuth') as mock_auth:
            mock_auth.return_value.verify_session.return_value = True
            mock_auth.return_value.get_session_info.return_value = {
                'username': 'limited_admin',
                'permissions': ['inventory_view']  # 没有管理权限
            }
            
            # 尝试创建产品（需要管理权限）
            product_data = {
                'product_name': '权限测试产品',
                'category': '测试',
                'price': 10.0
            }
            
            response = integration_client.post('/admin/inventory/products/add',
                                             data=product_data)
        
        # 验证无权限操作被拒绝
        assert response.status_code in [403, 302]  # 403禁止或302重定向

    @pytest.mark.integration
    @pytest.mark.auth
    def test_operation_logging_workflow(self, authenticated_session, integration_data_dir):
        """
        测试操作日志记录工作流
        
        验证：操作执行 -> 日志记录 -> 日志查询 -> 审计追踪
        """
        client = authenticated_session
        
        # 1. 执行需要记录的操作
        with patch('src.models.inventory_manager.InventoryManager') as mock_inventory, \
             patch('src.models.operation_logger.OperationLogger') as mock_logger:
            
            mock_inventory.return_value.add_product.return_value = 'new_product_id'
            mock_logger.return_value.log_operation.return_value = True
            
            product_data = {
                'product_name': '日志测试产品',
                'category': '测试类别',
                'price': 15.0,
                'unit': '个',
                'initial_stock': 100
            }
            
            response = client.post('/admin/inventory/products/add',
                                 data=product_data)
        
        # 验证操作成功
        assert response.status_code in [200, 201, 302]
        
        # 验证日志记录被调用
        mock_logger.return_value.log_operation.assert_called()
        
        # 2. 查询操作日志
        with patch('src.models.operation_logger.OperationLogger') as mock_logger:
            mock_logger.return_value.get_logs.return_value = [
                {
                    'timestamp': datetime.utcnow().isoformat(),
                    'operator': 'test_admin',
                    'action': 'create_product',
                    'target': 'new_product_id',
                    'details': {'product_name': '日志测试产品'}
                }
            ]
            
            response = client.get('/admin/logs')
        
        # 验证日志查询成功
        assert response.status_code == 200

    @pytest.mark.integration
    @pytest.mark.auth
    def test_data_export_workflow(self, authenticated_session, integration_data_dir):
        """
        测试数据导出工作流
        
        验证：导出请求 -> 数据收集 -> 文件生成 -> 下载响应
        """
        client = authenticated_session
        
        # 1. 测试库存数据导出
        with patch('src.models.data_exporter.DataExporter') as mock_exporter:
            mock_exporter.return_value.export_inventory.return_value = {
                'success': True,
                'file_path': '/tmp/inventory_export.xlsx',
                'file_name': 'inventory_export.xlsx'
            }
            
            response = client.post('/admin/export/inventory',
                                 data={'format': 'excel'})
        
        # 验证导出请求成功
        assert response.status_code in [200, 302]
        
        # 2. 测试反馈数据导出
        with patch('src.models.data_exporter.DataExporter') as mock_exporter:
            mock_exporter.return_value.export_feedback.return_value = {
                'success': True,
                'file_path': '/tmp/feedback_export.csv',
                'file_name': 'feedback_export.csv'
            }
            
            response = client.post('/admin/export/feedback',
                                 data={'format': 'csv'})
        
        # 验证导出请求成功
        assert response.status_code in [200, 302]

    @pytest.mark.integration
    @pytest.mark.auth
    def test_admin_dashboard_workflow(self, authenticated_session, integration_data_dir):
        """
        测试管理员控制台工作流
        
        验证：控制台访问 -> 数据统计 -> 快捷操作 -> 状态监控
        """
        client = authenticated_session
        
        # 1. 访问控制台主页
        with patch('src.models.inventory_manager.InventoryManager') as mock_inventory, \
             patch('src.models.feedback_manager.FeedbackManager') as mock_feedback:
            
            # 模拟统计数据
            mock_inventory.return_value.get_statistics.return_value = {
                'total_products': 50,
                'low_stock_count': 5,
                'total_value': 10000.0
            }
            
            mock_feedback.return_value.get_statistics.return_value = {
                'total_feedback': 20,
                'pending_count': 3,
                'resolved_count': 17
            }
            
            response = client.get('/admin/dashboard')
        
        # 验证控制台页面加载成功
        assert response.status_code == 200
        
        # 验证页面包含统计信息
        page_content = response.data.decode('utf-8')
        assert '50' in page_content or '产品' in page_content
        
        # 2. 测试快捷操作
        # 快速库存调整
        with patch('src.models.inventory_manager.InventoryManager') as mock_inventory:
            mock_inventory.return_value.update_stock.return_value = True
            
            quick_adjust_data = {
                'product_id': 'test_product_id',
                'quantity': 10,
                'note': '快速调整'
            }
            
            response = client.post('/admin/quick/stock-adjust',
                                 data=quick_adjust_data)
        
        # 验证快捷操作成功
        assert response.status_code in [200, 302]

    @pytest.mark.integration
    @pytest.mark.auth
    @pytest.mark.slow
    def test_complex_admin_scenario(self, integration_client, integration_data_dir):
        """
        测试复杂管理员场景
        
        验证：登录 -> 多项操作 -> 权限变更 -> 会话管理 -> 登出
        """
        # 1. 管理员登录
        login_data = {
            'username': 'super_admin',
            'password': 'super_password'
        }
        
        with patch('src.models.admin_auth.AdminAuth') as mock_auth:
            mock_auth.return_value.verify_credentials.return_value = True
            mock_auth.return_value.create_session.return_value = 'super_session'
            
            response = integration_client.post('/admin/login',
                                             data=login_data,
                                             follow_redirects=True)
        
        assert response.status_code == 200
        
        # 设置会话
        with integration_client.session_transaction() as sess:
            sess['admin_session'] = 'super_session'
            sess['admin_username'] = 'super_admin'
        
        # 2. 执行多项管理操作
        operations = [
            ('GET', '/admin/dashboard'),
            ('GET', '/admin/inventory/products'),
            ('GET', '/admin/feedback'),
            ('GET', '/admin/logs'),
        ]
        
        with patch('src.models.admin_auth.AdminAuth') as mock_auth:
            mock_auth.return_value.verify_session.return_value = True
            mock_auth.return_value.get_session_info.return_value = {
                'username': 'super_admin',
                'permissions': ['inventory_manage', 'user_manage', 'system_admin']
            }
            
            for method, url in operations:
                if method == 'GET':
                    response = integration_client.get(url)
                elif method == 'POST':
                    response = integration_client.post(url)
                
                # 验证所有操作都成功
                assert response.status_code == 200
        
        # 3. 测试会话活动更新
        with patch('src.models.admin_auth.AdminAuth') as mock_auth:
            mock_auth.return_value.verify_session.return_value = True
            mock_auth.return_value.update_session_activity.return_value = True
            
            response = integration_client.get('/admin/dashboard')
        
        assert response.status_code == 200
        
        # 4. 管理员登出
        with patch('src.models.admin_auth.AdminAuth') as mock_auth:
            mock_auth.return_value.destroy_session.return_value = True
            
            response = integration_client.post('/admin/logout',
                                             follow_redirects=True)
        
        assert response.status_code == 200
        
        # 5. 验证登出后无法访问管理页面
        response = integration_client.get('/admin/dashboard')
        assert response.status_code in [302, 401]  # 重定向到登录或401未授权
