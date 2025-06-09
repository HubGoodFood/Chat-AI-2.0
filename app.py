"""
果蔬客服AI系统 - Flask Web应用
"""
from flask import Flask, render_template, request, jsonify, session
import uuid
from datetime import datetime
from knowledge_retriever import KnowledgeRetriever
import os


app = Flask(__name__)
app.secret_key = 'fruit_vegetable_ai_service_2024'

# 全局变量
knowledge_retriever = None
conversation_sessions = {}


def initialize_system():
    """初始化系统"""
    global knowledge_retriever
    try:
        knowledge_retriever = KnowledgeRetriever()
        knowledge_retriever.initialize()
        print("✅ 果蔬客服AI系统初始化成功！")
        return True
    except Exception as e:
        print(f"❌ 系统初始化失败: {e}")
        return False


@app.route('/')
def index():
    """主页"""
    # 生成新的会话ID
    if 'session_id' not in session:
        session['session_id'] = str(uuid.uuid4())
        conversation_sessions[session['session_id']] = []
    
    return render_template('index.html')


@app.route('/api/chat', methods=['POST'])
def chat():
    """聊天API"""
    try:
        data = request.get_json()
        user_message = data.get('message', '').strip()
        
        if not user_message:
            return jsonify({
                'success': False,
                'error': '请输入您的问题'
            })
        
        # 获取会话ID
        session_id = session.get('session_id')
        if not session_id:
            session_id = str(uuid.uuid4())
            session['session_id'] = session_id
            conversation_sessions[session_id] = []
        
        # 获取对话历史
        conversation_history = conversation_sessions.get(session_id, [])
        
        # 生成AI回复
        if knowledge_retriever:
            ai_response = knowledge_retriever.answer_question(user_message, conversation_history)
        else:
            ai_response = "抱歉，系统暂时不可用，请稍后再试。"
        
        # 更新对话历史
        conversation_history.append({"role": "user", "content": user_message})
        conversation_history.append({"role": "assistant", "content": ai_response})
        
        # 保持最近10轮对话
        if len(conversation_history) > 20:
            conversation_history = conversation_history[-20:]
        
        conversation_sessions[session_id] = conversation_history
        
        return jsonify({
            'success': True,
            'response': ai_response,
            'timestamp': datetime.now().strftime('%H:%M')
        })
        
    except Exception as e:
        print(f"聊天API错误: {e}")
        return jsonify({
            'success': False,
            'error': '处理您的请求时出现错误，请稍后再试'
        })


@app.route('/api/categories')
def get_categories():
    """获取产品分类"""
    try:
        if knowledge_retriever:
            categories = knowledge_retriever.get_product_categories()
            return jsonify({
                'success': True,
                'categories': categories
            })
        else:
            return jsonify({
                'success': False,
                'error': '系统暂时不可用'
            })
    except Exception as e:
        print(f"获取分类错误: {e}")
        return jsonify({
            'success': False,
            'error': '获取分类信息失败'
        })


@app.route('/api/products/<category>')
def get_products_by_category(category):
    """根据分类获取产品"""
    try:
        if knowledge_retriever:
            products = knowledge_retriever.get_products_by_category(category)
            return jsonify({
                'success': True,
                'products': products
            })
        else:
            return jsonify({
                'success': False,
                'error': '系统暂时不可用'
            })
    except Exception as e:
        print(f"获取产品错误: {e}")
        return jsonify({
            'success': False,
            'error': '获取产品信息失败'
        })


@app.route('/api/quick-answers')
def get_quick_answers():
    """获取常见问题快速回答"""
    try:
        if knowledge_retriever:
            quick_answers = knowledge_retriever.get_quick_answers()
            return jsonify({
                'success': True,
                'quick_answers': quick_answers
            })
        else:
            return jsonify({
                'success': False,
                'error': '系统暂时不可用'
            })
    except Exception as e:
        print(f"获取快速回答错误: {e}")
        return jsonify({
            'success': False,
            'error': '获取快速回答失败'
        })


@app.route('/api/clear-session', methods=['POST'])
def clear_session():
    """清除会话"""
    try:
        session_id = session.get('session_id')
        if session_id and session_id in conversation_sessions:
            conversation_sessions[session_id] = []
        
        return jsonify({
            'success': True,
            'message': '会话已清除'
        })
    except Exception as e:
        print(f"清除会话错误: {e}")
        return jsonify({
            'success': False,
            'error': '清除会话失败'
        })


@app.route('/health')
def health_check():
    """健康检查"""
    return jsonify({
        'status': 'healthy',
        'system_ready': knowledge_retriever is not None,
        'timestamp': datetime.now().isoformat()
    })


@app.errorhandler(404)
def not_found(error):
    return render_template('404.html'), 404


@app.errorhandler(500)
def internal_error(error):
    return render_template('500.html'), 500


if __name__ == '__main__':
    print("🚀 启动果蔬客服AI系统...")
    
    # 初始化系统
    if initialize_system():
        print("🌐 启动Web服务器...")
        app.run(debug=True, host='0.0.0.0', port=5000)
    else:
        print("❌ 系统初始化失败，无法启动服务器")
