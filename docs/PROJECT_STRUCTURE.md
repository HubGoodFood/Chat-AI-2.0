# 📁 Chat AI 2.0 项目结构说明

本文档详细说明了Chat AI 2.0项目重组后的目录结构和文件组织方式。

## 🏗️ 整体架构

项目采用模块化设计，将不同功能的文件分类组织，提高代码的可维护性和可读性。

## 📂 目录结构详解

### 🔧 src/ - 源代码目录
包含所有核心业务逻辑代码，采用分层架构设计。

#### src/models/ - 核心业务模块
- `knowledge_retriever.py` - 知识检索引擎，负责问答逻辑
- `data_processor.py` - 数据处理模块，处理CSV和JSON数据
- `llm_client.py` - LLM客户端，封装AI模型调用

#### src/utils/ - 工具函数
- `generate_secret_key.py` - 安全密钥生成工具

### 🧪 tests/ - 测试目录
包含所有测试脚本，确保系统质量。

- `test_system.py` - 系统功能测试
- `test_api.py` - API接口测试

### 📊 data/ - 数据目录
集中管理所有数据文件。

- `products.csv` - 产品信息数据
- `policy.json` - 平台政策数据

### 📚 docs/ - 文档目录
包含所有项目文档和指南。

- `PROJECT_SUMMARY.md` - 项目总结
- `DEPLOYMENT_CHECKLIST.md` - 部署检查清单
- `GITHUB_SETUP.md` - GitHub设置指南
- `RENDER_DEPLOYMENT.md` - Render部署指南
- `render_env_setup_guide.md` - 环境设置指南
- `secret_key_lifecycle_guide.md` - 密钥管理指南
- `security_best_practices.md` - 安全最佳实践

### 🔧 scripts/ - 脚本目录
包含自动化脚本和工具。

- `upload_to_github.bat` - GitHub上传脚本

### 🌐 Web资源
- `templates/` - HTML模板文件
- `static/` - 静态资源文件（CSS、JS、图片等）

### 🚀 根目录文件
- `app.py` - Flask主应用入口
- `start.py` - 系统启动脚本
- `requirements.txt` - Python依赖包列表
- `render.yaml` - 云平台部署配置
- `.env.example` - 环境变量配置示例
- `README.md` - 项目主文档

## 🔄 重组前后对比

### 重组前的问题
- 所有文件混在根目录
- 缺乏清晰的分类
- 难以维护和扩展
- 文档散乱

### 重组后的优势
- ✅ 模块化清晰的代码结构
- ✅ 分离的测试和文档
- ✅ 集中的数据管理
- ✅ 便于团队协作
- ✅ 符合Python项目标准

## 📋 文件导入路径

重组后的导入路径示例：

```python
# 导入核心模块
from src.models.knowledge_retriever import KnowledgeRetriever
from src.models.data_processor import DataProcessor
from src.models.llm_client import LLMClient

# 导入工具函数
from src.utils.generate_secret_key import generate_secret_key
```

## 🛠️ 开发指南

### 添加新功能模块
1. 在 `src/models/` 中创建新的Python文件
2. 在 `src/models/__init__.py` 中添加导入
3. 在 `tests/` 中创建对应的测试文件

### 添加新工具函数
1. 在 `src/utils/` 中创建新的Python文件
2. 在需要的地方导入使用

### 更新数据
1. 编辑 `data/` 目录中的相应文件
2. 重启系统自动加载新数据

### 添加文档
1. 在 `docs/` 目录中创建Markdown文件
2. 在主README.md中添加链接

## 🔍 质量保证

项目重组后通过了以下验证：
- ✅ 所有模块导入正常
- ✅ 数据文件路径正确
- ✅ 目录结构完整
- ✅ 系统功能正常

---

**重组完成时间**: 2024年
**重组版本**: 2.0
**状态**: 生产就绪 ✅
