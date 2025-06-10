"""
果蔬客服AI系统 - Flask Web应用
"""
from flask import Flask, render_template, request, jsonify, session
import uuid
import os
from datetime import datetime
from src.models.knowledge_retriever import KnowledgeRetriever
from src.models.admin_auth import AdminAuth
from src.models.inventory_manager import InventoryManager
from src.models.inventory_count_manager import InventoryCountManager
from src.models.inventory_comparison_manager import InventoryComparisonManager
from src.models.feedback_manager import FeedbackManager
from src.models.operation_logger import operation_logger, log_admin_operation
from src.models.data_exporter import data_exporter
from src.utils.i18n_config import i18n_config, _, SystemMessages, UITexts
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'fruit_vegetable_ai_service_2024')

# 初始化国际化配置
i18n_config.init_app(app)

# 全局变量
knowledge_retriever = None
conversation_sessions = {}
admin_auth = None
inventory_manager = None
inventory_count_manager = None
inventory_comparison_manager = None
feedback_manager = None


def initialize_system():
    """初始化系统"""
    global knowledge_retriever, admin_auth, inventory_manager, inventory_count_manager, inventory_comparison_manager, feedback_manager
    try:
        knowledge_retriever = KnowledgeRetriever()
        knowledge_retriever.initialize()

        # 初始化管理员模块
        admin_auth = AdminAuth()
        inventory_manager = InventoryManager()
        inventory_count_manager = InventoryCountManager()
        inventory_comparison_manager = InventoryComparisonManager()
        feedback_manager = FeedbackManager()

        try:
            print("✅ 果蔬客服AI系统初始化成功！")
        except UnicodeEncodeError:
            print("AI Customer Service System initialized successfully!")
        return True
    except Exception as e:
        try:
            print(f"❌ 系统初始化失败: {e}")
        except UnicodeEncodeError:
            print(f"System initialization failed: {e}")
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


# ==================== 国际化路由 ====================

@app.route('/api/language', methods=['GET'])
def get_language_info():
    """获取语言信息"""
    return jsonify({
        'success': True,
        'current_language': i18n_config.get_current_language(),
        'available_languages': i18n_config.get_available_languages()
    })


@app.route('/api/language/<language_code>', methods=['POST'])
def set_language(language_code):
    """设置语言"""
    try:
        success = i18n_config.set_language(language_code)
        if success:
            return jsonify({
                'success': True,
                'message': _('语言设置成功'),
                'current_language': i18n_config.get_current_language()
            })
        else:
            return jsonify({
                'success': False,
                'error': _('不支持的语言')
            })
    except Exception as e:
        print(f"设置语言错误: {e}")
        return jsonify({
            'success': False,
            'error': _('设置语言失败')
        })


# ==================== 管理员路由 ====================

@app.route('/admin/login')
def admin_login_page():
    """管理员登录页面"""
    return render_template('admin/login.html')


@app.route('/admin/dashboard')
def admin_dashboard():
    """管理员控制台"""
    return render_template('admin/dashboard.html')


@app.route('/api/admin/login', methods=['POST'])
def admin_login():
    """管理员登录API"""
    try:
        data = request.get_json()
        username = data.get('username', '').strip()
        password = data.get('password', '').strip()

        if not username or not password:
            return jsonify({
                'success': False,
                'error': '请输入用户名和密码'
            })

        if admin_auth:
            session_token = admin_auth.login(username, password)
            if session_token:
                session['admin_token'] = session_token
                return jsonify({
                    'success': True,
                    'message': '登录成功'
                })
            else:
                return jsonify({
                    'success': False,
                    'error': '用户名或密码错误'
                })
        else:
            return jsonify({
                'success': False,
                'error': '系统暂时不可用'
            })

    except Exception as e:
        print(f"管理员登录错误: {e}")
        return jsonify({
            'success': False,
            'error': '登录失败，请稍后再试'
        })


@app.route('/api/admin/logout', methods=['POST'])
def admin_logout():
    """管理员登出API"""
    try:
        admin_token = session.get('admin_token')
        if admin_token and admin_auth:
            admin_auth.logout(admin_token)

        session.pop('admin_token', None)

        return jsonify({
            'success': True,
            'message': '已退出登录'
        })

    except Exception as e:
        print(f"管理员登出错误: {e}")
        return jsonify({
            'success': False,
            'error': '登出失败'
        })


@app.route('/api/admin/status')
def admin_status():
    """检查管理员认证状态"""
    try:
        admin_token = session.get('admin_token')

        if admin_token and admin_auth and admin_auth.verify_session(admin_token):
            session_info = admin_auth.get_session_info(admin_token)
            return jsonify({
                'authenticated': True,
                'username': session_info.get('username', '管理员') if session_info else '管理员'
            })
        else:
            return jsonify({
                'authenticated': False
            })

    except Exception as e:
        print(f"检查管理员状态错误: {e}")
        return jsonify({
            'authenticated': False
        })


def require_admin_auth():
    """管理员认证装饰器"""
    admin_token = session.get('admin_token')
    if not admin_token or not admin_auth or not admin_auth.verify_session(admin_token):
        return False
    return True


def get_current_operator():
    """获取当前操作员信息"""
    admin_token = session.get('admin_token')
    if admin_token and admin_auth:
        session_info = admin_auth.get_session_info(admin_token)
        return session_info.get('username', '管理员') if session_info else '管理员'
    return '未知用户'


