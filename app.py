# -*- coding: utf-8 -*-
"""
果蔬客服AI系统 - Flask Web应用
"""
from flask import Flask, render_template, request, jsonify, session, send_from_directory, redirect, url_for, send_file
import uuid
import os
import time
from datetime import datetime
from src.models.knowledge_retriever import KnowledgeRetriever
from src.models.admin_auth import AdminAuth
from src.models.inventory_manager import InventoryManager
from src.models.inventory_count_manager import InventoryCountManager
from src.models.inventory_comparison_manager import InventoryComparisonManager
from src.models.feedback_manager import FeedbackManager
from src.models.policy_manager import PolicyManager
from src.models.operation_logger import operation_logger, log_admin_operation
from src.models.data_exporter import data_exporter
from src.utils.i18n_simple import i18n_simple, _
from src.utils.simple_flask_fix import apply_simple_fixes
from src.utils.logger_config import get_logger, safe_print
from src.utils.barcode_batch_generator import BarcodeBatchGenerator
from src.utils.security_config import security_config
from src.utils.decorators import validate_json, require_admin_auth, handle_service_errors, check_login_attempts, log_admin_operation
from src.utils.validators import ChatMessageRequest, AdminLoginRequest, ProductCreateRequest, ProductUpdateRequest, StockUpdateRequest
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 初始化日志记录器
logger = get_logger('app')

app = Flask(__name__)
# 记录应用启动时间（用于性能监控）
app.start_time = time.time()

# 使用增强的安全配置
from src.utils.security_config_enhanced import security_config

# 应用Flask配置修复
apply_simple_fixes(app)

# 初始化增强的安全配置
security_config.init_app(app)

# 初始化简洁的国际化配置
i18n_simple.init_app(app)

# 全局变量
knowledge_retriever = None
conversation_sessions = {}
admin_auth = None
inventory_manager = None
inventory_count_manager = None
inventory_comparison_manager = None
feedback_manager = None
policy_manager = None


def initialize_system():
    """初始化系统"""
    global knowledge_retriever, admin_auth, inventory_manager, inventory_count_manager, inventory_comparison_manager, feedback_manager
    try:
        # 初始化存储系统（可选：如果需要使用NAS存储）
        # 取消注释以下代码来启用NAS存储
        # from src.storage.storage_manager import initialize_storage, StorageType
        # nas_path = "Z:\\ChatAI_System\\data"  # Windows示例
        # nas_path = "/mnt/nas/ChatAI_Data/ChatAI_System/data"  # Linux示例
        # storage_success = initialize_storage(StorageType.NAS, nas_path=nas_path)
        # if storage_success:
        #     logger.info("NAS存储系统初始化成功")
        # else:
        #     logger.warning("NAS存储初始化失败，使用本地存储")

        # 🚀 使用数据库化知识检索器（性能优化）
        knowledge_retriever = KnowledgeRetriever(use_database_processor=True)
        knowledge_retriever.initialize()

        # 初始化管理员模块
        admin_auth = AdminAuth()
        inventory_manager = InventoryManager()
        inventory_count_manager = InventoryCountManager()
        inventory_comparison_manager = InventoryComparisonManager()
        feedback_manager = FeedbackManager()
        policy_manager = PolicyManager()

        logger.info("果蔬客服AI系统初始化成功！")
        return True
    except Exception as e:
        logger.error(f"系统初始化失败: {e}")
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
@validate_json(ChatMessageRequest)
@handle_service_errors
def chat(validated_data: ChatMessageRequest):
    """聊天API（已增强安全验证）"""
    try:
        user_message = validated_data.message

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
        try:
            print(f"聊天API错误: {e}")
        except UnicodeEncodeError:
            print("Chat API error occurred (Unicode display issue)")
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


@app.route('/api/performance/stats')
def performance_stats():
    """
    性能统计接口 - 查看系统性能指标

    这个接口提供了系统的性能统计信息，包括：
    - 缓存命中率：显示智能缓存的效果
    - 响应时间统计：监控系统响应速度
    - 系统资源使用：内存、CPU等指标

    适合编程初学者学习：
    - 了解如何监控系统性能
    - 理解缓存对性能的影响
    - 学习性能优化的量化方法
    """
    try:
        # 🚀 安全导入模块，避免导入错误导致404
        try:
            from src.services.intelligent_cache_manager import intelligent_cache_manager
            cache_stats = intelligent_cache_manager.get_cache_stats()
        except Exception as e:
            logger.warning(f"智能缓存管理器导入失败: {e}")
            cache_stats = {'total_requests': 0, 'cache_hits': 0, 'cache_misses': 0, 'hit_rate': 0, 'exact_matches': 0, 'similarity_matches': 0, 'similarity_threshold': 80}

        try:
            from src.services.performance_collector import performance_collector
            performance_summary = performance_collector.get_performance_summary()
            performance_recommendations = performance_collector.get_performance_recommendations()
        except Exception as e:
            logger.warning(f"性能收集器导入失败: {e}")
            performance_summary = {'response_time_stats': {}, 'user_experience': {}, 'error_stats': {}}
            performance_recommendations = ["性能收集器暂不可用"]

        # 获取系统资源使用情况
        try:
            import psutil
            import os
            process = psutil.Process(os.getpid())
            memory_info = process.memory_info()
            cpu_percent = psutil.cpu_percent(interval=1)
        except Exception as e:
            logger.warning(f"系统资源监控失败: {e}")
            memory_info = type('obj', (object,), {'rss': 0})()
            cpu_percent = 0

        # 🚀 构建增强的性能统计响应
        stats = {
            'cache_performance': {
                'total_requests': cache_stats.get('total_requests', 0),
                'cache_hits': cache_stats.get('cache_hits', 0),
                'cache_misses': cache_stats.get('cache_misses', 0),
                'hit_rate_percentage': cache_stats.get('hit_rate', 0),
                'exact_matches': cache_stats.get('exact_matches', 0),
                'similarity_matches': cache_stats.get('similarity_matches', 0),
                'similarity_threshold': cache_stats.get('similarity_threshold', 80)
            },
            'response_time_stats': performance_summary.get('response_time_stats', {}),
            'user_experience': performance_summary.get('user_experience', {}),
            'system_resources': {
                'memory_usage_mb': round(memory_info.rss / 1024 / 1024, 2),
                'cpu_percent': cpu_percent,
                'process_id': os.getpid() if 'os' in locals() else 0
            },
            'system_status': {
                'knowledge_retriever_ready': knowledge_retriever is not None,
                'cache_service_enabled': True,
                'uptime_seconds': time.time() - app.start_time if hasattr(app, 'start_time') else 0
            },
            'error_stats': performance_summary.get('error_stats', {}),
            'performance_recommendations': performance_recommendations,
            'timestamp': datetime.now().isoformat()
        }

        return jsonify({
            'success': True,
            'data': stats,
            'message': f"缓存命中率: {cache_stats.get('hit_rate', 0):.1f}%"
        })

    except Exception as e:
        logger.error(f"获取性能统计失败: {e}")
        return jsonify({
            'success': False,
            'error': '获取性能统计失败',
            'timestamp': datetime.now().isoformat()
        })


