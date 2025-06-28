# -*- coding: utf-8 -*-
"""
产品数据导入脚本
将CSV文件中的产品数据导入到数据库中
"""
import sys
import os
import pandas as pd
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from src.database.database_config import db_config, init_database
from src.database.models import Product
from src.models.operation_logger import operation_logger


def import_products_from_csv():
    """从CSV文件导入产品数据"""
    print("开始导入产品数据...")

    try:
        # 确保数据库表已创建
        print("检查数据库表...")
        init_database()

        # 读取CSV文件
        csv_path = project_root / 'data' / 'products.csv'
        if not csv_path.exists():
            print(f"CSV文件不存在: {csv_path}")
            return False

        print(f"读取CSV文件: {csv_path}")
        df = pd.read_csv(csv_path)

        # 清理列名中的空格
        df.columns = df.columns.str.strip()

        print(f"CSV文件包含 {len(df)} 行产品数据")
        print(f"列名: {list(df.columns)}")

        # 检查现有产品数量
        with db_config.get_session() as session:
            existing_count = session.query(Product).count()
            print(f"数据库中现有产品数量: {existing_count}")

            if existing_count > 0:
                response = input("数据库中已有产品数据，是否清空后重新导入？(y/N): ")
                if response.lower() == 'y':
                    session.query(Product).delete()
                    session.commit()
                    print("已清空现有产品数据")
                else:
                    print("将在现有数据基础上添加新产品")
        
        # 导入产品数据
        imported_count = 0
        skipped_count = 0
        
        with db_config.get_session() as session:
            for index, row in df.iterrows():
                try:
                    # 检查产品是否已存在
                    existing_product = session.query(Product).filter(
                        Product.product_name == row['ProductName'].strip()
                    ).first()
                    
                    if existing_product:
                        print(f"跳过已存在的产品: {row['ProductName']}")
                        skipped_count += 1
                        continue

                    # 创建新产品
                    product = Product(
                        product_name=row['ProductName'].strip(),
                        category=row['Category'].strip() if pd.notna(row['Category']) else '未分类',
                        specification=row['Specification'].strip() if pd.notna(row['Specification']) else '',
                        price=float(row['Price']) if pd.notna(row['Price']) else 0.0,
                        unit=row['Unit'].strip() if pd.notna(row['Unit']) else '个',
                        description=f"口感: {row.get('Taste', '')}, 产地: {row.get('Origin', '')}, 功效: {row.get('Benefits', '')}, 适宜人群: {row.get('SuitableFor', '')}".strip(),
                        keywords=row['Keywords'].strip() if pd.notna(row['Keywords']) else '',
                        current_stock=100,  # 默认库存
                        min_stock_warning=10,  # 默认预警值
                        status='active'
                    )

                    session.add(product)
                    imported_count += 1

                    if imported_count % 10 == 0:
                        print(f"已导入 {imported_count} 个产品...")

                except Exception as e:
                    print(f"导入产品失败 {row.get('ProductName', 'Unknown')}: {e}")
                    continue
            
            # 提交事务
            session.commit()
        
        print(f"产品数据导入完成!")
        print(f"导入统计:")
        print(f"   - 成功导入: {imported_count} 个产品")
        print(f"   - 跳过重复: {skipped_count} 个产品")
        print(f"   - 总计处理: {len(df)} 行数据")

        # 验证导入结果
        with db_config.get_session() as session:
            total_count = session.query(Product).count()
            print(f"验证: 数据库中现有 {total_count} 个产品")

        operation_logger.info(f"产品数据导入完成: 导入{imported_count}个, 跳过{skipped_count}个")
        return True

    except Exception as e:
        print(f"导入过程中发生错误: {e}")
        import traceback
        traceback.print_exc()
        operation_logger.error(f"产品数据导入失败: {e}")
        return False


if __name__ == '__main__':
    print("果蔬客服AI系统 - 产品数据导入工具")
    print("=" * 50)

    success = import_products_from_csv()

    if success:
        print("\n数据导入成功！现在可以启动AI客服系统了。")
    else:
        print("\n数据导入失败！请检查错误信息并重试。")

    print("=" * 50)
