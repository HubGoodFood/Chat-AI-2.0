# -*- coding: utf-8 -*-
"""
聊天服务实现
"""
import logging
import json
import requests
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from ...core.interfaces import IChatService
from ...core.exceptions import ValidationError, ServiceError, ExternalServiceError
from ...core.config import config_service
from ...services.cache_service import cached
from ...services.impl.product_service_impl import ProductServiceImpl

logger = logging.getLogger(__name__)


class ChatServiceImpl(IChatService):
    """聊天服务实现"""
    
    def __init__(self):
        self.llm_config = config_service.get_section('llm')
        self.business_config = config_service.get_section('business')
        self.product_service = ProductServiceImpl()
        
        # 对话历史存储（生产环境应使用Redis）
        self.conversation_sessions = {}
        
        # 预定义提示词
        self.system_prompt = """你是一个专业的果蔬客服AI助手，名叫小果。你的主要职责是：

1. 回答客户关于果蔬产品的询问
2. 提供产品信息、价格、库存状态
3. 协助客户选择合适的产品
4. 处理客户的问题和投诉

回答要求：
- 语言亲切友好，专业准确
- 如果不确定信息，诚实告知并建议联系人工客服
- 优先推荐当前有库存的产品
- 价格信息要准确，如有变动及时说明
- 保持简洁明了，避免冗长回复

当前你可以查询的产品信息包括：产品名称、价格、库存、分类、规格等。"""
    
    def process_message(self, message: str, session_id: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """处理用户消息"""
        try:
            # 数据验证
            if not message or not message.strip():
                raise ValidationError("消息不能为空", field="message")
            
            if not session_id or not session_id.strip():
                raise ValidationError("会话ID不能为空", field="session_id")
            
            message = message.strip()
            session_id = session_id.strip()
            
            # 获取或创建对话历史
            conversation = self._get_or_create_conversation(session_id)
            
            # 添加用户消息到历史
            user_message = {
                'role': 'user',
                'content': message,
                'timestamp': datetime.utcnow().isoformat()
            }
            conversation['messages'].append(user_message)
            
            # 意图识别和信息检索
            intent_result = self._analyze_intent(message)
            retrieved_info = self._retrieve_information(intent_result, message)
            
            # 构建LLM上下文
            llm_context = self._build_llm_context(conversation['messages'], retrieved_info, context)
            
            # 调用LLM获取回复
            ai_response = self._call_llm(llm_context)
            
            # 添加AI回复到历史
            assistant_message = {
                'role': 'assistant',
                'content': ai_response,
                'timestamp': datetime.utcnow().isoformat(),
                'intent': intent_result,
                'retrieved_info': retrieved_info
            }
            conversation['messages'].append(assistant_message)
            
            # 清理过长的对话历史
            self._cleanup_conversation(conversation)
            
            # 更新对话统计
            conversation['message_count'] += 1
            conversation['last_activity'] = datetime.utcnow().isoformat()
            
            logger.info(f"处理消息成功 session: {session_id}, intent: {intent_result.get('type', 'unknown')}")
            
            return {
                'response': ai_response,
                'session_id': session_id,
                'intent': intent_result,
                'timestamp': datetime.utcnow().isoformat(),
                'message_count': conversation['message_count']
            }
            
        except (ValidationError, ServiceError):
            raise
        except Exception as e:
            logger.error(f"处理消息失败 session: {session_id}: {e}")
            raise ServiceError("消息处理失败，请稍后重试")
    
    def get_conversation_history(self, session_id: str, limit: int = 20) -> List[Dict[str, Any]]:
        """获取对话历史"""
        try:
            if not session_id or not session_id.strip():
                raise ValidationError("会话ID不能为空", field="session_id")
            
            session_id = session_id.strip()
            conversation = self.conversation_sessions.get(session_id)
            
            if not conversation:
                return []
            
            # 返回最近的消息，限制数量
            messages = conversation['messages'][-limit:] if limit > 0 else conversation['messages']
            
            return [
                {
                    'role': msg['role'],
                    'content': msg['content'],
                    'timestamp': msg['timestamp']
                }
                for msg in messages
            ]
            
        except ValidationError:
            raise
        except Exception as e:
            logger.error(f"获取对话历史失败 session: {session_id}: {e}")
            raise ServiceError("获取对话历史失败")
    
    def clear_conversation(self, session_id: str) -> bool:
        """清除对话历史"""
        try:
            if not session_id or not session_id.strip():
                raise ValidationError("会话ID不能为空", field="session_id")
            
            session_id = session_id.strip()
            
            if session_id in self.conversation_sessions:
                del self.conversation_sessions[session_id]
                logger.info(f"清除对话历史成功 session: {session_id}")
                return True
            
            return False
            
        except ValidationError:
            raise
        except Exception as e:
            logger.error(f"清除对话历史失败 session: {session_id}: {e}")
            raise ServiceError("清除对话历史失败")
    
    @cached(prefix="chat:stats", timeout=300)
    def get_conversation_stats(self) -> Dict[str, Any]:
        """获取对话统计"""
        try:
            total_sessions = len(self.conversation_sessions)
            total_messages = sum(conv['message_count'] for conv in self.conversation_sessions.values())
            
            # 活跃会话（最近1小时有活动）
            one_hour_ago = datetime.utcnow() - timedelta(hours=1)
            active_sessions = 0
            
            for conversation in self.conversation_sessions.values():
                last_activity = datetime.fromisoformat(conversation['last_activity'])
                if last_activity > one_hour_ago:
                    active_sessions += 1
            
            return {
                'total_sessions': total_sessions,
                'active_sessions': active_sessions,
                'total_messages': total_messages,
                'average_messages_per_session': total_messages / total_sessions if total_sessions > 0 else 0
            }
            
        except Exception as e:
            logger.error(f"获取对话统计失败: {e}")
            raise ServiceError("获取对话统计失败")
    
    def _get_or_create_conversation(self, session_id: str) -> Dict[str, Any]:
        """获取或创建对话会话"""
        if session_id not in self.conversation_sessions:
            self.conversation_sessions[session_id] = {
                'session_id': session_id,
                'messages': [],
                'message_count': 0,
                'created_at': datetime.utcnow().isoformat(),
                'last_activity': datetime.utcnow().isoformat()
            }
        
        return self.conversation_sessions[session_id]
    
    def _analyze_intent(self, message: str) -> Dict[str, Any]:
        """分析用户意图"""
        message_lower = message.lower()
        
        # 简单的关键词匹配（生产环境可使用更复杂的意图识别）
        if any(keyword in message_lower for keyword in ['价格', '多少钱', '费用', '成本']):
            return {'type': 'price_inquiry', 'confidence': 0.8}
        
        elif any(keyword in message_lower for keyword in ['库存', '有没有', '还有吗', '现货']):
            return {'type': 'stock_inquiry', 'confidence': 0.8}
        
        elif any(keyword in message_lower for keyword in ['推荐', '建议', '什么好', '选择']):
            return {'type': 'recommendation', 'confidence': 0.7}
        
        elif any(keyword in message_lower for keyword in ['投诉', '问题', '不满', '退货']):
            return {'type': 'complaint', 'confidence': 0.9}
        
        elif any(keyword in message_lower for keyword in ['营养', '功效', '作用', '好处']):
            return {'type': 'nutrition_inquiry', 'confidence': 0.7}
        
        else:
            return {'type': 'general_inquiry', 'confidence': 0.5}
    
    def _retrieve_information(self, intent_result: Dict[str, Any], message: str) -> Dict[str, Any]:
        """检索相关信息"""
        retrieved_info = {
            'products': [],
            'categories': [],
            'general_info': None
        }
        
        try:
            intent_type = intent_result.get('type')
            
            # 从消息中提取可能的产品关键词
            product_keywords = self._extract_product_keywords(message)
            
            if product_keywords:
                # 搜索相关产品
                search_result = self.product_service.search_products(
                    query=' '.join(product_keywords),
                    per_page=5
                )
                retrieved_info['products'] = search_result.items
            
            # 根据意图类型获取额外信息
            if intent_type in ['recommendation', 'general_inquiry']:
                # 获取热门分类
                categories = self.product_service.get_categories()
                retrieved_info['categories'] = categories[:5]  # 前5个分类
            
            elif intent_type == 'stock_inquiry':
                # 如果有产品关键词，获取库存信息
                if retrieved_info['products']:
                    for product in retrieved_info['products']:
                        product['stock_status'] = '有库存' if product['current_stock'] > 0 else '缺货'
            
        except Exception as e:
            logger.error(f"检索信息失败: {e}")
            # 检索失败不影响对话，返回空信息
        
        return retrieved_info
    
    def _extract_product_keywords(self, message: str) -> List[str]:
        """从消息中提取产品关键词"""
        # 简单的关键词提取（生产环境可使用NLP工具）
        import jieba
        
        # 中文分词
        words = list(jieba.cut(message))
        
        # 过滤掉无意义的词
        stop_words = {'的', '了', '是', '有', '没有', '吗', '呢', '啊', '哦', '嗯', '怎么', '什么', '哪个', '这个', '那个'}
        keywords = [word for word in words if len(word) > 1 and word not in stop_words]
        
        return keywords[:3]  # 返回前3个关键词
    
    def _build_llm_context(self, messages: List[Dict[str, Any]], retrieved_info: Dict[str, Any], context: Dict[str, Any] = None) -> List[Dict[str, str]]:
        """构建LLM上下文"""
        llm_messages = [{'role': 'system', 'content': self.system_prompt}]
        
        # 添加检索到的信息
        if retrieved_info.get('products'):
            info_content = "当前可用的产品信息：\n"
            for product in retrieved_info['products']:
                info_content += f"- {product['product_name']}: ¥{product['price']}, 库存{product['current_stock']}{product['unit']}\n"
            
            llm_messages.append({'role': 'system', 'content': info_content})
        
        # 添加对话历史（最近几轮）
        recent_messages = messages[-6:] if len(messages) > 6 else messages  # 最多保留3轮对话
        for msg in recent_messages:
            if msg['role'] in ['user', 'assistant']:
                llm_messages.append({'role': msg['role'], 'content': msg['content']})
        
        return llm_messages
    
    def _call_llm(self, messages: List[Dict[str, str]]) -> str:
        """调用LLM服务"""
        try:
            headers = {
                'Authorization': f"Bearer {self.llm_config['api_key']}",
                'Content-Type': 'application/json'
            }
            
            payload = {
                'model': self.llm_config['model'],
                'messages': messages,
                'temperature': self.llm_config['temperature'],
                'max_tokens': self.llm_config['max_tokens']
            }
            
            response = requests.post(
                self.llm_config['api_url'],
                headers=headers,
                json=payload,
                timeout=self.llm_config['timeout']
            )
            
            if response.status_code != 200:
                logger.error(f"LLM API错误 {response.status_code}: {response.text}")
                raise ExternalServiceError(
                    "AI服务暂时不可用，请稍后重试",
                    service_name="llm",
                    status_code=response.status_code
                )
            
            result = response.json()
            
            if 'choices' not in result or not result['choices']:
                logger.error(f"LLM响应格式错误: {result}")
                raise ExternalServiceError("AI服务响应格式错误", service_name="llm")
            
            return result['choices'][0]['message']['content'].strip()
            
        except requests.RequestException as e:
            logger.error(f"LLM API请求失败: {e}")
            raise ExternalServiceError("AI服务连接失败，请稍后重试", service_name="llm")
        except Exception as e:
            logger.error(f"调用LLM失败: {e}")
            raise ExternalServiceError("AI服务异常，请稍后重试", service_name="llm")
    
    def _cleanup_conversation(self, conversation: Dict[str, Any]):
        """清理过长的对话历史"""
        max_messages = self.business_config.get('max_conversation_history', 20)
        
        if len(conversation['messages']) > max_messages:
            # 保留系统消息和最近的消息
            system_messages = [msg for msg in conversation['messages'] if msg['role'] == 'system']
            recent_messages = conversation['messages'][-(max_messages-len(system_messages)):]
            
            conversation['messages'] = system_messages + recent_messages
    
    def cleanup_expired_sessions(self, hours: int = 24):
        """清理过期会话"""
        try:
            cutoff_time = datetime.utcnow() - timedelta(hours=hours)
            expired_sessions = []
            
            for session_id, conversation in self.conversation_sessions.items():
                last_activity = datetime.fromisoformat(conversation['last_activity'])
                if last_activity < cutoff_time:
                    expired_sessions.append(session_id)
            
            for session_id in expired_sessions:
                del self.conversation_sessions[session_id]
            
            logger.info(f"清理过期会话完成: {len(expired_sessions)}个会话")
            return len(expired_sessions)
            
        except Exception as e:
            logger.error(f"清理过期会话失败: {e}")
            return 0