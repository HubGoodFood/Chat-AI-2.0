# 🚀 API快速参考手册

**果蔬客服AI系统 v2.1.0**

---

## 🔗 基础信息

- **基础URL**: `http://localhost:5000`
- **认证方式**: Session-based (管理员API)
- **数据格式**: JSON
- **字符编码**: UTF-8

---

## 📋 API端点总览

### 🤖 客服聊天 (3个端点)

| 方法 | 端点 | 说明 | 认证 |
|------|------|------|------|
| `POST` | `/api/chat` | 发送消息获取AI回复 | ❌ |
| `GET` | `/api/chat/history/{session_id}` | 获取对话历史 | ❌ |
| `GET` | `/api/chat/sessions` | 获取活跃会话列表 | ❌ |

### 🔐 管理员认证 (3个端点)

| 方法 | 端点 | 说明 | 认证 |
|------|------|------|------|
| `POST` | `/api/admin/login` | 管理员登录 | ❌ |
| `POST` | `/api/admin/logout` | 管理员登出 | ✅ |
| `GET` | `/api/admin/status` | 检查认证状态 | ✅ |

### 📦 库存管理 (15个端点)

| 方法 | 端点 | 说明 | 认证 |
|------|------|------|------|
| `GET` | `/api/admin/inventory` | 获取产品列表 | ✅ |
| `POST` | `/api/admin/inventory` | 添加新产品 | ✅ |
| `PUT` | `/api/admin/inventory/{id}` | 更新产品信息 | ✅ |
| `DELETE` | `/api/admin/inventory/{id}` | 删除产品 | ✅ |
| `GET` | `/api/admin/inventory/search` | 产品搜索 | ✅ |
| `GET` | `/api/admin/inventory/summary` | 库存汇总统计 | ✅ |
| `GET` | `/api/admin/inventory/low-stock` | 低库存产品 | ✅ |
| `POST` | `/api/admin/inventory/{id}/stock` | 库存数量调整 | ✅ |
| `GET` | `/api/admin/inventory/storage-areas` | 存储区域列表 | ✅ |
| `POST` | `/api/admin/inventory/storage-areas` | 添加存储区域 | ✅ |
| `PUT` | `/api/admin/inventory/storage-areas/{id}` | 更新存储区域 | ✅ |
| `GET` | `/api/admin/inventory/categories` | 产品分类列表 | ✅ |
| `GET` | `/api/admin/inventory/{id}/history` | 库存变动历史 | ✅ |
| `POST` | `/api/admin/inventory/barcode/generate` | 批量生成条形码 | ✅ |
| `GET` | `/api/admin/inventory/barcode/{barcode}` | 条形码查询产品 | ✅ |

### 📊 库存盘点 (8个端点)

| 方法 | 端点 | 说明 | 认证 |
|------|------|------|------|
| `GET` | `/api/admin/inventory/counts` | 获取盘点任务列表 | ✅ |
| `POST` | `/api/admin/inventory/counts` | 创建盘点任务 | ✅ |
| `GET` | `/api/admin/inventory/counts/{id}` | 获取盘点详情 | ✅ |
| `PUT` | `/api/admin/inventory/counts/{id}` | 更新盘点状态 | ✅ |
| `DELETE` | `/api/admin/inventory/counts/{id}` | 删除盘点任务 | ✅ |
| `POST` | `/api/admin/inventory/counts/{id}/items` | 添加盘点记录 | ✅ |
| `GET` | `/api/admin/inventory/counts/{id}/report` | 获取盘点报告 | ✅ |
| `GET` | `/api/admin/inventory/counts/{id}/excel` | 导出盘点Excel | ✅ |

### 📈 对比分析 (6个端点)

| 方法 | 端点 | 说明 | 认证 |
|------|------|------|------|
| `GET` | `/api/admin/inventory/comparisons` | 获取分析列表 | ✅ |
| `POST` | `/api/admin/inventory/comparisons` | 创建手动对比分析 | ✅ |
| `POST` | `/api/admin/inventory/comparisons/weekly` | 创建周对比分析 | ✅ |
| `GET` | `/api/admin/inventory/comparisons/{id}` | 获取分析详情 | ✅ |
| `GET` | `/api/admin/inventory/comparisons/{id}/report` | 下载分析报告 | ✅ |
| `GET` | `/api/admin/inventory/comparisons/{id}/excel` | 导出Excel数据 | ✅ |

