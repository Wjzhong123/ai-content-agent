"""
Bilibili Scraper v3 - 使用反爬工具集
集成完整的反爬策略
"""

import asyncio
import aiohttp
import json
from datetime import datetime
from typing import List, Optional
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


class BilibiliScraperV3:
    """B站爬虫 v3 - 集成反爬工具"""

    def __init__(self):
        self.base_url = "https://api.bilibili.com"
        self.search_url = "https://api.bilibili.com/x/web-interface/search/all/v2"

        # 反爬工具
        self.fingerprint = BrowserFingerprint()
        self.cookie_manager = CookieManager("./data/bilibili_cookies.json")
        self.rate_limiter = RateLimiter(min_delay=2.0, max_delay=5.0)
        self.retry_strategy = RetryStrategy(max_retries=5, base_delay=2.0)

        self.session: Optional[aiohttp.ClientSession] = None

    async def _get_session(self) -> aiohttp.ClientSession:
        """获取会话"""
        if self.session is None or self.session.closed:
            headers = self.fingerprint.generate()
            self.session = aiohttp.ClientSession(headers=headers)
        return self.session

    async def search(self, keyword: str, limit: int = 20) -> List[ContentItem]:
        """搜索B站内容"""
        logger.info(f"🚀 B站搜索 v3: {keyword}")

        results = []
        page = 1

        while len(results) < limit:
            try:
                # 速率限制
                await self.rate_limiter.wait()

                # 构建参数
                params = {
                    "keyword": keyword,
                    "page": page,
                    "pagesize": min(20, limit - len(results)),
                }

                # 使用重试策略执行请求
                data = await self._fetch_search(params)

                if not data or data.get("code") != 0:
                    logger.warning("B站搜索无结果或出错")
                    break

                # 解析结果
                search_data = data.get("data", {})
                videos = search_data.get("result", [])

                if not videos:
                    logger.info("B站搜索无更多结果")
                    break

                for video in videos:
                    if len(results) >= limit:
                        break

                    if video.get("result_type") == "video":
                        content_item = self._parse_video(video)
                        if content_item:
                            results.append(content_item)

                page += 1

            except Exception as e:
                logger.error(f"B站搜索出错: {e}")
                break

        logger.info(f"✅ B站搜索完成: {keyword}, 找到 {len(results)} 条结果")
        return results

    async def _fetch_search(self, params: dict) -> Optional[dict]:
        """获取搜索结果（带重试）"""
        session = await self._get_session()

        for retry in range(self.retry_strategy.max_retries):
            try:
                # 生成新的指纹
                session._default_headers = self.fingerprint.generate()

                async with session.get(
                    self.search_url,
                    params=params,
                    timeout=aiohttp.ClientTimeout(total=30),
                ) as response:
                    if response.status == 412:
                        logger.warning(f"B站返回412，等待重试...")
                        # 增加延迟
                        self.rate_limiter.increase_delay()
                        delay = self.retry_strategy.calculate_delay(retry)
                        await asyncio.sleep(delay)
                        continue

                    if response.status == 403:
                        logger.error("B站返回403，可能被拉黑")
                        return None

                    if response.status != 200:
                        logger.warning(f"B站返回 {response.status}")
                        delay = self.retry_strategy.calculate_delay(retry)
                        await asyncio.sleep(delay)
                        continue

                    data = await response.json()

                    # 保存Cookie
                    if response.cookies:
                        cookies = {k: v.value for k, v in response.cookies.items()}
                        self.cookie_manager.set("bilibili", cookies)

                    return data

            except asyncio.TimeoutError:
                logger.warning(
                    f"请求超时，重试 {retry + 1}/{self.retry_strategy.max_retries}"
                )
                delay = self.retry_strategy.calculate_delay(retry)
                await asyncio.sleep(delay)

            except Exception as e:
                logger.error(f"请求出错: {e}")
                delay = self.retry_strategy.calculate_delay(retry)
                await asyncio.sleep(delay)

        return None

    def _parse_video(self, video: dict) -> Optional[ContentItem]:
        """解析视频"""
        try:
            data = video.get("data", {})
            if isinstance(data, list) and len(data) > 0:
                video_data = data[0]
            else:
                video_data = data

            if not video_data:
                return None

            bvid = video_data.get("bvid", "")
            title = (
                video_data.get("title", "")
                .replace('<em class="keyword">', "")
                .replace("</em>", "")
            )

            # 解析数字（处理"万"）
            def parse_count(s):
                if not s:
                    return 0
                s = str(s)
                if "万" in s:
                    return int(float(s.replace("万", "")) * 10000)
                try:
                    return int(s)
                except:
                    return 0

            metrics = Metrics(
                views=parse_count(video_data.get("play", "0")),
                likes=parse_count(video_data.get("like", "0")),
                favorites=parse_count(video_data.get("favorites", "0")),
                comments=parse_count(video_data.get("review", "0")),
                danmaku=parse_count(video_data.get("danmaku", "0")),
            )

            return ContentItem(
                id=f"bilibili_{bvid}",
                platform=PlatformType.BILIBILI,
                type=ContentType.VIDEO,
                title=title,
                content=video_data.get("description", ""),
                author=Author(
                    platform=PlatformType.BILIBILI,
                    user_id=str(video_data.get("mid", "")),
                    username=video_data.get("author", ""),
                    display_name=video_data.get("author", ""),
                ),
                url=f"https://www.bilibili.com/video/{bvid}",
                cover_url=video_data.get("pic", "").replace("//", "https://"),
                created_at=datetime.now(),
                metrics=metrics,
                tags=video_data.get("tag", "").split(","),
                platform_data=video_data,
            )

        except Exception as e:
            logger.error(f"解析视频失败: {e}")
            return None

    async def health_check(self) -> bool:
        """健康检查"""
        try:
            session = await self._get_session()
            async with session.get(
                f"{self.base_url}/x/web-interface/search/all/v2?keyword=test&limit=1"
            ) as response:
                return response.status == 200
        except:
            return False

    async def close(self):
        """关闭"""
        if self.session and not self.session.closed:
            await self.session.close()


# 测试代码
async def test():
    """测试"""
    print("=" * 60)
    print("🚀 B站爬虫 v3 测试")
    print("=" * 60)

    scraper = BilibiliScraperV3()

    try:
        results = await scraper.search("Python教程", limit=3)
        print(f"\n✅ 找到 {len(results)} 条结果")

        for i, item in enumerate(results, 1):
            print(f"\n{i}. {item.title[:50]}")
            print(f"   作者: {item.author.username}")
            print(f"   播放: {item.metrics.views:,}")

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
