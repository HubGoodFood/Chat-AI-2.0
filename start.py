"""
果蔬客服AI系统启动脚本
"""
import os
import sys
import subprocess
import time


def check_dependencies():
    """检查依赖包"""
    print("[INFO] 检查依赖包...")

    required_packages = [
        'flask', 'pandas', 'requests', 'jieba', 'fuzzywuzzy'
    ]

    missing_packages = []

    for package in required_packages:
        try:
            __import__(package)
            print(f"[OK] {package}")
        except ImportError:
            print(f"[FAIL] {package} - 未安装")
            missing_packages.append(package)

    if missing_packages:
        print(f"\n[WARN] 缺少依赖包: {', '.join(missing_packages)}")
        print("[INFO] 正在安装依赖包...")

        try:
            subprocess.check_call([sys.executable, '-m', 'pip', 'install', '-r', 'requirements.txt'])
            print("[OK] 依赖包安装完成")
        except subprocess.CalledProcessError as e:
            print(f"[FAIL] 依赖包安装失败: {e}")
            return False

    return True


def check_data_files():
    """检查数据文件"""
    print("\n[INFO] 检查数据文件...")

    required_files = ['data/products.csv', 'data/policy.json']

    for file_path in required_files:
        if os.path.exists(file_path):
            print(f"[OK] {os.path.basename(file_path)}")
        else:
            print(f"[FAIL] {os.path.basename(file_path)} - 文件不存在")
            return False

    return True


def run_tests():
    """运行系统测试"""
    print("\n[INFO] 运行系统测试...")

    try:
        from tests.test_system import test_data_loading
        if test_data_loading():
            print("[OK] 系统测试通过")
            return True
        else:
            print("[FAIL] 系统测试失败")
            return False
    except Exception as e:
        print(f"[FAIL] 测试运行失败: {e}")
        print("[INFO] 跳过测试，继续启动...")
        return True  # 允许跳过测试继续启动


def start_server():
    """启动服务器"""
    print("\n[INFO] 启动果蔬客服AI系统...")

    try:
        from app import app, initialize_system

        # 初始化系统
        if not initialize_system():
            print("[FAIL] 系统初始化失败")
            return False

        print("[OK] 系统初始化成功")
        print("[INFO] 启动Web服务器...")
        print("[INFO] 访问地址: http://localhost:5000")
        print("[INFO] 按 Ctrl+C 停止服务器")

        # 启动Flask应用
        app.run(debug=False, host='0.0.0.0', port=5000)

    except KeyboardInterrupt:
        print("\n[INFO] 服务器已停止")
    except Exception as e:
        print(f"[FAIL] 服务器启动失败: {e}")
        return False

    return True


def main():
    """主函数"""
    print("果蔬客服AI系统启动器")
    print("=" * 40)
    
    # 检查依赖
    if not check_dependencies():
        print("[FAIL] 依赖检查失败，无法启动系统")
        return

    # 检查数据文件
    if not check_data_files():
        print("[FAIL] 数据文件检查失败，无法启动系统")
        print("[INFO] 请确保 products.csv 和 policy.json 文件存在")
        return

    # 运行测试
    if not run_tests():
        print("[FAIL] 系统测试失败")
        response = input("是否继续启动？(y/N): ")
        if response.lower() != 'y':
            return
    
    # 启动服务器
    start_server()


if __name__ == "__main__":
    main()
