#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
安全配置验证脚本
"""
import os
import sys
import re
from typing import List, Tuple

def check_environment_variables() -> List[Tuple[str, bool, str]]:
    """检查环境变量配置"""
    checks = []
    
    # 必需的环境变量
    secret_key = os.environ.get('SECRET_KEY')
    if secret_key:
        if len(secret_key) >= 32:
            checks.append(("SECRET_KEY", True, f"✅ 密钥长度: {len(secret_key)} 字符"))
        else:
            checks.append(("SECRET_KEY", False, f"❌ 密钥过短: {len(secret_key)} 字符 (需要至少32字符)"))
    else:
        checks.append(("SECRET_KEY", False, "❌ 未设置 SECRET_KEY"))
    
    # LLM API配置
    llm_api_key = os.environ.get('LLM_API_KEY')
    if llm_api_key:
        checks.append(("LLM_API_KEY", True, "✅ LLM API密钥已设置"))
    else:
        checks.append(("LLM_API_KEY", False, "❌ 未设置 LLM_API_KEY"))
    
    # Flask环境
    flask_env = os.environ.get('FLASK_ENV', 'development')
    if flask_env == 'production':
        checks.append(("FLASK_ENV", True, "✅ 生产环境配置"))
    else:
        checks.append(("FLASK_ENV", False, f"⚠️  当前环境: {flask_env} (建议生产环境设置为 'production')"))
    
    # Redis配置
    redis_url = os.environ.get('REDIS_URL')
    if redis_url:
        checks.append(("REDIS_URL", True, "✅ Redis连接已配置"))
    else:
        checks.append(("REDIS_URL", False, "⚠️  未设置 REDIS_URL (将使用内存存储)"))
    
    return checks

def check_file_permissions() -> List[Tuple[str, bool, str]]:
    """检查文件权限"""
    checks = []
    
    critical_files = [
        'data/admin.json',
        'data/inventory.json',
        '.env'
    ]
    
    for file_path in critical_files:
        if os.path.exists(file_path):
            stat = os.stat(file_path)
            mode = oct(stat.st_mode)[-3:]
            
            # 检查文件权限（应该限制为600或644）
            if mode in ['600', '644', '640']:
                checks.append((file_path, True, f"✅ 文件权限: {mode}"))
            else:
                checks.append((file_path, False, f"⚠️  文件权限: {mode} (建议设置为600)"))
        else:
            checks.append((file_path, False, f"❌ 文件不存在: {file_path}"))
    
    return checks

def check_dependencies() -> List[Tuple[str, bool, str]]:
    """检查安全相关依赖"""
    checks = []
    
    required_packages = [
        'pydantic',
        'redis',
        'bleach',
        'werkzeug'
    ]
    
    for package in required_packages:
        try:
            __import__(package)
            checks.append((package, True, f"✅ {package} 已安装"))
        except ImportError:
            checks.append((package, False, f"❌ {package} 未安装"))
    
    return checks

def check_security_configuration() -> List[Tuple[str, bool, str]]:
    """检查安全配置"""
    checks = []
    
    try:
        # 检查安全配置模块
        from src.utils.security_config_enhanced import security_config
        checks.append(("security_config", True, "✅ 安全配置模块可用"))
        
        # 检查会话管理器
        from src.utils.session_manager import session_manager
        stats = session_manager.get_session_stats()
        checks.append(("session_manager", True, f"✅ 会话管理器可用 (当前会话: {stats['total_sessions']})"))
        
        # 检查文件处理器
        from src.utils.secure_file_handler import secure_file_handler
        checks.append(("secure_file_handler", True, "✅ 安全文件处理器可用"))
        
        # 检查验证器
        from src.utils.validators import ChatMessageRequest
        checks.append(("validators", True, "✅ 输入验证器可用"))
        
    except ImportError as e:
        checks.append(("security_modules", False, f"❌ 安全模块导入失败: {e}"))
    
    return checks

def test_redis_connection() -> Tuple[bool, str]:
    """测试Redis连接"""
    try:
        import redis
        redis_url = os.environ.get('REDIS_URL', 'redis://localhost:6379/0')
        
        client = redis.from_url(redis_url, decode_responses=True)
        client.ping()
        
        return True, "✅ Redis连接成功"
    except Exception as e:
        return False, f"❌ Redis连接失败: {e}"

def generate_secure_key() -> str:
    """生成安全密钥"""
    import secrets
    return secrets.token_urlsafe(32)

def main():
    """主函数"""
    print("🔒 安全配置验证")
    print("=" * 50)
    
    all_passed = True
    
    # 环境变量检查
    print("\n📋 环境变量检查")
    print("-" * 30)
    env_checks = check_environment_variables()
    for name, passed, message in env_checks:
        print(f"{message}")
        if not passed:
            all_passed = False
    
    # 文件权限检查
    print("\n📁 文件权限检查")
    print("-" * 30)
    file_checks = check_file_permissions()
    for name, passed, message in file_checks:
        print(f"{message}")
        if not passed and "不存在" not in message:
            all_passed = False
    
    # 依赖检查
    print("\n📦 依赖包检查")
    print("-" * 30)
    dep_checks = check_dependencies()
    for name, passed, message in dep_checks:
        print(f"{message}")
        if not passed:
            all_passed = False
    
    # 安全配置检查
    print("\n🛡️  安全配置检查")
    print("-" * 30)
    security_checks = check_security_configuration()
    for name, passed, message in security_checks:
        print(f"{message}")
        if not passed:
            all_passed = False
    
    # Redis连接测试
    print("\n🔗 Redis连接测试")
    print("-" * 30)
    redis_passed, redis_message = test_redis_connection()
    print(redis_message)
    if not redis_passed:
        print("⚠️  Redis不可用时系统将使用内存存储")
    
    # 总结
    print("\n" + "=" * 50)
    if all_passed:
        print("🎉 所有安全检查通过！系统可以安全部署。")
    else:
        print("⚠️  发现安全问题，请根据上述提示进行修复。")
        
        # 提供修复建议
        print("\n🔧 修复建议:")
        if not os.environ.get('SECRET_KEY'):
            print(f"   export SECRET_KEY='{generate_secure_key()}'")
        
        if not os.environ.get('LLM_API_KEY'):
            print("   export LLM_API_KEY='your_deepseek_api_key'")
        
        print("   pip install -r requirements.txt")
    
    print("\n📖 详细部署指南请参考: docs/SECURITY_DEPLOYMENT_GUIDE.md")
    
    return 0 if all_passed else 1

if __name__ == "__main__":
    sys.exit(main())