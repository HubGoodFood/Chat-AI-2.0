# -*- coding: utf-8 -*-
"""
数据迁移服务 - 从JSON文件迁移到数据库
"""
import os
import json
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from ..database.database_config import db_config
from ..database.models import Product, StockHistory, AdminUser, Feedback, StorageArea, PickupLocation, OperationLog
from ..repositories.product_repository import ProductRepository
import hashlib
import secrets

logger = logging.getLogger(__name__)


class DataMigrationService:
    """数据迁移服务"""
    
    def __init__(self):
        self.data_path = os.path.join(os.getcwd(), 'data')
        self.backup_path = os.path.join(self.data_path, 'backups')
        os.makedirs(self.backup_path, exist_ok=True)
    
    def migrate_all_data(self) -> Dict[str, Any]:
        """迁移所有数据"""
        results = {
            'products': 0,
            'admin_users': 0,
            'feedback': 0,
            'storage_areas': 0,
            'pickup_locations': 0,
            'operation_logs': 0,
            'errors': []
        }
        
        try:
            with db_config.get_session() as session:
                # 按依赖顺序迁移
                results['admin_users'] = self._migrate_admin_users(session)
                results['storage_areas'] = self._migrate_storage_areas(session)
                results['pickup_locations'] = self._migrate_pickup_locations(session)
                results['products'] = self._migrate_products(session)
                results['feedback'] = self._migrate_feedback(session)
                results['operation_logs'] = self._migrate_operation_logs(session)
                
                logger.info(f"数据迁移完成: {results}")
                return results
                
        except Exception as e:
            logger.error(f"数据迁移失败: {e}")
            results['errors'].append(str(e))
            return results
    
    def _migrate_products(self, session: Session) -> int:
        """迁移产品数据"""
        try:
            products_file = os.path.join(self.data_path, 'products.csv')
            inventory_file = os.path.join(self.data_path, 'inventory.json')
            
            if not os.path.exists(products_file) or not os.path.exists(inventory_file):
                logger.warning("产品数据文件不存在，跳过迁移")
                return 0
            
            # 备份原文件
            self._backup_file(products_file)
            self._backup_file(inventory_file)
            
            # 读取CSV产品数据
            import pandas as pd
            products_df = pd.read_csv(products_file)
            
            # 读取库存数据
            with open(inventory_file, 'r', encoding='utf-8') as f:
                inventory_data = json.load(f)
            
            migrated_count = 0
            product_repo = ProductRepository(session)
            
            for _, row in products_df.iterrows():
                try:
                    # 检查产品是否已存在
                    existing = product_repo.find_one_by(product_name=row['产品名称'])
                    if existing:
                        continue
                    
                    # 获取库存信息
                    current_stock = 0
                    product_inventory = inventory_data.get(row['产品名称'], {})
                    if isinstance(product_inventory, dict):
                        current_stock = product_inventory.get('current_stock', 0)
                    
                    # 创建产品
                    product = Product(
                        product_name=row['产品名称'],
                        category=row.get('分类', '未分类'),
                        specification=row.get('规格', ''),
                        price=float(row.get('价格', 0)),
                        unit=row.get('单位', '个'),
                        current_stock=current_stock,
                        min_stock_warning=int(row.get('最低库存警告', 10)),
                        description=row.get('描述', ''),
                        keywords=row.get('关键词', ''),
                        barcode=row.get('条码', ''),
                        barcode_image=row.get('条码图片', ''),
                        storage_area=row.get('存储区域', 'A1'),
                        status='active'
                    )
                    
                    session.add(product)
                    session.flush()
                    
                    # 如果有库存，记录初始库存历史
                    if current_stock > 0:
                        stock_history = StockHistory(
                            product_id=product.id,
                            action='initial_import',
                            quantity_change=current_stock,
                            quantity_before=0,
                            quantity_after=current_stock,
                            operator='system',
                            note='数据迁移初始导入'
                        )
                        session.add(stock_history)
                    
                    migrated_count += 1
                    
                except Exception as e:
                    logger.error(f"迁移产品失败 {row.get('产品名称', 'unknown')}: {e}")
                    continue
            
            session.flush()
            return migrated_count
            
        except Exception as e:
            logger.error(f"产品数据迁移失败: {e}")
            raise
    
    def _migrate_admin_users(self, session: Session) -> int:
        """迁移管理员用户数据"""
        try:
            admin_file = os.path.join(self.data_path, 'admin.json')
            if not os.path.exists(admin_file):
                logger.warning("管理员数据文件不存在，跳过迁移")
                return 0
            
            self._backup_file(admin_file)
            
            with open(admin_file, 'r', encoding='utf-8') as f:
                admin_data = json.load(f)
            
            migrated_count = 0
            
            for username, user_info in admin_data.items():
                try:
                    # 检查用户是否已存在
                    existing = session.query(AdminUser).filter(AdminUser.username == username).first()
                    if existing:
                        continue
                    
                    # 生成新的salt和密码哈希
                    salt = secrets.token_hex(16)
                    password = user_info.get('password', 'admin123')
                    password_hash = hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), 100000).hex()
                    
                    admin_user = AdminUser(
                        username=username,
                        password_hash=password_hash,
                        salt=salt,
                        email=user_info.get('email', f"{username}@example.com"),
                        full_name=user_info.get('full_name', username),
                        is_active=user_info.get('is_active', True),
                        is_super_admin=user_info.get('is_super_admin', False),
                        password_changed=False,
                        created_by='system'
                    )
                    
                    session.add(admin_user)
                    migrated_count += 1
                    
                except Exception as e:
                    logger.error(f"迁移管理员用户失败 {username}: {e}")
                    continue
            
            session.flush()
            return migrated_count
            
        except Exception as e:
            logger.error(f"管理员数据迁移失败: {e}")
            raise
    
    def _migrate_feedback(self, session: Session) -> int:
        """迁移反馈数据"""
        try:
            feedback_file = os.path.join(self.data_path, 'feedback.json')
            if not os.path.exists(feedback_file):
                logger.warning("反馈数据文件不存在，跳过迁移")
                return 0
            
            self._backup_file(feedback_file)
            
            with open(feedback_file, 'r', encoding='utf-8') as f:
                feedback_data = json.load(f)
            
            migrated_count = 0
            
            for feedback_info in feedback_data:
                try:
                    feedback = Feedback(
                        product_name=feedback_info.get('product_name', ''),
                        customer_wechat_name=feedback_info.get('customer_wechat_name', ''),
                        customer_group_number=feedback_info.get('customer_group_number', ''),
                        customer_phone=feedback_info.get('customer_phone', ''),
                        payment_status=feedback_info.get('payment_status', 'unknown'),
                        feedback_type=feedback_info.get('feedback_type', 'general'),
                        feedback_content=feedback_info.get('feedback_content', ''),
                        order_amount=float(feedback_info.get('order_amount', 0)),
                        processing_status='pending'
                    )
                    
                    session.add(feedback)
                    migrated_count += 1
                    
                except Exception as e:
                    logger.error(f"迁移反馈数据失败: {e}")
                    continue
            
            session.flush()
            return migrated_count
            
        except Exception as e:
            logger.error(f"反馈数据迁移失败: {e}")
            raise
    
    def _migrate_storage_areas(self, session: Session) -> int:
        """迁移存储区域数据"""
        try:
            storage_file = os.path.join(self.data_path, 'storage_areas.json')
            if not os.path.exists(storage_file):
                logger.warning("存储区域数据文件不存在，跳过迁移")
                return 0
            
            self._backup_file(storage_file)
            
            with open(storage_file, 'r', encoding='utf-8') as f:
                storage_data = json.load(f)
            
            migrated_count = 0
            
            for area_id, area_info in storage_data.items():
                try:
                    # 检查区域是否已存在
                    existing = session.query(StorageArea).filter(StorageArea.area_id == area_id).first()
                    if existing:
                        continue
                    
                    storage_area = StorageArea(
                        area_id=area_id,
                        area_name=area_info.get('area_name', area_id),
                        description=area_info.get('description', ''),
                        capacity=int(area_info.get('capacity', 1000)),
                        status=area_info.get('status', 'active'),
                        created_by='system'
                    )
                    
                    session.add(storage_area)
                    migrated_count += 1
                    
                except Exception as e:
                    logger.error(f"迁移存储区域失败 {area_id}: {e}")
                    continue
            
            session.flush()
            return migrated_count
            
        except Exception as e:
            logger.error(f"存储区域数据迁移失败: {e}")
            raise
    
    def _migrate_pickup_locations(self, session: Session) -> int:
        """迁移取货点数据"""
        try:
            pickup_file = os.path.join(self.data_path, 'pickup_locations.json')
            if not os.path.exists(pickup_file):
                logger.warning("取货点数据文件不存在，跳过迁移")
                return 0
            
            self._backup_file(pickup_file)
            
            with open(pickup_file, 'r', encoding='utf-8') as f:
                pickup_data = json.load(f)
            
            migrated_count = 0
            
            for location_id, location_info in pickup_data.items():
                try:
                    # 检查取货点是否已存在
                    existing = session.query(PickupLocation).filter(PickupLocation.location_id == location_id).first()
                    if existing:
                        continue
                    
                    pickup_location = PickupLocation(
                        location_id=location_id,
                        location_name=location_info.get('location_name', location_id),
                        address=location_info.get('address', ''),
                        phone=location_info.get('phone', ''),
                        contact_person=location_info.get('contact_person', ''),
                        business_hours=location_info.get('business_hours', ''),
                        description=location_info.get('description', ''),
                        status=location_info.get('status', 'active'),
                        created_by='system'
                    )
                    
                    session.add(pickup_location)
                    migrated_count += 1
                    
                except Exception as e:
                    logger.error(f"迁移取货点失败 {location_id}: {e}")
                    continue
            
            session.flush()
            return migrated_count
            
        except Exception as e:
            logger.error(f"取货点数据迁移失败: {e}")
            raise
    
    def _migrate_operation_logs(self, session: Session) -> int:
        """迁移操作日志数据"""
        try:
            logs_file = os.path.join(self.data_path, 'operation_logs.json')
            if not os.path.exists(logs_file):
                logger.warning("操作日志文件不存在，跳过迁移")
                return 0
            
            self._backup_file(logs_file)
            
            with open(logs_file, 'r', encoding='utf-8') as f:
                logs_data = json.load(f)
            
            migrated_count = 0
            
            for log_info in logs_data:
                try:
                    operation_log = OperationLog(
                        operator=log_info.get('operator', 'unknown'),
                        operation_type=log_info.get('operation_type', 'unknown'),
                        target_type=log_info.get('target_type', 'unknown'),
                        target_id=str(log_info.get('target_id', '')),
                        details=json.dumps(log_info.get('details', {}), ensure_ascii=False),
                        result=log_info.get('result', 'success'),
                        ip_address=log_info.get('ip_address', ''),
                        user_agent=log_info.get('user_agent', ''),
                        timestamp=datetime.fromisoformat(log_info['timestamp']) if 'timestamp' in log_info else datetime.utcnow()
                    )
                    
                    session.add(operation_log)
                    migrated_count += 1
                    
                except Exception as e:
                    logger.error(f"迁移操作日志失败: {e}")
                    continue
            
            session.flush()
            return migrated_count
            
        except Exception as e:
            logger.error(f"操作日志迁移失败: {e}")
            raise
    
    def _backup_file(self, file_path: str):
        """备份文件"""
        try:
            if os.path.exists(file_path):
                filename = os.path.basename(file_path)
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                backup_name = f"{timestamp}_{filename}"
                backup_path = os.path.join(self.backup_path, backup_name)
                
                import shutil
                shutil.copy2(file_path, backup_path)
                logger.info(f"文件已备份: {backup_path}")
        except Exception as e:
            logger.error(f"备份文件失败 {file_path}: {e}")
    
    def rollback_migration(self) -> bool:
        """回滚迁移（删除所有数据库数据，恢复JSON文件）"""
        try:
            # 清空数据库表
            with db_config.get_session() as session:
                session.query(OperationLog).delete()
                session.query(StockHistory).delete()
                session.query(Feedback).delete()
                session.query(Product).delete()
                session.query(PickupLocation).delete()
                session.query(StorageArea).delete()
                session.query(AdminUser).delete()
                session.flush()
            
            logger.info("数据库数据已清除")
            return True
            
        except Exception as e:
            logger.error(f"回滚迁移失败: {e}")
            return False
    
    def verify_migration(self) -> Dict[str, Any]:
        """验证迁移结果"""
        results = {}
        
        try:
            with db_config.get_session() as session:
                results['products_count'] = session.query(Product).count()
                results['admin_users_count'] = session.query(AdminUser).count()
                results['feedback_count'] = session.query(Feedback).count()
                results['storage_areas_count'] = session.query(StorageArea).count()
                results['pickup_locations_count'] = session.query(PickupLocation).count()
                results['operation_logs_count'] = session.query(OperationLog).count()
                results['stock_history_count'] = session.query(StockHistory).count()
                
                # 数据一致性检查
                products_with_history = session.query(Product).join(StockHistory).count()
                results['data_consistency'] = {
                    'products_with_stock_history': products_with_history
                }
                
        except Exception as e:
            logger.error(f"验证迁移失败: {e}")
            results['error'] = str(e)
        
        return results


# 全局迁移服务实例
migration_service = DataMigrationService()