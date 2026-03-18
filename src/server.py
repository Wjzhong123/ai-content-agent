"""
Content Scraper MCP Server v2.0
多平台内容抓取 MCP 服务器

升级功能：
- 三层架构（抓取层/结构层/知识层）
- AI级工具（热门话题、创作者分析、内容对比）
- 调度系统支持
- 向量搜索
"""

import os
import sys
import json
from typing import Optional, List, Dict, Any
from datetime import datetime
from fastmcp import FastMCP, Context
from loguru import logger

# 导入所有模块
from models.content_model import ContentItem, TrendingTopic, CreatorProfile
from scrapers.douyin import DouyinScraper
from scrapers.xiaohongshu import XiaohongshuScraper
from scrapers.bilibili import BilibiliScraper
from scrapers.zhihu import ZhihuScraper
from scrapers.youtube import YouTubeScraper
from scrapers.reddit import RedditScraper
from scrapers.wechat import WeChatScraper
from knowledge.vector_store import VectorStore
from knowledge.embedding import EmbeddingService
from knowledge.search import KnowledgeSearch
from scheduler.scheduler import ContentScheduler

# 配置日志
os.makedirs("logs", exist_ok=True)
logger.add("logs/scraper_{time}.log", rotation="500 MB", retention="10 days")

# 初始化 MCP Server
mcp = FastMCP(
    name="content-scraper-mcp",
    description="🚀 AI级内容抓取员工 - 支持抖音、小红书、B站、知乎、YouTube、Reddit、公众号",
    version="2.0.0",
    dependencies=["mcp", "fastmcp", "loguru", "pydantic"]
)

# 初始化各层组件
logger.info("初始化 AI Content Agent...")

# 抓取层
scrapers = {
    "douyin": DouyinScraper(),
    "xiaohongshu": XiaohongshuScraper(),
    "bilibili": BilibiliScraper(),
    "zhihu": ZhihuScraper(),
    "youtube": YouTubeScraper(),
    "reddit": RedditScraper(),
    "wechat": WeChatScraper()
}

# 知识层
embedding_service = EmbeddingService()
vector_store = VectorStore()
knowledge_search = KnowledgeSearch(vector_store, embedding_service)

# 调度层
scheduler = None  # 延迟初始化

# 输出目录
OUTPUT_DIR = os.getenv("OUTPUT_DIR", "/app/scraped_content")

logger.info("AI Content Agent 初始化完成")

# ========== 基础工具（保留）==========

@mcp.tool()
async def scraper_douyin_search(
    keyword: str,
    limit: int = 20,
    sort: str = "general",
    ctx: Context = None
) -> str:
    """搜索抖音视频"""
    try:
        if ctx:
            await ctx.info(f"🔍 正在搜索抖音: {keyword}")
        
        scraper = scrapers["douyin"]
        results = await scraper.search(keyword, limit, sort)
        
        if not results:
            return f"❌ 未找到抖音视频: {keyword}"
        
        # 保存到Markdown
        await ctx.info(f"✅ 找到 {len(results)} 条结果，正在生成报告...") if ctx else None
        
        # 向量化并存储
        content_items = [r.to_content_item() for r in results if hasattr(r, 'to_content_item')]
        if content_items:
            await _store_content_batch(content_items)
        
        # 生成Markdown
        from output.markdown import MarkdownGenerator
        md_gen = MarkdownGenerator()
        markdown = md_gen.generate_content_list(content_items, keyword)
        
        # 保存
        filename = f"douyin/search_{keyword}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
        filepath = md_gen.save_to_file(markdown, filename, OUTPUT_DIR)
        
        return f"✅ 抖音搜索完成！\n\n关键词: {keyword}\n找到: {len(results)} 条结果\n已保存至: {filepath}"
    
    except Exception as e:
        logger.error(f"抖音搜索失败: {e}")
        return f"❌ 抖音搜索失败: {str(e)}"

@mcp.tool()
async def scraper_xiaohongshu_search(keyword: str, limit: int = 20, ctx: Context = None) -> str:
    """搜索小红书笔记"""
    try:
        scraper = scrapers["xiaohongshu"]
        results = await scraper.search(keyword, limit)
        return f"✅ 小红书搜索完成！找到 {len(results)} 条结果\n关键词: {keyword}"
    except Exception as e:
        return f"❌ 小红书搜索失败: {str(e)}"

