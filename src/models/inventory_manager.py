# -*- coding: utf-8 -*-
"""
库存管理模块 - 增强版
支持条形码生成、存储区域管理等功能
"""
import json
import os
import pandas as pd
from datetime import datetime
from typing import List, Dict, Optional, Any
import barcode
from barcode.writer import ImageWriter
from PIL import Image
import secrets
from .storage_area_manager import StorageAreaManager
from .pickup_location_manager import PickupLocationManager
from ..utils.encoding_utils import safe_barcode_filename, clean_product_data, safe_print
from ..utils.logger_config import get_logger

# 初始化日志记录器
logger = get_logger('inventory_manager')


class InventoryManager:
    def __init__(self):
        self.inventory_file = 'data/inventory.json'
        self.products_file = 'data/products.csv'
        self.barcode_dir = 'static/barcodes'  # 条形码图片存储目录
        self.storage_area_manager = StorageAreaManager()  # 存储区域管理器
        self.pickup_location_manager = PickupLocationManager()  # 取货点管理器
        self._ensure_directories()
        self._ensure_inventory_file()

    def _ensure_directories(self):
        """确保必要的目录存在"""
        os.makedirs(os.path.dirname(self.inventory_file), exist_ok=True)
        os.makedirs(self.barcode_dir, exist_ok=True)

    def _generate_barcode(self, product_id: str, product_name: str) -> str:
        """
        为产品生成唯一的条形码

        Args:
            product_id: 产品ID
            product_name: 产品名称

        Returns:
            str: 生成的条形码字符串
        """
        try:
            # 生成基于产品ID的条形码（确保唯一性）
            # 格式：前缀(2位) + 产品ID(6位，不足补0) + 随机数(4位)
            prefix = "88"  # 自定义前缀，避免与标准商品条码冲突
            padded_id = str(product_id).zfill(6)  # 产品ID补零到6位
            random_suffix = str(secrets.randbelow(10000)).zfill(4)  # 4位随机数

            barcode_number = f"{prefix}{padded_id}{random_suffix}"
            return barcode_number

        except Exception as e:
            logger.error(f"生成条形码失败: {e}")
            # 如果生成失败，返回基于时间戳的备用条形码
            timestamp = str(int(datetime.now().timestamp()))[-8:]
            return f"88{timestamp}0000"

    def _save_barcode_image(self, barcode_number: str, product_name: str) -> str:
        """
        保存条形码图片到文件

        Args:
            barcode_number: 条形码数字
            product_name: 产品名称（用于文件命名）

        Returns:
            str: 条形码图片的相对路径
        """
        try:
            # 使用Code128格式生成条形码
            code128 = barcode.get_barcode_class('code128')
            barcode_instance = code128(barcode_number, writer=ImageWriter())

            # 生成安全的文件名
            filename = safe_barcode_filename(product_name, barcode_number)

            # 保存条形码图片
            filepath = os.path.join(self.barcode_dir, filename)
            barcode_instance.save(filepath)

            # 返回相对路径（用于Web访问）
            return f"barcodes/{filename}.png"

        except Exception as e:
            safe_print(f"保存条形码图片失败: {e}")
            return ""

    def _ensure_inventory_file(self):
        """确保库存文件存在，如果不存在则从产品文件初始化"""
        if not os.path.exists(self.inventory_file):
            self._initialize_inventory_from_products()
    
    def _initialize_inventory_from_products(self):
        """从产品CSV文件初始化库存数据"""
        try:
            # 读取产品数据
            products_df = pd.read_csv(self.products_file)
            products_df.columns = products_df.columns.str.strip()
            
            inventory_data = {
                "last_updated": datetime.now().isoformat(),
                "products": {}
            }
            
            # 为每个产品创建库存记录
            for idx, row in products_df.iterrows():
                product_id = str(idx + 1)
                product_name = row['ProductName']

                # 生成条形码
                barcode_number = self._generate_barcode(product_id, product_name)
                barcode_image_path = self._save_barcode_image(barcode_number, product_name)

                # 随机分配存储区域（实际使用中应该由管理员指定）
                available_areas = self.storage_area_manager.get_area_ids()
                storage_area = available_areas[idx % len(available_areas)] if available_areas else "A"

                inventory_data["products"][product_id] = {
                    "product_name": product_name,
                    "category": row['Category'],
                    "specification": row['Specification'],
                    "price": row['Price'],
                    "unit": row['Unit'],
                    "current_stock": 100,  # 默认库存
                    "min_stock_warning": 10,  # 最小库存警告
                    "description": row.get('Keywords', ''),
                    "image_url": "",  # 商品图片URL
                    "barcode": barcode_number,  # 新增：条形码
                    "barcode_image": barcode_image_path,  # 新增：条形码图片路径
                    "storage_area": storage_area,  # 新增：存储区域
                    "status": "active",  # active, inactive
                    "created_at": datetime.now().isoformat(),
                    "updated_at": datetime.now().isoformat(),
                    "stock_history": [
                        {
                            "action": "初始化",
                            "quantity": 100,
                            "timestamp": datetime.now().isoformat(),
                            "operator": "system",
                            "note": "系统初始化库存"
                        }
                    ]
                }
            
            # 保存库存文件
            os.makedirs(os.path.dirname(self.inventory_file), exist_ok=True)
            with open(self.inventory_file, 'w', encoding='utf-8') as f:
                json.dump(inventory_data, f, ensure_ascii=False, indent=2)
            
            logger.info(f"库存数据初始化完成，共 {len(inventory_data['products'])} 个产品")

        except Exception as e:
            logger.error(f"初始化库存数据失败: {e}")
            # 创建空的库存文件
            empty_inventory = {
                "last_updated": datetime.now().isoformat(),
                "products": {}
            }
            with open(self.inventory_file, 'w', encoding='utf-8') as f:
                json.dump(empty_inventory, f, ensure_ascii=False, indent=2)
    
    def _load_inventory(self) -> Dict:
        """加载库存数据"""
        try:
            with open(self.inventory_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"加载库存数据失败: {e}")
            return {"last_updated": datetime.now().isoformat(), "products": {}}
    
    def _save_inventory(self, inventory_data: Dict):
        """保存库存数据"""
        try:
            inventory_data["last_updated"] = datetime.now().isoformat()
            with open(self.inventory_file, 'w', encoding='utf-8') as f:
                json.dump(inventory_data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"保存库存数据失败: {e}")
    
    def get_all_products(self) -> List[Dict]:
        """获取所有产品库存信息"""
        inventory_data = self._load_inventory()
        products = []
        
        for product_id, product_info in inventory_data["products"].items():
            product_info["product_id"] = product_id
            products.append(product_info)
        
        return products

    def search_products(self, keyword: str) -> List[Dict]:
        """搜索产品"""
        inventory_data = self._load_inventory()
        products = []
        keyword = keyword.lower()

        for product_id, product_info in inventory_data["products"].items():
            if product_info["status"] == "active":
                # 在产品名称、分类、描述、条形码中搜索
                search_fields = [
                    product_info.get("product_name", ""),
                    product_info.get("category", ""),
                    product_info.get("description", ""),
                    product_info.get("barcode", ""),
                    product_info.get("specification", "")
                ]

                if any(keyword in str(field).lower() for field in search_fields):
                    product_info["product_id"] = product_id
                    products.append(product_info)

        return products

    def get_product_by_id(self, product_id: str) -> Optional[Dict]:
        """根据ID获取产品信息"""
        inventory_data = self._load_inventory()
        product = inventory_data["products"].get(product_id)
        if product:
            product["product_id"] = product_id
        return product
    
    def update_stock(self, product_id: str, quantity_change: int, operator: str, note: str = "") -> bool:
        """更新库存数量"""
        try:
            inventory_data = self._load_inventory()

            if product_id not in inventory_data["products"]:
                return False

            product = inventory_data["products"][product_id]
            # 确保current_stock是数字类型（防止字符串类型导致的错误）
            old_stock = int(product["current_stock"]) if isinstance(product["current_stock"], str) else product["current_stock"]
            new_stock = old_stock + quantity_change
            
            # 检查库存不能为负数
            if new_stock < 0:
                return False
            
            # 更新库存
            product["current_stock"] = new_stock
            product["updated_at"] = datetime.now().isoformat()
            
            # 记录库存变动历史
            action = "增加库存" if quantity_change > 0 else "减少库存"
            product["stock_history"].append({
                "action": action,
                "quantity": quantity_change,
                "old_stock": old_stock,
                "new_stock": new_stock,
                "timestamp": datetime.now().isoformat(),
                "operator": operator,
                "note": note
            })
            
            # 保存数据
            self._save_inventory(inventory_data)
            return True
            
        except Exception as e:
            logger.error(f"更新库存失败: {e}")
            return False
    
    def add_product(self, product_data: Dict, operator: str) -> Optional[str]:
        """添加新产品（增强版：自动生成条形码）"""
        try:
            # 清理产品数据中的编码问题
            cleaned_data = clean_product_data(product_data)

            inventory_data = self._load_inventory()

            # 生成新的产品ID
            existing_ids = [int(pid) for pid in inventory_data["products"].keys() if pid.isdigit()]
            new_id = str(max(existing_ids) + 1) if existing_ids else "1"

            product_name = cleaned_data["product_name"]

            # 生成条形码
            barcode_number = self._generate_barcode(new_id, product_name)
            barcode_image_path = self._save_barcode_image(barcode_number, product_name)

            # 创建产品记录（包含新字段）
            inventory_data["products"][new_id] = {
                "product_name": product_name,
                "category": cleaned_data["category"],
                "specification": cleaned_data.get("specification", ""),
                "price": cleaned_data["price"],
                "unit": cleaned_data["unit"],
                "current_stock": cleaned_data.get("initial_stock", 0),
                "min_stock_warning": cleaned_data.get("min_stock_warning", 10),
                "description": cleaned_data.get("description", ""),
                "image_url": cleaned_data.get("image_url", ""),
                "barcode": barcode_number,  # 新增：条形码
                "barcode_image": barcode_image_path,  # 新增：条形码图片路径
                "storage_area": cleaned_data.get("storage_area", "A"),  # 新增：存储区域
                "status": "active",
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat(),
                "stock_history": [
                    {
                        "action": "新增产品",
                        "quantity": cleaned_data.get("initial_stock", 0),
                        "timestamp": datetime.now().isoformat(),
                        "operator": operator,
                        "note": "新增产品"
                    }
                ]
            }

            # 保存数据
            self._save_inventory(inventory_data)
            logger.info(f"产品添加成功，ID: {new_id}, 条形码: {barcode_number}")
            return new_id

        except Exception as e:
            logger.error(f"添加产品失败: {e}")
            return None
    
    def update_product(self, product_id: str, product_data: Dict, operator: str) -> bool:
        """更新产品信息"""
        try:
            inventory_data = self._load_inventory()
            
            if product_id not in inventory_data["products"]:
                return False
            
            product = inventory_data["products"][product_id]
            
            # 更新产品信息（不包括库存）
            product["product_name"] = product_data.get("product_name", product["product_name"])
            product["category"] = product_data.get("category", product["category"])
            product["specification"] = product_data.get("specification", product["specification"])
            product["price"] = product_data.get("price", product["price"])
            product["unit"] = product_data.get("unit", product["unit"])
            product["min_stock_warning"] = product_data.get("min_stock_warning", product["min_stock_warning"])
            product["description"] = product_data.get("description", product["description"])
            product["image_url"] = product_data.get("image_url", product["image_url"])
            product["status"] = product_data.get("status", product["status"])
            product["updated_at"] = datetime.now().isoformat()
            
            # 保存数据
            self._save_inventory(inventory_data)
            return True
            
        except Exception as e:
            logger.error(f"更新产品失败: {e}")
            return False
    
    def delete_product(self, product_id: str) -> bool:
        """删除产品（软删除，设置状态为inactive）"""
        try:
            inventory_data = self._load_inventory()
            
            if product_id not in inventory_data["products"]:
                return False
            
            inventory_data["products"][product_id]["status"] = "inactive"
            inventory_data["products"][product_id]["updated_at"] = datetime.now().isoformat()
            
            # 保存数据
            self._save_inventory(inventory_data)
            return True
            
        except Exception as e:
            logger.error(f"删除产品失败: {e}")
            return False
    
    def get_low_stock_products(self) -> List[Dict]:
        """获取低库存产品"""
        inventory_data = self._load_inventory()
        low_stock_products = []
        
        for product_id, product in inventory_data["products"].items():
            if (product["status"] == "active" and 
                product["current_stock"] <= product["min_stock_warning"]):
                product["product_id"] = product_id
                low_stock_products.append(product)
        
        return low_stock_products
    
    def get_stock_history(self, product_id: str) -> List[Dict]:
        """获取产品库存变动历史"""
        inventory_data = self._load_inventory()
        product = inventory_data["products"].get(product_id)
        
        if product:
            return product.get("stock_history", [])
        return []
    
    def get_inventory_summary(self) -> Dict:
        """获取库存汇总信息"""
        inventory_data = self._load_inventory()
        
        total_products = 0
        active_products = 0
        low_stock_count = 0
        total_value = 0
        
        for product in inventory_data["products"].values():
            total_products += 1
            if product["status"] == "active":
                active_products += 1
                if product["current_stock"] <= product["min_stock_warning"]:
                    low_stock_count += 1
                
                # 计算库存价值
                try:
                    price = float(str(product["price"]).replace('元', '').replace('/', ''))
                    total_value += price * product["current_stock"]
                except:
                    pass
        
        return {
            "total_products": total_products,
            "active_products": active_products,
            "low_stock_count": low_stock_count,
            "total_value": round(total_value, 2),
            "last_updated": inventory_data["last_updated"]
        }

    # ==================== 新增：条形码相关方法 ====================

    def get_product_by_barcode(self, barcode: str) -> Optional[Dict]:
        """
        根据条形码获取产品信息

        Args:
            barcode: 条形码字符串

        Returns:
            Dict: 产品信息，如果未找到返回None
        """
        inventory_data = self._load_inventory()

        for product_id, product in inventory_data["products"].items():
            if product.get("barcode") == barcode and product["status"] == "active":
                product["product_id"] = product_id
                return product

        return None

    def get_products_by_storage_area(self, storage_area: str) -> List[Dict]:
        """
        根据存储区域获取产品列表

        Args:
            storage_area: 存储区域 (A, B, C, D)

        Returns:
            List[Dict]: 该区域的产品列表
        """
        inventory_data = self._load_inventory()
        products = []

        for product_id, product in inventory_data["products"].items():
            if (product.get("storage_area") == storage_area and
                product["status"] == "active"):
                product["product_id"] = product_id
                products.append(product)

        return products

    def get_available_storage_areas(self) -> List[str]:
        """
        获取可用的存储区域列表

        Returns:
            List[str]: 存储区域列表
        """
        return self.storage_area_manager.get_area_ids()

    def regenerate_barcode(self, product_id: str, operator: str) -> bool:
        """
        为产品重新生成条形码

        Args:
            product_id: 产品ID
            operator: 操作员

        Returns:
            bool: 操作是否成功
        """
        try:
            inventory_data = self._load_inventory()

            if product_id not in inventory_data["products"]:
                return False

            product = inventory_data["products"][product_id]
            product_name = product["product_name"]

            # 生成新的条形码
            new_barcode = self._generate_barcode(product_id, product_name)
            new_barcode_image = self._save_barcode_image(new_barcode, product_name)

            # 更新产品信息
            product["barcode"] = new_barcode
            product["barcode_image"] = new_barcode_image
            product["updated_at"] = datetime.now().isoformat()

            # 记录操作历史
            product["stock_history"].append({
                "action": "重新生成条形码",
                "quantity": 0,
                "timestamp": datetime.now().isoformat(),
                "operator": operator,
                "note": f"新条形码: {new_barcode}"
            })

            # 保存数据
            self._save_inventory(inventory_data)
            print(f"✅ 条形码重新生成成功: {new_barcode}")
            return True

        except Exception as e:
            print(f"重新生成条形码失败: {e}")
            return False

    # ==================== 存储区域管理方法 ====================

    def add_storage_area(self, area_id: str, area_name: str, description: str = "",
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
        return self.storage_area_manager.add_area(area_id, area_name, description, capacity, operator)

    def update_storage_area(self, area_id: str, area_name: str = None,
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
        return self.storage_area_manager.update_area(area_id, area_name, description, capacity, operator)

    def deactivate_storage_area(self, area_id: str, operator: str = "system") -> bool:
        """
        停用存储区域

        Args:
            area_id: 区域ID
            operator: 操作员

        Returns:
            bool: 是否停用成功
        """
        return self.storage_area_manager.deactivate_area(area_id, operator)

    def get_all_storage_areas(self, include_inactive: bool = False) -> List[Dict]:
        """
        获取所有存储区域详细信息

        Args:
            include_inactive: 是否包含非活跃区域

        Returns:
            List[Dict]: 存储区域详细信息列表
        """
        return self.storage_area_manager.get_all_areas(include_inactive)

    def is_valid_storage_area(self, area_id: str) -> bool:
        """
        验证存储区域是否有效

        Args:
            area_id: 区域ID

        Returns:
            bool: 是否有效
        """
        return self.storage_area_manager.is_valid_area(area_id)

    def get_storage_area_statistics(self) -> Dict:
        """
        获取存储区域统计信息

        Returns:
            Dict: 统计信息
        """
        return self.storage_area_manager.get_area_statistics()

    def get_storage_area_product_counts(self) -> Dict[str, int]:
        """
        获取每个存储区域的产品数量统计

        Returns:
            Dict[str, int]: 存储区域ID到产品数量的映射
        """
        try:
            inventory_data = self._load_inventory()
            area_counts = {}

            # 初始化所有活跃存储区域的计数为0
            active_areas = self.storage_area_manager.get_area_ids()
            for area_id in active_areas:
                area_counts[area_id] = 0

            # 统计每个区域的产品数量
            for product in inventory_data["products"].values():
                if product["status"] == "active":
                    storage_area = product.get("storage_area", "")
                    if storage_area in area_counts:
                        area_counts[storage_area] += 1
                    elif storage_area:  # 处理可能存在的无效存储区域
                        area_counts[storage_area] = area_counts.get(storage_area, 0) + 1

            return area_counts

        except Exception as e:
            print(f"获取存储区域产品统计失败: {e}")
            return {}

    def get_storage_areas_with_product_counts(self, include_inactive: bool = False) -> List[Dict]:
        """
        获取包含产品数量统计的存储区域列表

        Args:
            include_inactive: 是否包含非活跃区域

        Returns:
            List[Dict]: 包含产品数量的存储区域列表
        """
        try:
            # 获取存储区域列表
            areas = self.storage_area_manager.get_all_areas(include_inactive)

            # 获取产品数量统计
            product_counts = self.get_storage_area_product_counts()

            # 为每个区域添加产品数量信息
            for area in areas:
                area_id = area["area_id"]
                area["product_count"] = product_counts.get(area_id, 0)

            return areas

        except Exception as e:
            print(f"获取存储区域及产品统计失败: {e}")
            return []

    # ==================== 取货点管理方法 ====================

    def get_all_pickup_locations(self, include_inactive: bool = False) -> List[Dict]:
        """
        获取所有取货点

        Args:
            include_inactive: 是否包含非活跃取货点

        Returns:
            List[Dict]: 取货点列表
        """
        return self.pickup_location_manager.get_all_locations(include_inactive)

    def get_pickup_location_by_id(self, location_id: str) -> Optional[Dict]:
        """
        根据ID获取取货点信息

        Args:
            location_id: 取货点ID

        Returns:
            Optional[Dict]: 取货点信息
        """
        return self.pickup_location_manager.get_location_by_id(location_id)

    def add_pickup_location(self, location_id: str, location_name: str, address: str,
                           phone: str = "", contact_person: str = "",
                           business_hours: str = "请关注群内通知",
                           description: str = "", operator: str = "system") -> bool:
        """
        添加新的取货点

        Args:
            location_id: 取货点ID
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
        return self.pickup_location_manager.add_location(
            location_id, location_name, address, phone,
            contact_person, business_hours, description, operator
        )

    def update_pickup_location(self, location_id: str, **kwargs) -> bool:
        """
        更新取货点信息

        Args:
            location_id: 取货点ID
            **kwargs: 要更新的字段

        Returns:
            bool: 是否更新成功
        """
        return self.pickup_location_manager.update_location(location_id, **kwargs)

    def deactivate_pickup_location(self, location_id: str, operator: str = "system") -> bool:
        """
        停用取货点

        Args:
            location_id: 取货点ID
            operator: 操作员

        Returns:
            bool: 是否停用成功
        """
        return self.pickup_location_manager.deactivate_location(location_id, operator)

    def get_pickup_locations_summary(self) -> Dict:
        """
        获取取货点统计信息

        Returns:
            Dict: 统计信息
        """
        return self.pickup_location_manager.get_locations_summary()
