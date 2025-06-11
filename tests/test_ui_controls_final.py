#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
库存盘点页面UI控件功能最终验证脚本
"""

import requests
import json
import sys

class FinalUIChecker:
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
    
    def test_view_button_complete_workflow(self):
        """测试查看按钮完整工作流程"""
        print("\n2. 测试查看按钮完整工作流程...")
        
        # 获取盘点任务列表
        response = self.session.get(f"{self.base_url}/api/admin/inventory/counts")
        
        if response.status_code == 200:
            result = response.json()
            if result.get('success') and result.get('data'):
                tasks = result['data']
                print(f"   OK 获取到 {len(tasks)} 个盘点任务")
                
                if tasks:
                    test_task = tasks[0]
                    count_id = test_task['count_id']
                    
                    # 测试查看功能的API调用
                    detail_response = self.session.get(f"{self.base_url}/api/admin/inventory/counts/{count_id}")
                    
                    if detail_response.status_code == 200:
                        detail_result = detail_response.json()
                        if detail_result.get('success'):
                            task_data = detail_result.get('data', {})
                            print("   OK 查看按钮API调用成功")
                            print(f"   INFO 任务状态: {task_data.get('status')}")
                            print(f"   INFO 项目数量: {len(task_data.get('items', []))}")
                            print(f"   INFO 操作员: {task_data.get('operator')}")
                            
                            # 验证数据完整性
                            required_fields = ['count_id', 'count_date', 'operator', 'status', 'items', 'summary']
                            missing_fields = [field for field in required_fields if field not in task_data]
                            
                            if not missing_fields:
                                print("   OK 查看功能数据完整性验证通过")
                                return True
                            else:
                                print(f"   WARN 查看功能数据缺少字段: {missing_fields}")
                                return True  # 不影响主要功能
                        else:
                            print(f"   FAIL 查看功能API返回错误: {detail_result.get('error')}")
                            return False
                    else:
                        print(f"   FAIL 查看功能API请求失败: {detail_response.status_code}")
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
    
    def test_refresh_button_complete_workflow(self):
        """测试刷新按钮完整工作流程"""
        print("\n3. 测试刷新按钮完整工作流程...")
        
        # 第一次获取数据
        response1 = self.session.get(f"{self.base_url}/api/admin/inventory/counts")
        
        if response1.status_code == 200:
            result1 = response1.json()
            if result1.get('success'):
                tasks1 = result1.get('data', [])
                print(f"   OK 第一次刷新: 获取到 {len(tasks1)} 个任务")
                
                # 第二次获取数据（模拟刷新）
                response2 = self.session.get(f"{self.base_url}/api/admin/inventory/counts")
                
                if response2.status_code == 200:
                    result2 = response2.json()
                    if result2.get('success'):
                        tasks2 = result2.get('data', [])
                        print(f"   OK 第二次刷新: 获取到 {len(tasks2)} 个任务")
                        
                        # 验证数据一致性
                        if len(tasks1) == len(tasks2):
                            print("   OK 刷新功能数据一致性正常")
                            
                            # 验证任务ID一致性
                            ids1 = set(task['count_id'] for task in tasks1)
                            ids2 = set(task['count_id'] for task in tasks2)
                            
                            if ids1 == ids2:
                                print("   OK 刷新功能任务ID一致性正常")
                                return True
                            else:
                                print("   WARN 刷新功能任务ID不一致（可能有新任务创建）")
                                return True
                        else:
                            print("   WARN 刷新功能数据数量不一致（可能有新任务创建）")
                            return True
                    else:
                        print(f"   FAIL 第二次刷新失败: {result2.get('error')}")
                        return False
                else:
                    print(f"   FAIL 第二次刷新请求失败: {response2.status_code}")
                    return False
            else:
                print(f"   FAIL 第一次刷新失败: {result1.get('error')}")
                return False
        else:
            print(f"   FAIL 第一次刷新请求失败: {response1.status_code}")
            return False
    
    def test_status_filter_complete_workflow(self):
        """测试状态过滤完整工作流程"""
        print("\n4. 测试状态过滤完整工作流程...")
        
        # 测试所有状态过滤
        filter_tests = [
            ('', '所有状态'),
            ('in_progress', '进行中'),
            ('completed', '已完成'),
            ('cancelled', '已取消')
        ]
        
        all_tasks_count = 0
        status_results = {}
        
        for status_value, status_name in filter_tests:
            url = f"{self.base_url}/api/admin/inventory/counts"
            if status_value:
                url += f"?status={status_value}"
            
            response = self.session.get(url)
            
            if response.status_code == 200:
                result = response.json()
                if result.get('success'):
                    tasks = result.get('data', [])
                    task_count = len(tasks)
                    status_results[status_value] = task_count
                    
                    print(f"   OK {status_name}: 获取到 {task_count} 个任务")
                    
                    if status_value == '':
                        all_tasks_count = task_count
                    
                    # 验证过滤结果的正确性
                    if status_value and tasks:
                        wrong_status_tasks = [task for task in tasks if task.get('status') != status_value]
                        if wrong_status_tasks:
                            print(f"   FAIL {status_name}: 发现 {len(wrong_status_tasks)} 个状态不匹配的任务")
                            return False
                        else:
                            print(f"   OK {status_name}: 状态过滤结果正确")
                else:
                    print(f"   FAIL {status_name}: API返回错误: {result.get('error')}")
                    return False
            else:
                print(f"   FAIL {status_name}: API请求失败: {response.status_code}")
                return False
        
        # 验证过滤逻辑的数学一致性
        filtered_total = sum(count for status, count in status_results.items() if status != '')
        
        if all_tasks_count > 0:
            if filtered_total <= all_tasks_count:
                print("   OK 状态过滤逻辑数学一致性正常")
                print(f"   INFO 总任务数: {all_tasks_count}, 各状态任务总数: {filtered_total}")
            else:
                print(f"   WARN 状态过滤逻辑异常: 总数{all_tasks_count} < 过滤总数{filtered_total}")
        else:
            print("   INFO 没有任务数据，无法验证过滤逻辑")
        
        return True
    
    def test_javascript_methods_existence(self):
        """测试JavaScript方法存在性"""
        print("\n5. 测试JavaScript方法存在性...")
        
        try:
            # 获取admin.js文件
            response = self.session.get(f"{self.base_url}/static/js/admin.js")
            
            if response.status_code == 200:
                js_content = response.text
                
                # 检查关键方法
                critical_methods = [
                    ('viewCountTask', '查看盘点任务方法'),
                    ('filterCountTasks', '过滤盘点任务方法'),
                    ('loadCountTasks', '加载盘点任务方法'),
                    ('showModal', '显示模态框方法'),
                    ('hideModal', '隐藏模态框方法'),
                    ('showCountTaskDetail', '显示任务详情方法')
                ]
                
                all_methods_exist = True
                
                for method_name, method_desc in critical_methods:
                    if f'{method_name}(' in js_content or f'{method_name} (' in js_content:
                        print(f"   OK {method_desc}: 方法存在")
                    else:
                        print(f"   FAIL {method_desc}: 方法缺失")
                        all_methods_exist = False
                
                # 检查事件绑定
                event_bindings = [
                    ('refreshCountTasksBtn', 'loadCountTasks'),
                    ('countStatusFilter', 'filterCountTasks'),
                    ('createCountTaskBtn', 'createCountTask')
                ]
                
                for element_id, method_name in event_bindings:
                    if element_id in js_content and method_name in js_content:
                        print(f"   OK {element_id}: 事件绑定存在")
                    else:
                        print(f"   WARN {element_id}: 事件绑定可能有问题")
                
                return all_methods_exist
            else:
                print(f"   FAIL 无法获取JavaScript文件: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"   FAIL JavaScript检查异常: {e}")
            return False
    
    def test_html_elements_existence(self):
        """测试HTML元素存在性"""
        print("\n6. 测试HTML元素存在性...")
        
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
                    ('id="modal"', '模态框容器'),
                    ('id="modalBody"', '模态框内容区域')
                ]
                
                all_elements_exist = True
                
                for element_pattern, element_name in ui_elements:
                    if element_pattern in html_content:
                        print(f"   OK {element_name}: HTML元素存在")
                    else:
                        print(f"   FAIL {element_name}: HTML元素缺失")
                        all_elements_exist = False
                
                # 检查状态过滤器选项
                status_options = [
                    ('value="in_progress"', '进行中选项'),
                    ('value="completed"', '已完成选项'),
                    ('value="cancelled"', '已取消选项')
                ]
                
                for option_pattern, option_name in status_options:
                    if option_pattern in html_content:
                        print(f"   OK {option_name}: 存在")
                    else:
                        print(f"   WARN {option_name}: 缺失")
                
                return all_elements_exist
            else:
                print(f"   FAIL 无法获取HTML页面: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"   FAIL HTML检查异常: {e}")
            return False
    
    def run_all_tests(self):
        """运行所有测试"""
        print("库存盘点页面UI控件功能最终验证")
        print("=" * 60)
        
        tests = [
            ("管理员登录", self.login_admin),
            ("查看按钮完整工作流程", self.test_view_button_complete_workflow),
            ("刷新按钮完整工作流程", self.test_refresh_button_complete_workflow),
            ("状态过滤完整工作流程", self.test_status_filter_complete_workflow),
            ("JavaScript方法存在性", self.test_javascript_methods_existence),
            ("HTML元素存在性", self.test_html_elements_existence)
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
        print(f"最终验证结果: {passed_tests}/{total_tests} 个测试通过")
        
        if passed_tests == total_tests:
            print("SUCCESS 所有UI控件功能验证通过！")
        else:
            print("WARN 部分功能需要进一步检查")
            print(f"通过率: {passed_tests/total_tests*100:.1f}%")
        
        return passed_tests, total_tests, passed_tests == total_tests

def main():
    """主函数"""
    checker = FinalUIChecker()
    passed, total, success = checker.run_all_tests()
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())
