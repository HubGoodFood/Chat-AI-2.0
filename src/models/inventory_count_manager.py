"""
库存盘点管理器
负责处理库存盘点相关的业务逻辑
"""
import json
import os
from datetime import datetime
from typing import List, Dict, Optional, Any
import uuid


class InventoryCountManager:
    """
    库存盘点管理器
    
    主要功能：
    1. 创建和管理库存盘点任务
    2. 记录盘点数据（账面数量 vs 实际数量）
    3. 计算库存差异
    4. 生成盘点报告
    """
    
    def __init__(self):
        self.counts_file = 'data/inventory_counts.json'
        self.inventory_file = 'data/inventory.json'
        self._ensure_counts_file()
    
    def _ensure_counts_file(self):
        """确保盘点数据文件存在"""
        if not os.path.exists(self.counts_file):
            self._initialize_counts_file()
    
    def _initialize_counts_file(self):
        """初始化盘点数据文件"""
        try:
            initial_data = {
                "last_updated": datetime.now().isoformat(),
                "counts": {}
            }
            
            os.makedirs(os.path.dirname(self.counts_file), exist_ok=True)
            with open(self.counts_file, 'w', encoding='utf-8') as f:
                json.dump(initial_data, f, ensure_ascii=False, indent=2)
            
            print("库存盘点数据文件初始化完成")

        except Exception as e:
            print(f"初始化盘点数据文件失败: {e}")
    
    def _load_counts(self) -> Dict:
        """加载盘点数据"""
        try:
            with open(self.counts_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"加载盘点数据失败: {e}")
            return {"last_updated": datetime.now().isoformat(), "counts": {}}
    
    def _save_counts(self, counts_data: Dict):
        """保存盘点数据"""
        try:
            counts_data["last_updated"] = datetime.now().isoformat()
            with open(self.counts_file, 'w', encoding='utf-8') as f:
                json.dump(counts_data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"保存盘点数据失败: {e}")
    
    def _load_inventory(self) -> Dict:
        """加载库存数据（用于获取账面数量）"""
        try:
            with open(self.inventory_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"加载库存数据失败: {e}")
            return {"products": {}}
    
    def _generate_count_id(self) -> str:
        """
        生成唯一的盘点ID
        
        Returns:
            str: 盘点ID，格式：COUNT_YYYYMMDD_HHMMSS_随机数
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        random_suffix = str(uuid.uuid4())[:8]
        return f"COUNT_{timestamp}_{random_suffix}"
    
    def create_count_task(self, operator: str, note: str = "") -> str:
        """
        创建新的库存盘点任务
        
        Args:
            operator: 操作员名称
            note: 盘点备注
            
        Returns:
            str: 盘点任务ID
        """
        try:
            counts_data = self._load_counts()
            count_id = self._generate_count_id()
            
            # 创建新的盘点任务
            counts_data["counts"][count_id] = {
                "count_id": count_id,
                "count_date": datetime.now().isoformat(),
                "operator": operator,
                "status": "in_progress",  # in_progress, completed, cancelled
                "note": note,
                "items": [],  # 盘点项目列表
                "summary": {
                    "total_items": 0,
                    "items_with_difference": 0,
                    "total_difference_value": 0.0,
                    "created_at": datetime.now().isoformat(),
                    "completed_at": None
                }
            }
            
            # 保存数据
            self._save_counts(counts_data)
            print(f"盘点任务创建成功，ID: {count_id}")
            return count_id
            
        except Exception as e:
            print(f"创建盘点任务失败: {e}")
            return ""
    
    def get_count_task(self, count_id: str) -> Optional[Dict]:
        """
        获取盘点任务信息
        
        Args:
            count_id: 盘点任务ID
            
        Returns:
            Dict: 盘点任务信息，如果不存在返回None
        """
        counts_data = self._load_counts()
        return counts_data["counts"].get(count_id)
    
    def get_all_count_tasks(self, status: str = None) -> List[Dict]:
        """
        获取所有盘点任务
        
        Args:
            status: 可选，按状态筛选 (in_progress, completed, cancelled)
            
        Returns:
            List[Dict]: 盘点任务列表
        """
        counts_data = self._load_counts()
        tasks = list(counts_data["counts"].values())
        
        if status:
            tasks = [task for task in tasks if task["status"] == status]
        
        # 按创建时间倒序排列
        tasks.sort(key=lambda x: x["count_date"], reverse=True)
        return tasks

    def add_count_item_by_barcode(self, count_id: str, barcode: str) -> bool:
        """
        通过条形码添加盘点项目

        Args:
            count_id: 盘点任务ID
            barcode: 产品条形码

        Returns:
            bool: 是否添加成功
        """
        try:
            # 加载数据
            counts_data = self._load_counts()
            inventory_data = self._load_inventory()

            # 检查盘点任务是否存在
            if count_id not in counts_data["counts"]:
                print(f"盘点任务不存在: {count_id}")
                return False

            count_task = counts_data["counts"][count_id]

            # 检查盘点任务状态
            if count_task["status"] != "in_progress":
                print(f"盘点任务状态不允许添加项目: {count_task['status']}")
                return False

            # 通过条形码查找产品
            product_found = None
            product_id = None

            for pid, product in inventory_data["products"].items():
                if (product.get("barcode") == barcode and
                    product["status"] == "active"):
                    product_found = product
                    product_id = pid
                    break

            if not product_found:
                print(f"未找到条形码对应的产品: {barcode}")
                return False

            # 检查是否已经添加过该产品
            for item in count_task["items"]:
                if item["product_id"] == product_id:
                    print(f"产品已存在于盘点列表中: {product_found['product_name']}")
                    return False

            # 添加盘点项目
            count_item = {
                "product_id": product_id,
                "product_name": product_found["product_name"],
                "barcode": barcode,
                "category": product_found["category"],
                "unit": product_found["unit"],
                "storage_area": product_found.get("storage_area", ""),
                "expected_quantity": product_found["current_stock"],  # 账面数量
                "actual_quantity": None,  # 实际数量（待录入）
                "difference": None,  # 差异（待计算）
                "note": "",
                "added_at": datetime.now().isoformat()
            }

            count_task["items"].append(count_item)

            # 保存数据
            self._save_counts(counts_data)
            print(f"产品添加到盘点列表: {product_found['product_name']}")
            return True

        except Exception as e:
            print(f"通过条形码添加盘点项目失败: {e}")
            return False

    def add_count_item_by_product_id(self, count_id: str, product_id: str) -> bool:
        """
        通过产品ID添加盘点项目

        Args:
            count_id: 盘点任务ID
            product_id: 产品ID

        Returns:
            bool: 是否添加成功
        """
        try:
            # 加载数据
            inventory_data = self._load_inventory()

            # 检查产品是否存在
            if product_id not in inventory_data["products"]:
                print(f"产品不存在: {product_id}")
                return False

            product = inventory_data["products"][product_id]

            # 检查产品状态
            if product["status"] != "active":
                print(f"产品状态不活跃: {product['product_name']}")
                return False

            # 使用产品的条形码添加（复用条形码添加逻辑）
            barcode = product.get("barcode", "")
            if barcode:
                return self.add_count_item_by_barcode(count_id, barcode)
            else:
                print(f"产品没有条形码: {product['product_name']}")
                return False

        except Exception as e:
            print(f"通过产品ID添加盘点项目失败: {e}")
            return False

    def record_actual_quantity(self, count_id: str, product_id: str, actual_quantity: int, note: str = "") -> bool:
        """
        记录产品的实际盘点数量

        Args:
            count_id: 盘点任务ID
            product_id: 产品ID
            actual_quantity: 实际盘点数量
            note: 备注信息

        Returns:
            bool: 是否记录成功
        """
        try:
            counts_data = self._load_counts()

            # 检查盘点任务是否存在
            if count_id not in counts_data["counts"]:
                print(f"盘点任务不存在: {count_id}")
                return False

            count_task = counts_data["counts"][count_id]

            # 检查盘点任务状态
            if count_task["status"] != "in_progress":
                print(f"盘点任务状态不允许修改: {count_task['status']}")
                return False

            # 查找对应的盘点项目
            item_found = False
            for item in count_task["items"]:
                if item["product_id"] == product_id:
                    # 记录实际数量
                    item["actual_quantity"] = actual_quantity
                    item["note"] = note
                    item["recorded_at"] = datetime.now().isoformat()

                    # 计算差异（账面数量 - 实际数量）
                    expected = item["expected_quantity"]
                    item["difference"] = expected - actual_quantity

                    item_found = True
                    print(f"记录实际数量: {item['product_name']} - 账面:{expected}, 实际:{actual_quantity}, 差异:{item['difference']}")
                    break

            if not item_found:
                print(f"在盘点列表中未找到产品: {product_id}")
                return False

            # 保存数据
            self._save_counts(counts_data)
            return True

        except Exception as e:
            print(f"记录实际数量失败: {e}")
            return False

    def remove_count_item(self, count_id: str, product_id: str) -> bool:
        """
        从盘点列表中移除产品

        Args:
            count_id: 盘点任务ID
            product_id: 产品ID

        Returns:
            bool: 是否移除成功
        """
        try:
            counts_data = self._load_counts()

            # 检查盘点任务是否存在
            if count_id not in counts_data["counts"]:
                return False

            count_task = counts_data["counts"][count_id]

            # 检查盘点任务状态
            if count_task["status"] != "in_progress":
                return False

            # 查找并移除项目
            original_length = len(count_task["items"])
            count_task["items"] = [item for item in count_task["items"]
                                 if item["product_id"] != product_id]

            if len(count_task["items"]) < original_length:
                self._save_counts(counts_data)
                print(f"产品已从盘点列表中移除")
                return True
            else:
                print(f"在盘点列表中未找到产品: {product_id}")
                return False

        except Exception as e:
            print(f"移除盘点项目失败: {e}")
            return False

    def complete_count_task(self, count_id: str) -> bool:
        """
        完成盘点任务并生成汇总统计

        Args:
            count_id: 盘点任务ID

        Returns:
            bool: 是否完成成功
        """
        try:
            counts_data = self._load_counts()

            # 检查盘点任务是否存在
            if count_id not in counts_data["counts"]:
                print(f"盘点任务不存在: {count_id}")
                return False

            count_task = counts_data["counts"][count_id]

            # 检查盘点任务状态
            if count_task["status"] != "in_progress":
                print(f"盘点任务状态不允许完成: {count_task['status']}")
                return False

            # 检查是否所有项目都已记录实际数量
            incomplete_items = []
            for item in count_task["items"]:
                if item["actual_quantity"] is None:
                    incomplete_items.append(item["product_name"])

            if incomplete_items:
                print(f"以下产品尚未记录实际数量: {', '.join(incomplete_items)}")
                return False

            # 计算汇总统计
            total_items = len(count_task["items"])
            items_with_difference = 0
            total_difference_value = 0.0

            for item in count_task["items"]:
                if item["difference"] != 0:
                    items_with_difference += 1
                    # 这里可以根据产品价格计算差异价值，暂时使用差异数量
                    total_difference_value += abs(item["difference"])

            # 更新汇总信息
            count_task["summary"] = {
                "total_items": total_items,
                "items_with_difference": items_with_difference,
                "total_difference_value": total_difference_value,
                "created_at": count_task["summary"]["created_at"],
                "completed_at": datetime.now().isoformat()
            }

            # 更新状态为已完成
            count_task["status"] = "completed"
            count_task["completed_at"] = datetime.now().isoformat()

            # 保存数据
            self._save_counts(counts_data)

            print(f"盘点任务完成")
            print(f"   - 总计项目: {total_items}")
            print(f"   - 有差异项目: {items_with_difference}")
            print(f"   - 总差异数量: {total_difference_value}")

            return True

        except Exception as e:
            print(f"完成盘点任务失败: {e}")
            return False

    def cancel_count_task(self, count_id: str, reason: str = "") -> bool:
        """
        取消盘点任务

        Args:
            count_id: 盘点任务ID
            reason: 取消原因

        Returns:
            bool: 是否取消成功
        """
        try:
            counts_data = self._load_counts()

            # 检查盘点任务是否存在
            if count_id not in counts_data["counts"]:
                return False

            count_task = counts_data["counts"][count_id]

            # 只有进行中的任务可以取消
            if count_task["status"] != "in_progress":
                return False

            # 更新状态
            count_task["status"] = "cancelled"
            count_task["cancelled_at"] = datetime.now().isoformat()
            count_task["cancel_reason"] = reason

            # 保存数据
            self._save_counts(counts_data)
            print(f"盘点任务已取消: {reason}")
            return True

        except Exception as e:
            print(f"取消盘点任务失败: {e}")
            return False

    def get_count_items(self, count_id: str) -> List[Dict]:
        """
        获取盘点任务的所有项目

        Args:
            count_id: 盘点任务ID

        Returns:
            List[Dict]: 盘点项目列表
        """
        count_task = self.get_count_task(count_id)
        if count_task:
            return count_task.get("items", [])
        return []

    def get_count_summary(self, count_id: str) -> Optional[Dict]:
        """
        获取盘点任务汇总信息

        Args:
            count_id: 盘点任务ID

        Returns:
            Dict: 汇总信息，如果不存在返回None
        """
        count_task = self.get_count_task(count_id)
        if count_task:
            return count_task.get("summary")
        return None

    def get_difference_items(self, count_id: str) -> List[Dict]:
        """
        获取有差异的盘点项目

        Args:
            count_id: 盘点任务ID

        Returns:
            List[Dict]: 有差异的项目列表
        """
        items = self.get_count_items(count_id)
        return [item for item in items if item.get("difference") != 0]

    def get_count_statistics(self) -> Dict:
        """
        获取盘点统计信息

        Returns:
            Dict: 统计信息
        """
        try:
            counts_data = self._load_counts()

            total_counts = len(counts_data["counts"])
            in_progress_counts = 0
            completed_counts = 0
            cancelled_counts = 0

            for count_task in counts_data["counts"].values():
                status = count_task["status"]
                if status == "in_progress":
                    in_progress_counts += 1
                elif status == "completed":
                    completed_counts += 1
                elif status == "cancelled":
                    cancelled_counts += 1

            return {
                "total_counts": total_counts,
                "in_progress_counts": in_progress_counts,
                "completed_counts": completed_counts,
                "cancelled_counts": cancelled_counts,
                "last_updated": counts_data["last_updated"]
            }

        except Exception as e:
            print(f"获取盘点统计失败: {e}")
            return {
                "total_counts": 0,
                "in_progress_counts": 0,
                "completed_counts": 0,
                "cancelled_counts": 0,
                "last_updated": datetime.now().isoformat()
            }
