#!/usr/bin/env python3
"""
完整的语言切换功能测试脚本
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import json
from app import app

def test_language_api():
    """测试语言切换API"""
    print("=== 语言切换API测试 ===\n")
    
    with app.test_client() as client:
        # 测试获取语言信息
        print("1. 测试获取语言信息API")
        response = client.get('/api/language')
        data = response.get_json()
        print(f"   状态码: {response.status_code}")
        if data and 'current_language' in data:
            current_lang = data['current_language']
            print(f"   当前语言代码: {current_lang.get('code', 'unknown')}")
            print(f"   当前语言名称: {current_lang.get('name', 'unknown')}")
        print(f"   成功状态: {data.get('success', False) if data else False}")
        print()
        
        # 测试切换到英文
        print("2. 测试切换到英文")
        response = client.post('/api/language/en')
        data = response.get_json()
        print(f"   状态码: {response.status_code}")
        print(f"   成功状态: {data.get('success', False) if data else False}")
        print()

        # 再次获取语言信息，验证切换是否成功
        print("3. 验证语言切换结果")
        response = client.get('/api/language')
        data = response.get_json()
        print(f"   状态码: {response.status_code}")
        print(f"   当前语言: {data.get('current_language', {}).get('code')}")
        print()

        # 测试切换回中文
        print("4. 测试切换回中文")
        response = client.post('/api/language/zh')
        data = response.get_json()
        print(f"   状态码: {response.status_code}")
        print(f"   成功状态: {data.get('success', False) if data else False}")
        print()

        # 测试无效语言
        print("5. 测试无效语言")
        response = client.post('/api/language/fr')
        data = response.get_json()
        print(f"   状态码: {response.status_code}")
        print(f"   成功状态: {data.get('success', False) if data else False}")
        print()

def test_template_rendering():
    """测试模板渲染"""
    print("=== 模板渲染测试 ===\n")
    
    with app.test_client() as client:
        # 测试中文页面渲染
        print("1. 测试中文登录页面")
        response = client.get('/admin/login')
        print(f"   状态码: {response.status_code}")
        content = response.get_data(as_text=True)
        
        # 检查关键中文文本
        chinese_texts = ["管理员登录", "用户名", "密码", "果蔬客服AI系统后台管理"]
        for text in chinese_texts:
            if text in content:
                print(f"   [OK] 找到中文文本: {text}")
            else:
                print(f"   [MISS] 缺少中文文本: {text}")
        print()
        
        # 切换到英文后测试页面渲染
        print("2. 切换到英文并测试页面")
        # 先切换语言
        client.post('/api/language/en')
        
        # 再次访问登录页面
        response = client.get('/admin/login')
        print(f"   状态码: {response.status_code}")
        content = response.get_data(as_text=True)
        
        # 检查关键英文文本
        english_texts = ["Admin Login", "Username", "Password", "Fruit & Vegetable AI System Admin Panel"]
        for text in english_texts:
            if text in content:
                print(f"   [OK] 找到英文文本: {text}")
            else:
                print(f"   [MISS] 缺少英文文本: {text}")
        print()
        
        # 测试管理后台页面
        print("3. 测试英文管理后台页面")
        response = client.get('/admin/dashboard')
        print(f"   状态码: {response.status_code}")
        content = response.get_data(as_text=True)
        
        # 检查管理后台的英文文本
        admin_english_texts = ["Admin Panel", "Dashboard", "Inventory Management", "Product Entry"]
        for text in admin_english_texts:
            if text in content:
                print(f"   [OK] 找到英文文本: {text}")
            else:
                print(f"   [MISS] 缺少英文文本: {text}")
        print()

def test_session_persistence():
    """测试session持久性"""
    print("=== Session持久性测试 ===\n")
    
    with app.test_client() as client:
        # 设置语言
        print("1. 设置语言为英文")
        response = client.post('/api/language/en')
        data = response.get_json()
        print(f"   设置结果: {data.get('success')}")
        
        # 多次访问页面，检查语言是否保持
        print("2. 多次访问页面检查语言保持")
        for i in range(3):
            response = client.get('/api/language')
            data = response.get_json()
            current_lang = data.get('current_language', {}).get('code')
            print(f"   第{i+1}次访问 - 当前语言: {current_lang}")
        print()

def check_language_switcher_html():
    """检查语言切换器HTML"""
    print("=== 语言切换器HTML检查 ===\n")
    
    with app.test_client() as client:
        # 检查登录页面的语言切换器
        print("1. 检查登录页面语言切换器")
        response = client.get('/admin/login')
        content = response.get_data(as_text=True)
        
        if 'language-switcher' in content:
            print("   [OK] 找到语言切换器容器")
        else:
            print("   [MISS] 缺少语言切换器容器")
            
        if 'changeLanguage' in content:
            print("   [OK] 找到changeLanguage函数")
        else:
            print("   [MISS] 缺少changeLanguage函数")
        print()
        
        # 检查管理后台页面的语言切换器
        print("2. 检查管理后台语言切换器")
        response = client.get('/admin/dashboard')
        content = response.get_data(as_text=True)
        
        if 'languageSelect' in content:
            print("   [OK] 找到语言选择器")
        else:
            print("   [MISS] 缺少语言选择器")
            
        if 'onchange="changeLanguage' in content:
            print("   [OK] 找到语言切换事件")
        else:
            print("   [MISS] 缺少语言切换事件")
        print()

if __name__ == '__main__':
    try:
        test_language_api()
        print("\n" + "="*50 + "\n")
        test_template_rendering()
        print("\n" + "="*50 + "\n")
        test_session_persistence()
        print("\n" + "="*50 + "\n")
        check_language_switcher_html()
    except Exception as e:
        print(f"测试过程中出现错误: {e}")
        import traceback
        traceback.print_exc()
