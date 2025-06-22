# -*- coding: utf-8 -*-
"""
测试配置文件 - 提供测试fixtures和工具函数

这个文件包含了所有测试需要的共享fixtures和工具函数，
确保测试环境的一致性和可重复性。

主要功能：
1. Flask应用测试实例
2. 测试数据库配置
3. 测试数据工厂
4. 认证相关fixtures
5. 模拟外部服务

设计原则：
- 隔离的测试环境
- 可重复的测试数据
- 快速的测试执行
- 清晰的测试结构
"""
import pytest
import os
import tempfile
import json
from unittest.mock import Mock, patch
from datetime import datetime, timedelta
import sqlite3

# Flask相关导入
from flask import Flask
from flask.testing import FlaskClient

# 项目模块导入
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.utils.logger_config import get_logger
from src.models.admin_auth import AdminAuth
from src.models.inventory_manager import InventoryManager
from src.models.data_processor import DataProcessor

logger = get_logger('test_conftest')


@pytest.fixture(scope='session')
def app():
    """
    创建Flask应用测试实例

    这个fixture在整个测试会话中只创建一次，
    提供一个干净的Flask应用实例用于测试。
    """
    # 创建临时目录用于测试
    test_dir = tempfile.mkdtemp()

    # 设置测试环境变量
    os.environ['FLASK_ENV'] = 'testing'
    os.environ['TESTING'] = 'true'
    os.environ['SECRET_KEY'] = 'test-secret-key-for-testing-only'
    os.environ['DATABASE_URL'] = f'sqlite:///{os.path.join(test_dir, "test.db")}'

    # 导入并创建应用
    try:
        from app import app as flask_app

        # 配置测试环境
        flask_app.config.update({
            'TESTING': True,
            'SECRET_KEY': 'test-secret-key-for-testing-only',
            'WTF_CSRF_ENABLED': False,
            'SERVER_NAME': 'localhost.localdomain',
            'APPLICATION_ROOT': '/',
            'PREFERRED_URL_SCHEME': 'http',
        })

        # 创建应用上下文
        with flask_app.app_context():
            yield flask_app

    except Exception as e:
        logger.error(f"创建测试应用失败: {e}")
        # 创建最小化的测试应用
        test_app = Flask(__name__)
        test_app.config.update({
            'TESTING': True,
            'SECRET_KEY': 'test-secret-key-for-testing-only',
            'WTF_CSRF_ENABLED': False,
        })
        yield test_app

    finally:
        # 清理临时文件
        import shutil
        try:
            shutil.rmtree(test_dir)
        except Exception as e:
            logger.warning(f"清理测试目录失败: {e}")


@pytest.fixture
def client(app):
    """
    创建Flask测试客户端

    用于发送HTTP请求到Flask应用进行测试。
    """
    return app.test_client()


@pytest.fixture
def runner(app):
    """
    创建Flask CLI测试运行器

    用于测试Flask命令行接口。
    """
    return app.test_cli_runner()


@pytest.fixture(scope='function')
def temp_data_dir():
    """
    创建临时数据目录

    每个测试函数都会获得一个独立的临时目录，
    用于存储测试数据文件。
    """
    temp_dir = tempfile.mkdtemp()
    yield temp_dir

    # 清理临时目录
    import shutil
    try:
        shutil.rmtree(temp_dir)
    except Exception as e:
        logger.warning(f"清理临时数据目录失败: {e}")


@pytest.fixture
def mock_admin_auth():
    """
    模拟管理员认证

    提供一个模拟的管理员认证实例，
    避免在测试中进行真实的认证操作。
    """
    mock_auth = Mock(spec=AdminAuth)

    # 设置默认的模拟行为
    mock_auth.verify_session.return_value = True
    mock_auth.get_session_info.return_value = {
        'username': 'test_admin',
        'login_time': datetime.utcnow().isoformat(),
        'last_activity': datetime.utcnow().isoformat(),
        'permissions': ['inventory_manage', 'user_manage']
    }
    mock_auth.create_session.return_value = 'test_session_token'

    return mock_auth


@pytest.fixture
def authenticated_session(client, mock_admin_auth):
    """
    创建已认证的会话

    返回一个已经登录的测试客户端，
    可以直接访问需要认证的端点。
    """
    with client.session_transaction() as sess:
        sess['admin_token'] = 'test_session_token'
        sess['admin_username'] = 'test_admin'

    # 模拟认证检查
    with patch('src.models.admin_auth.AdminAuth') as mock_auth_class:
        mock_auth_class.return_value = mock_admin_auth
        yield client


