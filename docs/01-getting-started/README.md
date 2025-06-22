# 🍎 AI客服系统 - 快速开始指南

## 📋 项目概述

**项目名称**: 果蔬客服AI系统  
**版本**: v2.0.0  
**开发状态**: ✅ 完成  
**测试状态**: ✅ 全部通过  
**部署状态**: ✅ 生产就绪  

这是一个专为果蔬行业设计的智能客服系统，集成了AI对话、库存管理、客户反馈管理等完整功能模块。

## ✨ 核心功能

### 🤖 AI客服系统
- 智能产品咨询（60种产品）
- 政策解答（8大板块）
- 中文语义理解
- 上下文对话管理
- 专业客服语调

### 📦 库存管理系统
- 产品信息管理
- 库存数量控制
- 条形码生成和管理
- 库存盘点功能
- 数据对比分析

### 💬 客户反馈管理
- 反馈信息收集
- 处理状态管理
- 统计分析功能
- 图片支持

### 🔐 管理员系统
- 安全登录机制
- 权限控制
- 操作日志记录
- 数据导出功能

## 🚀 快速开始

### 1. 环境要求
- Python 3.11+
- 现代浏览器（Chrome、Firefox、Edge等）

### 2. 安装依赖
```bash
pip install -r requirements.txt
```

### 3. 启动系统
```bash
python start.py
```

### 4. 访问系统
- **客服界面**: http://localhost:5000
- **管理后台**: http://localhost:5000/admin/login
- **默认管理员账户**: admin / admin123

## 📚 文档导航

### 快速开始
- [用户指南](USER_GUIDE.md) - 详细的使用说明
- [GitHub设置](GITHUB_SETUP.md) - 代码仓库配置

### API文档
- [API文档](../02-api/API_DOCUMENTATION.md) - 完整的API参考
- [API密钥设置](../02-api/API_KEY_SETUP.md) - API配置指南

### 功能模块
- [库存管理指南](../03-features/INVENTORY_MANAGEMENT_GUIDE.md) - 库存功能详解
- [多语言支持](../03-features/MULTILINGUAL_SUPPORT.md) - 国际化功能

### 部署配置
- [部署检查清单](../04-deployment/DEPLOYMENT_CHECKLIST.md) - 生产部署指南
- [安全配置](../04-deployment/SECURITY_CONFIG.md) - 安全设置

### 开发维护
- [项目结构](../05-development/PROJECT_STRUCTURE.md) - 代码架构说明
- [集成测试](../05-development/INTEGRATION_TESTING.md) - 测试指南

## 🎯 设计原则

- **简约设计**: 避免过度设计，界面简洁实用
- **模块化**: 功能模块独立，易于维护和扩展
- **安全性**: 完整的认证和权限控制机制
- **一致性**: 与现有系统风格和技术栈保持一致

## 🔧 技术栈

### 后端技术
- **Python 3.11+**: 主要开发语言
- **Flask**: Web框架
- **DeepSeek-V3**: AI模型
- **SQLite**: 数据存储

### 前端技术
- **HTML5/CSS3**: 页面结构和样式
- **JavaScript**: 交互逻辑
- **Bootstrap**: UI框架

## 📞 支持与帮助

如果您在使用过程中遇到问题，请参考：
1. [用户指南](USER_GUIDE.md) - 常见问题解答
2. [API文档](../02-api/API_DOCUMENTATION.md) - 技术参考
3. [项目改进指南](../05-development/PROJECT_IMPROVEMENT_GUIDE.md) - 问题排查

---

**最后更新**: 2025年6月22日  
**维护状态**: 🔄 持续维护
