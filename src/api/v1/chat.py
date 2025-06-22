# -*- coding: utf-8 -*-
"""
聊天API控制器 v1
"""
import logging
from flask import Blueprint, request, g
from ...core.service_registry import get_chat_service
from ...core.response import ResponseBuilder, ResponseHelper
from ...core.exceptions import ValidationError
from ..version_control import api_version
from ...utils.validators import validate_json, ChatMessageRequest

logger = logging.getLogger(__name__)

chat_bp = Blueprint('chat', __name__)


@chat_bp.route('', methods=['POST'])
@api_version()
@validate_json(ChatMessageRequest)
def send_message():
    """发送聊天消息"""
    try:
        data = request.get_json()
        
        # 从请求中获取会话ID
        session_id = data.get('session_id') or request.headers.get('X-Session-ID')
        if not session_id:
            # 生成新的会话ID
            import uuid
            session_id = str(uuid.uuid4())
        
        # 获取用户消息
        message = data['message']
        
        # 获取上下文信息
        context = data.get('context', {})
        
        # 添加请求元信息到上下文
        context.update({
            'user_agent': request.headers.get('User-Agent'),
            'client_ip': request.remote_addr,
            'timestamp': request.json.get('timestamp') if request.json else None
        })
        
        # 调用聊天服务
        chat_service = get_chat_service()
        result = chat_service.process_message(message, session_id, context)
        
        response = ResponseBuilder.success(
            data=result,
            message="消息处理成功"
        )
        
        # 添加会话元信息
        response.set_meta('session_id', session_id)
        response.set_meta('processing_time', None)  # 可以添加处理时间统计
        
        return response.to_json_response()
        
    except Exception as e:
        logger.error(f"处理聊天消息失败: {e}")
        return ResponseHelper.handle_exception(e)


@chat_bp.route('/history/<session_id>', methods=['GET'])
@api_version()
def get_conversation_history(session_id: str):
    """获取对话历史"""
    try:
        # 限制参数
        limit = int(request.args.get('limit', 20))
        limit = min(max(1, limit), 100)  # 限制在1-100之间
        
        chat_service = get_chat_service()
        history = chat_service.get_conversation_history(session_id, limit)
        
        response = ResponseBuilder.success(
            data=history,
            message=f"获取到 {len(history)} 条历史消息"
        )
        
        response.set_meta('session_id', session_id)
        response.set_meta('limit', limit)
        
        return response.to_json_response()
        
    except ValueError as e:
        logger.warning(f"获取对话历史参数错误: {e}")
        return ResponseHelper.handle_exception(ValidationError(f"参数格式错误: {e}"))
    except Exception as e:
        logger.error(f"获取对话历史失败 {session_id}: {e}")
        return ResponseHelper.handle_exception(e)


@chat_bp.route('/history/<session_id>', methods=['DELETE'])
@api_version()
def clear_conversation_history(session_id: str):
    """清除对话历史"""
    try:
        chat_service = get_chat_service()
        success = chat_service.clear_conversation(session_id)
        
        if success:
            response = ResponseBuilder.success(message="对话历史已清除")
        else:
            response = ResponseBuilder.success(message="会话不存在或已清空")
        
        response.set_meta('session_id', session_id)
        
        return response.to_json_response()
        
    except Exception as e:
        logger.error(f"清除对话历史失败 {session_id}: {e}")
        return ResponseHelper.handle_exception(e)


@chat_bp.route('/statistics', methods=['GET'])
@api_version()
def get_chat_statistics():
    """获取聊天统计信息"""
    try:
        chat_service = get_chat_service()
        stats = chat_service.get_conversation_stats()
        
        response = ResponseBuilder.success(
            data=stats,
            message="聊天统计信息"
        )
        
        return response.to_json_response()
        
    except Exception as e:
        logger.error(f"获取聊天统计失败: {e}")
        return ResponseHelper.handle_exception(e)


