# 🍎🥬 果蔬客服AI系统 - API文档

**版本**: v2.1.0  
**基础URL**: `http://localhost:5000`  
**文档更新**: 2025年6月22日

---

## 📋 目录

- [概述](#概述)
- [认证机制](#认证机制)
- [响应格式](#响应格式)
- [错误处理](#错误处理)
- [API端点](#api端点)
  - [客服聊天API](#客服聊天api)
  - [管理员认证API](#管理员认证api)
  - [库存管理API](#库存管理api)
  - [反馈管理API](#反馈管理api)
  - [操作日志API](#操作日志api)

---

## 🔍 概述

果蔬客服AI系统提供RESTful API接口，支持智能客服对话、库存管理、反馈处理等功能。API采用JSON格式进行数据交换，支持版本控制和统一的错误处理机制。

### 主要特性

- **智能对话**: 基于LLM的智能客服对话
- **库存管理**: 完整的产品库存CRUD操作
- **条形码支持**: 自动生成和管理产品条形码
- **数据分析**: 库存对比分析和报表生成
- **安全认证**: 基于会话的管理员认证机制
- **操作审计**: 完整的操作日志记录

---

## 🔐 认证机制

### 管理员认证

管理员API需要通过会话认证访问。认证流程：

1. 通过 `/api/admin/login` 登录获取会话
2. 会话信息存储在Cookie中
3. 后续请求自动携带会话信息
4. 会话超时时间为1小时

### 认证状态码

| 状态码 | 说明 |
|--------|------|
| `401` | 未认证或认证过期 |
| `403` | 权限不足 |

---

## 📊 响应格式

### 成功响应

```json
{
  "success": true,
  "data": {
    // 响应数据
  },
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
  "error_code": "ERROR_CODE",
  "details": {
    // 错误详情（可选）
  }
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

## ⚠️ 错误处理

### 常见错误码

| 错误码 | HTTP状态 | 说明 |
|--------|----------|------|
| `VALIDATION_ERROR` | 400 | 请求参数验证失败 |
| `AUTH_REQUIRED` | 401 | 需要认证 |
| `AUTH_EXPIRED` | 401 | 认证已过期 |
| `PERMISSION_DENIED` | 403 | 权限不足 |
| `NOT_FOUND` | 404 | 资源不存在 |
| `RATE_LIMIT_EXCEEDED` | 429 | 请求频率过高 |
| `INTERNAL_ERROR` | 500 | 服务器内部错误 |

---

## 💬 客服聊天API

### 发送消息

**端点**: `POST /api/chat`

发送用户消息并获取AI回复。

#### 请求参数

```json
{
  "message": "苹果多少钱？",
  "session_id": "uuid-string",
  "context": {
    "user_agent": "Mozilla/5.0...",
    "timestamp": "2025-06-22T10:30:00Z"
  }
}
```

#### 响应示例

```json
{
  "success": true,
  "data": {
    "response": "🍎 **爱妃苹果** - $60/大箱\n规格：大箱装\n产地：进口\n口感：脆甜多汁",
    "session_id": "uuid-string",
    "message_id": "msg_123",
    "timestamp": "2025-06-22T10:30:00Z"
  },
  "message": "消息处理成功"
}
```

### 获取对话历史

**端点**: `GET /api/chat/history/{session_id}`

获取指定会话的对话历史记录。

#### 查询参数

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `limit` | int | 20 | 返回消息数量限制 (1-100) |

#### 响应示例

```json
{
  "success": true,
  "data": [
    {
      "message_id": "msg_123",
      "role": "user",
      "content": "苹果多少钱？",
      "timestamp": "2025-06-22T10:30:00Z"
    },
    {
      "message_id": "msg_124",
      "role": "assistant", 
      "content": "🍎 **爱妃苹果** - $60/大箱",
      "timestamp": "2025-06-22T10:30:05Z"
    }
  ],
  "meta": {
    "session_id": "uuid-string",
    "limit": 20
  }
}
```

---

## 🔑 管理员认证API

### 管理员登录

**端点**: `POST /api/admin/login`

管理员账户登录认证。

#### 请求参数

```json
{
  "username": "admin",
  "password": "admin123"
}
```

#### 响应示例

```json
{
  "success": true,
  "data": {
    "username": "admin",
    "login_time": "2025-06-22T10:30:00Z",
    "session_timeout": 3600
  },
  "message": "登录成功"
}
```

### 管理员登出

**端点**: `POST /api/admin/logout`

管理员账户登出。

#### 响应示例

```json
{
  "success": true,
  "message": "登出成功"
}
```

### 验证会话状态

**端点**: `GET /api/admin/status`

检查当前管理员会话状态。

#### 响应示例

```json
{
  "success": true,
  "data": {
    "authenticated": true,
    "username": "admin",
    "last_activity": "2025-06-22T10:30:00Z",
    "session_remaining": 3540
  }
}
```

---

## 📦 库存管理API

### 获取产品列表

**端点**: `GET /api/admin/inventory`

获取产品库存列表，支持分页和筛选。

#### 查询参数

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `page` | int | 1 | 页码 |
| `per_page` | int | 20 | 每页数量 (1-100) |
| `category` | string | - | 产品分类筛选 |
| `status` | string | active | 产品状态 (active/inactive) |
| `search` | string | - | 搜索关键词 |

#### 响应示例

```json
{
  "success": true,
  "data": {
    "items": [
      {
        "product_id": "1",
        "product_name": "爱妃苹果",
        "category": "水果",
        "price": 60,
        "unit": "大箱",
        "current_stock": 50,
        "min_stock_warning": 10,
        "barcode": "880000010001",
        "barcode_image": "barcodes/爱妃苹果_880000010001.png",
        "storage_area": "A",
        "status": "active",
        "created_at": "2025-06-01T00:00:00Z",
        "updated_at": "2025-06-22T10:30:00Z"
      }
    ],
    "pagination": {
      "page": 1,
      "per_page": 20,
      "total": 150,
      "pages": 8
    }
  }
}
```

### 添加新产品

**端点**: `POST /api/admin/inventory`

添加新的产品到库存系统。

#### 请求参数

```json
{
  "product_name": "新鲜香蕉",
  "category": "水果",
  "specification": "中等大小",
  "price": 25,
  "unit": "小箱",
  "initial_stock": 100,
  "min_stock_warning": 15,
  "description": "进口香蕉，香甜可口",
  "image_url": "https://example.com/banana.jpg",
  "storage_area": "B"
}
```

#### 响应示例

```json
{
  "success": true,
  "data": {
    "product_id": "151",
    "product_name": "新鲜香蕉",
    "barcode": "880001510001",
    "barcode_image": "barcodes/新鲜香蕉_880001510001.png",
    "created_at": "2025-06-22T10:30:00Z"
  },
  "message": "产品添加成功"
}
```

### 更新产品信息

**端点**: `PUT /api/admin/inventory/{product_id}`

更新指定产品的信息。

#### 请求参数

```json
{
  "product_name": "优质香蕉",
  "price": 28,
  "min_stock_warning": 20,
  "description": "精选进口香蕉，品质优良"
}
```

#### 响应示例

```json
{
  "success": true,
  "data": {
    "product_id": "151",
    "updated_fields": ["product_name", "price", "min_stock_warning", "description"],
    "updated_at": "2025-06-22T10:35:00Z"
  },
  "message": "产品信息更新成功"
}
```

### 删除产品

**端点**: `DELETE /api/admin/inventory/{product_id}`

软删除产品（设置为inactive状态）。

#### 响应示例

```json
{
  "success": true,
  "data": {
    "product_id": "151",
    "status": "inactive",
    "deleted_at": "2025-06-22T10:40:00Z"
  },
  "message": "产品删除成功"
}
```

### 库存数量调整

**端点**: `POST /api/admin/inventory/{product_id}/stock`

调整产品的库存数量。

#### 请求参数

```json
{
  "quantity_change": 50,
  "action": "increase",
  "note": "新到货补充库存"
}
```

#### 响应示例

```json
{
  "success": true,
  "data": {
    "product_id": "1",
    "old_stock": 50,
    "new_stock": 100,
    "quantity_change": 50,
    "action": "increase",
    "operator": "admin",
    "timestamp": "2025-06-22T10:45:00Z"
  },
  "message": "库存调整成功"
}
```

### 获取库存汇总

**端点**: `GET /api/admin/inventory/summary`

获取库存系统的汇总统计信息。

#### 响应示例

```json
{
  "success": true,
  "data": {
    "total_products": 150,
    "active_products": 145,
    "low_stock_count": 8,
    "total_value": 125680.50,
    "categories": {
      "水果": 85,
      "蔬菜": 45,
      "禽类": 15
    },
    "storage_areas": {
      "A": 60,
      "B": 45,
      "C": 25,
      "D": 15
    },
    "last_updated": "2025-06-22T10:30:00Z"
  },
  "message": "库存汇总获取成功"
}
```

### 获取低库存产品

**端点**: `GET /api/admin/inventory/low-stock`

获取库存数量低于警告线的产品列表。

#### 响应示例

```json
{
  "success": true,
  "data": [
    {
      "product_id": "5",
      "product_name": "有机胡萝卜",
      "current_stock": 8,
      "min_stock_warning": 15,
      "shortage": 7,
      "category": "蔬菜",
      "storage_area": "C"
    },
    {
      "product_id": "12",
      "product_name": "新鲜菠菜",
      "current_stock": 3,
      "min_stock_warning": 10,
      "shortage": 7,
      "category": "蔬菜",
      "storage_area": "B"
    }
  ],
  "message": "低库存产品列表获取成功"
}
```

### 产品搜索

**端点**: `GET /api/admin/inventory/search`

根据关键词搜索产品。

#### 查询参数

| 参数 | 类型 | 说明 |
|------|------|------|
| `q` | string | 搜索关键词 |
| `category` | string | 分类筛选 |
| `storage_area` | string | 存储区域筛选 |

#### 响应示例

```json
{
  "success": true,
  "data": [
    {
      "product_id": "1",
      "product_name": "爱妃苹果",
      "category": "水果",
      "current_stock": 50,
      "price": 60,
      "barcode": "880000010001"
    }
  ],
  "meta": {
    "query": "苹果",
    "results_count": 1
  }
}
```

---

## 📋 反馈管理API

### 获取反馈列表

**端点**: `GET /api/admin/feedback`

获取客户反馈列表。

#### 查询参数

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `page` | int | 1 | 页码 |
| `per_page` | int | 20 | 每页数量 |
| `status` | string | - | 处理状态筛选 |
| `type` | string | - | 反馈类型筛选 |

#### 响应示例

```json
{
  "success": true,
  "data": {
    "items": [
      {
        "feedback_id": "fb_001",
        "product_name": "爱妃苹果",
        "customer_name": "张三",
        "wechat_group": "果蔬拼台群1",
        "payment_status": "已付款",
        "feedback_type": "positive",
        "content": "苹果很新鲜，味道很好！",
        "images": ["feedback/fb_001_1.jpg"],
        "status": "已处理",
        "created_at": "2025-06-22T09:00:00Z",
        "processed_at": "2025-06-22T10:00:00Z",
        "processor": "admin"
      }
    ],
    "pagination": {
      "page": 1,
      "per_page": 20,
      "total": 45,
      "pages": 3
    }
  }
}
```

### 添加新反馈

**端点**: `POST /api/admin/feedback`

添加新的客户反馈记录。

#### 请求参数

```json
{
  "product_name": "爱妃苹果",
  "customer_name": "李四",
  "wechat_group": "果蔬拼台群2",
  "payment_status": "已付款",
  "feedback_type": "negative",
  "content": "苹果有些软了，不够新鲜",
  "images": ["base64_image_data_1", "base64_image_data_2"]
}
```

#### 响应示例

```json
{
  "success": true,
  "data": {
    "feedback_id": "fb_002",
    "created_at": "2025-06-22T11:00:00Z",
    "status": "待处理"
  },
  "message": "反馈添加成功"
}
```

### 更新反馈状态

**端点**: `PUT /api/admin/feedback/{feedback_id}`

更新反馈的处理状态和处理结果。

#### 请求参数

```json
{
  "status": "已处理",
  "processor_note": "已联系客户并提供解决方案",
  "solution": "重新发货新鲜苹果"
}
```

#### 响应示例

```json
{
  "success": true,
  "data": {
    "feedback_id": "fb_002",
    "status": "已处理",
    "processed_at": "2025-06-22T11:30:00Z",
    "processor": "admin"
  },
  "message": "反馈状态更新成功"
}
```

---

## 📊 操作日志API

### 获取操作日志

**端点**: `GET /api/admin/logs`

获取系统操作日志记录。

#### 查询参数

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `page` | int | 1 | 页码 |
| `per_page` | int | 50 | 每页数量 |
| `operator` | string | - | 操作员筛选 |
| `operation_type` | string | - | 操作类型筛选 |
| `start_date` | string | - | 开始日期 (YYYY-MM-DD) |
| `end_date` | string | - | 结束日期 (YYYY-MM-DD) |

#### 响应示例

```json
{
  "success": true,
  "data": {
    "items": [
      {
        "log_id": "log_001",
        "operator": "admin",
        "operation_type": "update_product",
        "target_type": "product",
        "target_id": "1",
        "details": {
          "method": "PUT",
          "endpoint": "/api/admin/inventory/1",
          "changes": {
            "price": {"old": 60, "new": 65}
          }
        },
        "result": "success",
        "timestamp": "2025-06-22T10:35:00Z",
        "ip_address": "192.168.1.100"
      }
    ],
    "pagination": {
      "page": 1,
      "per_page": 50,
      "total": 1250,
      "pages": 25
    }
  }
}
```

---

## 🔧 库存盘点API

### 创建盘点任务

**端点**: `POST /api/admin/inventory/counts`

创建新的库存盘点任务。

#### 请求参数

```json
{
  "count_name": "月度全面盘点",
  "description": "2025年6月月度库存盘点",
  "storage_areas": ["A", "B", "C"],
  "product_categories": ["水果", "蔬菜"]
}
```

#### 响应示例

```json
{
  "success": true,
  "data": {
    "count_id": "count_001",
    "count_name": "月度全面盘点",
    "status": "进行中",
    "created_at": "2025-06-22T12:00:00Z",
    "products_count": 120,
    "operator": "admin"
  },
  "message": "盘点任务创建成功"
}
```

### 添加盘点记录

**端点**: `POST /api/admin/inventory/counts/{count_id}/items`

为盘点任务添加产品盘点记录。

#### 请求参数

```json
{
  "product_id": "1",
  "actual_quantity": 48,
  "note": "发现2个损坏"
}
```

#### 响应示例

```json
{
  "success": true,
  "data": {
    "item_id": "item_001",
    "product_id": "1",
    "product_name": "爱妃苹果",
    "system_quantity": 50,
    "actual_quantity": 48,
    "difference": -2,
    "status": "差异",
    "recorded_at": "2025-06-22T12:15:00Z"
  },
  "message": "盘点记录添加成功"
}
```

---

## 📈 数据分析API

### 创建对比分析

**端点**: `POST /api/admin/inventory/comparisons`

创建库存对比分析任务。

#### 请求参数

```json
{
  "analysis_type": "weekly",
  "name": "本周库存对比分析",
  "description": "分析本周库存变化情况",
  "date_range": {
    "start_date": "2025-06-15",
    "end_date": "2025-06-22"
  }
}
```

#### 响应示例

```json
{
  "success": true,
  "data": {
    "comparison_id": "comp_001",
    "analysis_type": "weekly",
    "status": "已完成",
    "created_at": "2025-06-22T13:00:00Z",
    "summary": {
      "total_products": 150,
      "products_with_changes": 45,
      "significant_changes": 8,
      "trend": "stable"
    }
  },
  "message": "对比分析创建成功"
}
```

### 获取分析报告

**端点**: `GET /api/admin/inventory/comparisons/{comparison_id}/report`

获取详细的分析报告。

#### 响应示例

```json
{
  "success": true,
  "data": {
    "comparison_id": "comp_001",
    "report": {
      "summary": {
        "analysis_period": "2025-06-15 至 2025-06-22",
        "total_products": 150,
        "products_analyzed": 150,
        "significant_changes": 8
      },
      "categories": [
        {
          "category": "水果",
          "products_count": 85,
          "avg_change_percent": 2.5,
          "trend": "增长"
        }
      ],
      "top_changes": [
        {
          "product_id": "5",
          "product_name": "有机胡萝卜",
          "change_percent": -45.2,
          "reason": "销售旺盛"
        }
      ]
    }
  }
}
```

---

## 📄 数据导出API

### 导出库存数据

**端点**: `GET /api/admin/export/inventory`

导出库存数据为Excel文件。

#### 查询参数

| 参数 | 类型 | 说明 |
|------|------|------|
| `format` | string | 导出格式 (excel/csv) |
| `category` | string | 分类筛选 |
| `include_history` | boolean | 是否包含历史记录 |

#### 响应

返回文件下载，Content-Type为 `application/vnd.openxmlformats-officedocument.spreadsheetml.sheet`

---

## 🔍 系统状态API

### 系统健康检查

**端点**: `GET /api/health`

检查系统运行状态。

#### 响应示例

```json
{
  "success": true,
  "data": {
    "status": "healthy",
    "version": "2.1.0",
    "uptime": "2 days, 5 hours",
    "services": {
      "database": "connected",
      "llm_api": "available",
      "file_system": "accessible"
    },
    "timestamp": "2025-06-22T14:00:00Z"
  }
}
```

---

## 📝 使用示例

### JavaScript示例

```javascript
// 发送聊天消息
async function sendMessage(message) {
  const response = await fetch('/api/chat', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      message: message,
      session_id: localStorage.getItem('session_id')
    })
  });

  const data = await response.json();
  if (data.success) {
    console.log('AI回复:', data.data.response);
    localStorage.setItem('session_id', data.data.session_id);
  }
}

// 管理员登录
async function adminLogin(username, password) {
  const response = await fetch('/api/admin/login', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({ username, password })
  });

  const data = await response.json();
  return data.success;
}
```

### Python示例

```python
import requests

# 发送聊天消息
def send_message(message, session_id=None):
    url = 'http://localhost:5000/api/chat'
    data = {
        'message': message,
        'session_id': session_id
    }

    response = requests.post(url, json=data)
    return response.json()

# 获取库存列表
def get_inventory(page=1, per_page=20):
    url = 'http://localhost:5000/api/admin/inventory'
    params = {'page': page, 'per_page': per_page}

    # 需要先登录获取会话
    session = requests.Session()
    login_response = session.post(
        'http://localhost:5000/api/admin/login',
        json={'username': 'admin', 'password': 'admin123'}
    )

    if login_response.json()['success']:
        response = session.get(url, params=params)
        return response.json()
```

---

## 📞 技术支持

如有API使用问题，请联系技术支持：

- **文档版本**: v2.1.0
- **最后更新**: 2025年6月22日
- **维护团队**: 果蔬客服AI系统开发团队

---

*本文档将随着系统更新持续维护，请关注版本变更。*
```