@app.route('/api/performance/query-stats')
def query_performance_stats():
    """
    🚀 查询性能统计接口（数据库查询优化）

    这个接口提供了数据库查询的详细性能统计，包括：
    - 查询时间分析：各类查询的响应时间统计
    - 慢查询检测：识别性能瓶颈
    - 查询趋势：历史性能变化趋势
    - 优化建议：基于数据的性能改进建议

    适合编程初学者学习：
    - 了解数据库查询性能监控
    - 学习如何识别和优化慢查询
    - 理解查询优化对系统性能的影响
    """
    try:
        # 🚀 安全导入查询性能分析器
        try:
            from src.services.query_performance_analyzer import query_performance_analyzer

            # 获取查询性能摘要
            performance_summary = query_performance_analyzer.get_performance_summary()

            # 获取慢查询列表
            slow_queries = query_performance_analyzer.get_slow_queries(10)

            # 获取查询趋势
            query_trends = query_performance_analyzer.get_query_trends(24)

            # 获取优化建议
            recommendations = query_performance_analyzer.get_optimization_recommendations()

        except Exception as import_error:
            logger.warning(f"查询性能分析器导入失败: {import_error}")
            # 提供默认数据
            performance_summary = {
                'total_queries': 0,
                'total_slow_queries': 0,
                'slow_query_rate': 0,
                'query_types': {}
            }
            slow_queries = []
            query_trends = []
            recommendations = ["查询性能分析器暂不可用，请检查系统配置"]

        stats = {
            'query_performance': performance_summary,
            'slow_queries': slow_queries,
            'query_trends': query_trends,
            'optimization_recommendations': recommendations,
            'timestamp': datetime.now().isoformat()
        }

        return jsonify({
            'success': True,
            'data': stats,
            'message': f"查询性能监控 - 慢查询率: {performance_summary.get('slow_query_rate', 0):.1f}%"
        })

    except Exception as e:
        logger.error(f"获取查询性能统计失败: {e}")
        return jsonify({
            'success': False,
            'error': '获取查询性能统计失败',
            'timestamp': datetime.now().isoformat()
        })





# ==================== 国际化路由 ====================

@app.route('/api/language', methods=['GET'])
def get_language_info():
    """获取语言信息"""
    print(f"[DEBUG] get_language_info被调用")
    print(f"[DEBUG] i18n_simple.languages.keys(): {list(i18n_simple.languages.keys())}")
    print(f"[DEBUG] 'en_US' in i18n_simple.languages: {'en_US' in i18n_simple.languages}")

    return jsonify({
        'success': True,
        'current_language': i18n_simple.get_current_language(),
        'available_languages': i18n_simple.get_available_languages(),
        'debug_info': {
            'all_language_keys': list(i18n_simple.languages.keys()),
            'en_US_exists': 'en_US' in i18n_simple.languages
        }
    })


@app.route('/api/language/<language_code>', methods=['POST'])
def set_language(language_code):
    """设置语言"""
    try:
        print(f"[DEBUG] 设置语言请求: {language_code}")
        print(f"[DEBUG] 当前session: {dict(session)}")

        success = i18n_simple.set_language(language_code)
        print(f"[DEBUG] 设置语言结果: {success}")
        print(f"[DEBUG] 设置后session: {dict(session)}")

        if success:
            return jsonify({
                'success': True,
                'message': 'Language set successfully',
                'current_language': i18n_simple.get_current_language()
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Unsupported language'
            })
    except Exception as e:
        print(f"设置语言错误: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to set language'
        })

