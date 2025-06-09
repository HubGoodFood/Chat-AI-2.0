"""
库存管理模块
"""
import json
import os
import pandas as pd
from datetime import datetime
from typing import List, Dict, Optional, Any


class InventoryManager:
    def __init__(self):
        self.inventory_file = 'data/inventory.json'
        self.products_file = 'data/products.csv'
        self._ensure_inventory_file()
    
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
                inventory_data["products"][product_id] = {
                    "product_name": row['ProductName'],
                    "category": row['Category'],
                    "specification": row['Specification'],
                    "price": row['Price'],
                    "unit": row['Unit'],
                    "current_stock": 100,  # 默认库存
                    "min_stock_warning": 10,  # 最小库存警告
                    "description": row.get('Keywords', ''),
                    "image_url": "",  # 商品图片URL
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
            
            print(f"✅ 库存数据初始化完成，共 {len(inventory_data['products'])} 个产品")
            
        except Exception as e:
            print(f"❌ 初始化库存数据失败: {e}")
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
            print(f"加载库存数据失败: {e}")
            return {"last_updated": datetime.now().isoformat(), "products": {}}
    
    def _save_inventory(self, inventory_data: Dict):
        """保存库存数据"""
        try:
            inventory_data["last_updated"] = datetime.now().isoformat()
            with open(self.inventory_file, 'w', encoding='utf-8') as f:
                json.dump(inventory_data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"保存库存数据失败: {e}")
    
    def get_all_products(self) -> List[Dict]:
        """获取所有产品库存信息"""
        inventory_data = self._load_inventory()
        products = []
        
        for product_id, product_info in inventory_data["products"].items():
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
            old_stock = product["current_stock"]
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
            print(f"更新库存失败: {e}")
            return False
    
    def add_product(self, product_data: Dict, operator: str) -> Optional[str]:
        """添加新产品"""
        try:
            inventory_data = self._load_inventory()
            
            # 生成新的产品ID
            existing_ids = [int(pid) for pid in inventory_data["products"].keys() if pid.isdigit()]
            new_id = str(max(existing_ids) + 1) if existing_ids else "1"
            
            # 创建产品记录
            inventory_data["products"][new_id] = {
                "product_name": product_data["product_name"],
                "category": product_data["category"],
                "specification": product_data.get("specification", ""),
                "price": product_data["price"],
                "unit": product_data["unit"],
                "current_stock": product_data.get("initial_stock", 0),
                "min_stock_warning": product_data.get("min_stock_warning", 10),
                "description": product_data.get("description", ""),
                "image_url": product_data.get("image_url", ""),
                "status": "active",
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat(),
                "stock_history": [
                    {
                        "action": "新增产品",
                        "quantity": product_data.get("initial_stock", 0),
                        "timestamp": datetime.now().isoformat(),
                        "operator": operator,
                        "note": "新增产品"
                    }
                ]
            }
            
            # 保存数据
            self._save_inventory(inventory_data)
            return new_id
            
        except Exception as e:
            print(f"添加产品失败: {e}")
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
            print(f"更新产品失败: {e}")
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
            print(f"删除产品失败: {e}")
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
