#!/usr/bin/env python3
"""
多平台完整测试
B站(真实) + 知乎/抖音/小红书(模拟)
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))

# 导入所有爬虫
from scrapers.bilibili_v3 import BilibiliScraperV3
from scrapers.zhihu_v3 import ZhihuScraperV3
from scrapers.douyin_v2 import DouyinScraperV2
from scrapers.xiaohongshu_v2 import XiaohongshuScraperV2
from output.markdown import MarkdownGenerator
from loguru import logger


async def test_all_platforms():
    """测试所有平台"""
    print("=" * 80)
    print("🚀 AI Content Agent - 多平台完整测试")
    print("=" * 80)
    print()

    keyword = "Python学习"
    all_results = []

    platforms = [
        ("B站", BilibiliScraperV3(), "真实数据"),
        ("知乎", ZhihuScraperV3(), "模拟数据"),
        ("抖音", DouyinScraperV2(), "模拟数据"),
        ("小红书", XiaohongshuScraperV2(), "模拟数据"),
    ]

    for name, scraper, data_type in platforms:
        print(f"🔍 正在抓取 {name}... ({data_type})")

        try:
            results = await scraper.search(keyword, limit=3)
            all_results.extend(results)

            print(f"   ✅ 成功: {len(results)} 条")

            for i, item in enumerate(results[:2], 1):
                print(f"      {i}. {item.title[:40]}...")

        except Exception as e:
            print(f"   ❌ 失败: {e}")

        finally:
            await scraper.close()

        print()

    print("-" * 80)
    print(f"📊 总共抓取: {len(all_results)} 条内容")
    print()

    # 生成Markdown
    print("📝 生成Markdown...")
    md_gen = MarkdownGenerator()
    markdown = md_gen.generate_content_list(all_results, keyword)

    output_dir = Path(__file__).parent / "scraped_content"
    filepath = md_gen.save_to_file(
        markdown, f"multi_platform/{keyword}_多平台搜索.md", output_dir
    )

    print(f"✅ 已保存: {filepath}")
    print(f"   文件大小: {Path(filepath).stat().st_size:,} bytes")
    print()

    # 显示统计
    print("📈 各平台统计:")
    from collections import Counter

    platform_counts = Counter([r.platform.value for r in all_results])
    for platform, count in platform_counts.items():
        total_views = sum(
            [r.metrics.views for r in all_results if r.platform.value == platform]
        )
        print(f"   - {platform}: {count}条, {total_views:,}次浏览")

    print()
    print("=" * 80)
    print("✅ 多平台测试完成！")
    print("=" * 80)
    print()
    print("💡 说明:")
    print("   • B站: 抓取真实数据")
    print("   • 知乎/抖音/小红书: 使用模拟数据（待完善）")
    print("   • 系统架构完整，可扩展更多平台")


if __name__ == "__main__":
    asyncio.run(test_all_platforms())
