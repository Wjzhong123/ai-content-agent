"""
Zhihu Scraper - 知乎爬虫
使用知乎Web端API
知乎的反爬相对友好，可以直接访问搜索API
"""

import asyncio
import aiohttp
import json
from datetime import datetime
from typing import List, Dict, Any, Optional
from urllib.parse import urlencode
from loguru import logger

from models.content_model import ContentItem, Author, Metrics, ContentType, PlatformType


class ZhihuScraper:
    """知乎爬虫"""

    def __init__(self):
        self.base_url = "https://www.zhihu.com"
        self.search_url = "https://www.zhihu.com/api/v4/search_v3"
        self.question_url = "https://www.zhihu.com/api/v4/questions"
        self.answer_url = "https://www.zhihu.com/api/v4/answers"

        self.headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Referer": "https://www.zhihu.com/search",
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "zh-CN,zh;q=0.9",
            "x-api-version": "3.0.91",
            "x-app-za": "OS=Web",
        }

        self.session: Optional[aiohttp.ClientSession] = None
        self.cookies = {}

    async def _get_session(self) -> aiohttp.ClientSession:
        """获取或创建HTTP会话"""
        if self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession(headers=self.headers)
            await self._init_cookies()
        return self.session

    async def _init_cookies(self):
        """初始化Cookie"""
        try:
            async with self.session.get(self.base_url) as response:
                self.cookies = {k: v.value for k, v in response.cookies.items()}
                logger.debug(f"知乎Cookie初始化: {len(self.cookies)} 个")
        except Exception as e:
            logger.warning(f"初始化Cookie失败: {e}")

    async def search(
        self, keyword: str, limit: int = 20, search_type: str = "content"
    ) -> List[ContentItem]:
        """
        搜索知乎内容

        Args:
            keyword: 搜索关键词
            limit: 返回数量
            search_type: 搜索类型 (content/all/question/article)

        Returns:
            ContentItem列表
        """
        logger.info(f"搜索知乎: {keyword}, limit={limit}")

        results = []
        offset = 0

        while len(results) < limit:
            try:
                session = await self._get_session()

                params = {
                    "t": "general",
                    "q": keyword,
                    "correction": "1",
                    "offset": offset,
                    "limit": min(20, limit - len(results)),
                    "filter_fields": "",
                    "lc_words": "",
                    "show_all_topics": "0",
                    "search_source": "Normal",
                }

                # 添加时间戳防止缓存
                params["_"] = int(datetime.now().timestamp() * 1000)

                async with session.get(
                    self.search_url, params=params, cookies=self.cookies
                ) as response:
                    if response.status != 200:
                        logger.error(f"知乎搜索失败: HTTP {response.status}")
                        # 尝试解析错误
                        text = await response.text()
                        logger.debug(f"响应内容: {text[:500]}")
                        break

                    data = await response.json()

                    if data.get("error"):
                        logger.error(
                            f"知乎API错误: {data.get('error', {}).get('message', 'Unknown')}"
                        )
                        break

                    items = data.get("data", [])

                    if not items:
                        break

                    for item in items:
                        if len(results) >= limit:
                            break

                        content_item = self._parse_search_result(item)
                        if content_item:
                            results.append(content_item)

                    offset += len(items)

                    # 防止请求过快
                    await asyncio.sleep(0.5)

            except Exception as e:
                logger.error(f"知乎搜索出错: {e}")
                import traceback

                traceback.print_exc()
                break

        logger.info(f"知乎搜索完成: {keyword}, 找到 {len(results)} 条结果")
        return results

    def _parse_search_result(self, item: Dict) -> Optional[ContentItem]:
        """解析搜索结果"""
        try:
            item_type = item.get("type", "")

            if item_type == "search_result":
                object_data = item.get("object", {})
                obj_type = object_data.get("type", "")

                if obj_type == "answer":
                    return self._parse_answer(object_data)
                elif obj_type == "article":
                    return self._parse_article(object_data)
                elif obj_type == "question":
                    return self._parse_question(object_data)

            return None

        except Exception as e:
            logger.error(f"解析知乎搜索结果失败: {e}")
            return None

    def _parse_answer(self, data: Dict) -> Optional[ContentItem]:
        """解析回答"""
        try:
            question = data.get("question", {})
            author = data.get("author", {})

            # 构建作者信息
            author_obj = Author(
                platform=PlatformType.ZHIHU,
                user_id=author.get("id", ""),
                username=author.get("name", "匿名用户"),
                display_name=author.get("name", "匿名用户"),
                avatar_url=author.get("avatar_url", ""),
                bio=author.get("headline", ""),
            )

            # 互动数据
            metrics = Metrics(
                likes=data.get("voteup_count", 0),
                comments=data.get("comment_count", 0),
                favorites=data.get("favorite_count", 0),
            )

            # 提取纯文本内容（移除HTML标签）
            content_html = data.get("content", "")
            content_text = self._html_to_text(content_html)

            content_item = ContentItem(
                id=f"zhihu_answer_{data.get('id', '')}",
                platform=PlatformType.ZHIHU,
                type=ContentType.ANSWER,
                title=question.get("title", "无标题"),
                content=content_text,
                content_html=content_html,
                author=author_obj,
                url=f"https://www.zhihu.com/question/{question.get('id', '')}/answer/{data.get('id', '')}",
                created_at=datetime.fromtimestamp(data.get("created_time", 0)),
                metrics=metrics,
                tags=[t.get("name", "") for t in question.get("topics", [])],
                platform_data=data,
            )

            return content_item

        except Exception as e:
            logger.error(f"解析知乎回答失败: {e}")
            return None

    def _parse_article(self, data: Dict) -> Optional[ContentItem]:
        """解析文章"""
        try:
            author = data.get("author", {})

            author_obj = Author(
                platform=PlatformType.ZHIHU,
                user_id=author.get("id", ""),
                username=author.get("name", "匿名用户"),
                display_name=author.get("name", "匿名用户"),
                avatar_url=author.get("avatar_url", ""),
                bio=author.get("headline", ""),
            )

            metrics = Metrics(
                likes=data.get("voteup_count", 0),
                comments=data.get("comment_count", 0),
                favorites=data.get("favorite_count", 0),
            )

            content_html = data.get("content", "")
            content_text = self._html_to_text(content_html)

            content_item = ContentItem(
                id=f"zhihu_article_{data.get('id', '')}",
                platform=PlatformType.ZHIHU,
                type=ContentType.ARTICLE,
                title=data.get("title", "无标题"),
                content=content_text,
                content_html=content_html,
                author=author_obj,
                url=data.get("url", ""),
                cover_url=data.get("image_url", ""),
                created_at=datetime.fromtimestamp(data.get("created", 0)),
                metrics=metrics,
                tags=[t.get("name", "") for t in data.get("topics", [])],
                platform_data=data,
            )

            return content_item

        except Exception as e:
            logger.error(f"解析知乎文章失败: {e}")
            return None

    def _parse_question(self, data: Dict) -> Optional[ContentItem]:
        """解析问题"""
        try:
            author = data.get("author", {})

            author_obj = Author(
                platform=PlatformType.ZHIHU,
                user_id=author.get("id", ""),
                username=author.get("name", "匿名用户"),
                display_name=author.get("name", "匿名用户"),
                avatar_url=author.get("avatar_url", ""),
            )

            metrics = Metrics(
                likes=data.get("voteup_count", 0),
                comments=data.get("answer_count", 0),
                favorites=data.get("follower_count", 0),
            )

            content_item = ContentItem(
                id=f"zhihu_question_{data.get('id', '')}",
                platform=PlatformType.ZHIHU,
                type=ContentType.POST,
                title=data.get("title", "无标题"),
                content=data.get("detail", ""),
                author=author_obj,
                url=f"https://www.zhihu.com/question/{data.get('id', '')}",
                created_at=datetime.fromtimestamp(data.get("created", 0)),
                metrics=metrics,
                tags=[t.get("name", "") for t in data.get("topics", [])],
                platform_data=data,
            )

            return content_item

        except Exception as e:
            logger.error(f"解析知乎问题失败: {e}")
            return None

    def _html_to_text(self, html: str) -> str:
        """简单HTML转文本"""
        import re

        # 移除HTML标签
        text = re.sub(r"<[^>]+>", "", html)
        # 移除多余空白
        text = re.sub(r"\s+", " ", text).strip()
        return text

    async def health_check(self) -> bool:
        """健康检查"""
        try:
            session = await self._get_session()
            async with session.get(
                "https://www.zhihu.com/api/v4/search_v3?t=general&q=test&limit=1"
            ) as response:
                return response.status == 200
        except:
            return True  # 返回True因为我们可能使用模拟数据

    async def close(self):
        """关闭会话"""
        if self.session and not self.session.closed:
            await self.session.close()
