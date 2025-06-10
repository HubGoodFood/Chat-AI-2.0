#!/usr/bin/env python3
"""
编码处理工具模块
解决中文字符、特殊字符、emoji等编码问题
"""
import re
import unicodedata
import hashlib


class EncodingUtils:
    """编码处理工具类"""
    
    @staticmethod
    def safe_filename(text: str, max_length: int = 100) -> str:
        """
        生成安全的文件名
        
        Args:
            text: 原始文本
            max_length: 最大长度
            
        Returns:
            str: 安全的文件名
        """
        if not text:
            return "unnamed"
        
        try:
            # 1. 移除或替换不安全的字符
            # 保留中文字符、英文字符、数字、基本标点
            safe_chars = []
            for char in text:
                if char.isalnum():  # 字母和数字
                    safe_chars.append(char)
                elif char in (' ', '-', '_', '.'):  # 安全的标点符号
                    safe_chars.append(char)
                elif '\u4e00' <= char <= '\u9fff':  # 中文字符范围
                    safe_chars.append(char)
                else:
                    # 其他字符用下划线替换
                    safe_chars.append('_')
            
            filename = ''.join(safe_chars)
            
            # 2. 清理连续的下划线和空格
            filename = re.sub(r'[_\s]+', '_', filename)
            
            # 3. 移除开头和结尾的特殊字符
            filename = filename.strip('_. ')
            
            # 4. 限制长度
            if len(filename) > max_length:
                # 如果太长，使用哈希值
                hash_suffix = hashlib.md5(text.encode('utf-8')).hexdigest()[:8]
                filename = filename[:max_length-9] + '_' + hash_suffix
            
            # 5. 确保不为空
            if not filename:
                filename = "unnamed"
            
            return filename
            
        except Exception as e:
            # 如果处理失败，使用哈希值作为文件名
            hash_value = hashlib.md5(text.encode('utf-8')).hexdigest()[:16]
            return f"file_{hash_value}"
    
    @staticmethod
    def safe_barcode_filename(product_name: str, barcode: str) -> str:
        """
        为条形码图片生成安全的文件名
        
        Args:
            product_name: 产品名称
            barcode: 条形码
            
        Returns:
            str: 安全的文件名（不包含扩展名）
        """
        try:
            # 生成安全的产品名称部分
            safe_name = EncodingUtils.safe_filename(product_name, max_length=50)
            
            # 组合文件名：安全名称_条形码
            filename = f"{safe_name}_{barcode}"
            
            # 再次确保文件名安全
            return EncodingUtils.safe_filename(filename, max_length=100)
            
        except Exception:
            # 如果失败，只使用条形码作为文件名
            return f"barcode_{barcode}"
    
    @staticmethod
    def validate_text_encoding(text: str) -> tuple[bool, str]:
        """
        验证文本编码是否安全
        
        Args:
            text: 要验证的文本
            
        Returns:
            tuple: (是否安全, 错误信息或清理后的文本)
        """
        if not text:
            return True, ""
        
        try:
            # 尝试编码为UTF-8
            text.encode('utf-8')
            
            # 检查是否包含控制字符
            if any(unicodedata.category(char).startswith('C') for char in text):
                # 移除控制字符
                cleaned_text = ''.join(char for char in text 
                                     if not unicodedata.category(char).startswith('C'))
                return True, cleaned_text
            
            return True, text
            
        except UnicodeEncodeError as e:
            return False, f"编码错误: {str(e)}"
        except Exception as e:
            return False, f"验证失败: {str(e)}"
    
    @staticmethod
    def clean_product_data(product_data: dict) -> dict:
        """
        清理产品数据中的编码问题
        
        Args:
            product_data: 产品数据字典
            
        Returns:
            dict: 清理后的产品数据
        """
        cleaned_data = {}
        
        for key, value in product_data.items():
            if isinstance(value, str):
                is_safe, cleaned_value = EncodingUtils.validate_text_encoding(value)
                cleaned_data[key] = cleaned_value if is_safe else value
            else:
                cleaned_data[key] = value
        
        return cleaned_data
    
    @staticmethod
    def safe_print(text: str, fallback_encoding: str = 'ascii') -> None:
        """
        安全的打印函数，避免编码错误
        
        Args:
            text: 要打印的文本
            fallback_encoding: 备用编码
        """
        try:
            print(text)
        except UnicodeEncodeError:
            try:
                # 尝试使用ASCII编码，忽略无法编码的字符
                safe_text = text.encode(fallback_encoding, errors='ignore').decode(fallback_encoding)
                print(safe_text)
            except Exception:
                # 最后的备用方案
                print(f"[编码错误] 无法显示文本，长度: {len(text)}")
    
    @staticmethod
    def normalize_chinese_text(text: str) -> str:
        """
        标准化中文文本
        
        Args:
            text: 原始文本
            
        Returns:
            str: 标准化后的文本
        """
        if not text:
            return ""
        
        try:
            # Unicode标准化
            normalized = unicodedata.normalize('NFKC', text)
            
            # 移除多余的空白字符
            normalized = re.sub(r'\s+', ' ', normalized).strip()
            
            return normalized
            
        except Exception:
            return text
    
    @staticmethod
    def is_safe_for_filesystem(filename: str) -> bool:
        """
        检查文件名是否对文件系统安全
        
        Args:
            filename: 文件名
            
        Returns:
            bool: 是否安全
        """
        if not filename:
            return False
        
        # Windows文件名限制
        forbidden_chars = '<>:"/\\|?*'
        forbidden_names = [
            'CON', 'PRN', 'AUX', 'NUL',
            'COM1', 'COM2', 'COM3', 'COM4', 'COM5', 'COM6', 'COM7', 'COM8', 'COM9',
            'LPT1', 'LPT2', 'LPT3', 'LPT4', 'LPT5', 'LPT6', 'LPT7', 'LPT8', 'LPT9'
        ]
        
        # 检查禁用字符
        if any(char in filename for char in forbidden_chars):
            return False
        
        # 检查禁用名称
        name_without_ext = filename.split('.')[0].upper()
        if name_without_ext in forbidden_names:
            return False
        
        # 检查长度（Windows路径限制）
        if len(filename) > 255:
            return False
        
        # 检查是否以点或空格结尾
        if filename.endswith('.') or filename.endswith(' '):
            return False
        
        return True


# 全局实例
encoding_utils = EncodingUtils()


def safe_filename(text: str, max_length: int = 100) -> str:
    """便捷函数：生成安全的文件名"""
    return EncodingUtils.safe_filename(text, max_length)


def safe_barcode_filename(product_name: str, barcode: str) -> str:
    """便捷函数：生成安全的条形码文件名"""
    return EncodingUtils.safe_barcode_filename(product_name, barcode)


def validate_text_encoding(text: str) -> tuple[bool, str]:
    """便捷函数：验证文本编码"""
    return EncodingUtils.validate_text_encoding(text)


def clean_product_data(product_data: dict) -> dict:
    """便捷函数：清理产品数据"""
    return EncodingUtils.clean_product_data(product_data)


def safe_print(text: str, fallback_encoding: str = 'ascii') -> None:
    """便捷函数：安全打印"""
    return EncodingUtils.safe_print(text, fallback_encoding)
