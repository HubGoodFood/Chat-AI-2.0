# ✅ Render部署检查清单

## 📋 部署前检查

### 代码准备
- [ ] 代码已推送到GitHub仓库
- [ ] 包含 `render.yaml` 配置文件
- [ ] 包含 `requirements.txt` 依赖文件
- [ ] 包含数据文件：`products.csv`, `policy.json`
- [ ] app.py 支持动态端口配置
- [ ] llm_client.py 使用环境变量

### 环境变量准备
- [ ] 获得DeepSeek API密钥
- [ ] 生成随机SECRET_KEY
- [ ] 确认API端点可访问

## 🚀 Render部署步骤

### 1. 创建服务
- [ ] 登录 Render.com
- [ ] 点击 "New +" → "Web Service"
- [ ] 连接GitHub仓库
- [ ] 选择项目仓库

### 2. 基本配置
- [ ] **Name**: `chat-ai-2-0`
- [ ] **Environment**: `Python`
- [ ] **Build Command**: `pip install -r requirements.txt`
- [ ] **Start Command**: `python app.py`
- [ ] **Auto-Deploy**: 启用

### 3. 环境变量设置
- [ ] `LLM_API_KEY` = 您的DeepSeek API密钥
- [ ] `SECRET_KEY` = 随机生成的密钥
- [ ] `FLASK_ENV` = `production`

### 4. 高级设置
- [ ] **Health Check Path**: `/health`
- [ ] **Instance Type**: Free (测试) / Starter (生产)

### 5. 部署
- [ ] 点击 "Create Web Service"
- [ ] 等待构建完成（2-5分钟）
- [ ] 获得 `.onrender.com` 域名

## ✅ 部署后验证

### 基本功能测试
- [ ] 访问主页显示聊天界面
- [ ] 健康检查: `https://your-app.onrender.com/health`
- [ ] 发送测试消息并收到AI回复
- [ ] 测试快速问题按钮
- [ ] 测试产品查询功能

### API端点测试
- [ ] `/api/chat` - 聊天接口
- [ ] `/api/categories` - 产品分类
- [ ] `/api/products/<category>` - 产品查询
- [ ] `/api/quick-answers` - 快速回答
- [ ] `/api/clear-session` - 清除会话

### 性能检查
- [ ] 首次响应时间 < 30秒（冷启动）
- [ ] 后续响应时间 < 10秒
- [ ] 无明显错误或崩溃
- [ ] 内存使用正常

## 🔍 故障排除

### 常见问题
- [ ] **构建失败**: 检查 requirements.txt 和 Python 版本
- [ ] **启动失败**: 检查环境变量设置
- [ ] **AI无响应**: 验证 LLM_API_KEY 正确性
- [ ] **数据加载失败**: 确认数据文件存在且格式正确

### 日志检查
- [ ] 查看 Render 控制台日志
- [ ] 检查构建日志中的错误
- [ ] 监控运行时日志

## 📊 监控和维护

### 定期检查
- [ ] 监控应用运行状态
- [ ] 检查错误率和响应时间
- [ ] 更新依赖包版本
- [ ] 备份重要数据

### 扩展建议
- [ ] 考虑升级到付费实例
- [ ] 添加自定义域名
- [ ] 实现缓存机制
- [ ] 添加监控告警

---

**部署完成后，您的AI客服系统将在云端24/7运行！** 🎉

**访问地址**: `https://your-app-name.onrender.com`
**健康检查**: `https://your-app-name.onrender.com/health`
