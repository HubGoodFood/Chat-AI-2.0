# 🚀 Render云平台部署指南

## 📋 部署前准备

### 1. 项目概述
- **项目类型**: Python Flask Web应用
- **AI模型**: DeepSeek-V3-0324
- **数据库**: 无需数据库（使用CSV和JSON文件）
- **部署类型**: Web Service

### 2. 必需的环境变量
在Render控制台中需要设置以下环境变量：

| 环境变量 | 说明 | 示例值 | 必需 |
|---------|------|--------|------|
| `LLM_API_KEY` | DeepSeek API密钥 | `cpk_xxx...` | ✅ |
| `SECRET_KEY` | Flask会话密钥 | 随机字符串 | ✅ |
| `FLASK_ENV` | Flask环境 | `production` | ✅ |
| `LLM_API_URL` | API端点 | `https://llm.chutes.ai/v1/chat/completions` | ❌ |
| `LLM_MODEL` | 模型名称 | `deepseek-ai/DeepSeek-V3-0324` | ❌ |

## 🔧 Render部署步骤

### 第一步：准备代码仓库
1. 确保代码已推送到GitHub仓库
2. 确保包含以下文件：
   - `render.yaml` - Render配置文件
   - `requirements.txt` - Python依赖
   - `app.py` - 主应用文件
   - 数据文件：`products.csv`, `policy.json`

### 第二步：在Render创建服务
1. 登录 [Render控制台](https://render.com)
2. 点击 "New +" → "Web Service"
3. 连接GitHub仓库
4. 选择您的项目仓库

### 第三步：配置服务设置
**基本设置：**
- **Name**: `chat-ai-2-0`（或您喜欢的名称）
- **Environment**: `Python`
- **Build Command**: `pip install -r requirements.txt`
- **Start Command**: `python app.py`

**高级设置：**
- **Auto-Deploy**: 启用（推荐）
- **Health Check Path**: `/health`

### 第四步：设置环境变量
在 "Environment" 标签页中添加：

```
LLM_API_KEY=您的DeepSeek API密钥
SECRET_KEY=随机生成的密钥字符串
FLASK_ENV=production
```

### 第五步：部署
1. 点击 "Create Web Service"
2. 等待构建和部署完成（通常需要2-5分钟）
3. 部署成功后会获得一个 `.onrender.com` 域名

## ✅ 部署验证

### 健康检查
访问 `https://your-app.onrender.com/health` 应该返回：
```json
{
  "status": "healthy",
  "system_ready": true,
  "timestamp": "2024-xx-xxTxx:xx:xx"
}
```

### 功能测试
1. **主页访问**: 访问根域名应显示聊天界面
2. **AI对话**: 测试发送消息并接收AI回复
3. **快速问题**: 测试快速问题按钮
4. **API端点**: 测试各个API接口

## 🔍 故障排除

### 常见问题

**1. 应用无法启动**
- 检查环境变量是否正确设置
- 查看构建日志中的错误信息
- 确保 `requirements.txt` 包含所有依赖

**2. AI回复失败**
- 检查 `LLM_API_KEY` 是否正确
- 验证API端点是否可访问
- 查看应用日志中的错误信息

**3. 数据加载失败**
- 确保 `products.csv` 和 `policy.json` 文件存在
- 检查文件格式是否正确
- 查看应用启动日志

**4. 冷启动延迟**
- Render免费版有冷启动延迟（~30秒）
- 考虑升级到付费版本以获得更好性能

### 查看日志
在Render控制台中：
1. 进入您的服务页面
2. 点击 "Logs" 标签
3. 查看实时日志输出

## 📊 性能优化

### 建议配置
- **实例类型**: 免费版足够测试，生产环境建议Starter或更高
- **自动扩展**: 启用以处理流量峰值
- **健康检查**: 使用 `/health` 端点

### 监控指标
- 响应时间
- 错误率
- 内存使用
- CPU使用率

## 🔒 安全考虑

1. **API密钥安全**: 
   - 不要在代码中硬编码API密钥
   - 使用Render的环境变量功能

2. **会话安全**:
   - 使用强随机SECRET_KEY
   - 定期轮换密钥

3. **HTTPS**:
   - Render自动提供HTTPS
   - 确保所有API调用使用HTTPS

## 📈 扩展建议

### 短期优化
- 添加请求缓存
- 实现错误重试机制
- 添加更详细的日志

### 长期规划
- 考虑使用Redis缓存
- 实现用户认证
- 添加数据库支持

## 🆘 获取帮助

如果遇到问题：
1. 查看Render官方文档
2. 检查项目的GitHub Issues
3. 联系技术支持

---

**部署完成后，您的AI客服系统将在云端24/7运行！** 🎉
