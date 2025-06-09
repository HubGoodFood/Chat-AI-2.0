"""
知识检索模块 - 智能检索产品和政策信息
"""
import jieba
import re
from typing import List, Dict, Any, Tuple
from .data_processor import DataProcessor
from .llm_client import LLMClient


class KnowledgeRetriever:
    def __init__(self):
        self.data_processor = DataProcessor()
        self.llm_client = LLMClient()
        
        # 问题类型关键词映射
        self.question_patterns = {
            'price': ['价格', '多少钱', '费用', '成本', '贵', '便宜', '价位'],
            'origin': ['产地', '哪里产', '来源', '出产', '原产地'],
            'nutrition': ['营养', '维生素', '蛋白质', '好处', '功效', '健康'],
            'taste': ['口感', '味道', '好吃', '甜', '酸', '脆', '嫩'],
            'storage': ['保存', '储存', '放置', '保鲜', '冷藏'],
            'cooking': ['做法', '烹饪', '怎么做', '料理', '制作'],
            'delivery': ['配送', '送货', '运费', '快递', '物流'],
            'payment': ['付款', '支付', '付费', 'venmo', '现金'],
            'pickup': ['取货', '自取', '提货', '领取'],
            'return': ['退货', '换货', '退款', '质量问题', '不满意'],
            'policy': ['政策', '规定', '规则', '制度', '条款']
        }
        
    def initialize(self):
        """初始化数据"""
        self.data_processor.load_data()
        
    def analyze_question_intent(self, question: str) -> Tuple[str, List[str]]:
        """分析问题意图"""
        question_lower = question.lower()
        detected_intents = []
        keywords = jieba.lcut(question)
        
        for intent, patterns in self.question_patterns.items():
            for pattern in patterns:
                if pattern in question_lower:
                    detected_intents.append(intent)
                    break
        
        # 如果没有检测到特定意图，默认为一般查询
        if not detected_intents:
            detected_intents = ['general']
            
        return detected_intents[0] if detected_intents else 'general', keywords
    
    def extract_product_names(self, question: str) -> List[str]:
        """从问题中提取可能的产品名称"""
        # 获取所有产品名称
        if self.data_processor.products_df is None:
            return []
            
        product_names = self.data_processor.products_df['ProductName'].tolist()
        found_products = []
        
        for product_name in product_names:
            # 检查产品名称是否在问题中
            if any(word in question for word in jieba.lcut(product_name)):
                found_products.append(product_name)
        
        return found_products
    
    def retrieve_information(self, question: str) -> Dict[str, Any]:
        """检索相关信息"""
        intent, keywords = self.analyze_question_intent(question)
        
        # 检索产品信息
        product_results = self.data_processor.search_products(question)
        
        # 检索政策信息
        policy_results = self.data_processor.search_policies(question)
        
        # 提取具体产品名称
        mentioned_products = self.extract_product_names(question)
        
        return {
            'intent': intent,
            'keywords': keywords,
            'products': product_results,
            'policies': policy_results,
            'mentioned_products': mentioned_products,
            'has_product_info': len(product_results) > 0,
            'has_policy_info': len(policy_results) > 0
        }
    
    def generate_context_info(self, retrieval_result: Dict[str, Any]) -> str:
        """生成上下文信息"""
        context_parts = []
        
        # 添加产品信息
        if retrieval_result['has_product_info']:
            product_info = self.llm_client.format_product_info(retrieval_result['products'])
            context_parts.append(product_info)
        
        # 添加政策信息
        if retrieval_result['has_policy_info']:
            policy_info = self.llm_client.format_policy_info(retrieval_result['policies'])
            context_parts.append(policy_info)
        
        return "\n".join(context_parts)
    
    def answer_question(self, question: str, conversation_history: List[Dict] = None) -> str:
        """回答用户问题"""
        try:
            # 检索相关信息
            retrieval_result = self.retrieve_information(question)
            
            # 生成上下文信息
            context_info = self.generate_context_info(retrieval_result)
            
            # 如果没有找到相关信息
            if not retrieval_result['has_product_info'] and not retrieval_result['has_policy_info']:
                return self._handle_no_information(question, retrieval_result['intent'])
            
            # 调用LLM生成回答
            response = self.llm_client.chat(question, context_info, conversation_history)
            
            return response
            
        except Exception as e:
            print(f"回答问题时出错: {e}")
            return self.llm_client.generate_error_message("general")
    
    def _handle_no_information(self, question: str, intent: str) -> str:
        """处理没有找到信息的情况"""
        # 根据意图提供不同的建议
        suggestions = {
            'price': "您可以浏览我们的产品目录查看价格，或者告诉我具体的产品名称。",
            'delivery': "关于配送政策，我们每周三截单，周五送货。起送标准是三只鸡或同等金额。",
            'payment': "我们接受Venmo付款（账号：Sabrina0861）和指定地点现金付款。",
            'pickup': "我们有Malden和Chinatown两个取货点，具体地址我可以为您提供。",
            'general': "请告诉我更具体的问题，比如想了解哪个产品或哪方面的政策。"
        }
        
        base_message = "抱歉，我没有找到相关信息。"
        suggestion = suggestions.get(intent, suggestions['general'])
        
        return f"{base_message}{suggestion}\n\n您也可以：\n• 查看产品分类：{', '.join(self.data_processor.get_all_categories())}\n• 联系人工客服获取更多帮助"
    
    def get_product_categories(self) -> List[str]:
        """获取产品分类"""
        return self.data_processor.get_all_categories()
    
    def get_products_by_category(self, category: str) -> List[Dict]:
        """根据分类获取产品"""
        return self.data_processor.get_products_by_category(category)
    
    def get_quick_answers(self) -> Dict[str, str]:
        """获取常见问题快速回答"""
        return {
            "配送时间": "每周三截单，周五送货。特殊情况会另行通知。",
            "起送标准": "三只鸡或同等金额起可送到家，不同种类可累计。",
            "配送费用": "波士顿周边（Quincy、Waltham、Newton）运费$5/次，10只鸡以上免费配送。",
            "付款方式": "接受Venmo付款（Sabrina0861）和指定地点现金付款。",
            "取货地点": "Malden取货点：273 Salem St, Malden, MA；Chinatown取货点：25 Chauncy St, Boston, MA 02110",
            "质量保证": "不好不拼，不新鲜不拼，不好吃不拼。质量问题24小时内反馈可退换。"
        }


# 测试代码
if __name__ == "__main__":
    retriever = KnowledgeRetriever()
    retriever.initialize()
    
    # 测试问题
    test_questions = [
        "苹果多少钱？",
        "配送费用是多少？",
        "怎么付款？",
        "有什么蔬菜？",
        "质量有问题怎么办？"
    ]
    
    print("=== 知识检索测试 ===")
    for question in test_questions:
        print(f"\n问题: {question}")
        answer = retriever.answer_question(question)
        print(f"回答: {answer}")
        print("-" * 50)
