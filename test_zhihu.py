#!/usr/bin/env python3
"""
知乎爬虫测试脚本
"""

import asyncio
import sys
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent / "src"))

from scrapers.zhihu import ZhihuScraper
from output.markdown import MarkdownGenerator


async def test_zhihu():
    """测试知乎爬虫"""
    print("🚀 开始测试知乎爬虫...")
    print("=" * 60)

    scraper = ZhihuScraper()

    try:
        # 测试搜索
        keyword = "Python学习"
        print(f"\n🔍 搜索: {keyword}")
        results = await scraper.search(keyword, limit=3)

        print(f"✅ 找到 {len(results)} 条结果\n")

        # 显示结果
        for i, item in enumerate(results, 1):
            print(f"{i}. {item.title[:80]}")
            print(f"   作者: {item.author.username}")
            print(f"   类型: {item.type.value}")
            print(f"   点赞: {item.metrics.likes:,}")
            print(f"   评论: {item.metrics.comments:,}")
            print()

        # 生成Markdown
        if results:
            print("📝 生成Markdown文件...")
            md_gen = MarkdownGenerator()
            markdown = md_gen.generate_content_list(results, keyword)

            output_dir = Path(__file__).parent / "scraped_content"
            filepath = md_gen.save_to_file(
                markdown, f"zhihu/{keyword}_search.md", output_dir
            )

            print(f"✅ 已保存: {filepath}")

            # 显示Markdown预览
            print("\n📄 Markdown预览（前800字符）：")
            print("=" * 60)
            print(markdown[:800])
            print("=" * 60)

    except Exception as e:
        print(f"❌ 错误: {e}")
        import traceback

        traceback.print_exc()

    finally:
        await scraper.close()

    print("\n" + "=" * 60)
    print("✅ 测试完成！")


if __name__ == "__main__":
    asyncio.run(test_zhihu())
