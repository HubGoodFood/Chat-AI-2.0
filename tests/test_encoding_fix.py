#!/usr/bin/env python3
"""
编码修复验证测试
"""
import os
import sys
import json
import tempfile
import shutil
from datetime import datetime

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.models.inventory_manager import InventoryManager
from src.utils.encoding_utils import safe_filename, safe_barcode_filename, validate_text_encoding


def test_encoding_utils():
    """测试编码工具函数"""
    print("测试编码工具函数...")
    
    test_cases = [
        ("红富士苹果", "正常中文"),
        ("Apple苹果123", "中英文数字混合"),
        ("蔬菜(有机)", "包含括号"),
        ("🍎苹果🍎", "包含emoji"),
        ("超级长的产品名称测试用例" * 10, "超长名称"),
        ("产品-名称【特殊】", "特殊标点符号"),
        ("", "空字符串"),
        ("   ", "空白字符"),
    ]
    
    success_count = 0
    
    for text, case_type in test_cases:
        try:
            # 测试安全文件名生成
            safe_name = safe_filename(text)
            
            # 测试条形码文件名生成
            barcode_filename = safe_barcode_filename(text, "8800001234")
            
            # 测试文本编码验证
            is_valid, result = validate_text_encoding(text)
            
            print(f"  OK {case_type}:")
            print(f"    原文: '{text[:50]}{'...' if len(text) > 50 else ''}'")
            print(f"    安全文件名: '{safe_name}'")
            print(f"    条形码文件名: '{barcode_filename}'")
            print(f"    编码验证: {is_valid}")
            
            success_count += 1
            
        except Exception as e:
            print(f"  FAIL {case_type}: {e}")
    
    print(f"\n编码工具测试: {success_count}/{len(test_cases)} 通过")
    return success_count == len(test_cases)


def test_product_addition_with_encoding():
    """测试产品添加的编码处理"""
    print("\n测试产品添加的编码处理...")
    
    # 创建临时目录
    temp_dir = tempfile.mkdtemp(prefix="encoding_test_")
    
    try:
        # 创建库存管理器
        inventory_manager = InventoryManager()
        inventory_manager.inventory_file = os.path.join(temp_dir, "inventory.json")
        inventory_manager.products_file = os.path.join(temp_dir, "products.csv")
        inventory_manager.barcode_dir = os.path.join(temp_dir, "barcodes")
        
        # 确保目录存在
        os.makedirs(inventory_manager.barcode_dir, exist_ok=True)
        os.makedirs(os.path.dirname(inventory_manager.inventory_file), exist_ok=True)
        
        # 测试产品数据（包含各种编码挑战）
        test_products = [
            {
                "product_name": "红富士苹果",
                "category": "水果",
                "price": "15.8",
                "unit": "斤",
                "specification": "500g/个",
                "description": "香甜脆嫩的红富士苹果"
            },
            {
                "product_name": "有机蔬菜(精选)",
                "category": "蔬菜",
                "price": "12.5",
                "unit": "份",
                "specification": "混合装",
                "description": "100%有机认证蔬菜"
            },
            {
                "product_name": "Premium橙子No.1",
                "category": "水果",
                "price": "20.0",
                "unit": "个",
                "specification": "大号",
                "description": "进口优质橙子"
            },
            {
                "product_name": "🍎特色苹果🍎",
                "category": "水果",
                "price": "18.0",
                "unit": "个",
                "specification": "中等",
                "description": "新鲜美味苹果"
            }
        ]
        
        success_count = 0
        
        for product in test_products:
            try:
                product_id = inventory_manager.add_product(product, "测试员")
                
                if product_id:
                    # 验证产品是否真的被添加
                    added_product = inventory_manager.get_product_by_id(product_id)
                    if added_product and added_product["product_name"]:
                        success_count += 1
                        print(f"  OK '{product['product_name']}' 添加成功 (ID: {product_id})")
                        
                        # 检查条形码图片是否存在
                        if added_product.get("barcode_image"):
                            barcode_path = os.path.join(temp_dir, added_product["barcode_image"])
                            if os.path.exists(barcode_path):
                                print(f"    条形码图片已生成: {added_product['barcode_image']}")
                            else:
                                print(f"    警告: 条形码图片未找到")
                    else:
                        print(f"  FAIL '{product['product_name']}': 添加后验证失败")
                else:
                    print(f"  FAIL '{product['product_name']}': 添加返回None")
                    
            except Exception as e:
                print(f"  ERROR '{product['product_name']}': {e}")
        
        success_rate = (success_count / len(test_products)) * 100
        print(f"\n产品添加测试: {success_count}/{len(test_products)} 通过 ({success_rate:.1f}%)")
        
        return success_rate >= 95
        
    finally:
        # 清理临时目录
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)


def test_json_encoding_safety():
    """测试JSON编码安全性"""
    print("\n测试JSON编码安全性...")
    
    # 创建包含各种字符的测试数据
    test_data = {
        "中文": "测试中文字符",
        "English": "Test English characters",
        "数字": 12345,
        "特殊字符": "!@#$%^&*()",
        "emoji": "🍎🥕🥬",
        "混合": "Mixed中英文123!@#",
        "长文本": "这是一个很长的文本" * 100,
        "timestamp": datetime.now().isoformat()
    }
    
    try:
        # 测试JSON序列化
        json_str = json.dumps(test_data, ensure_ascii=False, indent=2)
        
        # 测试JSON反序列化
        parsed_data = json.loads(json_str)
        
        # 验证数据完整性
        for key, value in test_data.items():
            if parsed_data.get(key) != value:
                print(f"  FAIL JSON编码测试: {key} 数据不匹配")
                return False
        
        print("  OK JSON编码安全性测试通过")
        return True
        
    except Exception as e:
        print(f"  FAIL JSON编码测试异常: {e}")
        return False


def main():
    """主测试函数"""
    print("编码修复验证测试")
    print("=" * 50)
    
    tests = [
        ("编码工具函数", test_encoding_utils),
        ("JSON编码安全性", test_json_encoding_safety),
        ("产品添加编码处理", test_product_addition_with_encoding)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        try:
            if test_func():
                print(f"OK {test_name}: 通过")
                passed += 1
            else:
                print(f"FAIL {test_name}: 失败")
        except Exception as e:
            print(f"ERROR {test_name}: 异常 - {e}")
    
    print("\n" + "=" * 50)
    success_rate = (passed / total) * 100
    print(f"总体测试结果: {passed}/{total} 通过 ({success_rate:.1f}%)")
    
    if success_rate >= 95:
        print("编码问题修复成功！")
        return True
    elif success_rate >= 80:
        print("大部分问题已修复，仍有少量问题")
        return False
    else:
        print("编码问题仍然存在，需要进一步修复")
        return False


if __name__ == "__main__":
    main()
