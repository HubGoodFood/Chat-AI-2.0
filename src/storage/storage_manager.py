"""
统一存储管理器
支持多种存储后端的统一接口
"""
import json
import os
from datetime import datetime
from typing import Dict, Optional, Any
from enum import Enum


class StorageType(Enum):
    """存储类型枚举"""
    LOCAL = "local"
    NAS = "nas"
    GOOGLE_DRIVE = "google_drive"
    CLOUD_OSS = "cloud_oss"


class StorageManager:
    """
    统一存储管理器
    
    提供统一的存储接口，支持多种存储后端
    """
    
    def __init__(self, storage_type: StorageType = StorageType.LOCAL, **kwargs):
        """
        初始化存储管理器
        
        Args:
            storage_type: 存储类型
            **kwargs: 存储后端特定的配置参数
        """
        self.storage_type = storage_type
        self.storage_adapter = None
        
        # 根据存储类型初始化适配器
        self._initialize_adapter(**kwargs)
    
    def _initialize_adapter(self, **kwargs):
        """初始化存储适配器"""
        if self.storage_type == StorageType.LOCAL:
            self.storage_adapter = LocalStorageAdapter(**kwargs)
        elif self.storage_type == StorageType.NAS:
            from .nas_storage_adapter import NASStorageAdapter
            self.storage_adapter = NASStorageAdapter(**kwargs)
        else:
            raise ValueError(f"不支持的存储类型: {self.storage_type}")
    
    def save_data(self, filename: str, data: Dict) -> bool:
        """
        保存数据
        
        Args:
            filename: 文件名
            data: 要保存的数据
            
        Returns:
            bool: 是否保存成功
        """
        return self.storage_adapter.save_data(filename, data)
    
    def load_data(self, filename: str) -> Optional[Dict]:
        """
        加载数据
        
        Args:
            filename: 文件名
            
        Returns:
            Dict: 加载的数据，失败返回None
        """
        return self.storage_adapter.load_data(filename)
    
    def get_storage_info(self) -> Dict:
        """
        获取存储信息
        
        Returns:
            Dict: 存储状态信息
        """
        info = self.storage_adapter.get_storage_info()
        info["storage_type"] = self.storage_type.value
        return info


class LocalStorageAdapter:
    """
    本地存储适配器（原有的JSON文件存储）
    """
    
    def __init__(self, data_dir: str = "data"):
        """
        初始化本地存储适配器
        
        Args:
            data_dir: 数据目录
        """
        self.data_dir = data_dir
        os.makedirs(self.data_dir, exist_ok=True)
    
    def save_data(self, filename: str, data: Dict) -> bool:
        """保存数据到本地文件"""
        try:
            file_path = os.path.join(self.data_dir, filename)
            
            # 添加最后更新时间
            if isinstance(data, dict):
                data["last_updated"] = datetime.now().isoformat()
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            return True
            
        except Exception as e:
            print(f"保存本地数据失败: {e}")
            return False
    
    def load_data(self, filename: str) -> Optional[Dict]:
        """从本地文件加载数据"""
        try:
            file_path = os.path.join(self.data_dir, filename)
            
            if not os.path.exists(file_path):
                return None
            
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
                
        except Exception as e:
            print(f"加载本地数据失败: {e}")
            return None
    
    def get_storage_info(self) -> Dict:
        """获取本地存储信息"""
        try:
            files = [f for f in os.listdir(self.data_dir) if f.endswith('.json')]
            total_size = sum(
                os.path.getsize(os.path.join(self.data_dir, f)) 
                for f in files
            )
            
            return {
                "data_dir": self.data_dir,
                "files_count": len(files),
                "total_size_bytes": total_size,
                "total_size_mb": round(total_size / 1024 / 1024, 2)
            }
            
        except Exception as e:
            print(f"获取本地存储信息失败: {e}")
            return {
                "data_dir": self.data_dir,
                "files_count": 0,
                "total_size_bytes": 0,
                "total_size_mb": 0
            }


# 全局存储管理器实例
_storage_manager = None


def get_storage_manager() -> StorageManager:
    """获取全局存储管理器实例"""
    global _storage_manager
    if _storage_manager is None:
        # 默认使用本地存储
        _storage_manager = StorageManager(StorageType.LOCAL)
    return _storage_manager


def initialize_storage(storage_type: StorageType, **kwargs) -> bool:
    """
    初始化存储系统
    
    Args:
        storage_type: 存储类型
        **kwargs: 存储配置参数
        
    Returns:
        bool: 是否初始化成功
    """
    global _storage_manager
    try:
        _storage_manager = StorageManager(storage_type, **kwargs)
        print(f"存储系统初始化成功: {storage_type.value}")
        return True
    except Exception as e:
        print(f"存储系统初始化失败: {e}")
        return False


def migrate_to_nas(nas_path: str) -> bool:
    """
    迁移数据到NAS存储
    
    Args:
        nas_path: NAS存储路径
        
    Returns:
        bool: 是否迁移成功
    """
    try:
        # 获取当前的本地存储管理器
        current_manager = get_storage_manager()
        
        # 创建NAS存储管理器
        nas_manager = StorageManager(StorageType.NAS, nas_path=nas_path)
        
        # 获取本地数据文件列表
        local_data_dir = "data"
        if not os.path.exists(local_data_dir):
            print("本地数据目录不存在")
            return False
        
        json_files = [f for f in os.listdir(local_data_dir) if f.endswith('.json')]
        
        if not json_files:
            print("没有找到需要迁移的数据文件")
            return True
        
        migrated_count = 0
        failed_count = 0
        
        # 逐个迁移文件
        for filename in json_files:
            print(f"正在迁移: {filename}")
            
            # 从本地加载数据
            data = current_manager.load_data(filename)
            if data is None:
                print(f"加载本地文件失败: {filename}")
                failed_count += 1
                continue
            
            # 保存到NAS
            if nas_manager.save_data(filename, data):
                migrated_count += 1
                print(f"迁移成功: {filename}")
            else:
                failed_count += 1
                print(f"迁移失败: {filename}")
        
        print(f"\n迁移完成:")
        print(f"  - 成功: {migrated_count} 个文件")
        print(f"  - 失败: {failed_count} 个文件")
        
        if failed_count == 0:
            # 更新全局存储管理器
            global _storage_manager
            _storage_manager = nas_manager
            print("已切换到NAS存储")
            return True
        else:
            print("部分文件迁移失败，请检查后重试")
            return False
            
    except Exception as e:
        print(f"迁移到NAS失败: {e}")
        return False
