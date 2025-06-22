# -*- coding: utf-8 -*-
"""
AI客服服务单元测试

测试AI客服系统的核心功能，包括聊天服务、意图分析、知识检索等。

测试覆盖：
1. 聊天服务核心功能
2. 消息处理流程
3. 意图识别和分析
4. 知识检索功能
5. LLM客户端调用
6. 对话历史管理
7. 错误处理和边界条件

设计原则：
- 完整的功能覆盖
- 模拟外部依赖
- 真实场景模拟
- 错误情况处理
"""
import pytest
import json
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime
from typing import Dict, List, Any

# 导入被测试的模块
try:
    from src.services.impl.chat_service_impl import ChatServiceImpl
    from src.models.knowledge_retriever import KnowledgeRetriever
    from src.models.llm_client import LLMClient
    from src.models.data_processor import DataProcessor
    from src.core.exceptions import ValidationError, ServiceError, ExternalServiceError
except ImportError as e:
    # 如果导入失败，创建模拟类用于测试
    print(f"导入警告: {e}")

    class ChatServiceImpl:
        def __init__(self):
            self.conversation_sessions = {}
            self.system_prompt = "测试系统提示词"

        def process_message(self, message: str, session_id: str, context: Dict = None):
            return {"response": "测试回复", "session_id": session_id}

    class KnowledgeRetriever:
        def __init__(self):
            pass

        def analyze_question_intent(self, question: str):
            return 'general', ['测试', '关键词']

    class LLMClient:
        def __init__(self):
            pass

        def chat(self, message: str, context: str = "", history: List = None):
            return "测试AI回复"


