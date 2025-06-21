# -*- coding: utf-8 -*-
"""
批量条形码生成脚本
为库存管理系统中所有尚未生成条形码的产品批量生成条形码

使用方法:
python scripts/batch_generate_barcodes.py

功能:
1. 扫描数据库中所有产品记录
2. 识别尚未生成条形码的产品
3. 使用python-barcode库生成Code128格式条形码
4. 更新数据库中的barcode字段
5. 保存条形码图片到static/barcodes/目录
6. 显示处理进度和结果统计
"""

import os
import sys
import json
from datetime import datetime
from typing import List, Dict, Tuple

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.models.inventory_manager import InventoryManager
from src.utils.logger_config import get_logger

# 初始化日志记录器
logger = get_logger('batch_barcode_generator')

class BatchBarcodeGenerator:
    """批量条形码生成器"""
    
    def __init__(self):
        """初始化批量条形码生成器"""
        self.inventory_manager = InventoryManager()
        self.stats = {
            'total_products': 0,
            'products_without_barcode': 0,
            'successfully_generated': 0,
            'failed_generations': 0,
            'errors': []
        }
    
    def scan_products_without_barcode(self) -> List[Tuple[str, Dict]]:
        """
        扫描所有没有条形码的产品
        
        Returns:
            List[Tuple[str, Dict]]: 产品ID和产品数据的元组列表
        """
        try:
            inventory_data = self.inventory_manager._load_inventory()
            products_without_barcode = []
            
            for product_id, product_data in inventory_data["products"].items():
                self.stats['total_products'] += 1
                
                # 检查产品是否缺少条形码
                if self._needs_barcode_generation(product_data):
                    products_without_barcode.append((product_id, product_data))
                    self.stats['products_without_barcode'] += 1
            
            logger.info(f"扫描完成: 总产品数 {self.stats['total_products']}, "
                       f"需要生成条形码的产品数 {self.stats['products_without_barcode']}")
            
            return products_without_barcode
            
        except Exception as e:
            error_msg = f"扫描产品失败: {e}"
            logger.error(error_msg)
            self.stats['errors'].append(error_msg)
            return []
    
    def _needs_barcode_generation(self, product_data: Dict) -> bool:
        """
        检查产品是否需要生成条形码
        
        Args:
            product_data: 产品数据
            
        Returns:
            bool: 是否需要生成条形码
        """
        # 检查条形码字段是否存在且不为空
        barcode = product_data.get('barcode', '')
        if not barcode or barcode.strip() == '':
            return True
        
        # 检查条形码图片字段是否存在且不为空
        barcode_image = product_data.get('barcode_image', '')
        if not barcode_image or barcode_image.strip() == '':
            return True
        
        # 检查条形码图片文件是否实际存在
        if barcode_image:
            # 构建完整的文件路径
            image_path = os.path.join('static', barcode_image.replace('barcodes/', ''))
            if not os.path.exists(image_path):
                logger.warning(f"条形码图片文件不存在: {image_path}")
                return True
        
        return False
    
    def generate_barcodes_batch(self, products_list: List[Tuple[str, Dict]]) -> None:
        """
        批量生成条形码
        
        Args:
            products_list: 需要生成条形码的产品列表
        """
        if not products_list:
            print("✅ 所有产品都已有条形码，无需生成。")
            return
        
        print(f"🔄 开始为 {len(products_list)} 个产品生成条形码...")
        print("-" * 60)
        
        for i, (product_id, product_data) in enumerate(products_list, 1):
            try:
                product_name = product_data.get('product_name', f'产品{product_id}')
                print(f"[{i}/{len(products_list)}] 正在处理: {product_name.strip()}")
                
                # 使用现有的条形码生成方法
                success = self.inventory_manager.regenerate_barcode(product_id, "batch_generator")
                
                if success:
                    self.stats['successfully_generated'] += 1
                    print(f"  ✅ 成功生成条形码")
                else:
                    self.stats['failed_generations'] += 1
                    error_msg = f"为产品 {product_id} ({product_name.strip()}) 生成条形码失败"
                    self.stats['errors'].append(error_msg)
                    print(f"  ❌ 生成失败")
                
            except Exception as e:
                self.stats['failed_generations'] += 1
                error_msg = f"处理产品 {product_id} 时发生错误: {e}"
                self.stats['errors'].append(error_msg)
                logger.error(error_msg)
                print(f"  ❌ 处理错误: {e}")
        
        print("-" * 60)
        self._print_summary()
    
    def _print_summary(self) -> None:
        """打印处理结果摘要"""
        print("\n📊 批量条形码生成结果摘要:")
        print("=" * 50)
        print(f"总产品数量:           {self.stats['total_products']}")
        print(f"需要生成条形码的产品:   {self.stats['products_without_barcode']}")
        print(f"成功生成条形码:       {self.stats['successfully_generated']}")
        print(f"生成失败:            {self.stats['failed_generations']}")
        
        if self.stats['errors']:
            print(f"\n❌ 错误详情 ({len(self.stats['errors'])} 个):")
            for i, error in enumerate(self.stats['errors'], 1):
                print(f"  {i}. {error}")
        
        if self.stats['successfully_generated'] > 0:
            print(f"\n✅ 成功为 {self.stats['successfully_generated']} 个产品生成了条形码！")
            print("📁 条形码图片已保存到: static/barcodes/ 目录")
        
        print("=" * 50)
    
    def run(self) -> None:
        """运行批量条形码生成流程"""
        print("🚀 启动批量条形码生成器")
        print("=" * 50)
        
        # 确保条形码目录存在
        barcode_dir = "static/barcodes"
        if not os.path.exists(barcode_dir):
            os.makedirs(barcode_dir)
            print(f"📁 创建条形码目录: {barcode_dir}")
        
        # 扫描需要生成条形码的产品
        print("🔍 正在扫描产品数据库...")
        products_without_barcode = self.scan_products_without_barcode()
        
        # 批量生成条形码
        self.generate_barcodes_batch(products_without_barcode)
        
        # 记录操作日志
        logger.info(f"批量条形码生成完成: 成功 {self.stats['successfully_generated']}, "
                   f"失败 {self.stats['failed_generations']}")

def main():
    """主函数"""
    try:
        generator = BatchBarcodeGenerator()
        generator.run()
        
    except KeyboardInterrupt:
        print("\n\n⚠️  用户中断操作")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ 程序执行失败: {e}")
        logger.error(f"批量条形码生成程序异常: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
