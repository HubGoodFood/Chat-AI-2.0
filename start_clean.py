#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
清洁启动脚本 - 预防端口冲突和确保单一Flask实例
"""
import os
import sys
import time
import subprocess
import psutil
from datetime import datetime


def print_status(message, status="INFO"):
    """打印状态信息"""
    timestamp = datetime.now().strftime("%H:%M:%S")
    print(f"[{timestamp}] [{status}] {message}")


def check_and_kill_port_processes(port=5000):
    """检查并终止占用指定端口的进程"""
    print_status(f"检查端口 {port} 的占用情况...")
    
    killed_count = 0
    current_pid = os.getpid()
    
    try:
        for proc in psutil.process_iter(['pid', 'name', 'connections', 'cmdline']):
            try:
                # 跳过当前进程
                if proc.info['pid'] == current_pid:
                    continue
                
                # 检查进程的网络连接
                for conn in proc.info['connections'] or []:
                    if (hasattr(conn, 'laddr') and 
                        conn.laddr.port == port and 
                        conn.status == 'LISTEN'):
                        
                        # 检查是否是Python进程
                        cmdline = proc.info['cmdline'] or []
                        is_python = any('python' in str(cmd).lower() for cmd in cmdline)
                        is_flask = any('app.py' in str(cmd) or 'flask' in str(cmd).lower() for cmd in cmdline)
                        
                        print_status(f"发现进程占用端口 {port}: PID {proc.info['pid']} ({proc.info['name']})")
                        if is_python or is_flask:
                            print_status(f"  -> Python/Flask进程，正在终止...")
                            proc.terminate()
                            killed_count += 1
                        else:
                            print_status(f"  -> 非Python进程，跳过")
                        break
                        
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                continue
        
        if killed_count > 0:
            print_status(f"已终止 {killed_count} 个冲突进程，等待进程完全停止...")
            time.sleep(3)
        else:
            print_status(f"端口 {port} 没有冲突进程")
            
    except Exception as e:
        print_status(f"检查端口进程时出错: {e}", "ERROR")
    
    return killed_count


def check_python_processes():
    """检查是否有其他Python Flask进程在运行"""
    print_status("检查其他Python Flask进程...")
    
    current_pid = os.getpid()
    flask_processes = []
    
    try:
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            try:
                if proc.info['pid'] == current_pid:
                    continue
                
                cmdline = proc.info['cmdline'] or []
                cmdline_str = ' '.join(str(cmd) for cmd in cmdline).lower()
                
                # 检查是否是Flask相关进程
                if (proc.info['name'].lower() in ['python.exe', 'pythonw.exe', 'python'] and
                    ('app.py' in cmdline_str or 'flask' in cmdline_str)):
                    flask_processes.append({
                        'pid': proc.info['pid'],
                        'name': proc.info['name'],
                        'cmdline': cmdline_str
                    })
                    
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
    
    except Exception as e:
        print_status(f"检查Python进程时出错: {e}", "ERROR")
    
    if flask_processes:
        print_status(f"发现 {len(flask_processes)} 个Flask进程:")
        for proc in flask_processes:
            print_status(f"  - PID {proc['pid']}: {proc['cmdline'][:100]}...")
        
        # 询问是否终止
        try:
            response = input("是否终止这些进程? (y/N): ").strip().lower()
            if response == 'y':
                for proc in flask_processes:
                    try:
                        psutil.Process(proc['pid']).terminate()
                        print_status(f"已终止进程 PID {proc['pid']}")
                    except Exception as e:
                        print_status(f"终止进程 PID {proc['pid']} 失败: {e}", "ERROR")
                time.sleep(2)
        except KeyboardInterrupt:
            print_status("用户取消操作")
    else:
        print_status("没有发现其他Flask进程")


def clean_cache_files():
    """清理Python缓存文件"""
    print_status("清理Python缓存文件...")
    
    cleaned_count = 0
    
    try:
        for root, dirs, files in os.walk('.'):
            # 清理__pycache__目录
            if '__pycache__' in dirs:
                cache_dir = os.path.join(root, '__pycache__')
                try:
                    import shutil
                    shutil.rmtree(cache_dir)
                    cleaned_count += 1
                except Exception as e:
                    print_status(f"清理缓存目录失败: {cache_dir} - {e}", "WARN")
            
            # 清理.pyc文件
            for file in files:
                if file.endswith(('.pyc', '.pyo')):
                    file_path = os.path.join(root, file)
                    try:
                        os.remove(file_path)
                        cleaned_count += 1
                    except Exception as e:
                        print_status(f"删除缓存文件失败: {file_path} - {e}", "WARN")
        
        if cleaned_count > 0:
            print_status(f"已清理 {cleaned_count} 个缓存文件/目录")
        else:
            print_status("没有发现需要清理的缓存文件")
            
    except Exception as e:
        print_status(f"清理缓存时出错: {e}", "ERROR")


def verify_environment():
    """验证运行环境"""
    print_status("验证运行环境...")
    
    # 检查必要文件
    required_files = ['app.py', 'src/utils/i18n_simple.py', '.env']
    missing_files = []
    
    for file_path in required_files:
        if not os.path.exists(file_path):
            missing_files.append(file_path)
    
    if missing_files:
        print_status(f"缺少必要文件: {', '.join(missing_files)}", "ERROR")
        return False
    
    # 检查环境变量
    if not os.path.exists('.env'):
        print_status("缺少.env配置文件", "WARN")
    
    print_status("环境验证通过")
    return True


def start_flask_app():
    """启动Flask应用"""
    print_status("启动Flask应用...")
    
    try:
        # 设置环境变量
        os.environ['PYTHONPATH'] = os.getcwd()
        
        # 启动Flask应用
        import app
        
        # 获取端口配置
        port = int(os.environ.get('PORT', 5000))
        debug_mode = os.environ.get('FLASK_ENV', 'development') == 'development'
        
        print_status(f"Flask应用配置: 端口={port}, 调试模式={debug_mode}")
        print_status("Flask应用启动中...")
        print_status("访问地址: http://localhost:5000")
        print_status("按 Ctrl+C 停止服务器")
        
        # 启动应用
        app.app.run(debug=debug_mode, host='0.0.0.0', port=port, use_reloader=False)
        
    except KeyboardInterrupt:
        print_status("用户停止了服务器")
    except Exception as e:
        print_status(f"启动Flask应用失败: {e}", "ERROR")
        return False
    
    return True


def main():
    """主函数"""
    print("=" * 60)
    print("Flask应用清洁启动工具")
    print("=" * 60)
    print_status("开始清洁启动流程...")
    
    # 1. 验证环境
    if not verify_environment():
        print_status("环境验证失败，无法启动", "ERROR")
        return
    
    # 2. 检查并清理端口冲突
    check_and_kill_port_processes(5000)
    
    # 3. 检查其他Python进程
    check_python_processes()
    
    # 4. 清理缓存
    clean_cache_files()
    
    # 5. 启动Flask应用
    print_status("准备启动Flask应用...")
    time.sleep(1)
    
    if start_flask_app():
        print_status("Flask应用已正常退出")
    else:
        print_status("Flask应用启动失败", "ERROR")


if __name__ == "__main__":
    main()
