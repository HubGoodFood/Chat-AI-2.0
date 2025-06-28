# -*- coding: utf-8 -*-
"""
知识检索模块 - 智能检索产品和政策信息
"""
import jieba
import re
import time
from typing import List, Dict, Any, Tuple
from .data_processor import DataProcessor
from .database_data_processor import DatabaseDataProcessor
from .llm_client import LLMClient
from .pickup_location_manager import PickupLocationManager
from .operation_logger import operation_logger
# 延迟导入以避免循环导入
# from ..services.intelligent_cache_manager import intelligent_cache_manager
# from ..services.performance_collector import performance_collector
# from ..services.query_performance_analyzer import query_performance_analyzer


class KnowledgeRetriever:
    """
    知识检索器类 - 智能客服系统的核心组件

    负责处理用户问题的意图分析、信息检索和智能回答生成。
    集成了产品数据处理、政策查询、LLM调用等功能，为用户提供准确的客服回答。

    主要功能：
    - 问题意图分析：识别用户询问的类型（价格、产地、配送等）
    - 信息检索：从产品数据和政策数据中检索相关信息
    - 智能回答：结合本地知识和LLM生成准确回答
    - 上下文管理：维护对话历史和上下文信息

    Attributes:
        data_processor (DataProcessor): 数据处理器，负责产品和政策数据的加载和搜索
        llm_client (LLMClient): LLM客户端，负责与AI模型的交互
        pickup_location_manager (PickupLocationManager): 取货点管理器，动态管理取货地点信息
        question_patterns (Dict): 问题类型关键词映射表，用于意图识别
    """

    def __init__(self, use_database_processor: bool = True):
        """
        初始化知识检索器

        创建必要的组件实例并设置问题类型关键词映射表。
        这些关键词用于分析用户问题的意图，帮助系统提供更准确的回答。

        Args:
            use_database_processor (bool): 是否使用数据库化数据处理器（默认True，性能更好）
        """
        # 🚀 根据配置选择数据处理器（数据库查询优化）
        if use_database_processor:
            try:
                self.data_processor = DatabaseDataProcessor()
                self.processor_type = "database"
                print("[OK] 使用数据库化数据处理器（高性能模式）")
            except Exception as e:
                print(f"[WARN] 数据库处理器初始化失败，降级到文件处理器: {e}")
                self.data_processor = DataProcessor()
                self.processor_type = "file"
        else:
            self.data_processor = DataProcessor()
            self.processor_type = "file"
            print("使用文件数据处理器（兼容模式）")

        # 初始化其他核心组件
        self.llm_client = LLMClient()  # LLM客户端：与AI模型交互
        self.pickup_location_manager = PickupLocationManager()  # 取货点管理器：动态管理取货地点

        # 问题类型关键词映射表
        # 用于识别用户问题的意图类型，每个类型包含相关的关键词列表
        self.question_patterns = {
            'price': ['价格', '多少钱', '费用', '成本', '贵', '便宜', '价位'],  # 价格相关询问
            'origin': ['产地', '哪里产', '来源', '出产', '原产地'],  # 产地相关询问
            'nutrition': ['营养', '维生素', '蛋白质', '好处', '功效', '健康'],  # 营养价值询问
            'taste': ['口感', '味道', '好吃', '甜', '酸', '脆', '嫩'],  # 口感味道询问
            'storage': ['保存', '储存', '放置', '保鲜', '冷藏'],  # 储存方法询问
            'cooking': ['做法', '烹饪', '怎么做', '料理', '制作'],  # 烹饪方法询问
            'delivery': ['配送', '送货', '运费', '快递', '物流'],  # 配送服务询问
            'payment': ['付款', '支付', '付费', 'venmo', '现金'],  # 付款方式询问
            'pickup': ['取货', '自取', '提货', '领取'],  # 取货相关询问
            'return': ['退货', '换货', '退款', '质量问题', '不满意'],  # 退换货询问
            'policy': ['政策', '规定', '规则', '制度', '条款']  # 政策规定询问
        }
        
    def initialize(self):
        """
        初始化知识检索器的数据

        加载产品数据和政策数据，为后续的信息检索做准备。
        这个方法应该在使用知识检索器之前调用。

        Raises:
            Exception: 如果数据加载失败
        """
        self.data_processor.load_data()

    def analyze_question_intent(self, question: str) -> Tuple[str, List[str]]:
        """
        分析用户问题的意图类型

        通过关键词匹配的方式识别用户问题的意图类型，帮助系统提供更准确的回答。
        使用jieba分词工具对问题进行分词，然后与预定义的关键词模式进行匹配。

        Args:
            question (str): 用户输入的问题文本

        Returns:
            Tuple[str, List[str]]: 包含两个元素的元组
                - str: 检测到的意图类型（如'price', 'delivery', 'general'等）
                - List[str]: 问题的分词结果列表

        Example:
            >>> retriever = KnowledgeRetriever()
            >>> intent, keywords = retriever.analyze_question_intent("苹果多少钱？")
            >>> print(intent)  # 'price'
            >>> print(keywords)  # ['苹果', '多少钱', '？']
        """
        question_lower = question.lower()  # 转换为小写以便匹配
        detected_intents = []  # 存储检测到的意图类型
        keywords = jieba.lcut(question)  # 使用jieba进行中文分词

        # 遍历所有意图类型和对应的关键词模式
        for intent, patterns in self.question_patterns.items():
            for pattern in patterns:
                if pattern in question_lower:
                    detected_intents.append(intent)
                    break  # 找到匹配的关键词后跳出内层循环

        # 如果没有检测到特定意图，默认为一般查询
        if not detected_intents:
            detected_intents = ['general']

        # 返回第一个检测到的意图类型和分词结果
        return detected_intents[0] if detected_intents else 'general', keywords
    
    def extract_product_names(self, question: str) -> List[str]:
        """
        从用户问题中提取可能提到的产品名称

        通过分词匹配的方式识别用户问题中提到的具体产品。
        这个方法对于提供精准的产品信息回答非常重要。

        Args:
            question (str): 用户输入的问题文本

        Returns:
            List[str]: 在问题中找到的产品名称列表

        Example:
            >>> retriever = KnowledgeRetriever()
            >>> products = retriever.extract_product_names("苹果和香蕉的价格是多少？")
            >>> print(products)  # ['苹果', '香蕉']
        """
        # 🚀 兼容数据库处理器和文件处理器
        try:
            # 如果是数据库处理器，使用专门的方法获取产品名称
            if hasattr(self.data_processor, 'get_all_product_names'):
                product_names = self.data_processor.get_all_product_names()
            # 如果是文件处理器，使用DataFrame
            elif hasattr(self.data_processor, 'products_df') and self.data_processor.products_df is not None:
                product_names = self.data_processor.products_df['ProductName'].tolist()
            else:
                return []
        except Exception as e:
            operation_logger.warning(f"获取产品名称失败: {e}")
            return []

        found_products = []

        # 遍历所有产品名称，检查是否在问题中被提到
        for product_name in product_names:
            # 对产品名称进行分词，检查是否有词汇在问题中出现
            if any(word in question for word in jieba.lcut(product_name)):
                found_products.append(product_name)

        return found_products

    def retrieve_information(self, question: str) -> Dict[str, Any]:
        """
        检索与用户问题相关的所有信息

        这是知识检索的核心方法，整合了意图分析、产品搜索、政策查询等功能。
        返回的信息将用于生成最终的回答。

        Args:
            question (str): 用户输入的问题文本

        Returns:
            Dict[str, Any]: 包含检索结果的字典，包含以下键：
                - intent (str): 问题意图类型
                - keywords (List[str]): 问题关键词列表
                - products (List[Dict]): 相关产品信息列表
                - policies (List[Dict]): 相关政策信息列表
                - mentioned_products (List[str]): 问题中提到的产品名称
                - has_product_info (bool): 是否找到相关产品信息
                - has_policy_info (bool): 是否找到相关政策信息

        Example:
            >>> retriever = KnowledgeRetriever()
            >>> result = retriever.retrieve_information("苹果多少钱？")
            >>> print(result['intent'])  # 'price'
            >>> print(result['has_product_info'])  # True
        """
        # 分析问题意图和关键词
        intent, keywords = self.analyze_question_intent(question)

        # 🚀 从产品数据中检索相关信息（带性能监控）
        try:
            from ..services.query_performance_analyzer import query_performance_analyzer
            with query_performance_analyzer.monitor_query('product_search', f'搜索产品: {question[:30]}...'):
                product_results = self.data_processor.search_products(question)
        except ImportError:
            product_results = self.data_processor.search_products(question)

        # 🚀 从政策数据中检索相关信息（带性能监控）
        try:
            from ..services.query_performance_analyzer import query_performance_analyzer
            with query_performance_analyzer.monitor_query('policy_search', f'搜索政策: {question[:30]}...'):
                policy_results = self.data_processor.search_policies(question)
        except ImportError:
            policy_results = self.data_processor.search_policies(question)

        # 提取问题中明确提到的产品名称
        mentioned_products = self.extract_product_names(question)

        # 构建并返回检索结果
        return {
            'intent': intent,  # 问题意图类型
            'keywords': keywords,  # 分词结果
            'products': product_results,  # 相关产品信息
            'policies': policy_results,  # 相关政策信息
            'mentioned_products': mentioned_products,  # 提到的产品名称
            'has_product_info': len(product_results) > 0,  # 是否有产品信息
            'has_policy_info': len(policy_results) > 0  # 是否有政策信息
        }
    
    def generate_context_info(self, retrieval_result: Dict[str, Any]) -> str:
        """
        根据检索结果生成LLM所需的上下文信息

        将检索到的产品信息和政策信息格式化为LLM可以理解的上下文文本。
        这个上下文将帮助LLM生成更准确和相关的回答。

        Args:
            retrieval_result (Dict[str, Any]): 信息检索结果，包含产品和政策信息

        Returns:
            str: 格式化的上下文信息文本

        Note:
            如果没有找到相关信息，返回空字符串
        """
        context_parts = []

        # 添加产品信息到上下文
        if retrieval_result['has_product_info']:
            product_info = self.llm_client.format_product_info(retrieval_result['products'])
            context_parts.append(product_info)

        # 添加政策信息到上下文
        if retrieval_result['has_policy_info']:
            policy_info = self.llm_client.format_policy_info(retrieval_result['policies'])
            context_parts.append(policy_info)

        return "\n".join(context_parts)

    def answer_question(self, question: str, conversation_history: List[Dict] = None) -> str:
        """
        回答用户问题的主要方法

        这是知识检索器的核心方法，整合了智能缓存、信息检索、本地回答和LLM调用。
        采用多层回答策略：优先使用缓存，然后本地知识，最后调用LLM，确保回答的准确性和响应速度。

        回答策略（已优化）：
        1. 🚀 检查智能缓存（新增）- 大幅提升响应速度
        2. 检索相关信息（产品、政策）
        3. 如果没有找到信息，提供通用建议
        4. 尝试使用本地知识直接回答
        5. 如果本地知识不足，调用LLM生成回答
        6. 🚀 缓存AI响应（新增）- 为后续相似问题提速
        7. 如果LLM调用失败，使用备用本地回答

        Args:
            question (str): 用户输入的问题
            conversation_history (List[Dict], optional): 对话历史记录，用于维护上下文

        Returns:
            str: 生成的回答文本

        Example:
            >>> retriever = KnowledgeRetriever()
            >>> answer = retriever.answer_question("苹果多少钱？")
            >>> print(answer)  # 返回苹果的价格信息（可能来自缓存，响应更快）
        """
        try:
            # 🚀 记录请求开始时间（性能监控）
            start_time = time.time()

            # 🚀 第一步：检查智能缓存（性能优化的关键）
            try:
                from ..services.intelligent_cache_manager import intelligent_cache_manager
                cached_response = intelligent_cache_manager.get_cached_response(question)
                if cached_response:
                    # 🚀 记录缓存命中的性能数据
                    response_time = (time.time() - start_time) * 1000  # 转换为毫秒
                    cache_type = 'exact' if '精确匹配' in str(cached_response) else 'similarity'
                    try:
                        from ..services.performance_collector import performance_collector
                        performance_collector.record_response_time(response_time, True, cache_type)
                    except ImportError:
                        pass

                    print(f"[缓存命中] 问题: {question[:30]}... 响应时间: {response_time:.0f}ms")
                    return cached_response
            except ImportError:
                pass

            # 第二步：检索相关信息
            retrieval_result = self.retrieve_information(question)

            # 第三步：生成LLM所需的上下文信息
            context_info = self.generate_context_info(retrieval_result)

            # 第四步：如果没有找到相关信息，使用预设的处理方式
            if not retrieval_result['has_product_info'] and not retrieval_result['has_policy_info']:
                return self._handle_no_information(question, retrieval_result['intent'])

            # 第五步：尝试使用本地知识直接回答（快速响应）
            local_answer = self._try_local_answer(question, retrieval_result)
            if local_answer:
                # 🚀 记录本地回答的性能数据
                response_time = (time.time() - start_time) * 1000
                try:
                    from ..services.performance_collector import performance_collector
                    performance_collector.record_response_time(response_time, False, None)
                except ImportError:
                    pass

                # 🚀 缓存本地回答
                try:
                    from ..services.intelligent_cache_manager import intelligent_cache_manager
                    intelligent_cache_manager.cache_response(question, local_answer)
                except ImportError:
                    pass
                print(f"[本地回答] 问题: {question[:30]}... 响应时间: {response_time:.0f}ms")
                return local_answer

            # 第六步：调用LLM生成智能回答
            try:
                print(f"[LLM调用] 问题: {question[:30]}...")
                response = self.llm_client.chat(question, context_info, conversation_history)

                # 🚀 记录LLM调用的性能数据
                response_time = (time.time() - start_time) * 1000
                try:
                    from ..services.performance_collector import performance_collector
                    performance_collector.record_response_time(response_time, False, None)
                except ImportError:
                    pass

                # 🚀 缓存LLM响应（关键优化）
                try:
                    from ..services.intelligent_cache_manager import intelligent_cache_manager
                    intelligent_cache_manager.cache_response(question, response)
                except ImportError:
                    pass
                print(f"[LLM响应] 问题: {question[:30]}... 响应时间: {response_time:.0f}ms")

                return response
            except Exception as llm_error:
                # 🚀 记录错误
                response_time = (time.time() - start_time) * 1000
                try:
                    from ..services.performance_collector import performance_collector
                    performance_collector.record_error('llm_error', str(llm_error))
                    performance_collector.record_response_time(response_time, False, None)
                except ImportError:
                    pass

                print(f"LLM调用失败，使用本地回答: {llm_error}")
                # 第七步：LLM失败时的备用方案
                local_fallback = self._generate_local_answer(question, retrieval_result)

                # 🚀 也缓存本地备用回答
                try:
                    from ..services.intelligent_cache_manager import intelligent_cache_manager
                    intelligent_cache_manager.cache_response(question, local_fallback)
                except ImportError:
                    pass

                return local_fallback

        except Exception as e:
            # 🚀 记录系统错误
            response_time = (time.time() - start_time) * 1000 if 'start_time' in locals() else 0
            try:
                from ..services.performance_collector import performance_collector
                performance_collector.record_error('system_error', str(e))
                if response_time > 0:
                    performance_collector.record_response_time(response_time, False, None)
            except ImportError:
                pass

            print(f"回答问题时出错: {e}")
            # 最终备用方案：返回通用错误消息
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
