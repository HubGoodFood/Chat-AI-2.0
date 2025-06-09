"""
数据导出模块
"""
import json
import csv
import io
from datetime import datetime
from typing import List, Dict, Any


class DataExporter:
    def __init__(self):
        pass
    
    def export_inventory_to_csv(self, inventory_data: List[Dict]) -> str:
        """导出库存数据为CSV格式"""
        try:
            output = io.StringIO()
            
            if not inventory_data:
                return ""
            
            # 定义CSV列
            fieldnames = [
                'product_id', 'product_name', 'category', 'specification',
                'price', 'unit', 'current_stock', 'min_stock_warning',
                'description', 'image_url', 'status', 'created_at', 'updated_at'
            ]
            
            writer = csv.DictWriter(output, fieldnames=fieldnames)
            writer.writeheader()
            
            for product in inventory_data:
                # 清理数据，确保所有字段都存在
                row = {}
                for field in fieldnames:
                    row[field] = product.get(field, '')
                writer.writerow(row)
            
            return output.getvalue()
            
        except Exception as e:
            print(f"导出库存数据失败: {e}")
            return ""
    
    def export_feedback_to_csv(self, feedback_data: List[Dict]) -> str:
        """导出反馈数据为CSV格式"""
        try:
            output = io.StringIO()
            
            if not feedback_data:
                return ""
            
            # 定义CSV列
            fieldnames = [
                'feedback_id', 'product_name', 'customer_wechat_name',
                'customer_group_number', 'payment_status', 'feedback_type',
                'feedback_content', 'processing_status', 'processor',
                'processing_notes', 'feedback_time', 'processing_time'
            ]
            
            writer = csv.DictWriter(output, fieldnames=fieldnames)
            writer.writeheader()
            
            for feedback in feedback_data:
                # 清理数据
                row = {}
                for field in fieldnames:
                    value = feedback.get(field, '')
                    # 处理客户图片列表
                    if field == 'customer_images' and isinstance(value, list):
                        value = '; '.join(value)
                    row[field] = value
                writer.writerow(row)
            
            return output.getvalue()
            
        except Exception as e:
            print(f"导出反馈数据失败: {e}")
            return ""
    
    def export_logs_to_csv(self, log_data: List[Dict]) -> str:
        """导出操作日志为CSV格式"""
        try:
            output = io.StringIO()
            
            if not log_data:
                return ""
            
            # 定义CSV列
            fieldnames = [
                'log_id', 'timestamp', 'operator', 'operation_type',
                'target_type', 'target_id', 'result', 'details'
            ]
            
            writer = csv.DictWriter(output, fieldnames=fieldnames)
            writer.writeheader()
            
            for log in log_data:
                # 清理数据
                row = {}
                for field in fieldnames:
                    value = log.get(field, '')
                    # 处理details字典
                    if field == 'details' and isinstance(value, dict):
                        value = json.dumps(value, ensure_ascii=False)
                    row[field] = value
                writer.writerow(row)
            
            return output.getvalue()
            
        except Exception as e:
            print(f"导出日志数据失败: {e}")
            return ""
    
    def export_to_json(self, data: Any, pretty: bool = True) -> str:
        """导出数据为JSON格式"""
        try:
            if pretty:
                return json.dumps(data, ensure_ascii=False, indent=2)
            else:
                return json.dumps(data, ensure_ascii=False)
        except Exception as e:
            print(f"导出JSON数据失败: {e}")
            return ""
    
    def generate_inventory_report(self, inventory_data: List[Dict], 
                                 summary_data: Dict) -> str:
        """生成库存报告"""
        try:
            report_lines = []
            report_lines.append("# 库存管理报告")
            report_lines.append(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            report_lines.append("")
            
            # 汇总信息
            report_lines.append("## 库存汇总")
            report_lines.append(f"- 总产品数: {summary_data.get('total_products', 0)}")
            report_lines.append(f"- 正常产品数: {summary_data.get('active_products', 0)}")
            report_lines.append(f"- 低库存产品数: {summary_data.get('low_stock_count', 0)}")
            report_lines.append(f"- 库存总价值: ¥{summary_data.get('total_value', 0)}")
            report_lines.append("")
            
            # 按分类统计
            category_stats = {}
            low_stock_products = []
            
            for product in inventory_data:
                if product['status'] == 'active':
                    category = product['category']
                    if category not in category_stats:
                        category_stats[category] = {'count': 0, 'total_stock': 0}
                    
                    category_stats[category]['count'] += 1
                    category_stats[category]['total_stock'] += product['current_stock']
                    
                    # 检查低库存
                    if product['current_stock'] <= product['min_stock_warning']:
                        low_stock_products.append(product)
            
            report_lines.append("## 分类统计")
            for category, stats in category_stats.items():
                report_lines.append(f"- {category}: {stats['count']} 个产品, 总库存 {stats['total_stock']}")
            report_lines.append("")
            
            # 低库存产品
            if low_stock_products:
                report_lines.append("## ⚠️ 低库存产品")
                for product in low_stock_products:
                    report_lines.append(f"- {product['product_name']}: {product['current_stock']} {product['unit']} (警告线: {product['min_stock_warning']})")
            else:
                report_lines.append("## ✅ 库存状态良好")
                report_lines.append("所有产品库存充足")
            
            return "\n".join(report_lines)
            
        except Exception as e:
            print(f"生成库存报告失败: {e}")
            return ""
    
    def generate_feedback_report(self, feedback_data: List[Dict], 
                                stats_data: Dict) -> str:
        """生成反馈报告"""
        try:
            report_lines = []
            report_lines.append("# 客户反馈报告")
            report_lines.append(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            report_lines.append("")
            
            # 汇总信息
            report_lines.append("## 反馈汇总")
            report_lines.append(f"- 总反馈数: {stats_data.get('total_feedback', 0)}")
            report_lines.append(f"- 正面反馈: {stats_data.get('positive_feedback', 0)}")
            report_lines.append(f"- 负面反馈: {stats_data.get('negative_feedback', 0)}")
            report_lines.append(f"- 待处理: {stats_data.get('pending_feedback', 0)}")
            report_lines.append(f"- 处理中: {stats_data.get('processing_feedback', 0)}")
            report_lines.append(f"- 已解决: {stats_data.get('resolved_feedback', 0)}")
            report_lines.append("")
            
            # 按产品统计
            product_feedback = stats_data.get('product_feedback', {})
            if product_feedback:
                report_lines.append("## 产品反馈统计")
                for product, stats in product_feedback.items():
                    total = stats['total']
                    positive = stats['positive']
                    negative = stats['negative']
                    satisfaction = (positive / total * 100) if total > 0 else 0
                    report_lines.append(f"- {product}: {total} 条反馈 (正面: {positive}, 负面: {negative}, 满意度: {satisfaction:.1f}%)")
                report_lines.append("")
            
            # 待处理反馈
            pending_feedback = [f for f in feedback_data if f['processing_status'] == '待处理']
            if pending_feedback:
                report_lines.append("## ⏳ 待处理反馈")
                for feedback in pending_feedback[:10]:  # 只显示前10条
                    feedback_type = "正面" if feedback['feedback_type'] == 'positive' else "负面"
                    report_lines.append(f"- {feedback['product_name']} ({feedback_type}) - {feedback['customer_wechat_name']}")
            
            return "\n".join(report_lines)
            
        except Exception as e:
            print(f"生成反馈报告失败: {e}")
            return ""
    
    def create_backup_data(self, inventory_data: List[Dict], feedback_data: List[Dict], 
                          log_data: List[Dict]) -> Dict:
        """创建完整的数据备份"""
        try:
            backup_data = {
                "backup_info": {
                    "created_at": datetime.now().isoformat(),
                    "version": "2.0",
                    "description": "果蔬客服AI系统数据备份"
                },
                "inventory": inventory_data,
                "feedback": feedback_data,
                "operation_logs": log_data
            }
            
            return backup_data
            
        except Exception as e:
            print(f"创建备份数据失败: {e}")
            return {}


# 全局导出器实例
data_exporter = DataExporter()
