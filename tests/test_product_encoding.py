#!/usr/bin/env python3
"""
产品添加功能编码问题诊断测试
"""
import os
import sys
import json
import tempfile
import shutil
from datetime import datetime
from typing import Dict, List, Tuple

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.models.inventory_manager import InventoryManager


class ProductEncodingTester:
    """产品编码问题测试器"""
    
    def __init__(self):
        """初始化测试器"""
        self.test_results = []
        self.temp_dir = None
        self.inventory_manager = None
        
        # 测试用例数据
        self.test_products = [
            # 正常中文产品
            {
                "product_name": "红富士苹果",
                "category": "水果",
                "price": "15.8",
                "unit": "斤",
                "specification": "500g/个",
                "description": "香甜脆嫩的红富士苹果"
            },
            # 包含特殊字符的产品
            {
                "product_name": "有机蔬菜(精选)",
                "category": "蔬菜",
                "price": "12.5",
                "unit": "份",
                "specification": "混合装",
                "description": "100%有机认证蔬菜"
            },
            # 包含英文和数字的产品
            {
                "product_name": "Premium橙子No.1",
                "category": "水果",
                "price": "20.0",
                "unit": "个",
                "specification": "大号",
                "description": "进口优质橙子"
            },
            # 长名称产品
            {
                "product_name": "超级新鲜有机无农药绿色健康营养丰富的特级胡萝卜",
                "category": "蔬菜",
                "price": "8.8",
                "unit": "根",
                "specification": "特大号",
                "description": "营养价值极高的有机胡萝卜"
            },
            # 包含emoji的产品（边界测试）
            {
                "product_name": "🍎苹果🍎",
                "category": "水果",
                "price": "18.0",
                "unit": "个",
                "specification": "中等",
                "description": "新鲜美味苹果"
            },
            # 包含各种标点符号的产品
            {
                "product_name": "蔬菜-混合装【精选】",
                "category": "蔬菜",
                "price": "25.0",
                "unit": "盒",
                "specification": "500g装",
                "description": "多种蔬菜组合装"
            }
        ]
    
    def setup_test_environment(self):
        """设置测试环境"""
        try:
            # 创建临时目录
            self.temp_dir = tempfile.mkdtemp(prefix="inventory_test_")

            # 创建测试用的库存管理器
            self.inventory_manager = InventoryManager()

            # 修改库存管理器的文件路径为临时目录
            self.inventory_manager.inventory_file = os.path.join(self.temp_dir, "inventory.json")
            self.inventory_manager.products_file = os.path.join(self.temp_dir, "products.csv")
            self.inventory_manager.barcode_dir = os.path.join(self.temp_dir, "barcodes")

            # 确保目录存在
            os.makedirs(os.path.join(self.temp_dir, "barcodes"), exist_ok=True)
            os.makedirs(os.path.dirname(self.inventory_manager.inventory_file), exist_ok=True)

            return True

        except Exception as e:
            print(f"测试环境设置失败: {e}")
            return False
    
    def cleanup_test_environment(self):
        """清理测试环境"""
        try:
            if self.temp_dir and os.path.exists(self.temp_dir):
                shutil.rmtree(self.temp_dir)
            return True
        except Exception as e:
            print(f"⚠️ 清理测试环境失败: {e}")
            return False
    
    def test_filename_generation(self) -> Tuple[bool, str]:
        """测试文件名生成逻辑"""
        try:
            print("\n测试文件名生成逻辑...")

            test_cases = [
                ("红富士苹果", "正常中文"),
                ("Apple苹果123", "中英文数字混合"),
                ("蔬菜(有机)", "包含括号"),
                ("🍎苹果🍎", "包含emoji"),
                ("超级长的产品名称测试用例", "长名称"),
                ("产品-名称【特殊】", "特殊标点符号")
            ]
            
            failed_cases = []
            
            for product_name, case_type in test_cases:
                try:
                    # 模拟原有的文件名生成逻辑
                    safe_name = "".join(c for c in product_name if c.isalnum() or c in (' ', '-', '_')).rstrip()
                    barcode_number = "8800001234"
                    filename = f"{safe_name}_{barcode_number}"
                    
                    # 检查文件名是否安全
                    if not safe_name:
                        failed_cases.append(f"{case_type}: 文件名为空")
                    elif len(filename) > 200:  # Windows文件名长度限制
                        failed_cases.append(f"{case_type}: 文件名过长({len(filename)}字符)")
                    else:
                        print(f"  OK {case_type}: '{product_name}' -> '{filename}'")
                        
                except Exception as e:
                    failed_cases.append(f"{case_type}: {str(e)}")
            
            if failed_cases:
                return False, f"文件名生成失败: {'; '.join(failed_cases)}"
            else:
                return True, "文件名生成测试通过"
                
        except Exception as e:
            return False, f"文件名生成测试异常: {e}"
    
    def test_barcode_image_saving(self) -> Tuple[bool, str]:
        """测试条形码图片保存功能"""
        try:
            print("\n测试条形码图片保存...")

            failed_cases = []
            success_count = 0
            
            for i, product in enumerate(self.test_products[:4]):  # 测试前4个产品
                try:
                    product_name = product["product_name"]
                    barcode_number = f"880000{str(i+1).zfill(4)}"
                    
                    # 尝试保存条形码图片
                    barcode_image_path = self.inventory_manager._save_barcode_image(
                        barcode_number, product_name
                    )
                    
                    if barcode_image_path:
                        # 检查文件是否真的被创建
                        full_path = os.path.join(self.temp_dir, "barcodes", 
                                               barcode_image_path.replace("barcodes/", ""))
                        if os.path.exists(full_path):
                            success_count += 1
                            print(f"  OK '{product_name}' 条形码图片保存成功")
                        else:
                            failed_cases.append(f"'{product_name}': 图片文件未创建")
                    else:
                        failed_cases.append(f"'{product_name}': 返回路径为空")
                        
                except Exception as e:
                    failed_cases.append(f"'{product['product_name']}': {str(e)}")
            
            success_rate = (success_count / len(self.test_products[:4])) * 100
            
            if failed_cases:
                return False, f"条形码保存失败({success_rate:.1f}%成功): {'; '.join(failed_cases)}"
            else:
                return True, f"条形码图片保存测试通过(100%成功)"
                
        except Exception as e:
            return False, f"条形码图片保存测试异常: {e}"
    
    def test_product_addition(self) -> Tuple[bool, str]:
        """测试产品添加功能"""
        try:
            print("\n测试产品添加功能...")

            failed_cases = []
            success_count = 0
            
            for product in self.test_products:
                try:
                    product_id = self.inventory_manager.add_product(product, "测试员")
                    
                    if product_id:
                        # 验证产品是否真的被添加
                        added_product = self.inventory_manager.get_product_by_id(product_id)
                        if added_product and added_product["product_name"] == product["product_name"]:
                            success_count += 1
                            print(f"  OK '{product['product_name']}' 添加成功 (ID: {product_id})")
                        else:
                            failed_cases.append(f"'{product['product_name']}': 添加后验证失败")
                    else:
                        failed_cases.append(f"'{product['product_name']}': 添加返回None")
                        
                except Exception as e:
                    failed_cases.append(f"'{product['product_name']}': {str(e)}")
            
            success_rate = (success_count / len(self.test_products)) * 100
            
            if failed_cases:
                return False, f"产品添加失败({success_rate:.1f}%成功): {'; '.join(failed_cases)}"
            else:
                return True, f"产品添加测试通过(100%成功)"
                
        except Exception as e:
            return False, f"产品添加测试异常: {e}"
    
    def test_json_encoding(self) -> Tuple[bool, str]:
        """测试JSON编码处理"""
        try:
            print("\n测试JSON编码处理...")

            # 创建包含各种字符的测试数据
            test_data = {
                "中文": "测试中文字符",
                "English": "Test English characters",
                "数字": 12345,
                "特殊字符": "!@#$%^&*()",
                "emoji": "🍎🥕🥬",
                "混合": "Mixed中英文123!@#",
                "timestamp": datetime.now().isoformat()
            }
            
            # 测试JSON序列化
            json_str = json.dumps(test_data, ensure_ascii=False, indent=2)
            
            # 测试JSON反序列化
            parsed_data = json.loads(json_str)
            
            # 验证数据完整性
            for key, value in test_data.items():
                if parsed_data.get(key) != value:
                    return False, f"JSON编码测试失败: {key} 数据不匹配"
            
            # 测试文件写入和读取
            test_file = os.path.join(self.temp_dir, "encoding_test.json")
            with open(test_file, 'w', encoding='utf-8') as f:
                json.dump(test_data, f, ensure_ascii=False, indent=2)
            
            with open(test_file, 'r', encoding='utf-8') as f:
                file_data = json.load(f)
            
            # 验证文件数据完整性
            for key, value in test_data.items():
                if file_data.get(key) != value:
                    return False, f"JSON文件编码测试失败: {key} 数据不匹配"
            
            return True, "JSON编码处理测试通过"
            
        except Exception as e:
            return False, f"JSON编码测试异常: {e}"
    
    def run_all_tests(self) -> Dict:
        """运行所有测试"""
        print("开始产品添加功能编码问题诊断测试")
        print("=" * 60)
        
        # 设置测试环境
        if not self.setup_test_environment():
            return {"success": False, "error": "测试环境设置失败"}
        
        try:
            tests = [
                ("文件名生成逻辑", self.test_filename_generation),
                ("JSON编码处理", self.test_json_encoding),
                ("条形码图片保存", self.test_barcode_image_saving),
                ("产品添加功能", self.test_product_addition)
            ]
            
            results = {}
            passed = 0
            total = len(tests)
            
            for test_name, test_func in tests:
                try:
                    success, message = test_func()
                    results[test_name] = {"success": success, "message": message}
                    
                    if success:
                        print(f"OK {test_name}: {message}")
                        passed += 1
                    else:
                        print(f"FAIL {test_name}: {message}")

                except Exception as e:
                    error_msg = f"测试异常: {e}"
                    results[test_name] = {"success": False, "message": error_msg}
                    print(f"ERROR {test_name}: {error_msg}")
            
            # 计算总体结果
            success_rate = (passed / total) * 100
            
            print("\n" + "=" * 60)
            print(f"测试结果: {passed}/{total} 通过 ({success_rate:.1f}%)")

            if success_rate >= 95:
                print("测试通过率达到95%以上，系统功能基本正常")
            elif success_rate >= 80:
                print("测试通过率80-95%，存在一些问题需要修复")
            else:
                print("测试通过率低于80%，存在严重问题需要立即修复")
            
            return {
                "success": success_rate >= 95,
                "success_rate": success_rate,
                "passed": passed,
                "total": total,
                "results": results
            }
            
        finally:
            # 清理测试环境
            self.cleanup_test_environment()


def main():
    """主函数"""
    tester = ProductEncodingTester()
    results = tester.run_all_tests()
    
    if results.get("success"):
        print("\n编码问题诊断完成，系统功能正常")
        return True
    else:
        print("\n发现编码问题，需要进行修复")
        return False


if __name__ == "__main__":
    main()
