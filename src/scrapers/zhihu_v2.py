"""
Zhihu Scraper v2 - 改进版知乎爬虫
使用正确的API端点和参数
"""

import asyncio
import aiohttp
import json
from datetime import datetime
from typing import List, Optional
from urllib.parse import quote
from loguru import logger

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from models.content_model import ContentItem, Author, Metrics, ContentType, PlatformType
from utils.anti_crawler import (
    BrowserFingerprint,
    CookieManager,
    RateLimiter,
    RetryStrategy,
)


class ZhihuScraperV2:
    """知乎爬虫 v2"""

    def __init__(self):
        self.base_url = "https://www.zhihu.com"
        # 正确的搜索API
        self.search_url = "https://www.zhihu.com/api/v4/search_v3"
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Referer": "https://www.zhihu.com/search",
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "zh-CN,zh;q=0.9",
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
        }

        self.fingerprint = BrowserFingerprint()
        self.cookie_manager = CookieManager("./data/zhihu_cookies.json")
        self.rate_limiter = RateLimiter(min_delay=2.0, max_delay=4.0)
        self.retry_strategy = RetryStrategy(max_retries=3, base_delay=2.0)

        self.session: Optional[aiohttp.ClientSession] = None

    async def _get_session(self) -> aiohttp.ClientSession:
        """获取会话"""
        if self.session is None or self.session.closed:
            headers = self.fingerprint.generate()
            headers.update(self.headers)
            self.session = aiohttp.ClientSession(headers=headers)
        return self.session

    async def search(self, keyword: str, limit: int = 20) -> List[ContentItem]:
        """搜索知乎内容"""
        logger.info(f"🚀 知乎搜索 v2: {keyword}")

        results = []
        offset = 0

        while len(results) < limit:
            try:
                await self.rate_limiter.wait()

                # 正确的参数格式
                params = {
                    "gk_version": "gz-gaokao",
                    "t": "general",
                    "q": keyword,
                    "correction": "1",
                    "offset": offset,
                    "limit": min(20, limit - len(results)),
                    "filter_fields": "",
                    "lc_idx": str(offset),
                    "show_all_topics": "0",
                    "search_source": "Normal",
                }

                session = await self._get_session()

                async with session.get(
                    self.search_url,
                    params=params,
                    timeout=aiohttp.ClientTimeout(total=30),
                ) as response:
                    if response.status != 200:
                        logger.error(f"知乎搜索失败: HTTP {response.status}")
                        text = await response.text()
                        logger.debug(f"响应: {text[:500]}")
                        break

                    data = await response.json()

                    if data.get("error"):
                        logger.error(
                            f"知乎API错误: {data.get('error', {}).get('message', 'Unknown')}"
                        )
                        break

                    items = data.get("data", [])

                    if not items:
                        logger.info("知乎搜索无更多结果")
                        break

                    for item in items:
                        if len(results) >= limit:
                            break

                        content_item = self._parse_search_result(item)
                        if content_item:
                            results.append(content_item)

                    offset += len(items)

            except Exception as e:
                logger.error(f"知乎搜索出错: {e}")
                break

        logger.info(f"✅ 知乎搜索完成: {keyword}, 找到 {len(results)} 条结果")
        return results

    def _parse_search_result(self, item: dict) -> Optional[ContentItem]:
        """解析搜索结果"""
        try:
            item_type = item.get("type", "")

            if item_type != "search_result":
                return None

            obj = item.get("object", {})
            obj_type = obj.get("type", "")

            if obj_type == "answer":
                return self._parse_answer(obj)
            elif obj_type == "article":
                return self._parse_article(obj)
            elif obj_type == "question":
                return self._parse_question(obj)

            return None

        except Exception as e:
            logger.error(f"解析失败: {e}")
            return None

    def _parse_answer(self, data: dict) -> Optional[ContentItem]:
        """解析回答"""
        try:
            question = data.get("question", {})
            author = data.get("author", {})

            content_html = data.get("content", "")
            content_text = self._html_to_text(content_html)

            return ContentItem(
                id=f"zhihu_answer_{data.get('id', '')}",
                platform=PlatformType.ZHIHU,
                type=ContentType.ANSWER,
                title=question.get("title", "无标题"),
                content=content_text,
                author=Author(
                    platform=PlatformType.ZHIHU,
                    user_id=str(author.get("id", "")),
                    username=author.get("name", "匿名用户"),
                    display_name=author.get("name", "匿名用户"),
                ),
                url=f"https://www.zhihu.com/question/{question.get('id', '')}/answer/{data.get('id', '')}",
                created_at=datetime.fromtimestamp(data.get("created_time", 0)),
                metrics=Metrics(
                    likes=data.get("voteup_count", 0),
                    comments=data.get("comment_count", 0),
                ),
                tags=[],
                platform_data=data,
            )

        except Exception as e:
            logger.error(f"解析回答失败: {e}")
            return None

    def _parse_article(self, data: dict) -> Optional[ContentItem]:
        """解析文章"""
        try:
            author = data.get("author", {})

            content_html = data.get("content", "")
            content_text = self._html_to_text(content_html)

            return ContentItem(
                id=f"zhihu_article_{data.get('id', '')}",
                platform=PlatformType.ZHIHU,
                type=ContentType.ARTICLE,
                title=data.get("title", "无标题"),
                content=content_text,
                author=Author(
                    platform=PlatformType.ZHIHU,
                    user_id=str(author.get("id", "")),
                    username=author.get("name", "匿名用户"),
                    display_name=author.get("name", "匿名用户"),
                ),
                url=data.get("url", ""),
                created_at=datetime.fromtimestamp(data.get("created", 0)),
                metrics=Metrics(
                    likes=data.get("voteup_count", 0),
                    comments=data.get("comment_count", 0),
                ),
                tags=[],
                platform_data=data,
            )

        except Exception as e:
            logger.error(f"解析文章失败: {e}")
            return None

    def _parse_question(self, data: dict) -> Optional[ContentItem]:
        """解析问题"""
        try:
            author = data.get("author", {})

            return ContentItem(
                id=f"zhihu_question_{data.get('id', '')}",
                platform=PlatformType.ZHIHU,
                type=ContentType.POST,
                title=data.get("title", "无标题"),
                content=data.get("detail", ""),
                author=Author(
                    platform=PlatformType.ZHIHU,
                    user_id=str(author.get("id", "")),
                    username=author.get("name", "匿名用户"),
                    display_name=author.get("name", "匿名用户"),
                ),
                url=f"https://www.zhihu.com/question/{data.get('id', '')}",
                created_at=datetime.fromtimestamp(data.get("created", 0)),
                metrics=Metrics(
                    likes=data.get("voteup_count", 0),
                    comments=data.get("answer_count", 0),
                ),
                tags=[],
                platform_data=data,
            )

        except Exception as e:
            logger.error(f"解析问题失败: {e}")
            return None

    def _html_to_text(self, html: str) -> str:
        """HTML转文本"""
        import re

        text = re.sub(r"<[^>]+>", "", html)
        text = re.sub(r"\s+", " ", text).strip()
        return text[:500]  # 限制长度

    async def close(self):
        """关闭会话"""
        if self.session and not self.session.closed:
            await self.session.close()


# 测试
async def test():
    """测试"""
    print("=" * 60)
    print("🚀 知乎爬虫 v2 测试")
    print("=" * 60)

    scraper = ZhihuScraperV2()

    try:
        results = await scraper.search("Python学习", limit=3)
        print(f"\n✅ 找到 {len(results)} 条结果")

        for i, item in enumerate(results, 1):
            print(f"\n{i}. {item.title[:60]}")
            print(f"   作者: {item.author.username}")
            print(f"   类型: {item.type.value}")
            print(f"   点赞: {item.metrics.likes:,}")

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
