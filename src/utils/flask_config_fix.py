"""
Flask配置修复模块 - 解决缓存、调试模式和端口冲突问题
"""
import os
import signal
import psutil
from flask import Flask


class FlaskConfigFix:
    """Flask配置修复类"""
    
    def __init__(self):
        self.fixed_issues = []
        self.warnings = []
    
    def apply_fixes(self, app: Flask):
        """应用所有修复"""
        print("[CONFIG] 开始应用Flask配置修复...")

        # 1. 修复缓存问题
        self._fix_cache_issues(app)

        # 2. 修复调试模式
        self._fix_debug_mode(app)

        # 3. 修复模板配置
        self._fix_template_config(app)

        # 4. 检查端口冲突
        self._check_port_conflicts()

        # 5. 优化开发环境配置
        self._optimize_dev_config(app)

        # 输出修复结果
        self._print_fix_results()

        return len(self.fixed_issues) > 0
    
    def _fix_cache_issues(self, app: Flask):
        """修复缓存问题"""
        try:
            # 禁用模板缓存
            app.config['TEMPLATES_AUTO_RELOAD'] = True
            app.jinja_env.auto_reload = True
            app.jinja_env.cache = {}
            self.fixed_issues.append("[OK] 已禁用模板缓存")

            # 禁用静态文件缓存
            app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0
            self.fixed_issues.append("[OK] 已禁用静态文件缓存")
            
            # 设置缓存控制头
            @app.after_request
            def after_request(response):
                if app.debug:
                    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
                    response.headers['Pragma'] = 'no-cache'
                    response.headers['Expires'] = '0'
                return response
            
            self.fixed_issues.append("✅ 已设置无缓存响应头")
            
        except Exception as e:
            self.warnings.append(f"⚠️ 缓存修复部分失败: {e}")
    
    def _fix_debug_mode(self, app: Flask):
        """修复调试模式配置"""
        try:
            # 确保调试模式正确设置
            debug_env = os.environ.get('DEBUG', 'True').lower() == 'true'
            flask_env = os.environ.get('FLASK_ENV', 'development')
            
            if flask_env == 'development':
                app.debug = True
                app.config['DEBUG'] = True
                self.fixed_issues.append("✅ 已启用调试模式")
            else:
                app.debug = False
                app.config['DEBUG'] = False
                self.fixed_issues.append("✅ 已禁用调试模式（生产环境）")
            
            # 设置热重载
            if app.debug:
                app.config['USE_RELOADER'] = True
                self.fixed_issues.append("✅ 已启用热重载")
            
        except Exception as e:
            self.warnings.append(f"⚠️ 调试模式修复失败: {e}")
    
    def _fix_template_config(self, app: Flask):
        """修复模板配置"""
        try:
            # 强制模板重新加载
            app.jinja_env.auto_reload = True
            app.config['TEMPLATES_AUTO_RELOAD'] = True
            
            # 清除模板缓存
            if hasattr(app.jinja_env, 'cache'):
                app.jinja_env.cache.clear()
            
            # 设置模板调试
            if app.debug:
                app.jinja_env.undefined = 'jinja2.DebugUndefined'
            
            self.fixed_issues.append("✅ 已优化模板配置")
            
        except Exception as e:
            self.warnings.append(f"⚠️ 模板配置修复失败: {e}")
    
    def _check_port_conflicts(self):
        """检查端口冲突"""
        try:
            port = int(os.environ.get('PORT', 5000))
            
            # 查找占用指定端口的进程
            conflicting_processes = []
            for proc in psutil.process_iter(['pid', 'name', 'connections']):
                try:
                    for conn in proc.info['connections'] or []:
                        if conn.laddr.port == port and conn.status == 'LISTEN':
                            conflicting_processes.append({
                                'pid': proc.info['pid'],
                                'name': proc.info['name']
                            })
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            
            if conflicting_processes:
                self.warnings.append(f"⚠️ 发现{len(conflicting_processes)}个进程占用端口{port}")
                for proc in conflicting_processes[:5]:  # 只显示前5个
                    self.warnings.append(f"   - PID {proc['pid']}: {proc['name']}")
                
                if len(conflicting_processes) > 5:
                    self.warnings.append(f"   - 还有{len(conflicting_processes) - 5}个进程...")
            else:
                self.fixed_issues.append(f"✅ 端口{port}无冲突")
                
        except Exception as e:
            self.warnings.append(f"⚠️ 端口冲突检查失败: {e}")
    
    def _optimize_dev_config(self, app: Flask):
        """优化开发环境配置"""
        try:
            if app.debug:
                # 设置更详细的错误信息
                app.config['PROPAGATE_EXCEPTIONS'] = True
                
                # 禁用CSRF（开发环境）
                app.config['WTF_CSRF_ENABLED'] = False
                
                # 设置更长的会话超时
                app.config['PERMANENT_SESSION_LIFETIME'] = 3600  # 1小时
                
                self.fixed_issues.append("✅ 已优化开发环境配置")
            
        except Exception as e:
            self.warnings.append(f"⚠️ 开发环境优化失败: {e}")
    
    def _print_fix_results(self):
        """输出修复结果"""
        print("\n" + "="*50)
        print("🔧 Flask配置修复结果")
        print("="*50)
        
        if self.fixed_issues:
            print("\n✅ 成功修复的问题:")
            for issue in self.fixed_issues:
                print(f"  {issue}")
        
        if self.warnings:
            print("\n⚠️ 警告信息:")
            for warning in self.warnings:
                print(f"  {warning}")
        
        if not self.fixed_issues and not self.warnings:
            print("✅ 没有发现需要修复的问题")
        
        print("\n" + "="*50)
    
    def kill_conflicting_processes(self, port=5000, exclude_current=True):
        """终止占用指定端口的进程"""
        killed_count = 0
        current_pid = os.getpid()
        
        try:
            for proc in psutil.process_iter(['pid', 'name', 'connections']):
                try:
                    # 跳过当前进程
                    if exclude_current and proc.info['pid'] == current_pid:
                        continue
                    
                    for conn in proc.info['connections'] or []:
                        if conn.laddr.port == port and conn.status == 'LISTEN':
                            print(f"🔪 终止进程 PID {proc.info['pid']}: {proc.info['name']}")
                            proc.terminate()
                            killed_count += 1
                            break
                            
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            
            if killed_count > 0:
                print(f"✅ 已终止 {killed_count} 个冲突进程")
            else:
                print("ℹ️ 没有发现冲突进程")
                
        except Exception as e:
            print(f"❌ 终止进程失败: {e}")
        
        return killed_count


def apply_flask_fixes(app: Flask):
    """应用Flask配置修复的便捷函数"""
    fixer = FlaskConfigFix()
    return fixer.apply_fixes(app)


def clean_port_conflicts(port=5000):
    """清理端口冲突的便捷函数"""
    fixer = FlaskConfigFix()
    return fixer.kill_conflicting_processes(port)


# 导出
__all__ = [
    'FlaskConfigFix',
    'apply_flask_fixes',
    'clean_port_conflicts'
]