# ==================== 库存管理API ====================

@app.route('/api/admin/inventory')
def get_inventory():
    """获取库存列表"""
    try:
        if not require_admin_auth():
            return jsonify({'success': False, 'error': '未授权访问'})

        if inventory_manager:
            products = inventory_manager.get_all_products()
            return jsonify({
                'success': True,
                'data': products
            })
        else:
            return jsonify({
                'success': False,
                'error': '库存管理系统不可用'
            })

    except Exception as e:
        print(f"获取库存列表错误: {e}")
        return jsonify({
            'success': False,
            'error': '获取库存数据失败'
        })


@app.route('/api/admin/inventory/summary')
def get_inventory_summary():
    """获取库存汇总信息"""
    try:
        if not require_admin_auth():
            return jsonify({'success': False, 'error': '未授权访问'})

        if inventory_manager:
            summary = inventory_manager.get_inventory_summary()
            return jsonify({
                'success': True,
                'data': summary
            })
        else:
            return jsonify({
                'success': False,
                'error': '库存管理系统不可用'
            })

    except Exception as e:
        print(f"获取库存汇总错误: {e}")
        return jsonify({
            'success': False,
            'error': '获取库存汇总失败'
        })


@app.route('/api/admin/inventory/low-stock')
def get_low_stock():
    """获取低库存产品"""
    try:
        if not require_admin_auth():
            return jsonify({'success': False, 'error': '未授权访问'})

        if inventory_manager:
            low_stock_products = inventory_manager.get_low_stock_products()
            return jsonify({
                'success': True,
                'data': low_stock_products
            })
        else:
            return jsonify({
                'success': False,
                'error': '库存管理系统不可用'
            })

    except Exception as e:
        print(f"获取低库存产品错误: {e}")
        return jsonify({
            'success': False,
            'error': '获取低库存产品失败'
        })


@app.route('/api/admin/inventory/<product_id>', methods=['GET'])
def get_product_detail(product_id):
    """获取产品详情"""
    try:
        if not require_admin_auth():
            return jsonify({'success': False, 'error': '未授权访问'})

        if inventory_manager:
            product = inventory_manager.get_product_by_id(product_id)
            if product:
                return jsonify({
                    'success': True,
                    'data': product
                })
            else:
                return jsonify({
                    'success': False,
                    'error': '产品不存在'
                })
        else:
            return jsonify({
                'success': False,
                'error': '库存管理系统不可用'
            })

    except Exception as e:
        print(f"获取产品详情错误: {e}")
        return jsonify({
            'success': False,
            'error': '获取产品详情失败'
        })


@app.route('/api/admin/inventory/<product_id>/stock', methods=['POST'])
def update_stock(product_id):
    """更新库存数量"""
    try:
        if not require_admin_auth():
            return jsonify({'success': False, 'error': '未授权访问'})

        data = request.get_json()
        quantity_change = data.get('quantity_change', 0)
        note = data.get('note', '')

        # 获取操作员信息
        operator = get_current_operator()

        if inventory_manager:
            success = inventory_manager.update_stock(product_id, quantity_change, operator, note)

            # 记录操作日志
            log_admin_operation(
                operator=operator,
                operation_type="update_stock",
                target_type="inventory",
                target_id=product_id,
                details={
                    "quantity_change": quantity_change,
                    "note": note
                },
                result="success" if success else "failed"
            )

            if success:
                return jsonify({
                    'success': True,
                    'message': '库存更新成功'
                })
            else:
                return jsonify({
                    'success': False,
                    'error': '库存更新失败'
                })
        else:
            return jsonify({
                'success': False,
                'error': '库存管理系统不可用'
            })

    except Exception as e:
        print(f"更新库存错误: {e}")
        return jsonify({
            'success': False,
            'error': '更新库存失败'
        })


@app.route('/api/admin/inventory', methods=['POST'])
def add_product():
    """添加新产品"""
    try:
        if not require_admin_auth():
            return jsonify({'success': False, 'error': '未授权访问'})

        data = request.get_json()

        # 获取操作员信息
        admin_token = session.get('admin_token')
        session_info = admin_auth.get_session_info(admin_token)
        operator = session_info.get('username', '管理员') if session_info else '管理员'

        if inventory_manager:
            product_id = inventory_manager.add_product(data, operator)
            if product_id:
                return jsonify({
                    'success': True,
                    'message': '产品添加成功',
                    'product_id': product_id
                })
            else:
                return jsonify({
                    'success': False,
                    'error': '添加产品失败'
                })
        else:
            return jsonify({
                'success': False,
                'error': '库存管理系统不可用'
            })

    except Exception as e:
        print(f"添加产品错误: {e}")
        return jsonify({
            'success': False,
            'error': '添加产品失败'
        })


@app.route('/api/admin/inventory/<product_id>', methods=['PUT'])
def update_product(product_id):
    """更新产品信息"""
    try:
        if not require_admin_auth():
            return jsonify({'success': False, 'error': '未授权访问'})

        data = request.get_json()

        # 获取操作员信息
        admin_token = session.get('admin_token')
        session_info = admin_auth.get_session_info(admin_token)
        operator = session_info.get('username', '管理员') if session_info else '管理员'

        if inventory_manager:
            success = inventory_manager.update_product(product_id, data, operator)
            if success:
                return jsonify({
                    'success': True,
                    'message': '产品更新成功'
                })
            else:
                return jsonify({
                    'success': False,
                    'error': '产品更新失败'
                })
        else:
            return jsonify({
                'success': False,
                'error': '库存管理系统不可用'
            })

    except Exception as e:
        print(f"更新产品错误: {e}")
        return jsonify({
            'success': False,
            'error': '更新产品失败'
        })


