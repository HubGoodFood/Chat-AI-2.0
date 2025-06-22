# -*- coding: utf-8 -*-
"""
库存管理工作流集成测试

这个文件包含了库存管理系统的端到端集成测试，
验证产品管理、库存调整、条形码生成等完整业务流程。

测试场景：
1. 产品生命周期管理
2. 库存调整完整流程
3. 条形码生成和管理
4. 库存盘点工作流
5. 存储区域管理
6. 数据持久化验证

设计原则：
- 测试完整的业务流程
- 验证数据一致性
- 确保文件操作正确
- 检查权限控制
"""
import pytest
import json
import os
import tempfile
from unittest.mock import patch, Mock
from datetime import datetime

# 项目模块导入
from src.models.inventory_manager import InventoryManager


class TestInventoryWorkflows:
    """库存管理工作流集成测试类"""

    @pytest.mark.integration
    @pytest.mark.inventory
    def test_product_lifecycle_workflow(self, integration_data_dir):
        """
        测试产品生命周期管理工作流
        
        验证：创建产品 -> 更新信息 -> 库存调整 -> 条形码生成 -> 删除产品
        """
        # 初始化库存管理器
        inventory_manager = InventoryManager(data_dir=integration_data_dir)
        
        # 1. 创建新产品
        product_data = {
            'product_name': '集成测试苹果',
            'category': '时令水果',
            'specification': '大果',
            'price': 12.0,
            'unit': '斤',
            'initial_stock': 100,
            'min_stock_warning': 10,
            'description': '用于集成测试的苹果产品',
            'storage_area': 'A1'
        }
        
        product_id = inventory_manager.add_product(product_data, operator='test_admin')
        assert product_id is not None
        assert isinstance(product_id, str)
        
        # 2. 验证产品创建成功
        created_product = inventory_manager.get_product_by_id(product_id)
        assert created_product is not None
        assert created_product['product_name'] == product_data['product_name']
        assert created_product['current_stock'] == product_data['initial_stock']
        
        # 3. 更新产品信息
        update_data = {
            'price': 15.0,
            'description': '更新后的产品描述'
        }
        
        success = inventory_manager.update_product(product_id, update_data, operator='test_admin')
        assert success is True
        
        # 验证更新成功
        updated_product = inventory_manager.get_product_by_id(product_id)
        assert updated_product['price'] == 15.0
        assert updated_product['description'] == '更新后的产品描述'
        
        # 4. 库存调整
        stock_change = 50
        note = '集成测试库存增加'
        
        success = inventory_manager.update_stock(product_id, stock_change, 'test_admin', note)
        assert success is True
        
        # 验证库存调整
        product_after_stock_update = inventory_manager.get_product_by_id(product_id)
        expected_stock = product_data['initial_stock'] + stock_change
        assert product_after_stock_update['current_stock'] == expected_stock
        
        # 验证库存历史记录
        assert len(product_after_stock_update['stock_history']) >= 2
        latest_history = product_after_stock_update['stock_history'][-1]
        assert latest_history['quantity'] == stock_change
        assert latest_history['note'] == note
        
        # 5. 条形码生成
        barcode_result = inventory_manager.generate_barcode(product_id)
        assert barcode_result is True
        
        # 验证条形码信息
        product_with_barcode = inventory_manager.get_product_by_id(product_id)
        assert 'barcode' in product_with_barcode
        assert product_with_barcode['barcode'] is not None

    @pytest.mark.integration
    @pytest.mark.inventory
    def test_inventory_count_workflow(self, integration_data_dir):
        """
        测试库存盘点完整工作流
        
        验证：创建盘点 -> 添加盘点项目 -> 计算差异 -> 生成报告
        """
        # 初始化管理器
        inventory_manager = InventoryManager(data_dir=integration_data_dir)
        count_manager = InventoryCountManager(data_dir=integration_data_dir)
        
        # 1. 先创建一些测试产品
        product_data1 = {
            'product_name': '盘点测试产品1',
            'category': '测试类别',
            'specification': '规格1',
            'price': 10.0,
            'unit': '个',
            'initial_stock': 100,
            'min_stock_warning': 10,
            'description': '盘点测试产品1',
            'storage_area': 'A1'
        }
        
        product_id1 = inventory_manager.add_product(product_data1, operator='test_admin')
        assert product_id1 is not None
        
        product_data2 = {
            'product_name': '盘点测试产品2',
            'category': '测试类别',
            'specification': '规格2',
            'price': 20.0,
            'unit': '个',
            'initial_stock': 50,
            'min_stock_warning': 5,
            'description': '盘点测试产品2',
            'storage_area': 'A2'
        }
        
        product_id2 = inventory_manager.add_product(product_data2, operator='test_admin')
        assert product_id2 is not None
        
        # 2. 创建库存盘点
        count_data = {
            'title': '集成测试盘点',
            'description': '用于集成测试的库存盘点',
            'storage_areas': ['A1', 'A2']
        }
        
        count_id = count_manager.create_count(count_data, operator='test_admin')
        assert count_id is not None
        
        # 3. 添加盘点项目
        count_item1 = {
            'product_id': product_id1,
            'actual_quantity': 95,  # 比系统库存少5个
            'note': '实际盘点数量'
        }
        
        success = count_manager.add_count_item(count_id, count_item1, operator='test_admin')
        assert success is True
        
        count_item2 = {
            'product_id': product_id2,
            'actual_quantity': 55,  # 比系统库存多5个
            'note': '实际盘点数量'
        }
        
        success = count_manager.add_count_item(count_id, count_item2, operator='test_admin')
        assert success is True
        
        # 4. 完成盘点并计算差异
        success = count_manager.complete_count(count_id, operator='test_admin')
        assert success is True
        
        # 5. 验证盘点结果
        count_result = count_manager.get_count_by_id(count_id)
        assert count_result is not None
        assert count_result['status'] == 'completed'
        assert len(count_result['items']) == 2
        
        # 验证差异计算
        for item in count_result['items']:
            if item['product_id'] == product_id1:
                assert item['difference'] == -5  # 少了5个
            elif item['product_id'] == product_id2:
                assert item['difference'] == 5   # 多了5个

    @pytest.mark.integration
    @pytest.mark.inventory
    def test_storage_area_management_workflow(self, integration_data_dir):
        """
        测试存储区域管理工作流
        
        验证：创建存储区域 -> 分配产品 -> 区域统计 -> 更新区域信息
        """
        # 初始化库存管理器
        inventory_manager = InventoryManager(data_dir=integration_data_dir)
        
        # 1. 创建新的存储区域
        area_data = {
            'id': 'TEST_AREA',
            'name': '集成测试区域',
            'location': '测试仓库第1排'
        }
        
        success = inventory_manager.add_storage_area(area_data)
        assert success is True
        
        # 2. 验证存储区域创建
        areas = inventory_manager.get_storage_areas()
        test_area = next((area for area in areas if area['id'] == 'TEST_AREA'), None)
        assert test_area is not None
        assert test_area['name'] == '集成测试区域'
        
        # 3. 创建产品并分配到测试区域
        product_data = {
            'product_name': '区域测试产品',
            'category': '测试类别',
            'specification': '测试规格',
            'price': 10.0,
            'unit': '个',
            'initial_stock': 100,
            'min_stock_warning': 10,
            'description': '用于测试存储区域的产品',
            'storage_area': 'TEST_AREA'
        }
        
        product_id = inventory_manager.add_product(product_data, operator='test_admin')
        assert product_id is not None
        
        # 4. 验证产品分配到正确区域
        created_product = inventory_manager.get_product_by_id(product_id)
        assert created_product['storage_area'] == 'TEST_AREA'
        
        # 5. 获取区域产品统计
        area_stats = inventory_manager.get_area_statistics('TEST_AREA')
        assert area_stats is not None
        assert area_stats['product_count'] >= 1
        assert area_stats['total_stock'] >= 100

    @pytest.mark.integration
    @pytest.mark.inventory
    def test_barcode_generation_workflow(self, integration_data_dir):
        """
        测试条形码生成工作流
        
        验证：产品创建 -> 条形码生成 -> 文件保存 -> 批量生成
        """
        # 初始化库存管理器
        inventory_manager = InventoryManager(data_dir=integration_data_dir)
        
        # 1. 创建多个测试产品
        products_data = [
            {
                'product_name': f'条形码测试产品{i}',
                'category': '测试类别',
                'specification': f'规格{i}',
                'price': 10.0 + i,
                'unit': '个',
                'initial_stock': 100,
                'min_stock_warning': 10,
                'description': f'条形码测试产品{i}',
                'storage_area': 'A1'
            }
            for i in range(1, 4)
        ]
        
        product_ids = []
        for product_data in products_data:
            product_id = inventory_manager.add_product(product_data, operator='test_admin')
            assert product_id is not None
            product_ids.append(product_id)
        
        # 2. 单个条形码生成
        success = inventory_manager.generate_barcode(product_ids[0])
        assert success is True
        
        # 验证条形码信息
        product = inventory_manager.get_product_by_id(product_ids[0])
        assert 'barcode' in product
        assert product['barcode'] is not None
        
        # 3. 批量条形码生成
        batch_result = inventory_manager.batch_generate_barcodes()
        assert batch_result is not None
        assert 'generated_count' in batch_result
        assert batch_result['generated_count'] >= 2  # 至少为剩余的2个产品生成了条形码
        
        # 4. 验证所有产品都有条形码
        for product_id in product_ids:
            product = inventory_manager.get_product_by_id(product_id)
            assert 'barcode' in product
            assert product['barcode'] is not None

    @pytest.mark.integration
    @pytest.mark.inventory
    def test_data_persistence_workflow(self, integration_data_dir):
        """
        测试数据持久化工作流
        
        验证：数据修改 -> 文件保存 -> 重新加载 -> 数据一致性
        """
        # 1. 第一个管理器实例 - 创建数据
        inventory_manager1 = InventoryManager(data_dir=integration_data_dir)
        
        product_data = {
            'product_name': '持久化测试产品',
            'category': '测试类别',
            'specification': '测试规格',
            'price': 25.0,
            'unit': '个',
            'initial_stock': 200,
            'min_stock_warning': 20,
            'description': '用于测试数据持久化',
            'storage_area': 'A1'
        }
        
        product_id = inventory_manager1.add_product(product_data, operator='test_admin')
        assert product_id is not None
        
        # 进行库存调整
        success = inventory_manager1.update_stock(product_id, 30, 'test_admin', '持久化测试调整')
        assert success is True
        
        # 2. 第二个管理器实例 - 验证数据持久化
        inventory_manager2 = InventoryManager(data_dir=integration_data_dir)
        
        # 验证产品数据被正确保存和加载
        loaded_product = inventory_manager2.get_product_by_id(product_id)
        assert loaded_product is not None
        assert loaded_product['product_name'] == product_data['product_name']
        assert loaded_product['current_stock'] == 230  # 200 + 30
        
        # 验证库存历史记录也被保存
        assert len(loaded_product['stock_history']) >= 2
        latest_history = loaded_product['stock_history'][-1]
        assert latest_history['quantity'] == 30
        assert latest_history['note'] == '持久化测试调整'
        
        # 3. 验证文件确实存在
        inventory_file = os.path.join(integration_data_dir, 'inventory.json')
        assert os.path.exists(inventory_file)
        
        # 验证文件内容格式正确
        with open(inventory_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            assert 'products' in data
            assert len(data['products']) >= 1

    @pytest.mark.integration
    @pytest.mark.inventory
    @pytest.mark.slow
    def test_complex_inventory_scenario(self, integration_data_dir):
        """
        测试复杂库存管理场景
        
        验证：多产品 -> 多区域 -> 多次调整 -> 盘点 -> 报告生成
        """
        # 初始化管理器
        inventory_manager = InventoryManager(data_dir=integration_data_dir)
        count_manager = InventoryCountManager(data_dir=integration_data_dir)
        
        # 1. 创建多个存储区域
        areas = [
            {'id': 'COMPLEX_A', 'name': '复杂测试区域A', 'location': '仓库A区'},
            {'id': 'COMPLEX_B', 'name': '复杂测试区域B', 'location': '仓库B区'}
        ]
        
        for area in areas:
            success = inventory_manager.add_storage_area(area)
            assert success is True
        
        # 2. 创建多个产品分布在不同区域
        products_data = [
            {
                'product_name': '复杂场景产品A1',
                'category': '类别A',
                'specification': '规格A1',
                'price': 10.0,
                'unit': '个',
                'initial_stock': 100,
                'min_stock_warning': 10,
                'description': '复杂场景测试产品A1',
                'storage_area': 'COMPLEX_A'
            },
            {
                'product_name': '复杂场景产品A2',
                'category': '类别A',
                'specification': '规格A2',
                'price': 15.0,
                'unit': '个',
                'initial_stock': 80,
                'min_stock_warning': 8,
                'description': '复杂场景测试产品A2',
                'storage_area': 'COMPLEX_A'
            },
            {
                'product_name': '复杂场景产品B1',
                'category': '类别B',
                'specification': '规格B1',
                'price': 20.0,
                'unit': '个',
                'initial_stock': 60,
                'min_stock_warning': 6,
                'description': '复杂场景测试产品B1',
                'storage_area': 'COMPLEX_B'
            }
        ]
        
        product_ids = []
        for product_data in products_data:
            product_id = inventory_manager.add_product(product_data, operator='test_admin')
            assert product_id is not None
            product_ids.append(product_id)
        
        # 3. 进行多次库存调整
        adjustments = [
            (product_ids[0], 20, '销售出库'),
            (product_ids[1], -10, '损耗'),
            (product_ids[2], 15, '补货入库'),
            (product_ids[0], -5, '样品使用')
        ]
        
        for product_id, quantity, note in adjustments:
            success = inventory_manager.update_stock(product_id, quantity, 'test_admin', note)
            assert success is True
        
        # 4. 创建全面盘点
        count_data = {
            'title': '复杂场景全面盘点',
            'description': '覆盖所有区域的复杂场景盘点',
            'storage_areas': ['COMPLEX_A', 'COMPLEX_B']
        }
        
        count_id = count_manager.create_count(count_data, operator='test_admin')
        assert count_id is not None
        
        # 5. 添加盘点项目（模拟实际盘点结果）
        count_items = [
            {'product_id': product_ids[0], 'actual_quantity': 113, 'note': '实际盘点A1'},  # 期望115，差异-2
            {'product_id': product_ids[1], 'actual_quantity': 70, 'note': '实际盘点A2'},   # 期望70，无差异
            {'product_id': product_ids[2], 'actual_quantity': 77, 'note': '实际盘点B1'}    # 期望75，差异+2
        ]
        
        for item in count_items:
            success = count_manager.add_count_item(count_id, item, operator='test_admin')
            assert success is True
        
        # 6. 完成盘点
        success = count_manager.complete_count(count_id, operator='test_admin')
        assert success is True
        
        # 7. 验证复杂场景结果
        count_result = count_manager.get_count_by_id(count_id)
        assert count_result is not None
        assert count_result['status'] == 'completed'
        assert len(count_result['items']) == 3
        
        # 验证差异计算正确
        differences = {item['product_id']: item['difference'] for item in count_result['items']}
        assert differences[product_ids[0]] == -2  # 113 - 115
        assert differences[product_ids[1]] == 0   # 70 - 70
        assert differences[product_ids[2]] == 2   # 77 - 75
