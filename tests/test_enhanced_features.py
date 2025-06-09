"""
增强功能测试 - 测试操作日志和数据导出功能
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.models.operation_logger import operation_logger, log_admin_operation
from src.models.data_exporter import data_exporter
from src.models.inventory_manager import InventoryManager
from src.models.feedback_manager import FeedbackManager


def test_operation_logger():
    """测试操作日志功能"""
    print("🔍 测试操作日志功能...")
    
    # 测试记录操作日志
    log_admin_operation(
        operator="测试员",
        operation_type="test",
        target_type="system",
        target_id="test_001",
        details={"action": "测试操作日志", "value": 123},
        result="success"
    )
    
    # 测试获取日志
    logs = operation_logger.get_logs(limit=10)
    if logs and len(logs) > 0:
        print(f"✅ 操作日志记录成功，共 {len(logs)} 条日志")
        
        # 测试日志统计
        stats = operation_logger.get_operation_statistics(days=7)
        if stats:
            print(f"✅ 日志统计成功: 总操作 {stats['total_operations']} 次")
        else:
            print("❌ 日志统计失败")
            return False
    else:
        print("❌ 操作日志记录失败")
        return False
    
    return True


def test_data_exporter():
    """测试数据导出功能"""
    print("\n🔍 测试数据导出功能...")
    
    # 准备测试数据
    inventory_manager = InventoryManager()
    feedback_manager = FeedbackManager()
    
    # 获取测试数据
    inventory_data = inventory_manager.get_all_products()
    feedback_data = feedback_manager.get_all_feedback()
    log_data = operation_logger.get_logs(limit=10)
    
    # 测试库存数据导出
    csv_data = data_exporter.export_inventory_to_csv(inventory_data)
    if csv_data:
        print(f"✅ 库存CSV导出成功，数据长度: {len(csv_data)} 字符")
    else:
        print("❌ 库存CSV导出失败")
        return False
    
    # 测试反馈数据导出
    feedback_csv = data_exporter.export_feedback_to_csv(feedback_data)
    if feedback_csv is not None:  # 可能为空字符串
        print(f"✅ 反馈CSV导出成功，数据长度: {len(feedback_csv)} 字符")
    else:
        print("❌ 反馈CSV导出失败")
        return False
    
    # 测试日志导出
    log_csv = data_exporter.export_logs_to_csv(log_data)
    if log_csv:
        print(f"✅ 日志CSV导出成功，数据长度: {len(log_csv)} 字符")
    else:
        print("❌ 日志CSV导出失败")
        return False
    
    # 测试JSON导出
    json_data = data_exporter.export_to_json(inventory_data[:5])  # 只导出前5个产品
    if json_data:
        print(f"✅ JSON导出成功，数据长度: {len(json_data)} 字符")
    else:
        print("❌ JSON导出失败")
        return False
    
    return True


def test_report_generation():
    """测试报告生成功能"""
    print("\n🔍 测试报告生成功能...")
    
    inventory_manager = InventoryManager()
    feedback_manager = FeedbackManager()
    
    # 获取数据
    inventory_data = inventory_manager.get_all_products()
    inventory_summary = inventory_manager.get_inventory_summary()
    feedback_data = feedback_manager.get_all_feedback()
    feedback_stats = feedback_manager.get_feedback_statistics()
    
    # 测试库存报告生成
    inventory_report = data_exporter.generate_inventory_report(inventory_data, inventory_summary)
    if inventory_report:
        print(f"✅ 库存报告生成成功，报告长度: {len(inventory_report)} 字符")
        
        # 检查报告内容
        if "库存管理报告" in inventory_report and "库存汇总" in inventory_report:
            print("✅ 库存报告内容完整")
        else:
            print("❌ 库存报告内容不完整")
            return False
    else:
        print("❌ 库存报告生成失败")
        return False
    
    # 测试反馈报告生成
    feedback_report = data_exporter.generate_feedback_report(feedback_data, feedback_stats)
    if feedback_report:
        print(f"✅ 反馈报告生成成功，报告长度: {len(feedback_report)} 字符")
        
        # 检查报告内容
        if "客户反馈报告" in feedback_report and "反馈汇总" in feedback_report:
            print("✅ 反馈报告内容完整")
        else:
            print("❌ 反馈报告内容不完整")
            return False
    else:
        print("❌ 反馈报告生成失败")
        return False
    
    return True


def test_backup_creation():
    """测试备份创建功能"""
    print("\n🔍 测试备份创建功能...")
    
    inventory_manager = InventoryManager()
    feedback_manager = FeedbackManager()
    
    # 获取所有数据
    inventory_data = inventory_manager.get_all_products()
    feedback_data = feedback_manager.get_all_feedback()
    log_data = operation_logger.get_logs(limit=50)
    
    # 创建备份
    backup_data = data_exporter.create_backup_data(inventory_data, feedback_data, log_data)
    
    if backup_data and 'backup_info' in backup_data:
        print("✅ 备份数据创建成功")
        
        # 检查备份内容
        required_keys = ['backup_info', 'inventory', 'feedback', 'operation_logs']
        if all(key in backup_data for key in required_keys):
            print("✅ 备份数据结构完整")
            print(f"   - 库存数据: {len(backup_data['inventory'])} 条")
            print(f"   - 反馈数据: {len(backup_data['feedback'])} 条")
            print(f"   - 日志数据: {len(backup_data['operation_logs'])} 条")
        else:
            print("❌ 备份数据结构不完整")
            return False
    else:
        print("❌ 备份数据创建失败")
        return False
    
    return True


def test_integration_workflow():
    """测试集成工作流程"""
    print("\n🔍 测试集成工作流程...")
    
    inventory_manager = InventoryManager()
    
    # 模拟一个完整的操作流程
    try:
        # 1. 获取产品信息
        products = inventory_manager.get_all_products()
        if not products:
            print("❌ 无法获取产品信息")
            return False
        
        first_product = products[0]
        product_id = first_product['product_id']
        
        # 2. 记录查看操作
        log_admin_operation(
            operator="测试员",
            operation_type="view",
            target_type="inventory",
            target_id=product_id,
            details={"product_name": first_product['product_name']}
        )
        
        # 3. 模拟库存调整
        original_stock = first_product['current_stock']
        success = inventory_manager.update_stock(product_id, 5, "测试员", "集成测试库存调整")
        
        if success:
            # 4. 记录库存调整操作
            log_admin_operation(
                operator="测试员",
                operation_type="update_stock",
                target_type="inventory",
                target_id=product_id,
                details={
                    "quantity_change": 5,
                    "original_stock": original_stock,
                    "new_stock": original_stock + 5,
                    "note": "集成测试库存调整"
                }
            )
            
            # 5. 恢复原始库存
            inventory_manager.update_stock(product_id, -5, "测试员", "恢复原始库存")
            
            print("✅ 集成工作流程测试成功")
        else:
            print("❌ 库存调整失败")
            return False
        
        # 6. 验证日志记录
        recent_logs = operation_logger.get_logs(limit=5)
        test_logs = [log for log in recent_logs if log['operator'] == '测试员']
        
        if len(test_logs) >= 2:
            print(f"✅ 操作日志记录正常，共 {len(test_logs)} 条测试日志")
        else:
            print("❌ 操作日志记录异常")
            return False
        
    except Exception as e:
        print(f"❌ 集成测试异常: {e}")
        return False
    
    return True


def main():
    """主测试函数"""
    print("🧪 增强功能测试开始")
    print("=" * 60)
    
    tests = [
        ("操作日志功能", test_operation_logger),
        ("数据导出功能", test_data_exporter),
        ("报告生成功能", test_report_generation),
        ("备份创建功能", test_backup_creation),
        ("集成工作流程", test_integration_workflow)
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
    
    print("\n" + "=" * 60)
    print(f"🎯 测试结果: {passed}/{total} 通过")
    
    if passed == total:
        print("🎉 所有增强功能测试通过！系统功能完整")
        return True
    else:
        print("⚠️ 部分测试失败，请检查系统配置")
        return False


if __name__ == "__main__":
    main()
