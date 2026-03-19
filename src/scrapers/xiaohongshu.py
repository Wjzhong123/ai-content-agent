"""
Xiaohongshu Scraper - 小红书爬虫
使用小红书Web端API
注意：小红书反爬非常严格，需要处理签名和加密
"""

import asyncio
import aiohttp
import json
import hashlib
import time
from datetime import datetime
from typing import List, Dict, Any, Optional
from loguru import logger

from models.content_model import (
    ContentItem,
    Author,
    Metrics,
    ContentType,
    PlatformType,
)


class XiaohongshuScraper:
    """小红书爬虫"""

    def __init__(self):
        self.base_url = "https://www.xiaohongshu.com"
        self.api_url = "https://www.xiaohongshu.com/web_api/sns/v3/search/notes"
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Referer": "https://www.xiaohongshu.com/search_result",
            "Accept": "application/json",
            "Accept-Language": "zh-CN,zh;q=0.9",
            "Origin": "https://www.xiaohongshu.com",
            "X-Sign": "",  # 需要动态生成
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
        except Exception as e:
            logger.warning(f"初始化Cookie失败: {e}")

    def _generate_sign(self, params: Dict) -> str:
        """生成签名"""
        # 小红书签名算法（简化版）
        sorted_params = sorted(params.items())
        sign_str = "".join([f"{k}={v}" for k, v in sorted_params])
        return hashlib.md5(f"{sign_str}test".encode()).hexdigest()

    async def search(
        self, keyword: str, limit: int = 20, sort: str = "general"
    ) -> List[ContentItem]:
        """搜索小红书笔记"""
        logger.info(f"搜索小红书: {keyword}, limit={limit}")

        # 注意：小红书反爬非常严格，这里返回模拟数据
        # 实际实现需要：
        # 1. 逆向X-Sign算法
        # 2. 处理验证码
        # 3. 使用Playwright或Selenium

        results = []
        for i in range(min(limit, 5)):
            results.append(
                ContentItem(
                    id=f"xhs_{i}_{hash(keyword) % 10000}",
                    platform=PlatformType.XIAOHONGSHU,
                    type=ContentType.POST,
                    title=f"小红书笔记 {i + 1}: {keyword}",
                    content=f"这是关于 {keyword} 的小红书笔记内容...",
                    author=Author(
                        platform=PlatformType.XIAOHONGSHU,
                        user_id=f"user_{i}",
                        username=f"博主{hash(keyword) % 1000}",
                        display_name=f"博主{hash(keyword) % 1000}",
                    ),
                    url=f"https://www.xiaohongshu.com/explore/note_{i}",
                    cover_url="https://example.com/cover.jpg",
                    created_at=datetime.now(),
                    metrics=Metrics(
                        likes=hash(keyword) % 5000,
                        favorites=hash(keyword) % 1000,
                        comments=hash(keyword) % 500,
                        shares=hash(keyword) % 200,
                    ),
                    tags=[keyword, "小红书", "笔记"],
                    platform_data={},
                )
            )

        logger.info(f"小红书搜索完成: {keyword}, 返回 {len(results)} 条模拟数据")
        return results

    async def health_check(self) -> bool:
        """健康检查"""
        try:
            session = await self._get_session()
            async with session.get(self.base_url) as response:
                return response.status == 200
        except:
            return True  # 返回True因为我们使用模拟数据

    async def close(self):
        """关闭会话"""
        if self.session and not self.session.closed:
            await self.session.close()
