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

### 本地开发

#### 1. 环境要求

- Python 3.7+
- 网络连接 (调用LLM API)

#### 2. 安装依赖

```bash
pip install -r requirements.txt
```

#### 3. 环境变量配置

复制 `.env.example` 为 `.env` 并配置：

```bash
cp .env.example .env
```

编辑 `.env` 文件，填入您的API密钥：
```
LLM_API_KEY=your_deepseek_api_key_here
SECRET_KEY=your_random_secret_key
```

#### 4. 数据准备

确保以下文件存在：
- `data/products.csv` - 产品数据
- `data/policy.json` - 政策数据

#### 5. 启动系统

```bash
python start.py
```

或者直接运行：

```bash
python app.py
```

#### 6. 访问系统

打开浏览器访问: http://localhost:5000

### 云端部署 (Render)

#### 快速部署到Render云平台

1. **Fork或克隆此仓库**到您的GitHub账户

2. **登录Render控制台**: https://render.com

3. **创建Web Service**:
   - 点击 "New +" → "Web Service"
   - 连接您的GitHub仓库
   - 选择此项目

4. **配置服务**:
   - **Name**: `chat-ai-2-0`
   - **Environment**: `Python`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `python app.py`

5. **设置环境变量**:
   ```
   LLM_API_KEY=您的DeepSeek API密钥
   SECRET_KEY=随机生成的密钥字符串
   FLASK_ENV=production
   ```

6. **部署**: 点击 "Create Web Service"，等待部署完成

7. **访问**: 部署成功后获得 `.onrender.com` 域名

📖 **详细部署指南**: 查看 [RENDER_DEPLOYMENT.md](RENDER_DEPLOYMENT.md)

## 📁 项目结构

```
Chat AI 2.0/
├── src/                          # 源代码目录
│   ├── __init__.py
│   ├── models/                   # 核心业务模块
│   │   ├── __init__.py
│   │   ├── knowledge_retriever.py    # 知识检索模块
│   │   ├── data_processor.py         # 数据处理模块
│   │   └── llm_client.py            # LLM客户端
│   └── utils/                    # 工具函数
│       ├── __init__.py
│       └── generate_secret_key.py   # 密钥生成工具
├── tests/                        # 测试文件
│   ├── __init__.py
│   ├── test_api.py              # API测试脚本
│   └── test_system.py           # 系统测试脚本
├── data/                         # 数据文件
│   ├── products.csv             # 产品数据
│   └── policy.json              # 政策数据
├── docs/                         # 文档目录
│   ├── PROJECT_SUMMARY.md       # 项目总结
│   ├── DEPLOYMENT_CHECKLIST.md  # 部署检查清单
│   ├── GITHUB_SETUP.md          # GitHub设置指南
│   ├── RENDER_DEPLOYMENT.md     # Render部署指南
│   ├── render_env_setup_guide.md # 环境设置指南
│   ├── secret_key_lifecycle_guide.md # 密钥管理指南
│   └── security_best_practices.md # 安全最佳实践
├── scripts/                      # 脚本文件
│   └── upload_to_github.bat     # GitHub上传脚本
├── templates/                    # HTML模板
│   ├── index.html               # 主页面
│   ├── 404.html                 # 404错误页
│   └── 500.html                 # 500错误页
├── static/                       # 静态资源
├── app.py                        # Flask主应用
├── start.py                      # 启动脚本
├── requirements.txt              # Python依赖
├── render.yaml                   # 部署配置
├── .env.example                  # 环境变量示例
└── README.md                     # 项目文档
```

## 🧪 测试系统

### 运行完整测试

```bash
python tests/test_system.py
```

### 运行特定测试

```bash
python tests/test_system.py data      # 数据加载测试
python tests/test_system.py product   # 产品搜索测试
python tests/test_system.py policy    # 政策搜索测试
python tests/test_system.py ai        # AI回答测试
python tests/test_system.py performance # 性能测试
```

### API测试

```bash
python tests/test_api.py              # 测试所有API端点
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

### 环境变量配置

系统支持通过环境变量进行配置，主要变量包括：

| 变量名 | 说明 | 默认值 | 必需 |
|--------|------|--------|------|
| `LLM_API_KEY` | DeepSeek API密钥 | - | ✅ |
| `LLM_API_URL` | API端点地址 | https://llm.chutes.ai/v1/chat/completions | ❌ |
| `LLM_MODEL` | 模型名称 | deepseek-ai/DeepSeek-V3-0324 | ❌ |
| `SECRET_KEY` | Flask会话密钥 | 默认密钥 | ✅ |
| `FLASK_ENV` | Flask环境 | development | ❌ |
| `PORT` | 服务端口 | 5000 | ❌ |

### 本地开发配置

创建 `.env` 文件：

```bash
LLM_API_KEY=your_deepseek_api_key
SECRET_KEY=your_random_secret_key
FLASK_ENV=development
```

### 生产环境配置

在Render等云平台中设置环境变量：

```bash
LLM_API_KEY=your_deepseek_api_key
SECRET_KEY=your_random_secret_key
FLASK_ENV=production
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

1. 编辑 `data/products.csv` 文件
2. 重启系统自动加载新数据

### 更新政策信息

1. 编辑 `data/policy.json` 文件
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
