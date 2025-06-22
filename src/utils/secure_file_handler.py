# -*- coding: utf-8 -*-
"""
安全文件处理模块
"""
import os
import hashlib
import uuid
from typing import Optional, Set, Tuple
from werkzeug.utils import secure_filename
from flask import send_file, abort, current_app
from .logger_config import get_logger

logger = get_logger('secure_file_handler')


class SecureFileHandler:
    """安全的文件处理类"""
    
    def __init__(self):
        # 允许的静态文件列表
        self.allowed_static_files = {
            'test_cleanup.html',
            'clean_test.html', 
            'test_customer_service.html'
        }
        
        # 允许的文件扩展名
        self.allowed_upload_extensions = {
            'png', 'jpg', 'jpeg', 'gif', 'bmp',  # 图片
            'pdf', 'doc', 'docx', 'txt',         # 文档
            'csv', 'xls', 'xlsx'                 # 数据文件
        }
        
        # 允许的条形码扩展名
        self.allowed_barcode_extensions = {'png', 'jpg', 'jpeg'}
        
        # 文件大小限制
        self.max_upload_size = 5 * 1024 * 1024  # 5MB
        self.max_barcode_size = 1 * 1024 * 1024  # 1MB
    
    def validate_static_file_access(self, filename: str) -> bool:
        """验证静态文件访问权限"""
        # 清理文件名
        secure_name = secure_filename(filename)
        if secure_name != filename:
            logger.warning(f"不安全的文件名被拒绝: {filename}")
            return False
        
        # 检查是否在允许列表中
        if filename not in self.allowed_static_files:
            logger.warning(f"未授权的静态文件访问: {filename}")
            return False
        
        return True
    
    def safe_send_static_file(self, filename: str, directory: str = '.') -> any:
        """安全发送静态文件"""
        try:
            # 验证文件访问权限
            if not self.validate_static_file_access(filename):
                abort(404, "文件不存在")
            
            # 构建安全路径
            directory_path = os.path.abspath(directory)
            file_path = os.path.abspath(os.path.join(directory, filename))
            
            # 防止路径遍历攻击
            if not file_path.startswith(directory_path):
                logger.warning(f"路径遍历攻击被阻止: {filename} -> {file_path}")
                abort(400, "不安全的文件路径")
            
            # 检查文件是否存在
            if not os.path.exists(file_path):
                logger.info(f"请求的文件不存在: {file_path}")
                abort(404, "文件不存在")
            
            # 检查是否为文件而不是目录
            if not os.path.isfile(file_path):
                logger.warning(f"尝试访问目录: {file_path}")
                abort(400, "无效的文件请求")
            
            logger.info(f"安全发送静态文件: {filename}")
            return send_file(file_path)
            
        except Exception as e:
            logger.error(f"发送静态文件失败: {e}")
            abort(500, "文件服务错误")
    
    def validate_barcode_access(self, product_id: str, require_auth: bool = True) -> Tuple[bool, str, Optional[str]]:
        """验证条形码文件访问"""
        try:
            # 验证产品ID格式
            if not product_id or not isinstance(product_id, str):
                return False, "无效的产品ID", None
            
            # 产品ID只能包含字母、数字、下划线、连字符
            if not self._is_safe_identifier(product_id):
                logger.warning(f"不安全的产品ID: {product_id}")
                return False, "不合法的产品ID格式", None
            
            # 如果需要认证，检查管理员权限
            if require_auth:
                from flask import session
                from src.models.admin_auth import AdminAuth
                
                admin_token = session.get('admin_token')
                if not admin_token:
                    return False, "需要管理员权限", None
                
                admin_auth = AdminAuth()
                if not admin_auth.verify_session(admin_token):
                    return False, "认证已过期", None
            
            # 获取产品信息
            from src.models.inventory_manager import InventoryManager
            inventory_manager = InventoryManager()
            product = inventory_manager.get_product_by_id(product_id)
            
            if not product:
                logger.info(f"产品不存在: {product_id}")
                return False, "产品不存在", None
            
            barcode_path = product.get('barcode_image')
            if not barcode_path:
                return False, "产品未生成条形码", None
            
            # 验证条形码文件路径
            static_path = os.path.abspath('static')
            full_path = os.path.abspath(os.path.join('static', barcode_path))
            
            # 防止路径遍历
            if not full_path.startswith(static_path):
                logger.warning(f"条形码路径遍历攻击被阻止: {barcode_path}")
                return False, "不安全的文件路径", None
            
            # 检查文件是否存在
            if not os.path.exists(full_path):
                logger.warning(f"条形码文件不存在: {full_path}")
                return False, "条形码文件不存在", None
            
            # 验证文件扩展名
            ext = os.path.splitext(full_path)[1][1:].lower()
            if ext not in self.allowed_barcode_extensions:
                logger.warning(f"不允许的条形码文件类型: {ext}")
                return False, "不支持的文件类型", None
            
            return True, "验证通过", full_path
            
        except Exception as e:
            logger.error(f"验证条形码访问失败: {e}")
            return False, "验证失败", None
    
    def validate_file_upload(self, file, allowed_extensions: Optional[Set[str]] = None, 
                           max_size: Optional[int] = None) -> Tuple[bool, str]:
        """验证文件上传"""
        try:
            if not file or file.filename == '':
                return False, "没有选择文件"
            
            # 使用默认扩展名如果未指定
            if allowed_extensions is None:
                allowed_extensions = self.allowed_upload_extensions
            
            # 使用默认大小限制如果未指定
            if max_size is None:
                max_size = self.max_upload_size
            
            # 检查文件名
            if not file.filename or '.' not in file.filename:
                return False, "文件名无效"
            
            # 检查扩展名
            ext = file.filename.rsplit('.', 1)[1].lower()
            if ext not in allowed_extensions:
                return False, f"不支持的文件类型，仅支持: {', '.join(allowed_extensions)}"
            
            # 检查文件大小
            file.seek(0, os.SEEK_END)
            file_size = file.tell()
            file.seek(0)  # 重置文件指针
            
            if file_size > max_size:
                return False, f"文件大小超过限制 ({max_size / 1024 / 1024:.1f}MB)"
            
            if file_size == 0:
                return False, "文件为空"
            
            # 验证文件内容（基础MIME类型检查）
            if not self._validate_file_content(file, ext):
                return False, "文件内容与扩展名不匹配"
            
            return True, "文件验证通过"
            
        except Exception as e:
            logger.error(f"文件上传验证失败: {e}")
            return False, "文件验证失败"
    
    def generate_safe_filename(self, original_filename: str, prefix: str = '') -> str:
        """生成安全的文件名"""
        try:
            # 获取文件扩展名
            if '.' in original_filename:
                name, ext = original_filename.rsplit('.', 1)
                ext = '.' + ext.lower()
            else:
                name = original_filename
                ext = ''
            
            # 清理原始文件名
            safe_name = secure_filename(name)
            
            # 限制长度
            if len(safe_name) > 50:
                safe_name = safe_name[:50]
            
            # 生成唯一标识符
            unique_id = str(uuid.uuid4().hex)[:8]
            
            # 组合文件名
            if prefix:
                final_name = f"{prefix}_{unique_id}_{safe_name}{ext}"
            else:
                final_name = f"{unique_id}_{safe_name}{ext}"
            
            return final_name
            
        except Exception as e:
            logger.error(f"生成安全文件名失败: {e}")
            # 降级方案：使用纯UUID
            return f"{uuid.uuid4().hex}.unknown"
    
    def safe_file_path(self, base_dir: str, filename: str) -> Tuple[bool, str, Optional[str]]:
        """构建安全的文件路径"""
        try:
            # 确保基础目录存在
            base_path = os.path.abspath(base_dir)
            if not os.path.exists(base_path):
                os.makedirs(base_path, exist_ok=True)
            
            # 构建文件路径
            file_path = os.path.abspath(os.path.join(base_path, filename))
            
            # 验证路径安全性
            if not file_path.startswith(base_path):
                logger.warning(f"路径遍历攻击被阻止: {filename}")
                return False, "不安全的文件路径", None
            
            return True, "路径验证通过", file_path
            
        except Exception as e:
            logger.error(f"构建安全文件路径失败: {e}")
            return False, "路径构建失败", None
    
    def _is_safe_identifier(self, identifier: str) -> bool:
        """检查标识符是否安全"""
        import re
        # 只允许字母、数字、下划线、连字符
        return bool(re.match(r'^[a-zA-Z0-9_-]+$', identifier))
    
    def _validate_file_content(self, file, expected_ext: str) -> bool:
        """验证文件内容与扩展名是否匹配"""
        try:
            # 读取文件头部字节
            file.seek(0)
            header = file.read(16)
            file.seek(0)  # 重置文件指针
            
            # 常见文件类型的魔数检查
            file_signatures = {
                'png': [b'\x89\x50\x4E\x47\x0D\x0A\x1A\x0A'],
                'jpg': [b'\xFF\xD8\xFF\xE0', b'\xFF\xD8\xFF\xE1', b'\xFF\xD8\xFF\xDB'],
                'jpeg': [b'\xFF\xD8\xFF\xE0', b'\xFF\xD8\xFF\xE1', b'\xFF\xD8\xFF\xDB'],
                'gif': [b'\x47\x49\x46\x38\x37\x61', b'\x47\x49\x46\x38\x39\x61'],
                'pdf': [b'\x25\x50\x44\x46'],
                'bmp': [b'\x42\x4D']
            }
            
            if expected_ext in file_signatures:
                signatures = file_signatures[expected_ext]
                for signature in signatures:
                    if header.startswith(signature):
                        return True
                
                logger.warning(f"文件内容与扩展名不匹配: {expected_ext}")
                return False
            
            # 对于其他类型，暂时允许通过
            return True
            
        except Exception as e:
            logger.error(f"文件内容验证失败: {e}")
            return False


# 全局安全文件处理器实例
secure_file_handler = SecureFileHandler()