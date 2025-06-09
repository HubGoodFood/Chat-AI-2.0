#!/usr/bin/env python3
"""
生成Flask SECRET_KEY的工具脚本
"""
import secrets
import os
import base64

def generate_secret_key_methods():
    """生成SECRET_KEY的多种方法"""
    
    print("🔐 Flask SECRET_KEY 生成工具")
    print("=" * 50)
    
    # 方法1：使用secrets模块（最推荐）
    secret_key_1 = secrets.token_hex(32)  # 64字符的十六进制字符串
    print(f"方法1 - secrets.token_hex(32):")
    print(f"SECRET_KEY={secret_key_1}")
    print()
    
    # 方法2：使用secrets.token_urlsafe（URL安全）
    secret_key_2 = secrets.token_urlsafe(32)  # 43字符的URL安全字符串
    print(f"方法2 - secrets.token_urlsafe(32):")
    print(f"SECRET_KEY={secret_key_2}")
    print()
    
    # 方法3：使用os.urandom + base64
    secret_key_3 = base64.b64encode(os.urandom(32)).decode('utf-8')
    print(f"方法3 - os.urandom + base64:")
    print(f"SECRET_KEY={secret_key_3}")
    print()
    
    # 方法4：使用uuid（不太推荐，但简单）
    import uuid
    secret_key_4 = str(uuid.uuid4()).replace('-', '') + str(uuid.uuid4()).replace('-', '')
    print(f"方法4 - 双UUID组合:")
    print(f"SECRET_KEY={secret_key_4}")
    print()
    
    print("🎯 推荐使用方法1或方法2")
    print("💡 密钥长度建议：至少32字节（64个十六进制字符）")
    print("⚠️  注意：生产环境中绝不要使用默认或简单的密钥！")

def validate_secret_key(key):
    """验证SECRET_KEY的安全性"""
    print(f"\n🔍 验证SECRET_KEY安全性: {key[:10]}...")
    
    issues = []
    
    # 检查长度
    if len(key) < 32:
        issues.append("❌ 密钥长度不足32字符，安全性较低")
    else:
        print("✅ 密钥长度充足")
    
    # 检查是否为常见弱密钥
    weak_keys = [
        'your_secret_key_here',
        'secret',
        'password',
        'key',
        'flask_secret',
        'development_key'
    ]
    
    if key.lower() in weak_keys:
        issues.append("❌ 使用了常见的弱密钥")
    else:
        print("✅ 不是常见弱密钥")
    
    # 检查字符复杂性
    has_upper = any(c.isupper() for c in key)
    has_lower = any(c.islower() for c in key)
    has_digit = any(c.isdigit() for c in key)
    has_special = any(c in '!@#$%^&*()_+-=[]{}|;:,.<>?' for c in key)
    
    complexity_score = sum([has_upper, has_lower, has_digit, has_special])
    
    if complexity_score >= 3:
        print("✅ 字符复杂性良好")
    else:
        issues.append("⚠️  建议增加字符复杂性（大小写、数字、特殊字符）")
    
    if not issues:
        print("🎉 SECRET_KEY 安全性良好！")
    else:
        print("\n⚠️  发现以下安全问题：")
        for issue in issues:
            print(f"   {issue}")

if __name__ == "__main__":
    generate_secret_key_methods()
    
    # 示例验证
    print("\n" + "=" * 50)
    print("🧪 示例验证：")
    
    # 验证一个好的密钥
    good_key = secrets.token_hex(32)
    validate_secret_key(good_key)
    
    # 验证一个弱密钥
    print("\n" + "-" * 30)
    weak_key = "your_secret_key_here"
    validate_secret_key(weak_key)
