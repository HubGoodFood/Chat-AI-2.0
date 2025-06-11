#!/usr/bin/env python3
"""
AI客服系统英文本地化测试脚本
测试英文翻译覆盖率和质量
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.utils.i18n_simple import i18n_simple

def test_language_support():
    """测试语言支持"""
    print("=== 语言支持测试 ===\n")
    
    available_languages = i18n_simple.get_available_languages()
    print(f"支持的语言数量: {len(available_languages)}")
    
    for lang in available_languages:
        print(f"  - {lang['code']}: {lang['name']} ({lang['native_name']}) {lang['flag']}")
    
    # 测试en_US支持
    if any(lang['code'] == 'en_US' for lang in available_languages):
        print("\n[OK] en_US语言支持已添加")
    else:
        print("\n[ERROR] en_US语言支持缺失")

def test_translation_coverage():
    """测试翻译覆盖率"""
    print("\n=== 翻译覆盖率测试 ===\n")
    
    # 关键界面文本
    key_interface_texts = [
        # 页面标题
        "管理员登录 - 果蔬客服AI系统",
        "管理员控制台 - 果蔬客服AI系统",
        
        # 导航菜单
        "管理后台", "控制台", "库存管理", "产品入库", "库存盘点", 
        "数据对比分析", "反馈管理", "操作日志", "数据导出", "系统设置",
        
        # 基础操作
        "保存", "取消", "删除", "编辑", "添加", "搜索", "导出", "刷新",
        
        # 状态文本
        "正在加载...", "操作成功", "操作失败", "进行中", "已完成", "已取消",
        
        # 表单元素
        "用户名", "密码", "登录", "产品名称", "分类", "价格", "当前库存", "状态",
        
        # 新增的翻译
        "客户反馈管理", "客户昵称", "反馈时间", "系统版本", "运行状态",
        "修改密码", "当前密码", "新密码", "确认新密码",
        "存储区域信息", "条形码预览", "产品信息"
    ]
    
    en_translations = i18n_simple.translations.get('en', {})
    en_us_translations = i18n_simple.translations.get('en_US', {})
    
    print(f"英文翻译条目数: {len(en_translations)}")
    print(f"美式英文翻译条目数: {len(en_us_translations)}")
    
    print("\n关键界面文本翻译检查:")
    missing_count = 0
    for text in key_interface_texts:
        if text in en_translations:
            print(f"   [OK] {text}")
        else:
            print(f"   [MISS] {text} -> 缺少翻译")
            missing_count += 1
    
    coverage_rate = (len(key_interface_texts) - missing_count) / len(key_interface_texts) * 100
    print(f"\n翻译覆盖率: {coverage_rate:.1f}% ({len(key_interface_texts) - missing_count}/{len(key_interface_texts)})")
    
    if missing_count == 0:
        print("[SUCCESS] 所有关键界面文本都有翻译")
    else:
        print(f"[WARNING] 还有 {missing_count} 个文本需要翻译")

def test_translation_quality():
    """测试翻译质量"""
    print("\n=== 翻译质量测试 ===\n")
    
    # 检查专业术语翻译
    professional_terms = {
        "库存管理": "Inventory Management",
        "库存盘点": "Inventory Count", 
        "数据对比分析": "Data Analysis",
        "反馈管理": "Feedback Management",
        "操作日志": "Operation Logs",
        "数据导出": "Data Export",
        "系统设置": "System Settings",
        "产品入库": "Product Entry",
        "存储区域": "Storage Area",
        "条形码": "Barcode",
        "实际数量": "Actual Quantity",
        "账面数量": "Book Quantity"
    }
    
    en_translations = i18n_simple.translations.get('en', {})
    
    print("专业术语翻译质量检查:")
    quality_issues = 0
    for chinese, expected_english in professional_terms.items():
        actual_english = en_translations.get(chinese, "")
        if actual_english == expected_english:
            print(f"   [OK] {chinese} -> {actual_english}")
        elif actual_english:
            print(f"   [WARN] {chinese} -> {actual_english} (建议: {expected_english})")
            quality_issues += 1
        else:
            print(f"   [MISS] {chinese} -> 缺少翻译")
            quality_issues += 1

    if quality_issues == 0:
        print("\n[SUCCESS] 专业术语翻译质量良好")
    else:
        print(f"\n[WARNING] 发现 {quality_issues} 个翻译质量问题")

def test_language_switching():
    """测试语言切换功能"""
    print("\n=== 语言切换功能测试 ===\n")
    
    # 测试设置不同语言
    test_languages = ['zh', 'en', 'en_US']
    
    for lang in test_languages:
        success = i18n_simple.set_language(lang)
        if success:
            current_lang = i18n_simple.get_locale()
            print(f"   [OK] 设置语言 {lang}: 成功 (当前: {current_lang})")
        else:
            print(f"   [ERROR] 设置语言 {lang}: 失败")
    
    # 测试翻译功能
    test_text = "管理后台"
    
    # 测试中文
    i18n_simple.set_language('zh')
    zh_result = i18n_simple.translate(test_text)
    print(f"\n中文翻译: '{test_text}' -> '{zh_result}'")
    
    # 测试英文
    i18n_simple.set_language('en')
    en_result = i18n_simple.translate(test_text)
    print(f"英文翻译: '{test_text}' -> '{en_result}'")
    
    # 测试美式英文
    i18n_simple.set_language('en_US')
    en_us_result = i18n_simple.translate(test_text)
    print(f"美式英文翻译: '{test_text}' -> '{en_us_result}'")

def main():
    """主测试函数"""
    print("AI客服系统英文本地化测试")
    print("=" * 50)

    test_language_support()
    test_translation_coverage()
    test_translation_quality()
    test_language_switching()

    print("\n" + "=" * 50)
    print("英文本地化测试完成")

if __name__ == "__main__":
    main()
