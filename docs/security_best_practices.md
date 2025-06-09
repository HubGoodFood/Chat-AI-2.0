# 🛡️ 环境变量安全最佳实践

## 🔐 SECRET_KEY 安全指南

### ✅ 正确做法

1. **使用强随机密钥**
```python
# 生成安全密钥
import secrets
SECRET_KEY = secrets.token_hex(32)  # 64字符十六进制
```

2. **不同环境使用不同密钥**
```
开发环境: SECRET_KEY=dev_key_here...
测试环境: SECRET_KEY=test_key_here...
生产环境: SECRET_KEY=prod_key_here...
```

3. **定期轮换密钥**
```
建议频率: 每3-6个月更换一次
紧急情况: 发现泄露时立即更换
```

### ❌ 错误做法

1. **使用弱密钥**
```python
# ❌ 绝对不要这样做
SECRET_KEY = "password"
SECRET_KEY = "123456"
SECRET_KEY = "your_secret_key_here"
SECRET_KEY = "flask_secret"
```

2. **在代码中硬编码**
```python
# ❌ 不要在代码中写死
app.secret_key = "hardcoded_secret_key"
```

3. **在日志中记录**
```python
# ❌ 不要记录敏感信息
print(f"Using secret key: {SECRET_KEY}")
logger.info(f"Secret: {SECRET_KEY}")
```

## 🌍 FLASK_ENV 环境配置

### 环境对比表

| 特性 | development | production | testing |
|------|-------------|------------|---------|
| 调试模式 | ✅ 开启 | ❌ 关闭 | ❌ 关闭 |
| 自动重载 | ✅ 开启 | ❌ 关闭 | ❌ 关闭 |
| 错误详情 | 🔍 完整显示 | 🔒 隐藏敏感信息 | 🧪 测试友好 |
| 性能 | 🐌 较慢 | 🚀 最快 | ⚡ 快速 |
| 安全性 | ⚠️ 较低 | 🔒 最高 | 🔒 高 |
| 日志级别 | DEBUG | INFO/WARNING | DEBUG |

### 配置示例

#### 开发环境 (.env)
```bash
FLASK_ENV=development
SECRET_KEY=dev_04bc895f186f0999d9ea8bc3c60168917caba4ba66572897f024ba28fb73d2b0
LLM_API_KEY=your_dev_api_key
```

#### 生产环境 (Render)
```bash
FLASK_ENV=production
SECRET_KEY=prod_a1b2c3d4e5f6789012345678901234567890abcdef1234567890abcdef123456
LLM_API_KEY=your_prod_api_key
```

## 🔍 安全检查清单

### 部署前检查

- [ ] SECRET_KEY 长度 ≥ 32字节（64字符）
- [ ] SECRET_KEY 使用随机生成
- [ ] FLASK_ENV 设置为 production
- [ ] API密钥未在代码中硬编码
- [ ] 环境变量在Render中正确设置
- [ ] 敏感信息未提交到Git仓库

### 部署后验证

- [ ] 健康检查端点正常响应
- [ ] 错误页面不显示敏感信息
- [ ] 日志中无敏感信息泄露
- [ ] 应用运行在生产模式
- [ ] 调试模式已关闭

## 🚨 应急响应

### 密钥泄露处理

1. **立即更换密钥**
```bash
# 生成新密钥
python -c "import secrets; print(secrets.token_hex(32))"
```

2. **更新Render环境变量**
- 登录Render控制台
- 更新SECRET_KEY值
- 保存更改（服务自动重启）

3. **撤销旧会话**
- 新密钥会使所有旧会话失效
- 用户需要重新开始对话

### 配置错误恢复

1. **FLASK_ENV错误设置**
```bash
# 正确设置
FLASK_ENV=production
```

2. **检查应用日志**
```
查看Render日志确认：
- Environment: production
- Debug mode: off
```

## 📊 监控和审计

### 安全监控指标

1. **错误率监控**
- 监控500错误频率
- 检查是否有敏感信息泄露

2. **性能监控**
- 响应时间
- 内存使用
- CPU使用率

3. **访问日志审计**
- 异常访问模式
- 可疑请求来源

### 定期安全检查

1. **每月检查**
- 环境变量配置
- 依赖包安全更新
- 日志审计

2. **每季度检查**
- 密钥轮换
- 安全策略更新
- 渗透测试

## 🔧 故障排除

### 常见问题诊断

1. **会话问题**
```
症状: 用户会话频繁丢失
原因: SECRET_KEY 设置错误或频繁更改
解决: 检查SECRET_KEY配置
```

2. **性能问题**
```
症状: 应用响应缓慢
原因: FLASK_ENV=development
解决: 设置FLASK_ENV=production
```

3. **安全问题**
```
症状: 错误页面显示敏感信息
原因: 调试模式未关闭
解决: 确保FLASK_ENV=production
```

### 调试命令

```bash
# 检查环境变量
echo $FLASK_ENV
echo $SECRET_KEY | wc -c  # 检查长度

# 验证密钥强度
python -c "
key='your_secret_key_here'
print(f'长度: {len(key)}')
print(f'安全: {len(key) >= 32}')
"
```
