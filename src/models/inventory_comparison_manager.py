"""
库存对比分析管理器
负责处理不同时期库存数据的对比分析和报表生成
"""
import json
import os
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
import uuid
from collections import defaultdict


class InventoryComparisonManager:
    """
    库存对比分析管理器
    
    主要功能：
    1. 对比不同时期的盘点结果
    2. 分析库存变化趋势
    3. 检测异常库存波动
    4. 生成各类库存报表
    """
    
    def __init__(self):
        self.comparisons_file = 'data/inventory_comparisons.json'
        self.counts_file = 'data/inventory_counts.json'
        self.inventory_file = 'data/inventory.json'
        self._ensure_comparisons_file()
    
    def _ensure_comparisons_file(self):
        """确保对比分析数据文件存在"""
        if not os.path.exists(self.comparisons_file):
            self._initialize_comparisons_file()
    
    def _initialize_comparisons_file(self):
        """初始化对比分析数据文件"""
        try:
            initial_data = {
                "last_updated": datetime.now().isoformat(),
                "comparisons": {}
            }
            
            os.makedirs(os.path.dirname(self.comparisons_file), exist_ok=True)
            with open(self.comparisons_file, 'w', encoding='utf-8') as f:
                json.dump(initial_data, f, ensure_ascii=False, indent=2)
            
            print("库存对比分析数据文件初始化完成")
            
        except Exception as e:
            print(f"初始化对比分析数据文件失败: {e}")
    
    def _load_comparisons(self) -> Dict:
        """加载对比分析数据"""
        try:
            with open(self.comparisons_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"加载对比分析数据失败: {e}")
            return {"last_updated": datetime.now().isoformat(), "comparisons": {}}
    
    def _save_comparisons(self, comparisons_data: Dict):
        """保存对比分析数据"""
        try:
            comparisons_data["last_updated"] = datetime.now().isoformat()
            with open(self.comparisons_file, 'w', encoding='utf-8') as f:
                json.dump(comparisons_data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"保存对比分析数据失败: {e}")
    
    def _load_counts(self) -> Dict:
        """加载盘点数据"""
        try:
            with open(self.counts_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"加载盘点数据失败: {e}")
            return {"counts": {}}
    
    def _load_inventory(self) -> Dict:
        """加载库存数据"""
        try:
            with open(self.inventory_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"加载库存数据失败: {e}")
            return {"products": {}}
    
    def _generate_comparison_id(self) -> str:
        """
        生成唯一的对比分析ID
        
        Returns:
            str: 对比分析ID，格式：COMP_YYYYMMDD_HHMMSS_随机数
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        random_suffix = str(uuid.uuid4())[:8]
        return f"COMP_{timestamp}_{random_suffix}"
    
    def get_completed_counts(self) -> List[Dict]:
        """
        获取所有已完成的盘点任务
        
        Returns:
            List[Dict]: 已完成的盘点任务列表，按时间倒序排列
        """
        counts_data = self._load_counts()
        completed_counts = []
        
        for count_id, count_task in counts_data["counts"].items():
            if count_task["status"] == "completed":
                completed_counts.append(count_task)
        
        # 按完成时间倒序排列
        completed_counts.sort(
            key=lambda x: x.get("completed_at", x["count_date"]), 
            reverse=True
        )
        
        return completed_counts
    
    def get_latest_counts(self, limit: int = 2) -> List[Dict]:
        """
        获取最近的已完成盘点任务
        
        Args:
            limit: 获取数量限制
            
        Returns:
            List[Dict]: 最近的盘点任务列表
        """
        completed_counts = self.get_completed_counts()
        return completed_counts[:limit]
    
    def calculate_item_changes(self, current_items: List[Dict], previous_items: List[Dict]) -> List[Dict]:
        """
        计算盘点项目之间的变化
        
        Args:
            current_items: 当前盘点的项目列表
            previous_items: 之前盘点的项目列表
            
        Returns:
            List[Dict]: 变化分析结果列表
        """
        changes = []
        
        # 将之前的盘点数据转换为字典，便于查找
        previous_dict = {item["product_id"]: item for item in previous_items}
        current_dict = {item["product_id"]: item for item in current_items}
        
        # 获取所有涉及的产品ID
        all_product_ids = set(previous_dict.keys()) | set(current_dict.keys())
        
        for product_id in all_product_ids:
            current_item = current_dict.get(product_id)
            previous_item = previous_dict.get(product_id)
            
            change_record = {
                "product_id": product_id,
                "product_name": "",
                "category": "",
                "storage_area": "",
                "previous_quantity": 0,
                "current_quantity": 0,
                "quantity_change": 0,
                "change_percentage": 0.0,
                "status": "unchanged"  # new, removed, changed, unchanged
            }
            
            if current_item and previous_item:
                # 产品在两次盘点中都存在
                change_record.update({
                    "product_name": current_item["product_name"],
                    "category": current_item["category"],
                    "storage_area": current_item.get("storage_area", ""),
                    "previous_quantity": previous_item["actual_quantity"],
                    "current_quantity": current_item["actual_quantity"],
                })
                
                quantity_change = current_item["actual_quantity"] - previous_item["actual_quantity"]
                change_record["quantity_change"] = quantity_change
                
                # 计算变化百分比
                if previous_item["actual_quantity"] > 0:
                    change_percentage = (quantity_change / previous_item["actual_quantity"]) * 100
                    change_record["change_percentage"] = round(change_percentage, 2)
                
                # 判断变化状态
                if quantity_change == 0:
                    change_record["status"] = "unchanged"
                else:
                    change_record["status"] = "changed"
                    
            elif current_item and not previous_item:
                # 新增产品
                change_record.update({
                    "product_name": current_item["product_name"],
                    "category": current_item["category"],
                    "storage_area": current_item.get("storage_area", ""),
                    "current_quantity": current_item["actual_quantity"],
                    "quantity_change": current_item["actual_quantity"],
                    "status": "new"
                })
                
            elif previous_item and not current_item:
                # 移除的产品
                change_record.update({
                    "product_name": previous_item["product_name"],
                    "category": previous_item["category"],
                    "storage_area": previous_item.get("storage_area", ""),
                    "previous_quantity": previous_item["actual_quantity"],
                    "quantity_change": -previous_item["actual_quantity"],
                    "status": "removed"
                })
            
            changes.append(change_record)

        return changes

    def create_comparison(self, current_count_id: str, previous_count_id: str,
                         comparison_type: str = "manual", operator: str = "system") -> Optional[str]:
        """
        创建库存对比分析

        Args:
            current_count_id: 当前盘点任务ID
            previous_count_id: 之前盘点任务ID
            comparison_type: 对比类型 (weekly, manual, auto)
            operator: 操作员

        Returns:
            str: 对比分析ID，失败返回None
        """
        try:
            counts_data = self._load_counts()

            # 检查盘点任务是否存在且已完成
            current_count = counts_data["counts"].get(current_count_id)
            previous_count = counts_data["counts"].get(previous_count_id)

            if not current_count or current_count["status"] != "completed":
                print(f"当前盘点任务不存在或未完成: {current_count_id}")
                return None

            if not previous_count or previous_count["status"] != "completed":
                print(f"之前盘点任务不存在或未完成: {previous_count_id}")
                return None

            # 计算变化
            changes = self.calculate_item_changes(
                current_count["items"],
                previous_count["items"]
            )

            # 生成统计信息
            statistics = self._calculate_comparison_statistics(changes)

            # 异常检测
            anomalies = self._detect_anomalies(changes)

            # 创建对比记录
            comparison_id = self._generate_comparison_id()
            comparison_record = {
                "comparison_id": comparison_id,
                "comparison_date": datetime.now().isoformat(),
                "comparison_type": comparison_type,
                "operator": operator,
                "current_count": {
                    "count_id": current_count_id,
                    "count_date": current_count["count_date"],
                    "operator": current_count["operator"]
                },
                "previous_count": {
                    "count_id": previous_count_id,
                    "count_date": previous_count["count_date"],
                    "operator": previous_count["operator"]
                },
                "changes": changes,
                "statistics": statistics,
                "anomalies": anomalies,
                "created_at": datetime.now().isoformat()
            }

            # 保存对比记录
            comparisons_data = self._load_comparisons()
            comparisons_data["comparisons"][comparison_id] = comparison_record
            self._save_comparisons(comparisons_data)

            print(f"对比分析创建成功，ID: {comparison_id}")
            return comparison_id

        except Exception as e:
            print(f"创建对比分析失败: {e}")
            return None

    def _calculate_comparison_statistics(self, changes: List[Dict]) -> Dict:
        """
        计算对比统计信息

        Args:
            changes: 变化记录列表

        Returns:
            Dict: 统计信息
        """
        stats = {
            "total_products": len(changes),
            "new_products": 0,
            "removed_products": 0,
            "changed_products": 0,
            "unchanged_products": 0,
            "total_quantity_change": 0,
            "positive_changes": 0,
            "negative_changes": 0,
            "largest_increase": {"product_name": "", "change": 0},
            "largest_decrease": {"product_name": "", "change": 0},
            "average_change_percentage": 0.0
        }

        total_percentage_change = 0
        percentage_count = 0

        for change in changes:
            status = change["status"]
            quantity_change = change["quantity_change"]

            # 统计状态
            if status == "new":
                stats["new_products"] += 1
            elif status == "removed":
                stats["removed_products"] += 1
            elif status == "changed":
                stats["changed_products"] += 1
            else:
                stats["unchanged_products"] += 1

            # 统计数量变化
            stats["total_quantity_change"] += quantity_change

            if quantity_change > 0:
                stats["positive_changes"] += 1
                if quantity_change > stats["largest_increase"]["change"]:
                    stats["largest_increase"] = {
                        "product_name": change["product_name"],
                        "change": quantity_change
                    }
            elif quantity_change < 0:
                stats["negative_changes"] += 1
                if quantity_change < stats["largest_decrease"]["change"]:
                    stats["largest_decrease"] = {
                        "product_name": change["product_name"],
                        "change": quantity_change
                    }

            # 计算平均变化百分比
            if change["change_percentage"] != 0:
                total_percentage_change += abs(change["change_percentage"])
                percentage_count += 1

        # 计算平均变化百分比
        if percentage_count > 0:
            stats["average_change_percentage"] = round(
                total_percentage_change / percentage_count, 2
            )

        return stats

    def _detect_anomalies(self, changes: List[Dict],
                         threshold_percentage: float = 50.0,
                         threshold_quantity: int = 20) -> List[Dict]:
        """
        检测异常的库存变化

        Args:
            changes: 变化记录列表
            threshold_percentage: 百分比变化阈值
            threshold_quantity: 数量变化阈值

        Returns:
            List[Dict]: 异常记录列表
        """
        anomalies = []

        for change in changes:
            anomaly_reasons = []

            # 检查百分比变化异常
            if abs(change["change_percentage"]) > threshold_percentage:
                anomaly_reasons.append(f"变化百分比超过{threshold_percentage}%")

            # 检查数量变化异常
            if abs(change["quantity_change"]) > threshold_quantity:
                anomaly_reasons.append(f"数量变化超过{threshold_quantity}个")

            # 检查新增或移除产品
            if change["status"] == "new":
                anomaly_reasons.append("新增产品")
            elif change["status"] == "removed":
                anomaly_reasons.append("产品被移除")

            # 如果有异常，记录下来
            if anomaly_reasons:
                anomaly_record = {
                    "product_id": change["product_id"],
                    "product_name": change["product_name"],
                    "category": change["category"],
                    "storage_area": change["storage_area"],
                    "quantity_change": change["quantity_change"],
                    "change_percentage": change["change_percentage"],
                    "status": change["status"],
                    "anomaly_reasons": anomaly_reasons,
                    "severity": self._calculate_anomaly_severity(change, anomaly_reasons)
                }
                anomalies.append(anomaly_record)

        # 按严重程度排序
        anomalies.sort(key=lambda x: x["severity"], reverse=True)

        return anomalies

    def _calculate_anomaly_severity(self, change: Dict, reasons: List[str]) -> int:
        """
        计算异常严重程度

        Args:
            change: 变化记录
            reasons: 异常原因列表

        Returns:
            int: 严重程度分数 (1-10)
        """
        severity = 0

        # 基于变化百分比
        percentage = abs(change["change_percentage"])
        if percentage > 100:
            severity += 5
        elif percentage > 50:
            severity += 3
        elif percentage > 20:
            severity += 1

        # 基于数量变化
        quantity = abs(change["quantity_change"])
        if quantity > 50:
            severity += 3
        elif quantity > 20:
            severity += 2
        elif quantity > 10:
            severity += 1

        # 基于状态
        if change["status"] in ["new", "removed"]:
            severity += 2

        return min(severity, 10)  # 最大值为10

    def create_weekly_comparison(self, operator: str = "system") -> Optional[str]:
        """
        创建周对比分析（对比最近两次盘点）

        Args:
            operator: 操作员

        Returns:
            str: 对比分析ID，失败返回None
        """
        try:
            # 获取最近两次盘点
            recent_counts = self.get_latest_counts(2)

            if len(recent_counts) < 2:
                print("没有足够的盘点数据进行周对比分析")
                return None

            current_count = recent_counts[0]
            previous_count = recent_counts[1]

            # 创建对比分析
            comparison_id = self.create_comparison(
                current_count["count_id"],
                previous_count["count_id"],
                "weekly",
                operator
            )

            if comparison_id:
                print(f"周对比分析创建成功: {comparison_id}")

            return comparison_id

        except Exception as e:
            print(f"创建周对比分析失败: {e}")
            return None

    def get_comparison(self, comparison_id: str) -> Optional[Dict]:
        """
        获取对比分析结果

        Args:
            comparison_id: 对比分析ID

        Returns:
            Dict: 对比分析结果，如果不存在返回None
        """
        comparisons_data = self._load_comparisons()
        return comparisons_data["comparisons"].get(comparison_id)

    def get_comparison_by_id(self, comparison_id: str) -> Optional[Dict]:
        """
        根据ID获取对比分析结果（别名方法）

        Args:
            comparison_id: 对比分析ID

        Returns:
            Dict: 对比分析结果，如果不存在返回None
        """
        return self.get_comparison(comparison_id)

    def get_all_comparisons(self, comparison_type: str = None) -> List[Dict]:
        """
        获取所有对比分析

        Args:
            comparison_type: 可选，按类型筛选 (weekly, manual, auto)

        Returns:
            List[Dict]: 对比分析列表
        """
        comparisons_data = self._load_comparisons()
        comparisons = list(comparisons_data["comparisons"].values())

        if comparison_type:
            comparisons = [comp for comp in comparisons
                          if comp["comparison_type"] == comparison_type]

        # 按创建时间倒序排列
        comparisons.sort(key=lambda x: x["comparison_date"], reverse=True)
        return comparisons

    def get_product_trend_analysis(self, product_id: str, limit: int = 5) -> Dict:
        """
        获取单个产品的历史变化趋势

        Args:
            product_id: 产品ID
            limit: 分析的对比记录数量限制

        Returns:
            Dict: 产品趋势分析结果
        """
        try:
            # 获取最近的对比记录
            comparisons = self.get_all_comparisons()[:limit]

            trend_data = {
                "product_id": product_id,
                "product_name": "",
                "category": "",
                "storage_area": "",
                "trend_points": [],
                "summary": {
                    "total_comparisons": 0,
                    "average_change": 0.0,
                    "trend_direction": "stable",  # increasing, decreasing, stable, volatile
                    "volatility_score": 0.0
                }
            }

            changes_list = []

            for comparison in comparisons:
                for change in comparison["changes"]:
                    if change["product_id"] == product_id:
                        trend_point = {
                            "comparison_date": comparison["comparison_date"],
                            "comparison_id": comparison["comparison_id"],
                            "quantity_change": change["quantity_change"],
                            "change_percentage": change["change_percentage"],
                            "current_quantity": change["current_quantity"],
                            "previous_quantity": change["previous_quantity"]
                        }
                        trend_data["trend_points"].append(trend_point)
                        changes_list.append(change["quantity_change"])

                        # 更新产品基本信息
                        if not trend_data["product_name"]:
                            trend_data["product_name"] = change["product_name"]
                            trend_data["category"] = change["category"]
                            trend_data["storage_area"] = change["storage_area"]

            # 计算趋势汇总
            if changes_list:
                trend_data["summary"]["total_comparisons"] = len(changes_list)
                trend_data["summary"]["average_change"] = round(
                    sum(changes_list) / len(changes_list), 2
                )

                # 判断趋势方向
                positive_changes = sum(1 for x in changes_list if x > 0)
                negative_changes = sum(1 for x in changes_list if x < 0)

                if positive_changes > negative_changes * 1.5:
                    trend_data["summary"]["trend_direction"] = "increasing"
                elif negative_changes > positive_changes * 1.5:
                    trend_data["summary"]["trend_direction"] = "decreasing"
                elif abs(positive_changes - negative_changes) <= 1:
                    trend_data["summary"]["trend_direction"] = "stable"
                else:
                    trend_data["summary"]["trend_direction"] = "volatile"

                # 计算波动性分数
                if len(changes_list) > 1:
                    variance = sum((x - trend_data["summary"]["average_change"]) ** 2
                                 for x in changes_list) / len(changes_list)
                    trend_data["summary"]["volatility_score"] = round(variance ** 0.5, 2)

            return trend_data

        except Exception as e:
            print(f"获取产品趋势分析失败: {e}")
            return {
                "product_id": product_id,
                "error": str(e)
            }

    def generate_weekly_report(self, comparison_id: str = None) -> Dict:
        """
        生成周报表

        Args:
            comparison_id: 可选，指定对比分析ID，否则使用最新的周对比

        Returns:
            Dict: 周报表数据
        """
        try:
            # 如果没有指定对比ID，获取最新的周对比
            if not comparison_id:
                weekly_comparisons = self.get_all_comparisons("weekly")
                if not weekly_comparisons:
                    return {"error": "没有可用的周对比数据"}
                comparison = weekly_comparisons[0]
            else:
                comparison = self.get_comparison(comparison_id)
                if not comparison:
                    return {"error": "对比分析不存在"}

            # 生成报表数据
            report = {
                "report_type": "weekly",
                "report_date": datetime.now().isoformat(),
                "comparison_period": {
                    "current": comparison["current_count"],
                    "previous": comparison["previous_count"]
                },
                "summary": comparison["statistics"],
                "top_changes": self._get_top_changes(comparison["changes"]),
                "anomalies": comparison["anomalies"][:10],  # 前10个异常
                "category_analysis": self._analyze_by_category(comparison["changes"]),
                "storage_area_analysis": self._analyze_by_storage_area(comparison["changes"]),
                "recommendations": self._generate_recommendations(comparison)
            }

            return report

        except Exception as e:
            print(f"生成周报表失败: {e}")
            return {"error": str(e)}

    def _get_top_changes(self, changes: List[Dict], limit: int = 10) -> Dict:
        """
        获取变化最大的产品

        Args:
            changes: 变化记录列表
            limit: 返回数量限制

        Returns:
            Dict: 包含增加最多和减少最多的产品
        """
        # 按数量变化排序
        sorted_by_increase = sorted(changes, key=lambda x: x["quantity_change"], reverse=True)
        sorted_by_decrease = sorted(changes, key=lambda x: x["quantity_change"])

        return {
            "top_increases": sorted_by_increase[:limit],
            "top_decreases": sorted_by_decrease[:limit]
        }

    def _analyze_by_category(self, changes: List[Dict]) -> Dict:
        """
        按产品分类分析变化

        Args:
            changes: 变化记录列表

        Returns:
            Dict: 分类分析结果
        """
        category_stats = defaultdict(lambda: {
            "total_products": 0,
            "changed_products": 0,
            "total_change": 0,
            "average_change": 0.0
        })

        for change in changes:
            category = change["category"].strip()
            stats = category_stats[category]

            stats["total_products"] += 1
            if change["status"] == "changed":
                stats["changed_products"] += 1
            stats["total_change"] += change["quantity_change"]

        # 计算平均变化
        for category, stats in category_stats.items():
            if stats["total_products"] > 0:
                stats["average_change"] = round(
                    stats["total_change"] / stats["total_products"], 2
                )

        return dict(category_stats)

    def _analyze_by_storage_area(self, changes: List[Dict]) -> Dict:
        """
        按存储区域分析变化

        Args:
            changes: 变化记录列表

        Returns:
            Dict: 存储区域分析结果
        """
        area_stats = defaultdict(lambda: {
            "total_products": 0,
            "changed_products": 0,
            "total_change": 0,
            "average_change": 0.0
        })

        for change in changes:
            area = change.get("storage_area", "未知").strip()
            stats = area_stats[area]

            stats["total_products"] += 1
            if change["status"] == "changed":
                stats["changed_products"] += 1
            stats["total_change"] += change["quantity_change"]

        # 计算平均变化
        for area, stats in area_stats.items():
            if stats["total_products"] > 0:
                stats["average_change"] = round(
                    stats["total_change"] / stats["total_products"], 2
                )

        return dict(area_stats)

    def _generate_recommendations(self, comparison: Dict) -> List[str]:
        """
        基于对比分析生成建议

        Args:
            comparison: 对比分析数据

        Returns:
            List[str]: 建议列表
        """
        recommendations = []
        stats = comparison["statistics"]
        anomalies = comparison["anomalies"]

        # 基于统计数据的建议
        if stats["new_products"] > 0:
            recommendations.append(f"发现 {stats['new_products']} 个新增产品，请确认是否为正常入库")

        if stats["removed_products"] > 0:
            recommendations.append(f"发现 {stats['removed_products']} 个产品被移除，请检查是否为正常出库")

        if stats["negative_changes"] > stats["positive_changes"]:
            recommendations.append("库存整体呈下降趋势，建议关注补货计划")
        elif stats["positive_changes"] > stats["negative_changes"] * 2:
            recommendations.append("库存增长较快，请检查是否有积压风险")

        # 基于异常的建议
        if len(anomalies) > 0:
            high_severity_anomalies = [a for a in anomalies if a["severity"] >= 7]
            if high_severity_anomalies:
                recommendations.append(f"发现 {len(high_severity_anomalies)} 个高风险异常，需要立即处理")

        # 基于平均变化的建议
        if stats["average_change_percentage"] > 30:
            recommendations.append("库存变化波动较大，建议加强库存管控")

        return recommendations

    def get_comparison_statistics(self) -> Dict:
        """
        获取对比分析统计信息

        Returns:
            Dict: 统计信息
        """
        try:
            comparisons_data = self._load_comparisons()

            total_comparisons = len(comparisons_data["comparisons"])
            weekly_comparisons = 0
            manual_comparisons = 0
            auto_comparisons = 0

            for comparison in comparisons_data["comparisons"].values():
                comp_type = comparison["comparison_type"]
                if comp_type == "weekly":
                    weekly_comparisons += 1
                elif comp_type == "manual":
                    manual_comparisons += 1
                elif comp_type == "auto":
                    auto_comparisons += 1

            return {
                "total_comparisons": total_comparisons,
                "weekly_comparisons": weekly_comparisons,
                "manual_comparisons": manual_comparisons,
                "auto_comparisons": auto_comparisons,
                "last_updated": comparisons_data["last_updated"]
            }

        except Exception as e:
            print(f"获取对比统计失败: {e}")
            return {
                "total_comparisons": 0,
                "weekly_comparisons": 0,
                "manual_comparisons": 0,
                "auto_comparisons": 0,
                "last_updated": datetime.now().isoformat()
            }

    def delete_comparison(self, comparison_id: str) -> bool:
        """
        删除对比分析记录

        Args:
            comparison_id: 对比分析ID

        Returns:
            bool: 是否删除成功
        """
        try:
            comparisons_data = self._load_comparisons()

            if comparison_id in comparisons_data["comparisons"]:
                del comparisons_data["comparisons"][comparison_id]
                self._save_comparisons(comparisons_data)
                print(f"对比分析记录已删除: {comparison_id}")
                return True
            else:
                print(f"对比分析记录不存在: {comparison_id}")
                return False

        except Exception as e:
            print(f"删除对比分析记录失败: {e}")
            return False

    def generate_comparison_report(self, comparison: Dict) -> str:
        """
        生成对比分析报告（Markdown格式）

        Args:
            comparison: 对比分析数据

        Returns:
            str: Markdown格式的报告内容
        """
        try:
            report_lines = []

            # 报告标题
            report_lines.append(f"# 库存对比分析报告")
            report_lines.append(f"")
            report_lines.append(f"**报告ID**: {comparison['comparison_id']}")
            report_lines.append(f"**生成时间**: {comparison['comparison_date']}")
            report_lines.append(f"**分析类型**: {comparison['comparison_type']}")
            report_lines.append(f"**操作员**: {comparison['operator']}")
            report_lines.append(f"")

            # 对比范围
            report_lines.append(f"## 对比范围")
            report_lines.append(f"")
            report_lines.append(f"- **当前盘点**: {comparison['current_count']['count_id']} ({comparison['current_count']['count_date']})")
            report_lines.append(f"- **对比盘点**: {comparison['previous_count']['count_id']} ({comparison['previous_count']['count_date']})")
            report_lines.append(f"")

            # 统计汇总
            stats = comparison['statistics']
            report_lines.append(f"## 统计汇总")
            report_lines.append(f"")
            report_lines.append(f"| 指标 | 数值 |")
            report_lines.append(f"|------|------|")
            report_lines.append(f"| 总产品数 | {stats['total_products']} |")
            report_lines.append(f"| 变化产品数 | {stats['changed_products']} |")
            report_lines.append(f"| 新增产品 | {stats['new_products']} |")
            report_lines.append(f"| 移除产品 | {stats['removed_products']} |")
            report_lines.append(f"| 库存增加项目 | {stats['positive_changes']} |")
            report_lines.append(f"| 库存减少项目 | {stats['negative_changes']} |")
            report_lines.append(f"| 平均变化百分比 | {stats.get('average_change_percentage', 0):.2f}% |")
            report_lines.append(f"")

            # 变化明细（前20项）
            changes = comparison['changes'][:20]
            if changes:
                report_lines.append(f"## 主要变化明细")
                report_lines.append(f"")
                report_lines.append(f"| 产品名称 | 分类 | 之前数量 | 当前数量 | 变化量 | 状态 |")
                report_lines.append(f"|----------|------|----------|----------|--------|------|")

                for change in changes:
                    status_text = {
                        'increased': '库存增加',
                        'decreased': '库存减少',
                        'new': '新增产品',
                        'removed': '移除产品'
                    }.get(change['status'], change['status'])

                    report_lines.append(f"| {change['product_name']} | {change['category']} | {change.get('previous_quantity', '-')} | {change.get('current_quantity', '-')} | {change['quantity_change']} | {status_text} |")

                report_lines.append(f"")

            # 异常检测结果
            anomalies = comparison['anomalies'][:10]
            if anomalies:
                report_lines.append(f"## 异常检测结果")
                report_lines.append(f"")
                for i, anomaly in enumerate(anomalies, 1):
                    report_lines.append(f"### 异常 {i}: {anomaly['type']}")
                    report_lines.append(f"")
                    report_lines.append(f"**严重程度**: {anomaly['severity']}/10")
                    report_lines.append(f"**描述**: {anomaly['description']}")
                    report_lines.append(f"")

            # 建议
            recommendations = self._generate_recommendations(comparison)
            if recommendations:
                report_lines.append(f"## 管理建议")
                report_lines.append(f"")
                for i, rec in enumerate(recommendations, 1):
                    report_lines.append(f"{i}. {rec}")
                report_lines.append(f"")

            # 报告结尾
            report_lines.append(f"---")
            report_lines.append(f"*报告由AI客服系统自动生成*")

            return "\n".join(report_lines)

        except Exception as e:
            print(f"生成对比分析报告失败: {e}")
            return f"# 报告生成失败\n\n错误信息: {str(e)}"

    def generate_comparison_excel(self, comparison: Dict) -> str:
        """
        生成对比分析Excel数据（CSV格式）

        Args:
            comparison: 对比分析数据

        Returns:
            str: CSV格式的数据内容
        """
        try:
            csv_lines = []

            # CSV标题行
            csv_lines.append("产品名称,分类,存储区域,之前数量,当前数量,变化量,变化百分比,状态")

            # 数据行
            for change in comparison['changes']:
                status_text = {
                    'increased': '库存增加',
                    'decreased': '库存减少',
                    'new': '新增产品',
                    'removed': '移除产品'
                }.get(change['status'], change['status'])

                change_percent = change.get('change_percentage', 0)

                csv_lines.append(f'"{change["product_name"]}","{change["category"]}","{change.get("storage_area", "")}",{change.get("previous_quantity", 0)},{change.get("current_quantity", 0)},{change["quantity_change"]},{change_percent:.2f}%,"{status_text}"')

            return "\n".join(csv_lines)

        except Exception as e:
            print(f"生成对比分析Excel失败: {e}")
            return f"错误,生成Excel失败: {str(e)}"