@pytest.fixture
def sample_products():
    """
    提供示例产品数据

    返回一组标准的测试产品数据，
    用于库存管理相关的测试。
    """
    return [
        {
            'id': 'PROD001',
            'product_name': '红富士苹果',
            'category': '水果',
            'price': 8.5,
            'current_stock': 100,
            'min_stock_warning': 10,
            'storage_area': 'A1',
            'barcode': '1234567890123',
            'status': 'active',
            'created_at': datetime.utcnow().isoformat(),
            'updated_at': datetime.utcnow().isoformat()
        },
        {
            'id': 'PROD002',
            'product_name': '有机胡萝卜',
            'category': '蔬菜',
            'price': 6.0,
            'current_stock': 50,
            'min_stock_warning': 5,
            'storage_area': 'B2',
            'barcode': '1234567890124',
            'status': 'active',
            'created_at': datetime.utcnow().isoformat(),
            'updated_at': datetime.utcnow().isoformat()
        },
        {
            'id': 'PROD003',
            'product_name': '新鲜白菜',
            'category': '蔬菜',
            'price': 3.5,
            'current_stock': 0,
            'min_stock_warning': 10,
            'storage_area': 'B1',
            'barcode': '1234567890125',
            'status': 'active',
            'created_at': datetime.utcnow().isoformat(),
            'updated_at': datetime.utcnow().isoformat()
        }
    ]


@pytest.fixture
def sample_inventory_data(temp_data_dir, sample_products):
    """
    创建示例库存数据文件

    在临时目录中创建包含示例数据的JSON文件，
    用于测试库存管理功能。
    """
    inventory_file = os.path.join(temp_data_dir, 'inventory.json')

    inventory_data = {
        'products': {product['id']: product for product in sample_products},
        'last_updated': datetime.utcnow().isoformat(),
        'version': '1.0'
    }

    with open(inventory_file, 'w', encoding='utf-8') as f:
        json.dump(inventory_data, f, ensure_ascii=False, indent=2)

    return inventory_file


@pytest.fixture
def mock_llm_client():
    """
    模拟LLM客户端

    提供一个模拟的LLM客户端，
    避免在测试中调用真实的AI服务。
    """
    mock_client = Mock()

    # 设置默认的模拟响应
    mock_client.chat_completion.return_value = {
        'choices': [{
            'message': {
                'content': '这是一个测试回复。我理解您的问题，这里是相关的产品信息。'
            }
        }],
        'usage': {
            'prompt_tokens': 50,
            'completion_tokens': 30,
            'total_tokens': 80
        }
    }

    return mock_client


@pytest.fixture
def mock_knowledge_retriever():
    """
    模拟知识检索器

    提供一个模拟的知识检索器，
    返回预定义的测试数据。
    """
    mock_retriever = Mock()

    # 设置默认的模拟行为
    mock_retriever.search_products_by_keyword.return_value = [
        {
            'ProductName': '红富士苹果',
            'Category': '水果',
            'Price': '8.5元/斤',
            'Description': '新鲜红富士苹果，口感脆甜'
        }
    ]

    mock_retriever.get_product_info.return_value = {
        'ProductName': '红富士苹果',
        'Category': '水果',
        'Price': '8.5元/斤',
        'Stock': '100斤',
        'Description': '新鲜红富士苹果，口感脆甜，营养丰富'
    }

    mock_retriever.analyze_intent.return_value = {
        'intent': 'product_inquiry',
        'entities': ['苹果'],
        'confidence': 0.95
    }

    return mock_retriever


@pytest.fixture
def sample_chat_messages():
    """
    提供示例聊天消息数据

    返回一组标准的测试聊天消息，
    用于AI客服相关的测试。
    """
    return [
        {
            'role': 'user',
            'content': '你好，请问有苹果吗？',
            'timestamp': datetime.utcnow().isoformat()
        },
        {
            'role': 'assistant',
            'content': '您好！我们有新鲜的红富士苹果，价格是8.5元/斤，目前库存充足。',
            'timestamp': datetime.utcnow().isoformat()
        },
        {
            'role': 'user',
            'content': '价格怎么样？',
            'timestamp': datetime.utcnow().isoformat()
        }
    ]


@pytest.fixture
def mock_barcode_generator():
    """
    模拟条形码生成器

    提供一个模拟的条形码生成器，
    避免在测试中生成真实的条形码图片。
    """
    mock_generator = Mock()

    # 设置默认的模拟行为
    mock_generator.generate_barcode.return_value = '1234567890123'
    mock_generator.generate_barcode_image.return_value = 'static/barcodes/test_barcode.png'
    mock_generator.validate_barcode.return_value = True

    return mock_generator


