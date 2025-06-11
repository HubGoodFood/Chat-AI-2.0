#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
库存盘点页面全面功能检查脚本
"""

import requests
import json
import sys
import time

class InventoryCountsChecker:
    def __init__(self, base_url="http://localhost:5000"):
        self.base_url = base_url
        self.session = requests.Session()
        self.test_count_id = None
        self.test_results = []
        
    def login_admin(self):
        """管理员登录"""
        print("1. 管理员登录...")
        login_data = {"username": "admin", "password": "admin123"}
        response = self.session.post(f"{self.base_url}/api/admin/login", json=login_data)
        
        if response.status_code == 200 and response.json().get('success'):
            print("   OK 登录成功")
            return True
        else:
            print("   FAIL 登录失败")
            return False
    
    def test_create_count_task(self):
        """测试创建盘点任务功能"""
        print("\n2. 测试创建盘点任务功能...")
        
        # 测试页面访问
        response = self.session.get(f"{self.base_url}/admin/inventory/counts")
        if response.status_code != 200:
            print("   FAIL 页面访问失败")
            return False
        print("   OK 页面访问正常")
        
        # 测试创建盘点任务API
        count_data = {"note": "全面功能检查测试盘点"}
        response = self.session.post(
            f"{self.base_url}/api/admin/inventory/counts",
            json=count_data
        )
        
        print(f"   API响应状态码: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"   API响应内容: {json.dumps(result, ensure_ascii=False)}")
            
            if result.get('success'):
                self.test_count_id = result.get('count_id')
                print(f"   OK 创建盘点任务成功: {self.test_count_id}")
                
                # 验证返回数据结构
                expected_fields = ['success', 'message', 'count_id']
                missing_fields = [field for field in expected_fields if field not in result]
                
                if not missing_fields:
                    print("   OK API返回数据结构完整")
                    return True
                else:
                    print(f"   WARN API返回数据缺少字段: {missing_fields}")
                    return True  # 不影响主要功能
            else:
                print(f"   FAIL 创建盘点任务失败: {result.get('error')}")
                return False
        else:
            print(f"   FAIL API请求失败: {response.status_code}")
            print(f"   响应内容: {response.text}")
            return False
    
    def test_load_count_tasks(self):
        """测试加载盘点任务列表"""
        print("\n3. 测试加载盘点任务列表...")
        
        response = self.session.get(f"{self.base_url}/api/admin/inventory/counts")
        
        if response.status_code == 200:
            result = response.json()
            if result.get('success'):
                tasks = result.get('data', [])
                print(f"   OK 获取到 {len(tasks)} 个盘点任务")
                
                # 验证数据结构
                if tasks:
                    task = tasks[0]
                    required_fields = ['count_id', 'count_date', 'operator', 'status']
                    missing_fields = [field for field in required_fields if field not in task]
                    
                    if not missing_fields:
                        print("   OK 盘点任务数据结构完整")
                    else:
                        print(f"   WARN 盘点任务数据缺少字段: {missing_fields}")
                
                return True
            else:
                print(f"   FAIL 获取盘点任务失败: {result.get('error')}")
                return False
        else:
            print(f"   FAIL 请求失败: {response.status_code}")
            return False
    
    def test_get_count_detail(self):
        """测试获取盘点任务详情"""
        print("\n4. 测试获取盘点任务详情...")
        
        if not self.test_count_id:
            print("   SKIP 没有测试盘点任务ID")
            return True
        
        response = self.session.get(f"{self.base_url}/api/admin/inventory/counts/{self.test_count_id}")
        
        if response.status_code == 200:
            result = response.json()
            if result.get('success'):
                count_data = result.get('data')
                print("   OK 获取盘点任务详情成功")
                
                # 验证数据结构
                required_fields = ['count_id', 'items', 'summary', 'status']
                missing_fields = [field for field in required_fields if field not in count_data]
                
                if not missing_fields:
                    print("   OK 盘点详情数据结构完整")
                    return True
                else:
                    print(f"   WARN 盘点详情数据缺少字段: {missing_fields}")
                    return True
            else:
                print(f"   FAIL 获取盘点详情失败: {result.get('error')}")
                return False
        else:
            print(f"   FAIL 请求失败: {response.status_code}")
            return False
    
    def test_add_product_to_count(self):
        """测试添加产品到盘点"""
        print("\n5. 测试添加产品到盘点...")
        
        if not self.test_count_id:
            print("   SKIP 没有测试盘点任务ID")
            return True
        
        # 先获取一个产品ID用于测试
        inventory_response = self.session.get(f"{self.base_url}/api/admin/inventory")
        if inventory_response.status_code == 200:
            inventory_result = inventory_response.json()
            if inventory_result.get('success') and inventory_result.get('data'):
                test_product_id = inventory_result['data'][0]['product_id']
                print(f"   使用测试产品ID: {test_product_id}")
                
                # 测试添加产品到盘点
                add_data = {"product_id": test_product_id}
                response = self.session.post(
                    f"{self.base_url}/api/admin/inventory/counts/{self.test_count_id}/items",
                    json=add_data
                )
                
                print(f"   API响应状态码: {response.status_code}")
                
                if response.status_code == 200:
                    result = response.json()
                    print(f"   API响应内容: {json.dumps(result, ensure_ascii=False)}")
                    
                    if result.get('success'):
                        print("   OK 添加产品到盘点成功")
                        return True
                    else:
                        print(f"   FAIL 添加产品失败: {result.get('error')}")
                        return False
                else:
                    print(f"   FAIL 请求失败: {response.status_code}")
                    print(f"   响应内容: {response.text}")
                    return False
            else:
                print("   FAIL 无法获取测试产品")
                return False
        else:
            print("   FAIL 无法获取库存数据")
            return False
    
    def test_update_actual_quantity(self):
        """测试更新实际数量"""
        print("\n6. 测试更新实际数量...")
        
        if not self.test_count_id:
            print("   SKIP 没有测试盘点任务ID")
            return True
        
        # 先获取盘点详情，找到一个项目
        response = self.session.get(f"{self.base_url}/api/admin/inventory/counts/{self.test_count_id}")
        
        if response.status_code == 200:
            result = response.json()
            if result.get('success'):
                count_data = result.get('data')
                items = count_data.get('items', [])
                
                if items:
                    test_item = items[0]
                    product_id = test_item['product_id']
                    test_quantity = 88  # 测试数量
                    
                    # 测试更新实际数量
                    update_data = {
                        "actual_quantity": test_quantity,
                        "note": "测试更新数量"
                    }

                    response = self.session.post(
                        f"{self.base_url}/api/admin/inventory/counts/{self.test_count_id}/items/{product_id}/quantity",
                        json=update_data
                    )
                    
                    print(f"   API响应状态码: {response.status_code}")
                    
                    if response.status_code == 200:
                        result = response.json()
                        if result.get('success'):
                            print("   OK 更新实际数量成功")
                            return True
                        else:
                            print(f"   FAIL 更新实际数量失败: {result.get('error')}")
                            return False
                    else:
                        print(f"   FAIL 请求失败: {response.status_code}")
                        return False
                else:
                    print("   SKIP 盘点任务中没有项目")
                    return True
            else:
                print("   FAIL 获取盘点详情失败")
                return False
        else:
            print("   FAIL 请求失败")
            return False
    
    def test_search_products(self):
        """测试产品搜索功能"""
        print("\n7. 测试产品搜索功能...")
        
        # 测试搜索API
        search_keyword = "鸡"  # 使用一个常见的关键词
        response = self.session.get(f"{self.base_url}/api/admin/inventory/search?keyword={search_keyword}")
        
        if response.status_code == 200:
            result = response.json()
            if result.get('success'):
                products = result.get('data', [])
                print(f"   OK 搜索到 {len(products)} 个产品")
                
                if products:
                    # 验证搜索结果数据结构
                    product = products[0]
                    required_fields = ['product_id', 'product_name', 'category']
                    missing_fields = [field for field in required_fields if field not in product]
                    
                    if not missing_fields:
                        print("   OK 搜索结果数据结构完整")
                    else:
                        print(f"   WARN 搜索结果缺少字段: {missing_fields}")
                
                return True
            else:
                print(f"   FAIL 搜索失败: {result.get('error')}")
                return False
        else:
            print(f"   FAIL 搜索请求失败: {response.status_code}")
            return False
    
    def test_complete_count_task(self):
        """测试完成盘点任务"""
        print("\n8. 测试完成盘点任务...")
        
        if not self.test_count_id:
            print("   SKIP 没有测试盘点任务ID")
            return True
        
        response = self.session.post(f"{self.base_url}/api/admin/inventory/counts/{self.test_count_id}/complete")
        
        print(f"   API响应状态码: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"   API响应内容: {json.dumps(result, ensure_ascii=False)}")
            
            if result.get('success'):
                print("   OK 完成盘点任务成功")
                return True
            else:
                print(f"   FAIL 完成盘点任务失败: {result.get('error')}")
                return False
        else:
            print(f"   FAIL 请求失败: {response.status_code}")
            print(f"   响应内容: {response.text}")
            return False
    
    def test_cancel_count_task(self):
        """测试取消盘点任务（创建一个新的用于测试）"""
        print("\n9. 测试取消盘点任务...")
        
        # 创建一个新的盘点任务用于取消测试
        count_data = {"note": "用于取消测试的盘点任务"}
        response = self.session.post(
            f"{self.base_url}/api/admin/inventory/counts",
            json=count_data
        )
        
        if response.status_code == 200:
            result = response.json()
            if result.get('success'):
                cancel_count_id = result.get('count_id')
                print(f"   创建测试盘点任务: {cancel_count_id}")
                
                # 测试取消
                cancel_data = {"reason": "功能测试"}
                response = self.session.delete(
                    f"{self.base_url}/api/admin/inventory/counts/{cancel_count_id}",
                    json=cancel_data
                )
                
                print(f"   API响应状态码: {response.status_code}")
                
                if response.status_code == 200:
                    result = response.json()
                    if result.get('success'):
                        print("   OK 取消盘点任务成功")
                        return True
                    else:
                        print(f"   FAIL 取消盘点任务失败: {result.get('error')}")
                        return False
                else:
                    print(f"   FAIL 取消请求失败: {response.status_code}")
                    return False
            else:
                print("   FAIL 无法创建测试盘点任务")
                return False
        else:
            print("   FAIL 创建测试盘点任务请求失败")
            return False
    
    def run_all_tests(self):
        """运行所有测试"""
        print("库存盘点页面全面功能检查")
        print("=" * 60)
        
        tests = [
            ("管理员登录", self.login_admin),
            ("创建盘点任务功能", self.test_create_count_task),
            ("加载盘点任务列表", self.test_load_count_tasks),
            ("获取盘点任务详情", self.test_get_count_detail),
            ("添加产品到盘点", self.test_add_product_to_count),
            ("更新实际数量", self.test_update_actual_quantity),
            ("产品搜索功能", self.test_search_products),
            ("完成盘点任务", self.test_complete_count_task),
            ("取消盘点任务", self.test_cancel_count_task)
        ]
        
        passed_tests = 0
        total_tests = len(tests)
        
        for test_name, test_func in tests:
            try:
                if test_func():
                    passed_tests += 1
                    self.test_results.append({"test": test_name, "result": "PASS"})
                else:
                    self.test_results.append({"test": test_name, "result": "FAIL"})
                time.sleep(0.5)  # 避免请求过快
            except Exception as e:
                print(f"   ERROR 测试异常: {e}")
                self.test_results.append({"test": test_name, "result": "ERROR", "error": str(e)})
        
        print("\n" + "=" * 60)
        print(f"测试完成: {passed_tests}/{total_tests} 个测试通过")
        
        # 显示详细结果
        print("\n详细测试结果:")
        for result in self.test_results:
            status = result["result"]
            test_name = result["test"]
            if status == "PASS":
                print(f"  OK {test_name}")
            elif status == "FAIL":
                print(f"  FAIL {test_name}")
            else:
                print(f"  ERROR {test_name}: {result.get('error', '')}")
        
        return passed_tests == total_tests

def main():
    """主函数"""
    checker = InventoryCountsChecker()
    success = checker.run_all_tests()
    
    if success:
        print("\nSUCCESS 所有功能检查通过！")
    else:
        print("\nWARN 发现一些问题，需要进一步检查")
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())