@mcp.tool()
async def scraper_bilibili_search(keyword: str, limit: int = 20, ctx: Context = None) -> str:
    """搜索B站视频"""
    try:
        scraper = scrapers["bilibili"]
        results = await scraper.search(keyword, limit)
        return f"✅ B站搜索完成！找到 {len(results)} 条结果\n关键词: {keyword}"
    except Exception as e:
        return f"❌ B站搜索失败: {str(e)}"

@mcp.tool()
async def scraper_zhihu_search(keyword: str, limit: int = 20, ctx: Context = None) -> str:
    """搜索知乎"""
    try:
        scraper = scrapers["zhihu"]
        results = await scraper.search(keyword, limit)
        return f"✅ 知乎搜索完成！找到 {len(results)} 条结果\n关键词: {keyword}"
    except Exception as e:
        return f"❌ 知乎搜索失败: {str(e)}"

@mcp.tool()
async def scraper_youtube_search(query: str, limit: int = 20, ctx: Context = None) -> str:
    """搜索YouTube"""
    try:
        scraper = scrapers["youtube"]
        results = await scraper.search(query, limit)
        return f"✅ YouTube搜索完成！找到 {len(results)} 条结果\n关键词: {query}"
    except Exception as e:
        return f"❌ YouTube搜索失败: {str(e)}"

@mcp.tool()
async def scraper_reddit_search(subreddit: str, keyword: str = "", limit: int = 20, ctx: Context = None) -> str:
    """搜索Reddit"""
    try:
        scraper = scrapers["reddit"]
        results = await scraper.search_subreddit(subreddit, keyword, limit)
        return f"✅ Reddit搜索完成！找到 {len(results)} 条结果\nr/{subreddit}: {keyword or '热门'}"
    except Exception as e:
        return f"❌ Reddit搜索失败: {str(e)}"

@mcp.tool()
async def scraper_wechat_search(keyword: str, limit: int = 20, ctx: Context = None) -> str:
    """搜索公众号"""
    try:
        scraper = scrapers["wechat"]
        results = await scraper.search_articles(keyword, limit)
        return f"✅ 公众号搜索完成！找到 {len(results)} 条结果\n关键词: {keyword}"
    except Exception as e:
        return f"❌ 公众号搜索失败: {str(e)}"

# ========== AI级工具（新增）==========

