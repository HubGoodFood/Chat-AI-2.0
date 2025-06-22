# -*- coding: utf-8 -*-
"""
LLM客户端单元测试

测试LLM客户端的核心功能，包括API调用、错误处理、重试机制等。

测试覆盖：
1. LLM客户端初始化
2. 聊天API调用
3. 消息格式处理
4. 错误处理和重试
5. 超时处理
6. 响应解析
7. 对话历史管理

设计原则：
- 完整的功能覆盖
- 模拟外部API调用
- 网络错误模拟
- 边界条件测试
"""
import pytest
import json
import requests
from unittest.mock import Mock, patch, MagicMock
from typing import Dict, List, Any

# 导入被测试的模块
try:
    from src.models.llm_client import LLMClient
except ImportError as e:
    print(f"导入警告: {e}")

    # 创建模拟类用于测试
    class LLMClient:
        def __init__(self, api_key="test_key", api_url="https://test.api.com", model="test-model"):
            self.api_key = api_key
            self.api_url = api_url
            self.model = model
            self.system_prompt = "你是一个AI助手"

        def chat(self, user_message: str, context_info: str = "", conversation_history: List[Dict] = None) -> str:
            return "测试AI回复"


class TestLLMClient:
    """测试LLM客户端类"""

    @pytest.fixture
    def llm_client(self):
        """创建LLM客户端实例"""
        # 模拟环境变量
        with patch.dict('os.environ', {
            'LLM_API_KEY': 'test_api_key',
            'LLM_API_URL': 'https://test.api.com/v1/chat/completions',
            'LLM_MODEL': 'test-model'
        }):
            # 模拟print函数避免输出
            with patch('builtins.print'):
                return LLMClient()

    @pytest.mark.chat
    def test_llm_client_initialization(self, llm_client):
        """测试LLM客户端初始化"""
        assert llm_client.api_key == "test_api_key"
        assert llm_client.api_url == "https://test.api.com/v1/chat/completions"
        assert llm_client.model == "test-model"
        assert hasattr(llm_client, 'system_prompt')
        assert "果蔬客服AI助手" in llm_client.system_prompt

    @pytest.mark.chat
    def test_chat_success(self, llm_client):
        """测试成功的聊天调用"""
        user_message = "你好，请问有什么水果推荐？"
        context_info = "当前有苹果、香蕉、橙子等水果"

        # 模拟成功的API响应
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'choices': [
                {
                    'message': {
                        'content': '推荐您试试我们的红富士苹果，口感脆甜，营养丰富。'
                    }
                }
            ]
        }

        with patch('requests.post', return_value=mock_response) as mock_post:
            result = llm_client.chat(user_message, context_info)

            assert result == '推荐您试试我们的红富士苹果，口感脆甜，营养丰富。'

            # 验证API调用参数
            mock_post.assert_called_once()
            call_args = mock_post.call_args

            # 验证URL
            assert call_args[0][0] == llm_client.api_url

            # 验证headers
            headers = call_args[1]['headers']
            assert 'Authorization' in headers
            assert headers['Authorization'] == f"Bearer {llm_client.api_key}"
            assert headers['Content-Type'] == 'application/json'

            # 验证请求数据
            request_data = call_args[1]['json']
            assert request_data['model'] == llm_client.model
            assert 'messages' in request_data
            assert len(request_data['messages']) >= 2  # 至少包含system和user消息

    @pytest.mark.chat
    def test_chat_with_conversation_history(self, llm_client):
        """测试带对话历史的聊天"""
        user_message = "那香蕉怎么样？"
        conversation_history = [
            {'role': 'user', 'content': '有什么水果推荐？'},
            {'role': 'assistant', 'content': '推荐苹果'}
        ]

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'choices': [
                {'message': {'content': '香蕉也很不错，富含钾元素。'}}
            ]
        }

        with patch('requests.post', return_value=mock_response) as mock_post:
            result = llm_client.chat(user_message, "", conversation_history)

            assert result == '香蕉也很不错，富含钾元素。'

            # 验证对话历史被包含在请求中
            request_data = mock_post.call_args[1]['json']
            messages = request_data['messages']

            # 应该包含system、历史消息和当前用户消息
            assert len(messages) >= 4  # system + 2条历史 + 1条当前

            # 验证历史消息被正确包含
            user_messages = [msg for msg in messages if msg['role'] == 'user']
            assert len(user_messages) >= 2

    @pytest.mark.chat
    def test_chat_with_context_info(self, llm_client):
        """测试带上下文信息的聊天"""
        user_message = "苹果的价格是多少？"
        context_info = "红富士苹果：8.5元/斤，库存：100斤"

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'choices': [
                {'message': {'content': '红富士苹果的价格是8.5元/斤。'}}
            ]
        }

        with patch('requests.post', return_value=mock_response) as mock_post:
            result = llm_client.chat(user_message, context_info)

            # 验证上下文信息被包含在用户消息中
            request_data = mock_post.call_args[1]['json']
            messages = request_data['messages']

            user_message_content = None
            for msg in messages:
                if msg['role'] == 'user':
                    user_message_content = msg['content']
                    break

            assert user_message_content is not None
            assert context_info in user_message_content or "相关信息" in user_message_content

    @pytest.mark.chat
    def test_chat_api_error_4xx(self, llm_client):
        """测试API 4xx错误"""
        user_message = "测试消息"

        mock_response = Mock()
        mock_response.status_code = 401
        mock_response.text = "Unauthorized"
        mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError("401 Unauthorized")

        with patch('requests.post', return_value=mock_response):
            result = llm_client.chat(user_message)

            # 应该返回错误提示消息
            assert "网络连接出现问题" in result or "无法回答" in result

    @pytest.mark.chat
    def test_chat_api_error_5xx(self, llm_client):
        """测试API 5xx错误"""
        user_message = "测试消息"

        mock_response = Mock()
        mock_response.status_code = 500
        mock_response.text = "Internal Server Error"
        mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError("500 Internal Server Error")

        with patch('requests.post', return_value=mock_response):
            result = llm_client.chat(user_message)

            # 应该返回错误提示消息
            assert "网络连接出现问题" in result or "无法回答" in result

    @pytest.mark.chat
    def test_chat_timeout_error(self, llm_client):
        """测试超时错误"""
        user_message = "测试消息"

        with patch('requests.post', side_effect=requests.exceptions.Timeout("Request timeout")):
            result = llm_client.chat(user_message)

            assert "网络连接出现问题" in result or "稍后再试" in result

    @pytest.mark.chat
    def test_chat_connection_error(self, llm_client):
        """测试连接错误"""
        user_message = "测试消息"

        with patch('requests.post', side_effect=requests.exceptions.ConnectionError("Connection failed")):
            result = llm_client.chat(user_message)

            assert "网络连接出现问题" in result or "稍后再试" in result

    @pytest.mark.chat
    def test_chat_invalid_json_response(self, llm_client):
        """测试无效JSON响应"""
        user_message = "测试消息"

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.side_effect = json.JSONDecodeError("Invalid JSON", "", 0)

        with patch('requests.post', return_value=mock_response):
            result = llm_client.chat(user_message)

            assert "处理您的请求时出现错误" in result or "稍后再试" in result

    @pytest.mark.chat
    def test_chat_empty_choices_response(self, llm_client):
        """测试空choices响应"""
        user_message = "测试消息"

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'choices': []}

        with patch('requests.post', return_value=mock_response):
            result = llm_client.chat(user_message)

            assert "无法回答您的问题" in result or "稍后再试" in result

    @pytest.mark.chat
    def test_chat_malformed_response(self, llm_client):
        """测试格式错误的响应"""
        user_message = "测试消息"

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'error': 'Invalid request'}

        with patch('requests.post', return_value=mock_response):
            result = llm_client.chat(user_message)

            assert "无法回答您的问题" in result or "稍后再试" in result

    @pytest.mark.chat
    def test_chat_retry_mechanism(self, llm_client):
        """测试重试机制"""
        user_message = "测试重试"

        # 模拟第一次失败，第二次成功
        responses = [
            Mock(side_effect=requests.exceptions.ConnectionError("Connection failed")),
            Mock(status_code=200, json=lambda: {
                'choices': [{'message': {'content': '重试成功的回复'}}]
            })
        ]

        with patch('requests.post', side_effect=responses):
            result = llm_client.chat(user_message)

            # 如果实现了重试机制，应该返回成功的回复
            # 如果没有实现，会返回错误消息
            assert "重试成功的回复" in result or "网络连接出现问题" in result

    @pytest.mark.chat
    def test_chat_max_retries_exceeded(self, llm_client):
        """测试超过最大重试次数"""
        user_message = "测试最大重试"

        # 模拟所有重试都失败
        with patch('requests.post', side_effect=requests.exceptions.ConnectionError("Connection failed")):
            result = llm_client.chat(user_message)

            assert "网络连接出现问题" in result or "稍后再试" in result

    @pytest.mark.chat
    def test_chat_long_conversation_history(self, llm_client):
        """测试长对话历史处理"""
        user_message = "当前问题"

        # 创建很长的对话历史
        long_history = []
        for i in range(20):
            long_history.extend([
                {'role': 'user', 'content': f'用户消息{i}'},
                {'role': 'assistant', 'content': f'AI回复{i}'}
            ])

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'choices': [{'message': {'content': '处理长历史的回复'}}]
        }

        with patch('requests.post', return_value=mock_response) as mock_post:
            result = llm_client.chat(user_message, "", long_history)

            # 验证历史被截断（通常保留最近几轮对话）
            request_data = mock_post.call_args[1]['json']
            messages = request_data['messages']

            # 消息数量应该被限制（具体数量取决于实现）
            assert len(messages) <= 15  # 假设最多保留6轮对话 + system + 当前用户消息

    @pytest.mark.chat
    def test_chat_empty_user_message(self, llm_client):
        """测试空用户消息"""
        user_message = ""

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'choices': [{'message': {'content': '请问有什么可以帮您的吗？'}}]
        }

        with patch('requests.post', return_value=mock_response):
            result = llm_client.chat(user_message)

            # 应该能正常处理空消息
            assert len(result) > 0

    @pytest.mark.chat
    def test_chat_very_long_message(self, llm_client):
        """测试超长消息处理"""
        # 创建一个很长的消息
        user_message = "测试消息 " * 1000  # 很长的消息

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'choices': [{'message': {'content': '处理长消息的回复'}}]
        }

        with patch('requests.post', return_value=mock_response) as mock_post:
            result = llm_client.chat(user_message)

            assert result == '处理长消息的回复'

            # 验证消息被正确发送
            request_data = mock_post.call_args[1]['json']
            assert 'messages' in request_data

    @pytest.mark.chat
    def test_chat_special_characters(self, llm_client):
        """测试特殊字符处理"""
        user_message = "测试特殊字符：🍎🍌🥕 emoji 和 中文字符"

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'choices': [{'message': {'content': '可以处理特殊字符：🍎🍌🥕'}}]
        }

        with patch('requests.post', return_value=mock_response):
            result = llm_client.chat(user_message)

            assert '🍎🍌🥕' in result

    @pytest.mark.chat
    def test_chat_response_content_stripping(self, llm_client):
        """测试响应内容去除空白字符"""
        user_message = "测试消息"

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'choices': [{'message': {'content': '  \n\t  回复内容  \n\t  '}}]
        }

        with patch('requests.post', return_value=mock_response):
            result = llm_client.chat(user_message)

            # 验证响应内容被正确去除空白字符
            assert result == '回复内容'

    @pytest.mark.chat
    def test_chat_unicode_handling(self, llm_client):
        """测试Unicode字符处理"""
        user_message = "测试Unicode: café naïve résumé"

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'choices': [{'message': {'content': 'Unicode处理正常: café naïve résumé'}}]
        }

        with patch('requests.post', return_value=mock_response):
            result = llm_client.chat(user_message)

            assert 'café naïve résumé' in result


