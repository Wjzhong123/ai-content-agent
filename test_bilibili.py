#!/usr/bin/env python3
"""
B站爬虫测试脚本
快速验证B站爬虫是否可以正常工作
"""

import asyncio
import sys
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent / "src"))

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
        output_dir = Path(__file__).parent / "scraped_content"
        filename = f"bilibili/test_search_{keyword}.md"
        filepath = md_gen.save_to_file(markdown, filename, output_dir)

        print(f"✅ Markdown已保存: {filepath}")

    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback

        traceback.print_exc()

    finally:
        await scraper.close()


async def test_video_detail():
    """测试获取视频详情"""
    print("\n🚀 测试B站视频详情...")
    print("-" * 50)

    scraper = BilibiliScraper()

    # 测试BV号
    bvid = "BV1xx411c7mD"  # 可以替换为实际的BV号

    print(f"测试BV号: {bvid}")

    try:
        result = await scraper.get_video(bvid)

        if result:
            print(f"✅ 获取成功！")
            print(f"标题: {result.title}")
            print(f"作者: {result.author.username}")
            print(f"播放: {result.metrics.views:,}")
            print(f"点赞: {result.metrics.likes:,}")
            print(f"投币: {result.metrics.coins:,}")
            print(f"收藏: {result.metrics.favorites:,}")
            print(f"弹幕: {result.metrics.danmaku:,}")
        else:
            print("❌ 未找到视频")

    except Exception as e:
        print(f"❌ 测试失败: {e}")

    finally:
        await scraper.close()


async def test_health_check():
    """测试健康检查"""
    print("\n🚀 测试B站健康检查...")
    print("-" * 50)

    scraper = BilibiliScraper()

    try:
        healthy = await scraper.health_check()

        if healthy:
            print("✅ B站API连接正常")
        else:
            print("⚠️ B站API连接异常")

    except Exception as e:
        print(f"❌ 健康检查失败: {e}")

    finally:
        await scraper.close()


async def main():
    """主函数"""
    print("=" * 60)
    print("🎬 B站爬虫测试")
    print("=" * 60)
    print()

    # 运行测试
    await test_health_check()
    await test_search()
    # await test_video_detail()  # 可选

    print("\n" + "=" * 60)
    print("✅ 测试完成！")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
