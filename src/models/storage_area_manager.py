"""
存储区域管理模块
支持动态添加、删除、修改存储区域
"""
import json
import os
from datetime import datetime
from typing import List, Dict, Optional


class StorageAreaManager:
    """
    存储区域管理器
    
    主要功能：
    1. 动态管理存储区域（增删改查）
    2. 验证存储区域的有效性
    3. 提供存储区域的统计信息
    4. 确保数据一致性
    """
    
    def __init__(self):
        self.storage_areas_file = 'data/storage_areas.json'
        self._ensure_storage_areas_file()
    
    def _ensure_storage_areas_file(self):
        """确保存储区域配置文件存在"""
        if not os.path.exists(self.storage_areas_file):
            self._initialize_storage_areas_file()
    
    def _initialize_storage_areas_file(self):
        """初始化存储区域配置文件"""
        try:
            # 默认的存储区域配置
            initial_data = {
                "last_updated": datetime.now().isoformat(),
                "areas": {
                    "A": {
                        "area_id": "A",
                        "area_name": "A区",
                        "description": "主要存储区域A",
                        "capacity": 1000,  # 容量（可选）
                        "status": "active",  # active, inactive
                        "created_at": datetime.now().isoformat(),
                        "updated_at": datetime.now().isoformat()
                    },
                    "B": {
                        "area_id": "B", 
                        "area_name": "B区",
                        "description": "主要存储区域B",
                        "capacity": 1000,
                        "status": "active",
                        "created_at": datetime.now().isoformat(),
                        "updated_at": datetime.now().isoformat()
                    },
                    "C": {
                        "area_id": "C",
                        "area_name": "C区", 
                        "description": "主要存储区域C",
                        "capacity": 1000,
                        "status": "active",
                        "created_at": datetime.now().isoformat(),
                        "updated_at": datetime.now().isoformat()
                    },
                    "D": {
                        "area_id": "D",
                        "area_name": "D区",
                        "description": "主要存储区域D", 
                        "capacity": 1000,
                        "status": "active",
                        "created_at": datetime.now().isoformat(),
                        "updated_at": datetime.now().isoformat()
                    }
                }
            }
            
            os.makedirs(os.path.dirname(self.storage_areas_file), exist_ok=True)
            with open(self.storage_areas_file, 'w', encoding='utf-8') as f:
                json.dump(initial_data, f, ensure_ascii=False, indent=2)
            
            print("存储区域配置文件初始化完成")
            
        except Exception as e:
            print(f"初始化存储区域配置文件失败: {e}")
    
    def _load_storage_areas(self) -> Dict:
        """加载存储区域配置"""
        try:
            with open(self.storage_areas_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"加载存储区域配置失败: {e}")
            return {"last_updated": datetime.now().isoformat(), "areas": {}}
    
    def _save_storage_areas(self, areas_data: Dict):
        """保存存储区域配置"""
        try:
            areas_data["last_updated"] = datetime.now().isoformat()
            with open(self.storage_areas_file, 'w', encoding='utf-8') as f:
                json.dump(areas_data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"保存存储区域配置失败: {e}")
    
    def get_all_areas(self, include_inactive: bool = False) -> List[Dict]:
        """
        获取所有存储区域
        
        Args:
            include_inactive: 是否包含非活跃区域
            
        Returns:
            List[Dict]: 存储区域列表
        """
        areas_data = self._load_storage_areas()
        areas = []
        
        for area_id, area_info in areas_data["areas"].items():
            if include_inactive or area_info["status"] == "active":
                areas.append(area_info)
        
        # 按区域ID排序
        areas.sort(key=lambda x: x["area_id"])
        return areas
    
    def get_area_ids(self, include_inactive: bool = False) -> List[str]:
        """
        获取所有存储区域ID列表

        Args:
            include_inactive: 是否包含非活跃区域

        Returns:
            List[str]: 存储区域ID列表
        """
        areas = self.get_all_areas(include_inactive)
        return [area["area_id"] for area in areas]

    def get_area_by_id(self, area_id: str) -> Optional[Dict]:
        """
        根据ID获取存储区域详情

        Args:
            area_id: 区域ID

        Returns:
            Optional[Dict]: 存储区域信息，如果不存在则返回None
        """
        try:
            areas_data = self._load_storage_areas()
            area_info = areas_data["areas"].get(area_id)
            return area_info if area_info else None
        except Exception as e:
            print(f"获取存储区域详情失败: {e}")
            return None
    
    def add_area(self, area_id: str, area_name: str, description: str = "", 
                 capacity: int = 1000, operator: str = "system") -> bool:
        """
        添加新的存储区域
        
        Args:
            area_id: 区域ID（如E、F等）
            area_name: 区域名称
            description: 区域描述
            capacity: 容量
            operator: 操作员
            
        Returns:
            bool: 是否添加成功
        """
        try:
            areas_data = self._load_storage_areas()
            
            # 检查区域ID是否已存在
            if area_id in areas_data["areas"]:
                print(f"存储区域已存在: {area_id}")
                return False
            
            # 验证区域ID格式（只允许字母）
            if not area_id.isalpha() or len(area_id) != 1:
                print(f"区域ID格式无效，只允许单个字母: {area_id}")
                return False
            
            # 添加新区域
            areas_data["areas"][area_id.upper()] = {
                "area_id": area_id.upper(),
                "area_name": area_name,
                "description": description,
                "capacity": capacity,
                "status": "active",
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat(),
                "created_by": operator
            }
            
            # 保存配置
            self._save_storage_areas(areas_data)
            print(f"存储区域添加成功: {area_id.upper()} - {area_name}")
            return True
            
        except Exception as e:
            print(f"添加存储区域失败: {e}")
            return False
    
    def update_area(self, area_id: str, area_name: str = None, 
                   description: str = None, capacity: int = None,
                   operator: str = "system") -> bool:
        """
        更新存储区域信息
        
        Args:
            area_id: 区域ID
            area_name: 新的区域名称（可选）
            description: 新的描述（可选）
            capacity: 新的容量（可选）
            operator: 操作员
            
        Returns:
            bool: 是否更新成功
        """
        try:
            areas_data = self._load_storage_areas()
            
            if area_id not in areas_data["areas"]:
                print(f"存储区域不存在: {area_id}")
                return False
            
            area = areas_data["areas"][area_id]
            
            # 更新字段
            if area_name is not None:
                area["area_name"] = area_name
            if description is not None:
                area["description"] = description
            if capacity is not None:
                area["capacity"] = capacity
            
            area["updated_at"] = datetime.now().isoformat()
            area["updated_by"] = operator
            
            # 保存配置
            self._save_storage_areas(areas_data)
            print(f"存储区域更新成功: {area_id}")
            return True
            
        except Exception as e:
            print(f"更新存储区域失败: {e}")
            return False
    
    def deactivate_area(self, area_id: str, operator: str = "system") -> bool:
        """
        停用存储区域（软删除）
        
        Args:
            area_id: 区域ID
            operator: 操作员
            
        Returns:
            bool: 是否停用成功
        """
        try:
            areas_data = self._load_storage_areas()
            
            if area_id not in areas_data["areas"]:
                print(f"存储区域不存在: {area_id}")
                return False
            
            areas_data["areas"][area_id]["status"] = "inactive"
            areas_data["areas"][area_id]["updated_at"] = datetime.now().isoformat()
            areas_data["areas"][area_id]["deactivated_by"] = operator
            
            # 保存配置
            self._save_storage_areas(areas_data)
            print(f"存储区域已停用: {area_id}")
            return True
            
        except Exception as e:
            print(f"停用存储区域失败: {e}")
            return False
    
    def is_valid_area(self, area_id: str) -> bool:
        """
        验证存储区域是否有效
        
        Args:
            area_id: 区域ID
            
        Returns:
            bool: 是否有效
        """
        valid_areas = self.get_area_ids()
        return area_id in valid_areas
    
    def get_area_statistics(self) -> Dict:
        """
        获取存储区域统计信息
        
        Returns:
            Dict: 统计信息
        """
        areas_data = self._load_storage_areas()
        
        total_areas = len(areas_data["areas"])
        active_areas = sum(1 for area in areas_data["areas"].values() 
                          if area["status"] == "active")
        inactive_areas = total_areas - active_areas
        
        return {
            "total_areas": total_areas,
            "active_areas": active_areas,
            "inactive_areas": inactive_areas,
            "last_updated": areas_data["last_updated"]
        }
