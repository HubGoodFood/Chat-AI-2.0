"""
简洁的国际化配置模块 - 自定义多语言支持
"""
import os
import json
from flask import request, session
from typing import Dict, List


class SimpleI18n:
    """简洁的国际化配置类"""
    
    def __init__(self):
        """初始化国际化配置"""
        self.default_language = 'zh'
        self.languages = {
            'zh': {
                'name': '简体中文',
                'native_name': '简体中文',
                'flag': '🇨🇳',
                'code': 'zh'
            },
            'en': {
                'name': 'English',
                'native_name': 'English',
                'flag': '🇺🇸',
                'code': 'en'
            }
        }
        self.translations = {}
        self._load_translations()
    
    def _load_translations(self):
        """加载翻译文件"""
        try:
            # 创建简化的翻译字典
            # 英文翻译字典（en和en_US共享）
            english_translations = {
                    # 登录页面
                    '管理员登录': 'Admin Login',
                    '管理员登录 - 果蔬客服AI系统': 'Admin Login - Fruit & Vegetable AI System',
                    '果蔬客服AI系统后台管理': 'Fruit & Vegetable AI System Admin Panel',
                    '用户名': 'Username',
                    '密码': 'Password',
                    '登录': 'Login',
                    '默认账户：admin / admin123': 'Default account: admin / admin123',
                    '返回客服系统': 'Return to Chat System',
                    
                    # 管理后台
                    '管理后台': 'Admin Panel',
                    '控制台': 'Dashboard',
                    '欢迎，管理员': 'Welcome, Admin',
                    '退出登录': 'Logout',
                    '库存管理': 'Inventory Management',
                    '产品入库': 'Product Entry',
                    '库存盘点': 'Inventory Count',
                    '数据对比分析': 'Data Analysis',
                    '反馈管理': 'Feedback Management',
                    '操作日志': 'Operation Logs',
                    '数据导出': 'Data Export',
                    '系统设置': 'System Settings',
                    
                    # 系统概览
                    '系统概览': 'System Overview',
                    '果蔬客服AI系统管理控制台': 'Fruit & Vegetable AI System Admin Console',
                    '总产品数': 'Total Products',
                    '低库存产品': 'Low Stock Products',
                    '总反馈数': 'Total Feedback',
                    '待处理反馈': 'Pending Feedback',
                    '库存状态': 'Inventory Status',
                    '最新反馈': 'Recent Feedback',
                    '正在加载...': 'Loading...',
                    
                    # 表格和表单
                    '产品名称': 'Product Name',
                    '分类': 'Category',
                    '价格': 'Price',
                    '当前库存': 'Current Stock',
                    '状态': 'Status',
                    '操作': 'Actions',
                    '添加产品': 'Add Product',
                    '搜索产品...': 'Search products...',
                    '所有分类': 'All Categories',
                    '所有状态': 'All Status',
                    '正常': 'Normal',
                    '停用': 'Disabled',
                    
                    # 按钮和操作
                    '保存': 'Save',
                    '取消': 'Cancel',
                    '删除': 'Delete',
                    '编辑': 'Edit',
                    '添加': 'Add',
                    '搜索': 'Search',
                    '导出': 'Export',
                    '刷新': 'Refresh',
                    '提交': 'Submit',
                    '重置': 'Reset',
                    '确认': 'Confirm',
                    '完成': 'Complete',
                    '开始': 'Start',
                    '继续': 'Continue',
                    '暂停': 'Pause',
                    '停止': 'Stop',

                    # 库存盘点页面
                    '库存盘点': 'Inventory Count',
                    '创建和管理库存盘点任务，支持条形码扫描和手动录入': 'Create and manage inventory count tasks with barcode scanning and manual entry',
                    '+ 创建新盘点': '+ Create New Count',
                    '盘点任务列表': 'Count Task List',
                    '所有状态': 'All Status',
                    '进行中': 'In Progress',
                    '已完成': 'Completed',
                    '已取消': 'Cancelled',
                    '任务ID': 'Task ID',
                    '创建时间': 'Created Time',
                    '操作员': 'Operator',
                    '产品数量': 'Product Count',
                    '加载中...': 'Loading...',
                    '暂无盘点任务': 'No count tasks',
                    '暂无库存数据': 'No inventory data',
                    '暂无反馈数据': 'No feedback data',
                    '暂无日志数据': 'No log data',

                    # 盘点操作区域
                    '添加盘点产品': 'Add Count Products',
                    '条形码扫描/输入': 'Barcode Scan/Input',
                    '扫描或输入条形码': 'Scan or enter barcode',
                    '或': 'or',
                    '产品搜索': 'Product Search',
                    '搜索产品名称': 'Search product name',
                    '当前盘点项目': 'Current Count Items',
                    '任务ID: ': 'Task ID: ',
                    '创建时间: ': 'Created Time: ',
                    '项目数量: ': 'Item Count: ',
                    '条形码': 'Barcode',
                    '存储区域': 'Storage Area',
                    '账面数量': 'Book Quantity',
                    '实际数量': 'Actual Quantity',
                    '差异': 'Difference',
                    '暂无盘点项目': 'No count items',
                    '总项目: ': 'Total Items: ',
                    '已录入: ': 'Recorded: ',
                    '有差异: ': 'With Difference: ',
                    '完成盘点': 'Complete Count',
                    '取消盘点': 'Cancel Count',

                    # 数据对比分析页面
                    '数据对比分析': 'Data Analysis',
                    '对比不同时期的库存数据，分析变化趋势和异常情况': 'Compare inventory data from different periods, analyze trends and anomalies',
                    '创建对比分析': 'Create Comparison Analysis',
                    '周对比分析': 'Weekly Comparison',
                    '自动对比最近一周的盘点数据': 'Automatically compare inventory data from the past week',
                    '生成周对比': 'Generate Weekly Comparison',
                    '手动对比选择': 'Manual Comparison Selection',
                    '选择两个盘点任务进行对比': 'Select two count tasks for comparison',
                    '当前盘点:': 'Current Count:',
                    '对比盘点:': 'Comparison Count:',
                    '请选择盘点任务': 'Please select count task',
                    '开始对比': 'Start Comparison',

                    # 分析结果
                    '总产品数': 'Total Products',
                    '变化产品数': 'Changed Products',
                    '异常项目数': 'Anomaly Items',
                    '总价值变化': 'Total Value Change',
                    '变化明细': 'Change Details',
                    '所有变化': 'All Changes',
                    '库存增加': 'Stock Increased',
                    '库存减少': 'Stock Decreased',
                    '新增产品': 'New Products',
                    '移除产品': 'Removed Products',
                    '之前数量': 'Previous Quantity',
                    '当前数量': 'Current Quantity',
                    '变化量': 'Change Amount',
                    '变化百分比': 'Change Percentage',
                    '暂无变化数据': 'No change data',
                    '异常检测结果': 'Anomaly Detection Results',
                    '暂无异常检测结果': 'No anomaly detection results',
                    '报表生成': 'Report Generation',
                    '📄 下载分析报告': '📄 Download Analysis Report',
                    '📊 导出Excel': '📊 Export Excel',
                    '📈 生成趋势图': '📈 Generate Trend Chart',
                    '分析时间：': 'Analysis Time: ',
                    '对比范围：': 'Comparison Range: ',
                    '分析类型：': 'Analysis Type: ',

                    # 状态和消息
                    '正在加载库存数据...': 'Loading inventory data...',
                    '正在加载反馈数据...': 'Loading feedback data...',
                    '正在加载日志数据...': 'Loading log data...',
                    '操作成功': 'Operation successful',
                    '操作失败': 'Operation failed',
                    '登录成功': 'Login successful',
                    '登录失败': 'Login failed',
                    '用户名或密码错误': 'Invalid username or password',
                    '网络错误，请稍后再试': 'Network error, please try again later',
                    '网络错误': 'Network error',
                    '产品删除成功': 'Product deleted successfully',
                    '反馈删除成功': 'Feedback deleted successfully',
                    '盘点任务创建成功！': 'Count task created successfully!',
                    '周对比分析创建成功！': 'Weekly comparison analysis created successfully!',
                    '手动对比分析创建成功！': 'Manual comparison analysis created successfully!',
                    
                    # 表单相关
                    '产品分类': 'Product Category',
                    '请选择分类': 'Please select category',
                    '禽类产品': 'Poultry Products',
                    '蛋类': 'Eggs',
                    '美味熟食/面点': 'Delicious Cooked Food/Pastries',
                    '新鲜蔬菜': 'Fresh Vegetables',
                    '海鲜河鲜': 'Seafood',
                    '时令水果': 'Seasonal Fruits',
                    '优选干货': 'Premium Dried Goods',
                    '单位': 'Unit',
                    '如：个、斤、包': 'e.g.: piece, kg, pack',
                    '规格': 'Specification',
                    '如：500g、2个装': 'e.g.: 500g, 2-pack',
                    '初始库存': 'Initial Stock',
                    '最小库存警告': 'Low Stock Warning',
                    '产品描述': 'Product Description',
                    '产品关键词、特点等': 'Product keywords, features, etc.',
                    '产品图片URL': 'Product Image URL',
                    '调整库存': 'Adjust Stock',
                    '库存变动': 'Stock Change',
                    '正数为增加库存，负数为减少库存': 'Positive for increase, negative for decrease',
                    '备注': 'Notes',
                    '库存变动原因...': 'Reason for stock change...',
                    '确认调整': 'Confirm Adjustment',

                    # 反馈管理
                    '反馈详情': 'Feedback Details',
                    '添加客户反馈': 'Add Customer Feedback',
                    '反馈类型': 'Feedback Type',
                    '请选择类型': 'Please select type',
                    '正面反馈': 'Positive Feedback',
                    '负面反馈': 'Negative Feedback',
                    '客户微信昵称': 'Customer WeChat Name',
                    '客户所在群号': 'Customer Group Number',
                    '付款状态': 'Payment Status',
                    '请选择状态': 'Please select status',
                    '已付款': 'Paid',
                    '未付款': 'Unpaid',
                    '反馈内容': 'Feedback Content',
                    '客户反馈的具体内容...': 'Specific customer feedback content...',
                    '客户上传图片URL': 'Customer Uploaded Image URLs',
                    '多个图片URL请用换行分隔': 'Separate multiple image URLs with line breaks',
                    '每行一个图片URL': 'One image URL per line',
                    '添加反馈': 'Add Feedback',
                    '处理反馈': 'Process Feedback',
                    '处理状态': 'Processing Status',
                    '待处理': 'Pending',
                    '处理中': 'Processing',
                    '已解决': 'Resolved',
                    '处理备注': 'Processing Notes',
                    '处理过程、解决方案等...': 'Processing steps, solutions, etc...',
                    '更新状态': 'Update Status',

                    # 通用提示
                    '错误': 'Error',
                    '成功': 'Success',
                    '确认删除吗？': 'Are you sure you want to delete?',
                    '确定要删除这个产品吗？此操作将设置产品状态为停用。': 'Are you sure you want to delete this product? This will set the product status to inactive.',
                    '请输入盘点备注（可选）:': 'Please enter count notes (optional):',
                    '请选择要对比的盘点任务': 'Please select count tasks to compare',
                    '请先选择两个不同的盘点任务': 'Please select two different count tasks first',
                    '请输入条形码': 'Please enter barcode',
                    '请输入搜索关键词': 'Please enter search keyword',
                    '确认完成盘点吗？': 'Are you sure you want to complete the count?',
                    '确认取消盘点吗？': 'Are you sure you want to cancel the count?',
                    '所有项目都已录入实际数量': 'All items have actual quantities recorded',
                    '还有项目未录入实际数量': 'Some items still need actual quantities',

                    # 按钮文本
                    '查看': 'View',
                    '编辑': 'Edit',
                    '删除': 'Delete',
                    '继续': 'Continue',
                    '添加': 'Add',
                    '移除': 'Remove',
                    '调库存': 'Adjust Stock',
                    '处理': 'Process',

                    # 语言切换
                    '语言': 'Language',
                    '简体中文': '简体中文',
                    'English': 'English',

                    # 新增的遗漏翻译 - 页面标题
                    '管理员控制台 - 果蔬客服AI系统': 'Admin Console - Fruit & Vegetable AI System',

                    # 新增的遗漏翻译 - 反馈管理
                    '客户反馈管理': 'Customer Feedback Management',
                    '客户昵称': 'Customer Nickname',
                    '反馈时间': 'Feedback Time',

                    # 新增的遗漏翻译 - 操作日志
                    '时间': 'Time',
                    '目标ID': 'Target ID',
                    '结果': 'Result',
                    '详情': 'Details',
                    '所有操作员': 'All Operators',
                    '所有操作': 'All Operations',
                    '所有目标': 'All Targets',
                    '显示条数': 'Display Count',
                    '创建': 'Create',
                    '更新': 'Update',
                    '库存调整': 'Stock Adjustment',
                    '库存': 'Inventory',
                    '反馈': 'Feedback',
                    '管理员': 'Admin',

                    # 新增的遗漏翻译 - 数据导出
                    '库存数据导出': 'Inventory Data Export',
                    '反馈数据导出': 'Feedback Data Export',
                    '操作日志导出': 'Operation Logs Export',
                    '完整数据备份': 'Complete Data Backup',
                    '导出所有产品和库存信息': 'Export all products and inventory information',
                    '导出所有客户反馈信息': 'Export all customer feedback information',
                    '导出系统操作日志': 'Export system operation logs',
                    '导出所有系统数据的完整备份': 'Export complete backup of all system data',
                    '开始日期': 'Start Date',
                    '结束日期': 'End Date',
                    '创建备份': 'Create Backup',
                    '导出CSV': 'Export CSV',
                    '导出JSON': 'Export JSON',
                    '生成报告': 'Generate Report',

                    # 新增的遗漏翻译 - 系统设置
                    '修改密码': 'Change Password',
                    '当前密码': 'Current Password',
                    '新密码': 'New Password',
                    '确认新密码': 'Confirm New Password',
                    '系统信息': 'System Information',
                    '系统版本': 'System Version',
                    '最后更新': 'Last Updated',
                    '运行状态': 'Running Status',
                    '正常运行': 'Running Normally',
                    '系统维护': 'System Maintenance',
                    '清理旧日志': 'Clear Old Logs',
                    '优化数据': 'Optimize Data',
                    '重置系统': 'Reset System',
                    '注意：系统维护操作可能影响系统性能，请在低峰期执行。': 'Note: System maintenance operations may affect system performance. Please execute during off-peak hours.',

                    # 新增的遗漏翻译 - 产品入库
                    '产品信息': 'Product Information',
                    '请选择单位': 'Please select unit',
                    '斤': 'Jin (Chinese pound)',
                    '个': 'Piece',
                    '包': 'Pack',
                    '盒': 'Box',
                    '袋': 'Bag',
                    '例：15元/斤': 'e.g.: 15 yuan/jin',
                    '如：500g、2个装': 'e.g.: 500g, 2-pack',
                    '请选择存储区域': 'Please select storage area',
                    'A区 - 水果区': 'Area A - Fruit Zone',
                    'B区 - 蔬菜区': 'Area B - Vegetable Zone',
                    'C区 - 肉类区': 'Area C - Meat Zone',
                    'D区 - 海鲜区': 'Area D - Seafood Zone',
                    'E区 - 熟食区': 'Area E - Cooked Food Zone',
                    '产品关键词、特点等': 'Product keywords, features, etc.',
                    '保存产品': 'Save Product',
                    '重置表单': 'Reset Form',
                    '条形码预览': 'Barcode Preview',
                    '输入产品信息后将自动生成条形码': 'Barcode will be generated automatically after entering product information',
                    '产品ID': 'Product ID',
                    '存储区域信息': 'Storage Area Information',
                    'A区': 'Area A',
                    'B区': 'Area B',
                    'C区': 'Area C',
                    'D区': 'Area D',
                    'E区': 'Area E',
                    '水果类产品': 'Fruit products',
                    '蔬菜类产品': 'Vegetable products',
                    '肉类产品': 'Meat products',
                    '海鲜类产品': 'Seafood products',
                    '熟食类产品': 'Cooked food products',

                    # 主页面翻译
                    '果蔬拼台 - AI客服助手': 'Fruit & Vegetable Platform - AI Customer Service',
                    '果蔬拼台客服': 'Fruit & Vegetable Customer Service',
                    'AI智能助手为您服务': 'AI Smart Assistant at Your Service',
                    '欢迎使用果蔬拼台AI客服系统！': 'Welcome to Fruit & Vegetable Platform AI Customer Service!',
                    '我是您的专属AI助手，可以帮助您：': 'I am your dedicated AI assistant, I can help you with:',
                    '🍎 查询产品信息和价格': '🍎 Product information and pricing inquiries',
                    '📦 了解配送和物流状态': '📦 Delivery and logistics status',
                    '💰 处理订单和支付问题': '💰 Order and payment issues',
                    '🎯 获取优惠活动信息': '🎯 Promotional offers and discounts',
                    '❓ 解答其他相关问题': '❓ Other related questions',
                    '请输入您的问题...': 'Please enter your question...',
                    '发送': 'Send',
                    '清除对话': 'Clear Chat',
                    '管理后台': 'Admin Panel',
                    '正在输入...': 'Typing...',
                    '网络连接错误，请稍后重试': 'Network connection error, please try again later',
                    '发送失败，请重试': 'Failed to send, please try again',
                    '繁體中文': '繁體中文',

                    # 新增遗漏的翻译
                    '产品管理': 'Product Management',
                    '客户反馈': 'Customer Feedback',
                    '低库存': 'Low Stock',
                    '正常库存': 'Normal Stock',
                    '库存充足': 'Sufficient Stock',
                    '暂无数据': 'No Data',
                    '加载失败': 'Loading Failed',
                    '操作失败': 'Operation Failed',
                    '请稍后再试': 'Please try again later',
                    '数据加载中': 'Loading Data',
                    '请等待': 'Please Wait',
                    '操作中': 'Processing',
                    '已完成': 'Completed',
                    '失败': 'Failed',
                    '成功': 'Success',
                    '警告': 'Warning',
                    '信息': 'Information',
                    '确认': 'Confirm',
                    '取消': 'Cancel',
                    '关闭': 'Close',
                    '打开': 'Open',
                    '展开': 'Expand',
                    '收起': 'Collapse',
                    '全选': 'Select All',
                    '清空': 'Clear',
                    '重新加载': 'Reload',
                    '上一页': 'Previous',
                    '下一页': 'Next',
                    '第': 'Page',
                    '页': '',
                    '共': 'Total',
                    '条': 'items',
                    '每页显示': 'Items per page',
                    '跳转到': 'Go to page',
                    '总计': 'Total',
                    '小计': 'Subtotal',
                    '合计': 'Sum',
                    '平均': 'Average',
                    '最大': 'Maximum',
                    '最小': 'Minimum',
                    '今日': 'Today',
                    '昨日': 'Yesterday',
                    '本周': 'This Week',
                    '上周': 'Last Week',
                    '本月': 'This Month',
                    '上月': 'Last Month',
                    '今年': 'This Year',
                    '去年': 'Last Year',
                    '全部': 'All',
                    '无': 'None',
                    '是': 'Yes',
                    '否': 'No',
                    '启用': 'Enable',
                    '禁用': 'Disable',
                    '激活': 'Active',
                    '未激活': 'Inactive',
                    '在线': 'Online',
                    '离线': 'Offline',
                    '连接': 'Connected',
                    '断开': 'Disconnected',
                    '同步': 'Sync',
                    '异步': 'Async',
                    '手动': 'Manual',
                    '自动': 'Auto',
                    '立即': 'Immediately',
                    '延迟': 'Delayed',
                    '定时': 'Scheduled',
                    '循环': 'Recurring',
                    '一次性': 'One-time',
                    '永久': 'Permanent',
                    '临时': 'Temporary',

                    # JavaScript中使用的翻译
                    '所有产品库存充足': 'All products have sufficient stock',
                    '正面': 'Positive',
                    '负面': 'Negative',
                    '暂无最新反馈': 'No recent feedback',
                    '确认删除': 'Confirm Delete',
                    '数据已保存': 'Data saved',
                    '数据保存失败': 'Failed to save data',
                    '格式错误': 'Format error',
                    '必填项': 'Required field',
                    '客户': 'Customer',
                    '当前状态': 'Current Status',
                    '客户群号': 'Customer Group Number',
                    '处理人': 'Processor',
                    '反馈详情': 'Feedback Details',
                    '处理备注': 'Processing Notes',
                    '客户图片': 'Customer Images',

                    # 库存盘点相关翻译
                    '进行中': 'In Progress',
                    '已完成': 'Completed',
                    '已取消': 'Cancelled',
                    '条形码': 'Barcode',
                    '存储区域': 'Storage Area',
                    '账面数量': 'Expected Quantity',
                    '实际数量': 'Actual Quantity',
                    '差异': 'Difference',
                    '暂无盘点项目': 'No inventory items',
                    '盘点任务详情': 'Inventory Count Task Details',
                    '任务ID': 'Task ID',
                    '创建时间': 'Created Time',
                    '操作员': 'Operator',
                    '状态': 'Status',
                    '备注': 'Notes',
                    '无': 'None',
                    '盘点汇总': 'Count Summary',
                    '总项目': 'Total Items',
                    '有差异项目': 'Items with Difference',
                    '总差异价值': 'Total Difference Value',
                    '盘点项目': 'Count Items',
                    '继续盘点': 'Continue Count',

                    # 操作日志相关翻译
                    '暂无日志数据': 'No log data',
                    '登录': 'Login',
                    '登出': 'Logout',
                    '盘点': 'Count',
                    '完成盘点': 'Complete Count',
                    '取消盘点': 'Cancel Count',
                    '处理反馈': 'Process Feedback',
                    '产品': 'Product',
                    '盘点任务': 'Count Task',
                    '系统': 'System',
                    '导出': 'Export',
                    '备份': 'Backup',
                    '失败': 'Failed',
                    '已取消': 'Cancelled',
                    '待处理': 'Pending',
                    '测试': 'Test',

                    # 操作日志表头翻译
                    '操作类型': 'Operation Type',
                    '目标类型': 'Target Type',
                    '目标ID': 'Target ID',
                    '详情': 'Details',
                    '时间': 'Time',
                    '操作员': 'Operator',
                    '结果': 'Result'
                }

            # 创建翻译字典
            self.translations = {
                'zh': {},  # 中文使用原文，不需要翻译
                'en': english_translations
            }
            print(f"翻译字典加载完成 - 英文条目: {len(english_translations)}")
        except Exception as e:
            print(f"翻译字典加载失败: {e}")
            self.translations = {'zh': {}, 'en': {}}
    
    def get_locale(self):
        """获取当前语言设置，优先支持美国用户"""
        try:
            from flask import has_request_context

            # 只在有请求上下文时才访问session
            if has_request_context():
                print(f"[DEBUG] get_locale被调用 (有请求上下文)")
                print(f"[DEBUG] session内容: {dict(session)}")

                # 检查session中的语言设置
                if 'language' in session:
                    selected_lang = session['language']
                    if selected_lang in self.languages:
                        print(f"[DEBUG] 使用session语言: {selected_lang}")
                        return selected_lang
                    else:
                        print(f"[DEBUG] session中的语言无效: {selected_lang}")
                else:
                    print(f"[DEBUG] session中没有language字段")

                # 尝试检测浏览器语言偏好（优先支持美国用户）
                try:
                    from flask import request
                    if request and hasattr(request, 'headers'):
                        accept_language = request.headers.get('Accept-Language', '')
                        print(f"[DEBUG] 浏览器Accept-Language: {accept_language}")

                        # 检测英语
                        if 'en' in accept_language:
                            print(f"[DEBUG] 检测到英语，使用en")
                            return 'en'
                except Exception as e:
                    print(f"[DEBUG] 浏览器语言检测失败: {e}")
            else:
                print(f"[DEBUG] get_locale被调用 (无请求上下文)")

            # 返回默认语言
            print(f"[DEBUG] 使用默认语言: {self.default_language}")
            return self.default_language
        except Exception as e:
            print(f"[ERROR] get_locale错误: {e}")
            return self.default_language
    
    def translate(self, text, language=None):
        """翻译文本，支持en_US回退到en"""
        if language is None:
            language = self.get_locale()

        # 如果是中文，返回原文
        if language == 'zh':
            return text

        # 如果是英文或美式英文，使用英文翻译
        if language == 'en' or language == 'en_US':
            return self.translations['en'].get(text, text)

        # 其他语言或没有翻译，返回原文
        return text
    
    def set_language(self, language_code: str) -> bool:
        """设置用户语言偏好"""
        try:
            from flask import has_request_context

            print(f"[DEBUG] set_language被调用: {language_code}")
            print(f"[DEBUG] 可用语言: {list(self.languages.keys())}")
            print(f"[DEBUG] 语言是否存在: {language_code in self.languages}")

            if language_code in self.languages:
                if has_request_context():
                    session['language'] = language_code
                    print(f"[DEBUG] 语言设置成功: {language_code}")
                    return True
                else:
                    print(f"[DEBUG] 无请求上下文，无法设置session")
                    return False
            else:
                print(f"[DEBUG] 不支持的语言: {language_code}")
                return False
        except Exception as e:
            print(f"[ERROR] set_language错误: {e}")
            return False
    
    def get_current_language(self) -> Dict:
        """获取当前语言信息"""
        current_code = self.get_locale()
        return self.languages.get(current_code, self.languages[self.default_language])
    
    def get_available_languages(self) -> List[Dict]:
        """获取所有可用语言列表"""
        return [
            {
                'code': code,
                'name': info['name'],
                'native_name': info['native_name'],
                'flag': info['flag'],
                'is_current': code == self.get_locale()
            }
            for code, info in self.languages.items()
        ]
    
    def init_app(self, app):
        """初始化Flask应用的国际化配置"""
        print(f"简洁国际化配置初始化完成 - 支持语言: {list(self.languages.keys())}")
        
        # 存储引用
        app.i18n_manager = self
        
        # 注册模板全局函数
        self._register_template_globals(app)
    
    def _register_template_globals(self, app):
        """注册模板全局函数"""
        
        @app.template_global()
        def get_current_language():
            """模板中获取当前语言代码"""
            return self.get_locale()
        
        @app.template_global()
        def get_current_language_info():
            """模板中获取当前语言信息"""
            return self.get_current_language()
        
        @app.template_global()
        def get_available_languages():
            """模板中获取可用语言列表"""
            return self.get_available_languages()
        
        @app.template_global()
        def _(text, **kwargs):
            """模板中的翻译函数"""
            return self.translate(text)


# 全局国际化配置实例
i18n_simple = SimpleI18n()


# 便捷的翻译函数
def _(text, **kwargs):
    """翻译函数的简化别名"""
    return i18n_simple.translate(text)


# 导出常用函数和类
__all__ = [
    'i18n_simple',
    '_'
]
