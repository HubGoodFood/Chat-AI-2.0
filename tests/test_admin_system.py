"""
管理员系统测试
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.models.admin_auth import AdminAuth
from src.models.inventory_manager import InventoryManager
from src.models.feedback_manager import FeedbackManager


def test_admin_auth():
    """测试管理员认证"""
    print("🔍 测试管理员认证...")
    
    auth = AdminAuth()
    
    # 测试登录
    token = auth.login("admin", "admin123")
    if token:
        print("✅ 管理员登录成功")
        
        # 测试会话验证
        if auth.verify_session(token):
            print("✅ 会话验证成功")
        else:
            print("❌ 会话验证失败")
            return False
        
        # 测试登出
        if auth.logout(token):
            print("✅ 管理员登出成功")
        else:
            print("❌ 管理员登出失败")
            return False
    else:
        print("❌ 管理员登录失败")
        return False
    
    return True


def test_inventory_manager():
    """测试库存管理"""
    print("\n🔍 测试库存管理...")
    
    inventory = InventoryManager()
    
    # 测试获取所有产品
    products = inventory.get_all_products()
    if products:
        print(f"✅ 获取产品列表成功，共 {len(products)} 个产品")
        
        # 测试获取单个产品
        first_product = products[0]
        product_id = first_product['product_id']
        product = inventory.get_product_by_id(product_id)
        
        if product:
            print(f"✅ 获取产品详情成功: {product['product_name']}")
            
            # 测试库存调整
            original_stock = product['current_stock']
            success = inventory.update_stock(product_id, 10, "测试员", "测试增加库存")
            
            if success:
                print("✅ 库存增加成功")
                
                # 恢复原始库存
                inventory.update_stock(product_id, -10, "测试员", "恢复原始库存")
                print("✅ 库存恢复成功")
            else:
                print("❌ 库存调整失败")
                return False
        else:
            print("❌ 获取产品详情失败")
            return False
    else:
        print("❌ 获取产品列表失败")
        return False
    
    # 测试库存汇总
    summary = inventory.get_inventory_summary()
    if summary:
        print(f"✅ 库存汇总成功: 总产品 {summary['total_products']} 个")
    else:
        print("❌ 库存汇总失败")
        return False
    
    return True


def test_feedback_manager():
    """测试反馈管理"""
    print("\n🔍 测试反馈管理...")
    
    feedback_mgr = FeedbackManager()
    
    # 测试添加反馈
    test_feedback = {
        "product_name": "测试产品",
        "customer_wechat_name": "测试客户",
        "customer_group_number": "测试群001",
        "payment_status": "已付款",
        "feedback_type": "positive",
        "feedback_content": "这是一个测试反馈",
        "customer_images": ["http://example.com/test.jpg"]
    }
    
    feedback_id = feedback_mgr.add_feedback(test_feedback)
    if feedback_id:
        print(f"✅ 添加反馈成功，ID: {feedback_id}")
        
        # 测试获取反馈详情
        feedback = feedback_mgr.get_feedback_by_id(feedback_id)
        if feedback:
            print(f"✅ 获取反馈详情成功: {feedback['product_name']}")
            
            # 测试更新反馈状态
            success = feedback_mgr.update_feedback_status(feedback_id, "处理中", "测试员", "正在处理中")
            if success:
                print("✅ 更新反馈状态成功")
                
                # 测试删除反馈
                if feedback_mgr.delete_feedback(feedback_id):
                    print("✅ 删除反馈成功")
                else:
                    print("❌ 删除反馈失败")
                    return False
            else:
                print("❌ 更新反馈状态失败")
                return False
        else:
            print("❌ 获取反馈详情失败")
            return False
    else:
        print("❌ 添加反馈失败")
        return False
    
    # 测试反馈统计
    stats = feedback_mgr.get_feedback_statistics()
    if stats:
        print(f"✅ 反馈统计成功: 总反馈 {stats['total_feedback']} 条")
    else:
        print("❌ 反馈统计失败")
        return False
    
    return True


def main():
    """主测试函数"""
    print("🧪 管理员系统测试开始")
    print("=" * 50)
    
    tests = [
        ("管理员认证", test_admin_auth),
        ("库存管理", test_inventory_manager),
        ("反馈管理", test_feedback_manager)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        try:
            if test_func():
                print(f"✅ {test_name} 测试通过")
                passed += 1
            else:
                print(f"❌ {test_name} 测试失败")
        except Exception as e:
            print(f"❌ {test_name} 测试异常: {e}")
    
    print("\n" + "=" * 50)
    print(f"🎯 测试结果: {passed}/{total} 通过")
    
    if passed == total:
        print("🎉 所有测试通过！管理员系统运行正常")
        return True
    else:
        print("⚠️ 部分测试失败，请检查系统配置")
        return False


if __name__ == "__main__":
    main()
