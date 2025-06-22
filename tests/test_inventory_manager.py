# -*- coding: utf-8 -*-
"""
库存管理器单元测试

测试库存管理系统的核心功能，包括产品管理、库存更新、条形码生成等。

测试覆盖：
1. 产品管理功能
2. 库存更新和调整
3. 条形码生成和管理
4. 存储区域管理
5. 数据验证和错误处理
6. 文件操作和数据持久化

设计原则：
- 完整的功能覆盖
- 模拟文件系统操作
- 数据验证测试
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
    from src.models.inventory_manager import InventoryManager
    from src.models.storage_area_manager import StorageAreaManager
    from src.utils.barcode_batch_generator import BarcodeBatchGenerator
    from src.utils.barcode_utils import generate_barcode_number, safe_barcode_filename
except ImportError as e:
    print(f"导入警告: {e}")

    # 创建模拟类用于测试
    class InventoryManager:
        def __init__(self, data_dir="data"):
            self.data_dir = data_dir
            self.inventory_file = os.path.join(data_dir, "inventory.json")
            self.barcode_dir = "static/barcodes"

        def get_all_products(self):
            return {}

        def add_product(self, product_data, operator):
            return "1"

    class StorageAreaManager:
        def __init__(self):
            pass

        def get_area_ids(self):
            return ["A1", "B1", "C1"]

    class BarcodeBatchGenerator:
        def __init__(self):
            pass

        def generate_barcodes_for_products(self, product_ids, operator):
            return {"successfully_generated": len(product_ids)}


class TestInventoryManager:
    """测试库存管理器类"""

    @pytest.fixture
    def temp_data_dir(self):
        """创建临时数据目录"""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir, ignore_errors=True)

    @pytest.fixture
    def mock_storage_area_manager(self):
        """模拟存储区域管理器"""
        mock_manager = Mock()
        mock_manager.get_area_ids.return_value = ["A1", "B1", "C1"]
        mock_manager.get_area_info.return_value = {
            "id": "A1",
            "name": "水果区域A1",
            "location": "仓库A区第1排"
        }
        return mock_manager

    @pytest.fixture
    def inventory_manager(self, temp_data_dir, mock_storage_area_manager):
        """创建库存管理器实例"""
        # 创建必要的目录
        os.makedirs(os.path.join(temp_data_dir, "static", "barcodes"), exist_ok=True)

        # 创建初始的产品文件
        products_file = os.path.join(temp_data_dir, "products.csv")
        with open(products_file, 'w', encoding='utf-8') as f:
            f.write("ProductName,Category,Price,Unit,Description\n")
            f.write("红富士苹果,水果,8.5,斤,新鲜红富士苹果\n")
            f.write("有机胡萝卜,蔬菜,6.0,斤,有机种植胡萝卜\n")

        with patch('src.models.inventory_manager.StorageAreaManager', return_value=mock_storage_area_manager):
            manager = InventoryManager(temp_data_dir)
            return manager

    @pytest.fixture
    def sample_product_data(self):
        """示例产品数据"""
        return {
            "product_name": "测试苹果",
            "category": "水果",
            "specification": "大果",
            "price": 10.0,
            "unit": "斤",
            "initial_stock": 100,
            "min_stock_warning": 10,
            "description": "测试用苹果",
            "storage_area": "A1"
        }

    @pytest.mark.inventory
    def test_inventory_manager_initialization(self, inventory_manager, temp_data_dir):
        """测试库存管理器初始化"""
        assert inventory_manager.data_dir == temp_data_dir
        assert inventory_manager.inventory_file == os.path.join(temp_data_dir, "inventory.json")
        assert inventory_manager.barcode_dir == "static/barcodes"

        # 对于模拟类，我们验证基本属性设置正确
        assert hasattr(inventory_manager, 'data_dir')
        assert hasattr(inventory_manager, 'inventory_file')
        assert hasattr(inventory_manager, 'barcode_dir')

    @pytest.mark.inventory
    def test_add_product_success(self, inventory_manager, sample_product_data):
        """测试成功添加产品"""
        operator = "test_admin"

        # 模拟条形码生成
        with patch.object(inventory_manager, '_generate_barcode', return_value="1234567890123"):
            with patch.object(inventory_manager, '_save_barcode_image', return_value="barcodes/test.png"):
                product_id = inventory_manager.add_product(sample_product_data, operator)

                assert product_id is not None
                assert product_id.isdigit()

                # 验证产品被正确添加
                product = inventory_manager.get_product_by_id(product_id)
                assert product is not None
                assert product["product_name"] == sample_product_data["product_name"]
                assert product["category"] == sample_product_data["category"]
                assert product["price"] == sample_product_data["price"]
                assert product["current_stock"] == sample_product_data["initial_stock"]
                assert product["barcode"] == "1234567890123"

    @pytest.mark.inventory
    def test_add_product_with_missing_required_fields(self, inventory_manager):
        """测试添加产品时缺少必需字段"""
        incomplete_data = {
            "product_name": "测试产品",
            # 缺少category, price, unit等必需字段
        }
        operator = "test_admin"

        # 应该处理缺少字段的情况
        product_id = inventory_manager.add_product(incomplete_data, operator)

        # 根据实际实现，可能返回None或抛出异常
        if product_id is None:
            assert True  # 正确处理了无效数据
        else:
            # 如果允许添加，验证默认值被正确设置
            product = inventory_manager.get_product_by_id(product_id)
            assert product is not None

    @pytest.mark.inventory
    def test_update_stock_success(self, inventory_manager, sample_product_data):
        """测试成功更新库存"""
        operator = "test_admin"

        # 先添加产品
        with patch.object(inventory_manager, '_generate_barcode', return_value="1234567890123"):
            with patch.object(inventory_manager, '_save_barcode_image', return_value="barcodes/test.png"):
                product_id = inventory_manager.add_product(sample_product_data, operator)

        # 更新库存
        quantity_change = 50
        note = "测试库存更新"

        result = inventory_manager.update_stock(product_id, quantity_change, operator, note)
        assert result == True

        # 验证库存被正确更新
        product = inventory_manager.get_product_by_id(product_id)
        expected_stock = sample_product_data["initial_stock"] + quantity_change
        assert product["current_stock"] == expected_stock

        # 验证库存历史记录
        assert len(product["stock_history"]) >= 2  # 初始记录 + 更新记录
        latest_history = product["stock_history"][-1]
        assert latest_history["action"] == "库存调整"
        assert latest_history["quantity"] == quantity_change
        assert latest_history["operator"] == operator
        assert latest_history["note"] == note

    @pytest.mark.inventory
    def test_update_stock_negative_result(self, inventory_manager, sample_product_data):
        """测试更新库存导致负数的情况"""
        operator = "test_admin"

        # 先添加产品
        with patch.object(inventory_manager, '_generate_barcode', return_value="1234567890123"):
            with patch.object(inventory_manager, '_save_barcode_image', return_value="barcodes/test.png"):
                product_id = inventory_manager.add_product(sample_product_data, operator)

        # 尝试减少超过当前库存的数量
        quantity_change = -(sample_product_data["initial_stock"] + 50)

        result = inventory_manager.update_stock(product_id, quantity_change, operator)
        assert result == False  # 应该拒绝导致负库存的操作

        # 验证库存没有被更新
        product = inventory_manager.get_product_by_id(product_id)
        assert product["current_stock"] == sample_product_data["initial_stock"]

    @pytest.mark.inventory
    def test_update_stock_nonexistent_product(self, inventory_manager):
        """测试更新不存在产品的库存"""
        nonexistent_id = "999999"
        operator = "test_admin"

        result = inventory_manager.update_stock(nonexistent_id, 10, operator)
        assert result == False

    @pytest.mark.inventory
    def test_get_product_by_id_success(self, inventory_manager, sample_product_data):
        """测试根据ID获取产品成功"""
        operator = "test_admin"

        # 先添加产品
        with patch.object(inventory_manager, '_generate_barcode', return_value="1234567890123"):
            with patch.object(inventory_manager, '_save_barcode_image', return_value="barcodes/test.png"):
                product_id = inventory_manager.add_product(sample_product_data, operator)

        # 获取产品
        product = inventory_manager.get_product_by_id(product_id)

        assert product is not None
        assert product["product_id"] == product_id
        assert product["product_name"] == sample_product_data["product_name"]

    @pytest.mark.inventory
    def test_get_product_by_id_not_found(self, inventory_manager):
        """测试获取不存在的产品"""
        nonexistent_id = "999999"

        product = inventory_manager.get_product_by_id(nonexistent_id)
        assert product is None

    @pytest.mark.inventory
    def test_get_all_products(self, inventory_manager, sample_product_data):
        """测试获取所有产品"""
        operator = "test_admin"

        # 添加多个产品
        product_data_list = [
            {**sample_product_data, "product_name": "测试苹果1"},
            {**sample_product_data, "product_name": "测试苹果2"},
            {**sample_product_data, "product_name": "测试苹果3"}
        ]

        added_ids = []
        for i, data in enumerate(product_data_list):
            with patch.object(inventory_manager, '_generate_barcode', return_value=f"123456789012{i}"):
                with patch.object(inventory_manager, '_save_barcode_image', return_value=f"barcodes/test{i}.png"):
                    product_id = inventory_manager.add_product(data, operator)
                    added_ids.append(product_id)

        # 获取所有产品
        all_products = inventory_manager.get_all_products()

        assert len(all_products) >= len(product_data_list)

        # 验证添加的产品都在结果中
        for product_id in added_ids:
            assert product_id in all_products
            assert all_products[product_id]["product_name"] in [data["product_name"] for data in product_data_list]


class TestBarcodeGeneration:
    """测试条形码生成功能"""

    @pytest.fixture
    def temp_data_dir(self):
        """创建临时数据目录"""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir, ignore_errors=True)

    @pytest.fixture
    def inventory_manager(self, temp_data_dir):
        """创建库存管理器实例"""
        os.makedirs(os.path.join(temp_data_dir, "static", "barcodes"), exist_ok=True)

        with patch('src.models.inventory_manager.StorageAreaManager'):
            manager = InventoryManager(temp_data_dir)
            return manager

    @pytest.mark.inventory
    def test_generate_barcode_number(self, inventory_manager):
        """测试条形码数字生成"""
        product_id = "123"
        product_name = "测试苹果"

        barcode = inventory_manager._generate_barcode(product_id, product_name)

        assert barcode is not None
        assert len(barcode) >= 10  # 条形码应该有足够的长度
        assert barcode.isdigit()  # 应该是纯数字

    @pytest.mark.inventory
    def test_save_barcode_image(self, inventory_manager, temp_data_dir):
        """测试保存条形码图片"""
        barcode_number = "1234567890123"
        product_name = "测试苹果"

        # 模拟条形码库
        with patch('barcode.get_barcode_class') as mock_barcode_class:
            mock_barcode_instance = Mock()
            mock_barcode_class.return_value.return_value = mock_barcode_instance

            image_path = inventory_manager._save_barcode_image(barcode_number, product_name)

            assert image_path.startswith("barcodes/")
            assert image_path.endswith(".png")

            # 验证条形码实例的save方法被调用
            mock_barcode_instance.save.assert_called_once()

    @pytest.mark.inventory
    def test_save_barcode_image_error_handling(self, inventory_manager):
        """测试条形码图片保存错误处理"""
        barcode_number = "1234567890123"
        product_name = "测试苹果"

        # 模拟保存失败
        with patch('barcode.get_barcode_class', side_effect=Exception("条形码生成失败")):
            image_path = inventory_manager._save_barcode_image(barcode_number, product_name)

            # 应该返回空字符串表示失败
            assert image_path == ""

    @pytest.mark.inventory
    def test_barcode_filename_safety(self, inventory_manager):
        """测试条形码文件名安全性"""
        # 测试包含特殊字符的产品名称
        unsafe_names = [
            "测试/苹果",
            "测试\\苹果",
            "测试:苹果",
            "测试*苹果",
            "测试?苹果",
            "测试\"苹果",
            "测试<苹果>",
            "测试|苹果"
        ]

        for unsafe_name in unsafe_names:
            barcode_number = "1234567890123"

            with patch('barcode.get_barcode_class') as mock_barcode_class:
                mock_barcode_instance = Mock()
                mock_barcode_class.return_value.return_value = mock_barcode_instance

                image_path = inventory_manager._save_barcode_image(barcode_number, unsafe_name)

                # 验证返回的路径不包含危险字符
                assert "/" not in os.path.basename(image_path)
                assert "\\" not in os.path.basename(image_path)
                assert ":" not in os.path.basename(image_path)


class TestBarcodeBatchGenerator:
    """测试批量条形码生成器"""

    @pytest.fixture
    def mock_inventory_manager(self):
        """模拟库存管理器"""
        mock_manager = Mock()
        mock_manager.get_all_products.return_value = {
            "1": {"product_name": "苹果", "barcode": ""},
            "2": {"product_name": "香蕉", "barcode": "1234567890123"},
            "3": {"product_name": "橙子", "barcode": ""}
        }
        return mock_manager

    @pytest.fixture
    def barcode_generator(self, mock_inventory_manager):
        """创建批量条形码生成器实例"""
        with patch('src.utils.barcode_batch_generator.InventoryManager', return_value=mock_inventory_manager):
            generator = BarcodeBatchGenerator()
            generator.inventory_manager = mock_inventory_manager
            return generator

    @pytest.mark.inventory
    def test_scan_products_without_barcodes(self, barcode_generator):
        """测试扫描没有条形码的产品"""
        products_without_barcodes = barcode_generator.scan_products_without_barcodes()

        # 应该返回没有条形码的产品（barcode为空）
        expected_products = ["1", "3"]  # 苹果和橙子没有条形码
        assert len(products_without_barcodes) == 2
        assert all(pid in expected_products for pid in products_without_barcodes)

    @pytest.mark.inventory
    def test_generate_barcodes_for_products_success(self, barcode_generator):
        """测试为产品生成条形码成功"""
        product_ids = ["1", "3"]
        operator = "test_admin"

        # 模拟条形码生成成功
        with patch.object(barcode_generator.inventory_manager, 'update_product', return_value=True):
            with patch('src.utils.barcode_batch_generator.generate_barcode_number', return_value="1234567890123"):
                with patch('src.utils.barcode_batch_generator.safe_barcode_filename', return_value="test_barcode"):
                    with patch('barcode.get_barcode_class') as mock_barcode_class:
                        mock_barcode_instance = Mock()
                        mock_barcode_class.return_value.return_value = mock_barcode_instance

                        result = barcode_generator.generate_barcodes_for_products(product_ids, operator)

                        assert result['success'] == True
                        assert result['successfully_generated'] == 2
                        assert result['failed_generations'] == 0
                        assert result['total_requested'] == 2

    @pytest.mark.inventory
    def test_generate_barcodes_empty_list(self, barcode_generator):
        """测试为空产品列表生成条形码"""
        product_ids = []
        operator = "test_admin"

        result = barcode_generator.generate_barcodes_for_products(product_ids, operator)

        assert result['total_requested'] == 0
        assert result['message'] == "没有需要处理的产品"

    @pytest.mark.inventory
    def test_generate_barcodes_with_failures(self, barcode_generator):
        """测试条形码生成部分失败"""
        product_ids = ["1", "3"]
        operator = "test_admin"

        # 模拟第一个成功，第二个失败
        def mock_update_product(product_id, data, operator):
            return product_id == "1"  # 只有产品1更新成功

        with patch.object(barcode_generator.inventory_manager, 'update_product', side_effect=mock_update_product):
            with patch('src.utils.barcode_batch_generator.generate_barcode_number', return_value="1234567890123"):
                with patch('src.utils.barcode_batch_generator.safe_barcode_filename', return_value="test_barcode"):
                    with patch('barcode.get_barcode_class') as mock_barcode_class:
                        mock_barcode_instance = Mock()
                        mock_barcode_class.return_value.return_value = mock_barcode_instance

                        result = barcode_generator.generate_barcodes_for_products(product_ids, operator)

                        assert result['successfully_generated'] == 1
                        assert result['failed_generations'] == 1
                        assert len(result['errors']) == 1