# 🍎🥬 果蔬客服AI系统

一个专为果蔬拼台社区设计的智能客服AI助手，集成了完整的后台管理功能，能够准确回答客户关于产品和平台政策的问题，并提供专业的库存和反馈管理能力。

## ✨ 功能特点

### 🤖 智能客服功能
- **智能产品咨询**: 查询价格、产地、营养价值、保存方法等
- **政策解答**: 配送、付款、取货、售后等平台政策
- **友好交互**: 中文对话，专业客服体验
- **实时检索**: 基于本地数据的快速准确检索
- **响应式界面**: 支持桌面和移动设备

### 🔧 后台管理功能
- **📦 库存管理**: 产品信息管理、库存调整、低库存预警
- **💬 反馈管理**: 客户反馈收集、处理状态跟踪、统计分析
- **🔐 权限控制**: 管理员认证、会话管理、安全访问
- **📋 操作日志**: 自动记录操作、审计追踪、统计分析
- **📤 数据导出**: 多格式导出、报告生成、数据备份

## 🏗️ 系统架构

```
前端界面层
├── 客服聊天界面 (用户端)
└── 管理员控制台 (管理端)
    ↓
Flask Web应用层
├── 客服API (聊天、产品查询)
└── 管理API (库存、反馈、日志)
    ↓
业务逻辑层
├── AI对话处理 (LLM API + 提示词工程)
├── 知识检索 (产品/政策智能匹配)
├── 库存管理 (产品管理、库存调整)
├── 反馈管理 (反馈收集、处理跟踪)
├── 操作日志 (自动记录、审计追踪)
└── 数据导出 (多格式导出、报告生成)
    ↓
数据存储层
├── CSV文件 (产品数据)
├── JSON文件 (政策、库存、反馈、日志)
└── 文件上传 (图片等静态资源)
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

**客服系统**: http://localhost:5000
**管理后台**: http://localhost:5000/admin/login
- 默认账户：admin / admin123

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
│   │   ├── llm_client.py            # LLM客户端
│   │   ├── admin_auth.py            # 管理员认证
│   │   ├── inventory_manager.py     # 库存管理
│   │   ├── feedback_manager.py      # 反馈管理
│   │   ├── operation_logger.py      # 操作日志
│   │   └── data_exporter.py         # 数据导出
│   └── utils/                    # 工具函数
│       ├── __init__.py
│       └── generate_secret_key.py   # 密钥生成工具
├── tests/                        # 测试文件
│   ├── __init__.py
│   ├── test_api.py              # API测试脚本
│   ├── test_system.py           # 系统测试脚本
│   ├── test_admin_system.py     # 管理员系统测试
│   └── test_enhanced_features.py # 增强功能测试
├── data/                         # 数据文件
│   ├── products.csv             # 产品数据
│   ├── policy.json              # 政策数据
│   ├── inventory.json           # 库存数据
│   ├── feedback.json            # 反馈数据
│   ├── admin.json               # 管理员账户
│   └── operation_logs.json      # 操作日志
├── docs/                         # 文档目录
│   ├── PROJECT_SUMMARY.md       # 项目总结
│   ├── DEPLOYMENT_CHECKLIST.md  # 部署检查清单
│   ├── GITHUB_SETUP.md          # GitHub设置指南
│   ├── RENDER_DEPLOYMENT.md     # Render部署指南
│   ├── render_env_setup_guide.md # 环境设置指南
│   ├── secret_key_lifecycle_guide.md # 密钥管理指南
│   ├── security_best_practices.md # 安全最佳实践
│   ├── ADMIN_SYSTEM_SUMMARY.md  # 管理员系统总结
│   ├── FINAL_PROJECT_SUMMARY.md # 项目完成总结
│   └── USER_GUIDE.md            # 用户使用指南
├── scripts/                      # 脚本文件
│   └── upload_to_github.bat     # GitHub上传脚本
├── templates/                    # HTML模板
│   ├── index.html               # 客服主页面
│   ├── 404.html                 # 404错误页
│   ├── 500.html                 # 500错误页
│   └── admin/                   # 管理员页面
│       ├── login.html           # 登录页面
│       ├── dashboard.html       # 管理控制台
│       └── modals.html          # 模态框模板
├── static/                       # 静态资源
│   ├── css/
│   │   └── admin.css            # 管理员样式
│   ├── js/
│   │   └── admin.js             # 管理员脚本
│   └── uploads/                 # 文件上传目录
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
# 基础系统测试
python tests/test_system.py

# 管理员系统测试
python tests/test_admin_system.py

# 增强功能测试
python tests/test_enhanced_features.py
```

### 运行特定测试

```bash
# 基础功能测试
python tests/test_system.py data      # 数据加载测试
python tests/test_system.py product   # 产品搜索测试
python tests/test_system.py policy    # 政策搜索测试
python tests/test_system.py ai        # AI回答测试
python tests/test_system.py performance # 性能测试

# API测试
python tests/test_api.py              # 测试所有API端点
```

### 测试结果示例

