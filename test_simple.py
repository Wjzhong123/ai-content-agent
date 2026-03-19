#!/usr/bin/env python3
"""
简化测试 - B站爬虫 + Markdown
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))

# 直接导入爬虫
exec(open("src/scrapers/bilibili_v3.py").read().split("if __name__")[0])

from output.markdown import MarkdownGenerator


async def test():
    """测试"""
    print("=" * 60)
    print("🚀 B站爬虫 + Markdown 测试")
    print("=" * 60)

    # 创建爬虫
    scraper = BilibiliScraperV3()

    try:
        # 搜索
        keyword = "Python入门"
        print(f"\n🔍 搜索: {keyword}")
        results = await scraper.search(keyword, limit=3)

        print(f"✅ 找到 {len(results)} 条结果\n")

        # 显示
        for i, item in enumerate(results, 1):
            print(f"{i}. {item.title[:50]}...")
            print(f"   作者: {item.author.username}")
            print(f"   播放: {item.metrics.views:,}")
            print(f"   点赞: {item.metrics.likes:,}")
            print()

        # 生成Markdown
        print("📝 生成Markdown...")
        md_gen = MarkdownGenerator()
        markdown = md_gen.generate_content_list(results, keyword)

        # 保存
        output_dir = Path(__file__).parent / "scraped_content"
        filepath = md_gen.save_to_file(
            markdown, f"test/{keyword}_搜索结果.md", output_dir
        )

        print(f"✅ 已保存: {filepath}")
        print(f"\n📄 预览:")
        print(markdown[:800])

    except Exception as e:
        print(f"❌ 错误: {e}")
        import traceback

        traceback.print_exc()

    finally:
        await scraper.close()

    print("\n" + "=" * 60)
    print("✅ 测试完成")


if __name__ == "__main__":
    asyncio.run(test())
