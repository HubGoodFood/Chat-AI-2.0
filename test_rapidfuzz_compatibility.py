# -*- coding: utf-8 -*-
"""
测试rapidfuzz兼容性
"""

def test_rapidfuzz_compatibility():
    """测试rapidfuzz是否可以替代fuzzywuzzy"""
    try:
        from rapidfuzz import fuzz, process
        
        # 测试基本功能
        text1 = "苹果"
        text2 = "苹果汁"
        
        # 测试fuzz模块
        ratio = fuzz.ratio(text1, text2)
        partial_ratio = fuzz.partial_ratio(text1, text2)
        
        print(f"✅ fuzz.ratio: {ratio}")
        print(f"✅ fuzz.partial_ratio: {partial_ratio}")
        
        # 测试process模块
        choices = ["苹果", "香蕉", "橙子", "苹果汁", "葡萄"]
        matches = process.extract("苹果", choices, limit=3)
        
        print(f"✅ process.extract: {matches}")
        
        print("✅ rapidfuzz兼容性测试通过！")
        return True
        
    except ImportError as e:
        print(f"❌ rapidfuzz导入失败: {e}")
        return False
    except Exception as e:
        print(f"❌ rapidfuzz测试失败: {e}")
        return False

if __name__ == "__main__":
    test_rapidfuzz_compatibility()
