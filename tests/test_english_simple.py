#!/usr/bin/env python3
"""
AI客服系统英文本地化简化测试
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.utils.i18n_simple import i18n_simple

def test_basic_functionality():
    """测试基本功能"""
    print("=== 基本功能测试 ===")
    
    # 测试语言支持
    languages = i18n_simple.languages
    print(f"支持的语言: {list(languages.keys())}")
    
    # 检查en_US是否存在
    if 'en_US' in languages:
        print("[OK] en_US语言支持已添加")
        print(f"en_US配置: {languages['en_US']}")
    else:
        print("[ERROR] en_US语言支持缺失")
    
    # 测试翻译字典
    en_translations = i18n_simple.translations.get('en', {})
    en_us_translations = i18n_simple.translations.get('en_US', {})
    
    print(f"英文翻译条目数: {len(en_translations)}")
    print(f"美式英文翻译条目数: {len(en_us_translations)}")
    
    # 测试关键翻译
    key_texts = [
        "管理员登录",
        "管理后台", 
        "库存管理",
        "产品入库",
        "库存盘点",
        "数据对比分析",
        "反馈管理",
        "操作日志",
        "数据导出",
        "系统设置"
    ]
    
    print("\n关键翻译检查:")
    missing = 0
    for text in key_texts:
        if text in en_translations:
            print(f"   [OK] {text} -> {en_translations[text]}")
        else:
            print(f"   [MISS] {text}")
            missing += 1
    
    print(f"\n翻译覆盖率: {(len(key_texts) - missing) / len(key_texts) * 100:.1f}%")
    
    # 测试新增翻译
    new_translations = [
        "管理员控制台 - 果蔬客服AI系统",
        "客户反馈管理",
        "客户昵称", 
        "反馈时间",
        "系统版本",
        "运行状态",
        "修改密码",
        "存储区域信息",
        "条形码预览"
    ]
    
    print("\n新增翻译检查:")
    new_missing = 0
    for text in new_translations:
        if text in en_translations:
            print(f"   [OK] {text} -> {en_translations[text]}")
        else:
            print(f"   [MISS] {text}")
            new_missing += 1
    
    print(f"新增翻译覆盖率: {(len(new_translations) - new_missing) / len(new_translations) * 100:.1f}%")

def test_translation_quality():
    """测试翻译质量"""
    print("\n=== 翻译质量测试 ===")
    
    # 专业术语检查
    professional_terms = {
        "库存管理": "Inventory Management",
        "库存盘点": "Inventory Count",
        "数据对比分析": "Data Analysis", 
        "反馈管理": "Feedback Management",
        "操作日志": "Operation Logs",
        "数据导出": "Data Export",
        "系统设置": "System Settings",
        "产品入库": "Product Entry"
    }
    
    en_translations = i18n_simple.translations.get('en', {})
    
    print("专业术语翻译:")
    for chinese, expected in professional_terms.items():
        actual = en_translations.get(chinese, "")
        if actual == expected:
            print(f"   [OK] {chinese} -> {actual}")
        elif actual:
            print(f"   [DIFF] {chinese} -> {actual} (期望: {expected})")
        else:
            print(f"   [MISS] {chinese}")

def test_us_specific_features():
    """测试美国用户特定功能"""
    print("\n=== 美国用户特定功能测试 ===")
    
    # 检查美国用户友好的翻译
    us_friendly_terms = {
        "斤": "Jin (Chinese pound)",  # 保留中文单位但添加说明
        "A区 - 水果区": "Area A - Fruit Zone",
        "B区 - 蔬菜区": "Area B - Vegetable Zone",
        "例：15元/斤": "e.g.: 15 yuan/jin"
    }
    
    en_translations = i18n_simple.translations.get('en', {})
    
    print("美国用户友好翻译:")
    for chinese, expected in us_friendly_terms.items():
        actual = en_translations.get(chinese, "")
        if actual:
            print(f"   [OK] {chinese} -> {actual}")
        else:
            print(f"   [MISS] {chinese}")

def main():
    """主测试函数"""
    print("AI客服系统英文本地化测试")
    print("=" * 50)
    
    try:
        test_basic_functionality()
        test_translation_quality()
        test_us_specific_features()
        
        print("\n" + "=" * 50)
        print("测试完成")
        
    except Exception as e:
        print(f"测试过程中出现错误: {e}")

if __name__ == "__main__":
    main()
