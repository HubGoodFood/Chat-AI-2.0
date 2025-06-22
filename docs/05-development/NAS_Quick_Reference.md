# Synology NAS 快速参考卡片

## 🚀 快速配置检查清单

### 硬件连接 ✅
- [ ] 硬盘正确安装
- [ ] 网线连接到路由器
- [ ] 电源连接并开机
- [ ] 状态灯显示蓝色（正常）

### 网络访问 ✅
- [ ] 通过Synology Assistant发现设备
- [ ] 浏览器访问：`http://NAS_IP:5000`
- [ ] 完成DSM初始化向导
- [ ] 创建管理员账户

### 存储配置 ✅
- [ ] 创建存储池（推荐RAID 1）
- [ ] 创建存储空间（选择Btrfs）
- [ ] 格式化完成

### 用户权限 ✅
- [ ] 创建chatai_user账户
- [ ] 创建ChatAI_Data共享文件夹
- [ ] 设置读写权限

### 网络映射 ✅
- [ ] Windows：映射Z:驱动器
- [ ] Linux：挂载到/mnt/nas
- [ ] Mac：连接到/Volumes
- [ ] 测试读写权限

---

## 📋 关键配置信息

### 推荐账户设置
```
管理员账户：admin
密码：ChatAI2024!

专用账户：chatai_user  
密码：ChatAI_Storage2024!
```

### 共享文件夹配置
```
名称：ChatAI_Data
路径：/volume1/ChatAI_Data
权限：chatai_user (读写)
```

### 网络映射路径
```
Windows：\\NAS_IP\ChatAI_Data
Linux：//NAS_IP/ChatAI_Data  
Mac：smb://NAS_IP/ChatAI_Data
```

---

## 🔧 常用命令

### Windows映射命令
```cmd
net use Z: \\192.168.1.100\ChatAI_Data /user:chatai_user ChatAI_Storage2024! /persistent:yes
```

### Linux挂载命令
```bash
sudo mount -t cifs //192.168.1.100/ChatAI_Data /mnt/nas -o username=chatai_user,password=ChatAI_Storage2024!
```

### 测试连接
```bash
# 测试NAS连接
python migrate_to_nas.py test Z:\ChatAI_Data

# 执行数据迁移
python migrate_to_nas.py
```

---

## ⚠️ 故障排查

### 连接问题
1. **无法发现NAS**：检查网线、重启设备
2. **映射失败**：检查用户名密码、启用SMB 1.0
3. **权限拒绝**：检查共享文件夹权限设置

### 性能问题
1. **速度慢**：使用有线连接、检查网络带宽
2. **超时**：调整网络超时设置
3. **不稳定**：检查网络设备、更新驱动

---

## 📞 支持信息

### 官方资源
- Synology官网：https://www.synology.com
- 知识库：https://kb.synology.com
- 社区论坛：https://community.synology.com

### 系统信息查看
- DSM版本：控制面板 → 信息中心
- 硬盘状态：存储管理器 → HDD/SSD
- 网络状态：控制面板 → 网络 → 网络界面

---

## 🔄 定期维护

### 每周检查
- [ ] 存储空间使用率
- [ ] 系统运行状态
- [ ] 备份任务执行情况

### 每月检查  
- [ ] DSM系统更新
- [ ] 硬盘健康检查
- [ ] 清理系统日志

### 备份验证
- [ ] 测试数据恢复
- [ ] 检查快照完整性
- [ ] 验证外部备份
