#!/usr/bin/env python3
"""
语言切换功能测试脚本
"""
import requests
import json

def test_language_switch():
    """测试语言切换功能"""
    base_url = "http://localhost:5000"
    
    # 创建session以保持cookie
    session = requests.Session()
    
    print("[INFO] 测试语言切换功能...")
    print("=" * 50)
    
    # 1. 测试获取当前语言信息
    print("\n1. 获取当前语言信息:")
    try:
        response = session.get(f"{base_url}/api/language")
        if response.status_code == 200:
            data = response.json()
            print(f"   [OK] 成功: {data}")
        else:
            print(f"   [FAIL] 失败: {response.status_code}")
    except Exception as e:
        print(f"   [ERROR] 错误: {e}")
    
    # 2. 测试切换到英文
    print("\n2. 切换到英文:")
    try:
        response = session.post(f"{base_url}/api/language/en")
        if response.status_code == 200:
            data = response.json()
            print(f"   [OK] 成功: {data}")
        else:
            print(f"   [FAIL] 失败: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"   [ERROR] 错误: {e}")

    # 3. 验证语言是否切换成功
    print("\n3. 验证语言切换:")
    try:
        response = session.get(f"{base_url}/api/language")
        if response.status_code == 200:
            data = response.json()
            current_lang = data.get('current_language', {}).get('code', 'unknown')
            print(f"   当前语言: {current_lang}")
            if current_lang == 'en':
                print("   [OK] 语言切换成功!")
            else:
                print("   [FAIL] 语言切换失败!")
        else:
            print(f"   [FAIL] 失败: {response.status_code}")
    except Exception as e:
        print(f"   [ERROR] 错误: {e}")

    # 4. 测试切换回中文
    print("\n4. 切换回中文:")
    try:
        response = session.post(f"{base_url}/api/language/zh")
        if response.status_code == 200:
            data = response.json()
            print(f"   [OK] 成功: {data}")
        else:
            print(f"   [FAIL] 失败: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"   [ERROR] 错误: {e}")

    # 5. 测试访问登录页面
    print("\n5. 测试访问登录页面:")
    try:
        response = session.get(f"{base_url}/admin/login")
        if response.status_code == 200:
            print("   [OK] 登录页面访问成功")
            # 检查页面内容是否包含中文
            if "管理员登录" in response.text:
                print("   [OK] 页面显示中文内容")
            elif "Admin Login" in response.text:
                print("   [OK] 页面显示英文内容")
            else:
                print("   [FAIL] 页面内容异常")
        else:
            print(f"   [FAIL] 失败: {response.status_code}")
    except Exception as e:
        print(f"   [ERROR] 错误: {e}")
    
    print("\n" + "=" * 50)
    print("测试完成!")

if __name__ == "__main__":
    test_language_switch()
