#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI客服系统国际化翻译修复测试脚本
测试管理后台界面的英文翻译完整性
"""

import requests
import time
from urllib.parse import urljoin

class TranslationTestSuite:
    """翻译功能测试套件"""
    
    def __init__(self, base_url="http://localhost:5000"):
        self.base_url = base_url
        self.session = requests.Session()
        
    def test_admin_login(self):
        """测试管理员登录"""
        print("1. 测试管理员登录...")
        
        login_data = {
            'username': 'admin',
            'password': 'admin123'
        }
        
        response = self.session.post(
            f"{self.base_url}/admin/login",
            data=login_data,
            allow_redirects=False
        )
        
        if response.status_code == 302:
            print("   OK 管理员登录成功")
            return True
        else:
            print(f"   FAIL 登录失败: {response.status_code}")
            return False
    
    def test_language_switch_api(self):
        """测试语言切换API"""
        print("\n2. 测试语言切换API...")
        
        # 切换到英文
        response = self.session.post(f"{self.base_url}/api/language/en")
        
        if response.status_code == 200:
            result = response.json()
            if result.get('success'):
                print("   OK 语言切换API正常工作")
                return True
            else:
                print(f"   FAIL API返回错误: {result.get('error')}")
                return False
        else:
            print(f"   FAIL API请求失败: {response.status_code}")
            return False
    
    def test_admin_dashboard_english(self):
        """测试管理后台英文界面"""
        print("\n3. 测试管理后台英文界面...")
        
        # 先切换到英文
        self.session.post(f"{self.base_url}/api/language/en")
        
        # 访问管理后台
        response = self.session.get(f"{self.base_url}/admin/dashboard")
        
        if response.status_code == 200:
            content = response.text
            
            # 检查关键英文翻译是否存在
            english_elements = [
                'Inventory Management',
                'Inventory Count',
                'Data Analysis',
                'Create New Count',
                'Count Task List',
                'All Status',
                'In Progress',
                'Completed',
                'Cancelled',
                'Task ID',
                'Created Time',
                'Operator',
                'Product Count',
                'Actions',
                'Loading...',
                'Add Count Products',
                'Barcode Scan/Input',
                'Product Search',
                'Current Count Items',
                'Product Name',
                'Barcode',
                'Storage Area',
                'Book Quantity',
                'Actual Quantity',
                'Difference',
                'Complete Count',
                'Cancel Count',
                'Weekly Comparison',
                'Manual Comparison Selection',
                'Start Comparison',
                'Total Products',
                'Changed Products',
                'Anomaly Items',
                'Change Details',
                'All Changes',
                'Stock Increased',
                'Stock Decreased',
                'New Products',
                'Removed Products',
                'Download Analysis Report',
                'Export Excel',
                'Generate Trend Chart'
            ]
            
            found_count = 0
            missing_elements = []
            
            for element in english_elements:
                if element in content:
                    found_count += 1
                else:
                    missing_elements.append(element)
            
            print(f"   📊 翻译覆盖率: {found_count}/{len(english_elements)} ({found_count/len(english_elements)*100:.1f}%)")
            
            if found_count >= len(english_elements) * 0.8:  # 80%覆盖率认为通过
                print("   ✅ OK 英文翻译覆盖率良好")
                if missing_elements:
                    print(f"   ⚠️  缺失的翻译: {missing_elements[:5]}...")  # 只显示前5个
                return True
            else:
                print("   ❌ FAIL 英文翻译覆盖率不足")
                print(f"   缺失的翻译: {missing_elements}")
                return False
        else:
            print(f"   ❌ FAIL 无法访问管理后台: {response.status_code}")
            return False
    
    def test_inventory_count_page_english(self):
        """测试库存盘点页面英文翻译"""
        print("\n4. 测试库存盘点页面英文翻译...")
        
        # 确保是英文环境
        self.session.post(f"{self.base_url}/api/language/en")
        
        # 访问管理后台（包含库存盘点页面）
        response = self.session.get(f"{self.base_url}/admin/dashboard")
        
        if response.status_code == 200:
            content = response.text
            
            # 检查库存盘点页面的关键英文元素
            inventory_elements = [
                'Inventory Count',
                'Create and manage inventory count tasks',
                'Create New Count',
                'Count Task List',
                'Add Count Products',
                'Barcode Scan/Input',
                'Scan or enter barcode',
                'Product Search',
                'Search product name',
                'Current Count Items',
                'Complete Count',
                'Cancel Count'
            ]
            
            found_count = 0
            for element in inventory_elements:
                if element in content:
                    found_count += 1
            
            print(f"   📊 库存盘点页面翻译覆盖率: {found_count}/{len(inventory_elements)} ({found_count/len(inventory_elements)*100:.1f}%)")
            
            if found_count >= len(inventory_elements) * 0.8:
                print("   ✅ OK 库存盘点页面英文翻译良好")
                return True
            else:
                print("   ❌ FAIL 库存盘点页面英文翻译不完整")
                return False
        else:
            print(f"   ❌ FAIL 无法访问页面: {response.status_code}")
            return False
    
    def test_javascript_translations(self):
        """测试JavaScript翻译对象"""
        print("\n5. 测试JavaScript翻译对象...")
        
        # 确保是英文环境
        self.session.post(f"{self.base_url}/api/language/en")
        
        response = self.session.get(f"{self.base_url}/admin/dashboard")
        
        if response.status_code == 200:
            content = response.text
            
            # 检查JavaScript翻译对象是否存在
            js_translation_indicators = [
                'window.translations',
                'Network error',
                'Operation successful',
                'Count task created successfully',
                'Weekly comparison analysis created successfully'
            ]
            
            found_count = 0
            for indicator in js_translation_indicators:
                if indicator in content:
                    found_count += 1
            
            print(f"   📊 JavaScript翻译对象: {found_count}/{len(js_translation_indicators)} 项检测通过")
            
            if found_count >= len(js_translation_indicators) * 0.8:
                print("   ✅ OK JavaScript翻译支持正常")
                return True
            else:
                print("   ❌ FAIL JavaScript翻译支持不完整")
                return False
        else:
            print(f"   ❌ FAIL 无法访问页面: {response.status_code}")
            return False
    
    def test_chinese_fallback(self):
        """测试中文回退功能"""
        print("\n6. 测试中文回退功能...")
        
        # 切换回中文
        response = self.session.post(f"{self.base_url}/api/language/zh")
        
        if response.status_code == 200:
            result = response.json()
            if result.get('success'):
                print("   ✅ OK 中文回退功能正常")
                return True
            else:
                print(f"   ❌ FAIL 中文切换失败: {result.get('error')}")
                return False
        else:
            print(f"   ❌ FAIL 中文切换请求失败: {response.status_code}")
            return False
    
    def run_all_tests(self):
        """运行所有测试"""
        print("AI客服系统国际化翻译修复测试")
        print("=" * 60)
        
        tests = [
            self.test_admin_login,
            self.test_language_switch_api,
            self.test_admin_dashboard_english,
            self.test_inventory_count_page_english,
            self.test_javascript_translations,
            self.test_chinese_fallback
        ]
        
        passed = 0
        total = len(tests)
        
        for test in tests:
            try:
                if test():
                    passed += 1
                time.sleep(0.5)  # 短暂延迟
            except Exception as e:
                print(f"   ❌ ERROR 测试异常: {e}")
        
        print("\n" + "=" * 60)
        print(f"测试完成: {passed}/{total} 个测试通过")
        
        if passed == total:
            print("🎉 SUCCESS 所有翻译功能测试通过！")
        elif passed >= total * 0.8:
            print("⚠️  WARNING 大部分翻译功能正常，但仍有改进空间")
        else:
            print("❌ FAIL 翻译功能存在较多问题，需要进一步修复")
        
        return passed == total

if __name__ == "__main__":
    tester = TranslationTestSuite()
    tester.run_all_tests()
