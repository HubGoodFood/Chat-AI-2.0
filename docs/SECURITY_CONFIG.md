# 🔒 安全配置指南

本文档说明AI客服系统的安全配置和防护措施。

## 🛡️ 安全功能概览

### 1. 速率限制 (Rate Limiting)
- **默认限制**: 60次/分钟
- **API接口**: 100次/分钟  
- **管理接口**: 30次/分钟
- **登录接口**: 5次/分钟（严格限制）

### 2. CORS 跨域保护
- 指定允许的来源域名
- 配置允许的HTTP方法
- 设置安全的请求头

### 3. 输入验证与清理
- 自动检测恶意脚本
- SQL注入防护
- HTML标签过滤
- 长度限制验证

### 4. 请求大小限制
- 最大请求体: 16MB
- JSON负载限制: 1MB
- 防止资源耗尽攻击

### 5. 安全响应头
- 防点击劫持 (X-Frame-Options)
- 防MIME嗅探 (X-Content-Type-Options)
- XSS保护 (X-XSS-Protection)
- 内容安全策略 (CSP)

## ⚙️ 配置参数

### 环境变量配置

```env
# CORS配置
CORS_ORIGINS=http://localhost:5000,http://127.0.0.1:5000

# 速率限制
RATE_LIMIT_DEFAULT=60/minute
RATE_LIMIT_ADMIN=30/minute
RATE_LIMIT_API=100/minute

# 请求大小限制
MAX_CONTENT_LENGTH=16777216
MAX_JSON_PAYLOAD_SIZE=1048576
```

### 生产环境建议

```env
# 生产环境CORS配置（替换为实际域名）
CORS_ORIGINS=https://yourdomain.com,https://www.yourdomain.com

# 更严格的速率限制
RATE_LIMIT_DEFAULT=30/minute
RATE_LIMIT_ADMIN=10/minute
RATE_LIMIT_API=50/minute
```

## 🔧 安全机制详解

### 1. 速率限制实现

```python
# 不同端点的差异化限制
@app.route('/api/chat', methods=['POST'])
@security_config.limiter.limit("30/minute")  # 聊天限制
def chat():
    pass

@app.route('/api/admin/login', methods=['POST'])
@security_config.limiter.limit("5/minute")   # 登录严格限制
def admin_login():
    pass
```

### 2. 输入验证装饰器

```python
@require_valid_input(max_length=500, allow_html=False)
def api_endpoint():
    # 自动验证和清理输入数据
    pass
```

### 3. 安全响应头

系统自动添加以下安全头：
- `X-Frame-Options: DENY`
- `X-Content-Type-Options: nosniff`
- `X-XSS-Protection: 1; mode=block`
- `Content-Security-Policy: default-src 'self'...`

## 🚨 威胁防护

### 防护的攻击类型：

1. **DDoS攻击** - 通过速率限制
2. **XSS攻击** - 输入验证和CSP头
3. **SQL注入** - 输入模式检测
4. **CSRF攻击** - 安全头和来源验证
5. **点击劫持** - X-Frame-Options头
6. **资源耗尽** - 请求大小限制

### 恶意内容检测：

- JavaScript代码注入
- HTML脚本标签
- SQL注入模式
- 事件处理器注入
- CSS表达式攻击

## 📊 监控与日志

### 安全事件记录：
- 速率限制触发
- 输入验证失败
- 恶意请求检测
- 认证失败尝试

### 错误处理：
- 429: 速率限制超出
- 413: 请求实体过大
- 400: 输入验证失败

## 🔄 最佳实践

### 部署前检查：

1. **更新CORS配置**
   ```bash
   # 检查CORS设置
   CORS_ORIGINS=https://yourdomain.com
   ```

2. **调整速率限制**
   ```bash
   # 根据实际负载调整
   RATE_LIMIT_DEFAULT=30/minute
   ```

3. **启用HTTPS**
   - 生产环境必须使用HTTPS
   - 配置SSL证书
   - 强制重定向HTTP到HTTPS

4. **定期安全审计**
   - 检查依赖包漏洞
   - 更新安全配置
   - 监控异常访问

### 开发环境 vs 生产环境：

| 配置项 | 开发环境 | 生产环境 |
|--------|----------|----------|
| CORS来源 | localhost | 具体域名 |
| 速率限制 | 宽松 | 严格 |
| 错误详情 | 详细 | 简化 |
| 日志级别 | DEBUG | INFO/WARNING |

## ⚠️ 注意事项

1. **不要在生产环境使用CORS通配符(*)**
2. **定期更新安全依赖包**
3. **监控异常的访问模式**
4. **备份安全配置**
5. **测试安全措施的有效性**

## 🆘 故障排除

### 常见问题：

**Q: 用户反馈请求被拒绝**
A: 检查速率限制设置，可能需要调整限制值

**Q: CORS错误**
A: 确认CORS_ORIGINS包含正确的域名

**Q: 输入验证失败**
A: 检查输入内容是否包含特殊字符或超长

**Q: 速率限制器不工作**
A: 确认flask-limiter正确安装和配置

---

**安全提醒**: 安全是一个持续的过程，请定期审查和更新安全配置。