@mcp.tool()
async def get_trending_topics(
    platform: str = "all",
    days: int = 7,
    limit: int = 20,
    ctx: Context = None
) -> str:
    """
    🔥 获取热门话题/趋势
    
    获取指定平台的热门话题，帮助发现爆款内容方向
    
    Args:
        platform: 平台 (all/douyin/xiaohongshu/bilibili/zhihu/youtube/reddit)
        days: 时间范围（天）
        limit: 返回数量
    
    Returns:
        热门话题列表及分析
    """
    try:
        if ctx:
            await ctx.info(f"🔥 正在获取热门话题: {platform}")
        
        # 获取热门话题
        if platform == "all":
            # 获取所有平台
            platforms = ["douyin", "xiaohongshu", "bilibili", "zhihu"]
            all_topics = {}
            for p in platforms:
                topics = knowledge_search.get_trending_topics(p, days, limit // 2)
                all_topics[p] = topics
            
            # 生成报告
            report = "# 🔥 热门话题报告\n\n"
            report += f"**分析范围：** 过去 {days} 天\n"
            report += f"**生成时间：** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
            
            for p, topics in all_topics.items():
                report += f"## {p.upper()} 热门话题\n\n"
                for i, topic in enumerate(topics[:10], 1):
                    report += f"{i}. **{topic.topic}** - 热度: {topic.hot_score:.1f}\n"
                report += "\n"
            
            return report
        else:
            # 单个平台
            topics = knowledge_search.get_trending_topics(platform, days, limit)
            
            report = f"# 🔥 {platform.upper()} 热门话题\n\n"
            for i, topic in enumerate(topics, 1):
                report += f"{i}. **{topic.topic}**\n"
                report += f"   - 热度: {topic.hot_score:.1f}\n"
                report += f"   - 相关内容: {topic.content_count} 条\n\n"
            
            return report
    
    except Exception as e:
        logger.error(f"获取热门话题失败: {e}")
        return f"❌ 获取热门话题失败: {str(e)}"

@mcp.tool()
async def get_hot_videos(
    topic: str,
    platform: str = "douyin",
    limit: int = 10,
    ctx: Context = None
) -> str:
    """
    🎬 获取话题下的热门视频
    
    搜索指定话题的高互动内容，用于选题参考
    
    Args:
        topic: 话题关键词
        platform: 平台
        limit: 返回数量
    
    Returns:
        热门视频列表及数据分析
    """
    try:
        if ctx:
            await ctx.info(f"🎬 正在搜索话题热门内容: {topic} @ {platform}")
        
        # 语义搜索
        results = knowledge_search.get_content_by_topic(topic, limit * 2)
        
        # 过滤平台
        if platform != "all":
            results = [r for r in results if r.get('platform') == platform]
        
        # 按互动率排序
        results.sort(key=lambda x: x.get('metrics', {}).get('engagement_rate', 0), reverse=True)
        
        if not results:
            return f"❌ 未找到话题 '{topic}' 的相关内容"
        
        # 生成报告
        report = f"# 🎬 话题热门内容：{topic}\n\n"
        report += f"**平台：** {platform}\n"
        report += f"**结果数：** {len(results)}\n\n"
        
        for i, item in enumerate(results[:limit], 1):
            metrics = item.get('metrics', {})
            report += f"## {i}. {item.get('title', '无标题')[:50]}\n\n"
            report += f"- **作者：** {item.get('author', '未知')}\n"
            report += f"- **浏览：** {metrics.get('views', 0):,}\n"
            report += f"- **互动率：** {metrics.get('engagement_rate', 0):.2f}%\n"
            report += f"- **链接：** [{item.get('url', '查看')}]({item.get('url', '#')})\n\n"
        
        return report
    
    except Exception as e:
        logger.error(f"获取热门视频失败: {e}")
        return f"❌ 获取热门视频失败: {str(e)}"

@mcp.tool()
async def summarize_creator(
    author_id: str,
    platform: str,
    ctx: Context = None
) -> str:
    """
    👤 创作者内容分析
    
    分析指定创作者的内容风格、热门话题、互动数据
    
    Args:
        author_id: 创作者ID
        platform: 平台
    
    Returns:
        创作者分析报告
    """
    try:
        if ctx:
            await ctx.info(f"👤 正在分析创作者: {author_id} @ {platform}")
        
        # 获取创作者档案
        profile = await knowledge_search.analyze_creator(author_id, platform)
        
        if not profile:
            return f"❌ 未找到创作者信息: {author_id}"
        
        # 生成报告
        report = f"# 👤 创作者分析：{profile.author.display_name or profile.author.username}\n\n"
        report += f"**平台：** {platform}\n"
        report += f"**粉丝数：** {profile.author.followers_count:,}\n"
        report += f"**内容数：** {profile.total_content}\n"
        report += f"**平均互动率：** {profile.avg_metrics.engagement_rate:.2f}%\n\n"
        
        if profile.topics:
            report += "## 📌 主要内容标签\n\n"
            report += ", ".join([f"`{t}`" for t in profile.topics[:10]]) + "\n\n"
        
        if profile.top_content:
            report += "## 🔥 热门内容\n\n"
            for i, content in enumerate(profile.top_content[:5], 1):
                report += f"{i}. {content.title[:60]}\n"
                report += f"   - 点赞：{content.metrics.likes:,} | 评论：{content.metrics.comments:,}\n\n"
        
        return report
    
    except Exception as e:
        logger.error(f"创作者分析失败: {e}")
        return f"❌ 创作者分析失败: {str(e)}"

@mcp.tool()
async def compare_platforms(
    topic: str,
    platforms: str = "douyin,xiaohongshu,bilibili",
    ctx: Context = None
) -> str:
    """
    📊 跨平台内容对比
    
    对比同一话题在不同平台的表现差异
    
    Args:
        topic: 话题关键词
        platforms: 平台列表（逗号分隔）
    
    Returns:
        跨平台对比分析
    """
    try:
        platform_list = [p.strip() for p in platforms.split(",")]
        
        if ctx:
            await ctx.info(f"📊 正在对比话题: {topic} 在 {len(platform_list)} 个平台")
        
        # 执行对比
        comparison = knowledge_search.compare_platforms(topic, platform_list)
        
        return f"# 📊 跨平台对比：{topic}\n\n{comparison.get('summary', '暂无数据')}"
    
    except Exception as e:
        logger.error(f"跨平台对比失败: {e}")
        return f"❌ 跨平台对比失败: {str(e)}"

@mcp.tool()
async def semantic_search(
    query: str,
    limit: int = 10,
    ctx: Context = None
) -> str:
    """
    🔍 语义搜索
    
    基于语义理解搜索已抓取的内容（不是实时抓取）
    
    Args:
        query: 搜索查询
        limit: 返回数量
    
    Returns:
        语义搜索结果
    """
    try:
        if ctx:
            await ctx.info(f"🔍 语义搜索: {query}")
        
        # 执行语义搜索
        results = knowledge_search.semantic_search(query, limit)
        
        if not results:
            return f"❌ 未找到相关内容: {query}"
        
        report = f"# 🔍 语义搜索结果：{query}\n\n"
        report += f"找到 {len(results)} 条相关内容\n\n"
        
        for i, item in enumerate(results, 1):
            report += f"## {i}. {item.get('title', '无标题')[:60]}\n\n"
            report += f"**来源：** {item.get('platform', '未知')}  
"
            report += f"**作者：** {item.get('author', '未知')}  
"
            report += f"**相似度：** {item.get('similarity_score', 0):.2%}  
"
            report += f"**摘要：** {item.get('summary', '无摘要')[:150]}...\n\n"
        
        return report
    
    except Exception as e:
        logger.error(f"语义搜索失败: {e}")
        return f"❌ 语义搜索失败: {str(e)}"

@mcp.tool()
async def schedule_crawl(
    platform: str,
    task_type: str,
    params: str,
    schedule: str = "daily@08:00",
    ctx: Context = None
) -> str:
    """
    ⏰ 创建定时抓取任务
    
    设置自动定时抓取，让AI员工自动工作
    
    Args:
        platform: 平台
        task_type: 任务类型 (search/creator/trending)
        params: 任务参数（JSON格式）
        schedule: 定时规则 (daily@HH:MM/hourly/4h)
    
    Returns:
        任务创建结果
    """
    try:
        global scheduler
        if scheduler is None:
            scheduler = ContentScheduler()
            scheduler.start()
        
        # 解析参数
        params_dict = json.loads(params) if isinstance(params, str) else params
        
        # 创建任务
        from scheduler.scheduler import CrawlJob
        job = CrawlJob(
            id=f"{platform}_{task_type}_{int(datetime.now().timestamp())}",
            name=f"定时: {task_type}",
            platform=platform,
            task_type=task_type,
            params=params_dict,
            schedule=schedule
        )
        
        job_id = scheduler.add_job(job)
        
        return f"✅ 定时任务创建成功！\n\n任务ID: {job_id}\n平台: {platform}\n类型: {task_type}\n定时: {schedule}\n参数: {json.dumps(params_dict, ensure_ascii=False, indent=2)}"
    
    except Exception as e:
        logger.error(f"创建定时任务失败: {e}")
        return f"❌ 创建定时任务失败: {str(e)}"

@mcp.tool()
async def list_scheduled_tasks(ctx: Context = None) -> str:
    """
    📋 查看定时任务列表
    
    Returns:
        所有定时任务列表
    """
    try:
        global scheduler
        if scheduler is None:
            return "暂无定时任务"
        
        jobs = scheduler.list_jobs()
        
        if not jobs:
            return "暂无定时任务"
        
        report = "# 📋 定时任务列表\n\n"
        report += f"共 {len(jobs)} 个任务\n\n"
        
        for i, job in enumerate(jobs, 1):
            status = "✅ 启用" if job.enabled else "⏸️ 禁用"
            report += f"## {i}. {job.name}\n"
            report += f"- **ID:** `{job.id}`\n"
            report += f"- **平台:** {job.platform}\n"
            report += f"- **类型:** {job.task_type}\n"
            report += f"- **定时:** {job.schedule}\n"
            report += f"- **状态:** {status}\n"
            report += f"- **运行次数:** {job.run_count}\n\n"
        
        return report
    
    except Exception as e:
        logger.error(f"获取任务列表失败: {e}")
        return f"❌ 获取任务列表失败: {str(e)}"

# ========== 辅助函数 ==========

async def _store_content_batch(content_items: List[ContentItem]):
    """批量存储内容到向量库"""
    try:
        # 生成向量
        for item in content_items:
            if not item.embedding:
                text = item.get_text_for_embedding()
                item.embedding = embedding_service.encode(text)
        
        # 存储到向量库
        vector_store.add_contents(content_items)
        logger.info(f"已存储 {len(content_items)} 条内容到向量库")
    except Exception as e:
        logger.error(f"存储内容失败: {e}")

# ========== 系统工具 ==========

@mcp.tool()
async def scraper_list_platforms() -> str:
    """列出所有支持的平台和工具"""
    return """
# 🚀 AI Content Agent - 支持的平台

## 📱 基础抓取工具

### 中文平台
- `scraper_douyin_search` - 抖音搜索
- `scraper_xiaohongshu_search` - 小红书搜索
- `scraper_bilibili_search` - B站搜索
- `scraper_zhihu_search` - 知乎搜索
- `scraper_wechat_search` - 公众号搜索

### 国际平台
- `scraper_youtube_search` - YouTube搜索
- `scraper_reddit_search` - Reddit搜索

## 🤖 AI级工具

### 内容发现
- `get_trending_topics` - 获取热门话题 🔥
- `get_hot_videos` - 获取话题热门内容 🎬

### 创作者分析
- `summarize_creator` - 创作者内容分析 👤

### 对比分析
- `compare_platforms` - 跨平台内容对比 📊

### 知识库
- `semantic_search` - 语义搜索已抓取内容 🔍

### 自动调度
- `schedule_crawl` - 创建定时任务 ⏰
- `list_scheduled_tasks` - 查看定时任务 📋

## 💡 使用建议

1. **发现热点**: 先用 `get_trending_topics` 发现热点
2. **深入分析**: 用 `get_hot_videos` 分析爆款
3. **自动跟踪**: 用 `schedule_crawl` 设置自动抓取
4. **知识管理**: 所有内容自动向量化，支持语义搜索
"""

@mcp.tool()
async def scraper_health_check() -> str:
    """系统健康检查"""
    status = []
    
    # 检查各平台
    for name, scraper in scrapers.items():
        try:
            await scraper.health_check()
            status.append(f"✅ {name}")
        except:
            status.append(f"⚠️ {name}")
    
    # 检查向量库
    try:
        stats = vector_store.get_stats()
        status.append(f"✅ 向量库: {stats.get('total_vectors', 0)} 条记录")
    except:
        status.append("⚠️ 向量库")
    
    return "# 🏥 系统状态\n\n" + "\n".join(status)

@mcp.tool()
async def get_system_stats() -> str:
    """获取系统统计"""
    try:
        stats = knowledge_search.get_stats()
        
        report = "# 📊 系统统计\n\n"
        report += f"**向量存储：** {stats.get('vector_store', {}).get('total_vectors', 0)} 条\n"
        report += f"**Embedding模型：** {stats.get('embedding_model', 'unknown')}\n"
        report += f"**最后更新：** {stats.get('last_updated', 'unknown')}\n\n"
        
        if scheduler:
            scheduler_stats = scheduler.get_stats()
            report += "## ⏰ 调度任务\n\n"
            report += f"- 总任务数：{scheduler_stats.get('total_jobs', 0)}\n"
            report += f"- 启用任务：{scheduler_stats.get('enabled_jobs', 0)}\n"
            report += f"- 运行状态：{'运行中' if scheduler_stats.get('running') else '已停止'}\n"
        
        return report
    except Exception as e:
        return f"❌ 获取统计失败: {str(e)}"

# ========== 启动入口 ==========

if __name__ == "__main__":
    # 启动调度器
    try:
        scheduler = ContentScheduler()
        scheduler.start()
        logger.info("调度器已启动")
    except Exception as e:
        logger.error(f"调度器启动失败: {e}")
    
    # 启动 MCP Server
    mcp.run(transport="http", host="0.0.0.0", port=3001)