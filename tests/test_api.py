"""
API测试脚本
"""
import requests
import json


def test_chat_api():
    """测试聊天API"""
    url = "http://localhost:5000/api/chat"
    
    test_messages = [
        "苹果多少钱？",
        "配送费用是多少？",
        "怎么付款？",
        "有什么蔬菜？"
    ]
    
    print("🔍 测试聊天API...")
    
    for message in test_messages:
        print(f"\n发送消息: {message}")
        
        try:
            response = requests.post(
                url,
                json={"message": message},
                headers={"Content-Type": "application/json"},
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    print(f"✅ 回复: {data['response'][:100]}...")
                else:
                    print(f"❌ 错误: {data.get('error', '未知错误')}")
            else:
                print(f"❌ HTTP错误: {response.status_code}")
                
        except requests.exceptions.RequestException as e:
            print(f"❌ 请求失败: {e}")
        except Exception as e:
            print(f"❌ 处理失败: {e}")


def test_health_api():
    """测试健康检查API"""
    url = "http://localhost:5000/health"
    
    print("\n🔍 测试健康检查API...")
    
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ 系统状态: {data['status']}")
            print(f"✅ 系统就绪: {data['system_ready']}")
        else:
            print(f"❌ HTTP错误: {response.status_code}")
    except Exception as e:
        print(f"❌ 健康检查失败: {e}")


def test_categories_api():
    """测试分类API"""
    url = "http://localhost:5000/api/categories"
    
    print("\n🔍 测试分类API...")
    
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                categories = data['categories']
                print(f"✅ 产品分类: {', '.join(categories)}")
            else:
                print(f"❌ 错误: {data.get('error', '未知错误')}")
        else:
            print(f"❌ HTTP错误: {response.status_code}")
    except Exception as e:
        print(f"❌ 分类API测试失败: {e}")


if __name__ == "__main__":
    print("🚀 开始API测试...")
    print("=" * 50)
    
    test_health_api()
    test_categories_api()
    test_chat_api()
    
    print("\n" + "=" * 50)
    print("✅ API测试完成！")
