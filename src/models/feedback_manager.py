"""
客户反馈管理模块
"""
import json
import os
import uuid
from datetime import datetime
from typing import List, Dict, Optional, Any


class FeedbackManager:
    def __init__(self):
        self.feedback_file = 'data/feedback.json'
        self._ensure_feedback_file()
    
    def _ensure_feedback_file(self):
        """确保反馈文件存在"""
        if not os.path.exists(self.feedback_file):
            initial_data = {
                "last_updated": datetime.now().isoformat(),
                "feedback_list": []
            }
            os.makedirs(os.path.dirname(self.feedback_file), exist_ok=True)
            with open(self.feedback_file, 'w', encoding='utf-8') as f:
                json.dump(initial_data, f, ensure_ascii=False, indent=2)
    
    def _load_feedback_data(self) -> Dict:
        """加载反馈数据"""
        try:
            with open(self.feedback_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"加载反馈数据失败: {e}")
            return {"last_updated": datetime.now().isoformat(), "feedback_list": []}
    
    def _save_feedback_data(self, feedback_data: Dict):
        """保存反馈数据"""
        try:
            feedback_data["last_updated"] = datetime.now().isoformat()
            with open(self.feedback_file, 'w', encoding='utf-8') as f:
                json.dump(feedback_data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"保存反馈数据失败: {e}")
    
    def add_feedback(self, feedback_data: Dict) -> Optional[str]:
        """添加新的客户反馈"""
        try:
            data = self._load_feedback_data()
            
            # 生成唯一的反馈ID
            feedback_id = str(uuid.uuid4())
            
            # 创建反馈记录
            feedback_record = {
                "feedback_id": feedback_id,
                "product_name": feedback_data["product_name"],
                "product_image": feedback_data.get("product_image", ""),
                "customer_wechat_name": feedback_data["customer_wechat_name"],
                "customer_group_number": feedback_data["customer_group_number"],
                "payment_status": feedback_data["payment_status"],  # 已付款/未付款
                "feedback_type": feedback_data["feedback_type"],  # positive/negative
                "feedback_content": feedback_data["feedback_content"],
                "customer_images": feedback_data.get("customer_images", []),  # 客户上传的图片列表
                "feedback_time": datetime.now().isoformat(),
                "processing_status": "待处理",  # 待处理/处理中/已解决
                "processor": "",  # 处理人员
                "processing_notes": "",  # 处理备注
                "processing_time": "",  # 处理时间
                "resolution_details": "",  # 解决方案详情
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat()
            }
            
            # 添加到反馈列表
            data["feedback_list"].append(feedback_record)
            
            # 保存数据
            self._save_feedback_data(data)
            
            return feedback_id
            
        except Exception as e:
            print(f"添加反馈失败: {e}")
            return None
    
    def get_all_feedback(self, status_filter: str = None, type_filter: str = None) -> List[Dict]:
        """获取所有反馈，支持状态和类型过滤"""
        data = self._load_feedback_data()
        feedback_list = data["feedback_list"]
        
        # 应用过滤器
        if status_filter:
            feedback_list = [f for f in feedback_list if f["processing_status"] == status_filter]
        
        if type_filter:
            feedback_list = [f for f in feedback_list if f["feedback_type"] == type_filter]
        
        # 按时间倒序排列
        feedback_list.sort(key=lambda x: x["feedback_time"], reverse=True)
        
        return feedback_list
    
    def get_feedback_by_id(self, feedback_id: str) -> Optional[Dict]:
        """根据ID获取反馈详情"""
        data = self._load_feedback_data()
        
        for feedback in data["feedback_list"]:
            if feedback["feedback_id"] == feedback_id:
                return feedback
        
        return None
    
    def update_feedback_status(self, feedback_id: str, status: str, processor: str, notes: str = "") -> bool:
        """更新反馈处理状态"""
        try:
            data = self._load_feedback_data()
            
            for feedback in data["feedback_list"]:
                if feedback["feedback_id"] == feedback_id:
                    feedback["processing_status"] = status
                    feedback["processor"] = processor
                    feedback["processing_notes"] = notes
                    feedback["processing_time"] = datetime.now().isoformat()
                    feedback["updated_at"] = datetime.now().isoformat()
                    
                    # 保存数据
                    self._save_feedback_data(data)
                    return True
            
            return False
            
        except Exception as e:
            print(f"更新反馈状态失败: {e}")
            return False
    
    def add_resolution_details(self, feedback_id: str, resolution_details: str, processor: str) -> bool:
        """添加解决方案详情"""
        try:
            data = self._load_feedback_data()
            
            for feedback in data["feedback_list"]:
                if feedback["feedback_id"] == feedback_id:
                    feedback["resolution_details"] = resolution_details
                    feedback["processor"] = processor
                    feedback["processing_status"] = "已解决"
                    feedback["processing_time"] = datetime.now().isoformat()
                    feedback["updated_at"] = datetime.now().isoformat()
                    
                    # 保存数据
                    self._save_feedback_data(data)
                    return True
            
            return False
            
        except Exception as e:
            print(f"添加解决方案失败: {e}")
            return False
    
    def delete_feedback(self, feedback_id: str) -> bool:
        """删除反馈记录"""
        try:
            data = self._load_feedback_data()
            
            original_length = len(data["feedback_list"])
            data["feedback_list"] = [f for f in data["feedback_list"] if f["feedback_id"] != feedback_id]
            
            if len(data["feedback_list"]) < original_length:
                self._save_feedback_data(data)
                return True
            
            return False
            
        except Exception as e:
            print(f"删除反馈失败: {e}")
            return False
    
    def get_feedback_statistics(self) -> Dict:
        """获取反馈统计信息"""
        data = self._load_feedback_data()
        feedback_list = data["feedback_list"]
        
        total_feedback = len(feedback_list)
        positive_feedback = len([f for f in feedback_list if f["feedback_type"] == "positive"])
        negative_feedback = len([f for f in feedback_list if f["feedback_type"] == "negative"])
        
        pending_feedback = len([f for f in feedback_list if f["processing_status"] == "待处理"])
        processing_feedback = len([f for f in feedback_list if f["processing_status"] == "处理中"])
        resolved_feedback = len([f for f in feedback_list if f["processing_status"] == "已解决"])
        
        # 按产品统计反馈
        product_feedback = {}
        for feedback in feedback_list:
            product_name = feedback["product_name"]
            if product_name not in product_feedback:
                product_feedback[product_name] = {"positive": 0, "negative": 0, "total": 0}
            
            product_feedback[product_name][feedback["feedback_type"]] += 1
            product_feedback[product_name]["total"] += 1
        
        # 按付款状态统计
        paid_feedback = len([f for f in feedback_list if f["payment_status"] == "已付款"])
        unpaid_feedback = len([f for f in feedback_list if f["payment_status"] == "未付款"])
        
        return {
            "total_feedback": total_feedback,
            "positive_feedback": positive_feedback,
            "negative_feedback": negative_feedback,
            "pending_feedback": pending_feedback,
            "processing_feedback": processing_feedback,
            "resolved_feedback": resolved_feedback,
            "paid_feedback": paid_feedback,
            "unpaid_feedback": unpaid_feedback,
            "product_feedback": product_feedback,
            "last_updated": data["last_updated"]
        }
    
    def search_feedback(self, keyword: str) -> List[Dict]:
        """搜索反馈记录"""
        data = self._load_feedback_data()
        feedback_list = data["feedback_list"]
        
        keyword = keyword.lower()
        results = []
        
        for feedback in feedback_list:
            # 在多个字段中搜索关键词
            search_fields = [
                feedback["product_name"],
                feedback["customer_wechat_name"],
                feedback["customer_group_number"],
                feedback["feedback_content"],
                feedback["processing_notes"],
                feedback["resolution_details"]
            ]
            
            if any(keyword in str(field).lower() for field in search_fields):
                results.append(feedback)
        
        # 按时间倒序排列
        results.sort(key=lambda x: x["feedback_time"], reverse=True)
        
        return results
    
    def get_recent_feedback(self, days: int = 7) -> List[Dict]:
        """获取最近几天的反馈"""
        from datetime import timedelta
        
        data = self._load_feedback_data()
        feedback_list = data["feedback_list"]
        
        cutoff_date = datetime.now() - timedelta(days=days)
        recent_feedback = []
        
        for feedback in feedback_list:
            feedback_time = datetime.fromisoformat(feedback["feedback_time"])
            if feedback_time >= cutoff_date:
                recent_feedback.append(feedback)
        
        # 按时间倒序排列
        recent_feedback.sort(key=lambda x: x["feedback_time"], reverse=True)
        
        return recent_feedback
