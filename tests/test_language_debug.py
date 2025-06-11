#!/usr/bin/env python3
"""
语言切换功能调试测试脚本
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from flask import Flask, session
from src.utils.i18n_simple import i18n_simple, _

def test_language_switching():
    """测试语言切换功能"""
    print("=== 语言切换功能调试测试 ===\n")
    
    # 创建测试Flask应用
    app = Flask(__name__)
    app.secret_key = 'test_secret_key'
    
    # 初始化i18n
    i18n_simple.init_app(app)
    
    with app.test_request_context():
        print("1. 测试默认语言设置")
        print(f"   默认语言: {i18n_simple.get_locale()}")
        current_lang = i18n_simple.get_current_language()
        print(f"   当前语言代码: {current_lang.get('code', 'unknown')}")
        print(f"   当前语言名称: {current_lang.get('name', 'unknown')}")
        available_langs = i18n_simple.get_available_languages()
        print(f"   可用语言数量: {len(available_langs)}")
        for lang in available_langs:
            print(f"     - {lang.get('code')}: {lang.get('name')}")
        print()
        
        print("2. 测试中文翻译")
        test_text = "管理员登录"
        translated = _(test_text)
        print(f"   原文: {test_text}")
        print(f"   翻译: {translated}")
        print()
        
        print("3. 测试切换到英文")
        success = i18n_simple.set_language('en')
        print(f"   切换结果: {success}")
        print(f"   当前语言: {i18n_simple.get_locale()}")
        print(f"   Session内容: {dict(session)}")
        print()
        
        print("4. 测试英文翻译")
        translated_en = _(test_text)
        print(f"   原文: {test_text}")
        print(f"   英文翻译: {translated_en}")
        print()
        
        print("5. 测试更多翻译")
        test_texts = [
            "管理后台",
            "库存管理", 
            "产品入库",
            "库存盘点",
            "数据对比分析",
            "用户名",
            "密码",
            "登录",
            "退出登录"
        ]
        
        for text in test_texts:
            zh_text = i18n_simple.translate(text, 'zh')
            en_text = i18n_simple.translate(text, 'en')
            print(f"   {text}: 中文={zh_text}, 英文={en_text}")
        print()
        
        print("6. 测试切换回中文")
        success = i18n_simple.set_language('zh')
        print(f"   切换结果: {success}")
        print(f"   当前语言: {i18n_simple.get_locale()}")
        print(f"   Session内容: {dict(session)}")
        print()
        
        print("7. 测试无效语言")
        success = i18n_simple.set_language('fr')
        print(f"   切换到法语结果: {success}")
        print(f"   当前语言: {i18n_simple.get_locale()}")
        print()

def test_translation_coverage():
    """测试翻译覆盖率"""
    print("=== 翻译覆盖率测试 ===\n")
    
    # 检查英文翻译字典
    en_translations = i18n_simple.translations.get('en', {})
    print(f"英文翻译条目数: {len(en_translations)}")
    
    # 测试一些关键翻译
    key_texts = [
        "管理员登录",
        "果蔬客服AI系统后台管理", 
        "用户名",
        "密码",
        "登录",
        "管理后台",
        "控制台",
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
    missing_translations = []
    for text in key_texts:
        if text in en_translations:
            print(f"   [OK] {text} -> {en_translations[text]}")
        else:
            print(f"   [MISS] {text} -> 缺少翻译")
            missing_translations.append(text)

    if missing_translations:
        print(f"\n缺少翻译的文本: {missing_translations}")
    else:
        print("\n[OK] 所有关键文本都有翻译")

if __name__ == '__main__':
    test_language_switching()
    print("\n" + "="*50 + "\n")
    test_translation_coverage()
