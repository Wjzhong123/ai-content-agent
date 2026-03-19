"""
Bilibili Scraper - B站真实爬虫
使用B站公开API，无需登录即可搜索和获取视频信息

B站API文档: https://github.com/SocialSisterYi/bilibili-API-collect
"""

import asyncio
import aiohttp
import json
from datetime import datetime
from typing import List, Dict, Any, Optional
from urllib.parse import urlencode
from loguru import logger

from models.content_model import (
    ContentItem,
    Author,
    Metrics,
    ContentType,
    PlatformType,
)


class BilibiliScraper:
    """B站爬虫 - 基于官方API"""

    def __init__(self):
        self.base_url = "https://api.bilibili.com"
        self.search_url = "https://api.bilibili.com/x/web-interface/search/type"
        self.video_url = "https://api.bilibili.com/x/web-interface/view"
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Referer": "https://search.bilibili.com/",
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "zh-CN,zh;q=0.9",
            "Accept-Encoding": "gzip, deflate, br",
        }
        self.session: Optional[aiohttp.ClientSession] = None

    async def _get_session(self) -> aiohttp.ClientSession:
        """获取或创建HTTP会话"""
        if self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession(headers=self.headers)
        return self.session

    async def search(
        self, keyword: str, limit: int = 20, search_type: str = "video"
    ) -> List[ContentItem]:
        """
        搜索B站视频

        Args:
            keyword: 搜索关键词
            limit: 返回数量
            search_type: 搜索类型 (video/bangumi/live)

        Returns:
            ContentItem列表
        """
        logger.info(f"搜索B站: {keyword}, limit={limit}")

        results = []
        page = 1

        while len(results) < limit:
            try:
                session = await self._get_session()

                params = {
                    "search_type": search_type,
                    "keyword": keyword,
                    "page": page,
                    "pagesize": min(20, limit - len(results)),
                }

                async with session.get(self.search_url, params=params) as response:
                    if response.status != 200:
                        logger.error(f"B站搜索失败: HTTP {response.status}")
                        break

                    data = await response.json()

                    if data.get("code") != 0:
                        logger.error(f"B站API错误: {data.get('message')}")
                        break

                    videos = data.get("data", {}).get("result", [])

                    if not videos:
                        break

                    for video in videos:
                        if len(results) >= limit:
                            break

                        content_item = self._parse_search_result(video)
                        if content_item:
                            results.append(content_item)

                    page += 1

                    # 防止请求过快
                    await asyncio.sleep(0.5)

            except Exception as e:
                logger.error(f"B站搜索出错: {e}")
                break

        logger.info(f"B站搜索完成: {keyword}, 找到 {len(results)} 条结果")
        return results

    def _parse_search_result(self, video: Dict) -> Optional[ContentItem]:
        """解析搜索结果为ContentItem"""
        try:
            # B站搜索结果字段
            bvid = video.get("bvid", "")
            aid = video.get("aid", 0)
            title = (
                video.get("title", "")
                .replace('<em class="keyword">', "")
                .replace("</em>", "")
            )

            # 作者信息
            author = Author(
                platform=PlatformType.BILIBILI,
                user_id=str(video.get("mid", 0)),
                username=video.get("author", ""),
                display_name=video.get("author", ""),
            )

            # 互动数据
            metrics = Metrics(
                views=video.get("play", 0),
                likes=video.get("like", 0),
                favorites=video.get("favorites", 0),
                comments=video.get("review", 0),
                danmaku=video.get("danmaku", 0),
            )

            # 构建ContentItem
            content_item = ContentItem(
                id=f"bilibili_{bvid}",
                platform=PlatformType.BILIBILI,
                type=ContentType.VIDEO,
                title=title,
                content=video.get("description", ""),
                author=author,
                url=f"https://www.bilibili.com/video/{bvid}",
                cover_url=video.get("pic", "").replace("//", "https://"),
                created_at=datetime.fromtimestamp(video.get("pubdate", 0)),
                metrics=metrics,
                tags=video.get("tag", "").split(","),
                platform_data=video,
            )

            return content_item

        except Exception as e:
            logger.error(f"解析B站搜索结果失败: {e}")
            return None

    async def get_video(self, bvid: str) -> Optional[ContentItem]:
        """
        获取B站视频详情

        Args:
            bvid: BV号

        Returns:
            ContentItem
        """
        logger.info(f"获取B站视频详情: {bvid}")

        try:
            session = await self._get_session()

            params = {"bvid": bvid}

            async with session.get(self.video_url, params=params) as response:
                if response.status != 200:
                    logger.error(f"获取B站视频失败: HTTP {response.status}")
                    return None

                data = await response.json()

                if data.get("code") != 0:
                    logger.error(f"B站API错误: {data.get('message')}")
                    return None

                video_data = data.get("data", {})

                return self._parse_video_detail(video_data)

        except Exception as e:
            logger.error(f"获取B站视频详情失败: {e}")
            return None

    def _parse_video_detail(self, video: Dict) -> Optional[ContentItem]:
        """解析视频详情"""
        try:
            bvid = video.get("bvid", "")
            owner = video.get("owner", {})
            stat = video.get("stat", {})

            # 作者信息
            author = Author(
                platform=PlatformType.BILIBILI,
                user_id=str(owner.get("mid", 0)),
                username=owner.get("name", ""),
                display_name=owner.get("name", ""),
                avatar_url=owner.get("face", ""),
            )

            # 互动数据
            metrics = Metrics(
                views=stat.get("view", 0),
                likes=stat.get("like", 0),
                favorites=stat.get("favorite", 0),
                shares=stat.get("share", 0),
                coins=stat.get("coin", 0),
                comments=stat.get("reply", 0),
                danmaku=stat.get("danmaku", 0),
            )

            # 标签
            tags = [t.get("tag_name", "") for t in video.get("tags", [])]

            # 构建ContentItem
            content_item = ContentItem(
                id=f"bilibili_{bvid}",
                platform=PlatformType.BILIBILI,
                type=ContentType.VIDEO,
                title=video.get("title", ""),
                content=video.get("desc", ""),
                author=author,
                url=f"https://www.bilibili.com/video/{bvid}",
                cover_url=video.get("pic", "").replace("//", "https://"),
                duration=video.get("duration", 0),
                created_at=datetime.fromtimestamp(video.get("pubdate", 0)),
                metrics=metrics,
                tags=tags,
                platform_data=video,
            )

            return content_item

        except Exception as e:
            logger.error(f"解析B站视频详情失败: {e}")
            return None

    async def health_check(self) -> bool:
        """健康检查"""
        try:
            session = await self._get_session()
            async with session.get(
                "https://api.bilibili.com/x/web-interface/search/type?search_type=video&keyword=test&page=1&pagesize=1"
            ) as response:
                return response.status == 200
        except:
            return False

    async def close(self):
        """关闭会话"""
        if self.session and not self.session.closed:
            await self.session.close()
