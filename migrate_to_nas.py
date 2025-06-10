#!/usr/bin/env python3
"""
数据迁移工具 - 迁移到Synology NAS
"""
import sys
import os

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.storage.storage_manager import migrate_to_nas, StorageType, initialize_storage


def main():
    """主函数"""
    print("=" * 60)
    print("AI客服系统 - NAS数据迁移工具")
    print("=" * 60)
    
    print("\n此工具将帮助您将数据从本地JSON文件迁移到Synology NAS存储")
    print("\n迁移前准备工作：")
    print("1. 确保您的Synology NAS已正确配置")
    print("2. 确保已映射NAS网络驱动器（Windows）或挂载NAS（Linux/Mac）")
    print("3. 确保有足够的权限读写NAS目录")
    
    # 获取用户输入的NAS路径
    print("\n请输入NAS存储路径：")
    print("Windows示例: Z:\\ChatAI_Data")
    print("Linux示例: /mnt/nas/ChatAI_Data")
    print("Mac示例: /Volumes/nas/ChatAI_Data")
    
    nas_path = input("\nNAS路径: ").strip()
    
    if not nas_path:
        print("错误：NAS路径不能为空")
        return False
    
    # 验证路径格式
    if not os.path.isabs(nas_path):
        print("错误：请提供绝对路径")
        return False
    
    print(f"\n您输入的NAS路径: {nas_path}")
    
    # 确认操作
    confirm = input("\n确认开始迁移吗？(y/N): ").strip().lower()
    if confirm not in ['y', 'yes']:
        print("迁移已取消")
        return False
    
    print("\n开始迁移...")
    
    try:
        # 执行迁移
        success = migrate_to_nas(nas_path)
        
        if success:
            print("\n" + "=" * 60)
            print("迁移成功完成！")
            print("=" * 60)
            print("\n后续步骤：")
            print("1. 验证NAS中的数据文件是否完整")
            print("2. 备份原始的本地数据文件")
            print("3. 更新系统配置以使用NAS存储")
            print("4. 测试系统功能是否正常")
            
            # 提供配置建议
            print(f"\n配置建议：")
            print(f"在系统启动时添加以下配置：")
            print(f"```python")
            print(f"from src.storage.storage_manager import initialize_storage, StorageType")
            print(f"initialize_storage(StorageType.NAS, nas_path='{nas_path}')")
            print(f"```")
            
        else:
            print("\n" + "=" * 60)
            print("迁移失败！")
            print("=" * 60)
            print("\n可能的原因：")
            print("1. NAS路径不存在或无法访问")
            print("2. 权限不足，无法写入NAS目录")
            print("3. 网络连接问题")
            print("4. 磁盘空间不足")
            print("\n请检查上述问题后重试")
            
        return success
        
    except Exception as e:
        print(f"\n迁移过程中出现错误: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_nas_connection(nas_path: str):
    """测试NAS连接"""
    print(f"\n测试NAS连接: {nas_path}")
    
    try:
        # 尝试初始化NAS存储
        success = initialize_storage(StorageType.NAS, nas_path=nas_path)
        
        if success:
            print("NAS连接测试成功！")
            
            # 获取存储信息
            from src.storage.storage_manager import get_storage_manager
            storage_manager = get_storage_manager()
            info = storage_manager.get_storage_info()
            
            print("NAS存储信息：")
            print(f"  - 路径: {info.get('nas_path')}")
            print(f"  - 可用性: {info.get('nas_available')}")
            print(f"  - 文件数量: {info.get('nas_files_count', 0)}")
            print(f"  - 备份启用: {info.get('backup_enabled')}")
            
            return True
        else:
            print("NAS连接测试失败！")
            return False
            
    except Exception as e:
        print(f"NAS连接测试出错: {e}")
        return False


if __name__ == "__main__":
    # 检查命令行参数
    if len(sys.argv) > 1:
        if sys.argv[1] == "test":
            # 测试模式
            if len(sys.argv) > 2:
                nas_path = sys.argv[2]
                test_nas_connection(nas_path)
            else:
                print("用法: python migrate_to_nas.py test <NAS路径>")
        else:
            print("未知参数，使用交互模式")
            main()
    else:
        # 交互模式
        success = main()
        if success:
            print("\n迁移工具执行完成")
        else:
            print("\n迁移工具执行失败")
            sys.exit(1)
