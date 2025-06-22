# -*- coding: utf-8 -*-
"""
集成测试包 - AI客服系统集成测试

这个包包含了AI客服系统的集成测试，用于验证不同模块之间的交互
和端到端的业务流程。

集成测试特点：
1. 测试多个模块的协作
2. 验证完整的业务流程
3. 使用真实的数据流
4. 模拟外部依赖

测试分类：
- chat_workflows: AI客服聊天流程测试
- inventory_workflows: 库存管理工作流测试  
- api_integration: API端点集成测试
- admin_integration: 管理员功能集成测试

运行方式：
pytest tests/integration/ -m integration
"""
