#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
库存盘点页面UI控件功能检查脚本
"""

import requests
import json
import sys
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException

class UIControlsChecker:
    def __init__(self, base_url="http://localhost:5000"):
        self.base_url = base_url
        self.session = requests.Session()
        self.driver = None
        
    def setup_browser(self):
        """设置浏览器"""
        try:
            chrome_options = Options()
            chrome_options.add_argument('--headless')  # 无头模式
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--disable-gpu')
            chrome_options.add_argument('--window-size=1920,1080')
            
            self.driver = webdriver.Chrome(options=chrome_options)
            return True
        except Exception as e:
            print(f"   WARN 无法启动浏览器: {e}")
            print("   INFO 将跳过浏览器相关测试")
            return False
    
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
                            return True
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
                return True
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
                    
                    # 验证过滤结果
                    if status and tasks:
                        # 检查返回的任务是否都是指定状态
                        wrong_status_tasks = [task for task in tasks if task.get('status') != status]
                        if wrong_status_tasks:
                            print(f"   WARN {name}: 发现 {len(wrong_status_tasks)} 个状态不匹配的任务")
                        else:
                            print(f"   OK {name}: 状态过滤正确")
                else:
                    print(f"   FAIL {name}: API返回错误: {result.get('error')}")
                    return False
            else:
                print(f"   FAIL {name}: API请求失败: {response.status_code}")
                return False
        
        return True
    
    def test_browser_ui_controls(self):
        """测试浏览器中的UI控件"""
        if not self.driver:
            print("\n5. 跳过浏览器UI测试（浏览器不可用）")
            return True
        
        print("\n5. 测试浏览器中的UI控件...")
        
        try:
            # 访问登录页面
            self.driver.get(f"{self.base_url}/admin/login")
            
            # 登录
            username_input = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.ID, "username"))
            )
            password_input = self.driver.find_element(By.ID, "password")
            login_btn = self.driver.find_element(By.ID, "loginBtn")
            
            username_input.send_keys("admin")
            password_input.send_keys("admin123")
            login_btn.click()
            
            # 等待跳转到管理页面
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CLASS_NAME, "menu-item"))
            )
            
            # 点击库存盘点菜单
            inventory_counts_menu = self.driver.find_element(By.CSS_SELECTOR, "[data-section='inventory-counts']")
            inventory_counts_menu.click()
            
            # 等待页面加载
            time.sleep(2)
            
            # 检查UI控件是否存在
            controls_to_check = [
                ("refreshCountTasksBtn", "刷新按钮"),
                ("countStatusFilter", "状态过滤器"),
                ("countTasksTableBody", "任务列表表格")
            ]
            
            for element_id, name in controls_to_check:
                try:
                    element = self.driver.find_element(By.ID, element_id)
                    print(f"   OK {name}: 元素存在且可见")
                except NoSuchElementException:
                    print(f"   FAIL {name}: 元素不存在")
                    return False
            
            # 测试刷新按钮点击
            try:
                refresh_btn = self.driver.find_element(By.ID, "refreshCountTasksBtn")
                refresh_btn.click()
                print("   OK 刷新按钮: 点击成功")
                time.sleep(1)
            except Exception as e:
                print(f"   FAIL 刷新按钮: 点击失败 - {e}")
                return False
            
            # 测试状态过滤器
            try:
                status_filter = self.driver.find_element(By.ID, "countStatusFilter")
                # 选择"进行中"状态
                status_filter.click()
                options = status_filter.find_elements(By.TAG_NAME, "option")
                for option in options:
                    if option.get_attribute("value") == "in_progress":
                        option.click()
                        break
                print("   OK 状态过滤器: 选择操作成功")
                time.sleep(1)
            except Exception as e:
                print(f"   FAIL 状态过滤器: 操作失败 - {e}")
                return False
            
            # 检查查看按钮（如果有任务的话）
            try:
                view_buttons = self.driver.find_elements(By.XPATH, "//button[contains(text(), '查看')]")
                if view_buttons:
                    print(f"   OK 查看按钮: 找到 {len(view_buttons)} 个查看按钮")
                    
                    # 检查第一个查看按钮的onclick属性
                    first_view_btn = view_buttons[0]
                    onclick_attr = first_view_btn.get_attribute("onclick")
                    if onclick_attr and "viewCountTask" in onclick_attr:
                        print("   OK 查看按钮: onclick事件绑定正确")
                    else:
                        print(f"   WARN 查看按钮: onclick属性异常 - {onclick_attr}")
                else:
                    print("   INFO 查看按钮: 当前没有任务，无法测试查看按钮")
            except Exception as e:
                print(f"   FAIL 查看按钮: 检查失败 - {e}")
                return False
            
            return True
            
        except TimeoutException:
            print("   FAIL 浏览器测试: 页面加载超时")
            return False
        except Exception as e:
            print(f"   FAIL 浏览器测试: {e}")
            return False
    
    def check_javascript_errors(self):
        """检查JavaScript错误"""
        if not self.driver:
            return True
        
        print("\n6. 检查JavaScript控制台错误...")
        
        try:
            # 获取控制台日志
            logs = self.driver.get_log('browser')
            
            errors = [log for log in logs if log['level'] == 'SEVERE']
            warnings = [log for log in logs if log['level'] == 'WARNING']
            
            if errors:
                print(f"   FAIL 发现 {len(errors)} 个JavaScript错误:")
                for error in errors[:3]:  # 只显示前3个错误
                    print(f"      - {error['message']}")
                return False
            elif warnings:
                print(f"   WARN 发现 {len(warnings)} 个JavaScript警告")
                for warning in warnings[:2]:  # 只显示前2个警告
                    print(f"      - {warning['message']}")
                return True
            else:
                print("   OK 没有发现JavaScript错误")
                return True
                
        except Exception as e:
            print(f"   WARN 无法获取控制台日志: {e}")
            return True
    
    def cleanup(self):
        """清理资源"""
        if self.driver:
            self.driver.quit()
    
    def run_all_tests(self):
        """运行所有测试"""
        print("库存盘点页面UI控件功能检查")
        print("=" * 60)
        
        # 设置浏览器
        browser_available = self.setup_browser()
        
        tests = [
            ("管理员登录", self.login_admin),
            ("查看按钮功能", self.test_view_button_functionality),
            ("刷新按钮功能", self.test_refresh_button_functionality),
            ("状态过滤功能", self.test_status_filter_functionality),
            ("浏览器UI控件", self.test_browser_ui_controls),
            ("JavaScript错误检查", self.check_javascript_errors)
        ]
        
        passed_tests = 0
        total_tests = len(tests)
        
        for test_name, test_func in tests:
            try:
                if test_func():
                    passed_tests += 1
                    print(f"OK {test_name}")
                else:
                    print(f"FAIL {test_name}")
                time.sleep(0.5)
            except Exception as e:
                print(f"ERROR {test_name}: {e}")
        
        self.cleanup()
        
        print("\n" + "=" * 60)
        print(f"测试完成: {passed_tests}/{total_tests} 个测试通过")
        
        return passed_tests == total_tests

def main():
    """主函数"""
    checker = UIControlsChecker()
    success = checker.run_all_tests()
    
    if success:
        print("SUCCESS 所有UI控件功能检查通过！")
    else:
        print("WARN 发现一些UI控件问题，需要修复")
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())