@app.route('/api/admin/inventory/<product_id>', methods=['DELETE'])
def delete_product_api(product_id):
    """删除产品（软删除）"""
    try:
        if not require_admin_auth():
            return jsonify({'success': False, 'error': '未授权访问'})

        if inventory_manager:
            success = inventory_manager.delete_product(product_id)
            if success:
                return jsonify({
                    'success': True,
                    'message': '产品删除成功'
                })
            else:
                return jsonify({
                    'success': False,
                    'error': '产品删除失败'
                })
        else:
            return jsonify({
                'success': False,
                'error': '库存管理系统不可用'
            })

    except Exception as e:
        print(f"删除产品错误: {e}")
        return jsonify({
            'success': False,
            'error': '删除产品失败'
        })


# ==================== 库存盘点API ====================

@app.route('/api/admin/inventory/counts')
def get_count_tasks():
    """获取库存盘点任务列表"""
    try:
        if not require_admin_auth():
            return jsonify({'success': False, 'error': '未授权访问'})

        status_filter = request.args.get('status')  # in_progress, completed, cancelled

        if inventory_count_manager:
            tasks = inventory_count_manager.get_all_count_tasks(status_filter)
            return jsonify({
                'success': True,
                'data': tasks
            })
        else:
            return jsonify({
                'success': False,
                'error': '库存盘点系统不可用'
            })

    except Exception as e:
        print(f"获取盘点任务列表错误: {e}")
        return jsonify({
            'success': False,
            'error': '获取盘点任务失败'
        })


@app.route('/api/admin/inventory/counts', methods=['POST'])
def create_count_task():
    """创建新的库存盘点任务"""
    try:
        if not require_admin_auth():
            return jsonify({'success': False, 'error': '未授权访问'})

        data = request.get_json()
        note = data.get('note', '')

        # 获取操作员信息
        operator = get_current_operator()

        if inventory_count_manager:
            count_id = inventory_count_manager.create_count_task(operator, note)
            if count_id:
                return jsonify({
                    'success': True,
                    'message': '盘点任务创建成功',
                    'count_id': count_id
                })
            else:
                return jsonify({
                    'success': False,
                    'error': '创建盘点任务失败'
                })
        else:
            return jsonify({
                'success': False,
                'error': '库存盘点系统不可用'
            })

    except Exception as e:
        print(f"创建盘点任务错误: {e}")
        return jsonify({
            'success': False,
            'error': '创建盘点任务失败'
        })


@app.route('/api/admin/inventory/counts/<count_id>')
def get_count_task_detail(count_id):
    """获取盘点任务详情"""
    try:
        if not require_admin_auth():
            return jsonify({'success': False, 'error': '未授权访问'})

        if inventory_count_manager:
            task = inventory_count_manager.get_count_task(count_id)
            if task:
                return jsonify({
                    'success': True,
                    'data': task
                })
            else:
                return jsonify({
                    'success': False,
                    'error': '盘点任务不存在'
                })
        else:
            return jsonify({
                'success': False,
                'error': '库存盘点系统不可用'
            })

    except Exception as e:
        print(f"获取盘点任务详情错误: {e}")
        return jsonify({
            'success': False,
            'error': '获取盘点任务详情失败'
        })


@app.route('/api/admin/inventory/counts/<count_id>/items', methods=['POST'])
def add_count_item():
    """添加盘点项目（支持条形码和产品ID）"""
    try:
        if not require_admin_auth():
            return jsonify({'success': False, 'error': '未授权访问'})

        data = request.get_json()
        count_id = request.view_args['count_id']
        barcode = data.get('barcode', '').strip()
        product_id = data.get('product_id', '').strip()

        if not barcode and not product_id:
            return jsonify({
                'success': False,
                'error': '请提供条形码或产品ID'
            })

        if inventory_count_manager:
            # 优先使用条形码
            if barcode:
                success = inventory_count_manager.add_count_item_by_barcode(count_id, barcode)
            else:
                success = inventory_count_manager.add_count_item_by_product_id(count_id, product_id)

            if success:
                return jsonify({
                    'success': True,
                    'message': '产品已添加到盘点列表'
                })
            else:
                return jsonify({
                    'success': False,
                    'error': '添加盘点项目失败'
                })
        else:
            return jsonify({
                'success': False,
                'error': '库存盘点系统不可用'
            })

    except Exception as e:
        print(f"添加盘点项目错误: {e}")
        return jsonify({
            'success': False,
            'error': '添加盘点项目失败'
        })