@chat_bp.route('/sessions', methods=['GET'])
@api_version()
def get_active_sessions():
    """获取活跃会话列表"""
    try:
        # 这里可以扩展为从聊天服务获取活跃会话
        # 暂时返回统计信息
        chat_service = get_chat_service()
        stats = chat_service.get_conversation_stats()
        
        # 构建会话列表（示例数据）
        sessions = [
            {
                'session_id': 'session_001',
                'last_activity': '2025-06-22T10:30:00Z',
                'message_count': 15,
                'status': 'active'
            },
            {
                'session_id': 'session_002', 
                'last_activity': '2025-06-22T09:45:00Z',
                'message_count': 8,
                'status': 'idle'
            }
        ]
        
        response = ResponseBuilder.success(
            data={
                'sessions': sessions,
                'total_sessions': stats.get('total_sessions', 0),
                'active_sessions': stats.get('active_sessions', 0)
            },
            message=f"共有 {len(sessions)} 个会话"
        )
        
        return response.to_json_response()
        
    except Exception as e:
        logger.error(f"获取活跃会话失败: {e}")
        return ResponseHelper.handle_exception(e)


@chat_bp.route('/feedback', methods=['POST'])
@api_version()
def submit_feedback():
    """提交聊天反馈"""
    try:
        data = request.get_json()
        
        if not data:
            raise ValidationError("请求数据不能为空")
        
        # 验证必要字段
        required_fields = ['session_id', 'message_id', 'rating']
        for field in required_fields:
            if field not in data:
                raise ValidationError(f"缺少必要字段: {field}", field=field)
        
        session_id = data['session_id']
        message_id = data['message_id']
        rating = data['rating']
        comment = data.get('comment', '')
        
        # 验证评分
        if not isinstance(rating, int) or rating < 1 or rating > 5:
            raise ValidationError("评分必须是1-5之间的整数", field="rating")
        
        # 这里可以保存反馈到数据库
        feedback_data = {
            'session_id': session_id,
            'message_id': message_id,
            'rating': rating,
            'comment': comment,
            'submitted_at': request.json.get('timestamp') if request.json else None,
            'user_agent': request.headers.get('User-Agent'),
            'client_ip': request.remote_addr
        }
        
        # TODO: 保存到数据库
        logger.info(f"收到聊天反馈: session={session_id}, rating={rating}")
        
        response = ResponseBuilder.success(
            data={'feedback_id': f"fb_{session_id}_{message_id}"},
            message="反馈提交成功"
        )
        
        return response.to_json_response()
        
    except Exception as e:
        logger.error(f"提交聊天反馈失败: {e}")
        return ResponseHelper.handle_exception(e)


@chat_bp.route('/suggestions', methods=['GET'])
@api_version()
def get_chat_suggestions():
    """获取聊天建议"""
    try:
        # 查询参数
        query = request.args.get('q', '').strip()
        category = request.args.get('category', '').strip()
        
        # 预定义的建议（生产环境可以基于历史对话和产品数据生成）
        suggestions = []
        
        if not query:
            # 默认建议
            suggestions = [
                {"text": "有什么新鲜的水果吗？", "category": "product_inquiry"},
                {"text": "今天有什么特价商品？", "category": "promotion"},
                {"text": "苹果多少钱一斤？", "category": "price_inquiry"},
                {"text": "有机蔬菜怎么样？", "category": "product_recommendation"},
                {"text": "配送需要多长时间？", "category": "service_inquiry"}
            ]
        else:
            # 基于查询的建议（简单匹配）
            if '水果' in query or '果' in query:
                suggestions = [
                    {"text": "苹果新鲜吗？", "category": "product_inquiry"},
                    {"text": "有什么当季水果推荐？", "category": "product_recommendation"},
                    {"text": "水果的保存方法", "category": "service_inquiry"}
                ]
            elif '蔬菜' in query or '菜' in query:
                suggestions = [
                    {"text": "今天有什么新鲜蔬菜？", "category": "product_inquiry"},
                    {"text": "有机蔬菜和普通蔬菜的区别", "category": "product_recommendation"},
                    {"text": "蔬菜怎么搭配营养？", "category": "service_inquiry"}
                ]
            elif '价格' in query or '钱' in query:
                suggestions = [
                    {"text": "今日特价商品", "category": "promotion"},
                    {"text": "会员有优惠吗？", "category": "promotion"},
                    {"text": "大批量购买有折扣吗？", "category": "price_inquiry"}
                ]
        
        # 按分类过滤
        if category:
            suggestions = [s for s in suggestions if s['category'] == category]
        
        response = ResponseBuilder.success(
            data=suggestions,
            message=f"找到 {len(suggestions)} 个建议"
        )
        
        response.set_meta('query', query)
        response.set_meta('category', category)
        
        return response.to_json_response()
        
    except Exception as e:
        logger.error(f"获取聊天建议失败: {e}")
        return ResponseHelper.handle_exception(e)