@app.route('/test-translation')
def test_translation():
    """测试翻译功能"""
    import sys
    print(f"[DEBUG] 测试翻译功能", flush=True)
    print(f"[DEBUG] 当前语言: {i18n_simple.get_locale()}", flush=True)
    print(f"[DEBUG] session内容: {dict(session)}", flush=True)
    print(f"[DEBUG] 翻译测试 '管理后台': {i18n_simple.translate('管理后台')}", flush=True)
    sys.stdout.flush()

    return jsonify({
        'current_language': i18n_simple.get_locale(),
        'session': dict(session),
        'translation_test': i18n_simple.translate('管理后台'),
        'available_languages': i18n_simple.get_available_languages()
    })


@app.route('/test-translation-page')
def test_translation_page():
    """测试翻译页面"""
    print(f"[DEBUG] 渲染翻译测试页面")
    print(f"[DEBUG] 当前语言: {i18n_simple.get_locale()}")
    return render_template('test_translation.html')


@app.route('/final-translation-test')
def final_translation_test():
    """最终翻译测试页面"""
    print(f"[DEBUG] 渲染最终翻译测试页面")
    print(f"[DEBUG] 当前语言: {i18n_simple.get_locale()}")
    return render_template('translation_test_final.html')


@app.route('/test_cleanup.html')
def test_cleanup():
    """客服页面清理测试页面"""
    from flask import send_from_directory
    return send_from_directory('.', 'test_cleanup.html')


@app.route('/clean_test.html')
def clean_test():
    """干净测试页面"""
    from flask import send_from_directory
    return send_from_directory('.', 'clean_test.html')


@app.route('/test_customer_service.html')
def test_customer_service():
    """客服功能测试页面"""
    from flask import send_from_directory
    return send_from_directory('.', 'test_customer_service.html')


# ==================== 管理员路由 ====================

@app.route('/admin')
def admin_redirect():
    """管理员页面重定向"""
    from flask import redirect, url_for
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/login')
def admin_login_page():
    """管理员登录页面"""
    return render_template('admin/login.html')


@app.route('/test/language')
def test_language_debug():
    """语言调试测试页面"""
    print(f"[DEBUG] 访问语言测试页面")
    return "Language test page - working!"


@app.route('/test/lang')
def test_lang_simple():
    """简单语言测试"""
    print(f"[DEBUG] 访问简单语言测试页面")
    try:
        return render_template('test_language.html')
    except Exception as e:
        print(f"[ERROR] 渲染测试页面失败: {e}")
        return f"Error rendering test page: {e}"


@app.route('/test/auto')
def test_language_auto():
    """自动语言测试页面"""
    print(f"[DEBUG] 访问自动语言测试页面")
    try:
        with open('static/test_language_auto.html', 'r', encoding='utf-8') as f:
            content = f.read()
        return content
    except Exception as e:
        print(f"[ERROR] 读取自动测试页面失败: {e}")
        return f"Error loading auto test page: {e}"


@app.route('/debug/i18n')
def debug_i18n():
    """调试i18n配置"""
    return jsonify({
        'available_languages': list(i18n_simple.languages.keys()),
        'en_US_exists': 'en_US' in i18n_simple.languages,
        'current_language': i18n_simple.get_locale(),
        'session_content': dict(session),
        'languages_detail': i18n_simple.languages
    })


@app.route('/admin/dashboard')
def admin_dashboard():
    """管理员控制台"""
    print(f"[DEBUG] 渲染管理后台页面")
    print(f"[DEBUG] 当前语言: {i18n_simple.get_locale()}")
    print(f"[DEBUG] 翻译测试: {i18n_simple.translate('管理后台')}")
    return render_template('admin/dashboard.html')


@app.route('/admin/inventory/products/add')
def admin_inventory_add_product():
    """产品入库页面"""
    return render_template('admin/dashboard.html', default_section='inventory-add-product')


@app.route('/admin/inventory/counts')
def admin_inventory_counts():
    """库存盘点页面"""
    return render_template('admin/dashboard.html', default_section='inventory-counts')


@app.route('/admin/pickup-locations-test')
def admin_pickup_locations_test():
    """测试路由"""
    return "测试路由工作正常"

@app.route('/admin/pickup-locations')
def admin_pickup_locations():
    """取货点管理页面"""
    try:
        if not require_admin_auth():
            return redirect(url_for('admin_login_page'))
        return render_template('admin/dashboard.html', default_section='pickup-locations')
    except Exception as e:
        print(f"取货点页面错误: {e}")
        return f"错误: {e}", 500


@app.route('/admin/inventory/analysis')
def admin_inventory_analysis():
    """数据对比分析页面"""
    return render_template('admin/dashboard.html', default_section='inventory-analysis')


@app.route('/admin/policies')
def admin_policies():
    """政策管理页面"""
    try:
        if not require_admin_auth():
            return redirect(url_for('admin_login_page'))
        return render_template('admin/dashboard.html', default_section='policies')
    except Exception as e:
        logger.error(f"渲染政策管理页面失败: {e}")
        return f"页面加载失败: {e}", 500


@app.route('/admin/performance')
def admin_performance_monitor():
    """
    性能监控页面

    这个页面提供了AI客服系统的实时性能监控，包括：
    - 缓存命中率统计
    - 响应时间分析
    - 系统资源使用情况
    - 实时性能日志

    适合编程初学者学习：
    - 了解如何监控系统性能
    - 理解缓存对性能的影响
    - 学习性能优化的量化方法
    """
    try:
        # 🚀 临时禁用管理员权限检查，便于测试
        # TODO: 在生产环境中启用权限检查
        # if not require_admin_auth():
        #     return redirect(url_for('admin_login_page'))

        return render_template('admin/performance_monitor.html')

    except Exception as e:
        logger.error(f"性能监控页面错误: {e}")
        import traceback
        traceback.print_exc()
        return f"性能监控页面错误: {e}", 500


