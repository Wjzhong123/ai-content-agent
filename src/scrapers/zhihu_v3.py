"""
Zhihu Scraper v3 - 使用模拟数据
知乎API限制严格，暂时使用模拟数据
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


class ZhihuScraperV3:
    """知乎爬虫 v3 - 模拟数据版本"""

    def __init__(self):
        self.base_url = "https://www.zhihu.com"
        # 模拟数据模板
        self.templates = [
            {
                "title": "如何系统学习{keyword}？",
                "content": "这是一个关于{keyword}的详细回答。首先需要了解基础知识，然后...",
                "type": "answer",
            },
            {
                "title": "{keyword}入门指南",
                "content": "本文介绍了{keyword}的基本概念和入门方法...",
                "type": "article",
            },
            {
                "title": "{keyword}有哪些值得推荐的学习资源？",
                "content": "推荐几个学习{keyword}的优质资源：1. 官方文档 2. 优质课程...",
                "type": "answer",
            },
        ]

    async def search(self, keyword: str, limit: int = 20) -> List[ContentItem]:
        """搜索知乎内容（模拟数据）"""
        logger.info(f"🚀 知乎搜索 v3: {keyword}")

        results = []

        for i in range(min(limit, len(self.templates))):
            template = self.templates[i % len(self.templates)]

            # 替换关键词
            title = template["title"].format(keyword=keyword)
            content = template["content"].format(keyword=keyword)

            # 生成模拟数据
            result = ContentItem(
                id=f"zhihu_sim_{i}_{hash(keyword) % 10000}",
                platform=PlatformType.ZHIHU,
                type=ContentType.ANSWER
                if template["type"] == "answer"
                else ContentType.ARTICLE,
                title=title,
                content=content
                + "\n\n(注：这是模拟数据，实际部署时会抓取真实知乎内容)",
                author=Author(
                    platform=PlatformType.ZHIHU,
                    user_id=f"user_{i}",
                    username=f"知乎用户{random.randint(1000, 9999)}",
                    display_name=f"知乎用户{random.randint(1000, 9999)}",
                    followers_count=random.randint(1000, 50000),
                ),
                url=f"https://www.zhihu.com/question/{random.randint(10000000, 99999999)}",
                created_at=datetime.now(),
                metrics=Metrics(
                    views=random.randint(10000, 100000),
                    likes=random.randint(100, 5000),
                    comments=random.randint(10, 500),
                ),
                tags=[keyword, "知乎", "学习"],
                platform_data={"simulated": True},
            )

            results.append(result)

        logger.info(
            f"✅ 知乎搜索完成: {keyword}, 找到 {len(results)} 条结果 (模拟数据)"
        )
        return results

    async def health_check(self) -> bool:
        """健康检查"""
        return True

    async def close(self):
        """关闭"""
        pass


# 测试
async def test():
    """测试"""
    print("=" * 60)
    print("🚀 知乎爬虫 v3 测试 (模拟数据)")
    print("=" * 60)

    scraper = ZhihuScraperV3()

    try:
        results = await scraper.search("人工智能学习", limit=3)
        print(f"\n✅ 找到 {len(results)} 条结果\n")

        for i, item in enumerate(results, 1):
            print(f"{i}. {item.title}")
            print(f"   作者: {item.author.username}")
            print(f"   点赞: {item.metrics.likes:,}")
            print(f"   浏览: {item.metrics.views:,}")
            print()

    except Exception as e:
        print(f"❌ 错误: {e}")

    print("=" * 60)
    print("✅ 测试完成 (模拟数据)")


if __name__ == "__main__":
    asyncio.run(test())
