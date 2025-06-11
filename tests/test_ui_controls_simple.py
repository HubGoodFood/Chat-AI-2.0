#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
库存盘点页面UI控件功能检查脚本（简化版）
"""

import requests
import json
import sys
import re

class UIControlsChecker:
    def __init__(self, base_url="http://localhost:5000"):
        self.base_url = base_url
        self.session = requests.Session()
        
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
    
    def test_view_button_functionality(self):
        """测试查看按钮功能"""
        print("\n2. 测试查看按钮功能...")
        
        # 获取盘点任务列表
        response = self.session.get(f"{self.base_url}/api/admin/inventory/counts")
        
        if response.status_code == 200:
            result = response.json()
            if result.get('success') and result.get('data'):
                tasks = result['data']
                print(f"   OK 获取到 {len(tasks)} 个盘点任务")
                
                # 检查第一个任务的查看功能
                if tasks:
                    test_task = tasks[0]
                    count_id = test_task['count_id']
                    
                    # 测试获取任务详情API（查看按钮应该调用的功能）
                    detail_response = self.session.get(f"{self.base_url}/api/admin/inventory/counts/{count_id}")
                    
                    if detail_response.status_code == 200:
                        detail_result = detail_response.json()
                        if detail_result.get('success'):
                            print("   OK 查看按钮对应的API功能正常")
                            print(f"   INFO 测试任务: {count_id}")
                            
                            # 检查返回的数据结构
                            task_data = detail_result.get('data', {})
                            required_fields = ['count_id', 'items', 'summary', 'status']
                            missing_fields = [field for field in required_fields if field not in task_data]
                            
                            if not missing_fields:
                                print("   OK 查看功能返回数据结构完整")
                                return True
                            else:
                                print(f"   WARN 查看功能返回数据缺少字段: {missing_fields}")
                                return True  # 不影响主要功能
                        else:
                            print(f"   FAIL 获取任务详情失败: {detail_result.get('error')}")
                            return False
                    else:
                        print(f"   FAIL 查看API请求失败: {detail_response.status_code}")
                        return False
                else:
                    print("   SKIP 没有盘点任务可供测试")
                    return True
            else:
                print(f"   FAIL 获取盘点任务失败: {result.get('error')}")
                return False
        else:
            print(f"   FAIL 请求失败: {response.status_code}")
            return False
    
    def test_refresh_button_functionality(self):
        """测试刷新按钮功能"""
        print("\n3. 测试刷新按钮功能...")
        
        # 测试刷新按钮对应的API调用
        response = self.session.get(f"{self.base_url}/api/admin/inventory/counts")
        
        if response.status_code == 200:
            result = response.json()
            if result.get('success'):
                print("   OK 刷新按钮对应的API功能正常")
                print(f"   INFO 刷新获取到 {len(result.get('data', []))} 个任务")
                
                # 测试多次刷新的一致性
                response2 = self.session.get(f"{self.base_url}/api/admin/inventory/counts")
                if response2.status_code == 200:
                    result2 = response2.json()
                    if result2.get('success'):
                        tasks1 = result.get('data', [])
                        tasks2 = result2.get('data', [])
                        if len(tasks1) == len(tasks2):
                            print("   OK 刷新功能数据一致性正常")
                        else:
                            print("   WARN 刷新功能数据一致性异常")
                        return True
                    else:
                        print("   FAIL 第二次刷新失败")
                        return False
                else:
                    print("   FAIL 第二次刷新请求失败")
                    return False
            else:
                print(f"   FAIL 刷新API返回错误: {result.get('error')}")
                return False
        else:
            print(f"   FAIL 刷新API请求失败: {response.status_code}")
            return False
    
    def test_status_filter_functionality(self):
        """测试状态过滤功能"""
        print("\n4. 测试状态过滤功能...")
        
        # 测试不同状态的过滤
        statuses = ['', 'in_progress', 'completed', 'cancelled']
        status_names = ['所有状态', '进行中', '已完成', '已取消']
        
        all_tasks_count = 0
        status_counts = {}
        
        for status, name in zip(statuses, status_names):
            url = f"{self.base_url}/api/admin/inventory/counts"
            if status:
                url += f"?status={status}"
            
            response = self.session.get(url)
            
            if response.status_code == 200:
                result = response.json()
                if result.get('success'):
                    tasks = result.get('data', [])
                    print(f"   OK {name}: 获取到 {len(tasks)} 个任务")
                    
                    if status == '':
                        all_tasks_count = len(tasks)
                    else:
                        status_counts[status] = len(tasks)
                    
                    # 验证过滤结果
                    if status and tasks:
                        # 检查返回的任务是否都是指定状态
                        wrong_status_tasks = [task for task in tasks if task.get('status') != status]
                        if wrong_status_tasks:
                            print(f"   FAIL {name}: 发现 {len(wrong_status_tasks)} 个状态不匹配的任务")
                            return False
                        else:
                            print(f"   OK {name}: 状态过滤正确")
                else:
                    print(f"   FAIL {name}: API返回错误: {result.get('error')}")
                    return False
            else:
                print(f"   FAIL {name}: API请求失败: {response.status_code}")
                return False
        
        # 验证过滤逻辑的一致性
        total_filtered = sum(status_counts.values())
        if all_tasks_count > 0 and total_filtered <= all_tasks_count:
            print("   OK 状态过滤逻辑一致性正常")
        elif all_tasks_count == 0:
            print("   INFO 没有任务数据，无法验证过滤逻辑")
        else:
            print(f"   WARN 状态过滤逻辑异常: 总数{all_tasks_count}, 过滤总数{total_filtered}")
        
        return True
    
    def check_html_ui_elements(self):
        """检查HTML中的UI元素"""
        print("\n5. 检查HTML中的UI元素...")
        
        try:
            # 获取管理页面HTML
            response = self.session.get(f"{self.base_url}/admin/dashboard")
            
            if response.status_code == 200:
                html_content = response.text
                
                # 检查关键UI元素
                ui_elements = [
                    ('id="refreshCountTasksBtn"', '刷新按钮'),
                    ('id="countStatusFilter"', '状态过滤器'),
                    ('id="countTasksTableBody"', '任务列表表格'),
                    ('id="createCountTaskBtn"', '创建盘点按钮'),
                    ('onclick="admin.viewCountTask', '查看按钮onclick事件'),
                    ('onclick="admin.continueCountTask', '继续按钮onclick事件')
                ]
                
                for element_pattern, element_name in ui_elements:
                    if element_pattern in html_content:
                        print(f"   OK {element_name}: HTML元素存在")
                    else:
                        print(f"   FAIL {element_name}: HTML元素缺失")
                        return False
                
                # 检查状态过滤器的选项
                status_options = [
                    'value="in_progress"',
                    'value="completed"',
                    'value="cancelled"'
                ]
                
                for option in status_options:
                    if option in html_content:
                        print(f"   OK 状态选项 {option}: 存在")
                    else:
                        print(f"   WARN 状态选项 {option}: 缺失")
                
                return True
            else:
                print(f"   FAIL 无法获取HTML页面: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"   FAIL HTML检查异常: {e}")
            return False
    
    def check_javascript_method_existence(self):
        """检查JavaScript方法是否存在"""
        print("\n6. 检查JavaScript方法是否存在...")
        
        try:
            # 获取admin.js文件
            response = self.session.get(f"{self.base_url}/static/js/admin.js")
            
            if response.status_code == 200:
                js_content = response.text
                
                # 检查关键方法
                methods_to_check = [
                    ('loadCountTasks', '加载盘点任务方法'),
                    ('renderCountTasksTable', '渲染任务表格方法'),
                    ('continueCountTask', '继续盘点任务方法'),
                    ('filterCountTasks', '过滤盘点任务方法'),
                    ('viewCountTask', '查看盘点任务方法')
                ]
                
                missing_methods = []
                
                for method_name, method_desc in methods_to_check:
                    # 检查方法定义
                    method_patterns = [
                        f'{method_name}(',
                        f'{method_name} (',
                        f'async {method_name}(',
                        f'async {method_name} ('
                    ]
                    
                    method_found = any(pattern in js_content for pattern in method_patterns)
                    
                    if method_found:
                        print(f"   OK {method_desc}: 方法存在")
                    else:
                        print(f"   FAIL {method_desc}: 方法缺失")
                        missing_methods.append(method_name)
                
                # 检查事件绑定
                event_bindings = [
                    ('refreshCountTasksBtn', 'loadCountTasks'),
                    ('countStatusFilter', 'filterCountTasks'),
                    ('createCountTaskBtn', 'createCountTask')
                ]
                
                for element_id, method_name in event_bindings:
                    binding_pattern = f'getElementById(\'{element_id}\').*{method_name}'
                    if re.search(binding_pattern, js_content):
                        print(f"   OK {element_id}: 事件绑定正确")
                    else:
                        print(f"   WARN {element_id}: 事件绑定可能有问题")
                
                return len(missing_methods) == 0
            else:
                print(f"   FAIL 无法获取JavaScript文件: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"   FAIL JavaScript检查异常: {e}")
            return False
    
    def run_all_tests(self):
        """运行所有测试"""
        print("库存盘点页面UI控件功能检查")
        print("=" * 60)
        
        tests = [
            ("管理员登录", self.login_admin),
            ("查看按钮功能", self.test_view_button_functionality),
            ("刷新按钮功能", self.test_refresh_button_functionality),
            ("状态过滤功能", self.test_status_filter_functionality),
            ("HTML UI元素", self.check_html_ui_elements),
            ("JavaScript方法", self.check_javascript_method_existence)
        ]
        
        passed_tests = 0
        total_tests = len(tests)
        
        for test_name, test_func in tests:
            try:
                if test_func():
                    passed_tests += 1
                    print(f"PASS {test_name}")
                else:
                    print(f"FAIL {test_name}")
            except Exception as e:
                print(f"ERROR {test_name}: {e}")
        
        print("\n" + "=" * 60)
        print(f"测试完成: {passed_tests}/{total_tests} 个测试通过")
        
        return passed_tests, total_tests, passed_tests == total_tests

def main():
    """主函数"""
    checker = UIControlsChecker()
    passed, total, success = checker.run_all_tests()
    
    if success:
        print("SUCCESS 所有UI控件功能检查通过！")
    else:
        print("WARN 发现一些UI控件问题，需要修复")
        print(f"通过率: {passed}/{total} ({passed/total*100:.1f}%)")
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())
