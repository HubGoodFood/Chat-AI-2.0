# -*- coding: utf-8 -*-
"""
LLM客户端模块 - 封装DeepSeek API调用
"""
import requests
import os
import sys
from typing import List, Dict
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()


class LLMClient:
    """
    LLM客户端类 - 封装与DeepSeek AI模型的交互

    负责与外部LLM API进行通信，为果蔬客服系统提供智能对话能力。
    支持上下文管理、对话历史、重试机制等高级功能。

    主要功能：
    - API密钥安全管理：从环境变量读取，避免硬编码
    - 智能对话：支持上下文信息和对话历史
    - 错误处理：完善的异常处理和重试机制
    - 信息格式化：产品信息和政策信息的结构化输出
    - 消息生成：欢迎消息、错误消息等预设回复

    配置要求：
    - LLM_API_KEY：必需的API密钥环境变量
    - LLM_API_URL：可选的API端点URL
    - LLM_MODEL：可选的模型名称

    Attributes:
        api_url (str): LLM API的端点URL
        api_key (str): API访问密钥
        model (str): 使用的LLM模型名称
        system_prompt (str): 系统提示词，定义AI助手的角色和行为
    """

    def __init__(self):
        """
        初始化LLM客户端

        从环境变量读取配置信息，验证API密钥，初始化系统提示词。
        如果配置不正确，会提供详细的错误信息和解决方案。

        Raises:
            SystemExit: 如果API密钥未配置或配置错误
        """
        # 从环境变量读取配置，提供默认值
        self.api_url = os.environ.get('LLM_API_URL', "https://llm.chutes.ai/v1/chat/completions")
        self.api_key = self._get_api_key()  # 安全获取API密钥
        self.model = os.environ.get('LLM_MODEL', "deepseek-ai/DeepSeek-V3-0324")

        # 验证API密钥格式和有效性
        self._validate_api_key()

        # 初始化系统提示词，定义AI助手的角色和行为规范
        self._init_system_prompt()

    def _get_api_key(self) -> str:
        """
        安全地获取API密钥，只从环境变量读取

        Returns:
            str: API密钥

        Raises:
            SystemExit: 如果未设置API密钥环境变量
        """
        api_key = os.environ.get('LLM_API_KEY')

        if not api_key:
            try:
                print("❌ 错误：未设置LLM_API_KEY环境变量")
                print("请按照以下步骤配置API密钥：")
                print("1. 复制 .env.example 文件为 .env")
                print("2. 在 .env 文件中设置您的API密钥：")
                print("   LLM_API_KEY=your_actual_api_key_here")
                print("3. 重新启动应用程序")
                print("\n注意：请确保不要将真实的API密钥提交到代码仓库中！")
            except UnicodeEncodeError:
                print("Error: LLM_API_KEY environment variable not set")
                print("Please configure API key following these steps:")
                print("1. Copy .env.example to .env")
                print("2. Set your API key in .env file:")
                print("   LLM_API_KEY=your_actual_api_key_here")
                print("3. Restart the application")
            sys.exit(1)

        return api_key

    def _validate_api_key(self):
        """
        验证API密钥格式
        """
        if not self.api_key or len(self.api_key.strip()) < 10:
            try:
                print("⚠️  警告：API密钥格式可能不正确，请检查配置")
                print(f"当前密钥长度：{len(self.api_key) if self.api_key else 0}")
            except UnicodeEncodeError:
                print("Warning: API key format may be incorrect")
                print(f"Current key length: {len(self.api_key) if self.api_key else 0}")
        else:
            try:
                print("✅ API密钥配置成功")
            except UnicodeEncodeError:
                print("API key configured successfully")

    def _init_system_prompt(self):
        """
        初始化系统提示词

        设置AI助手的角色定义、行为规范和回答原则。
        系统提示词是确保AI回答质量和一致性的关键组件。

        提示词设计原则：
        - 明确角色定位：专业的果蔬客服AI助手
        - 详细职责说明：产品咨询、政策解答、客户服务
        - 具体回答规范：友好、准确、专业的服务态度
        - 特殊注意事项：价格准确性、政策详细性、信息真实性

        Note:
            系统提示词会在每次对话开始时发送给LLM，
            确保AI助手始终保持一致的服务标准和回答风格。
        """
        self.system_prompt = """你是一个专业的果蔬客服AI助手，专门为果蔬拼台社区提供客户服务。

你的职责：
1. 回答客户关于产品的咨询（价格、产地、营养价值、保存方法等）
2. 解答平台政策问题（配送、付款、取货、售后等）
3. 提供友好、专业、准确的客户服务

回答原则：
- 始终保持友好、耐心、专业的态度
- 基于提供的产品数据和政策信息进行准确回答
- 如果没有相关信息，诚实告知并建议联系人工客服
- 使用简洁明了的中文回答
- 适当使用表情符号增加亲和力
- 主动提供相关的有用信息

特别注意：
- 价格信息要准确，包含单位
- 配送政策要详细说明
- 质量问题要按照政策处理
- 不要编造不存在的信息"""

    def chat(self, user_message: str, context_info: str = "", conversation_history: List[Dict] = None) -> str:
        """
        与LLM进行智能对话的核心方法

        整合用户消息、上下文信息和对话历史，调用LLM API生成智能回答。
        支持重试机制、错误处理和详细的日志记录。

        对话流程：
        1. 构建消息列表（系统提示词 + 对话历史 + 当前消息）
        2. 整合上下文信息（产品数据、政策信息等）
        3. 调用LLM API（支持重试机制）
        4. 解析响应并返回AI回答
        5. 异常处理和错误消息生成

        Args:
            user_message (str): 用户输入的问题或消息
            context_info (str, optional): 检索到的相关信息（产品、政策等）
            conversation_history (List[Dict], optional): 对话历史记录，用于维护上下文

        Returns:
            str: AI生成的回答文本

        Example:
            >>> client = LLMClient()
            >>> response = client.chat("苹果多少钱？", "产品：苹果，价格：$5/斤")
            >>> print(response)  # AI生成的关于苹果价格的回答

        Note:
            - 对话历史最多保留最近6轮，避免上下文过长
            - 支持最多2次重试，提高API调用成功率
            - 所有异常都会被捕获并返回友好的错误消息
        """
        try:
            try:
                print(f"[LLM] 开始处理用户消息: {user_message}")
            except UnicodeEncodeError:
                print("[LLM] 开始处理用户消息 (包含特殊字符)")
            print(f"[LLM] API URL: {self.api_url}")
            print(f"[LLM] 模型: {self.model}")

            # 构建消息列表
            messages = [{"role": "system", "content": self.system_prompt}]

            # 添加对话历史
            if conversation_history:
                messages.extend(conversation_history[-6:])  # 保留最近6轮对话
                print(f"[LLM] 添加对话历史: {len(conversation_history[-6:])} 条消息")

            # 构建用户消息
            user_content = user_message
            if context_info:
                user_content = f"""用户问题：{user_message}

相关信息：
{context_info}

请基于以上信息回答用户问题。"""
                try:
                    print(f"[LLM] 添加上下文信息: {context_info[:100]}...")
                except UnicodeEncodeError:
                    print("[LLM] 添加上下文信息 (包含特殊字符)")

            messages.append({"role": "user", "content": user_content})
            print(f"[LLM] 消息列表构建完成，总消息数: {len(messages)}")

            # 调用API
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }

            data = {
                "model": self.model,
                "messages": messages,
                "temperature": 0.7,
                "max_tokens": 1000,
                "stream": False
            }

            print(f"[LLM] 准备发送API请求...")
            
            # 添加重试机制
            max_retries = 2
            for attempt in range(max_retries):
                try:
                    print(f"[LLM] 发送API请求 (尝试 {attempt + 1}/{max_retries + 1})")
                    response = requests.post(self.api_url, headers=headers, json=data, timeout=30)
                    print(f"[LLM] API响应状态码: {response.status_code}")
                    response.raise_for_status()
                    break
                except requests.exceptions.RequestException as e:
                    print(f"[LLM] API请求异常: {e}")
                    if attempt == max_retries - 1:
                        raise e
                    print(f"[LLM] API调用失败，重试中... (尝试 {attempt + 1}/{max_retries})")
                    import time
                    time.sleep(1)

            result = response.json()
            print(f"[LLM] API响应解析成功")

            if 'choices' in result and len(result['choices']) > 0:
                ai_response = result['choices'][0]['message']['content'].strip()
                try:
                    print(f"[LLM] AI回复生成成功: {ai_response[:50]}...")
                except UnicodeEncodeError:
                    print("[LLM] AI回复生成成功 (包含特殊字符)")
                return ai_response
            else:
                print(f"[LLM] API响应格式异常: {result}")
                return "抱歉，我现在无法回答您的问题，请稍后再试或联系人工客服。"
                
        except requests.exceptions.RequestException as e:
            print(f"API请求错误: {e}")
            print(f"请求URL: {self.api_url}")
            print(f"请求数据: {data}")
            return "抱歉，网络连接出现问题，请稍后再试。"
        except Exception as e:
            print(f"处理错误: {e}")
            print(f"错误类型: {type(e)}")
            import traceback
            print(f"错误堆栈: {traceback.format_exc()}")
            return "抱歉，处理您的请求时出现错误，请稍后再试。"
    
    def format_product_info(self, products: List[Dict]) -> str:
        """格式化产品信息"""
        if not products:
            return "没有找到相关产品信息。"
        
        formatted_info = "找到以下相关产品：\n\n"
        
        for i, product in enumerate(products[:3], 1):  # 最多显示3个产品
            formatted_info += f"{i}. **{product['name']}**\n"
            formatted_info += f"   - 规格：{product['specification']}\n"
            formatted_info += f"   - 价格：${product['price']} / {product['unit']}\n"
            formatted_info += f"   - 类别：{product['category']}\n"
            
            if product['taste']:
                formatted_info += f"   - 口感：{product['taste']}\n"
            if product['origin']:
                formatted_info += f"   - 产地：{product['origin']}\n"
            if product['benefits']:
                formatted_info += f"   - 特点：{product['benefits']}\n"
            if product['suitable_for']:
                formatted_info += f"   - 适合：{product['suitable_for']}\n"
            
            formatted_info += "\n"
        
        return formatted_info
    
    def format_policy_info(self, policies: List[Dict]) -> str:
        """格式化政策信息"""
        if not policies:
            return "没有找到相关政策信息。"
        
        formatted_info = "相关政策信息：\n\n"
        
        section_names = {
            'mission': '平台介绍',
            'group_rules': '群规管理',
            'product_quality': '产品质量',
            'delivery': '配送服务',
            'payment': '付款方式',
            'pickup': '取货信息',
            'after_sale': '售后服务',
            'community': '社区文化'
        }
        
        for policy in policies[:2]:  # 最多显示2个政策板块
            section_name = section_names.get(policy['section'], policy['section'])
            formatted_info += f"**{section_name}：**\n"
            
            content = policy['content']
            if isinstance(content, list):
                for item in content:
                    formatted_info += f"• {item}\n"
            else:
                formatted_info += f"{content}\n"
            
            formatted_info += "\n"
        
        return formatted_info
    
    def generate_welcome_message(self) -> str:
        """生成欢迎消息"""
        return """🍎🥬 欢迎来到果蔬拼台客服！

我是您的专属AI客服助手，可以帮您：
• 查询产品信息（价格、产地、营养等）
• 了解配送和付款政策
• 解答售后和取货问题
• 提供其他平台服务咨询

请告诉我您想了解什么，我会尽力为您解答！😊"""

    def generate_error_message(self, error_type: str = "general") -> str:
        """生成错误消息"""
        error_messages = {
            "no_info": "抱歉，我没有找到相关信息。您可以：\n• 尝试换个关键词重新询问\n• 联系人工客服获取帮助\n• 查看我们的产品目录",
            "api_error": "抱歉，系统暂时繁忙，请稍后再试。如有紧急问题，请联系人工客服。",
            "general": "抱歉，处理您的请求时出现问题。请稍后再试或联系人工客服。"
        }
        return error_messages.get(error_type, error_messages["general"])


# 测试代码
if __name__ == "__main__":
    client = LLMClient()
    
    # 测试基本对话
    print("=== LLM客户端测试 ===")
    response = client.chat("你好")
    print(f"AI回复: {response}")
    
    # 测试带上下文的对话
    context = "产品：爱妃苹果，价格：$60/大箱，产地：进口，特点：脆甜多汁"
    response = client.chat("这个苹果怎么样？", context)
    print(f"带上下文的回复: {response}")
