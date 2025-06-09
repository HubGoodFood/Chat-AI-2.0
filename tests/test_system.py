"""
果蔬客服AI系统测试脚本
"""
import sys
import time
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.models.knowledge_retriever import KnowledgeRetriever


def test_data_loading():
    """测试数据加载"""
    print("🔍 测试数据加载...")
    try:
        retriever = KnowledgeRetriever()
        retriever.initialize()
        
        # 检查产品数据
        categories = retriever.get_product_categories()
        print(f"✅ 产品类别数量: {len(categories)}")
        print(f"   类别列表: {', '.join(categories)}")
        
        # 检查政策数据
        quick_answers = retriever.get_quick_answers()
        print(f"✅ 快速回答数量: {len(quick_answers)}")
        
        return True
    except Exception as e:
        print(f"❌ 数据加载失败: {e}")
        return False


def test_product_search():
    """测试产品搜索功能"""
    print("\n🔍 测试产品搜索功能...")
    
    retriever = KnowledgeRetriever()
    retriever.initialize()
    
    test_queries = [
        "苹果",
        "蔬菜",
        "鸡蛋",
        "海鲜",
        "水果",
        "不存在的产品"
    ]
    
    for query in test_queries:
        print(f"\n搜索: '{query}'")
        result = retriever.retrieve_information(query)
        
        if result['has_product_info']:
            products = result['products'][:2]  # 显示前2个结果
            for product in products:
                print(f"  ✅ 找到: {product['name']} - ${product['price']}/{product['unit']}")
        else:
            print(f"  ❌ 未找到相关产品")


def test_policy_search():
    """测试政策搜索功能"""
    print("\n🔍 测试政策搜索功能...")
    
    retriever = KnowledgeRetriever()
    retriever.initialize()
    
    test_queries = [
        "配送",
        "付款",
        "取货",
        "退款",
        "质量问题",
        "运费"
    ]
    
    for query in test_queries:
        print(f"\n搜索: '{query}'")
        result = retriever.retrieve_information(query)
        
        if result['has_policy_info']:
            policies = result['policies'][:1]  # 显示第1个结果
            for policy in policies:
                print(f"  ✅ 找到政策: {policy['section']}")
        else:
            print(f"  ❌ 未找到相关政策")


def test_ai_responses():
    """测试AI回答功能"""
    print("\n🔍 测试AI回答功能...")
    
    retriever = KnowledgeRetriever()
    retriever.initialize()
    
    test_questions = [
        "苹果多少钱？",
        "配送费用是多少？",
        "怎么付款？",
        "有什么蔬菜？",
        "质量有问题怎么办？",
        "取货地点在哪里？"
    ]
    
    for question in test_questions:
        print(f"\n问题: {question}")
        print("回答: ", end="")
        
        try:
            answer = retriever.answer_question(question)
            # 显示回答的前100个字符
            preview = answer[:100] + "..." if len(answer) > 100 else answer
            print(f"✅ {preview}")
        except Exception as e:
            print(f"❌ 回答失败: {e}")


def test_system_performance():
    """测试系统性能"""
    print("\n🔍 测试系统性能...")
    
    retriever = KnowledgeRetriever()
    retriever.initialize()
    
    # 测试响应时间
    test_question = "苹果多少钱？"
    
    times = []
    for i in range(3):
        start_time = time.time()
        retriever.answer_question(test_question)
        end_time = time.time()
        response_time = end_time - start_time
        times.append(response_time)
        print(f"  第{i+1}次响应时间: {response_time:.2f}秒")
    
    avg_time = sum(times) / len(times)
    print(f"✅ 平均响应时间: {avg_time:.2f}秒")
    
    if avg_time < 5.0:
        print("✅ 性能良好")
    else:
        print("⚠️ 响应时间较长，建议优化")


def run_all_tests():
    """运行所有测试"""
    print("🚀 开始运行果蔬客服AI系统测试...")
    print("=" * 50)
    
    tests = [
        ("数据加载", test_data_loading),
        ("产品搜索", test_product_search),
        ("政策搜索", test_policy_search),
        ("AI回答", test_ai_responses),
        ("系统性能", test_system_performance)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n{'='*20} {test_name} {'='*20}")
        try:
            result = test_func()
            if result is not False:
                passed += 1
                print(f"✅ {test_name}测试通过")
            else:
                print(f"❌ {test_name}测试失败")
        except Exception as e:
            print(f"❌ {test_name}测试出错: {e}")
    
    print("\n" + "=" * 50)
    print(f"🎯 测试结果: {passed}/{total} 通过")
    
    if passed == total:
        print("🎉 所有测试通过！系统运行正常。")
    else:
        print("⚠️ 部分测试失败，请检查系统配置。")
    
    return passed == total


if __name__ == "__main__":
    if len(sys.argv) > 1:
        test_name = sys.argv[1].lower()
        
        if test_name == "data":
            test_data_loading()
        elif test_name == "product":
            test_product_search()
        elif test_name == "policy":
            test_policy_search()
        elif test_name == "ai":
            test_ai_responses()
        elif test_name == "performance":
            test_system_performance()
        else:
            print("可用的测试选项: data, product, policy, ai, performance")
    else:
        run_all_tests()
