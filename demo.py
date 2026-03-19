#!/usr/bin/env python3
"""
AI Content Agent 演示脚本
使用模拟数据展示完整流程
"""

import asyncio
import sys
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent / "src"))

from models.content_model import ContentItem, Author, Metrics, ContentType, PlatformType
from output.markdown import MarkdownGenerator


def create_mock_content(
    platform: PlatformType, keyword: str, index: int
) -> ContentItem:
    """创建模拟内容"""
    platform_names = {
        PlatformType.BILIBILI: ("B站UP主", "视频教程"),
        PlatformType.ZHIHU: ("知乎大V", "精华回答"),
        PlatformType.DOUYIN: ("抖音博主", "短视频"),
        PlatformType.XIAOHONGSHU: ("小红书博主", "种草笔记"),
    }

    author_name, content_type = platform_names.get(platform, ("用户", "内容"))

    return ContentItem(
        id=f"{platform.value}_mock_{index}",
        platform=platform,
        type=ContentType.VIDEO
        if platform in [PlatformType.BILIBILI, PlatformType.DOUYIN]
        else ContentType.ARTICLE,
        title=f"【{content_type}】{keyword} - 第{index + 1}条内容",
        content=f"这是关于 {keyword} 的详细内容。本内容展示了AI Content Agent系统的完整流程，包括内容抓取、结构化存储和Markdown输出。\n\n这是模拟数据，用于演示系统功能。实际部署时，这里会包含从各平台抓取的原始内容。",
        author=Author(
            platform=platform,
            user_id=f"user_{index}",
            username=f"{author_name}{index}",
            display_name=f"{author_name}{index}",
            followers_count=10000 + index * 1000,
        ),
        url=f"https://example.com/{platform.value}/content_{index}",
        cover_url=f"https://via.placeholder.com/800x600?text={platform.value}+{index}",
        created_at=datetime.now(),
        metrics=Metrics(
            views=50000 + index * 10000,
            likes=3000 + index * 500,
            comments=500 + index * 100,
            shares=200 + index * 50,
            favorites=1000 + index * 200,
        ),
        tags=[keyword, platform.value, "AI", "教程"],
        platform_data={"mock": True, "index": index},
    )


async def demo():
    """运行演示"""
    print("=" * 70)
    print("🚀 AI Content Agent 系统演示")
    print("=" * 70)
    print()

    keyword = "人工智能学习"
    print(f"📌 搜索关键词: {keyword}")
    print()

    # 模拟多平台搜索
    platforms = [
        PlatformType.BILIBILI,
        PlatformType.ZHIHU,
        PlatformType.DOUYIN,
        PlatformType.XIAOHONGSHU,
    ]

    all_results = []

    for platform in platforms:
        print(f"🔍 从 {platform.value} 抓取...")

        # 模拟3条内容
        for i in range(3):
            content = create_mock_content(platform, keyword, i)
            all_results.append(content)
            print(f"  ✅ {content.title[:50]}...")

        print()

    print("-" * 70)
    print(f"📊 总共抓取: {len(all_results)} 条内容")
    print()

    # 生成Markdown
    print("📝 生成Markdown文件...")
    md_gen = MarkdownGenerator()
    markdown = md_gen.generate_content_list(all_results, keyword)

    # 保存
    output_dir = Path(__file__).parent / "scraped_content"
    filepath = md_gen.save_to_file(markdown, f"demo/{keyword}_搜索结果.md", output_dir)

    print(f"✅ Markdown已保存: {filepath}")
    print()

    # 统计
    print("📈 数据统计:")
    for platform in platforms:
        count = len([r for r in all_results if r.platform == platform])
        total_views = sum(
            [r.metrics.views for r in all_results if r.platform == platform]
        )
        print(f"  - {platform.value}: {count}条, {total_views:,}次浏览")

    print()
    print("=" * 70)
    print("✅ 演示完成！系统框架已验证")
    print("=" * 70)
    print()
    print("📋 项目状态:")
    print("  ✅ 架构设计: 三层架构完整")
    print("  ✅ 统一模型: ContentItem标准化")
    print("  ✅ Markdown输出: 已验证")
    print("  ⚠️  平台爬虫: B站/知乎/抖音需要进一步开发")
    print("  📦 GitHub仓库: https://github.com/Wjzhong123/ai-content-agent")
    print()
    print("💡 下一步建议:")
    print("  1. 完善各平台爬虫的反爬策略")
    print("  2. 添加Cookie管理和登录功能")
    print("  3. 部署到k8服务器进行实际测试")


if __name__ == "__main__":
    asyncio.run(demo())
