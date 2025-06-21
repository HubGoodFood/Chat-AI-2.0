# -*- coding: utf-8 -*-
"""
操作日志记录模块
"""
import json
import os
from datetime import datetime
from typing import Dict, List, Optional
from ..utils.logger_config import get_logger

# 初始化日志记录器
logger = get_logger('operation_logger')


class OperationLogger:
    def __init__(self):
        self.log_file = 'data/operation_logs.json'
        self._ensure_log_file()
    
    def _ensure_log_file(self):
        """确保日志文件存在"""
        if not os.path.exists(self.log_file):
            initial_data = {
                "created_at": datetime.now().isoformat(),
                "logs": []
            }
            os.makedirs(os.path.dirname(self.log_file), exist_ok=True)
            with open(self.log_file, 'w', encoding='utf-8') as f:
                json.dump(initial_data, f, ensure_ascii=False, indent=2)
    
    def _load_logs(self) -> Dict:
        """加载日志数据"""
        try:
            with open(self.log_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"加载日志数据失败: {e}")
            return {"created_at": datetime.now().isoformat(), "logs": []}
    
    def _save_logs(self, log_data: Dict):
        """保存日志数据"""
        try:
            with open(self.log_file, 'w', encoding='utf-8') as f:
                json.dump(log_data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"保存日志数据失败: {e}")
    
    def log_operation(self, operator: str, operation_type: str, target_type: str, 
                     target_id: str, details: Dict = None, result: str = "success"):
        """记录操作日志"""
        try:
            log_data = self._load_logs()
            
            log_entry = {
                "log_id": f"{datetime.now().strftime('%Y%m%d%H%M%S')}_{len(log_data['logs']) + 1}",
                "timestamp": datetime.now().isoformat(),
                "operator": operator,
                "operation_type": operation_type,  # create, update, delete, view, etc.
                "target_type": target_type,        # product, feedback, inventory, etc.
                "target_id": target_id,
                "details": details or {},
                "result": result,                  # success, failed, error
                "ip_address": "",                  # 可以后续添加
                "user_agent": ""                   # 可以后续添加
            }
            
            log_data["logs"].append(log_entry)
            
            # 保持最近1000条日志
            if len(log_data["logs"]) > 1000:
                log_data["logs"] = log_data["logs"][-1000:]
            
            self._save_logs(log_data)
            
        except Exception as e:
            logger.error(f"记录操作日志失败: {e}")
    
    def get_logs(self, limit: int = 100, operator: str = None, 
                operation_type: str = None, target_type: str = None) -> List[Dict]:
        """获取操作日志"""
        try:
            log_data = self._load_logs()
            logs = log_data["logs"]
            
            # 应用过滤器
            if operator:
                logs = [log for log in logs if log["operator"] == operator]
            
            if operation_type:
                logs = [log for log in logs if log["operation_type"] == operation_type]
            
            if target_type:
                logs = [log for log in logs if log["target_type"] == target_type]
            
            # 按时间倒序排列并限制数量
            logs.sort(key=lambda x: x["timestamp"], reverse=True)
            return logs[:limit]
            
        except Exception as e:
            logger.error(f"获取操作日志失败: {e}")
            return []
    
    def get_operation_statistics(self, days: int = 7) -> Dict:
        """获取操作统计"""
        try:
            from datetime import timedelta
            
            log_data = self._load_logs()
            logs = log_data["logs"]
            
            cutoff_date = datetime.now() - timedelta(days=days)
            recent_logs = []
            
            for log in logs:
                log_time = datetime.fromisoformat(log["timestamp"])
                if log_time >= cutoff_date:
                    recent_logs.append(log)
            
            # 统计各种操作
            stats = {
                "total_operations": len(recent_logs),
                "by_operator": {},
                "by_operation_type": {},
                "by_target_type": {},
                "by_result": {},
                "by_date": {}
            }
            
            for log in recent_logs:
                # 按操作员统计
                operator = log["operator"]
                stats["by_operator"][operator] = stats["by_operator"].get(operator, 0) + 1
                
                # 按操作类型统计
                op_type = log["operation_type"]
                stats["by_operation_type"][op_type] = stats["by_operation_type"].get(op_type, 0) + 1
                
                # 按目标类型统计
                target_type = log["target_type"]
                stats["by_target_type"][target_type] = stats["by_target_type"].get(target_type, 0) + 1
                
                # 按结果统计
                result = log["result"]
                stats["by_result"][result] = stats["by_result"].get(result, 0) + 1
                
                # 按日期统计
                date_key = log["timestamp"][:10]  # YYYY-MM-DD
                stats["by_date"][date_key] = stats["by_date"].get(date_key, 0) + 1
            
            return stats
            
        except Exception as e:
            logger.error(f"获取操作统计失败: {e}")
            return {}
    
    def clear_old_logs(self, days: int = 30):
        """清理旧日志"""
        try:
            from datetime import timedelta
            
            log_data = self._load_logs()
            logs = log_data["logs"]
            
            cutoff_date = datetime.now() - timedelta(days=days)
            new_logs = []
            
            for log in logs:
                log_time = datetime.fromisoformat(log["timestamp"])
                if log_time >= cutoff_date:
                    new_logs.append(log)
            
            log_data["logs"] = new_logs
            self._save_logs(log_data)
            
            return len(logs) - len(new_logs)  # 返回清理的日志数量
            
        except Exception as e:
            logger.error(f"清理旧日志失败: {e}")
            return 0
    
    def export_logs(self, start_date: str = None, end_date: str = None) -> List[Dict]:
        """导出日志数据"""
        try:
            log_data = self._load_logs()
            logs = log_data["logs"]
            
            if start_date:
                start_dt = datetime.fromisoformat(start_date)
                logs = [log for log in logs if datetime.fromisoformat(log["timestamp"]) >= start_dt]
            
            if end_date:
                end_dt = datetime.fromisoformat(end_date)
                logs = [log for log in logs if datetime.fromisoformat(log["timestamp"]) <= end_dt]
            
            return logs
            
        except Exception as e:
            logger.error(f"导出日志失败: {e}")
            return []


# 全局日志记录器实例
operation_logger = OperationLogger()


def log_admin_operation(operator: str, operation_type: str, target_type: str, 
                       target_id: str, details: Dict = None, result: str = "success"):
    """便捷的日志记录函数"""
    operation_logger.log_operation(operator, operation_type, target_type, target_id, details, result)
