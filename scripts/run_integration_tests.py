#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
集成测试运行脚本

这个脚本用于运行AI客服系统的集成测试，
提供不同的测试运行选项和结果报告。

功能特点：
1. 支持不同测试类别的运行
2. 生成详细的测试报告
3. 提供测试结果统计
4. 支持并行测试执行
5. 集成测试环境检查

使用方法：
python scripts/run_integration_tests.py [选项]

选项：
--all: 运行所有集成测试
--chat: 只运行AI客服集成测试
--inventory: 只运行库存管理集成测试
--api: 只运行API集成测试
--admin: 只运行管理员集成测试
--parallel: 并行运行测试
--verbose: 详细输出
--report: 生成HTML报告
"""
import os
import sys
import argparse
import subprocess
import time
from datetime import datetime

# 添加项目根目录到Python路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from src.utils.logger_config import get_logger

logger = get_logger('integration_test_runner')


def check_test_environment():
    """
    检查集成测试环境

    验证：
    1. 必要的依赖包
    2. 测试数据目录
    3. 配置文件
    4. 权限设置
    """
    print("检查集成测试环境...")
    
    # 检查必要的包
    required_packages = ['pytest', 'flask', 'requests']
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package)
            print(f"[OK] {package} 已安装")
        except ImportError:
            missing_packages.append(package)
            print(f"[FAIL] {package} 未安装")
    
    if missing_packages:
        print(f"\n[WARNING] 缺少必要的包: {', '.join(missing_packages)}")
        print("请运行: pip install -r requirements.txt")
        return False
    
    # 检查测试目录
    test_dirs = [
        'tests',
        'tests/integration',
        'data',
        'static',
        'templates'
    ]
    
    for test_dir in test_dirs:
        dir_path = os.path.join(project_root, test_dir)
        if os.path.exists(dir_path):
            print(f"[OK] {test_dir}/ 目录存在")
        else:
            print(f"[FAIL] {test_dir}/ 目录不存在")
            return False
    
    # 检查配置文件
    config_files = [
        'pytest.ini',
        'tests/conftest.py',
        'tests/integration/conftest.py'
    ]
    
    for config_file in config_files:
        file_path = os.path.join(project_root, config_file)
        if os.path.exists(file_path):
            print(f"[OK] {config_file} 配置文件存在")
        else:
            print(f"[FAIL] {config_file} 配置文件不存在")
            return False

    print("[OK] 集成测试环境检查通过")
    return True


def run_tests(test_category=None, parallel=False, verbose=False, generate_report=False):
    """
    运行集成测试
    
    Args:
        test_category: 测试类别 ('all', 'chat', 'inventory', 'api', 'admin')
        parallel: 是否并行运行
        verbose: 是否详细输出
        generate_report: 是否生成HTML报告
    """
    print(f"\n开始运行集成测试 - {test_category or 'all'}")
    
    # 构建pytest命令
    cmd = ['python', '-m', 'pytest']
    
    # 添加测试路径和标记
    if test_category == 'all' or test_category is None:
        cmd.extend(['tests/integration/', '-m', 'integration'])
    elif test_category == 'chat':
        cmd.extend(['tests/integration/test_chat_workflows.py', '-m', 'chat'])
    elif test_category == 'inventory':
        cmd.extend(['tests/integration/test_inventory_workflows.py', '-m', 'inventory'])
    elif test_category == 'api':
        cmd.extend(['tests/integration/test_api_integration.py', '-m', 'api'])
    elif test_category == 'admin':
        cmd.extend(['tests/integration/test_admin_integration.py', '-m', 'auth'])
    else:
        print(f"[FAIL] 未知的测试类别: {test_category}")
        return False
    
    # 添加选项
    if verbose:
        cmd.append('-v')
    else:
        cmd.append('-q')
    
    if parallel:
        cmd.extend(['-n', 'auto'])  # 需要pytest-xdist
    
    if generate_report:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        report_file = f'integration_test_report_{timestamp}.html'
        cmd.extend(['--html', report_file, '--self-contained-html'])
    
    # 添加覆盖率报告
    cmd.extend(['--cov=src', '--cov-report=term-missing'])
    
    # 设置环境变量
    env = os.environ.copy()
    env['PYTHONPATH'] = project_root
    env['FLASK_ENV'] = 'testing'
    env['TESTING'] = 'true'
    
    print(f"执行命令: {' '.join(cmd)}")
    
    # 运行测试
    start_time = time.time()
    
    try:
        result = subprocess.run(cmd, 
                              cwd=project_root,
                              env=env,
                              capture_output=False,
                              text=True)
        
        end_time = time.time()
        duration = end_time - start_time
        
        print(f"\n测试运行时间: {duration:.2f} 秒")

        if result.returncode == 0:
            print("[OK] 所有集成测试通过！")
            return True
        else:
            print("[FAIL] 部分集成测试失败")
            return False
            
    except KeyboardInterrupt:
        print("\n[WARNING] 测试被用户中断")
        return False
    except Exception as e:
        print(f"[FAIL] 运行测试时出错: {e}")
        return False


def generate_test_summary():
    """生成测试摘要报告"""
    print("\n生成测试摘要...")
    
    # 运行测试并收集结果
    cmd = ['python', '-m', 'pytest', 
           'tests/integration/', 
           '-m', 'integration',
           '--collect-only', 
           '-q']
    
    try:
        result = subprocess.run(cmd, 
                              cwd=project_root,
                              capture_output=True,
                              text=True)
        
        if result.returncode == 0:
            lines = result.stdout.split('\n')
            test_count = len([line for line in lines if '::test_' in line])
            
            print(f"集成测试统计:")
            print(f"   总测试数量: {test_count}")
            print(f"   测试文件: 4个")
            print(f"   测试类别: chat, inventory, api, admin")

        else:
            print("[WARNING] 无法收集测试信息")

    except Exception as e:
        print(f"[FAIL] 生成摘要时出错: {e}")


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='AI客服系统集成测试运行器')
    
    parser.add_argument('--all', action='store_true', 
                       help='运行所有集成测试')
    parser.add_argument('--chat', action='store_true', 
                       help='只运行AI客服集成测试')
    parser.add_argument('--inventory', action='store_true', 
                       help='只运行库存管理集成测试')
    parser.add_argument('--api', action='store_true', 
                       help='只运行API集成测试')
    parser.add_argument('--admin', action='store_true', 
                       help='只运行管理员集成测试')
    parser.add_argument('--parallel', action='store_true', 
                       help='并行运行测试')
    parser.add_argument('--verbose', action='store_true', 
                       help='详细输出')
    parser.add_argument('--report', action='store_true', 
                       help='生成HTML报告')
    parser.add_argument('--summary', action='store_true', 
                       help='只显示测试摘要')
    
    args = parser.parse_args()
    
    print("AI客服系统集成测试运行器")
    print("=" * 50)
    
    # 检查测试环境
    if not check_test_environment():
        sys.exit(1)
    
    # 如果只要摘要，生成摘要后退出
    if args.summary:
        generate_test_summary()
        return
    
    # 确定测试类别
    test_category = None
    if args.all:
        test_category = 'all'
    elif args.chat:
        test_category = 'chat'
    elif args.inventory:
        test_category = 'inventory'
    elif args.api:
        test_category = 'api'
    elif args.admin:
        test_category = 'admin'
    else:
        # 默认运行所有测试
        test_category = 'all'
    
    # 运行测试
    success = run_tests(
        test_category=test_category,
        parallel=args.parallel,
        verbose=args.verbose,
        generate_report=args.report
    )
    
    # 生成摘要
    generate_test_summary()
    
    if success:
        print("\n[OK] 集成测试完成！")
        sys.exit(0)
    else:
        print("\n[FAIL] 集成测试失败！")
        sys.exit(1)


if __name__ == '__main__':
    main()
