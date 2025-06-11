#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据对比分析功能修复验证脚本
"""

import requests
import json
import sys

def test_analysis_workflow():
    """测试完整的分析工作流程"""
    base_url = "http://localhost:5000"
    session = requests.Session()
    
    print("数据对比分析功能修复验证")
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
            
            if len(completed_counts) < 2:
                print("   WARN 盘点任务数量不足，无法进行对比测试")
                return False
        else:
            print(f"   FAIL API返回错误: {result.get('error')}")
            return False
    else:
        print(f"   FAIL 请求失败: {response.status_code}")
        return False
    
    # 3. 测试手动对比分析完整流程
    print("\n3. 测试手动对比分析完整流程...")
    
    current_count_id = completed_counts[0]['count_id']
    previous_count_id = completed_counts[1]['count_id']
    
    print(f"   当前盘点: {current_count_id}")
    print(f"   对比盘点: {previous_count_id}")
    
    # 3.1 创建对比分析
    comparison_data = {
        "current_count_id": current_count_id,
        "previous_count_id": previous_count_id,
        "comparison_type": "manual"
    }
    
    response = session.post(
        f"{base_url}/api/admin/inventory/comparisons",
        json=comparison_data
    )
    
    if response.status_code == 200:
        result = response.json()
        if result.get('success'):
            comparison_id = result.get('comparison_id')
            print(f"   OK 对比分析创建成功: {comparison_id}")
            
            # 3.2 获取分析详情
            print("   正在获取分析详情...")
            detail_response = session.get(f"{base_url}/api/admin/inventory/comparisons/{comparison_id}")
            
            if detail_response.status_code == 200:
                detail_result = detail_response.json()
                if detail_result.get('success'):
                    analysis_data = detail_result.get('data')
                    print("   OK 分析详情获取成功")
                    
                    # 验证分析数据结构
                    required_fields = ['comparison_id', 'changes', 'statistics', 'anomalies']
                    missing_fields = [field for field in required_fields if field not in analysis_data]
                    
                    if not missing_fields:
                        print("   OK 分析数据结构完整")
                        
                        # 显示统计信息
                        stats = analysis_data['statistics']
                        print(f"   STATS 统计信息:")
                        print(f"      - 总产品数: {stats.get('total_products', 0)}")
                        print(f"      - 变化产品数: {stats.get('changed_products', 0)}")
                        print(f"      - 异常项目数: {len(analysis_data.get('anomalies', []))}")
                        
                        return True
                    else:
                        print(f"   FAIL 分析数据缺少字段: {missing_fields}")
                        return False
                else:
                    print(f"   FAIL 获取分析详情失败: {detail_result.get('error')}")
                    return False
            else:
                print(f"   FAIL 获取分析详情请求失败: {detail_response.status_code}")
                return False
        else:
            print(f"   FAIL 创建对比分析失败: {result.get('error')}")
            return False
    else:
        print(f"   FAIL 创建对比分析请求失败: {response.status_code}")
        return False

def test_weekly_analysis():
    """测试周对比分析"""
    base_url = "http://localhost:5000"
    session = requests.Session()
    
    print("\n4. 测试周对比分析...")
    
    # 登录
    login_data = {"username": "admin", "password": "admin123"}
    session.post(f"{base_url}/api/admin/login", json=login_data)
    
    # 创建周对比分析
    response = session.post(f"{base_url}/api/admin/inventory/comparisons/weekly")
    
    if response.status_code == 200:
        result = response.json()
        if result.get('success'):
            comparison_id = result.get('comparison_id')
            print(f"   OK 周对比分析创建成功: {comparison_id}")
            
            # 获取分析详情
            detail_response = session.get(f"{base_url}/api/admin/inventory/comparisons/{comparison_id}")
            
            if detail_response.status_code == 200:
                detail_result = detail_response.json()
                if detail_result.get('success'):
                    print("   OK 周对比分析详情获取成功")
                    return True
                else:
                    print(f"   FAIL 获取周对比分析详情失败: {detail_result.get('error')}")
                    return False
            else:
                print(f"   FAIL 获取周对比分析详情请求失败: {detail_response.status_code}")
                return False
        else:
            print(f"   FAIL 创建周对比分析失败: {result.get('error')}")
            return False
    else:
        print(f"   FAIL 创建周对比分析请求失败: {response.status_code}")
        return False

def test_frontend_simulation():
    """模拟前端JavaScript的调用流程"""
    print("\n5. 模拟前端JavaScript调用流程...")
    
    base_url = "http://localhost:5000"
    session = requests.Session()
    
    # 登录
    login_data = {"username": "admin", "password": "admin123"}
    session.post(f"{base_url}/api/admin/login", json=login_data)
    
    # 模拟loadCompletedCountTasks
    print("   模拟 loadCompletedCountTasks()...")
    response = session.get(f"{base_url}/api/admin/inventory/counts?status=completed")
    if response.status_code == 200 and response.json().get('success'):
        print("   OK 已完成盘点任务加载成功")
    else:
        print("   FAIL 已完成盘点任务加载失败")
        return False
    
    # 模拟createManualAnalysis的两步调用
    print("   模拟 createManualAnalysis() 两步调用...")
    
    completed_counts = response.json()['data']
    if len(completed_counts) >= 2:
        # 第一步：创建对比分析
        comparison_data = {
            "current_count_id": completed_counts[0]['count_id'],
            "previous_count_id": completed_counts[1]['count_id'],
            "comparison_type": "manual"
        }
        
        step1_response = session.post(
            f"{base_url}/api/admin/inventory/comparisons",
            json=comparison_data
        )
        
        if step1_response.status_code == 200:
            step1_result = step1_response.json()
            if step1_result.get('success'):
                comparison_id = step1_result.get('comparison_id')
                print(f"   OK 第一步：创建对比分析成功 ({comparison_id})")
                
                # 第二步：获取分析详情
                step2_response = session.get(f"{base_url}/api/admin/inventory/comparisons/{comparison_id}")
                
                if step2_response.status_code == 200:
                    step2_result = step2_response.json()
                    if step2_result.get('success'):
                        print("   OK 第二步：获取分析详情成功")
                        print("   OK 前端JavaScript调用流程模拟成功")
                        return True
                    else:
                        print(f"   FAIL 第二步失败: {step2_result.get('error')}")
                        return False
                else:
                    print(f"   FAIL 第二步请求失败: {step2_response.status_code}")
                    return False
            else:
                print(f"   FAIL 第一步失败: {step1_result.get('error')}")
                return False
        else:
            print(f"   FAIL 第一步请求失败: {step1_response.status_code}")
            return False
    else:
        print("   FAIL 盘点任务数量不足")
        return False

def main():
    """主函数"""
    print("开始数据对比分析功能修复验证")
    
    tests = [
        ("手动对比分析完整流程", test_analysis_workflow),
        ("周对比分析", test_weekly_analysis),
        ("前端JavaScript调用流程", test_frontend_simulation)
    ]
    
    passed_tests = 0
    total_tests = len(tests)
    
    for test_name, test_func in tests:
        try:
            if test_func():
                passed_tests += 1
                print(f"OK {test_name} - 通过")
            else:
                print(f"FAIL {test_name} - 失败")
        except Exception as e:
            print(f"FAIL {test_name} - 异常: {e}")
    
    print("\n" + "=" * 50)
    print(f"测试结果: {passed_tests}/{total_tests} 个测试通过")
    
    if passed_tests == total_tests:
        print("SUCCESS 所有测试通过！手动对比分析功能已修复")
        print("\nOK 修复内容:")
        print("   - 修复了createManualAnalysis方法的两步调用流程")
        print("   - 修复了createWeeklyAnalysis方法的数据获取")
        print("   - 确保showAnalysisResults能正确显示分析结果")
        return True
    else:
        print("WARN 部分测试失败，需要进一步检查")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
