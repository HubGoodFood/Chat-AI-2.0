# 🚀 GitHub上传指南

本指南将帮助您将果蔬客服AI系统上传到GitHub。

## 📋 准备工作

### 1. 确保Git已安装
```bash
git --version
```

如果未安装，请从 [git-scm.com](https://git-scm.com/) 下载安装。

### 2. 配置Git用户信息（首次使用）
```bash
git config --global user.name "您的用户名"
git config --global user.email "您的邮箱"
```

## 🔧 本地Git初始化

### 1. 初始化Git仓库
```bash
git init
```

### 2. 添加所有文件到暂存区
```bash
git add .
```

### 3. 查看文件状态
```bash
git status
```

### 4. 提交初始版本
```bash
git commit -m "🎉 初始提交: 果蔬客服AI系统v1.0

✨ 功能特点:
- 智能产品咨询 (60种产品)
- 政策解答 (8大板块)
- 中文语义理解
- Web聊天界面
- DeepSeek-V3集成

🏗️ 技术栈:
- Python Flask
- pandas + jieba
- HTML/CSS/JavaScript
- 模糊匹配算法

📊 测试状态:
- ✅ 数据加载测试通过
- ✅ 产品搜索测试通过
- ✅ 政策搜索测试通过
- ✅ AI回答测试通过
- ✅ API接口测试通过"
```

## 🌐 GitHub仓库创建

### 方法1: 通过GitHub网站创建

1. 登录 [GitHub](https://github.com)
2. 点击右上角的 "+" → "New repository"
3. 填写仓库信息：
   - **Repository name**: `fruit-vegetable-ai-service`
   - **Description**: `🍎🥬 智能果蔬客服AI系统 - 专业的果蔬拼台社区客服助手`
   - **Visibility**: 选择 Public 或 Private
   - **不要**勾选 "Add a README file"（我们已经有了）
   - **不要**勾选 "Add .gitignore"（我们已经创建了）
4. 点击 "Create repository"

### 方法2: 通过GitHub CLI创建（如果已安装）

```bash
# 安装GitHub CLI: https://cli.github.com/
gh repo create fruit-vegetable-ai-service --public --description "🍎🥬 智能果蔬客服AI系统"
```

## 🔗 连接远程仓库

### 1. 添加远程仓库
```bash
git remote add origin https://github.com/您的用户名/fruit-vegetable-ai-service.git
```

### 2. 验证远程仓库
```bash
git remote -v
```

### 3. 推送到GitHub
```bash
git branch -M main
git push -u origin main
```

## 📝 后续更新流程

### 日常更新命令
```bash
# 1. 查看文件状态
git status

# 2. 添加修改的文件
git add .
# 或添加特定文件
git add 文件名

# 3. 提交更改
git commit -m "📝 更新说明"

# 4. 推送到GitHub
git push
```

### 提交信息规范建议
```bash
# 新功能
git commit -m "✨ 添加新功能: 功能描述"

# 修复bug
git commit -m "🐛 修复: 问题描述"

# 文档更新
git commit -m "📝 文档: 更新内容"

# 性能优化
git commit -m "⚡ 优化: 优化内容"

# 代码重构
git commit -m "♻️ 重构: 重构内容"

# 测试相关
git commit -m "✅ 测试: 测试内容"

# 配置更改
git commit -m "🔧 配置: 配置更改"
```

## 🔒 安全注意事项

### 1. 敏感信息检查
确保以下信息不会被上传：
- ✅ API密钥已在代码中（但建议后续改为环境变量）
- ✅ 没有个人敏感数据
- ✅ 没有临时文件和缓存

### 2. 建议的安全改进
创建环境变量文件模板：

```bash
# 创建 .env.example 文件
echo "# 环境变量配置示例
API_URL=https://llm.chutes.ai/v1/chat/completions
API_KEY=your_api_key_here
MODEL_NAME=deepseek-ai/DeepSeek-V3-0324
DEBUG=False
PORT=5000" > .env.example
```

## 📊 仓库结构预览

上传后的GitHub仓库将包含：

```
fruit-vegetable-ai-service/
├── 📄 README.md              # 项目文档
├── 📄 .gitignore             # Git忽略文件
├── 📄 requirements.txt       # Python依赖
├── 📄 GITHUB_SETUP.md        # 本指南
├── 🐍 app.py                 # Flask主应用
├── 🐍 data_processor.py      # 数据处理模块
├── 🐍 llm_client.py          # LLM客户端
├── 🐍 knowledge_retriever.py # 知识检索模块
├── 🐍 start.py               # 启动脚本
├── 🧪 test_system.py         # 系统测试
├── 🧪 test_api.py            # API测试
├── 📊 products.csv           # 产品数据
├── 📋 policy.json            # 政策数据
└── 📁 templates/             # HTML模板
    ├── index.html
    ├── 404.html
    └── 500.html
```

## 🎯 推荐的GitHub设置

### 1. 仓库设置
- 启用 Issues（问题跟踪）
- 启用 Wiki（文档）
- 设置分支保护规则（如果是团队项目）

### 2. 添加标签（Topics）
在GitHub仓库页面添加以下标签：
- `ai`
- `chatbot`
- `customer-service`
- `flask`
- `python`
- `chinese`
- `fruit-vegetable`
- `deepseek`

### 3. 创建Release
```bash
# 创建标签
git tag -a v1.0.0 -m "🎉 发布v1.0.0: 果蔬客服AI系统首个稳定版本"
git push origin v1.0.0
```

## 🚨 常见问题解决

### 1. 推送被拒绝
```bash
# 如果远程有更新，先拉取
git pull origin main --rebase
git push
```

### 2. 文件过大
```bash
# 查看大文件
git ls-files | xargs ls -l | sort -k5 -rn | head

# 移除大文件
git rm --cached 大文件名
echo "大文件名" >> .gitignore
git commit -m "🗑️ 移除大文件"
```

### 3. 撤销最后一次提交
```bash
# 撤销但保留更改
git reset --soft HEAD~1

# 完全撤销
git reset --hard HEAD~1
```

## ✅ 完成检查清单

- [ ] Git仓库初始化完成
- [ ] .gitignore文件已创建
- [ ] 初始提交已完成
- [ ] GitHub仓库已创建
- [ ] 远程仓库已连接
- [ ] 代码已推送到GitHub
- [ ] 仓库描述和标签已设置
- [ ] README.md显示正常
- [ ] 敏感信息已检查

## 🎉 恭喜！

您的果蔬客服AI系统现在已经成功上传到GitHub！

**下一步建议：**
1. 在GitHub上完善项目描述
2. 添加项目演示截图
3. 设置GitHub Pages（如果需要在线演示）
4. 邀请团队成员协作
5. 设置CI/CD自动化部署

如有任何问题，请参考GitHub官方文档或寻求帮助。