### 💬 反馈管理 (4个端点)

| 方法 | 端点 | 说明 | 认证 |
|------|------|------|------|
| `GET` | `/api/admin/feedback` | 获取反馈列表 | ✅ |
| `POST` | `/api/admin/feedback` | 添加新反馈 | ✅ |
| `PUT` | `/api/admin/feedback/{id}` | 更新反馈状态 | ✅ |
| `DELETE` | `/api/admin/feedback/{id}` | 删除反馈 | ✅ |

### 📋 操作日志 (1个端点)

| 方法 | 端点 | 说明 | 认证 |
|------|------|------|------|
| `GET` | `/api/admin/logs` | 获取操作日志 | ✅ |

### 📤 数据导出 (3个端点)

| 方法 | 端点 | 说明 | 认证 |
|------|------|------|------|
| `GET` | `/api/admin/export/inventory` | 导出库存数据 | ✅ |
| `GET` | `/api/admin/export/feedback` | 导出反馈数据 | ✅ |
| `GET` | `/api/admin/export/logs` | 导出操作日志 | ✅ |

### 🔍 系统状态 (2个端点)

| 方法 | 端点 | 说明 | 认证 |
|------|------|------|------|
| `GET` | `/api/health` | 系统健康检查 | ❌ |
| `GET` | `/api` | API信息 | ❌ |

---

## 📊 统计总结

- **总端点数**: 45个
- **需要认证**: 39个
- **公开访问**: 6个
- **支持分页**: 8个
- **支持搜索**: 3个
- **文件导出**: 6个

---

## 🔧 常用请求示例

### 发送聊天消息

```bash
curl -X POST http://localhost:5000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "苹果多少钱？"}'
```

### 管理员登录

```bash
curl -X POST http://localhost:5000/api/admin/login \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "admin123"}' \
  -c cookies.txt
```

### 获取库存列表

```bash
curl -X GET "http://localhost:5000/api/admin/inventory?page=1&per_page=20" \
  -b cookies.txt
```

### 添加新产品

```bash
curl -X POST http://localhost:5000/api/admin/inventory \
  -H "Content-Type: application/json" \
  -b cookies.txt \
  -d '{
    "product_name": "新鲜香蕉",
    "category": "水果",
    "price": 25,
    "unit": "小箱",
    "initial_stock": 100
  }'
```

### 库存调整

```bash
curl -X POST http://localhost:5000/api/admin/inventory/1/stock \
  -H "Content-Type: application/json" \
  -b cookies.txt \
  -d '{
    "quantity_change": 50,
    "action": "increase",
    "note": "新到货补充"
  }'
```

---

## ⚠️ 常见错误码

| 状态码 | 错误码 | 说明 |
|--------|--------|------|
| `400` | `VALIDATION_ERROR` | 请求参数验证失败 |
| `401` | `AUTH_REQUIRED` | 需要管理员认证 |
| `401` | `AUTH_EXPIRED` | 认证已过期 |
| `403` | `PERMISSION_DENIED` | 权限不足 |
| `404` | `NOT_FOUND` | 资源不存在 |
| `429` | `RATE_LIMIT_EXCEEDED` | 请求频率过高 |
| `500` | `INTERNAL_ERROR` | 服务器内部错误 |

---

## 📝 响应格式

### 成功响应

```json
{
  "success": true,
  "data": { /* 响应数据 */ },
  "message": "操作成功",
  "meta": {
    "timestamp": "2025-06-22T10:30:00Z",
    "version": "v1"
  }
}
```

### 错误响应

```json
{
  "success": false,
  "error": "错误描述",
  "error_code": "ERROR_CODE"
}
```

### 分页响应

```json
{
  "success": true,
  "data": {
    "items": [...],
    "pagination": {
      "page": 1,
      "per_page": 20,
      "total": 100,
      "pages": 5
    }
  }
}
```

---

## 🔗 相关文档

- [完整API文档](./API_DOCUMENTATION.md)
- [系统架构文档](./PROJECT_STRUCTURE.md)
- [部署指南](../README.md#部署指南)

---

*快速参考手册 - 最后更新: 2025年6月22日*
