#!/usr/bin/env python3
"""
Synology NAS配置验证工具
用于验证NAS配置是否正确，适用于AI客服系统数据存储
"""
import os
import sys
import json
import time
import platform
from datetime import datetime
from pathlib import Path


class NASConfigValidator:
    """NAS配置验证器"""
    
    def __init__(self):
        self.system = platform.system()
        self.test_results = []
        self.nas_path = None
        
    def log_test(self, test_name: str, success: bool, message: str = ""):
        """记录测试结果"""
        status = "✅ 通过" if success else "❌ 失败"
        result = {
            "test": test_name,
            "status": status,
            "success": success,
            "message": message,
            "timestamp": datetime.now().isoformat()
        }
        self.test_results.append(result)
        print(f"{status} {test_name}: {message}")
        
    def get_nas_path(self):
        """获取NAS路径"""
        print("=" * 60)
        print("Synology NAS配置验证工具")
        print("=" * 60)
        
        print(f"\n当前操作系统: {self.system}")
        
        if self.system == "Windows":
            default_path = "Z:\\ChatAI_System\\data"
            print("Windows系统检测到，推荐使用映射驱动器")
            print("示例路径: Z:\\ChatAI_System\\data")
        elif self.system == "Darwin":  # macOS
            default_path = "/Volumes/ChatAI_Data/ChatAI_System/data"
            print("macOS系统检测到")
            print("示例路径: /Volumes/ChatAI_Data/ChatAI_System/data")
        else:  # Linux
            default_path = "/mnt/nas/ChatAI_Data/ChatAI_System/data"
            print("Linux系统检测到")
            print("示例路径: /mnt/nas/ChatAI_Data/ChatAI_System/data")
        
        nas_path = input(f"\n请输入NAS数据路径 (默认: {default_path}): ").strip()
        
        if not nas_path:
            nas_path = default_path
            
        self.nas_path = nas_path
        print(f"使用NAS路径: {nas_path}")
        
    def test_path_exists(self):
        """测试路径是否存在"""
        try:
            exists = os.path.exists(self.nas_path)
            if exists:
                self.log_test("路径存在性检查", True, f"路径 {self.nas_path} 存在")
            else:
                self.log_test("路径存在性检查", False, f"路径 {self.nas_path} 不存在")
            return exists
        except Exception as e:
            self.log_test("路径存在性检查", False, f"检查路径时出错: {e}")
            return False
    
    def test_read_permission(self):
        """测试读取权限"""
        try:
            readable = os.access(self.nas_path, os.R_OK)
            if readable:
                self.log_test("读取权限检查", True, "具有读取权限")
            else:
                self.log_test("读取权限检查", False, "缺少读取权限")
            return readable
        except Exception as e:
            self.log_test("读取权限检查", False, f"检查读取权限时出错: {e}")
            return False
    
    def test_write_permission(self):
        """测试写入权限"""
        try:
            writable = os.access(self.nas_path, os.W_OK)
            if writable:
                self.log_test("写入权限检查", True, "具有写入权限")
            else:
                self.log_test("写入权限检查", False, "缺少写入权限")
            return writable
        except Exception as e:
            self.log_test("写入权限检查", False, f"检查写入权限时出错: {e}")
            return False
    
    def test_create_file(self):
        """测试创建文件"""
        try:
            test_file = os.path.join(self.nas_path, "config_test.txt")
            test_content = f"NAS配置测试 - {datetime.now().isoformat()}"
            
            with open(test_file, 'w', encoding='utf-8') as f:
                f.write(test_content)
            
            self.log_test("文件创建测试", True, "成功创建测试文件")
            
            # 清理测试文件
            os.remove(test_file)
            return True
            
        except Exception as e:
            self.log_test("文件创建测试", False, f"创建文件失败: {e}")
            return False
    
    def test_json_operations(self):
        """测试JSON文件操作"""
        try:
            test_file = os.path.join(self.nas_path, "json_test.json")
            test_data = {
                "test": True,
                "timestamp": datetime.now().isoformat(),
                "system": self.system,
                "nas_path": self.nas_path,
                "message": "NAS JSON操作测试成功"
            }
            
            # 写入JSON
            with open(test_file, 'w', encoding='utf-8') as f:
                json.dump(test_data, f, ensure_ascii=False, indent=2)
            
            # 读取JSON
            with open(test_file, 'r', encoding='utf-8') as f:
                loaded_data = json.load(f)
            
            # 验证数据
            if loaded_data["test"] == True and loaded_data["message"] == test_data["message"]:
                self.log_test("JSON操作测试", True, "JSON读写操作正常")
                success = True
            else:
                self.log_test("JSON操作测试", False, "JSON数据验证失败")
                success = False
            
            # 清理测试文件
            os.remove(test_file)
            return success
            
        except Exception as e:
            self.log_test("JSON操作测试", False, f"JSON操作失败: {e}")
            return False
    
    def test_directory_operations(self):
        """测试目录操作"""
        try:
            test_dir = os.path.join(self.nas_path, "test_directory")
            
            # 创建目录
            os.makedirs(test_dir, exist_ok=True)
            
            # 检查目录是否存在
            if os.path.isdir(test_dir):
                self.log_test("目录操作测试", True, "目录创建和检查正常")
                success = True
            else:
                self.log_test("目录操作测试", False, "目录创建失败")
                success = False
            
            # 清理测试目录
            if os.path.exists(test_dir):
                os.rmdir(test_dir)
            
            return success
            
        except Exception as e:
            self.log_test("目录操作测试", False, f"目录操作失败: {e}")
            return False
    
    def test_performance(self):
        """测试基本性能"""
        try:
            test_file = os.path.join(self.nas_path, "performance_test.txt")
            test_data = "性能测试数据 " * 1000  # 约13KB数据
            
            # 测试写入性能
            start_time = time.time()
            with open(test_file, 'w', encoding='utf-8') as f:
                f.write(test_data)
            write_time = time.time() - start_time
            
            # 测试读取性能
            start_time = time.time()
            with open(test_file, 'r', encoding='utf-8') as f:
                read_data = f.read()
            read_time = time.time() - start_time
            
            # 清理测试文件
            os.remove(test_file)
            
            if write_time < 5.0 and read_time < 5.0:  # 5秒内完成
                self.log_test("性能测试", True, 
                            f"写入: {write_time:.2f}s, 读取: {read_time:.2f}s")
                return True
            else:
                self.log_test("性能测试", False, 
                            f"性能较慢 - 写入: {write_time:.2f}s, 读取: {read_time:.2f}s")
                return False
                
        except Exception as e:
            self.log_test("性能测试", False, f"性能测试失败: {e}")
            return False
    
    def test_ai_system_compatibility(self):
        """测试AI客服系统兼容性"""
        try:
            # 模拟AI客服系统的数据结构
            inventory_data = {
                "last_updated": datetime.now().isoformat(),
                "products": {
                    "test_1": {
                        "product_name": "测试产品",
                        "barcode": "1234567890123",
                        "storage_area": "A",
                        "current_stock": 100
                    }
                }
            }
            
            test_file = os.path.join(self.nas_path, "inventory_test.json")
            
            # 写入测试数据
            with open(test_file, 'w', encoding='utf-8') as f:
                json.dump(inventory_data, f, ensure_ascii=False, indent=2)
            
            # 读取并验证
            with open(test_file, 'r', encoding='utf-8') as f:
                loaded_data = json.load(f)
            
            # 验证数据结构
            if ("products" in loaded_data and 
                "test_1" in loaded_data["products"] and
                loaded_data["products"]["test_1"]["barcode"] == "1234567890123"):
                
                self.log_test("AI系统兼容性测试", True, "数据结构兼容性正常")
                success = True
            else:
                self.log_test("AI系统兼容性测试", False, "数据结构验证失败")
                success = False
            
            # 清理测试文件
            os.remove(test_file)
            return success
            
        except Exception as e:
            self.log_test("AI系统兼容性测试", False, f"兼容性测试失败: {e}")
            return False
    
    def generate_report(self):
        """生成测试报告"""
        print("\n" + "=" * 60)
        print("测试报告")
        print("=" * 60)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result["success"])
        failed_tests = total_tests - passed_tests
        
        print(f"总测试数: {total_tests}")
        print(f"通过: {passed_tests}")
        print(f"失败: {failed_tests}")
        print(f"成功率: {(passed_tests/total_tests)*100:.1f}%")
        
        if failed_tests > 0:
            print("\n失败的测试:")
            for result in self.test_results:
                if not result["success"]:
                    print(f"  - {result['test']}: {result['message']}")
        
        # 生成建议
        print("\n配置建议:")
        if passed_tests == total_tests:
            print("🎉 所有测试通过！NAS配置正确，可以进行数据迁移。")
        elif passed_tests >= total_tests * 0.8:
            print("⚠️ 大部分测试通过，但有一些问题需要解决。")
            print("   建议检查失败的测试项目并修复后重新测试。")
        else:
            print("❌ 多个测试失败，NAS配置存在问题。")
            print("   建议参考故障排查指南解决问题后重新测试。")
        
        # 保存报告到文件
        try:
            report_file = "nas_config_report.json"
            report_data = {
                "test_time": datetime.now().isoformat(),
                "system": self.system,
                "nas_path": self.nas_path,
                "summary": {
                    "total_tests": total_tests,
                    "passed_tests": passed_tests,
                    "failed_tests": failed_tests,
                    "success_rate": (passed_tests/total_tests)*100
                },
                "test_results": self.test_results
            }
            
            with open(report_file, 'w', encoding='utf-8') as f:
                json.dump(report_data, f, ensure_ascii=False, indent=2)
            
            print(f"\n详细报告已保存到: {report_file}")
            
        except Exception as e:
            print(f"保存报告失败: {e}")
    
    def run_all_tests(self):
        """运行所有测试"""
        self.get_nas_path()
        
        print(f"\n开始NAS配置验证...")
        print(f"测试路径: {self.nas_path}")
        print("-" * 60)
        
        # 基础测试
        if not self.test_path_exists():
            print("\n❌ 路径不存在，无法继续测试")
            self.generate_report()
            return False
        
        # 权限测试
        self.test_read_permission()
        self.test_write_permission()
        
        # 功能测试
        self.test_create_file()
        self.test_json_operations()
        self.test_directory_operations()
        
        # 性能测试
        self.test_performance()
        
        # 兼容性测试
        self.test_ai_system_compatibility()
        
        # 生成报告
        self.generate_report()
        
        # 返回总体结果
        return all(result["success"] for result in self.test_results)


def main():
    """主函数"""
    validator = NASConfigValidator()
    
    try:
        success = validator.run_all_tests()
        
        if success:
            print("\n🎉 NAS配置验证成功！")
            print("您可以继续进行数据迁移操作。")
            sys.exit(0)
        else:
            print("\n⚠️ NAS配置验证失败！")
            print("请参考故障排查指南解决问题。")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n\n用户取消操作")
        sys.exit(1)
    except Exception as e:
        print(f"\n验证过程中出现错误: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
