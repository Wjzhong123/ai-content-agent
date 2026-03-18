# 🤖 AI Content Agent

> **不是爬虫工具，而是你的AI员工**

一个基于MCP协议的智能内容抓取系统，支持7大平台，具备三层架构（抓取层/结构层/知识层），能够自动发现热点、分析趋势、管理知识库。

## 🚀 核心特性

### 三层架构设计

```
抓取层 → 结构层 → 知识层
├── 7平台独立爬虫策略
├── 统一内容模型
└── 向量存储 + 语义搜索
```

### 7大平台支持

| 平台 | 策略 | 反爬等级 |
|------|------|----------|
| 抖音 | Playwright浏览器 | 🔴 高 |
| 小红书 | Playwright浏览器 | 🔴 高 |
| B站 | API优先 | 🟡 中 |
| 知乎 | API优先 | 🟡 中 |
| YouTube | yt-dlp | 🟢 低 |
| Reddit | PRAW API | 🟢 低 |
| 公众号 | 降级方案 | 🟡 中 |

### 🤖 AI级工具

不只是"抓取"，而是"智能分析"：

- 🔥 **热门话题发现** - 自动发现平台热点趋势
- 🎬 **热门内容分析** - 分析爆款内容特征
- 👤 **创作者档案** - 深度分析创作者内容风格
- 📊 **跨平台对比** - 对比话题在不同平台表现
- 🔍 **语义搜索** - 理解语义的内容搜索
- ⏰ **自动调度** - 定时自动抓取，真正成为"员工"

### 📦 技术栈

- **MCP协议**: FastMCP
- **向量存储**: Qdrant + BGE-M3
- **爬虫**: Playwright + yt-dlp + PRAW
- **调度**: schedule
- **部署**: Docker Compose
- **输出**: Obsidian Markdown

## 📁 项目结构

```
content-scraper-mcp/
├── src/
│   ├── server.py              # MCP Server主入口
│   ├── scrapers/               # 抓取层 - 7平台独立策略
│   │   ├── douyin.py
│   │   ├── xiaohongshu.py
│   │   ├── bilibili.py
│   │   ├── zhihu.py
│   │   ├── youtube.py
│   │   ├── reddit.py
│   │   └── wechat.py
│   ├── models/                 # 结构层 - 统一内容模型
│   │   └── content_model.py
│   ├── knowledge/              # 知识层 - 向量存储
│   │   ├── vector_store.py
│   │   ├── embedding.py
│   │   └── search.py
│   ├── scheduler/              # 调度层 - 自动任务
│   │   └── scheduler.py
│   └── output/                 # 输出层 - Markdown生成
│       └── markdown.py
├── scrapers-config/             # 爬虫配置
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
└── README.md

../scraped_content/             # 输出目录
├── douyin/
├── xiaohongshu/
├── bilibili/
├── zhihu/
├── youtube/
├── reddit/
└── wechat/
```

## 🚀 快速开始

### 1. 环境准备

确保你的k8服务器已安装：
- Docker
- Docker Compose
- Git

### 2. 克隆仓库

```bash
git clone https://github.com/yourusername/ai-content-agent.git
cd ai-content-agent
```

### 3. 配置环境变量

```bash
cp .env.example .env
# 编辑 .env 文件，配置Reddit API等
```

### 4. 启动服务

```bash
docker-compose up -d
```

服务启动后：
- MCP Server: http://192.168.1.210:3001
- Qdrant Dashboard: http://192.168.1.210:6333/dashboard

### 5. 配置MCP客户端

在Openfang或其他MCP客户端中添加配置：

```json
{
  "mcpServers": {
    "content-scraper": {
      "url": "http://192.168.1.210:3001/sse"
    }
  }
}
```

## 🛠️ MCP工具使用指南

### 基础抓取工具

```
scraper_douyin_search(keyword="AI工具", limit=20)
scraper_xiaohongshu_search(keyword="副业赚钱", limit=20)
scraper_bilibili_search(keyword="Python教程", limit=20)
scraper_youtube_search(query="ChatGPT", limit=20)
scraper_reddit_search(subreddit="technology", keyword="AI", limit=20)
```

