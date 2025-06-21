"""
知识检索模块 - 智能检索产品和政策信息
"""
import jieba
import re
from typing import List, Dict, Any, Tuple
from .data_processor import DataProcessor
from .llm_client import LLMClient
from .pickup_location_manager import PickupLocationManager


class KnowledgeRetriever:
    def __init__(self):
        self.data_processor = DataProcessor()
        self.llm_client = LLMClient()
        self.pickup_location_manager = PickupLocationManager()
        
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

            # 如果没有找到相关信息，使用本地回答
            if not retrieval_result['has_product_info'] and not retrieval_result['has_policy_info']:
                return self._handle_no_information(question, retrieval_result['intent'])

            # 尝试使用本地知识直接回答
            local_answer = self._try_local_answer(question, retrieval_result)
            if local_answer:
                return local_answer

            # 调用LLM生成回答
            try:
                response = self.llm_client.chat(question, context_info, conversation_history)
                return response
            except Exception as llm_error:
                print(f"LLM调用失败，使用本地回答: {llm_error}")
                return self._generate_local_answer(question, retrieval_result)

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

    def _try_local_answer(self, question: str, retrieval_result: Dict) -> str:
        """尝试使用本地知识直接回答简单问题"""
        question_lower = question.lower()

        # 处理分类查询问题
        if any(keyword in question_lower for keyword in ['有什么', '什么', '哪些']):
            # 获取所有分类，并去除空格
            all_categories = self.data_processor.get_all_categories()
            category_map = {cat.strip(): cat for cat in all_categories}

            # 水果查询
            if '水果' in question_lower:
                # 查找包含"水果"的分类
                fruit_category = None
                for clean_cat, original_cat in category_map.items():
                    if '水果' in clean_cat:
                        fruit_category = original_cat
                        break

                if fruit_category:
                    fruits = self.data_processor.get_products_by_category(fruit_category)
                    if fruits:
                        answer = "🍎 **我们的时令水果：**\n\n"
                        for i, fruit in enumerate(fruits[:8], 1):  # 显示前8个水果
                            answer += f"{i}. **{fruit['name']}** - ${fruit['price']}/{fruit['unit']}"
                            if fruit['taste']:
                                answer += f" ({fruit['taste']})"
                            answer += "\n"
                        answer += "\n💡 如需了解具体水果的详细信息，请告诉我您感兴趣的水果名称！"
                        return answer

            # 蔬菜查询
            if '蔬菜' in question_lower:
                # 查找包含"蔬菜"的分类
                vegetable_category = None
                for clean_cat, original_cat in category_map.items():
                    if '蔬菜' in clean_cat:
                        vegetable_category = original_cat
                        break

                if vegetable_category:
                    vegetables = self.data_processor.get_products_by_category(vegetable_category)
                    if vegetables:
                        answer = "🥬 **我们的新鲜蔬菜：**\n\n"
                        for i, veg in enumerate(vegetables[:8], 1):  # 显示前8个蔬菜
                            answer += f"{i}. **{veg['name']}** - ${veg['price']}/{veg['unit']}"
                            if veg['taste']:
                                answer += f" ({veg['taste']})"
                            answer += "\n"
                        answer += "\n💡 如需了解具体蔬菜的详细信息，请告诉我您感兴趣的蔬菜名称！"
                        return answer

            # 禽类查询
            if any(keyword in question_lower for keyword in ['鸡', '禽类', '肉类']):
                # 查找包含"禽类"的分类
                poultry_category = None
                for clean_cat, original_cat in category_map.items():
                    if '禽类' in clean_cat:
                        poultry_category = original_cat
                        break

                if poultry_category:
                    poultry = self.data_processor.get_products_by_category(poultry_category)
                    if poultry:
                        answer = "🐔 **我们的禽类产品：**\n\n"
                        for i, item in enumerate(poultry[:5], 1):  # 显示前5个禽类产品
                            answer += f"{i}. **{item['name']}** - ${item['price']}/{item['unit']}"
                            if item['taste']:
                                answer += f" ({item['taste']})"
                            answer += "\n"
                        answer += "\n💡 如需了解具体产品的详细信息，请告诉我您感兴趣的产品名称！"
                        return answer

        # 处理取货地点问题
        if any(keyword in question_lower for keyword in ['取货', '地点', '地址', '在哪', '位置']):
            return self._generate_pickup_locations_info()

        # 处理配送问题
        if any(keyword in question_lower for keyword in ['配送', '送货', '运费', '快递']):
            return """🚚 **配送服务信息**

• **配送时间**：每周三截单，周五送货
• **起送标准**：三只鸡或同等金额起可送到家
• **配送费用**：波士顿周边（Quincy、Waltham、Newton）运费$5/次
• **免费配送**：10只鸡以上免费配送
• **配送范围**：波士顿周边地区

特殊情况会另行通知，请关注群内消息。"""

        # 处理付款问题
        if any(keyword in question_lower for keyword in ['付款', '支付', '付费', 'venmo', '现金']):
            return """💳 **付款方式**

我们接受以下付款方式：

• **Venmo付款**：账号 Sabrina0861
• **现金付款**：指定地点现金付款

请在下单后及时付款，以确保您的订单能够及时处理。"""

        return None

    def _generate_pickup_locations_info(self) -> str:
        """
        动态生成取货点信息

        Returns:
            str: 格式化的取货点信息
        """
        try:
            # 获取所有活跃的取货点
            locations = self.pickup_location_manager.get_all_locations(include_inactive=False)

            if not locations:
                return "抱歉，暂时没有可用的取货点信息。请联系客服获取最新信息。"

            # 构建取货点信息
            answer = "取货地点信息\n\n"

            for location in locations:
                answer += f"**{location['location_name']}：**\n"
                answer += f"地址: {location['address']}\n"

                if location.get('phone'):
                    answer += f"电话: {location['phone']}\n"

                if location.get('contact_person'):
                    answer += f"联系人: {location['contact_person']}\n"

                if location.get('business_hours') and location['business_hours'] != "请关注群内通知":
                    answer += f"营业时间: {location['business_hours']}\n"

                if location.get('description'):
                    answer += f"说明: {location['description']}\n"

                answer += "\n"

            answer += "请根据您的方便选择合适的取货地点。如有疑问，请联系客服确认。"
            return answer

        except Exception as e:
            print(f"生成取货点信息失败: {e}")
            # 返回备用信息
            return """📍 **取货地点信息**

**Malden取货点：**
📍 273 Salem St, Malden, MA
📞 781-480-4722

**Chinatown取货点：**
📍 25 Chauncy St, Boston, MA 02110
📞 718-578-3389

**Quincy取货点：**
📍 具体地址请联系客服确认

请根据您的方便选择合适的取货地点。如有疑问，请联系客服确认。"""

    def _generate_local_answer(self, question: str, retrieval_result: Dict) -> str:
        """生成本地回答作为LLM的备用方案"""
        if retrieval_result['has_product_info']:
            products = retrieval_result['products'][:3]
            answer = "🍎 **找到以下相关产品：**\n\n"

            for i, product in enumerate(products, 1):
                answer += f"{i}. **{product['name']}**\n"
                answer += f"   💰 价格：${product['price']} / {product['unit']}\n"
                answer += f"   📦 规格：{product['specification']}\n"
                if product['origin']:
                    answer += f"   🌍 产地：{product['origin']}\n"
                if product['taste']:
                    answer += f"   😋 口感：{product['taste']}\n"
                answer += "\n"

            return answer

        if retrieval_result['has_policy_info']:
            policies = retrieval_result['policies'][:2]
            answer = "📋 **相关政策信息：**\n\n"

            section_names = {
                'delivery': '配送服务',
                'payment': '付款方式',
                'pickup': '取货信息',
                'after_sale': '售后服务',
                'product_quality': '产品质量'
            }

            for policy in policies:
                section_name = section_names.get(policy['section'], policy['section'])
                answer += f"**{section_name}：**\n"

                content = policy['content']
                if isinstance(content, list):
                    for item in content:
                        answer += f"• {item}\n"
                else:
                    answer += f"{content}\n"
                answer += "\n"

            return answer

        return "抱歉，我暂时无法为您提供准确的回答。请稍后再试或联系人工客服。"
    
    def get_product_categories(self) -> List[str]:
        """获取产品分类"""
        return self.data_processor.get_all_categories()
    
    def get_products_by_category(self, category: str) -> List[Dict]:
        """根据分类获取产品"""
        return self.data_processor.get_products_by_category(category)
    
    def get_quick_answers(self) -> Dict[str, str]:
        """获取常见问题快速回答"""
        # 动态生成取货地点信息
        pickup_locations_text = self._get_pickup_locations_text()

        return {
            "配送时间": "每周三截单，周五送货。特殊情况会另行通知。",
            "起送标准": "三只鸡或同等金额起可送到家，不同种类可累计。",
            "配送费用": "波士顿周边（Quincy、Waltham、Newton）运费$5/次，10只鸡以上免费配送。",
            "付款方式": "接受Venmo付款（Sabrina0861）和指定地点现金付款。",
            "取货地点": pickup_locations_text,
            "质量保证": "不好不拼，不新鲜不拼，不好吃不拼。质量问题24小时内反馈可退换。"
        }

    def _get_pickup_locations_text(self) -> str:
        """
        获取取货地点的简短文本描述

        Returns:
            str: 取货地点文本
        """
        try:
            locations = self.pickup_location_manager.get_all_locations(include_inactive=False)

            if not locations:
                return "暂无可用取货点，请联系客服确认"

            location_texts = []
            for location in locations:
                text = f"{location['location_name']}：{location['address']}"
                location_texts.append(text)

            return "；".join(location_texts)

        except Exception as e:
            print(f"获取取货地点文本失败: {e}")
            return "Malden取货点：273 Salem St, Malden, MA；Chinatown取货点：25 Chauncy St, Boston, MA 02110；Quincy取货点：具体地址请联系客服"


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
