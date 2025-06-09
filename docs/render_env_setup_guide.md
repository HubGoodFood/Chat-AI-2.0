# 🔧 Render环境变量设置详细指南

## 📋 环境变量设置步骤

### 1. SECRET_KEY 设置

**变量名**: `SECRET_KEY`
**值**: 使用生成的安全密钥

```
# 示例（请使用您自己生成的密钥）
SECRET_KEY=04bc895f186f0999d9ea8bc3c60168917caba4ba66572897f024ba28fb73d2b0
```

**设置步骤**:
1. 点击 "Add Environment Variable"
2. Key: 输入 `SECRET_KEY`
3. Value: 粘贴您生成的64字符密钥
4. 点击 "Save Changes"

### 2. FLASK_ENV 设置

**变量名**: `FLASK_ENV`
**值**: `production`

**设置步骤**:
1. 点击 "Add Environment Variable"
2. Key: 输入 `FLASK_ENV`
3. Value: 输入 `production`
4. 点击 "Save Changes"

### 3. LLM_API_KEY 设置

**变量名**: `LLM_API_KEY`
**值**: 您的DeepSeek API密钥

**设置步骤**:
1. 点击 "Add Environment Variable"
2. Key: 输入 `LLM_API_KEY`
3. Value: 粘贴您的API密钥
4. 点击 "Save Changes"

## 🖼️ Render控制台界面说明

```
┌─────────────────────────────────────────────────────────┐
│ chat-ai-2-0 Service                                     │
├─────────────────────────────────────────────────────────┤
│ [Overview] [Logs] [Environment] [Settings] [Metrics]   │
├─────────────────────────────────────────────────────────┤
│ Environment Variables                                   │
│                                                         │
│ ┌─────────────────────────────────────────────────────┐ │
│ │ [Add Environment Variable]                          │ │
│ └─────────────────────────────────────────────────────┘ │
│                                                         │
│ Key: SECRET_KEY                                         │
│ Value: 04bc895f186f0999d9ea8bc3c60168917caba4ba...     │
│ [Edit] [Delete]                                         │
│                                                         │
│ Key: FLASK_ENV                                          │
│ Value: production                                       │
│ [Edit] [Delete]                                         │
│                                                         │
│ Key: LLM_API_KEY                                        │
│ Value: ••••••••••••••••••••••••••••••••••••••••••••    │
│ [Edit] [Delete]                                         │
│                                                         │
│ [Save Changes]                                          │
└─────────────────────────────────────────────────────────┘
```

## ⚠️ 重要注意事项

### SECRET_KEY 安全提示
- ✅ 使用至少32字节（64字符）的随机密钥
- ✅ 每个环境使用不同的密钥
- ❌ 不要在代码中硬编码
- ❌ 不要使用简单或默认值
- ❌ 不要在日志中记录密钥

### FLASK_ENV 设置提示
- ✅ 生产环境必须设置为 `production`
- ✅ 开发环境可以设置为 `development`
- ❌ 生产环境不要使用 `development`
- ❌ 不要在生产环境启用调试模式

### API密钥安全
- ✅ 使用Render的环境变量功能
- ✅ 定期轮换API密钥
- ❌ 不要在代码仓库中提交密钥
- ❌ 不要在日志中记录密钥

## 🔄 环境变量更新

### 修改环境变量
1. 在Environment页面找到要修改的变量
2. 点击 "Edit" 按钮
3. 修改值
4. 点击 "Save Changes"
5. 服务会自动重启以应用新配置

### 删除环境变量
1. 找到要删除的变量
2. 点击 "Delete" 按钮
3. 确认删除
4. 点击 "Save Changes"

## 📊 验证设置

### 检查环境变量是否生效
部署完成后，访问健康检查端点：
```
https://your-app.onrender.com/health
```

应该返回：
```json
{
  "status": "healthy",
  "system_ready": true,
  "timestamp": "2024-xx-xxTxx:xx:xx"
}
```

### 检查Flask环境
在应用日志中查看启动信息：
```
🚀 启动果蔬客服AI系统...
🌐 启动Web服务器... 端口: 10000
 * Environment: production
 * Debug mode: off
```

如果看到 `Debug mode: off`，说明FLASK_ENV设置正确。
