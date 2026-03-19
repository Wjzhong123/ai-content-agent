#!/usr/bin/env python3
"""
完整测试脚本
测试B站爬虫 + Markdown生成 + 文件保存
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))

from scrapers.bilibili_v3 import BilibiliScraperV3
from output.markdown import MarkdownGenerator
from knowledge.embedding import EmbeddingService
from knowledge.vector_store import VectorStore
from loguru import logger


async def test_full_pipeline():
    """测试完整流程"""
    print("=" * 70)
    print("🚀 AI Content Agent 完整流程测试")
    print("=" * 70)
    print()

    # 1. 抓取B站内容
    print("📥 Step 1: 抓取B站内容")
    print("-" * 70)

    bilibili_scraper = BilibiliScraperV3()
    keyword = "Python教程"

    try:
        print(f"搜索: {keyword}")
        results = await bilibili_scraper.search(keyword, limit=3)
        print(f"✅ 抓取成功: {len(results)} 条内容")

        for i, item in enumerate(results, 1):
            print(f"  {i}. {item.title[:50]}... ({item.metrics.views:,}播放)")
    except Exception as e:
        print(f"❌ 抓取失败: {e}")
        return
    finally:
        await bilibili_scraper.close()

    print()

    # 2. 生成Markdown
    print("📝 Step 2: 生成Markdown")
    print("-" * 70)

    md_gen = MarkdownGenerator()
    markdown = md_gen.generate_content_list(results, keyword)

    output_dir = Path(__file__).parent / "scraped_content"
    filepath = md_gen.save_to_file(markdown, f"test/{keyword}_搜索结果.md", output_dir)

    print(f"✅ Markdown已保存: {filepath}")
    print(f"📄 文件大小: {Path(filepath).stat().st_size:,} bytes")

    print()

    # 3. 显示预览
    print("📄 Step 3: Markdown预览")
    print("-" * 70)
    print(markdown[:1000])
    print("...")
    print(f"(共 {len(markdown):,} 字符)")

    print()

    # 4. 向量化（可选，如果安装了sentence-transformers）
    print("🧠 Step 4: 向量化（可选）")
    print("-" * 70)

    try:
        embedding_service = EmbeddingService()

        print("生成向量嵌入...")
        for item in results:
            text = item.get_text_for_embedding()
            item.embedding = embedding_service.encode(text)

        print(f"✅ 已向量化 {len(results)} 条内容")
        print(f"   向量维度: {len(results[0].embedding)}")

        # 5. 存储到向量库
        print("\n💾 Step 5: 存储到向量库")
        print("-" * 70)

        vector_store = VectorStore()
        count = vector_store.add_contents(results)

        print(f"✅ 已存储 {count} 条内容到向量库")

        # 显示向量库统计
        stats = vector_store.get_stats()
        print(f"   向量库状态: {stats}")

    except Exception as e:
        print(f"⚠️  向量化跳过: {e}")
        print("   (需要安装: pip install sentence-transformers)")

    print()
    print("=" * 70)
    print("✅ 完整流程测试完成！")
    print("=" * 70)
    print()
    print("📊 测试总结:")
    print("  ✅ B站爬虫: 成功")
    print("  ✅ Markdown生成: 成功")
    print("  ✅ 文件保存: 成功")
    print("  ⚠️  向量化: 可选（需安装依赖）")
    print()
    print(f"💾 输出文件: {filepath}")


if __name__ == "__main__":
    # 配置日志
    logger.add("logs/test_{time}.log", rotation="100 MB", retention="3 days")

    asyncio.run(test_full_pipeline())