@app.route('/api/admin/inventory/counts/<count_id>/items/<product_id>/quantity', methods=['POST'])
def record_actual_quantity():
    """记录产品的实际盘点数量"""
    try:
        if not require_admin_auth():
            return jsonify({'success': False, 'error': '未授权访问'})

        data = request.get_json()
        count_id = request.view_args['count_id']
        product_id = request.view_args['product_id']
        actual_quantity = data.get('actual_quantity')
        note = data.get('note', '')

        if actual_quantity is None or actual_quantity < 0:
            return jsonify({
                'success': False,
                'error': '请输入有效的实际数量'
            })

        if inventory_count_manager:
            success = inventory_count_manager.record_actual_quantity(
                count_id, product_id, actual_quantity, note
            )
            if success:
                return jsonify({
                    'success': True,
                    'message': '实际数量记录成功'
                })
            else:
                return jsonify({
                    'success': False,
                    'error': '记录实际数量失败'
                })
        else:
            return jsonify({
                'success': False,
                'error': '库存盘点系统不可用'
            })

    except Exception as e:
        print(f"记录实际数量错误: {e}")
        return jsonify({
            'success': False,
            'error': '记录实际数量失败'
        })


@app.route('/api/admin/inventory/counts/<count_id>/complete', methods=['POST'])
def complete_count_task():
    """完成盘点任务"""
    try:
        if not require_admin_auth():
            return jsonify({'success': False, 'error': '未授权访问'})

        count_id = request.view_args['count_id']

        if inventory_count_manager:
            success = inventory_count_manager.complete_count_task(count_id)
            if success:
                return jsonify({
                    'success': True,
                    'message': '盘点任务已完成'
                })
            else:
                return jsonify({
                    'success': False,
                    'error': '完成盘点任务失败'
                })
        else:
            return jsonify({
                'success': False,
                'error': '库存盘点系统不可用'
            })

    except Exception as e:
        print(f"完成盘点任务错误: {e}")
        return jsonify({
            'success': False,
            'error': '完成盘点任务失败'
        })


# ==================== 库存对比分析API ====================

@app.route('/api/admin/inventory/comparisons')
def get_comparisons():
    """获取库存对比分析列表"""
    try:
        if not require_admin_auth():
            return jsonify({'success': False, 'error': '未授权访问'})

        comparison_type = request.args.get('type')  # weekly, manual, auto

        if inventory_comparison_manager:
            comparisons = inventory_comparison_manager.get_all_comparisons(comparison_type)
            return jsonify({
                'success': True,
                'data': comparisons
            })
        else:
            return jsonify({
                'success': False,
                'error': '库存对比分析系统不可用'
            })

    except Exception as e:
        print(f"获取对比分析列表错误: {e}")
        return jsonify({
            'success': False,
            'error': '获取对比分析列表失败'
        })


@app.route('/api/admin/inventory/comparisons', methods=['POST'])
def create_comparison():
    """创建库存对比分析"""
    try:
        if not require_admin_auth():
            return jsonify({'success': False, 'error': '未授权访问'})

        data = request.get_json()
        current_count_id = data.get('current_count_id')
        previous_count_id = data.get('previous_count_id')
        comparison_type = data.get('comparison_type', 'manual')

        if not current_count_id or not previous_count_id:
            return jsonify({
                'success': False,
                'error': '请提供当前和之前的盘点任务ID'
            })

        # 获取操作员信息
        operator = get_current_operator()

        if inventory_comparison_manager:
            comparison_id = inventory_comparison_manager.create_comparison(
                current_count_id, previous_count_id, comparison_type, operator
            )
            if comparison_id:
                return jsonify({
                    'success': True,
                    'message': '对比分析创建成功',
                    'comparison_id': comparison_id
                })
            else:
                return jsonify({
                    'success': False,
                    'error': '创建对比分析失败'
                })
        else:
            return jsonify({
                'success': False,
                'error': '库存对比分析系统不可用'
            })

    except Exception as e:
        print(f"创建对比分析错误: {e}")
        return jsonify({
            'success': False,
            'error': '创建对比分析失败'
        })


@app.route('/api/admin/inventory/comparisons/weekly', methods=['POST'])
def create_weekly_comparison():
    """创建周对比分析"""
    try:
        if not require_admin_auth():
            return jsonify({'success': False, 'error': '未授权访问'})

        # 获取操作员信息
        operator = get_current_operator()

        if inventory_comparison_manager:
            comparison_id = inventory_comparison_manager.create_weekly_comparison(operator)
            if comparison_id:
                return jsonify({
                    'success': True,
                    'message': '周对比分析创建成功',
                    'comparison_id': comparison_id
                })
            else:
                return jsonify({
                    'success': False,
                    'error': '创建周对比分析失败，可能没有足够的盘点数据'
                })
        else:
            return jsonify({
                'success': False,
                'error': '库存对比分析系统不可用'
            })

    except Exception as e:
        print(f"创建周对比分析错误: {e}")
        return jsonify({
            'success': False,
            'error': '创建周对比分析失败'
        })


@app.route('/api/admin/inventory/comparisons/<comparison_id>')
def get_comparison_detail(comparison_id):
    """获取对比分析详情"""
    try:
        if not require_admin_auth():
            return jsonify({'success': False, 'error': '未授权访问'})

        if inventory_comparison_manager:
            comparison = inventory_comparison_manager.get_comparison(comparison_id)
            if comparison:
                return jsonify({
                    'success': True,
                    'data': comparison
                })
            else:
                return jsonify({
                    'success': False,
                    'error': '对比分析不存在'
                })
        else:
            return jsonify({
                'success': False,
                'error': '库存对比分析系统不可用'
            })

    except Exception as e:
        print(f"获取对比分析详情错误: {e}")
        return jsonify({
            'success': False,
            'error': '获取对比分析详情失败'
        })


