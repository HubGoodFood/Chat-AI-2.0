# 🍎🥬 果蔬客服AI系统

一个专为果蔬拼台社区设计的智能客服AI助手，能够准确回答客户关于产品和平台政策的问题。

## ✨ 功能特点

- **智能产品咨询**: 查询价格、产地、营养价值、保存方法等
- **政策解答**: 配送、付款、取货、售后等平台政策
- **友好交互**: 中文对话，专业客服体验
- **实时检索**: 基于本地数据的快速准确检索
- **响应式界面**: 支持桌面和移动设备

## 🏗️ 系统架构

```
用户界面层 (Web聊天界面)
    ↓
AI对话层 (LLM API调用 + 提示词工程)
    ↓
知识检索层 (产品/政策智能匹配)
    ↓
数据处理层 (CSV/JSON解析 + 关键词索引)
```

## 📋 技术栈

- **后端**: Python Flask
- **前端**: HTML + CSS + JavaScript
- **数据处理**: pandas + jieba (中文分词)
- **AI模型**: DeepSeek-V3-0324
- **搜索算法**: 模糊匹配 + 关键词索引

## 🚀 快速开始

### 1. 环境要求

- Python 3.7+
- 网络连接 (调用LLM API)

### 2. 安装依赖

```bash
pip install -r requirements.txt
```

### 3. 数据准备

确保以下文件存在：
- `products.csv` - 产品数据
- `policy.json` - 政策数据

### 4. 启动系统

```bash
python start.py
```

或者直接运行：

```bash
python app.py
```

### 5. 访问系统

打开浏览器访问: http://localhost:5000

## 📁 项目结构

```
果蔬客服AI系统/
├── app.py                 # Flask主应用
├── data_processor.py      # 数据处理模块
├── llm_client.py         # LLM客户端
├── knowledge_retriever.py # 知识检索模块
├── test_system.py        # 测试脚本
├── start.py              # 启动脚本
├── requirements.txt      # 依赖包列表
├── products.csv          # 产品数据
├── policy.json           # 政策数据
├── templates/            # HTML模板
│   ├── index.html        # 主页面
│   ├── 404.html          # 404错误页
│   └── 500.html          # 500错误页
└── README.md             # 项目文档
```

## 🧪 测试系统

### 运行完整测试

```bash
python test_system.py
```

### 运行特定测试

```bash
python test_system.py data      # 数据加载测试
python test_system.py product   # 产品搜索测试
python test_system.py policy    # 政策搜索测试
python test_system.py ai        # AI回答测试
python test_system.py performance # 性能测试
```

## 📊 数据格式

### 产品数据 (products.csv)

| 字段 | 说明 | 示例 |
|------|------|------|
| ProductName | 产品名称 | 爱妃苹果 |
| Specification | 规格 | 大箱 |
| Price | 价格 | 60 |
| Unit | 单位 | 大箱 |
| Category | 类别 | 时令水果 |
| Keywords | 关键词 | 苹果 |
| Taste | 口感 | 脆甜多汁 |
| Origin | 产地 | 进口 |
| Benefits | 特点 | 高品质苹果 |
| SuitableFor | 适合人群 | 苹果爱好者 |

### 政策数据 (policy.json)

```json
{
  "version": "2.0.0",
  "sections": {
    "delivery": ["配送相关政策条款"],
    "payment": ["付款相关政策条款"],
    "pickup": ["取货相关政策条款"],
    ...
  }
}
```

## 🔧 配置说明

### LLM API配置

在 `llm_client.py` 中配置：

```python
self.api_url = "https://llm.chutes.ai/v1/chat/completions"
self.api_key = "your_api_key"
self.model = "deepseek-ai/DeepSeek-V3-0324"
```

### 系统提示词

可在 `llm_client.py` 中的 `system_prompt` 变量中自定义AI助手的行为和回答风格。

## 📈 性能优化

- **缓存机制**: 对常见问题实现缓存
- **索引优化**: 使用关键词索引加速搜索
- **响应时间**: 平均响应时间 < 3秒
- **并发支持**: 支持多用户同时使用

## 🛠️ 故障排除

### 常见问题

1. **依赖安装失败**
   ```bash
   pip install --upgrade pip
   pip install -r requirements.txt
   ```

2. **数据加载失败**
   - 检查 `products.csv` 和 `policy.json` 文件是否存在
   - 确认文件编码为 UTF-8

3. **API调用失败**
   - 检查网络连接
   - 验证API密钥是否正确

4. **中文分词问题**
   ```bash
   pip install jieba
   ```

### 日志查看

系统运行时会在控制台输出详细日志，包括：
- 数据加载状态
- API调用结果
- 错误信息

## 🔄 更新和维护

### 更新产品数据

1. 编辑 `products.csv` 文件
2. 重启系统自动加载新数据

### 更新政策信息

1. 编辑 `policy.json` 文件
2. 重启系统自动加载新政策

### 系统升级

1. 备份数据文件
2. 更新代码
3. 安装新依赖
4. 重启系统

## 📞 技术支持

如有问题或建议，请：

1. 查看本文档的故障排除部分
2. 运行测试脚本诊断问题
3. 检查系统日志获取详细错误信息

## 📄 许可证

本项目仅供学习和内部使用。

---

**开发完成时间**: 2024年
**版本**: 1.0.0
**状态**: 生产就绪 ✅
