# -*- coding: utf-8 -*-
"""
集成测试配置文件 - 提供集成测试专用的fixtures和工具

这个文件包含了集成测试需要的特殊配置和fixtures，
专门用于测试多个模块之间的交互和完整的业务流程。

主要功能：
1. 集成测试环境配置
2. 模拟外部服务
3. 测试数据工厂
4. 端到端测试工具
5. 业务流程验证工具

设计原则：
- 真实的业务场景模拟
- 稳定的测试环境
- 快速的测试执行
- 清晰的测试结果
"""
import pytest
import os
import tempfile
import json
import shutil
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta
import sqlite3

# Flask相关导入
from flask import Flask
from flask.testing import FlaskClient

# 项目模块导入
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

from src.utils.logger_config import get_logger
from src.models.admin_auth import AdminAuth
from src.models.inventory_manager import InventoryManager
from src.models.data_processor import DataProcessor
from src.models.knowledge_retriever import KnowledgeRetriever
from src.models.llm_client import LLMClient

logger = get_logger('integration_test_conftest')


@pytest.fixture(scope='session')
def integration_app():
    """
    创建集成测试专用的Flask应用实例
    
    这个fixture提供一个完整配置的Flask应用，
    用于端到端的集成测试。
    """
    # 创建临时目录用于集成测试
    test_dir = tempfile.mkdtemp(prefix='integration_test_')
    
    # 设置集成测试环境变量
    os.environ['FLASK_ENV'] = 'testing'
    os.environ['TESTING'] = 'true'
    os.environ['SECRET_KEY'] = 'integration-test-secret-key'
    os.environ['DATABASE_URL'] = f'sqlite:///{os.path.join(test_dir, "integration_test.db")}'
    
    try:
        from app import app as flask_app
        
        # 配置集成测试环境
        flask_app.config.update({
            'TESTING': True,
            'SECRET_KEY': 'integration-test-secret-key',
            'WTF_CSRF_ENABLED': False,
            'SERVER_NAME': 'localhost.localdomain',
            'APPLICATION_ROOT': '/',
            'PREFERRED_URL_SCHEME': 'http',
            'INTEGRATION_TEST_DATA_DIR': test_dir,
        })
        
        # 创建应用上下文
        with flask_app.app_context():
            yield flask_app
            
    finally:
        # 清理临时目录
        try:
            shutil.rmtree(test_dir)
        except Exception as e:
            logger.warning(f"清理集成测试临时目录失败: {e}")


@pytest.fixture(scope='function')
def integration_client(integration_app):
    """
    创建集成测试客户端
    
    提供一个Flask测试客户端，用于模拟HTTP请求
    和测试API端点的完整流程。
    """
    return integration_app.test_client()


@pytest.fixture(scope='function')
def integration_data_dir():
    """
    创建集成测试数据目录
    
    每个集成测试都会获得一个独立的数据目录，
    包含完整的测试数据集。
    """
    temp_dir = tempfile.mkdtemp(prefix='integration_data_')
    
    # 创建标准的数据文件结构
    data_files = {
        'products.csv': _create_test_products_csv(),
        'policy.json': _create_test_policy_json(),
        'inventory.json': _create_test_inventory_json(),
        'admin.json': _create_test_admin_json(),
        'feedback.json': _create_test_feedback_json()
    }
    
    for filename, content in data_files.items():
        file_path = os.path.join(temp_dir, filename)
        if filename.endswith('.json'):
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(content, f, ensure_ascii=False, indent=2)
        else:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
    
    yield temp_dir
    
    # 清理临时目录
    try:
        shutil.rmtree(temp_dir)
    except Exception as e:
        logger.warning(f"清理集成测试数据目录失败: {e}")


@pytest.fixture
def mock_llm_client():
    """
    模拟LLM客户端
    
    提供一个模拟的AI客户端，避免真实API调用，
    确保集成测试的稳定性和速度。
    """
    mock_client = Mock(spec=LLMClient)
    
    # 设置默认的模拟响应
    mock_client.generate_response.return_value = {
        'success': True,
        'response': '这是一个模拟的AI回答，用于集成测试。',
        'usage': {'total_tokens': 100}
    }
    
    # 模拟不同类型的查询响应
    def mock_generate_response(prompt, context=None):
        if '苹果' in prompt:
            return {
                'success': True,
                'response': '我们有优质的苹果，价格实惠，口感脆甜。',
                'usage': {'total_tokens': 80}
            }
        elif '政策' in prompt or '规则' in prompt:
            return {
                'success': True,
                'response': '关于我们的政策，请查看相关规定。',
                'usage': {'total_tokens': 60}
            }
        else:
            return {
                'success': True,
                'response': '感谢您的咨询，我会尽力为您解答。',
                'usage': {'total_tokens': 70}
            }
    
    mock_client.generate_response.side_effect = mock_generate_response
    
    return mock_client


@pytest.fixture
def authenticated_session(integration_client, integration_data_dir):
    """
    创建已认证的管理员会话
    
    提供一个已经登录的管理员会话，
    用于测试需要认证的功能。
    """
    # 模拟管理员登录
    login_data = {
        'username': 'test_admin',
        'password': 'test_password'
    }
    
    with patch('src.models.admin_auth.AdminAuth') as mock_auth:
        mock_auth.return_value.verify_credentials.return_value = True
        mock_auth.return_value.create_session.return_value = 'test_session_token'
        
        response = integration_client.post('/admin/login', 
                                         data=login_data,
                                         follow_redirects=True)
        
        # 设置会话cookie
        with integration_client.session_transaction() as sess:
            sess['admin_session'] = 'test_session_token'
            sess['admin_username'] = 'test_admin'
    
    return integration_client


def _create_test_products_csv():
    """创建测试用的产品CSV数据"""
    return """ProductName,Specification,Price,Unit,Category,Keywords,Taste,Origin,Benefits,SuitableFor
测试苹果,大果,10.0,斤,时令水果,苹果,脆甜,进口,高品质,苹果爱好者
测试香蕉,中等,8.0,斤,时令水果,香蕉,香甜,进口,营养丰富,所有人群
测试白菜,新鲜,3.0,斤,新鲜蔬菜,白菜,清脆,本地,维生素丰富,健康人群"""


def _create_test_policy_json():
    """创建测试用的政策JSON数据"""
    return {
        "mission": {
            "title": "平台介绍",
            "content": "测试平台介绍内容"
        },
        "group_rules": {
            "title": "群规管理", 
            "content": "测试群规管理内容"
        }
    }


def _create_test_inventory_json():
    """创建测试用的库存JSON数据"""
    return {
        "products": [],
        "storage_areas": [
            {"id": "A1", "name": "A区1号", "location": "仓库A区第1排"}
        ],
        "pickup_points": [
            {"id": "P1", "name": "测试取货点", "address": "测试地址"}
        ]
    }


def _create_test_admin_json():
    """创建测试用的管理员JSON数据"""
    return {
        "admins": [
            {
                "username": "test_admin",
                "password_hash": "test_hash",
                "permissions": ["inventory_manage", "user_manage"],
                "created_at": "2024-01-01T00:00:00"
            }
        ]
    }


def _create_test_feedback_json():
    """创建测试用的反馈JSON数据"""
    return {
        "feedback": []
    }
