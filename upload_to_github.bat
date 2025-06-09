@echo off
echo 🚀 果蔬客服AI系统 - GitHub上传脚本
echo =====================================

echo.
echo 📋 请按照以下步骤操作：
echo.
echo 1. 在GitHub上创建新仓库：
echo    - 访问 https://github.com/new
echo    - 仓库名称：fruit-vegetable-ai-service
echo    - 描述：🍎🥬 智能果蔬客服AI系统 - 专业的果蔬拼台社区客服助手
echo    - 选择 Public 或 Private
echo    - 不要勾选 "Add a README file"
echo    - 不要勾选 "Add .gitignore"
echo    - 点击 "Create repository"
echo.

set /p username="请输入您的GitHub用户名: "
if "%username%"=="" (
    echo ❌ 用户名不能为空
    pause
    exit /b 1
)

echo.
echo 🔗 添加远程仓库...
git remote add origin https://github.com/%username%/fruit-vegetable-ai-service.git

echo.
echo 📤 推送到GitHub...
git branch -M main
git push -u origin main

if %errorlevel% equ 0 (
    echo.
    echo ✅ 上传成功！
    echo.
    echo 🌐 您的仓库地址：
    echo https://github.com/%username%/fruit-vegetable-ai-service
    echo.
    echo 🎉 恭喜！您的果蔬客服AI系统已成功上传到GitHub！
    echo.
    echo 📝 下一步建议：
    echo - 在GitHub上完善项目描述
    echo - 添加项目演示截图
    echo - 设置仓库标签（Topics）
    echo - 邀请团队成员协作
) else (
    echo.
    echo ❌ 上传失败！
    echo.
    echo 🔧 可能的解决方案：
    echo 1. 检查GitHub用户名是否正确
    echo 2. 确保已在GitHub上创建了仓库
    echo 3. 检查网络连接
    echo 4. 验证Git凭据
    echo.
    echo 💡 手动上传命令：
    echo git remote add origin https://github.com/%username%/fruit-vegetable-ai-service.git
    echo git branch -M main
    echo git push -u origin main
)

echo.
pause