@app.route('/api/admin/inventory/reports/weekly')
def get_weekly_report():
    """获取周报表"""
    try:
        if not require_admin_auth():
            return jsonify({'success': False, 'error': '未授权访问'})

        comparison_id = request.args.get('comparison_id')

        if inventory_comparison_manager:
            report = inventory_comparison_manager.generate_weekly_report(comparison_id)
            if 'error' not in report:
                return jsonify({
                    'success': True,
                    'data': report
                })
            else:
                return jsonify({
                    'success': False,
                    'error': report['error']
                })
        else:
            return jsonify({
                'success': False,
                'error': '库存对比分析系统不可用'
            })

    except Exception as e:
        print(f"获取周报表错误: {e}")
        return jsonify({
            'success': False,
            'error': '获取周报表失败'
        })


@app.route('/api/admin/inventory/products/<product_id>/trend')
def get_product_trend(product_id):
    """获取产品趋势分析"""
    try:
        if not require_admin_auth():
            return jsonify({'success': False, 'error': '未授权访问'})

        limit = int(request.args.get('limit', 5))

        if inventory_comparison_manager:
            trend_data = inventory_comparison_manager.get_product_trend_analysis(product_id, limit)
            if 'error' not in trend_data:
                return jsonify({
                    'success': True,
                    'data': trend_data
                })
            else:
                return jsonify({
                    'success': False,
                    'error': trend_data['error']
                })
        else:
            return jsonify({
                'success': False,
                'error': '库存对比分析系统不可用'
            })

    except Exception as e:
        print(f"获取产品趋势分析错误: {e}")
        return jsonify({
            'success': False,
            'error': '获取产品趋势分析失败'
        })


# ==================== 产品搜索API ====================

@app.route('/api/admin/inventory/search')
def search_products():
    """搜索产品"""
    try:
        if not require_admin_auth():
            return jsonify({'success': False, 'error': '未授权访问'})

        keyword = request.args.get('keyword', '').strip()
        if not keyword:
            return jsonify({
                'success': False,
                'error': '请提供搜索关键词'
            })

        if inventory_manager:
            products = inventory_manager.search_products(keyword)
            return jsonify({
                'success': True,
                'data': products
            })
        else:
            return jsonify({
                'success': False,
                'error': '库存管理系统不可用'
            })

    except Exception as e:
        print(f"搜索产品错误: {e}")
        return jsonify({
            'success': False,
            'error': '搜索产品失败'
        })


@app.route('/api/admin/inventory/comparisons/<comparison_id>/report')
def download_comparison_report(comparison_id):
    """下载对比分析报告"""
    try:
        if not require_admin_auth():
            return jsonify({'success': False, 'error': '未授权访问'})

        if inventory_comparison_manager:
            comparison = inventory_comparison_manager.get_comparison_by_id(comparison_id)
            if not comparison:
                return jsonify({
                    'success': False,
                    'error': '对比分析不存在'
                })

            # 生成报告内容
            report_content = inventory_comparison_manager.generate_comparison_report(comparison)

            response = app.response_class(
                report_content,
                mimetype='text/plain',
                headers={
                    "Content-disposition": f"attachment; filename=comparison_report_{comparison_id}.md"
                }
            )
            return response
        else:
            return jsonify({
                'success': False,
                'error': '库存对比分析系统不可用'
            })

    except Exception as e:
        print(f"下载对比分析报告错误: {e}")
        return jsonify({
            'success': False,
            'error': '下载报告失败'
        })


@app.route('/api/admin/inventory/comparisons/<comparison_id>/excel')
def download_comparison_excel(comparison_id):
    """下载对比分析Excel"""
    try:
        if not require_admin_auth():
            return jsonify({'success': False, 'error': '未授权访问'})

        if inventory_comparison_manager:
            comparison = inventory_comparison_manager.get_comparison_by_id(comparison_id)
            if not comparison:
                return jsonify({
                    'success': False,
                    'error': '对比分析不存在'
                })

            # 生成Excel内容（这里简化为CSV格式）
            excel_content = inventory_comparison_manager.generate_comparison_excel(comparison)

            response = app.response_class(
                excel_content,
                mimetype='text/csv',
                headers={
                    "Content-disposition": f"attachment; filename=comparison_changes_{comparison_id}.csv"
                }
            )
            return response
        else:
            return jsonify({
                'success': False,
                'error': '库存对比分析系统不可用'
            })

    except Exception as e:
        print(f"下载对比分析Excel错误: {e}")
        return jsonify({
            'success': False,
            'error': '下载Excel失败'
        })


# ==================== 存储区域管理API ====================

@app.route('/api/admin/inventory/storage-areas')
def get_storage_areas():
    """获取存储区域列表"""
    try:
        if not require_admin_auth():
            return jsonify({'success': False, 'error': '未授权访问'})

        include_inactive = request.args.get('include_inactive', 'false').lower() == 'true'

        if inventory_manager:
            areas = inventory_manager.get_all_storage_areas(include_inactive)
            return jsonify({
                'success': True,
                'data': areas
            })
        else:
            return jsonify({
                'success': False,
                'error': '库存管理系统不可用'
            })

    except Exception as e:
        print(f"获取存储区域列表错误: {e}")
        return jsonify({
            'success': False,
            'error': '获取存储区域列表失败'
        })


