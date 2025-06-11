#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
手动对比分析功能专项测试脚本
"""

import requests
import json
import sys

def test_manual_analysis():
    """测试手动对比分析功能"""
    base_url = "http://localhost:5000"
    session = requests.Session()
    
    print("手动对比分析功能测试")
    print("=" * 50)
    
    # 1. 管理员登录
    print("1. 管理员登录...")
    login_data = {"username": "admin", "password": "admin123"}
    response = session.post(f"{base_url}/api/admin/login", json=login_data)
    
    if response.status_code == 200 and response.json().get('success'):
        print("   OK 登录成功")
    else:
        print("   FAIL 登录失败")
        return False
    
    # 2. 获取已完成的盘点任务
    print("\n2. 获取已完成盘点任务...")
    response = session.get(f"{base_url}/api/admin/inventory/counts?status=completed")
    
    if response.status_code == 200:
        result = response.json()
        if result.get('success'):
            completed_counts = result.get('data', [])
            print(f"   OK 找到 {len(completed_counts)} 个已完成盘点任务")
            
            for count in completed_counts:
                print(f"   - {count['count_id']} ({count['count_date'][:10]})")
            
            if len(completed_counts) < 2:
                print("   WARN 盘点任务数量不足，无法进行对比测试")
                return False
        else:
            print(f"   FAIL API返回错误: {result.get('error')}")
            return False
    else:
        print(f"   FAIL 请求失败: {response.status_code}")
        return False
    
    # 3. 测试手动对比分析API
    print("\n3. 测试手动对比分析API...")
    
    # 选择前两个已完成的盘点任务
    current_count_id = completed_counts[0]['count_id']
    previous_count_id = completed_counts[1]['count_id']
    
    print(f"   当前盘点: {current_count_id}")
    print(f"   对比盘点: {previous_count_id}")
    
    comparison_data = {
        "current_count_id": current_count_id,
        "previous_count_id": previous_count_id,
        "comparison_type": "manual"
    }
    
    response = session.post(
        f"{base_url}/api/admin/inventory/comparisons",
        json=comparison_data
    )
    
    print(f"   请求状态码: {response.status_code}")
    print(f"   响应头: {dict(response.headers)}")
    
    if response.status_code == 200:
        try:
            result = response.json()
            print(f"   响应内容: {json.dumps(result, indent=2, ensure_ascii=False)}")
            
            if result.get('success'):
                print("   OK 手动对比分析创建成功")
                comparison_id = result.get('comparison_id')
                if comparison_id:
                    print(f"   对比分析ID: {comparison_id}")
                return True
            else:
                print(f"   FAIL API返回错误: {result.get('error')}")
                return False
        except json.JSONDecodeError as e:
            print(f"   FAIL JSON解析失败: {e}")
            print(f"   原始响应: {response.text}")
            return False
    else:
        print(f"   FAIL 请求失败: {response.status_code}")
        print(f"   响应内容: {response.text}")
        return False

def test_api_directly():
    """直接测试API接口"""
    print("\n" + "=" * 50)
    print("直接API测试")
    print("=" * 50)
    
    base_url = "http://localhost:5000"
    
    # 测试不同的API端点
    endpoints = [
        "/api/admin/inventory/counts",
        "/api/admin/inventory/counts?status=completed",
        "/api/admin/inventory/comparisons"
    ]
    
    for endpoint in endpoints:
        print(f"\n测试端点: {endpoint}")
        try:
            response = requests.get(f"{base_url}{endpoint}")
            print(f"状态码: {response.status_code}")
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    print(f"响应: {json.dumps(data, indent=2, ensure_ascii=False)[:200]}...")
                except:
                    print(f"响应: {response.text[:200]}...")
            else:
                print(f"错误响应: {response.text}")
        except Exception as e:
            print(f"请求异常: {e}")

def main():
    """主函数"""
    print("开始手动对比分析功能专项测试")
    
    # 测试手动对比功能
    success = test_manual_analysis()
    
    # 直接测试API
    test_api_directly()
    
    print("\n" + "=" * 50)
    if success:
        print("测试结果: 手动对比分析功能正常")
    else:
        print("测试结果: 手动对比分析功能存在问题")
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())
