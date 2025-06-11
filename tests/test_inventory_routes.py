#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
库存管理路由测试脚本
测试新添加的页面路由是否正常工作
"""

import requests
import sys
import time

def test_routes():
    """测试所有库存管理相关的路由"""
    base_url = "http://localhost:5000"

    # 测试路由列表
    routes_to_test = [
        "/admin/login",
        "/admin/dashboard",
        "/admin/inventory/products/add",
        "/admin/inventory/counts",
        "/admin/inventory/analysis"
    ]

    print("开始测试库存管理路由...")
    print("=" * 50)
    
    success_count = 0
    total_count = len(routes_to_test)
    
    for route in routes_to_test:
        try:
            url = base_url + route
            print(f"测试路由: {route}")
            
            response = requests.get(url, timeout=5)
            
            if response.status_code == 200:
                print(f"OK {route} - 状态码: {response.status_code}")

                # 检查响应内容是否包含预期的HTML元素
                content = response.text
                if "管理员控制台" in content and "库存管理" in content:
                    print(f"OK {route} - 内容验证通过")
                    success_count += 1
                else:
                    print(f"FAIL {route} - 内容验证失败")
            else:
                print(f"FAIL {route} - 状态码: {response.status_code}")
                
        except requests.exceptions.RequestException as e:
            print(f"FAIL {route} - 请求失败: {e}")

        print("-" * 30)
        time.sleep(0.5)  # 避免请求过快

    print("=" * 50)
    print(f"测试完成: {success_count}/{total_count} 个路由通过测试")

    if success_count == total_count:
        print("所有路由测试通过！")
        return True
    else:
        print("部分路由测试失败，请检查系统配置")
        return False

def test_api_endpoints():
    """测试API接口是否正常"""
    base_url = "http://localhost:5000"
    
    # 测试API接口（不需要认证的）
    api_endpoints = [
        "/api/admin/status",
    ]
    
    print("\n开始测试API接口...")
    print("=" * 50)

    for endpoint in api_endpoints:
        try:
            url = base_url + endpoint
            print(f"测试API: {endpoint}")

            response = requests.get(url, timeout=5)

            if response.status_code == 200:
                print(f"OK {endpoint} - 状态码: {response.status_code}")

                # 尝试解析JSON响应
                try:
                    json_data = response.json()
                    print(f"OK {endpoint} - JSON响应正常")
                except:
                    print(f"FAIL {endpoint} - JSON解析失败")
            else:
                print(f"FAIL {endpoint} - 状态码: {response.status_code}")

        except requests.exceptions.RequestException as e:
            print(f"FAIL {endpoint} - 请求失败: {e}")

        print("-" * 30)

def main():
    """主函数"""
    print("库存管理系统路由测试")
    print("确保系统已启动在 http://localhost:5000")
    print()

    # 测试页面路由
    routes_ok = test_routes()

    # 测试API接口
    test_api_endpoints()

    print("\n测试总结:")
    if routes_ok:
        print("OK 页面路由功能正常")
        print("OK 可以访问以下页面:")
        print("   - http://localhost:5000/admin/inventory/products/add")
        print("   - http://localhost:5000/admin/inventory/counts")
        print("   - http://localhost:5000/admin/inventory/analysis")
    else:
        print("FAIL 部分功能存在问题，需要进一步检查")

    print("\n下一步:")
    print("1. 在浏览器中访问 http://localhost:5000/admin/login")
    print("2. 使用账户 admin / admin123 登录")
    print("3. 测试库存管理功能")

if __name__ == "__main__":
    main()