@app.route('/api/admin/inventory/storage-areas', methods=['POST'])
def add_storage_area():
    """添加新的存储区域"""
    try:
        if not require_admin_auth():
            return jsonify({'success': False, 'error': '未授权访问'})

        data = request.get_json()
        area_id = data.get('area_id', '').strip().upper()
        area_name = data.get('area_name', '').strip()
        description = data.get('description', '').strip()
        capacity = data.get('capacity', 1000)

        if not area_id or not area_name:
            return jsonify({
                'success': False,
                'error': '请提供区域ID和区域名称'
            })

        # 获取操作员信息
        operator = get_current_operator()

        if inventory_manager:
            success = inventory_manager.add_storage_area(
                area_id, area_name, description, capacity, operator
            )
            if success:
                return jsonify({
                    'success': True,
                    'message': '存储区域添加成功'
                })
            else:
                return jsonify({
                    'success': False,
                    'error': '添加存储区域失败'
                })
        else:
            return jsonify({
                'success': False,
                'error': '库存管理系统不可用'
            })

    except Exception as e:
        print(f"添加存储区域错误: {e}")
        return jsonify({
            'success': False,
            'error': '添加存储区域失败'
        })


# ==================== 反馈管理API ====================

@app.route('/api/admin/feedback')
def get_feedback():
    """获取反馈列表"""
    try:
        if not require_admin_auth():
            return jsonify({'success': False, 'error': '未授权访问'})

        status_filter = request.args.get('status')
        type_filter = request.args.get('type')

        if feedback_manager:
            feedback_list = feedback_manager.get_all_feedback(status_filter, type_filter)
            return jsonify({
                'success': True,
                'data': feedback_list
            })
        else:
            return jsonify({
                'success': False,
                'error': '反馈管理系统不可用'
            })

    except Exception as e:
        print(f"获取反馈列表错误: {e}")
        return jsonify({
            'success': False,
            'error': '获取反馈数据失败'
        })


@app.route('/api/admin/feedback/statistics')
def get_feedback_statistics():
    """获取反馈统计信息"""
    try:
        if not require_admin_auth():
            return jsonify({'success': False, 'error': '未授权访问'})

        if feedback_manager:
            statistics = feedback_manager.get_feedback_statistics()
            return jsonify({
                'success': True,
                'data': statistics
            })
        else:
            return jsonify({
                'success': False,
                'error': '反馈管理系统不可用'
            })

    except Exception as e:
        print(f"获取反馈统计错误: {e}")
        return jsonify({
            'success': False,
            'error': '获取反馈统计失败'
        })


@app.route('/api/admin/feedback/recent')
def get_recent_feedback():
    """获取最近反馈"""
    try:
        if not require_admin_auth():
            return jsonify({'success': False, 'error': '未授权访问'})

        days = request.args.get('days', 7, type=int)

        if feedback_manager:
            recent_feedback = feedback_manager.get_recent_feedback(days)
            return jsonify({
                'success': True,
                'data': recent_feedback
            })
        else:
            return jsonify({
                'success': False,
                'error': '反馈管理系统不可用'
            })

    except Exception as e:
        print(f"获取最近反馈错误: {e}")
        return jsonify({
            'success': False,
            'error': '获取最近反馈失败'
        })


@app.route('/api/admin/feedback/<feedback_id>')
def get_feedback_detail(feedback_id):
    """获取反馈详情"""
    try:
        if not require_admin_auth():
            return jsonify({'success': False, 'error': '未授权访问'})

        if feedback_manager:
            feedback = feedback_manager.get_feedback_by_id(feedback_id)
            if feedback:
                return jsonify({
                    'success': True,
                    'data': feedback
                })
            else:
                return jsonify({
                    'success': False,
                    'error': '反馈不存在'
                })
        else:
            return jsonify({
                'success': False,
                'error': '反馈管理系统不可用'
            })

    except Exception as e:
        print(f"获取反馈详情错误: {e}")
        return jsonify({
            'success': False,
            'error': '获取反馈详情失败'
        })


@app.route('/api/admin/feedback', methods=['POST'])
def add_feedback():
    """添加新反馈"""
    try:
        if not require_admin_auth():
            return jsonify({'success': False, 'error': '未授权访问'})

        data = request.get_json()

        # 验证必需字段
        required_fields = ['product_name', 'customer_wechat_name', 'customer_group_number',
                          'payment_status', 'feedback_type', 'feedback_content']

        for field in required_fields:
            if not data.get(field):
                return jsonify({
                    'success': False,
                    'error': f'缺少必需字段: {field}'
                })

        if feedback_manager:
            feedback_id = feedback_manager.add_feedback(data)
            if feedback_id:
                return jsonify({
                    'success': True,
                    'message': '反馈添加成功',
                    'feedback_id': feedback_id
                })
            else:
                return jsonify({
                    'success': False,
                    'error': '添加反馈失败'
                })
        else:
            return jsonify({
                'success': False,
                'error': '反馈管理系统不可用'
            })

    except Exception as e:
        print(f"添加反馈错误: {e}")
        return jsonify({
            'success': False,
            'error': '添加反馈失败'
        })


