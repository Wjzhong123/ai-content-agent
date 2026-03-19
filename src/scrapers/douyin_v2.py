"""
Douyin Scraper v2 - 模拟数据版本
抖音反爬严格，暂时使用模拟数据
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


class DouyinScraperV2:
    """抖音爬虫 v2 - 模拟数据版本"""

    def __init__(self):
        self.templates = [
            "这绝对是你没见过的{keyword}神器！",
            "{keyword}入门教程，3分钟学会",
            "{keyword}技巧分享，建议收藏",
            "{keyword}实战演示",
            "关于{keyword}，你必须知道的事",
        ]

    async def search(self, keyword: str, limit: int = 20) -> List[ContentItem]:
        """搜索抖音视频（模拟数据）"""
        logger.info(f"🚀 抖音搜索 v2: {keyword}")

        results = []

        for i in range(min(limit, 5)):
            title = random.choice(self.templates).format(keyword=keyword)

            result = ContentItem(
                id=f"douyin_sim_{i}_{hash(keyword) % 10000}",
                platform=PlatformType.DOUYIN,
                type=ContentType.VIDEO,
                title=title,
                content=f"这是一个关于{keyword}的抖音视频。\n\n(注：这是模拟数据)",
                author=Author(
                    platform=PlatformType.DOUYIN,
                    user_id=f"user_{i}",
                    username=f"抖音达人{random.randint(1000, 9999)}",
                    display_name=f"抖音达人{random.randint(1000, 9999)}",
                    followers_count=random.randint(10000, 500000),
                ),
                url=f"https://www.douyin.com/video/{random.randint(1000000000, 9999999999)}",
                duration=random.randint(15, 300),
                created_at=datetime.now(),
                metrics=Metrics(
                    views=random.randint(10000, 500000),
                    likes=random.randint(1000, 50000),
                    comments=random.randint(100, 5000),
                    shares=random.randint(50, 2000),
                ),
                tags=[keyword, "抖音", "热门"],
                platform_data={"simulated": True},
            )

            results.append(result)

        logger.info(
            f"✅ 抖音搜索完成: {keyword}, 找到 {len(results)} 条结果 (模拟数据)"
        )
        return results

    async def health_check(self) -> bool:
        return True

    async def close(self):
        pass


if __name__ == "__main__":

    async def test():
        print("=" * 60)
        print("🚀 抖音爬虫 v2 测试 (模拟数据)")
        print("=" * 60)

        scraper = DouyinScraperV2()
        results = await scraper.search("人工智能", limit=3)

        print(f"\n✅ 找到 {len(results)} 条结果\n")

        for i, item in enumerate(results, 1):
            print(f"{i}. {item.title}")
            print(f"   作者: {item.author.username}")
            print(f"   播放: {item.metrics.views:,}")
            print(f"   点赞: {item.metrics.likes:,}")
            print()

        print("=" * 60)
        print("✅ 测试完成 (模拟数据)")

    asyncio.run(test())
