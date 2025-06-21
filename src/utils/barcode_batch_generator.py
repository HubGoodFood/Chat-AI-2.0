# -*- coding: utf-8 -*-
"""
批量条形码生成工具模块
提供批量为产品生成条形码的功能，可以集成到Web管理界面中

主要功能:
1. 检查产品条形码状态
2. 批量生成缺失的条形码
3. 提供进度反馈和错误处理
4. 遵循简约设计原则
"""

import os
from typing import List, Dict, Tuple, Optional
from datetime import datetime

from ..models.inventory_manager import InventoryManager
from .logger_config import get_logger

# 初始化日志记录器
logger = get_logger('barcode_batch_generator')

class BarcodeBatchGenerator:
    """批量条形码生成器 - 简约版"""
    
    def __init__(self):
        """初始化生成器"""
        self.inventory_manager = InventoryManager()
    
    def check_products_barcode_status(self) -> Dict:
        """
        检查所有产品的条形码状态
        
        Returns:
            Dict: 包含统计信息和需要处理的产品列表
        """
        try:
            inventory_data = self.inventory_manager._load_inventory()
            
            result = {
                'total_products': 0,
                'products_with_barcode': 0,
                'products_without_barcode': 0,
                'products_need_regeneration': 0,
                'products_to_process': [],
                'success': True,
                'message': ''
            }
            
            for product_id, product_data in inventory_data["products"].items():
                result['total_products'] += 1
                
                barcode_status = self._check_single_product_barcode(product_data)
                
                if barcode_status['needs_generation']:
                    result['products_without_barcode'] += 1
                    result['products_to_process'].append({
                        'product_id': product_id,
                        'product_name': product_data.get('product_name', '').strip(),
                        'reason': barcode_status['reason']
                    })
                elif barcode_status['needs_regeneration']:
                    result['products_need_regeneration'] += 1
                    result['products_to_process'].append({
                        'product_id': product_id,
                        'product_name': product_data.get('product_name', '').strip(),
                        'reason': barcode_status['reason']
                    })
                else:
                    result['products_with_barcode'] += 1
            
            result['message'] = f"扫描完成: 总计 {result['total_products']} 个产品"
            logger.info(result['message'])
            
            return result
            
        except Exception as e:
            error_msg = f"检查产品条形码状态失败: {e}"
            logger.error(error_msg)
            return {
                'success': False,
                'message': error_msg,
                'total_products': 0,
                'products_with_barcode': 0,
                'products_without_barcode': 0,
                'products_need_regeneration': 0,
                'products_to_process': []
            }
    
    def _check_single_product_barcode(self, product_data: Dict) -> Dict:
        """
        检查单个产品的条形码状态
        
        Args:
            product_data: 产品数据
            
        Returns:
            Dict: 条形码状态信息
        """
        result = {
            'needs_generation': False,
            'needs_regeneration': False,
            'reason': ''
        }
        
        # 检查条形码字段
        barcode = product_data.get('barcode', '')
        if not barcode or barcode.strip() == '':
            result['needs_generation'] = True
            result['reason'] = '缺少条形码数字'
            return result
        
        # 检查条形码图片字段
        barcode_image = product_data.get('barcode_image', '')
        if not barcode_image or barcode_image.strip() == '':
            result['needs_regeneration'] = True
            result['reason'] = '缺少条形码图片路径'
            return result
        
        # 检查条形码图片文件是否存在
        if barcode_image:
            # 处理路径格式
            if barcode_image.startswith('barcodes/'):
                image_path = os.path.join('static', barcode_image)
            else:
                image_path = os.path.join('static', 'barcodes', barcode_image)
            
            if not os.path.exists(image_path):
                result['needs_regeneration'] = True
                result['reason'] = '条形码图片文件不存在'
                return result
        
        return result
    
    def generate_barcodes_for_products(self, product_ids: List[str], operator: str = "batch_generator") -> Dict:
        """
        为指定的产品列表生成条形码
        
        Args:
            product_ids: 产品ID列表
            operator: 操作员名称
            
        Returns:
            Dict: 生成结果统计
        """
        result = {
            'total_requested': len(product_ids),
            'successfully_generated': 0,
            'failed_generations': 0,
            'errors': [],
            'success': True,
            'message': ''
        }
        
        if not product_ids:
            result['message'] = "没有需要处理的产品"
            return result
        
        # 确保条形码目录存在
        barcode_dir = "static/barcodes"
        if not os.path.exists(barcode_dir):
            os.makedirs(barcode_dir)
            logger.info(f"创建条形码目录: {barcode_dir}")
        
        for product_id in product_ids:
            try:
                # 使用现有的条形码重新生成方法
                success = self.inventory_manager.regenerate_barcode(product_id, operator)
                
                if success:
                    result['successfully_generated'] += 1
                    logger.info(f"成功为产品 {product_id} 生成条形码")
                else:
                    result['failed_generations'] += 1
                    error_msg = f"为产品 {product_id} 生成条形码失败"
                    result['errors'].append(error_msg)
                    logger.warning(error_msg)
                    
            except Exception as e:
                result['failed_generations'] += 1
                error_msg = f"处理产品 {product_id} 时发生错误: {e}"
                result['errors'].append(error_msg)
                logger.error(error_msg)
        
        # 设置结果消息
        if result['failed_generations'] == 0:
            result['message'] = f"成功为 {result['successfully_generated']} 个产品生成条形码"
        else:
            result['message'] = f"生成完成: 成功 {result['successfully_generated']} 个, 失败 {result['failed_generations']} 个"
            result['success'] = result['successfully_generated'] > 0
        
        logger.info(result['message'])
        return result
    
    def generate_all_missing_barcodes(self, operator: str = "batch_generator") -> Dict:
        """
        为所有缺少条形码的产品生成条形码
        
        Args:
            operator: 操作员名称
            
        Returns:
            Dict: 生成结果
        """
        # 首先检查产品状态
        status_check = self.check_products_barcode_status()
        
        if not status_check['success']:
            return status_check
        
        if not status_check['products_to_process']:
            return {
                'success': True,
                'message': '所有产品都已有条形码，无需生成',
                'total_requested': 0,
                'successfully_generated': 0,
                'failed_generations': 0,
                'errors': []
            }
        
        # 提取需要处理的产品ID
        product_ids = [p['product_id'] for p in status_check['products_to_process']]
        
        # 批量生成条形码
        return self.generate_barcodes_for_products(product_ids, operator)

# 便捷函数，供外部调用
def batch_generate_missing_barcodes(operator: str = "system") -> Dict:
    """
    便捷函数：批量生成所有缺失的条形码
    
    Args:
        operator: 操作员名称
        
    Returns:
        Dict: 生成结果
    """
    generator = BarcodeBatchGenerator()
    return generator.generate_all_missing_barcodes(operator)

def check_barcode_status() -> Dict:
    """
    便捷函数：检查所有产品的条形码状态
    
    Returns:
        Dict: 状态检查结果
    """
    generator = BarcodeBatchGenerator()
    return generator.check_products_barcode_status()