@app.route('/api/admin/feedback/<feedback_id>/status', methods=['POST'])
def update_feedback_status(feedback_id):
    """更新反馈处理状态"""
    try:
        if not require_admin_auth():
            return jsonify({'success': False, 'error': '未授权访问'})

        data = request.get_json()
        status = data.get('status', '')
        notes = data.get('notes', '')

        # 获取操作员信息
        admin_token = session.get('admin_token')
        session_info = admin_auth.get_session_info(admin_token)
        processor = session_info.get('username', '管理员') if session_info else '管理员'

        if feedback_manager:
            success = feedback_manager.update_feedback_status(feedback_id, status, processor, notes)
            if success:
                return jsonify({
                    'success': True,
                    'message': '反馈状态更新成功'
                })
            else:
                return jsonify({
                    'success': False,
                    'error': '反馈状态更新失败'
                })
        else:
            return jsonify({
                'success': False,
                'error': '反馈管理系统不可用'
            })

    except Exception as e:
        print(f"更新反馈状态错误: {e}")
        return jsonify({
            'success': False,
            'error': '更新反馈状态失败'
        })


@app.route('/api/admin/feedback/<feedback_id>', methods=['DELETE'])
def delete_feedback_api(feedback_id):
    """删除反馈记录"""
    try:
        if not require_admin_auth():
            return jsonify({'success': False, 'error': '未授权访问'})

        if feedback_manager:
            success = feedback_manager.delete_feedback(feedback_id)
            if success:
                return jsonify({
                    'success': True,
                    'message': '反馈删除成功'
                })
            else:
                return jsonify({
                    'success': False,
                    'error': '反馈删除失败'
                })
        else:
            return jsonify({
                'success': False,
                'error': '反馈管理系统不可用'
            })

    except Exception as e:
        print(f"删除反馈错误: {e}")
        return jsonify({
            'success': False,
            'error': '删除反馈失败'
        })


# ==================== 其他管理API ====================

@app.route('/api/admin/change-password', methods=['POST'])
def change_admin_password():
    """修改管理员密码"""
    try:
        if not require_admin_auth():
            return jsonify({'success': False, 'error': '未授权访问'})

        data = request.get_json()
        old_password = data.get('oldPassword', '')
        new_password = data.get('newPassword', '')

        if not old_password or not new_password:
            return jsonify({
                'success': False,
                'error': '请输入旧密码和新密码'
            })

        # 获取当前用户信息
        admin_token = session.get('admin_token')
        session_info = admin_auth.get_session_info(admin_token)
        username = session_info.get('username') if session_info else None

        if not username:
            return jsonify({
                'success': False,
                'error': '获取用户信息失败'
            })

        if admin_auth:
            success = admin_auth.change_password(username, old_password, new_password)
            if success:
                return jsonify({
                    'success': True,
                    'message': '密码修改成功'
                })
            else:
                return jsonify({
                    'success': False,
                    'error': '旧密码错误或修改失败'
                })
        else:
            return jsonify({
                'success': False,
                'error': '认证系统不可用'
            })

    except Exception as e:
        print(f"修改密码错误: {e}")
        return jsonify({
            'success': False,
            'error': '修改密码失败'
        })


# ==================== 数据导出和日志API ====================

@app.route('/api/admin/export/inventory')
def export_inventory():
    """导出库存数据"""
    try:
        if not require_admin_auth():
            return jsonify({'success': False, 'error': '未授权访问'})

        format_type = request.args.get('format', 'csv')
        operator = get_current_operator()

        if inventory_manager:
            products = inventory_manager.get_all_products()

            if format_type == 'csv':
                csv_data = data_exporter.export_inventory_to_csv(products)

                # 记录操作日志
                log_admin_operation(
                    operator=operator,
                    operation_type="export",
                    target_type="inventory",
                    target_id="all",
                    details={"format": "csv", "count": len(products)}
                )

                response = app.response_class(
                    csv_data,
                    mimetype='text/csv',
                    headers={"Content-disposition": f"attachment; filename=inventory_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"}
                )
                return response

            elif format_type == 'json':
                json_data = data_exporter.export_to_json(products)

                # 记录操作日志
                log_admin_operation(
                    operator=operator,
                    operation_type="export",
                    target_type="inventory",
                    target_id="all",
                    details={"format": "json", "count": len(products)}
                )

                response = app.response_class(
                    json_data,
                    mimetype='application/json',
                    headers={"Content-disposition": f"attachment; filename=inventory_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"}
                )
                return response

            else:
                return jsonify({
                    'success': False,
                    'error': '不支持的导出格式'
                })
        else:
            return jsonify({
                'success': False,
                'error': '库存管理系统不可用'
            })

    except Exception as e:
        print(f"导出库存数据错误: {e}")
        return jsonify({
            'success': False,
            'error': '导出数据失败'
        })


@app.route('/api/admin/export/feedback')
def export_feedback():
    """导出反馈数据"""
    try:
        if not require_admin_auth():
            return jsonify({'success': False, 'error': '未授权访问'})

        format_type = request.args.get('format', 'csv')
        operator = get_current_operator()

        if feedback_manager:
            feedback_list = feedback_manager.get_all_feedback()

            if format_type == 'csv':
                csv_data = data_exporter.export_feedback_to_csv(feedback_list)

                # 记录操作日志
                log_admin_operation(
                    operator=operator,
                    operation_type="export",
                    target_type="feedback",
                    target_id="all",
                    details={"format": "csv", "count": len(feedback_list)}
                )

                response = app.response_class(
                    csv_data,
                    mimetype='text/csv',
                    headers={"Content-disposition": f"attachment; filename=feedback_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"}
                )
                return response

            elif format_type == 'json':
                json_data = data_exporter.export_to_json(feedback_list)

                # 记录操作日志
                log_admin_operation(
                    operator=operator,
                    operation_type="export",
                    target_type="feedback",
                    target_id="all",
                    details={"format": "json", "count": len(feedback_list)}
                )

                response = app.response_class(
                    json_data,
                    mimetype='application/json',
                    headers={"Content-disposition": f"attachment; filename=feedback_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"}
                )
                return response

            else:
                return jsonify({
                    'success': False,
                    'error': '不支持的导出格式'
                })
        else:
            return jsonify({
                'success': False,
                'error': '反馈管理系统不可用'
            })

    except Exception as e:
        print(f"导出反馈数据错误: {e}")
        return jsonify({
            'success': False,
            'error': '导出数据失败'
        })


