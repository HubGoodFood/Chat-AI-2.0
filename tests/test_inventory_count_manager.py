# -*- coding: utf-8 -*-
"""
库存盘点管理器单元测试

测试库存盘点系统的核心功能，包括盘点任务创建、产品添加、数量记录等。

测试覆盖：
1. 盘点任务管理
2. 盘点项目添加
3. 实际数量记录
4. 差异计算和分析
5. 盘点任务完成
6. 数据验证和错误处理

设计原则：
- 完整的功能覆盖
- 模拟文件系统操作
- 业务逻辑验证
- 错误情况处理
"""
import pytest
import json
import os
import tempfile
import shutil
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime
from typing import Dict, List, Any

# 导入被测试的模块
try:
    from src.models.inventory_count_manager import InventoryCountManager
    from src.models.inventory_manager import InventoryManager
except ImportError as e:
    print(f"导入警告: {e}")

    # 创建模拟类用于测试
    class InventoryCountManager:
        def __init__(self, data_dir="data"):
            self.data_dir = data_dir
            self.counts_file = os.path.join(data_dir, "inventory_counts.json")

        def create_count_task(self, operator, note=""):
            return "COUNT001"

        def add_product_to_count(self, count_id, product_id, barcode=""):
            return True

    class InventoryManager:
        def __init__(self, data_dir="data"):
            self.data_dir = data_dir

        def get_product_by_id(self, product_id):
            return {"product_name": "测试产品", "current_stock": 100}