@pytest.fixture
def sample_storage_areas():
    """
    提供示例存储区域数据

    返回一组标准的测试存储区域数据，
    用于库存管理相关的测试。
    """
    return [
        {
            'id': 'A1',
            'name': '水果区域A1',
            'location': '仓库A区第1排',
            'capacity': 1000,
            'current_usage': 650,
            'temperature_range': '2-8°C',
            'humidity_range': '85-95%'
        },
        {
            'id': 'B1',
            'name': '蔬菜区域B1',
            'location': '仓库B区第1排',
            'capacity': 800,
            'current_usage': 400,
            'temperature_range': '0-4°C',
            'humidity_range': '90-95%'
        },
        {
            'id': 'B2',
            'name': '蔬菜区域B2',
            'location': '仓库B区第2排',
            'capacity': 800,
            'current_usage': 300,
            'temperature_range': '0-4°C',
            'humidity_range': '90-95%'
        }
    ]


@pytest.fixture
def sample_inventory_counts():
    """
    提供示例库存盘点数据

    返回一组标准的测试盘点数据，
    用于库存盘点相关的测试。
    """
    return [
        {
            'id': 'COUNT001',
            'product_id': 'PROD001',
            'product_name': '红富士苹果',
            'expected_quantity': 100,
            'actual_quantity': 98,
            'difference': -2,
            'operator': 'test_admin',
            'count_date': datetime.utcnow().isoformat(),
            'note': '正常损耗'
        },
        {
            'id': 'COUNT002',
            'product_id': 'PROD002',
            'product_name': '有机胡萝卜',
            'expected_quantity': 50,
            'actual_quantity': 52,
            'difference': 2,
            'operator': 'test_admin',
            'count_date': datetime.utcnow().isoformat(),
            'note': '发现额外库存'
        }
    ]


@pytest.fixture
def sample_feedback_data():
    """
    提供示例客户反馈数据

    返回一组标准的测试反馈数据，
    用于客户反馈管理相关的测试。
    """
    return [
        {
            'id': 'FB001',
            'customer_name': '张三',
            'customer_phone': '13800138001',
            'product_name': '红富士苹果',
            'purchase_date': '2025-06-20',
            'feedback_type': 'quality_issue',
            'feedback_content': '苹果有些软，不够新鲜',
            'images': ['feedback_001_1.jpg'],
            'status': 'pending',
            'created_at': datetime.utcnow().isoformat(),
            'updated_at': datetime.utcnow().isoformat()
        },
        {
            'id': 'FB002',
            'customer_name': '李四',
            'customer_phone': '13800138002',
            'product_name': '有机胡萝卜',
            'purchase_date': '2025-06-21',
            'feedback_type': 'praise',
            'feedback_content': '胡萝卜很新鲜，质量很好',
            'images': [],
            'status': 'resolved',
            'created_at': datetime.utcnow().isoformat(),
            'updated_at': datetime.utcnow().isoformat()
        }
    ]


# 测试工具函数
def assert_response_format(response_data, success=True):
    """
    验证响应格式是否符合标准

    Args:
        response_data: 响应数据字典
        success: 期望的成功状态
    """
    assert 'success' in response_data
    assert response_data['success'] == success
    assert 'timestamp' in response_data

    if success:
        assert 'message' in response_data
    else:
        assert 'error' in response_data


def assert_pagination_format(response_data):
    """
    验证分页响应格式是否符合标准

    Args:
        response_data: 响应数据字典
    """
    assert_response_format(response_data, success=True)
    assert 'data' in response_data

    data = response_data['data']
    assert 'items' in data
    assert 'pagination' in data

    pagination = data['pagination']
    required_fields = ['total', 'page', 'per_page', 'total_pages', 'has_next', 'has_prev']
    for field in required_fields:
        assert field in pagination


def create_test_request_data(data_type='product'):
    """
    创建测试请求数据

    Args:
        data_type: 数据类型 ('product', 'feedback', 'count')

    Returns:
        dict: 测试请求数据
    """
    if data_type == 'product':
        return {
            'product_name': '测试产品',
            'category': '测试分类',
            'price': 10.0,
            'current_stock': 100,
            'min_stock_warning': 10,
            'storage_area': 'A1'
        }
    elif data_type == 'feedback':
        return {
            'customer_name': '测试客户',
            'customer_phone': '13800138000',
            'product_name': '测试产品',
            'purchase_date': '2025-06-22',
            'feedback_type': 'quality_issue',
            'feedback_content': '测试反馈内容'
        }
    elif data_type == 'count':
        return {
            'product_id': 'PROD001',
            'actual_quantity': 95,
            'note': '测试盘点'
        }
    else:
        return {}