@app.route('/api/admin/logs')
def get_operation_logs():
    """获取操作日志"""
    try:
        if not require_admin_auth():
            return jsonify({'success': False, 'error': '未授权访问'})

        limit = request.args.get('limit', 100, type=int)
        operator = request.args.get('operator')
        operation_type = request.args.get('operation_type')
        target_type = request.args.get('target_type')

        logs = operation_logger.get_logs(limit, operator, operation_type, target_type)

        return jsonify({
            'success': True,
            'data': logs
        })

    except Exception as e:
        print(f"获取操作日志错误: {e}")
        return jsonify({
            'success': False,
            'error': '获取操作日志失败'
        })


@app.route('/api/admin/logs/statistics')
def get_log_statistics():
    """获取操作统计"""
    try:
        if not require_admin_auth():
            return jsonify({'success': False, 'error': '未授权访问'})

        days = request.args.get('days', 7, type=int)
        stats = operation_logger.get_operation_statistics(days)

        return jsonify({
            'success': True,
            'data': stats
        })

    except Exception as e:
        print(f"获取操作统计错误: {e}")
        return jsonify({
            'success': False,
            'error': '获取操作统计失败'
        })


@app.route('/api/admin/export/logs')
def export_logs():
    """导出操作日志"""
    try:
        if not require_admin_auth():
            return jsonify({'success': False, 'error': '未授权访问'})

        format_type = request.args.get('format', 'csv')
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        operator = get_current_operator()

        logs = operation_logger.export_logs(start_date, end_date)

        if format_type == 'csv':
            csv_data = data_exporter.export_logs_to_csv(logs)

            response = app.response_class(
                csv_data,
                mimetype='text/csv',
                headers={"Content-disposition": f"attachment; filename=operation_logs_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"}
            )
            return response

        elif format_type == 'json':
            json_data = data_exporter.export_to_json(logs)

            response = app.response_class(
                json_data,
                mimetype='application/json',
                headers={"Content-disposition": f"attachment; filename=operation_logs_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"}
            )
            return response

        else:
            return jsonify({
                'success': False,
                'error': '不支持的导出格式'
            })

    except Exception as e:
        print(f"导出操作日志错误: {e}")
        return jsonify({
            'success': False,
            'error': '导出日志失败'
        })


@app.route('/api/admin/reports/inventory')
def generate_inventory_report():
    """生成库存报告"""
    try:
        if not require_admin_auth():
            return jsonify({'success': False, 'error': '未授权访问'})

        if inventory_manager:
            products = inventory_manager.get_all_products()
            summary = inventory_manager.get_inventory_summary()

            report = data_exporter.generate_inventory_report(products, summary)

            response = app.response_class(
                report,
                mimetype='text/plain',
                headers={"Content-disposition": f"attachment; filename=inventory_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"}
            )
            return response
        else:
            return jsonify({
                'success': False,
                'error': '库存管理系统不可用'
            })

    except Exception as e:
        print(f"生成库存报告错误: {e}")
        return jsonify({
            'success': False,
            'error': '生成报告失败'
        })


@app.route('/api/admin/reports/feedback')
def generate_feedback_report():
    """生成反馈报告"""
    try:
        if not require_admin_auth():
            return jsonify({'success': False, 'error': '未授权访问'})

        if feedback_manager:
            feedback_list = feedback_manager.get_all_feedback()
            stats = feedback_manager.get_feedback_statistics()

            report = data_exporter.generate_feedback_report(feedback_list, stats)

            response = app.response_class(
                report,
                mimetype='text/plain',
                headers={"Content-disposition": f"attachment; filename=feedback_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"}
            )
            return response
        else:
            return jsonify({
                'success': False,
                'error': '反馈管理系统不可用'
            })

    except Exception as e:
        print(f"生成反馈报告错误: {e}")
        return jsonify({
            'success': False,
            'error': '生成报告失败'
        })


@app.errorhandler(404)
def not_found(error):
    return render_template('404.html'), 404


@app.errorhandler(500)
def internal_error(error):
    return render_template('500.html'), 500


if __name__ == '__main__':
    try:
        print("启动果蔬客服AI系统...")
    except UnicodeEncodeError:
        print("Starting AI Customer Service System...")

    # 获取端口配置（Render会提供PORT环境变量）
    port = int(os.environ.get('PORT', 5000))
    debug_mode = os.environ.get('FLASK_ENV') != 'production'

    # 初始化系统
    if initialize_system():
        try:
            print(f"启动Web服务器... 端口: {port}")
        except UnicodeEncodeError:
            print(f"Starting Web Server... Port: {port}")
        app.run(debug=debug_mode, host='0.0.0.0', port=port)
    else:
        try:
            print("系统初始化失败，无法启动服务器")
        except UnicodeEncodeError:
            print("System initialization failed, cannot start server")
