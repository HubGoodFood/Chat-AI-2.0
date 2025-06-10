"""
国际化配置模块 - 多语言支持
"""
import os
from flask import request, session
from flask_babel import Babel, gettext, ngettext, lazy_gettext
from typing import Dict, List


class I18nConfig:
    """国际化配置管理类"""
    
    def __init__(self, app=None):
        self.app = app
        self.babel = None
        
        # 支持的语言配置
        self.languages = {
            'zh': {
                'name': '简体中文',
                'native_name': '简体中文',
                'flag': '🇨🇳',
                'code': 'zh'
            },
            'en': {
                'name': 'English',
                'native_name': 'English',
                'flag': '🇺🇸',
                'code': 'en'
            },
            'zh_TW': {
                'name': '繁體中文',
                'native_name': '繁體中文',
                'flag': '🇹🇼',
                'code': 'zh_TW'
            }
        }
        
        # 默认语言
        self.default_language = os.environ.get('DEFAULT_LANGUAGE', 'zh')
        
        if app:
            self.init_app(app)
    
    def init_app(self, app):
        """初始化Flask应用的国际化配置"""
        self.app = app
        
        # 配置Babel
        app.config['LANGUAGES'] = self.languages
        app.config['BABEL_DEFAULT_LOCALE'] = self.default_language
        app.config['BABEL_DEFAULT_TIMEZONE'] = 'UTC'
        
        # 初始化Babel
        self.babel = Babel()
        self.babel.init_app(app)

        # 设置语言选择器
        self.babel.locale_selector_func = self.get_locale
        
        # 注册模板全局函数
        self._register_template_globals(app)
        
        print(f"国际化配置初始化完成 - 支持语言: {list(self.languages.keys())}")
    
    def get_locale(self):
        """
        获取当前语言设置
        优先级：用户选择 > 浏览器语言 > 默认语言
        """
        # 1. 检查用户是否手动选择了语言
        if 'language' in session:
            selected_lang = session['language']
            if selected_lang in self.languages:
                return selected_lang
        
        # 2. 检查浏览器语言偏好
        if request:
            browser_lang = request.accept_languages.best_match(list(self.languages.keys()))
            if browser_lang:
                return browser_lang
        
        # 3. 返回默认语言
        return self.default_language
    
    def set_language(self, language_code: str) -> bool:
        """
        设置用户语言偏好
        
        Args:
            language_code: 语言代码
            
        Returns:
            bool: 设置是否成功
        """
        if language_code in self.languages:
            session['language'] = language_code
            return True
        return False
    
    def get_current_language(self) -> Dict:
        """获取当前语言信息"""
        current_code = self.get_locale()
        return self.languages.get(current_code, self.languages[self.default_language])
    
    def get_available_languages(self) -> List[Dict]:
        """获取所有可用语言列表"""
        return [
            {
                'code': code,
                'name': info['name'],
                'native_name': info['native_name'],
                'flag': info['flag'],
                'is_current': code == self.get_locale()
            }
            for code, info in self.languages.items()
        ]
    
    def _register_template_globals(self, app):
        """注册模板全局函数"""
        
        @app.template_global()
        def get_current_language():
            """模板中获取当前语言"""
            return self.get_current_language()
        
        @app.template_global()
        def get_available_languages():
            """模板中获取可用语言列表"""
            return self.get_available_languages()
        
        @app.template_global()
        def _t(text, **kwargs):
            """模板中的翻译函数（简化版）"""
            return gettext(text, **kwargs)
        
        @app.template_global()
        def _nt(singular, plural, num, **kwargs):
            """模板中的复数翻译函数"""
            return ngettext(singular, plural, num, **kwargs)


# 全局国际化配置实例
i18n_config = I18nConfig()


# 便捷的翻译函数
def _(text, **kwargs):
    """翻译函数的简化别名"""
    return gettext(text, **kwargs)


def _n(singular, plural, num, **kwargs):
    """复数翻译函数的简化别名"""
    return ngettext(singular, plural, num, **kwargs)


def _l(text, **kwargs):
    """延迟翻译函数（用于在模块加载时定义翻译文本）"""
    return lazy_gettext(text, **kwargs)


# 常用的系统消息翻译
class SystemMessages:
    """系统消息翻译类"""
    
    # 通用消息
    SUCCESS = _l('操作成功')
    ERROR = _l('操作失败')
    LOADING = _l('加载中...')
    SAVING = _l('保存中...')
    
    # 认证消息
    LOGIN_SUCCESS = _l('登录成功')
    LOGIN_FAILED = _l('登录失败')
    LOGOUT_SUCCESS = _l('已退出登录')
    UNAUTHORIZED = _l('未授权访问')
    
    # 验证消息
    REQUIRED_FIELD = _l('此字段为必填项')
    INVALID_FORMAT = _l('格式不正确')
    TOO_LONG = _l('内容过长')
    TOO_SHORT = _l('内容过短')
    
    # 网络消息
    NETWORK_ERROR = _l('网络连接错误')
    SERVER_ERROR = _l('服务器错误')
    TIMEOUT_ERROR = _l('请求超时')
    
    # 业务消息
    INVENTORY_UPDATED = _l('库存更新成功')
    FEEDBACK_ADDED = _l('反馈添加成功')
    DATA_EXPORTED = _l('数据导出成功')


# 常用的界面文本翻译
class UITexts:
    """界面文本翻译类"""
    
    # 导航菜单
    HOME = _l('首页')
    ADMIN = _l('管理后台')
    INVENTORY = _l('库存管理')
    FEEDBACK = _l('客户反馈')
    REPORTS = _l('报告')
    SETTINGS = _l('设置')
    
    # 按钮文本
    LOGIN = _l('登录')
    LOGOUT = _l('退出')
    SAVE = _l('保存')
    CANCEL = _l('取消')
    DELETE = _l('删除')
    EDIT = _l('编辑')
    ADD = _l('添加')
    SEARCH = _l('搜索')
    EXPORT = _l('导出')
    
    # 表单标签
    USERNAME = _l('用户名')
    PASSWORD = _l('密码')
    EMAIL = _l('邮箱')
    PHONE = _l('电话')
    NAME = _l('姓名')
    DESCRIPTION = _l('描述')
    
    # 状态文本
    ACTIVE = _l('活跃')
    INACTIVE = _l('非活跃')
    PENDING = _l('待处理')
    PROCESSING = _l('处理中')
    COMPLETED = _l('已完成')
    
    # 聊天界面
    CHAT_PLACEHOLDER = _l('请输入您的问题...')
    CHAT_SEND = _l('发送')
    CHAT_CLEAR = _l('清除对话')
    CHAT_WELCOME = _l('欢迎使用果蔬客服AI助手！')


# 导出常用函数和类
__all__ = [
    'i18n_config',
    '_', '_n', '_l',
    'SystemMessages',
    'UITexts'
]
