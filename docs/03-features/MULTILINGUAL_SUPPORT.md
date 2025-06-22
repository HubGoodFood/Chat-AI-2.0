# 🌍 多语言支持指南

本文档说明AI客服系统的多语言功能配置和使用方法。

## 🎯 支持的语言

系统目前支持以下三种语言：

| 语言代码 | 语言名称 | 本地名称 | 标识 |
|---------|---------|---------|------|
| `zh` | 简体中文 | 简体中文 | 🇨🇳 |
| `en` | English | English | 🇺🇸 |
| `zh_TW` | 繁體中文 | 繁體中文 | 🇹🇼 |

## 🔧 技术实现

### 核心技术栈
- **Flask-Babel**: 国际化框架
- **Gettext**: 翻译文件格式
- **JavaScript**: 前端语言切换
- **Session**: 用户语言偏好存储

### 文件结构
```
translations/
├── zh/LC_MESSAGES/
│   ├── messages.po     # 简体中文翻译源文件
│   └── messages.mo     # 简体中文编译文件
├── en/LC_MESSAGES/
│   ├── messages.po     # 英文翻译源文件
│   └── messages.mo     # 英文编译文件
└── zh_TW/LC_MESSAGES/
    ├── messages.po     # 繁体中文翻译源文件
    └── messages.mo     # 繁体中文编译文件
```

## 🚀 功能特性

### 1. 自动语言检测
- 优先使用用户手动选择的语言
- 自动检测浏览器语言偏好
- 回退到系统默认语言

### 2. 实时语言切换
- 页面右上角语言选择器
- 无需刷新页面即可切换
- 保持当前页面状态

### 3. 全面的界面翻译
- 页面标题和导航
- 按钮和表单标签
- 错误信息和提示
- 聊天界面文本

### 4. 用户偏好记忆
- 语言选择保存在Session中
- 下次访问自动应用

## 🎮 用户使用指南

### 切换语言
1. 在页面右上角找到语言选择器
2. 点击下拉菜单选择目标语言
3. 页面内容将立即更新为选择的语言

### 支持的界面元素
- ✅ 页面标题和副标题
- ✅ 欢迎消息和说明文本
- ✅ 快速操作按钮
- ✅ 输入框占位符
- ✅ 错误和状态消息
- ✅ 加载和处理提示

## 🛠️ 开发者指南

### 添加新的翻译文本

1. **在代码中标记需要翻译的文本**
```python
from src.utils.i18n_config import _

# 使用翻译函数
message = _('需要翻译的文本')
```

2. **提取翻译文本**
```bash
python -m babel.messages.frontend extract -F babel.cfg -k _l -o messages.pot .
```

3. **更新翻译文件**
```bash
python -m babel.messages.frontend update -i messages.pot -d translations
```

4. **编辑翻译文件**
编辑 `translations/[语言]/LC_MESSAGES/messages.po` 文件，添加翻译：
```po
msgid "需要翻译的文本"
msgstr "Translated text"
```

5. **编译翻译文件**
```bash
python -m babel.messages.frontend compile -d translations
```

### 添加新语言支持

1. **在配置中添加语言**
编辑 `src/utils/i18n_config.py`：
```python
self.languages = {
    'zh': {...},
    'en': {...},
    'zh_TW': {...},
    'fr': {  # 新增法语
        'name': 'Français',
        'native_name': 'Français',
        'flag': '🇫🇷',
        'code': 'fr'
    }
}
```

2. **创建翻译文件**
```bash
python -m babel.messages.frontend init -i messages.pot -d translations -l fr
```

3. **更新前端语言选择器**
在 `templates/index.html` 中添加新选项：
```html
<option value="fr">🇫🇷 Français</option>
```

4. **添加前端翻译文本**
在 `languageTexts` 对象中添加法语翻译。

## 📝 翻译文本分类

### 系统消息 (SystemMessages)
- 操作成功/失败
- 登录相关消息
- 验证错误信息
- 网络错误提示
- 业务操作反馈

### 界面文本 (UITexts)
- 导航菜单项
- 按钮文本
- 表单标签
- 状态显示
- 聊天界面元素

## 🔄 维护和更新

### 定期维护任务
1. **检查翻译完整性**
   - 确保所有语言的翻译文件都是最新的
   - 检查是否有未翻译的文本

2. **更新翻译质量**
   - 根据用户反馈改进翻译
   - 保持术语的一致性

3. **添加新功能的翻译**
   - 新功能开发时同步添加翻译
   - 及时更新翻译文件

### 翻译文件管理
```bash
# 提取新的翻译文本
pybabel extract -F babel.cfg -k _l -o messages.pot .

# 更新所有语言的翻译文件
pybabel update -i messages.pot -d translations

# 编译所有翻译文件
pybabel compile -d translations
```

## ⚙️ 配置选项

### 环境变量配置
```env
# 默认语言设置
DEFAULT_LANGUAGE=zh

# 支持的语言列表（在代码中配置）
# zh, en, zh_TW
```

### 应用配置
```python
# Flask应用配置
app.config['LANGUAGES'] = languages
app.config['BABEL_DEFAULT_LOCALE'] = 'zh'
app.config['BABEL_DEFAULT_TIMEZONE'] = 'UTC'
```

## 🐛 故障排除

### 常见问题

**Q: 语言切换后部分文本没有更新**
A: 检查是否所有文本都使用了翻译函数，重新编译翻译文件

**Q: 新添加的翻译不生效**
A: 确保执行了编译命令：`pybabel compile -d translations`

**Q: 浏览器语言检测不准确**
A: 检查浏览器语言设置，或手动选择语言

**Q: 翻译文件格式错误**
A: 检查 .po 文件的语法，确保 msgid 和 msgstr 配对正确

### 调试技巧
1. 检查浏览器控制台的错误信息
2. 验证翻译文件是否正确编译
3. 确认语言代码与配置一致
4. 测试API端点 `/api/language` 的响应

## 📊 性能考虑

### 优化建议
- 翻译文件在应用启动时加载，运行时性能良好
- 使用Session存储用户语言偏好，减少重复检测
- 前端缓存语言文本，避免重复请求

### 内存使用
- 每种语言的翻译文件约占用几KB内存
- 支持3种语言的总内存开销很小

---

**多语言支持让您的AI客服系统能够服务更广泛的用户群体！** 🌍✨
