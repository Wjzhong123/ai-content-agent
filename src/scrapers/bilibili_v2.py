"""
Bilibili Scraper v2 - 改进版
更好的反爬处理策略
"""

import asyncio
import aiohttp
import json
import random
import time
from datetime import datetime
from typing import List, Dict, Any, Optional
from urllib.parse import urlencode
from loguru import logger

from models.content_model import ContentItem, Author, Metrics, ContentType, PlatformType


class BilibiliScraperV2:
    """B站爬虫 - 改进版，更好的反爬处理"""

    def __init__(self):
        self.base_url = "https://api.bilibili.com"
        self.search_url = "https://api.bilibili.com/x/web-interface/search/all/v2"
        self.video_url = "https://api.bilibili.com/x/web-interface/view"

        # 大量User-Agent轮换
        self.user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/121.0",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        ]

        # 基础Headers
        self.base_headers = {
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "none",
            "Sec-Fetch-User": "?1",
            "Cache-Control": "max-age=0",
        }

        self.session: Optional[aiohttp.ClientSession] = None
        self.request_count = 0
        self.last_request_time = 0

    def _get_headers(self) -> Dict:
        """生成随机Headers"""
        headers = self.base_headers.copy()
        headers["User-Agent"] = random.choice(self.user_agents)
        headers["Referer"] = f"https://search.bilibili.com/?t={int(time.time())}"
        return headers

    async def _rate_limit(self):
        """速率限制 - 防止请求过快"""
        min_interval = random.uniform(2, 4)  # 2-4秒间隔
        elapsed = time.time() - self.last_request_time
        if elapsed < min_interval:
            await asyncio.sleep(min_interval - elapsed)
        self.last_request_time = time.time()

    async def search(self, keyword: str, limit: int = 20) -> List[ContentItem]:
        """
        搜索B站内容

        改进点：
        1. 使用搜索类型分离（video/article/bili_user）
        2. 更好的错误处理
        3. 随机延迟
        4. 指数退避
        """
        logger.info(f"搜索B站 v2: {keyword}, limit={limit}")

        results = []
        page = 1
        retry_count = 0
        max_retries = 5

        async with aiohttp.ClientSession() as session:
            while len(results) < limit and retry_count < max_retries:
                try:
                    # 速率限制
                    await self._rate_limit()

                    # 构建参数
                    params = {
                        "keyword": keyword,
                        "page": page,
                        "pagesize": min(20, limit - len(results)),
                    }

                    headers = self._get_headers()

                    async with session.get(
                        self.search_url,
                        params=params,
                        headers=headers,
                        timeout=aiohttp.ClientTimeout(total=30),
                    ) as response:
                        if response.status == 412:
                            logger.warning(
                                f"B站返回412，触发反爬 (重试 {retry_count + 1}/{max_retries})"
                            )
                            retry_count += 1

                            # 指数退避 + 随机抖动
                            delay = (2**retry_count) + random.uniform(1, 3)
                            logger.info(f"等待 {delay:.1f} 秒后重试...")
                            await asyncio.sleep(delay)

                            # 更换User-Agent
                            continue

                        if response.status == 403:
                            logger.error("B站返回403，可能被拉黑")
                            break

                        if response.status != 200:
                            logger.error(f"B站搜索失败: HTTP {response.status}")
                            retry_count += 1
                            await asyncio.sleep(2**retry_count)
                            continue

                        data = await response.json()

                        if data.get("code") != 0:
                            logger.error(
                                f"B站API错误: {data.get('message', 'Unknown')}"
                            )
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

                            # 只处理视频类型
                            if video.get("result_type") == "video":
                                content_item = self._parse_video(video)
                                if content_item:
                                    results.append(content_item)

                        page += 1
                        retry_count = 0  # 成功后重置

                except asyncio.TimeoutError:
                    logger.warning("B站请求超时")
                    retry_count += 1
                    await asyncio.sleep(2**retry_count)

                except Exception as e:
                    logger.error(f"B站搜索出错: {e}")
                    retry_count += 1
                    await asyncio.sleep(2**retry_count)

        logger.info(f"B站搜索完成: {keyword}, 找到 {len(results)} 条结果")
        return results

    def _parse_video(self, video: Dict) -> Optional[ContentItem]:
        """解析视频数据"""
        try:
            data = video.get("data", {})
            if not data:
                return None

            # 获取第一个视频数据
            if isinstance(data, list) and len(data) > 0:
                video_data = data[0]
            else:
                video_data = data

            bvid = video_data.get("bvid", "")
            title = (
                video_data.get("title", "")
                .replace('<em class="keyword">', "")
                .replace("</em>", "")
            )

            author = Author(
                platform=PlatformType.BILIBILI,
                user_id=str(video_data.get("mid", "")),
                username=video_data.get("author", ""),
                display_name=video_data.get("author", ""),
            )

            metrics = Metrics(
                views=self._parse_count(video_data.get("play", "0")),
                likes=self._parse_count(video_data.get("like", "0")),
                favorites=self._parse_count(video_data.get("favorites", "0")),
                comments=self._parse_count(video_data.get("review", "0")),
                danmaku=self._parse_count(video_data.get("danmaku", "0")),
            )

            content_item = ContentItem(
                id=f"bilibili_{bvid}",
                platform=PlatformType.BILIBILI,
                type=ContentType.VIDEO,
                title=title,
                content=video_data.get("description", ""),
                author=author,
                url=f"https://www.bilibili.com/video/{bvid}",
                cover_url=video_data.get("pic", "").replace("//", "https://"),
                duration=video_data.get("duration", 0),
                created_at=datetime.now(),  # B站搜索API不返回发布时间
                metrics=metrics,
                tags=video_data.get("tag", "").split(","),
                platform_data=video_data,
            )

            return content_item

        except Exception as e:
            logger.error(f"解析B站视频失败: {e}")
            return None

    def _parse_count(self, count_str: str) -> int:
        """解析计数（处理"万"等后缀）"""
        if not count_str:
            return 0

        count_str = str(count_str).strip()

        if "万" in count_str:
            try:
                return int(float(count_str.replace("万", "")) * 10000)
            except:
                return 0

        try:
            return int(count_str)
        except:
            return 0


# 测试代码
async def test_bilibili_v2():
    """测试B站爬虫v2"""
    print("🚀 测试B站爬虫 v2...")
    print("=" * 60)

    scraper = BilibiliScraperV2()

    try:
        keyword = "Python教程"
        print(f"\n🔍 搜索: {keyword}")
        results = await scraper.search(keyword, limit=3)

        print(f"✅ 找到 {len(results)} 条结果\n")

        for i, item in enumerate(results, 1):
            print(f"{i}. {item.title[:60]}...")
            print(f"   作者: {item.author.username}")
            print(f"   播放: {item.metrics.views:,}")
            print(f"   点赞: {item.metrics.likes:,}")
            print(f"   URL: {item.url}")
            print()

    except Exception as e:
        print(f"❌ 错误: {e}")
        import traceback

        traceback.print_exc()

    print("=" * 60)
    print("✅ 测试完成")


if __name__ == "__main__":
    asyncio.run(test_bilibili_v2())
