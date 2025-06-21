# -*- coding: utf-8 -*-
"""
取货点管理模块
支持动态添加、删除、修改取货点信息
"""
import json
import os
from datetime import datetime
from typing import List, Dict, Optional


class PickupLocationManager:
    """
    取货点管理器
    
    主要功能：
    1. 动态管理取货点（增删改查）
    2. 验证取货点信息的有效性
    3. 提供取货点的统计信息
    4. 确保数据一致性
    """
    
    def __init__(self):
        self.pickup_locations_file = 'data/pickup_locations.json'
        self._ensure_pickup_locations_file()
    
    def _ensure_pickup_locations_file(self):
        """确保取货点配置文件存在"""
        if not os.path.exists(self.pickup_locations_file):
            self._initialize_pickup_locations_file()
    
    def _initialize_pickup_locations_file(self):
        """初始化取货点配置文件"""
        try:
            # 确保data目录存在
            os.makedirs('data', exist_ok=True)
            
            # 默认的取货点配置（基于现有的3个取货点）
            initial_data = {
                "last_updated": datetime.now().isoformat(),
                "locations": {
                    "malden": {
                        "location_id": "malden",
                        "location_name": "Malden取货点",
                        "address": "273 Salem St, Malden, MA",
                        "phone": "781-480-4722",
                        "contact_person": "",
                        "business_hours": "请关注群内通知",
                        "description": "Malden地区主要取货点",
                        "status": "active",
                        "created_at": datetime.now().isoformat(),
                        "updated_at": datetime.now().isoformat()
                    },
                    "chinatown": {
                        "location_id": "chinatown",
                        "location_name": "Chinatown取货点",
                        "address": "25 Chauncy St, Boston, MA 02110",
                        "phone": "718-578-3389",
                        "contact_person": "",
                        "business_hours": "请关注群内通知",
                        "description": "波士顿中国城取货点",
                        "status": "active",
                        "created_at": datetime.now().isoformat(),
                        "updated_at": datetime.now().isoformat()
                    },
                    "quincy": {
                        "location_id": "quincy",
                        "location_name": "Quincy取货点",
                        "address": "待补充具体地址",
                        "phone": "待补充联系电话",
                        "contact_person": "",
                        "business_hours": "请关注群内通知",
                        "description": "Quincy地区取货点",
                        "status": "active",
                        "created_at": datetime.now().isoformat(),
                        "updated_at": datetime.now().isoformat()
                    }
                }
            }
            
            # 保存初始配置
            with open(self.pickup_locations_file, 'w', encoding='utf-8') as f:
                json.dump(initial_data, f, ensure_ascii=False, indent=2)
            
            print(f"取货点配置文件初始化成功: {self.pickup_locations_file}")

        except Exception as e:
            print(f"初始化取货点配置文件失败: {e}")
    
    def _load_pickup_locations(self) -> Dict:
        """加载取货点配置"""
        try:
            with open(self.pickup_locations_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"加载取货点配置失败: {e}")
            return {"last_updated": datetime.now().isoformat(), "locations": {}}
    
    def _save_pickup_locations(self, locations_data: Dict):
        """保存取货点配置"""
        try:
            locations_data["last_updated"] = datetime.now().isoformat()
            with open(self.pickup_locations_file, 'w', encoding='utf-8') as f:
                json.dump(locations_data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"保存取货点配置失败: {e}")
    
    def get_all_locations(self, include_inactive: bool = False) -> List[Dict]:
        """
        获取所有取货点
        
        Args:
            include_inactive: 是否包含非活跃取货点
            
        Returns:
            List[Dict]: 取货点列表
        """
        locations_data = self._load_pickup_locations()
        locations = []
        
        for location_id, location_info in locations_data["locations"].items():
            if include_inactive or location_info["status"] == "active":
                locations.append(location_info)
        
        # 按取货点ID排序
        locations.sort(key=lambda x: x["location_id"])
        return locations
    
    def get_location_ids(self, include_inactive: bool = False) -> List[str]:
        """
        获取所有取货点ID列表
        
        Args:
            include_inactive: 是否包含非活跃取货点
            
        Returns:
            List[str]: 取货点ID列表
        """
        locations = self.get_all_locations(include_inactive)
        return [location["location_id"] for location in locations]
    
    def get_location_by_id(self, location_id: str) -> Optional[Dict]:
        """
        根据ID获取取货点信息
        
        Args:
            location_id: 取货点ID
            
        Returns:
            Optional[Dict]: 取货点信息，如果不存在返回None
        """
        locations_data = self._load_pickup_locations()
        return locations_data["locations"].get(location_id)
    
    def add_location(self, location_id: str, location_name: str, address: str,
                    phone: str = "", contact_person: str = "", 
                    business_hours: str = "请关注群内通知", 
                    description: str = "", operator: str = "system") -> bool:
        """
        添加新的取货点
        
        Args:
            location_id: 取货点ID（如malden、quincy等）
            location_name: 取货点名称
            address: 地址
            phone: 联系电话
            contact_person: 联系人
            business_hours: 营业时间
            description: 描述
            operator: 操作员
            
        Returns:
            bool: 是否添加成功
        """
        try:
            locations_data = self._load_pickup_locations()
            
            # 检查取货点ID是否已存在
            if location_id in locations_data["locations"]:
                print(f"取货点已存在: {location_id}")
                return False
            
            # 验证必填字段
            if not location_id or not location_name or not address:
                print("取货点ID、名称和地址为必填字段")
                return False
            
            # 添加新取货点
            locations_data["locations"][location_id.lower()] = {
                "location_id": location_id.lower(),
                "location_name": location_name,
                "address": address,
                "phone": phone,
                "contact_person": contact_person,
                "business_hours": business_hours,
                "description": description,
                "status": "active",
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat(),
                "created_by": operator
            }
            
            # 保存配置
            self._save_pickup_locations(locations_data)
            print(f"取货点添加成功: {location_id} - {location_name}")
            return True
            
        except Exception as e:
            print(f"添加取货点失败: {e}")
            return False
    
    def update_location(self, location_id: str, **kwargs) -> bool:
        """
        更新取货点信息
        
        Args:
            location_id: 取货点ID
            **kwargs: 要更新的字段
            
        Returns:
            bool: 是否更新成功
        """
        try:
            locations_data = self._load_pickup_locations()
            
            if location_id not in locations_data["locations"]:
                print(f"取货点不存在: {location_id}")
                return False
            
            # 更新字段
            location = locations_data["locations"][location_id]
            updatable_fields = ['location_name', 'address', 'phone', 'contact_person', 
                              'business_hours', 'description', 'status']
            
            for field, value in kwargs.items():
                if field in updatable_fields:
                    location[field] = value
            
            location["updated_at"] = datetime.now().isoformat()
            if 'operator' in kwargs:
                location["updated_by"] = kwargs['operator']
            
            # 保存配置
            self._save_pickup_locations(locations_data)
            print(f"取货点更新成功: {location_id}")
            return True
            
        except Exception as e:
            print(f"更新取货点失败: {e}")
            return False
    
    def deactivate_location(self, location_id: str, operator: str = "system") -> bool:
        """
        停用取货点（软删除）
        
        Args:
            location_id: 取货点ID
            operator: 操作员
            
        Returns:
            bool: 是否停用成功
        """
        try:
            locations_data = self._load_pickup_locations()
            
            if location_id not in locations_data["locations"]:
                print(f"取货点不存在: {location_id}")
                return False
            
            locations_data["locations"][location_id]["status"] = "inactive"
            locations_data["locations"][location_id]["updated_at"] = datetime.now().isoformat()
            locations_data["locations"][location_id]["deactivated_by"] = operator
            
            # 保存配置
            self._save_pickup_locations(locations_data)
            print(f"取货点已停用: {location_id}")
            return True
            
        except Exception as e:
            print(f"停用取货点失败: {e}")
            return False
    
    def get_locations_summary(self) -> Dict:
        """
        获取取货点统计信息
        
        Returns:
            Dict: 统计信息
        """
        all_locations = self.get_all_locations(include_inactive=True)
        active_locations = self.get_all_locations(include_inactive=False)
        
        return {
            "total_locations": len(all_locations),
            "active_locations": len(active_locations),
            "inactive_locations": len(all_locations) - len(active_locations),
            "last_updated": self._load_pickup_locations().get("last_updated", "")
        }