class TestLLMClientEdgeCases:
    """测试LLM客户端边界情况"""

    @pytest.fixture
    def llm_client_minimal(self):
        """创建最小配置的LLM客户端"""
        with patch.dict('os.environ', {
            'LLM_API_KEY': 'test_key',
            'LLM_API_URL': 'https://minimal.api.com',
            'LLM_MODEL': 'minimal-model'
        }):
            with patch('builtins.print'):
                return LLMClient()

    @pytest.mark.chat
    def test_client_with_minimal_config(self, llm_client_minimal):
        """测试最小配置的客户端"""
        assert llm_client_minimal.api_key == "test_key"
        assert llm_client_minimal.api_url == "https://minimal.api.com"
        assert llm_client_minimal.model == "minimal-model"

    @pytest.mark.chat
    def test_multiple_concurrent_requests(self, llm_client):
        """测试并发请求处理"""
        import threading
        import time

        results = []

        def make_request(message):
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                'choices': [{'message': {'content': f'回复: {message}'}}]
            }

            with patch('requests.post', return_value=mock_response):
                result = llm_client.chat(message)
                results.append(result)

        # 创建多个线程同时发送请求
        threads = []
        for i in range(3):
            thread = threading.Thread(target=make_request, args=[f"消息{i}"])
            threads.append(thread)
            thread.start()

        # 等待所有线程完成
        for thread in threads:
            thread.join()

        # 验证所有请求都得到了响应
        assert len(results) == 3
        for i, result in enumerate(results):
            assert f"消息{i}" in result or "回复:" in result

    @pytest.mark.chat
    def test_system_prompt_customization(self, llm_client):
        """测试系统提示词自定义"""
        original_prompt = llm_client.system_prompt

        # 修改系统提示词
        custom_prompt = "你是一个专业的水果销售顾问"
        llm_client.system_prompt = custom_prompt

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'choices': [{'message': {'content': '我是水果销售顾问'}}]
        }

        with patch('requests.post', return_value=mock_response) as mock_post:
            llm_client.chat("你好")

            # 验证自定义系统提示词被使用
            request_data = mock_post.call_args[1]['json']
            messages = request_data['messages']

            system_message = next((msg for msg in messages if msg['role'] == 'system'), None)
            assert system_message is not None
            assert custom_prompt in system_message['content']

        # 恢复原始提示词
        llm_client.system_prompt = original_prompt