### AI级工具

#### 🔥 获取热门话题
```
get_trending_topics(platform="all", days=7, limit=20)
# 返回各平台的热门话题列表
```

#### 🎬 获取话题热门内容
```
get_hot_videos(topic="AI赚钱", platform="douyin", limit=10)
# 返回话题下的高互动内容
```

#### 👤 创作者分析
```
summarize_creator(author_id="xxx", platform="douyin")
# 分析创作者的内容风格、热门话题
```

#### 📊 跨平台对比
```
compare_platforms(topic="AI工具", platforms="douyin,xiaohongshu,bilibili")
# 对比话题在不同平台的表现差异
```

#### 🔍 语义搜索
```
semantic_search(query="如何提高短视频完播率", limit=10)
# 搜索知识库中语义相关的内容
```

#### ⏰ 创建定时任务
```
schedule_crawl(
    platform="douyin",
    task_type="search",
    params='{"keyword": "AI工具", "limit": 50}',
    schedule="daily@08:00"
)
# 每天早上8点自动抓取"AI工具"相关内容
```

## 📊 输出示例

抓取的内容自动生成Obsidian兼容的Markdown文件：

```markdown
---
title: "抖音搜索 - AI工具"
date: 2024-01-15
platform: douyin
tags:
  - 抖音
  - AI
  - 搜索
keywords:
  - AI工具
  - 人工智能
  - 效率工具
metrics:
  views: 12345
  likes: 888
  engagement_rate: 7.2%
---

# 🔍 抖音搜索结果：AI工具

**搜索时间：** 2024-01-15 10:30:00  
**结果数：** 20条

---

## 1. 10个让效率翻倍的AI工具

**作者：** @科技达人  
**点赞：** 12.5K  **评论：** 888  **分享：** 666  
**互动率：** 8.5%

**视频描述：**
分享10个实用的AI工具...

**精选评论：**
> **用户A：** 真的好用！已收藏
> **用户B：** 第三个工具是什么？

---

## 2. ChatGPT使用技巧

...
```

## 🔧 配置详解

### Reddit API配置

1. 访问 https://www.reddit.com/prefs/apps
2. 创建应用，选择"script"类型
3. 获取 client_id 和 client_secret
4. 填入 .env 文件

### 代理配置

在 .env 中配置：
```
HTTP_PROXY=http://proxy.example.com:8080
HTTPS_PROXY=http://proxy.example.com:8080
```

### 定时任务配置

支持格式：
- `daily@08:00` - 每天8点
- `hourly` - 每小时
- `4h` - 每4小时
- `30m` - 每30分钟

## 🐛 故障排除

### Qdrant连接失败
```bash
docker-compose logs qdrant
# 检查Qdrant服务状态
```

### Playwright浏览器问题
```bash
docker-compose exec content-scraper-mcp playwright install chromium
# 重新安装浏览器
```

### 抓取被封
- 检查代理配置
- 降低抓取频率
- 使用Cookie登录

## 📈 性能优化建议

1. **向量存储**: 大量内容时Qdrant会自动建立索引
2. **代理池**: 配置多个代理轮换
3. **分批处理**: 大批量抓取使用小批次
4. **定时调度**: 避免高峰期集中抓取

## 🗺️ 路线图

- [x] 三层架构设计
- [x] 7大平台爬虫
- [x] 向量存储
- [x] 语义搜索
- [x] 调度系统
- [ ] Web UI管理界面
- [ ] 内容去重优化
- [ ] AI内容生成建议
- [ ] 多语言支持

## 🤝 贡献指南

1. Fork 本仓库
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启 Pull Request

## 📜 许可证

MIT License - 详见 LICENSE 文件

## 🙏 致谢

- [MediaCrawler](https://github.com/NanmiCoder/MediaCrawler) - 中文平台爬虫参考
- [yt-dlp](https://github.com/yt-dlp/yt-dlp) - YouTube下载
- [Qdrant](https://qdrant.tech/) - 向量数据库
- [BGE-M3](https://huggingface.co/BAAI/bge-m3) - Embedding模型

---

<p align="center">
  <strong>🤖 不只是工具，而是你的AI内容员工</strong>
</p>