class TestInventoryCountManager:
    """测试库存盘点管理器类"""

    @pytest.fixture
    def temp_data_dir(self):
        """创建临时数据目录"""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir, ignore_errors=True)

    @pytest.fixture
    def mock_inventory_manager(self):
        """模拟库存管理器"""
        mock_manager = Mock(spec=InventoryManager)

        # 模拟产品数据
        mock_products = {
            "1": {
                "product_name": "红富士苹果",
                "category": "水果",
                "unit": "斤",
                "current_stock": 100,
                "barcode": "1234567890123",
                "storage_area": "A1"
            },
            "2": {
                "product_name": "有机胡萝卜",
                "category": "蔬菜",
                "unit": "斤",
                "current_stock": 50,
                "barcode": "1234567890124",
                "storage_area": "B1"
            }
        }

        mock_manager.get_all_products.return_value = mock_products
        mock_manager.get_product_by_id.side_effect = lambda pid: mock_products.get(pid)
        mock_manager.find_product_by_barcode.side_effect = lambda barcode: next(
            ({"product_id": pid, **product} for pid, product in mock_products.items()
             if product.get("barcode") == barcode), None
        )

        return mock_manager

    @pytest.fixture
    def count_manager(self, temp_data_dir, mock_inventory_manager):
        """创建库存盘点管理器实例"""
        with patch('src.models.inventory_count_manager.InventoryManager', return_value=mock_inventory_manager):
            manager = InventoryCountManager(temp_data_dir)
            manager.inventory_manager = mock_inventory_manager
            return manager

    @pytest.mark.inventory
    def test_count_manager_initialization(self, count_manager, temp_data_dir):
        """测试盘点管理器初始化"""
        assert count_manager.data_dir == temp_data_dir
        assert count_manager.counts_file == os.path.join(temp_data_dir, "inventory_counts.json")

        # 验证初始化后盘点文件存在
        assert os.path.exists(count_manager.counts_file)

    @pytest.mark.inventory
    def test_create_count_task_success(self, count_manager):
        """测试成功创建盘点任务"""
        operator = "test_admin"
        note = "月度库存盘点"

        count_id = count_manager.create_count_task(operator, note)

        assert count_id is not None
        assert count_id != ""
        assert count_id.startswith("COUNT")

        # 验证盘点任务被正确创建
        count_task = count_manager.get_count_task(count_id)
        assert count_task is not None
        assert count_task["operator"] == operator
        assert count_task["note"] == note
        assert count_task["status"] == "in_progress"
        assert len(count_task["items"]) == 0

    @pytest.mark.inventory
    def test_create_multiple_count_tasks(self, count_manager):
        """测试创建多个盘点任务"""
        operator = "test_admin"

        count_id1 = count_manager.create_count_task(operator, "第一次盘点")
        count_id2 = count_manager.create_count_task(operator, "第二次盘点")

        assert count_id1 != count_id2

        # 验证两个任务都存在
        task1 = count_manager.get_count_task(count_id1)
        task2 = count_manager.get_count_task(count_id2)

        assert task1 is not None
        assert task2 is not None
        assert task1["note"] == "第一次盘点"
        assert task2["note"] == "第二次盘点"

    @pytest.mark.inventory
    def test_add_product_to_count_by_id(self, count_manager):
        """测试通过产品ID添加盘点项目"""
        operator = "test_admin"
        count_id = count_manager.create_count_task(operator)

        product_id = "1"
        result = count_manager.add_product_to_count(count_id, product_id)

        assert result == True

        # 验证产品被添加到盘点列表
        count_task = count_manager.get_count_task(count_id)
        assert len(count_task["items"]) == 1

        item = count_task["items"][0]
        assert item["product_id"] == product_id
        assert item["product_name"] == "红富士苹果"
        assert item["expected_quantity"] == 100
        assert item["actual_quantity"] is None
        assert item["difference"] is None

    @pytest.mark.inventory
    def test_add_product_to_count_by_barcode(self, count_manager):
        """测试通过条形码添加盘点项目"""
        operator = "test_admin"
        count_id = count_manager.create_count_task(operator)

        barcode = "1234567890124"
        result = count_manager.add_product_to_count(count_id, "", barcode)

        assert result == True

        # 验证产品被添加到盘点列表
        count_task = count_manager.get_count_task(count_id)
        assert len(count_task["items"]) == 1

        item = count_task["items"][0]
        assert item["product_id"] == "2"
        assert item["product_name"] == "有机胡萝卜"
        assert item["barcode"] == barcode

    @pytest.mark.inventory
    def test_add_duplicate_product_to_count(self, count_manager):
        """测试添加重复产品到盘点列表"""
        operator = "test_admin"
        count_id = count_manager.create_count_task(operator)

        product_id = "1"

        # 第一次添加应该成功
        result1 = count_manager.add_product_to_count(count_id, product_id)
        assert result1 == True

        # 第二次添加相同产品应该失败
        result2 = count_manager.add_product_to_count(count_id, product_id)
        assert result2 == False

        # 验证只有一个项目
        count_task = count_manager.get_count_task(count_id)
        assert len(count_task["items"]) == 1

    @pytest.mark.inventory
    def test_add_product_to_nonexistent_count(self, count_manager):
        """测试向不存在的盘点任务添加产品"""
        nonexistent_count_id = "COUNT999"
        product_id = "1"

        result = count_manager.add_product_to_count(nonexistent_count_id, product_id)
        assert result == False

    @pytest.mark.inventory
    def test_add_nonexistent_product_to_count(self, count_manager):
        """测试添加不存在的产品到盘点列表"""
        operator = "test_admin"
        count_id = count_manager.create_count_task(operator)

        nonexistent_product_id = "999"
        result = count_manager.add_product_to_count(count_id, nonexistent_product_id)

        assert result == False

        # 验证没有项目被添加
        count_task = count_manager.get_count_task(count_id)
        assert len(count_task["items"]) == 0

    @pytest.mark.inventory
    def test_record_actual_quantity_success(self, count_manager):
        """测试成功记录实际盘点数量"""
        operator = "test_admin"
        count_id = count_manager.create_count_task(operator)

        # 先添加产品到盘点列表
        product_id = "1"
        count_manager.add_product_to_count(count_id, product_id)

        # 记录实际数量
        actual_quantity = 95
        note = "实际盘点结果"

        result = count_manager.record_actual_quantity(count_id, product_id, actual_quantity, note)
        assert result == True

        # 验证数量被正确记录
        count_task = count_manager.get_count_task(count_id)
        item = count_task["items"][0]

        assert item["actual_quantity"] == actual_quantity
        assert item["difference"] == actual_quantity - 100  # 100是期望数量
        assert item["note"] == note

    @pytest.mark.inventory
    def test_record_actual_quantity_negative_difference(self, count_manager):
        """测试记录实际数量产生负差异"""
        operator = "test_admin"
        count_id = count_manager.create_count_task(operator)

        product_id = "1"
        count_manager.add_product_to_count(count_id, product_id)

        # 实际数量少于期望数量
        actual_quantity = 80
        result = count_manager.record_actual_quantity(count_id, product_id, actual_quantity)

        assert result == True

        count_task = count_manager.get_count_task(count_id)
        item = count_task["items"][0]

        assert item["actual_quantity"] == 80
        assert item["difference"] == -20  # 80 - 100 = -20

    @pytest.mark.inventory
    def test_record_actual_quantity_zero(self, count_manager):
        """测试记录实际数量为零"""
        operator = "test_admin"
        count_id = count_manager.create_count_task(operator)

        product_id = "1"
        count_manager.add_product_to_count(count_id, product_id)

        actual_quantity = 0
        result = count_manager.record_actual_quantity(count_id, product_id, actual_quantity)

        assert result == True

        count_task = count_manager.get_count_task(count_id)
        item = count_task["items"][0]

        assert item["actual_quantity"] == 0
        assert item["difference"] == -100  # 0 - 100 = -100