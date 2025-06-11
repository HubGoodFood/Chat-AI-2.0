"""
简化版Flask配置修复模块 - 避免Unicode编码问题
"""
import os
from flask import Flask


def apply_simple_fixes(app: Flask):
    """应用简化的Flask配置修复"""
    print("[CONFIG] Applying Flask configuration fixes...")
    
    try:
        # 1. 禁用模板缓存
        app.config['TEMPLATES_AUTO_RELOAD'] = True
        app.jinja_env.auto_reload = True
        if hasattr(app.jinja_env, 'cache'):
            app.jinja_env.cache = {}
        print("[OK] Template cache disabled")
        
        # 2. 禁用静态文件缓存
        app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0
        print("[OK] Static file cache disabled")
        
        # 3. 设置调试模式
        flask_env = os.environ.get('FLASK_ENV', 'development')
        if flask_env == 'development':
            app.debug = True
            app.config['DEBUG'] = True
            app.config['USE_RELOADER'] = True
            print("[OK] Debug mode enabled")
        
        # 4. 设置无缓存响应头
        @app.after_request
        def add_no_cache_headers(response):
            if app.debug:
                response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
                response.headers['Pragma'] = 'no-cache'
                response.headers['Expires'] = '0'
            return response
        
        print("[OK] No-cache headers configured")
        
        # 5. 优化开发环境
        if app.debug:
            app.config['PROPAGATE_EXCEPTIONS'] = True
            app.config['PERMANENT_SESSION_LIFETIME'] = 3600
            print("[OK] Development environment optimized")
        
        print("[CONFIG] Flask configuration fixes applied successfully")
        return True
        
    except Exception as e:
        print(f"[ERROR] Flask configuration fix failed: {e}")
        return False


# 导出
__all__ = ['apply_simple_fixes']
