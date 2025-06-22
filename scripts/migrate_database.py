#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据库迁移脚本
"""
import os
import sys
import argparse
import logging
from datetime import datetime

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.database.database_config import db_config, init_database
from src.services.data_migration import migration_service

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(f'migration_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log')
    ]
)

logger = logging.getLogger(__name__)


def create_tables():
    """创建数据库表"""
    print("🔧 正在创建数据库表...")
    try:
        success = init_database()
        if success:
            print("✅ 数据库表创建成功")
            return True
        else:
            print("❌ 数据库表创建失败")
            return False
    except Exception as e:
        print(f"❌ 数据库表创建异常: {e}")
        return False


def migrate_data():
    """迁移数据"""
    print("📦 正在迁移数据...")
    try:
        results = migration_service.migrate_all_data()
        
        print("\n📊 迁移结果:")
        print(f"  • 产品: {results['products']} 条")
        print(f"  • 管理员用户: {results['admin_users']} 条")
        print(f"  • 客户反馈: {results['feedback']} 条")
        print(f"  • 存储区域: {results['storage_areas']} 条")
        print(f"  • 取货点: {results['pickup_locations']} 条")
        print(f"  • 操作日志: {results['operation_logs']} 条")
        
        if results['errors']:
            print(f"\n⚠️  迁移过程中的错误:")
            for error in results['errors']:
                print(f"  • {error}")
        
        total_migrated = sum([
            results['products'],
            results['admin_users'],
            results['feedback'],
            results['storage_areas'],
            results['pickup_locations'],
            results['operation_logs']
        ])
        
        if total_migrated > 0:
            print(f"\n✅ 数据迁移完成，共迁移 {total_migrated} 条记录")
            return True
        else:
            print("\n⚠️  没有数据被迁移")
            return True
            
    except Exception as e:
        print(f"❌ 数据迁移失败: {e}")
        return False


def verify_migration():
    """验证迁移结果"""
    print("🔍 正在验证迁移结果...")
    try:
        results = migration_service.verify_migration()
        
        if 'error' in results:
            print(f"❌ 验证失败: {results['error']}")
            return False
        
        print("\n📈 数据库状态:")
        print(f"  • 产品总数: {results.get('products_count', 0)}")
        print(f"  • 管理员用户: {results.get('admin_users_count', 0)}")
        print(f"  • 客户反馈: {results.get('feedback_count', 0)}")
        print(f"  • 存储区域: {results.get('storage_areas_count', 0)}")
        print(f"  • 取货点: {results.get('pickup_locations_count', 0)}")
        print(f"  • 操作日志: {results.get('operation_logs_count', 0)}")
        print(f"  • 库存历史: {results.get('stock_history_count', 0)}")
        
        consistency = results.get('data_consistency', {})
        print(f"\n📋 数据一致性:")
        print(f"  • 有库存历史的产品: {consistency.get('products_with_stock_history', 0)}")
        
        print("\n✅ 迁移验证完成")
        return True
        
    except Exception as e:
        print(f"❌ 验证失败: {e}")
        return False


def test_database_connection():
    """测试数据库连接"""
    print("🔗 正在测试数据库连接...")
    try:
        if db_config.health_check():
            print("✅ 数据库连接正常")
            
            conn_info = db_config.get_connection_info()
            print(f"  • 数据库URL: {conn_info['database_url']}")
            if conn_info['pool_size']:
                print(f"  • 连接池大小: {conn_info['pool_size']}")
                print(f"  • 当前连接数: {conn_info['checked_out']}")
            
            return True
        else:
            print("❌ 数据库连接失败")
            return False
    except Exception as e:
        print(f"❌ 数据库连接测试异常: {e}")
        return False


def rollback_migration():
    """回滚迁移"""
    print("⏮️  正在回滚数据库迁移...")
    
    # 确认操作
    confirm = input("⚠️  这将删除所有数据库数据，确认继续？(yes/no): ")
    if confirm.lower() != 'yes':
        print("❌ 操作已取消")
        return False
    
    try:
        success = migration_service.rollback_migration()
        if success:
            print("✅ 数据库迁移已回滚")
            return True
        else:
            print("❌ 数据库迁移回滚失败")
            return False
    except Exception as e:
        print(f"❌ 回滚异常: {e}")
        return False


def full_migration():
    """完整迁移流程"""
    print("🚀 开始完整数据库迁移流程")
    print("=" * 50)
    
    steps = [
        ("测试数据库连接", test_database_connection),
        ("创建数据库表", create_tables),
        ("迁移数据", migrate_data),
        ("验证迁移结果", verify_migration)
    ]
    
    for step_name, step_func in steps:
        print(f"\n📍 步骤: {step_name}")
        print("-" * 30)
        
        success = step_func()
        if not success:
            print(f"❌ 步骤失败: {step_name}")
            print("💡 请检查错误信息并修复后重试")
            return False
    
    print("\n" + "=" * 50)
    print("🎉 数据库迁移完成！")
    print("\n💡 后续步骤:")
    print("  1. 运行应用程序测试迁移后的功能")
    print("  2. 如果一切正常，可以考虑删除JSON备份文件")
    print("  3. 更新部署配置以使用新的数据库设置")
    
    return True


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='数据库迁移工具')
    parser.add_argument('action', 
                       choices=['test', 'create', 'migrate', 'verify', 'rollback', 'full'],
                       help='要执行的操作')
    
    args = parser.parse_args()
    
    print("🔄 数据库迁移工具")
    print("=" * 50)
    
    if args.action == 'test':
        success = test_database_connection()
    elif args.action == 'create':
        success = create_tables()
    elif args.action == 'migrate':
        success = migrate_data()
    elif args.action == 'verify':
        success = verify_migration()
    elif args.action == 'rollback':
        success = rollback_migration()
    elif args.action == 'full':
        success = full_migration()
    else:
        print(f"❌ 未知操作: {args.action}")
        success = False
    
    if success:
        print(f"\n✅ 操作 '{args.action}' 执行成功")
        return 0
    else:
        print(f"\n❌ 操作 '{args.action}' 执行失败")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)