@app.route('/api/admin/login', methods=['POST'])
def admin_login():
    """管理员登录API"""
    try:
        data = request.get_json()
        username = data.get('username', '').strip()
        password = data.get('password', '').strip()

        print(f"[DEBUG] 登录尝试: 用户名={username}, 密码长度={len(password)}")
        print(f"[DEBUG] admin_auth对象: {admin_auth}")

        if not username or not password:
            print(f"[DEBUG] 用户名或密码为空")
            return jsonify({
                'success': False,
                'error': _('请输入用户名和密码')
            })

        if admin_auth:
            print(f"[DEBUG] 调用admin_auth.login方法")
            session_token = admin_auth.login(username, password)
            print(f"[DEBUG] 登录结果: session_token={session_token}")
            if session_token:
                session['admin_token'] = session_token
                print(f"[DEBUG] 登录成功，设置session")
                return jsonify({
                    'success': True,
                    'message': _('登录成功')
                })
            else:
                print(f"[DEBUG] 登录失败，session_token为None")
                return jsonify({
                    'success': False,
                    'error': _('用户名或密码错误')
                })
        else:
            print(f"[DEBUG] admin_auth对象为None")
            return jsonify({
                'success': False,
                'error': _('系统暂时不可用')
            })

    except Exception as e:
        print(f"管理员登录错误: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': _('登录失败，请稍后再试')
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


# ==================== 条形码相关API ====================

@app.route('/api/admin/inventory/<product_id>/barcode', methods=['POST'])
def generate_product_barcode(product_id):
    """为产品生成条形码"""
    try:
        if not require_admin_auth():
            return jsonify({'success': False, 'error': '未授权访问'})

        # 获取操作员信息
        admin_token = session.get('admin_token')
        session_info = admin_auth.get_session_info(admin_token)
        operator = session_info.get('username', '管理员') if session_info else '管理员'

        if inventory_manager:
            success = inventory_manager.regenerate_barcode(product_id, operator)
            if success:
                return jsonify({
                    'success': True,
                    'message': '条形码生成成功'
                })
            else:
                return jsonify({
                    'success': False,
                    'error': '产品不存在或生成失败'
                })
        else:
            return jsonify({
                'success': False,
                'error': '库存管理系统不可用'
            })

    except Exception as e:
        logger.error(f"生成条形码失败: {e}")
        return jsonify({
            'success': False,
            'error': '生成条形码失败'
        })


@app.route('/api/admin/inventory/<product_id>/barcode/regenerate', methods=['POST'])
def regenerate_product_barcode(product_id):
    """重新生成产品条形码"""
    try:
        if not require_admin_auth():
            return jsonify({'success': False, 'error': '未授权访问'})

        # 获取操作员信息
        admin_token = session.get('admin_token')
        session_info = admin_auth.get_session_info(admin_token)
        operator = session_info.get('username', '管理员') if session_info else '管理员'

        if inventory_manager:
            success = inventory_manager.regenerate_barcode(product_id, operator)
            if success:
                return jsonify({
                    'success': True,
                    'message': '条形码重新生成成功'
                })
            else:
                return jsonify({
                    'success': False,
                    'error': '产品不存在或重新生成失败'
                })
        else:
            return jsonify({
                'success': False,
                'error': '库存管理系统不可用'
            })

    except Exception as e:
        logger.error(f"重新生成条形码失败: {e}")
        return jsonify({
            'success': False,
            'error': '重新生成条形码失败'
        })


@app.route('/api/admin/inventory/<product_id>/barcode/download')
def download_product_barcode(product_id):
    """下载产品条形码图片"""
    try:
        if not require_admin_auth():
            return jsonify({'success': False, 'error': '未授权访问'})

        if inventory_manager:
            product = inventory_manager.get_product_by_id(product_id)
            if product and product.get('barcode_image'):
                barcode_path = product['barcode_image']
                # 移除路径前缀，获取实际文件路径
                if barcode_path.startswith('barcodes/'):
                    file_path = os.path.join('static', barcode_path)
                else:
                    file_path = barcode_path

                if os.path.exists(file_path):
                    return send_file(
                        file_path,
                        as_attachment=True,
                        download_name=f"barcode_{product_id}_{product.get('barcode', 'unknown')}.png",
                        mimetype='image/png'
                    )
                else:
                    return jsonify({
                        'success': False,
                        'error': '条形码图片文件不存在'
                    })
            else:
                return jsonify({
                    'success': False,
                    'error': '产品不存在或未生成条形码'
                })
        else:
            return jsonify({
                'success': False,
                'error': '库存管理系统不可用'
            })

    except Exception as e:
        logger.error(f"下载条形码失败: {e}")
        return jsonify({
            'success': False,
            'error': '下载条形码失败'
        })


@app.route('/api/admin/inventory/<product_id>/barcode/print')
def print_product_barcode(product_id):
    """打印产品条形码页面"""
    try:
        if not require_admin_auth():
            return '<h1>未授权访问</h1>'

        if inventory_manager:
            product = inventory_manager.get_product_by_id(product_id)
            if product and product.get('barcode_image'):
                barcode_path = product['barcode_image']
                # 构建完整的URL路径
                barcode_url = f"/{barcode_path}"

                # 返回简单的打印页面HTML
                return f'''
                <!DOCTYPE html>
                <html>
                <head>
                    <title>打印条形码 - {product['product_name']}</title>
                    <style>
                        body {{
                            font-family: Arial, sans-serif;
                            text-align: center;
                            padding: 20px;
                        }}
                        .barcode-container {{
                            border: 1px solid #ddd;
                            padding: 20px;
                            margin: 20px auto;
                            max-width: 400px;
                        }}
                        .product-info {{
                            margin-bottom: 15px;
                            font-size: 16px;
                        }}
                        .barcode-image {{
                            margin: 15px 0;
                        }}
                        .barcode-number {{
                            font-family: 'Courier New', monospace;
                            font-size: 18px;
                            font-weight: bold;
                            margin-top: 10px;
                        }}
                        @media print {{
                            body {{ margin: 0; }}
                            .no-print {{ display: none; }}
                        }}
                    </style>
                </head>
                <body>
                    <div class="barcode-container">
                        <div class="product-info">
                            <strong>{product['product_name']}</strong><br>
                            分类: {product['category']}<br>
                            价格: {product['price']}
                        </div>
                        <div class="barcode-image">
                            <img src="{barcode_url}" alt="条形码" style="max-width: 100%; height: auto;">
                        </div>
                        <div class="barcode-number">
                            {product['barcode']}
                        </div>
                    </div>
                    <div class="no-print">
                        <button onclick="window.print()">打印</button>
                        <button onclick="window.close()">关闭</button>
                    </div>
                </body>
                </html>
                '''
            else:
                return '<h1>产品不存在或未生成条形码</h1>'
        else:
            return '<h1>库存管理系统不可用</h1>'

    except Exception as e:
        logger.error(f"打印条形码页面失败: {e}")
        return '<h1>打印条形码页面加载失败</h1>'


# ==================== 批量条形码生成API ====================

@app.route('/api/admin/inventory/barcodes/status')
def check_barcodes_status():
    """检查所有产品的条形码状态"""
    try:
        if not require_admin_auth():
            return jsonify({'success': False, 'error': '未授权访问'})

        generator = BarcodeBatchGenerator()
        status_result = generator.check_products_barcode_status()

        return jsonify(status_result)

    except Exception as e:
        logger.error(f"检查条形码状态失败: {e}")
        return jsonify({
            'success': False,
            'message': f'检查条形码状态失败: {e}',
            'total_products': 0,
            'products_with_barcode': 0,
            'products_without_barcode': 0,
            'products_need_regeneration': 0,
            'products_to_process': []
        })


@app.route('/api/admin/inventory/barcodes/batch-generate', methods=['POST'])
def batch_generate_barcodes():
    """批量生成条形码"""
    try:
        if not require_admin_auth():
            return jsonify({'success': False, 'error': '未授权访问'})

        data = request.get_json() or {}
        product_ids = data.get('product_ids', [])

        # 获取操作员信息
        admin_token = session.get('admin_token')
        session_info = admin_auth.get_session_info(admin_token)
        operator = session_info.get('username', '管理员') if session_info else '管理员'

        generator = BarcodeBatchGenerator()

        if product_ids:
            # 为指定产品生成条形码
            result = generator.generate_barcodes_for_products(product_ids, operator)
        else:
            # 为所有缺失条形码的产品生成
            result = generator.generate_all_missing_barcodes(operator)

        return jsonify(result)

    except Exception as e:
        logger.error(f"批量生成条形码失败: {e}")
        return jsonify({
            'success': False,
            'message': f'批量生成条形码失败: {e}',
            'total_requested': 0,
            'successfully_generated': 0,
            'failed_generations': 0,
            'errors': [str(e)]
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
def add_count_item(count_id):
    """添加盘点项目（支持条形码和产品ID）"""
    try:
        if not require_admin_auth():
            return jsonify({'success': False, 'error': '未授权访问'})

        data = request.get_json()
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
def record_actual_quantity(count_id, product_id):
    """记录产品的实际盘点数量"""
    try:
        if not require_admin_auth():
            return jsonify({'success': False, 'error': '未授权访问'})

        data = request.get_json()
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
def complete_count_task(count_id):
    """完成盘点任务"""
    try:
        if not require_admin_auth():
            return jsonify({'success': False, 'error': '未授权访问'})

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


@app.route('/api/admin/inventory/counts/<count_id>', methods=['DELETE'])
def cancel_count_task(count_id):
    """取消盘点任务"""
    try:
        if not require_admin_auth():
            return jsonify({'success': False, 'error': '未授权访问'})

        data = request.get_json() or {}
        reason = data.get('reason', '')

        if inventory_count_manager:
            success = inventory_count_manager.cancel_count_task(count_id, reason)
            if success:
                return jsonify({
                    'success': True,
                    'message': '盘点任务已取消'
                })
            else:
                return jsonify({
                    'success': False,
                    'error': '取消盘点任务失败'
                })
        else:
            return jsonify({
                'success': False,
                'error': '库存盘点系统不可用'
            })

    except Exception as e:
        print(f"取消盘点任务错误: {e}")
        return jsonify({
            'success': False,
            'error': '取消盘点任务失败'
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
            # 获取包含产品数量统计的存储区域列表
            areas = inventory_manager.get_storage_areas_with_product_counts(include_inactive)
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


@app.route('/api/admin/inventory/storage-areas/<area_id>')
def get_storage_area_detail(area_id):
    """获取存储区域详情"""
    try:
        if not require_admin_auth():
            return jsonify({'success': False, 'error': '未授权访问'})

        if inventory_manager:
            area = inventory_manager.storage_area_manager.get_area_by_id(area_id)
            if area:
                # 添加产品数量统计
                product_counts = inventory_manager.get_storage_area_product_counts()
                area["product_count"] = product_counts.get(area_id, 0)

                return jsonify({
                    'success': True,
                    'data': area
                })
            else:
                return jsonify({
                    'success': False,
                    'error': '存储区域不存在'
                })
        else:
            return jsonify({
                'success': False,
                'error': '库存管理系统不可用'
            })

    except Exception as e:
        print(f"获取存储区域详情错误: {e}")
        return jsonify({
            'success': False,
            'error': '获取存储区域详情失败'
        })


@app.route('/api/admin/inventory/storage-areas/<area_id>', methods=['PUT'])
def update_storage_area(area_id):
    """更新存储区域信息"""
    try:
        if not require_admin_auth():
            return jsonify({'success': False, 'error': '未授权访问'})

        data = request.get_json()
        area_name = data.get('area_name', '').strip()
        description = data.get('description', '').strip()
        capacity = data.get('capacity', 1000)

        if not area_name:
            return jsonify({
                'success': False,
                'error': '请提供区域名称'
            })

        # 获取操作员信息
        operator = get_current_operator()

        if inventory_manager:
            success = inventory_manager.update_storage_area(
                area_id, area_name, description, capacity, operator
            )
            if success:
                return jsonify({
                    'success': True,
                    'message': '存储区域更新成功'
                })
            else:
                return jsonify({
                    'success': False,
                    'error': '更新存储区域失败'
                })
        else:
            return jsonify({
                'success': False,
                'error': '库存管理系统不可用'
            })

    except Exception as e:
        print(f"更新存储区域错误: {e}")
        return jsonify({
            'success': False,
            'error': '更新存储区域失败'
        })


@app.route('/api/admin/inventory/storage-areas/<area_id>', methods=['DELETE'])
def deactivate_storage_area(area_id):
    """停用存储区域"""
    try:
        if not require_admin_auth():
            return jsonify({'success': False, 'error': '未授权访问'})

        # 获取操作员信息
        operator = get_current_operator()

        if inventory_manager:
            success = inventory_manager.deactivate_storage_area(area_id, operator)
            if success:
                return jsonify({
                    'success': True,
                    'message': '存储区域停用成功'
                })
            else:
                return jsonify({
                    'success': False,
                    'error': '停用存储区域失败'
                })
        else:
            return jsonify({
                'success': False,
                'error': '库存管理系统不可用'
            })

    except Exception as e:
        print(f"停用存储区域错误: {e}")
        return jsonify({
            'success': False,
            'error': '停用存储区域失败'
        })


@app.route('/api/admin/inventory/storage-areas/<area_id>/products')
def get_storage_area_products(area_id):
    """获取指定存储区域的产品列表"""
    try:
        if not require_admin_auth():
            return jsonify({'success': False, 'error': '未授权访问'})

        # 获取查询参数
        search = request.args.get('search', '').strip()
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 50))

        if inventory_manager:
            # 获取该存储区域的所有产品
            products = inventory_manager.get_products_by_storage_area(area_id)

            # 如果有搜索条件，进行筛选
            if search:
                filtered_products = []
                search_lower = search.lower()
                for product in products:
                    if (search_lower in product.get('product_name', '').lower() or
                        search_lower in product.get('barcode', '').lower() or
                        search_lower in product.get('product_id', '').lower() or
                        search_lower in product.get('category', '').lower()):
                        filtered_products.append(product)
                products = filtered_products

            # 计算分页
            total = len(products)
            start = (page - 1) * per_page
            end = start + per_page
            paginated_products = products[start:end]

            # 获取存储区域信息
            area_info = inventory_manager.storage_area_manager.get_area_by_id(area_id)

            return jsonify({
                'success': True,
                'data': {
                    'products': paginated_products,
                    'total': total,
                    'page': page,
                    'per_page': per_page,
                    'total_pages': (total + per_page - 1) // per_page,
                    'area_info': area_info
                }
            })
        else:
            return jsonify({
                'success': False,
                'error': '库存管理系统不可用'
            })

    except Exception as e:
        print(f"获取存储区域产品列表错误: {e}")
        return jsonify({
            'success': False,
            'error': '获取产品列表失败'
        })


# ==================== 取货点管理API ====================

@app.route('/api/admin/inventory/pickup-locations')
def get_pickup_locations():
    """获取取货点列表"""
    try:
        if not require_admin_auth():
            return jsonify({'success': False, 'error': '未授权访问'})

        include_inactive = request.args.get('include_inactive', 'false').lower() == 'true'

        if inventory_manager:
            locations = inventory_manager.get_all_pickup_locations(include_inactive)
            return jsonify({
                'success': True,
                'data': locations
            })
        else:
            return jsonify({
                'success': False,
                'error': '库存管理系统不可用'
            })

    except Exception as e:
        print(f"获取取货点列表错误: {e}")
        return jsonify({
            'success': False,
            'error': '获取取货点列表失败'
        })


@app.route('/api/admin/inventory/pickup-locations', methods=['POST'])
def add_pickup_location():
    """添加新的取货点"""
    try:
        if not require_admin_auth():
            return jsonify({'success': False, 'error': '未授权访问'})

        data = request.get_json()
        location_id = data.get('location_id', '').strip().lower()
        location_name = data.get('location_name', '').strip()
        address = data.get('address', '').strip()
        phone = data.get('phone', '').strip()
        contact_person = data.get('contact_person', '').strip()
        business_hours = data.get('business_hours', '请关注群内通知').strip()
        description = data.get('description', '').strip()

        # 获取操作员信息
        admin_token = session.get('admin_token')
        session_info = admin_auth.get_session_info(admin_token)
        operator = session_info.get('username', '管理员') if session_info else '管理员'

        if not location_id or not location_name or not address:
            return jsonify({
                'success': False,
                'error': '请提供取货点ID、名称和地址'
            })

        if inventory_manager:
            success = inventory_manager.add_pickup_location(
                location_id, location_name, address, phone,
                contact_person, business_hours, description, operator
            )
            if success:
                return jsonify({
                    'success': True,
                    'message': '取货点添加成功'
                })
            else:
                return jsonify({
                    'success': False,
                    'error': '添加取货点失败'
                })
        else:
            return jsonify({
                'success': False,
                'error': '库存管理系统不可用'
            })

    except Exception as e:
        print(f"添加取货点错误: {e}")
        return jsonify({
            'success': False,
            'error': '添加取货点失败'
        })


@app.route('/api/admin/inventory/pickup-locations/<location_id>', methods=['PUT'])
def update_pickup_location(location_id):
    """更新取货点信息"""
    try:
        if not require_admin_auth():
            return jsonify({'success': False, 'error': '未授权访问'})

        data = request.get_json()

        # 获取操作员信息
        admin_token = session.get('admin_token')
        session_info = admin_auth.get_session_info(admin_token)
        operator = session_info.get('username', '管理员') if session_info else '管理员'

        # 添加操作员信息到更新数据中
        data['operator'] = operator

        if inventory_manager:
            success = inventory_manager.update_pickup_location(location_id, **data)
            if success:
                return jsonify({
                    'success': True,
                    'message': '取货点更新成功'
                })
            else:
                return jsonify({
                    'success': False,
                    'error': '更新取货点失败'
                })
        else:
            return jsonify({
                'success': False,
                'error': '库存管理系统不可用'
            })

    except Exception as e:
        print(f"更新取货点错误: {e}")
        return jsonify({
            'success': False,
            'error': '更新取货点失败'
        })


@app.route('/api/admin/inventory/pickup-locations/<location_id>', methods=['DELETE'])
def deactivate_pickup_location(location_id):
    """停用取货点"""
    try:
        if not require_admin_auth():
            return jsonify({'success': False, 'error': '未授权访问'})

        # 获取操作员信息
        admin_token = session.get('admin_token')
        session_info = admin_auth.get_session_info(admin_token)
        operator = session_info.get('username', '管理员') if session_info else '管理员'

        if inventory_manager:
            success = inventory_manager.deactivate_pickup_location(location_id, operator)
            if success:
                return jsonify({
                    'success': True,
                    'message': '取货点停用成功'
                })
            else:
                return jsonify({
                    'success': False,
                    'error': '停用取货点失败'
                })
        else:
            return jsonify({
                'success': False,
                'error': '库存管理系统不可用'
            })

    except Exception as e:
        print(f"停用取货点错误: {e}")
        return jsonify({
            'success': False,
            'error': '停用取货点失败'
        })


@app.route('/api/admin/inventory/pickup-locations/<location_id>')
def get_pickup_location_detail(location_id):
    """获取取货点详情"""
    try:
        if not require_admin_auth():
            return jsonify({'success': False, 'error': '未授权访问'})

        if inventory_manager:
            location = inventory_manager.get_pickup_location_by_id(location_id)
            if location:
                return jsonify({
                    'success': True,
                    'data': location
                })
            else:
                return jsonify({
                    'success': False,
                    'error': '取货点不存在'
                })
        else:
            return jsonify({
                'success': False,
                'error': '库存管理系统不可用'
            })

    except Exception as e:
        print(f"获取取货点详情错误: {e}")
        return jsonify({
            'success': False,
            'error': '获取取货点详情失败'
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


# ==================== 政策管理API ====================

@app.route('/api/admin/policies')
def get_policies():
    """获取政策列表"""
    try:
        if not require_admin_auth():
            return jsonify({'success': False, 'error': '未授权访问'})

        status = request.args.get('status')

        if policy_manager:
            policies = policy_manager.get_all_policies(status)
            return jsonify({
                'success': True,
                'data': policies
            })
        else:
            return jsonify({
                'success': False,
                'error': '政策管理系统不可用'
            })

    except Exception as e:
        logger.error(f"获取政策列表错误: {e}")
        return jsonify({
            'success': False,
            'error': '获取政策列表失败'
        })


@app.route('/api/admin/policies/types')
def get_policy_types():
    """获取政策类型列表"""
    try:
        if not require_admin_auth():
            return jsonify({'success': False, 'error': '未授权访问'})

        if policy_manager:
            policy_types = policy_manager.get_policy_types()
            return jsonify({
                'success': True,
                'data': policy_types
            })
        else:
            return jsonify({
                'success': False,
                'error': '政策管理系统不可用'
            })

    except Exception as e:
        logger.error(f"获取政策类型错误: {e}")
        return jsonify({
            'success': False,
            'error': '获取政策类型失败'
        })


@app.route('/api/admin/policies/<int:policy_id>')
def get_policy_detail(policy_id):
    """获取政策详情"""
    try:
        if not require_admin_auth():
            return jsonify({'success': False, 'error': '未授权访问'})

        if policy_manager:
            policy = policy_manager.get_policy_by_id(policy_id)
            if policy:
                return jsonify({
                    'success': True,
                    'data': policy
                })
            else:
                return jsonify({
                    'success': False,
                    'error': '政策不存在'
                })
        else:
            return jsonify({
                'success': False,
                'error': '政策管理系统不可用'
            })

    except Exception as e:
        logger.error(f"获取政策详情错误: {e}")
        return jsonify({
            'success': False,
            'error': '获取政策详情失败'
        })


@app.route('/api/admin/policies/type/<policy_type>')
def get_policy_by_type(policy_type):
    """根据类型获取当前有效政策"""
    try:
        if not require_admin_auth():
            return jsonify({'success': False, 'error': '未授权访问'})

        if policy_manager:
            policy = policy_manager.get_policy_by_type(policy_type)
            if policy:
                return jsonify({
                    'success': True,
                    'data': policy
                })
            else:
                return jsonify({
                    'success': False,
                    'error': '未找到该类型的有效政策'
                })
        else:
            return jsonify({
                'success': False,
                'error': '政策管理系统不可用'
            })

    except Exception as e:
        logger.error(f"获取政策错误: {e}")
        return jsonify({
            'success': False,
            'error': '获取政策失败'
        })


@app.route('/api/admin/policies', methods=['POST'])
def create_policy():
    """创建新政策"""
    try:
        if not require_admin_auth():
            return jsonify({'success': False, 'error': '未授权访问'})

        data = request.get_json()
        operator = get_current_operator()

        if policy_manager:
            success, message, policy_id = policy_manager.create_policy(data, operator)
            if success:
                return jsonify({
                    'success': True,
                    'message': message,
                    'policy_id': policy_id
                })
            else:
                return jsonify({
                    'success': False,
                    'error': message
                })
        else:
            return jsonify({
                'success': False,
                'error': '政策管理系统不可用'
            })

    except Exception as e:
        logger.error(f"创建政策错误: {e}")
        return jsonify({
            'success': False,
            'error': '创建政策失败'
        })


@app.route('/api/admin/policies/<int:policy_id>', methods=['PUT'])
def update_policy(policy_id):
    """更新政策"""
    try:
        if not require_admin_auth():
            return jsonify({'success': False, 'error': '未授权访问'})

        data = request.get_json()
        operator = get_current_operator()

        if policy_manager:
            success, message = policy_manager.update_policy(policy_id, data, operator)
            if success:
                return jsonify({
                    'success': True,
                    'message': message
                })
            else:
                return jsonify({
                    'success': False,
                    'error': message
                })
        else:
            return jsonify({
                'success': False,
                'error': '政策管理系统不可用'
            })

    except Exception as e:
        logger.error(f"更新政策错误: {e}")
        return jsonify({
            'success': False,
            'error': '更新政策失败'
        })


@app.route('/api/admin/policies/<int:policy_id>', methods=['DELETE'])
def delete_policy(policy_id):
    """删除政策（软删除）"""
    try:
        if not require_admin_auth():
            return jsonify({'success': False, 'error': '未授权访问'})

        operator = get_current_operator()

        if policy_manager:
            success, message = policy_manager.delete_policy(policy_id, operator)
            if success:
                return jsonify({
                    'success': True,
                    'message': message
                })
            else:
                return jsonify({
                    'success': False,
                    'error': message
                })
        else:
            return jsonify({
                'success': False,
                'error': '政策管理系统不可用'
            })

    except Exception as e:
        logger.error(f"删除政策错误: {e}")
        return jsonify({
            'success': False,
            'error': '删除政策失败'
        })


@app.route('/api/admin/policies/<int:policy_id>/publish', methods=['POST'])
def publish_policy(policy_id):
    """发布政策"""
    try:
        if not require_admin_auth():
            return jsonify({'success': False, 'error': '未授权访问'})

        operator = get_current_operator()

        if policy_manager:
            success, message = policy_manager.publish_policy(policy_id, operator)
            if success:
                return jsonify({
                    'success': True,
                    'message': message
                })
            else:
                return jsonify({
                    'success': False,
                    'error': message
                })
        else:
            return jsonify({
                'success': False,
                'error': '政策管理系统不可用'
            })

    except Exception as e:
        logger.error(f"发布政策错误: {e}")
        return jsonify({
            'success': False,
            'error': '发布政策失败'
        })


@app.route('/api/admin/policies/search')
def search_policies():
    """搜索政策"""
    try:
        if not require_admin_auth():
            return jsonify({'success': False, 'error': '未授权访问'})

        keyword = request.args.get('keyword', '')
        policy_type = request.args.get('policy_type')

        if policy_manager:
            policies = policy_manager.search_policies(keyword, policy_type)
            return jsonify({
                'success': True,
                'data': policies
            })
        else:
            return jsonify({
                'success': False,
                'error': '政策管理系统不可用'
            })

    except Exception as e:
        logger.error(f"搜索政策错误: {e}")
        return jsonify({
            'success': False,
            'error': '搜索政策失败'
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
    logger.info("启动果蔬客服AI系统...")

    # 获取端口配置（Render会提供PORT环境变量）
    port = int(os.environ.get('PORT', 5000))
    debug_mode = os.environ.get('FLASK_ENV') != 'production'

    # 初始化系统
    if initialize_system():
        logger.info(f"启动Web服务器... 端口: {port}")
        app.run(debug=debug_mode, host='0.0.0.0', port=port)
    else:
        logger.error("系统初始化失败，无法启动服务器")
