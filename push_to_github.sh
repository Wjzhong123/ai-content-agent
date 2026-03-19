#!/bin/bash
# GitHub自动推送脚本
# 使用方式: ./push_to_github.sh YOUR_GITHUB_TOKEN

set -e

TOKEN=$1
REPO_NAME="ai-content-agent"
USER="Wjzhong123"

if [ -z "$TOKEN" ]; then
    echo "❌ 错误: 需要提供GitHub Token"
    echo "使用方法: ./push_to_github.sh YOUR_GITHUB_TOKEN"
    echo ""
    echo "获取Token步骤:"
    echo "1. 访问 https://github.com/settings/tokens"
    echo "2. 点击 'Generate new token (classic)'"
    echo "3. 勾选 'repo' 权限"
    echo "4. 复制生成的token"
    exit 1
fi

echo "🚀 开始推送到GitHub..."

# 1. 创建仓库
echo "📦 创建GitHub仓库..."
curl -H "Authorization: token $TOKEN" \
     -H "Accept: application/vnd.github.v3+json" \
     https://api.github.com/user/repos \
     -d "{\"name\":\"$REPO_NAME\",\"description\":\"🤖 AI Content Agent - 多平台内容抓取系统\",\"private\":false}" \
     -s -o /dev/null -w "%{http_code}"

echo ""
echo "✅ 仓库创建成功"

# 2. 配置远程仓库
echo "🔗 配置远程仓库..."
cd /Users/mac/Documents/ObsidianVault/4.领域/ai_员工/content-scraper-mcp
git remote remove origin 2>/dev/null || true
git remote add origin https://$USER:$TOKEN@github.com/$USER/$REPO_NAME.git

# 3. 推送代码
echo "📤 推送代码..."
git push -u origin master

echo ""
echo "✅ 推送完成！"
echo "仓库地址: https://github.com/$USER/$REPO_NAME"

# 4. 恢复远程URL（移除token）
git remote set-url origin https://github.com/$USER/$REPO_NAME.git

echo ""
echo "🎉 完成！您现在可以访问:"
echo "   https://github.com/$USER/$REPO_NAME"