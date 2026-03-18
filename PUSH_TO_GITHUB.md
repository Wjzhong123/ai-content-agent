# 🚀 推送到GitHub指南

## 方法1: 使用GitHub网站 + HTTPS推送（推荐）

### 步骤1: 在GitHub创建仓库

1. 访问 https://github.com/new
2. 填写信息：
   - **Repository name**: `ai-content-agent` (建议) 或 `content-scraper-mcp`
   - **Description**: 🤖 AI Content Agent - 多平台内容抓取系统，支持抖音、小红书、B站、知乎、YouTube、Reddit、公众号
   - **Public**: ✅ (推荐开源)
   - 不要勾选 "Add a README" (已有README.md)
3. 点击 **Create repository**

### 步骤2: 使用Personal Access Token认证

#### 创建Token:
1. 访问 https://github.com/settings/tokens
2. 点击 **Generate new token (classic)**
3. 填写信息：
   - **Note**: AI Content Agent Push
   - **Expiration**: 90 days 或 No expiration
   - **Scopes**: 勾选 `repo` (完整仓库访问权限)
4. 点击 **Generate token**
5. **立即复制token**（只显示一次！）

### 步骤3: 推送代码

```bash
# 进入项目目录
cd /Users/mac/Documents/ObsidianVault/4.领域/ai_员工/content-scraper-mcp

# 更新远程仓库URL（使用您的用户名和仓库名）
git remote add origin https://github.com/Wjzhong123/ai-content-agent.git

# 或者如果已存在
# git remote set-url origin https://github.com/Wjzhong123/ai-content-agent.git

# 推送（输入您的用户名 Wjzhong123 和上面的token作为密码）
git push -u origin master
```

**注意**: 当提示输入密码时，输入您刚才复制的**Personal Access Token**，而不是您的GitHub密码。

---

## 方法2: 使用SSH推送

### 步骤1: 测试SSH连接

```bash
# 确保GitHub在known_hosts中
ssh-keyscan -t rsa github.com >> ~/.ssh/known_hosts

# 测试连接
ssh -T git@github.com
# 应该显示: Hi Wjzhong123! You've successfully authenticated...
```

### 步骤2: 添加SSH公钥到GitHub

1. 访问 https://github.com/settings/keys
2. 点击 **New SSH key**
3. 填写信息：
   - **Title**: MacBook Pro (或任意名称)
   - **Key**: 粘贴下面的公钥内容

```bash
# 复制公钥
cat ~/.ssh/id_rsa.pub | pbcopy
# 或手动复制
```

4. 点击 **Add SSH key**

### 步骤3: 推送代码

```bash
# 进入项目目录
cd /Users/mac/Documents/ObsidianVault/4.领域/ai_员工/content-scraper-mcp

# 使用SSH URL
git remote set-url origin git@github.com:Wjzhong123/ai-content-agent.git

# 推送
git push -u origin master
```

---

## 方法3: 使用GitHub Desktop（图形界面）

1. 下载 GitHub Desktop: https://desktop.github.com/
2. 登录您的GitHub账号
3. File → Add local repository
4. 选择项目文件夹
5. 点击 Publish repository

---

## 验证推送成功

推送成功后，访问：
```
https://github.com/Wjzhong123/ai-content-agent
```

应该能看到所有文件。

---

## 常见问题

### Q: 提示 "fatal: Authentication failed"
A: 使用Personal Access Token，不要用GitHub密码

### Q: 提示 "Repository not found"
A: 先在GitHub网站创建仓库

### Q: 提示 "Permission denied (publickey)"
A: SSH key未正确配置，使用方法1的HTTPS方式

---

## 快速命令参考

```bash
# 检查配置
git config --list
git remote -v

# 重置认证（如果之前失败过）
git credential-osxkeychain erase
host=github.com
protocol=https

# 重新推送
git push -u origin master
```