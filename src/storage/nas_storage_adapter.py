"""
Synology NAS存储适配器
支持通过网络共享访问NAS存储
"""
import json
import os
import shutil
from datetime import datetime
from typing import Dict, Optional
import platform


class NASStorageAdapter:
    """
    NAS存储适配器
    
    支持两种连接方式：
    1. 网络映射驱动器（Windows）
    2. 挂载点（Linux/Mac）
    """
    
    def __init__(self, nas_path: str, backup_enabled: bool = True):
        """
        初始化NAS存储适配器
        
        Args:
            nas_path: NAS存储路径
                Windows示例: "Z:\\ChatAI_Data"
                Linux示例: "/mnt/nas/ChatAI_Data"
            backup_enabled: 是否启用本地备份
        """
        self.nas_path = nas_path
        self.backup_enabled = backup_enabled
        self.local_backup_path = 'data_backup'
        self.connection_timeout = 10  # 连接超时时间（秒）
        
        # 确保目录存在
        self._ensure_directories()
    
    def _ensure_directories(self):
        """确保必要的目录存在"""
        try:
            # 创建NAS目录
            os.makedirs(self.nas_path, exist_ok=True)
            
            # 创建本地备份目录
            if self.backup_enabled:
                os.makedirs(self.local_backup_path, exist_ok=True)
            
            print(f"NAS存储路径已准备: {self.nas_path}")
            
        except Exception as e:
            print(f"创建NAS目录失败: {e}")
            raise
    
    def is_nas_available(self) -> bool:
        """
        检查NAS是否可用
        
        Returns:
            bool: NAS是否可访问
        """
        try:
            # 尝试在NAS路径创建测试文件
            test_file = os.path.join(self.nas_path, '.connection_test')
            with open(test_file, 'w') as f:
                f.write(datetime.now().isoformat())
            
            # 立即删除测试文件
            os.remove(test_file)
            return True
            
        except Exception as e:
            print(f"NAS连接测试失败: {e}")
            return False
    
    def save_data(self, filename: str, data: Dict) -> bool:
        """
        保存数据到NAS
        
        Args:
            filename: 文件名
            data: 要保存的数据
            
        Returns:
            bool: 是否保存成功
        """
        try:
            nas_file_path = os.path.join(self.nas_path, filename)
            
            # 保存到NAS
            with open(nas_file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            # 本地备份
            if self.backup_enabled:
                self._create_local_backup(filename, data)
            
            print(f"数据已保存到NAS: {filename}")
            return True
            
        except Exception as e:
            print(f"保存数据到NAS失败: {e}")
            
            # 如果NAS保存失败，尝试保存到本地备份
            if self.backup_enabled:
                return self._save_to_local_backup(filename, data)
            
            return False
    
    def load_data(self, filename: str) -> Optional[Dict]:
        """
        从NAS加载数据
        
        Args:
            filename: 文件名
            
        Returns:
            Dict: 加载的数据，失败返回None
        """
        try:
            nas_file_path = os.path.join(self.nas_path, filename)
            
            # 首先尝试从NAS加载
            if os.path.exists(nas_file_path):
                with open(nas_file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                return data
            
            # 如果NAS文件不存在，尝试从本地备份加载
            if self.backup_enabled:
                return self._load_from_local_backup(filename)
            
            return None
            
        except Exception as e:
            print(f"从NAS加载数据失败: {e}")
            
            # 如果NAS加载失败，尝试从本地备份加载
            if self.backup_enabled:
                return self._load_from_local_backup(filename)
            
            return None
    
    def _create_local_backup(self, filename: str, data: Dict):
        """创建本地备份"""
        try:
            backup_file_path = os.path.join(self.local_backup_path, filename)
            with open(backup_file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            # 创建带时间戳的备份
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            timestamped_filename = f"{filename}.{timestamp}.bak"
            timestamped_path = os.path.join(self.local_backup_path, timestamped_filename)
            shutil.copy2(backup_file_path, timestamped_path)
            
        except Exception as e:
            print(f"创建本地备份失败: {e}")
    
    def _save_to_local_backup(self, filename: str, data: Dict) -> bool:
        """保存到本地备份"""
        try:
            backup_file_path = os.path.join(self.local_backup_path, filename)
            with open(backup_file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            print(f"数据已保存到本地备份: {filename}")
            return True
            
        except Exception as e:
            print(f"保存到本地备份失败: {e}")
            return False
    
    def _load_from_local_backup(self, filename: str) -> Optional[Dict]:
        """从本地备份加载数据"""
        try:
            backup_file_path = os.path.join(self.local_backup_path, filename)
            
            if os.path.exists(backup_file_path):
                with open(backup_file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                print(f"从本地备份加载数据: {filename}")
                return data
            
            return None
            
        except Exception as e:
            print(f"从本地备份加载数据失败: {e}")
            return None
    
    def sync_to_nas(self) -> bool:
        """
        将本地备份同步到NAS
        
        Returns:
            bool: 是否同步成功
        """
        if not self.backup_enabled:
            return False
        
        try:
            if not self.is_nas_available():
                print("NAS不可用，无法同步")
                return False
            
            sync_count = 0
            
            # 遍历本地备份文件
            for filename in os.listdir(self.local_backup_path):
                if filename.endswith('.json'):
                    local_path = os.path.join(self.local_backup_path, filename)
                    nas_path = os.path.join(self.nas_path, filename)
                    
                    # 复制到NAS
                    shutil.copy2(local_path, nas_path)
                    sync_count += 1
            
            print(f"已同步 {sync_count} 个文件到NAS")
            return True
            
        except Exception as e:
            print(f"同步到NAS失败: {e}")
            return False
    
    def get_storage_info(self) -> Dict:
        """
        获取存储信息
        
        Returns:
            Dict: 存储状态信息
        """
        info = {
            "nas_path": self.nas_path,
            "nas_available": self.is_nas_available(),
            "backup_enabled": self.backup_enabled,
            "local_backup_path": self.local_backup_path,
            "platform": platform.system()
        }
        
        # 获取文件统计
        try:
            if info["nas_available"]:
                nas_files = [f for f in os.listdir(self.nas_path) if f.endswith('.json')]
                info["nas_files_count"] = len(nas_files)
            else:
                info["nas_files_count"] = 0
            
            if self.backup_enabled and os.path.exists(self.local_backup_path):
                backup_files = [f for f in os.listdir(self.local_backup_path) if f.endswith('.json')]
                info["backup_files_count"] = len(backup_files)
            else:
                info["backup_files_count"] = 0
                
        except Exception as e:
            print(f"获取文件统计失败: {e}")
            info["nas_files_count"] = 0
            info["backup_files_count"] = 0
        
        return info