```
🎯 基础功能测试: 3/3 通过
🎯 管理员系统测试: 3/3 通过
🎯 增强功能测试: 5/5 通过
🎉 所有测试通过！系统功能完整
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

## 🔧 管理员功能

### 访问管理后台

1. **启动系统**: `python start.py`
2. **访问地址**: `http://localhost:5000/admin/login`
3. **默认账户**: admin / admin123

### 功能模块

#### 📊 控制台
- 系统概览和关键统计信息
- 库存状态监控
- 最新反馈查看
- 低库存产品提醒

#### 📦 库存管理
- **产品管理**: 添加、编辑、删除产品信息
- **库存调整**: 手动增加/减少库存数量
- **库存监控**: 实时库存状态、低库存预警
- **分类管理**: 按产品分类筛选和管理
- **搜索功能**: 快速查找特定产品

#### 💬 反馈管理
- **反馈收集**: 记录客户反馈信息
- **处理跟踪**: 管理反馈处理状态
- **统计分析**: 反馈类型和处理状态统计
- **图片支持**: 支持客户上传图片
- **搜索过滤**: 按类型、状态、客户等过滤

#### 📋 操作日志
- **自动记录**: 所有管理员操作自动记录
- **日志查询**: 按操作员、类型、时间查询
- **审计追踪**: 完整的操作历史记录
- **统计分析**: 操作频率和趋势分析

#### 📤 数据导出
- **多格式导出**: CSV、JSON格式数据导出
- **报告生成**: 自动生成库存和反馈报告
- **数据备份**: 完整系统数据备份
- **日志导出**: 操作日志导出功能

#### ⚙️ 系统设置
- **密码管理**: 修改管理员密码
- **系统信息**: 查看系统状态和版本
- **系统维护**: 清理日志、优化数据

### 安全特性

- **认证机制**: 安全的登录/登出系统
- **会话管理**: 自动超时和会话控制
- **权限控制**: 管理员专用功能访问
- **操作记录**: 完整的操作审计日志
- **数据保护**: 密码哈希存储和数据验证

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

5. **管理员登录问题**
   - 默认账户：admin / admin123
   - 检查会话是否超时
   - 清除浏览器缓存

6. **数据文件权限问题**
   - 确保data目录有写入权限
   - 检查JSON文件格式是否正确

7. **导出功能失败**
   - 检查磁盘空间是否充足
   - 确认浏览器允许文件下载

### 日志查看

系统运行时会在控制台输出详细日志，包括：
- 数据加载状态
- API调用结果
- 错误信息

## 🔄 更新和维护

### 数据管理

#### 通过管理后台更新（推荐）
1. 访问管理后台：`http://localhost:5000/admin/login`
2. 使用库存管理功能添加/编辑产品
3. 使用反馈管理功能处理客户反馈
4. 所有操作自动记录日志

#### 直接编辑文件
1. **更新产品数据**: 编辑 `data/products.csv` 文件
2. **更新政策信息**: 编辑 `data/policy.json` 文件
3. **重启系统**: 自动加载新数据

### 数据备份

#### 自动备份（推荐）
1. 登录管理后台
2. 进入"数据导出"页面
3. 点击"创建备份"下载完整备份

#### 手动备份
```bash
# 备份数据目录
cp -r data/ backup/data_$(date +%Y%m%d)/
```

### 系统升级

1. **备份数据**: 使用管理后台导出完整备份
2. **更新代码**: 拉取最新代码
3. **安装依赖**: `pip install -r requirements.txt`
4. **重启系统**: `python start.py`
5. **验证功能**: 运行测试脚本确认功能正常

### 日常维护

#### 通过管理后台
- **清理日志**: 系统设置 → 清理旧日志
- **查看统计**: 控制台查看系统运行状态
- **导出报告**: 定期生成库存和反馈报告

#### 性能优化
- 定期清理30天前的操作日志
- 监控数据文件大小，适时归档
- 检查磁盘空间，确保充足存储

## 📞 技术支持

如有问题或建议，请：

1. 查看本文档的故障排除部分
2. 运行测试脚本诊断问题
3. 检查系统日志获取详细错误信息
4. 查看管理后台的操作日志
5. 参考用户使用指南：`docs/USER_GUIDE.md`

## 📚 相关文档

- **📖 用户使用指南**: [docs/USER_GUIDE.md](docs/USER_GUIDE.md)
- **📋 管理员系统总结**: [docs/ADMIN_SYSTEM_SUMMARY.md](docs/ADMIN_SYSTEM_SUMMARY.md)
- **🎉 项目完成总结**: [docs/FINAL_PROJECT_SUMMARY.md](docs/FINAL_PROJECT_SUMMARY.md)
- **🚀 部署指南**: [docs/RENDER_DEPLOYMENT.md](docs/RENDER_DEPLOYMENT.md)
- **🔒 安全最佳实践**: [docs/security_best_practices.md](docs/security_best_practices.md)

## 📄 许可证

本项目仅供学习和内部使用。

---

**开发完成时间**: 2024年6月9日
**版本**: 2.0.0
**状态**: 生产就绪 ✅
**功能**: 客服AI + 完整后台管理
**测试状态**: 全部通过 (8/8) 🎉
