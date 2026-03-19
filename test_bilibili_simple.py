#!/usr/bin/env python3
"""
B站爬虫测试脚本（简化版）
"""

import asyncio
import sys
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent / "src"))

from scrapers.bilibili import BilibiliScraper
from output.markdown import MarkdownGenerator


async def test_bilibili():
    """测试B站爬虫"""
    print("🚀 开始测试B站爬虫...")
    print("=" * 60)

    scraper = BilibiliScraper()

    try:
        # 测试搜索
        keyword = "Python教程"
        print(f"\n🔍 搜索: {keyword}")
        results = await scraper.search(keyword, limit=3)

        print(f"✅ 找到 {len(results)} 条结果\n")

        # 显示结果
        for i, item in enumerate(results, 1):
            print(f"{i}. {item.title}")
            print(f"   作者: {item.author.username}")
            print(f"   播放: {item.metrics.views:,}")
            print(f"   点赞: {item.metrics.likes:,}")
            print()

        # 生成Markdown
        if results:
            print("📝 生成Markdown文件...")
            md_gen = MarkdownGenerator()
            markdown = md_gen.generate_content_list(results, keyword)

            output_dir = Path(__file__).parent / "scraped_content"
            filepath = md_gen.save_to_file(
                markdown, f"bilibili/{keyword}_search.md", output_dir
            )

            print(f"✅ 已保存: {filepath}")

            # 显示Markdown预览
            print("\n📄 Markdown预览:")
            print(markdown[:500])

    except Exception as e:
        print(f"❌ 错误: {e}")
        import traceback

        traceback.print_exc()

    finally:
        await scraper.close()

    print("\n" + "=" * 60)
    print("✅ 测试完成！")


if __name__ == "__main__":
    asyncio.run(test_bilibili())
