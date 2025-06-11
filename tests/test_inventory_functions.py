#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
库存管理功能完整性测试脚本
测试三个页面的所有功能是否正常工作
"""

import requests
import json
import time
import sys

class InventoryFunctionTester:
    def __init__(self, base_url="http://localhost:5000"):
        self.base_url = base_url
        self.session = requests.Session()
        self.admin_token = None
        
    def login_admin(self):
        """管理员登录"""
        print("1. 测试管理员登录...")
        
        login_data = {
            "username": "admin",
            "password": "admin123"
        }
        
        response = self.session.post(
            f"{self.base_url}/api/admin/login",
            json=login_data
        )
        
        if response.status_code == 200:
            result = response.json()
            if result.get('success'):
                print("   OK 管理员登录成功")
                return True
            else:
                print(f"   FAIL 登录失败: {result.get('error')}")
                return False
        else:
            print(f"   FAIL 登录请求失败: {response.status_code}")
            return False
    
    def test_product_add_page(self):
        """测试产品入库页面功能"""
        print("\n2. 测试产品入库页面功能...")
        
        # 测试页面访问
        response = self.session.get(f"{self.base_url}/admin/inventory/products/add")
        if response.status_code == 200:
            print("   OK 产品入库页面访问正常")
        else:
            print(f"   FAIL 页面访问失败: {response.status_code}")
            return False
        
        # 测试添加产品API
        test_product = {
            "product_name": "测试产品_功能验证",
            "category": "测试分类",
            "price": "10元/个",
            "unit": "个",
            "specification": "测试规格",
            "storage_area": "A",
            "initial_stock": 50,
            "min_stock_warning": 5,
            "description": "功能测试用产品"
        }
        
        response = self.session.post(
            f"{self.base_url}/api/admin/inventory",
            json=test_product
        )
        
        if response.status_code == 200:
            result = response.json()
            if result.get('success'):
                print("   OK 产品添加API正常工作")
                self.test_product_id = result.get('product_id')
                return True
            else:
                print(f"   FAIL 产品添加失败: {result.get('error')}")
                return False
        else:
            print(f"   FAIL 产品添加请求失败: {response.status_code}")
            return False
    
    def test_inventory_counts_page(self):
        """测试库存盘点页面功能"""
        print("\n3. 测试库存盘点页面功能...")
        
        # 测试页面访问
        response = self.session.get(f"{self.base_url}/admin/inventory/counts")
        if response.status_code == 200:
            print("   OK 库存盘点页面访问正常")
        else:
            print(f"   FAIL 页面访问失败: {response.status_code}")
            return False
        
        # 测试创建盘点任务
        count_data = {
            "note": "功能测试盘点任务"
        }
        
        response = self.session.post(
            f"{self.base_url}/api/admin/inventory/counts",
            json=count_data
        )
        
        if response.status_code == 200:
            result = response.json()
            if result.get('success'):
                print("   OK 创建盘点任务API正常工作")
                self.test_count_id = result.get('count_id')
                
                # 测试添加产品到盘点
                if hasattr(self, 'test_product_id'):
                    add_item_data = {
                        "product_id": self.test_product_id
                    }
                    
                    response = self.session.post(
                        f"{self.base_url}/api/admin/inventory/counts/{self.test_count_id}/items",
                        json=add_item_data
                    )
                    
                    if response.status_code == 200:
                        result = response.json()
                        if result.get('success'):
                            print("   OK 添加产品到盘点API正常工作")
                        else:
                            print(f"   FAIL 添加产品到盘点失败: {result.get('error')}")
                    else:
                        print(f"   FAIL 添加产品到盘点请求失败: {response.status_code}")
                
                return True
            else:
                print(f"   FAIL 创建盘点任务失败: {result.get('error')}")
                return False
        else:
            print(f"   FAIL 创建盘点任务请求失败: {response.status_code}")
            return False
    
    def test_inventory_analysis_page(self):
        """测试数据对比分析页面功能"""
        print("\n4. 测试数据对比分析页面功能...")
        
        # 测试页面访问
        response = self.session.get(f"{self.base_url}/admin/inventory/analysis")
        if response.status_code == 200:
            print("   OK 数据对比分析页面访问正常")
        else:
            print(f"   FAIL 页面访问失败: {response.status_code}")
            return False
        
        # 测试获取已完成盘点任务
        response = self.session.get(f"{self.base_url}/api/admin/inventory/counts?status=completed")
        if response.status_code == 200:
            result = response.json()
            if result.get('success'):
                print("   OK 获取已完成盘点任务API正常工作")
                completed_counts = result.get('data', [])
                
                if len(completed_counts) >= 2:
                    # 测试创建手动对比分析
                    comparison_data = {
                        "current_count_id": completed_counts[0]['count_id'],
                        "previous_count_id": completed_counts[1]['count_id']
                    }
                    
                    response = self.session.post(
                        f"{self.base_url}/api/admin/inventory/comparisons",
                        json=comparison_data
                    )
                    
                    if response.status_code == 200:
                        result = response.json()
                        if result.get('success'):
                            print("   OK 创建手动对比分析API正常工作")
                        else:
                            print(f"   WARN 创建手动对比分析失败: {result.get('error')}")
                    else:
                        print(f"   WARN 创建手动对比分析请求失败: {response.status_code}")
                else:
                    print("   WARN 没有足够的已完成盘点任务进行对比分析测试")
                
                return True
            else:
                print(f"   FAIL 获取已完成盘点任务失败: {result.get('error')}")
                return False
        else:
            print(f"   FAIL 获取已完成盘点任务请求失败: {response.status_code}")
            return False
    
    def test_api_endpoints(self):
        """测试关键API接口"""
        print("\n5. 测试关键API接口...")
        
        api_tests = [
            ("/api/admin/inventory", "库存列表API"),
            ("/api/admin/inventory/summary", "库存汇总API"),
            ("/api/admin/inventory/storage-areas", "存储区域API"),
            ("/api/admin/inventory/counts", "盘点任务列表API"),
        ]
        
        success_count = 0
        for endpoint, name in api_tests:
            response = self.session.get(f"{self.base_url}{endpoint}")
            if response.status_code == 200:
                result = response.json()
                if result.get('success'):
                    print(f"   OK {name}正常工作")
                    success_count += 1
                else:
                    print(f"   FAIL {name}返回错误: {result.get('error')}")
            else:
                print(f"   FAIL {name}请求失败: {response.status_code}")
        
        print(f"   API测试结果: {success_count}/{len(api_tests)} 个接口正常")
        return success_count == len(api_tests)
    
    def cleanup_test_data(self):
        """清理测试数据"""
        print("\n6. 清理测试数据...")
        
        # 取消测试盘点任务
        if hasattr(self, 'test_count_id'):
            response = self.session.delete(
                f"{self.base_url}/api/admin/inventory/counts/{self.test_count_id}",
                json={"reason": "功能测试完成"}
            )
            if response.status_code == 200:
                print("   OK 测试盘点任务已清理")
        
        # 删除测试产品
        if hasattr(self, 'test_product_id'):
            response = self.session.delete(
                f"{self.base_url}/api/admin/inventory/{self.test_product_id}"
            )
            if response.status_code == 200:
                print("   OK 测试产品已清理")
    
    def run_all_tests(self):
        """运行所有测试"""
        print("开始库存管理功能完整性测试")
        print("=" * 60)
        
        # 登录
        if not self.login_admin():
            print("\nFAIL 测试失败：无法登录管理员账户")
            return False
        
        # 测试各个页面功能
        tests = [
            self.test_product_add_page,
            self.test_inventory_counts_page,
            self.test_inventory_analysis_page,
            self.test_api_endpoints
        ]
        
        passed_tests = 0
        for test in tests:
            try:
                if test():
                    passed_tests += 1
                time.sleep(1)  # 避免请求过快
            except Exception as e:
                print(f"   FAIL 测试异常: {e}")
        
        # 清理测试数据
        self.cleanup_test_data()
        
        # 测试结果
        print("\n" + "=" * 60)
        print(f"测试完成: {passed_tests}/{len(tests)} 个功能模块通过测试")
        
        if passed_tests == len(tests):
            print("所有功能测试通过！库存管理系统工作正常")
            return True
        else:
            print("部分功能存在问题，请检查上述错误信息")
            return False

def main():
    """主函数"""
    print("库存管理功能完整性测试")
    print("确保系统已启动在 http://localhost:5000")
    
    tester = InventoryFunctionTester()
    success = tester.run_all_tests()
    
    if success:
        print("\nOK 所有功能正常，可以开始使用库存管理系统")
    else:
        print("\nFAIL 发现问题，需要进一步检查和修复")
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())
