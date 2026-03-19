#!/usr/bin/env python3
"""
B站爬虫测试脚本（修复版）
使用绝对导入，避免相对导入问题
"""

import asyncio
import sys
from pathlib import Path

# 添加项目路径到系统路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root / "src"))

from scrapers.bilibili import BilibiliScraper
from output.markdown import MarkdownGenerator


async def test_search():
    """测试搜索功能"""
    print("🚀 测试B站搜索功能...")
    print("-" * 50)

    scraper = BilibiliScraper()

    # 测试搜索
    keyword = "Python教程"
    limit = 5

    print(f"搜索关键词: {keyword}")
    print(f"请求数量: {limit}")
    print()

    try:
        results = await scraper.search(keyword, limit)

        print(f"✅ 搜索成功！找到 {len(results)} 条结果")
        print()

        # 显示结果
        for i, item in enumerate(results, 1):
            print(f"\n{i}. {item.title[:60]}...")
            print(f"   作者: {item.author.username}")
            print(f"   播放: {item.metrics.views:,}")
            print(f"   点赞: {item.metrics.likes:,}")
            print(f"   链接: {item.url}")

        # 生成Markdown
        print("\n" + "-" * 50)
        print("📝 生成Markdown...")

        md_gen = MarkdownGenerator()
        markdown = md_gen.generate_content_list(results, keyword)

        # 保存
        output_dir = project_root / "scraped_content"
        filename = f"bilibili/test_search_{keyword}.md"
        filepath = md_gen.save_to_file(markdown, filename, output_dir)

        print(f"✅ Markdown已保存: {filepath}")

        # 显示Markdown预览
        print("\n📄 Markdown预览（前500字符）：")
        print(markdown[:500])

    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback

        traceback.print_exc()

    finally:
        await scraper.close()


async def main():
    """主函数"""
    print("=" * 60)
    print("🎬 B站爬虫测试（修复版）")
    print("=" * 60)
    print()

    # 运行测试
    await test_search()

    print("\n" + "=" * 60)
    print("✅ 测试完成！")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
