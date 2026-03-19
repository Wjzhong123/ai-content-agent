"""
Douyin Scraper - 抖音真实爬虫
使用抖音Web端API（无需登录）
注意：抖音反爬严格，需要处理签名和加密
"""

import asyncio
import aiohttp
import re
import json
from datetime import datetime
from typing import List, Dict, Any, Optional
from urllib.parse import urlencode, parse_qs, urlparse
from loguru import logger

from models.content_model import (
    ContentItem,
    Author,
    Metrics,
    ContentType,
    PlatformType,
)


class DouyinScraper:
    """抖音爬虫 - 基于Web端API"""

    def __init__(self):
        self.base_url = "https://www.douyin.com"
        self.search_url = "https://www.douyin.com/aweme/v1/web/general/search/"
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Referer": "https://www.douyin.com/",
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "zh-CN,zh;q=0.9",
        }
        self.session: Optional[aiohttp.ClientSession] = None
        # 获取初始Cookie
        self.cookies = {}

    async def _get_session(self) -> aiohttp.ClientSession:
        """获取或创建HTTP会话"""
        if self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession(headers=self.headers)
            # 获取初始cookie
            await self._init_cookies()
        return self.session

    async def _init_cookies(self):
        """初始化Cookie"""
        try:
            async with self.session.get(self.base_url) as response:
                self.cookies = {k: v.value for k, v in response.cookies.items()}
                logger.debug(f"抖音Cookie初始化完成: {len(self.cookies)} 个")
        except Exception as e:
            logger.warning(f"初始化Cookie失败: {e}")

    async def search(
        self, keyword: str, limit: int = 20, sort: str = "general"
    ) -> List[ContentItem]:
        """
        搜索抖音视频

        Args:
            keyword: 搜索关键词
            limit: 返回数量
            sort: 排序方式 (general/general/还有/)

        Returns:
            ContentItem列表
        """
        logger.info(f"搜索抖音: {keyword}, limit={limit}")

        results = []
        cursor = 0

        while len(results) < limit:
            try:
                session = await self._get_session()

                # 构建搜索URL
                params = {
                    "device_platform": "webapp",
                    "aid": "6383",
                    "channel": "channel_pc_web",
                    "search_channel": "aweme_general",
                    "sort_type": self._map_sort(sort),
                    "publish_time": "0",
                    "keyword": keyword,
                    "search_source": "normal_search",
                    "query_correct_type": "1",
                    "is_filter_search": "0",
                    "from_group_id": "",
                    "offset": cursor,
                    "count": min(10, limit - len(results)),
                    "pc_client_type": "1",
                    "version_code": "170400",
                    "version_name": "17.4.0",
                    "cookie_enabled": "true",
                    "screen_width": "1920",
                    "screen_height": "1080",
                    "browser_language": "zh-CN",
                    "browser_platform": "MacIntel",
                    "browser_name": "Chrome",
                    "browser_version": "120.0.0.0",
                    "browser_online": "true",
                    "engine_name": "Blink",
                    "engine_version": "120.0.0.0",
                    "os_name": "Mac OS",
                    "os_version": "10.15.7",
                    "cpu_core_num": "8",
                    "device_memory": "8",
                    "platform": "PC",
                    "downlink": "10",
                    "effective_type": "4g",
                    "round_trip_time": "50",
                    "webid": "",
                    "msToken": self._generate_ms_token(),
                }

                async with session.get(
                    self.search_url, params=params, cookies=self.cookies
                ) as response:
                    if response.status != 200:
                        logger.error(f"抖音搜索失败: HTTP {response.status}")
                        break

                    text = await response.text()

                    try:
                        data = json.loads(text)
                    except json.JSONDecodeError:
                        # 可能被反爬，返回HTML
                        logger.warning("抖音返回非JSON数据，可能被反爬")
                        break

                    if data.get("status_code") != 0:
                        logger.error(f"抖音API错误: {data.get('status_msg')}")
                        break

                    videos = data.get("data", [])

                    if not videos:
                        break

                    for video in videos:
                        if len(results) >= limit:
                            break

                        content_item = self._parse_search_result(video)
                        if content_item:
                            results.append(content_item)

                    # 更新cursor
                    cursor += len(videos)

                    # 防止请求过快
                    await asyncio.sleep(1)

            except Exception as e:
                logger.error(f"抖音搜索出错: {e}")
                break

        logger.info(f"抖音搜索完成: {keyword}, 找到 {len(results)} 条结果")
        return results

    def _map_sort(self, sort: str) -> str:
        """映射排序方式"""
        sort_map = {"general": "0", "time": "2", "hot": "1"}
        return sort_map.get(sort, "0")

    def _generate_ms_token(self) -> str:
        """生成msToken"""
        import random
        import string

        return "".join(random.choices(string.ascii_letters + string.digits, k=107))

    def _parse_search_result(self, video: Dict) -> Optional[ContentItem]:
        """解析搜索结果"""
        try:
            aweme_info = video.get("aweme_info", {})
            if not aweme_info:
                return None

            aweme_id = aweme_info.get("aweme_id", "")

            # 作者信息
            author_info = aweme_info.get("author", {})
            author = Author(
                platform=PlatformType.DOUYIN,
                user_id=str(author_info.get("uid", "")),
                username=author_info.get("nickname", ""),
                display_name=author_info.get("nickname", ""),
                avatar_url=author_info.get("avatar_thumb", {}).get("url_list", [""])[0]
                if author_info.get("avatar_thumb")
                else "",
            )

            # 统计数据
            stats = aweme_info.get("statistics", {})
            metrics = Metrics(
                views=stats.get("play_count", 0),
                likes=stats.get("digg_count", 0),
                shares=stats.get("share_count", 0),
                comments=stats.get("comment_count", 0),
            )

            # 构建ContentItem
            content_item = ContentItem(
                id=f"douyin_{aweme_id}",
                platform=PlatformType.DOUYIN,
                type=ContentType.VIDEO,
                title=aweme_info.get("desc", ""),
                content=aweme_info.get("desc", ""),
                author=author,
                url=f"https://www.douyin.com/video/{aweme_id}",
                cover_url=aweme_info.get("video", {})
                .get("cover", {})
                .get("url_list", [""])[0]
                if aweme_info.get("video")
                else "",
                duration=aweme_info.get("video", {}).get("duration", 0) // 1000,
                created_at=datetime.fromtimestamp(aweme_info.get("create_time", 0)),
                metrics=metrics,
                tags=[
                    t.get("hashtag_name", "")
                    for t in aweme_info.get("text_extra", [])
                    if t.get("hashtag_name")
                ],
                platform_data=aweme_info,
            )

            return content_item

        except Exception as e:
            logger.error(f"解析抖音搜索结果失败: {e}")
            return None

    async def health_check(self) -> bool:
        """健康检查"""
        try:
            session = await self._get_session()
            async with session.get(self.base_url) as response:
                return response.status == 200
        except:
            return False

    async def close(self):
        """关闭会话"""
        if self.session and not self.session.closed:
            await self.session.close()
