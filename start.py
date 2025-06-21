# -*- coding: utf-8 -*-
"""
果蔬客服AI系统启动脚本
"""
import os
import sys
import subprocess
import time
from src.utils.logger_config import get_logger

# 初始化日志记录器
logger = get_logger('start')


def check_dependencies():
    """检查依赖包"""
    logger.info("检查依赖包...")

    required_packages = [
        'flask', 'pandas', 'requests', 'jieba', 'fuzzywuzzy'
    ]

    missing_packages = []

    for package in required_packages:
        try:
            __import__(package)
            logger.info(f"依赖包检查通过: {package}")
        except ImportError:
            logger.warning(f"依赖包缺失: {package}")
            missing_packages.append(package)

    if missing_packages:
        logger.warning(f"缺少依赖包: {', '.join(missing_packages)}")
        logger.info("正在安装依赖包...")

        try:
            subprocess.check_call([sys.executable, '-m', 'pip', 'install', '-r', 'requirements.txt'])
            logger.info("依赖包安装完成")
        except subprocess.CalledProcessError as e:
            logger.error(f"依赖包安装失败: {e}")
            return False

    return True


def check_data_files():
    """检查数据文件"""
    logger.info("检查数据文件...")

    required_files = ['data/products.csv', 'data/policy.json']

    for file_path in required_files:
        if os.path.exists(file_path):
            logger.info(f"数据文件检查通过: {os.path.basename(file_path)}")
        else:
            logger.error(f"数据文件缺失: {os.path.basename(file_path)}")
            return False

    return True


def run_tests():
    """运行系统测试"""
    logger.info("运行系统测试...")

    try:
        from tests.test_system import test_data_loading
        if test_data_loading():
            logger.info("系统测试通过")
            return True
        else:
            logger.error("系统测试失败")
            return False
    except Exception as e:
        logger.error(f"测试运行失败: {e}")
        logger.info("跳过测试，继续启动...")
        return True  # 允许跳过测试继续启动


def start_server():
    """启动服务器"""
    logger.info("启动果蔬客服AI系统...")

    try:
        from app import app, initialize_system

        # 初始化系统
        if not initialize_system():
            logger.error("系统初始化失败")
            return False

        logger.info("系统初始化成功")
        logger.info("启动Web服务器...")
        logger.info("访问地址: http://localhost:5000")
        logger.info("按 Ctrl+C 停止服务器")

        # 启动Flask应用
        app.run(debug=False, host='0.0.0.0', port=5000)

    except KeyboardInterrupt:
        logger.info("服务器已停止")
    except Exception as e:
        logger.error(f"服务器启动失败: {e}")
        return False

    return True


def main():
    """主函数"""
    logger.info("果蔬客服AI系统启动器")
    logger.info("=" * 40)

    # 检查依赖
    if not check_dependencies():
        logger.error("依赖检查失败，无法启动系统")
        return

    # 检查数据文件
    if not check_data_files():
        logger.error("数据文件检查失败，无法启动系统")
        logger.info("请确保 products.csv 和 policy.json 文件存在")
        return

    # 运行测试
    if not run_tests():
        logger.error("系统测试失败")
        response = input("是否继续启动？(y/N): ")
        if response.lower() != 'y':
            return

    # 启动服务器
    start_server()


if __name__ == "__main__":
    main()
