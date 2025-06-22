# -*- coding: utf-8 -*-
"""
AI客服聊天流程集成测试

这个文件包含了AI客服系统的端到端集成测试，
验证从用户输入到AI回答的完整业务流程。

测试场景：
1. 基础聊天流程测试
2. 产品查询完整流程
3. 政策查询完整流程
4. 多语言支持测试
5. 错误处理和异常情况
6. 知识检索和AI生成集成

设计原则：
- 测试真实的用户场景
- 验证端到端的数据流
- 确保响应格式正确
- 检查业务逻辑完整性
"""
import pytest
import json
from unittest.mock import patch, Mock
from datetime import datetime

# 项目模块导入
from src.models.knowledge_retriever import KnowledgeRetriever
from src.models.data_processor import DataProcessor
from src.models.llm_client import LLMClient


class TestChatWorkflows:
    """AI客服聊天流程集成测试类"""

    @pytest.mark.integration
    @pytest.mark.chat
    def test_basic_chat_flow(self, integration_client, integration_data_dir, mock_llm_client):
        """
        测试基础聊天流程
        
        验证：用户输入 -> 意图识别 -> 知识检索 -> AI生成 -> 响应返回
        """
        # 模拟用户聊天请求
        chat_data = {
            'message': '你好，我想了解一下你们的服务',
            'language': 'zh'
        }
        
        with patch('src.models.llm_client.LLMClient', return_value=mock_llm_client):
            response = integration_client.post('/api/chat',
                                             json=chat_data,
                                             headers={'Content-Type': 'application/json'})
        
        # 验证响应状态
        assert response.status_code == 200
        
        # 验证响应格式
        data = response.get_json()
        assert data is not None
        assert 'success' in data
        assert 'response' in data
        assert data['success'] is True
        
        # 验证AI回答内容
        assert isinstance(data['response'], str)
        assert len(data['response']) > 0
        
        # 验证LLM客户端被正确调用
        mock_llm_client.generate_response.assert_called_once()

    @pytest.mark.integration
    @pytest.mark.chat
    def test_product_inquiry_workflow(self, integration_client, integration_data_dir, mock_llm_client):
        """
        测试产品查询完整工作流
        
        验证：产品查询 -> 数据检索 -> 信息整合 -> AI回答生成
        """
        # 配置模拟的产品查询响应
        mock_llm_client.generate_response.return_value = {
            'success': True,
            'response': '我们有优质的测试苹果，价格10元/斤，口感脆甜，适合苹果爱好者。',
            'usage': {'total_tokens': 120}
        }
        
        # 模拟产品查询请求
        chat_data = {
            'message': '请介绍一下苹果的价格和特点',
            'language': 'zh'
        }
        
        with patch('src.models.llm_client.LLMClient', return_value=mock_llm_client), \
             patch('src.models.data_processor.DataProcessor') as mock_processor:
            
            # 模拟数据处理器返回产品信息
            mock_processor.return_value.search_products.return_value = [
                {
                    'ProductName': '测试苹果',
                    'Price': '10.0',
                    'Unit': '斤',
                    'Taste': '脆甜',
                    'SuitableFor': '苹果爱好者'
                }
            ]
            
            response = integration_client.post('/api/chat',
                                             json=chat_data,
                                             headers={'Content-Type': 'application/json'})
        
        # 验证响应
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True
        
        # 验证产品信息被正确检索和使用
        assert '苹果' in data['response']
        assert '10' in data['response'] or '价格' in data['response']

    @pytest.mark.integration
    @pytest.mark.chat
    def test_policy_inquiry_workflow(self, integration_client, integration_data_dir, mock_llm_client):
        """
        测试政策查询完整工作流
        
        验证：政策查询 -> 政策检索 -> 信息整合 -> AI回答生成
        """
        # 配置模拟的政策查询响应
        mock_llm_client.generate_response.return_value = {
            'success': True,
            'response': '关于我们的平台介绍：测试平台介绍内容。',
            'usage': {'total_tokens': 90}
        }
        
        # 模拟政策查询请求
        chat_data = {
            'message': '请介绍一下你们的平台',
            'language': 'zh'
        }
        
        with patch('src.models.llm_client.LLMClient', return_value=mock_llm_client), \
             patch('src.models.data_processor.DataProcessor') as mock_processor:
            
            # 模拟数据处理器返回政策信息
            mock_processor.return_value.search_policies.return_value = [
                {
                    'title': '平台介绍',
                    'content': '测试平台介绍内容'
                }
            ]
            
            response = integration_client.post('/api/chat',
                                             json=chat_data,
                                             headers={'Content-Type': 'application/json'})
        
        # 验证响应
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True
        
        # 验证政策信息被正确检索和使用
        assert '平台' in data['response']

    @pytest.mark.integration
    @pytest.mark.chat
    def test_multilingual_chat_flow(self, integration_client, integration_data_dir, mock_llm_client):
        """
        测试多语言聊天流程
        
        验证：多语言输入 -> 语言识别 -> 对应语言回答
        """
        # 测试英文聊天
        mock_llm_client.generate_response.return_value = {
            'success': True,
            'response': 'Hello! Thank you for your inquiry.',
            'usage': {'total_tokens': 50}
        }
        
        chat_data = {
            'message': 'Hello, can you help me?',
            'language': 'en'
        }
        
        with patch('src.models.llm_client.LLMClient', return_value=mock_llm_client):
            response = integration_client.post('/api/chat',
                                             json=chat_data,
                                             headers={'Content-Type': 'application/json'})
        
        # 验证英文响应
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True
        assert 'Hello' in data['response'] or 'help' in data['response']

    @pytest.mark.integration
    @pytest.mark.chat
    def test_chat_error_handling(self, integration_client, integration_data_dir):
        """
        测试聊天错误处理流程
        
        验证：异常输入 -> 错误处理 -> 友好错误响应
        """
        # 测试空消息
        response = integration_client.post('/api/chat',
                                         json={'message': ''},
                                         headers={'Content-Type': 'application/json'})
        
        assert response.status_code == 400
        data = response.get_json()
        assert data['success'] is False
        assert 'error' in data
        
        # 测试无效JSON
        response = integration_client.post('/api/chat',
                                         data='invalid json',
                                         headers={'Content-Type': 'application/json'})
        
        assert response.status_code == 400

    @pytest.mark.integration
    @pytest.mark.chat
    def test_knowledge_retrieval_integration(self, integration_client, integration_data_dir, mock_llm_client):
        """
        测试知识检索与AI生成的集成
        
        验证：查询 -> 知识检索 -> 上下文构建 -> AI生成 -> 响应
        """
        # 模拟复杂查询，需要检索多种信息
        chat_data = {
            'message': '苹果的价格是多少？你们的配送政策是什么？',
            'language': 'zh'
        }
        
        # 配置复合查询的模拟响应
        mock_llm_client.generate_response.return_value = {
            'success': True,
            'response': '苹果价格10元/斤。关于配送政策，我们提供便民配送服务。',
            'usage': {'total_tokens': 150}
        }
        
        with patch('src.models.llm_client.LLMClient', return_value=mock_llm_client), \
             patch('src.models.knowledge_retriever.KnowledgeRetriever') as mock_retriever:
            
            # 模拟知识检索器返回综合信息
            mock_retriever.return_value.retrieve_relevant_info.return_value = {
                'products': [{'ProductName': '测试苹果', 'Price': '10.0'}],
                'policies': [{'title': '配送服务', 'content': '便民配送'}],
                'context': '用户询问苹果价格和配送政策'
            }
            
            response = integration_client.post('/api/chat',
                                             json=chat_data,
                                             headers={'Content-Type': 'application/json'})
        
        # 验证综合查询响应
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True
        
        # 验证回答包含了产品和政策信息
        response_text = data['response']
        assert '苹果' in response_text
        assert ('价格' in response_text or '10' in response_text)
        assert ('配送' in response_text or '政策' in response_text)

    @pytest.mark.integration
    @pytest.mark.chat
    @pytest.mark.slow
    def test_chat_session_continuity(self, integration_client, integration_data_dir, mock_llm_client):
        """
        测试聊天会话连续性
        
        验证：多轮对话 -> 上下文保持 -> 连贯回答
        """
        # 第一轮对话
        chat_data1 = {
            'message': '你们有什么水果？',
            'language': 'zh'
        }
        
        mock_llm_client.generate_response.return_value = {
            'success': True,
            'response': '我们有苹果、香蕉等新鲜水果。',
            'usage': {'total_tokens': 80}
        }
        
        with patch('src.models.llm_client.LLMClient', return_value=mock_llm_client):
            response1 = integration_client.post('/api/chat',
                                              json=chat_data1,
                                              headers={'Content-Type': 'application/json'})
        
        assert response1.status_code == 200
        data1 = response1.get_json()
        assert data1['success'] is True
        
        # 第二轮对话（基于上下文）
        chat_data2 = {
            'message': '苹果多少钱？',
            'language': 'zh'
        }
        
        mock_llm_client.generate_response.return_value = {
            'success': True,
            'response': '苹果价格是10元/斤。',
            'usage': {'total_tokens': 60}
        }
        
        with patch('src.models.llm_client.LLMClient', return_value=mock_llm_client):
            response2 = integration_client.post('/api/chat',
                                              json=chat_data2,
                                              headers={'Content-Type': 'application/json'})
        
        assert response2.status_code == 200
        data2 = response2.get_json()
        assert data2['success'] is True
        assert '苹果' in data2['response']