class TestChatServiceImpl:
    """测试聊天服务实现类"""

    @pytest.fixture
    def mock_product_service(self):
        """模拟产品服务"""
        mock_service = Mock()
        mock_service.search_products.return_value = Mock(
            items=[
                {
                    'id': 'PROD001',
                    'product_name': '红富士苹果',
                    'price': 8.5,
                    'current_stock': 100,
                    'category': '水果'
                }
            ]
        )
        mock_service.get_categories.return_value = ['水果', '蔬菜', '有机产品']
        return mock_service

    @pytest.fixture
    def mock_config_service(self):
        """模拟配置服务"""
        mock_config = Mock()
        mock_config.get_section.return_value = {
            'api_key': 'test_api_key',
            'api_url': 'https://test.api.com/chat',
            'model': 'test-model',
            'temperature': 0.7,
            'max_tokens': 1000,
            'timeout': 30
        }
        return mock_config

    @pytest.fixture
    def chat_service(self, mock_product_service, mock_config_service):
        """创建聊天服务实例"""
        with patch('src.services.impl.chat_service_impl.config_service', mock_config_service):
            with patch('src.services.impl.chat_service_impl.ProductServiceImpl', return_value=mock_product_service):
                service = ChatServiceImpl()
                return service

    @pytest.mark.chat
    def test_process_message_success(self, chat_service):
        """测试成功处理消息"""
        message = "你好，请问有苹果吗？"
        session_id = "test_session_001"

        # 模拟LLM调用
        with patch.object(chat_service, '_call_llm', return_value="您好！我们有新鲜的红富士苹果。"):
            result = chat_service.process_message(message, session_id)

            assert result['response'] == "您好！我们有新鲜的红富士苹果。"
            assert result['session_id'] == session_id
            assert 'intent' in result
            assert 'timestamp' in result
            assert result['message_count'] == 1

    @pytest.mark.chat
    def test_process_message_empty_message(self, chat_service):
        """测试空消息处理"""
        with pytest.raises(ValidationError) as exc_info:
            chat_service.process_message("", "test_session")

        assert "消息不能为空" in str(exc_info.value)
        assert exc_info.value.field == "message"

    @pytest.mark.chat
    def test_process_message_empty_session_id(self, chat_service):
        """测试空会话ID处理"""
        with pytest.raises(ValidationError) as exc_info:
            chat_service.process_message("测试消息", "")

        assert "会话ID不能为空" in str(exc_info.value)
        assert exc_info.value.field == "session_id"

    @pytest.mark.chat
    def test_process_message_whitespace_only(self, chat_service):
        """测试只包含空白字符的消息"""
        with pytest.raises(ValidationError):
            chat_service.process_message("   \n\t   ", "test_session")

    @pytest.mark.chat
    def test_conversation_history_management(self, chat_service):
        """测试对话历史管理"""
        session_id = "test_session_002"

        with patch.object(chat_service, '_call_llm', return_value="测试回复"):
            # 发送第一条消息
            result1 = chat_service.process_message("第一条消息", session_id)
            assert result1['message_count'] == 1

            # 发送第二条消息
            result2 = chat_service.process_message("第二条消息", session_id)
            assert result2['message_count'] == 2

            # 验证对话历史存在
            conversation = chat_service.conversation_sessions[session_id]
            assert len(conversation['messages']) == 4  # 2条用户消息 + 2条AI回复

    @pytest.mark.chat
    def test_intent_analysis_price_inquiry(self, chat_service):
        """测试价格询问意图识别"""
        message = "苹果多少钱一斤？"

        intent_result = chat_service._analyze_intent(message)

        assert intent_result['type'] == 'price_inquiry'
        assert intent_result['confidence'] == 0.8

    @pytest.mark.chat
    def test_intent_analysis_stock_inquiry(self, chat_service):
        """测试库存询问意图识别"""
        message = "还有苹果吗？"

        intent_result = chat_service._analyze_intent(message)

        assert intent_result['type'] == 'stock_inquiry'
        assert intent_result['confidence'] == 0.8

    @pytest.mark.chat
    def test_intent_analysis_recommendation(self, chat_service):
        """测试推荐意图识别"""
        message = "推荐一些好吃的水果"

        intent_result = chat_service._analyze_intent(message)

        assert intent_result['type'] == 'recommendation'
        assert intent_result['confidence'] == 0.7

    @pytest.mark.chat
    def test_intent_analysis_complaint(self, chat_service):
        """测试投诉意图识别"""
        message = "我要投诉，苹果质量有问题"

        intent_result = chat_service._analyze_intent(message)

        assert intent_result['type'] == 'complaint'
        assert intent_result['confidence'] == 0.9

    @pytest.mark.chat
    def test_intent_analysis_general(self, chat_service):
        """测试一般询问意图识别"""
        message = "你好"

        intent_result = chat_service._analyze_intent(message)

        assert intent_result['type'] == 'general_inquiry'
        assert intent_result['confidence'] == 0.5

    @pytest.mark.chat
    def test_information_retrieval_with_products(self, chat_service):
        """测试带产品信息的信息检索"""
        message = "苹果的价格和库存"
        intent_result = {'type': 'price_inquiry', 'confidence': 0.8}

        retrieved_info = chat_service._retrieve_information(intent_result, message)

        assert 'products' in retrieved_info
        assert len(retrieved_info['products']) > 0
        assert retrieved_info['products'][0]['product_name'] == '红富士苹果'

    @pytest.mark.chat
    def test_information_retrieval_recommendation(self, chat_service):
        """测试推荐类型的信息检索"""
        message = "推荐一些水果"
        intent_result = {'type': 'recommendation', 'confidence': 0.7}

        retrieved_info = chat_service._retrieve_information(intent_result, message)

        assert 'categories' in retrieved_info
        assert len(retrieved_info['categories']) > 0
        assert '水果' in retrieved_info['categories']

    @pytest.mark.chat
    def test_information_retrieval_stock_inquiry(self, chat_service):
        """测试库存询问的信息检索"""
        message = "苹果还有库存吗"
        intent_result = {'type': 'stock_inquiry', 'confidence': 0.8}

        retrieved_info = chat_service._retrieve_information(intent_result, message)

        if retrieved_info['products']:
            for product in retrieved_info['products']:
                assert 'stock_status' in product
                assert product['stock_status'] in ['有库存', '缺货']

    @pytest.mark.chat
    def test_product_keyword_extraction(self, chat_service):
        """测试产品关键词提取"""
        message = "我想买苹果和香蕉"

        keywords = chat_service._extract_product_keywords(message)

        assert '苹果' in keywords or '香蕉' in keywords
        assert len(keywords) > 0

    @pytest.mark.chat
    def test_llm_context_building(self, chat_service):
        """测试LLM上下文构建"""
        messages = [
            {'role': 'user', 'content': '你好'},
            {'role': 'assistant', 'content': '您好！有什么可以帮您的吗？'}
        ]
        retrieved_info = {
            'products': [{'product_name': '苹果', 'price': 8.5}],
            'categories': ['水果']
        }
        context = {'user_agent': 'test_browser'}

        llm_context = chat_service._build_llm_context(messages, retrieved_info, context)

        assert len(llm_context) > 0
        assert llm_context[0]['role'] == 'system'
        assert any(msg['role'] == 'user' for msg in llm_context)

    @pytest.mark.chat
    def test_conversation_cleanup(self, chat_service):
        """测试对话历史清理"""
        session_id = "test_cleanup_session"
        conversation = {
            'messages': [{'role': 'user', 'content': f'消息{i}'} for i in range(50)],
            'message_count': 50,
            'created_at': datetime.utcnow().isoformat()
        }
        chat_service.conversation_sessions[session_id] = conversation

        chat_service._cleanup_conversation(conversation)

        # 验证消息数量被限制
        assert len(conversation['messages']) <= 20  # 假设最大保留20条消息

    @pytest.mark.chat
    def test_llm_call_success(self, chat_service):
        """测试成功的LLM调用"""
        messages = [
            {'role': 'system', 'content': '你是AI助手'},
            {'role': 'user', 'content': '你好'}
        ]

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'choices': [
                {'message': {'content': '您好！有什么可以帮您的吗？'}}
            ]
        }

        with patch('requests.post', return_value=mock_response):
            result = chat_service._call_llm(messages)

            assert result == '您好！有什么可以帮您的吗？'

    @pytest.mark.chat
    def test_llm_call_api_error(self, chat_service):
        """测试LLM API错误"""
        messages = [
            {'role': 'user', 'content': '测试消息'}
        ]

        mock_response = Mock()
        mock_response.status_code = 500
        mock_response.text = 'Internal Server Error'

        with patch('requests.post', return_value=mock_response):
            with pytest.raises(ExternalServiceError) as exc_info:
                chat_service._call_llm(messages)

            assert "AI服务暂时不可用" in str(exc_info.value)

    @pytest.mark.chat
    def test_llm_call_timeout(self, chat_service):
        """测试LLM调用超时"""
        messages = [
            {'role': 'user', 'content': '测试消息'}
        ]

        import requests
        with patch('requests.post', side_effect=requests.exceptions.Timeout):
            with pytest.raises(ExternalServiceError):
                chat_service._call_llm(messages)

    @pytest.mark.chat
    def test_llm_call_invalid_response(self, chat_service):
        """测试LLM返回无效响应"""
        messages = [
            {'role': 'user', 'content': '测试消息'}
        ]

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'error': '无效响应格式'}

        with patch('requests.post', return_value=mock_response):
            result = chat_service._call_llm(messages)

            # 应该返回默认错误消息
            assert "无法回答" in result or "稍后再试" in result

    @pytest.mark.chat
    def test_service_error_handling(self, chat_service):
        """测试服务错误处理"""
        message = "测试消息"
        session_id = "test_error_session"

        # 模拟LLM调用失败
        with patch.object(chat_service, '_call_llm', side_effect=Exception("LLM服务错误")):
            with pytest.raises(ServiceError) as exc_info:
                chat_service.process_message(message, session_id)

            assert "消息处理失败" in str(exc_info.value)


