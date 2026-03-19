"""
Xiaohongshu Scraper v2 - 模拟数据版本
小红书反爬严格，暂时使用模拟数据
"""

import asyncio
import random
from datetime import datetime
from typing import List
from loguru import logger

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from models.content_model import ContentItem, Author, Metrics, ContentType, PlatformType


class XiaohongshuScraperV2:
    """小红书爬虫 v2 - 模拟数据版本"""

    def __init__(self):
        self.templates = [
            "🔥{keyword}｜亲测有效的学习方法",
            "✨{keyword}入门｜新手必看",
            "💡关于{keyword}，我有话要说",
            "📚{keyword}干货分享",
            "🎯{keyword}避坑指南",
        ]

    async def search(self, keyword: str, limit: int = 20) -> List[ContentItem]:
        """搜索小红书笔记（模拟数据）"""
        logger.info(f"🚀 小红书搜索 v2: {keyword}")

        results = []

        for i in range(min(limit, 5)):
            title = random.choice(self.templates).format(keyword=keyword)

            result = ContentItem(
                id=f"xhs_sim_{i}_{hash(keyword) % 10000}",
                platform=PlatformType.XIAOHONGSHU,
                type=ContentType.POST,
                title=title,
                content=f"这是关于{keyword}的小红书笔记内容...\n\n(注：这是模拟数据)",
                author=Author(
                    platform=PlatformType.XIAOHONGSHU,
                    user_id=f"user_{i}",
                    username=f"小红书博主{random.randint(1000, 9999)}",
                    display_name=f"小红书博主{random.randint(1000, 9999)}",
                    followers_count=random.randint(5000, 100000),
                ),
                url=f"https://www.xiaohongshu.com/explore/{random.randint(100000000, 999999999)}",
                created_at=datetime.now(),
                metrics=Metrics(
                    views=random.randint(5000, 100000),
                    likes=random.randint(500, 10000),
                    comments=random.randint(50, 1000),
                    favorites=random.randint(100, 2000),
                ),
                tags=[keyword, "小红书", "笔记", "学习"],
                platform_data={"simulated": True},
            )

            results.append(result)

        logger.info(
            f"✅ 小红书搜索完成: {keyword}, 找到 {len(results)} 条结果 (模拟数据)"
        )
        return results

    async def health_check(self) -> bool:
        return True

    async def close(self):
        pass


if __name__ == "__main__":

    async def test():
        print("=" * 60)
        print("🚀 小红书爬虫 v2 测试 (模拟数据)")
        print("=" * 60)

        scraper = XiaohongshuScraperV2()
        results = await scraper.search("学习方法", limit=3)

        print(f"\n✅ 找到 {len(results)} 条结果\n")

        for i, item in enumerate(results, 1):
            print(f"{i}. {item.title}")
            print(f"   作者: {item.author.username}")
            print(f"   点赞: {item.metrics.likes:,}")
            print(f"   收藏: {item.metrics.favorites:,}")
            print()

        print("=" * 60)
        print("✅ 测试完成 (模拟数据)")

    asyncio.run(test())