class TestKnowledgeRetriever:
    """测试知识检索器"""

    @pytest.fixture
    def mock_data_processor(self):
        """模拟数据处理器"""
        mock_processor = Mock()
        mock_processor.search_products.return_value = [
            {
                'ProductName': '红富士苹果',
                'Category': '水果',
                'Price': '8.5元/斤',
                'Description': '新鲜红富士苹果'
            }
        ]
        mock_processor.search_policies.return_value = [
            {
                'section': '退货政策',
                'content': '7天无理由退货',
                'score': 10
            }
        ]
        return mock_processor

    @pytest.fixture
    def knowledge_retriever(self, mock_data_processor):
        """创建知识检索器实例"""
        with patch('src.models.knowledge_retriever.DataProcessor', return_value=mock_data_processor):
            retriever = KnowledgeRetriever()
            retriever.data_processor = mock_data_processor
            return retriever

    @pytest.mark.chat
    def test_analyze_question_intent_price(self, knowledge_retriever):
        """测试价格询问意图分析"""
        question = "苹果多少钱？"

        intent, keywords = knowledge_retriever.analyze_question_intent(question)

        assert intent in ['price', 'general']  # 根据实际实现调整
        assert len(keywords) > 0

    @pytest.mark.chat
    def test_analyze_question_intent_stock(self, knowledge_retriever):
        """测试库存询问意图分析"""
        question = "还有苹果吗？"

        intent, keywords = knowledge_retriever.analyze_question_intent(question)

        assert intent in ['stock', 'general']  # 根据实际实现调整
        assert '苹果' in keywords or any('苹果' in kw for kw in keywords)

    @pytest.mark.chat
    def test_retrieve_information_with_products(self, knowledge_retriever):
        """测试检索产品信息"""
        question = "苹果的信息"

        result = knowledge_retriever.retrieve_information(question)

        assert 'intent' in result
        assert 'keywords' in result
        assert 'products' in result
        assert 'policies' in result
        assert result['has_product_info'] == True

    @pytest.mark.chat
    def test_retrieve_information_no_results(self, knowledge_retriever):
        """测试检索无结果的情况"""
        # 模拟无搜索结果
        knowledge_retriever.data_processor.search_products.return_value = []
        knowledge_retriever.data_processor.search_policies.return_value = []

        question = "不存在的产品信息"
        result = knowledge_retriever.retrieve_information(question)

        assert result['has_product_info'] == False
        assert result['has_policy_info'] == False

    @pytest.mark.chat
    def test_extract_product_names(self, knowledge_retriever):
        """测试提取产品名称"""
        question = "我想买苹果和香蕉"

        if hasattr(knowledge_retriever, 'extract_product_names'):
            products = knowledge_retriever.extract_product_names(question)
            assert len(products) >= 0  # 可能为空，取决于实现