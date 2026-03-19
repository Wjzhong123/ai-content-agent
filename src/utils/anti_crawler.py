"""
Anti-Crawler Tools - 反爬虫工具集
提供通用的反爬策略支持
"""

import random
import time
import json
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from loguru import logger


class BrowserFingerprint:
    """浏览器指纹生成器"""

    def __init__(self):
        # 常见的浏览器指纹组合
        self.chrome_versions = ["120.0.0.0", "119.0.0.0", "118.0.0.0", "117.0.0.0"]
        self.firefox_versions = ["121.0", "120.0", "119.0"]
        self.safari_versions = ["17.2", "17.1", "17.0", "16.6"]

        self.platforms = [
            "Windows NT 10.0; Win64; x64",
            "Macintosh; Intel Mac OS X 10_15_7",
            "X11; Linux x86_64",
            "Windows NT 10.0; Win64; x64; rv:109.0",
        ]

        self.languages = ["zh-CN,zh;q=0.9", "zh-CN,zh;q=0.9,en;q=0.8", "en-US,en;q=0.9"]
        self.encodings = ["gzip, deflate, br", "gzip, deflate", "identity"]

    def generate(self) -> Dict:
        """生成随机浏览器指纹"""
        browser_type = random.choice(["chrome", "firefox", "safari"])
        platform = random.choice(self.platforms)

        if browser_type == "chrome":
            version = random.choice(self.chrome_versions)
            ua = f"Mozilla/5.0 ({platform}) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{version} Safari/537.36"
        elif browser_type == "firefox":
            version = random.choice(self.firefox_versions)
            if "rv:" in platform:
                ua = f"Mozilla/5.0 ({platform}) Gecko/20100101 Firefox/{version}"
            else:
                ua = f"Mozilla/5.0 ({platform}; rv:109.0) Gecko/20100101 Firefox/{version}"
        else:
            version = random.choice(self.safari_versions)
            ua = f"Mozilla/5.0 ({platform}) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/{version} Safari/605.1.15"

        return {
            "User-Agent": ua,
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": random.choice(self.languages),
            "Accept-Encoding": random.choice(self.encodings),
            "Connection": random.choice(["keep-alive", "close"]),
            "Upgrade-Insecure-Requests": "1",
            "Sec-Fetch-Dest": random.choice(["document", "empty"]),
            "Sec-Fetch-Mode": random.choice(["navigate", "cors"]),
            "Sec-Fetch-Site": random.choice(["same-origin", "none"]),
            "Cache-Control": random.choice(["max-age=0", "no-cache"]),
        }


class CookieManager:
    """Cookie管理器"""

    def __init__(self, storage_path: str = "./data/cookies.json"):
        self.storage_path = Path(storage_path)
        self.cookies: Dict[str, Dict] = {}
        self._load()

    def _load(self):
        """加载Cookie"""
        if self.storage_path.exists():
            try:
                with open(self.storage_path, "r", encoding="utf-8") as f:
                    self.cookies = json.load(f)
                logger.info(f"加载Cookie: {len(self.cookies)} 个平台")
            except Exception as e:
                logger.error(f"加载Cookie失败: {e}")

    def _save(self):
        """保存Cookie"""
        try:
            self.storage_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.storage_path, "w", encoding="utf-8") as f:
                json.dump(self.cookies, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"保存Cookie失败: {e}")

    def get(self, platform: str) -> Dict:
        """获取指定平台的Cookie"""
        return self.cookies.get(platform, {})

    def set(self, platform: str, cookies: Dict):
        """设置指定平台的Cookie"""
        self.cookies[platform] = {
            "cookies": cookies,
            "updated_at": datetime.now().isoformat(),
            "expires_at": (datetime.now() + timedelta(days=7)).isoformat(),
        }
        self._save()

    def is_valid(self, platform: str) -> bool:
        """检查Cookie是否有效"""
        if platform not in self.cookies:
            return False

        try:
            expires = datetime.fromisoformat(self.cookies[platform]["expires_at"])
            return expires > datetime.now()
        except:
            return False


class ProxyPool:
    """代理池管理器"""

    def __init__(self):
        self.proxies: List[Dict] = []
        self.current_index = 0

    def add_proxy(
        self,
        host: str,
        port: int,
        username: str = "",
        password: str = "",
        protocol: str = "http",
    ):
        """添加代理"""
        proxy = {
            "host": host,
            "port": port,
            "username": username,
            "password": password,
            "protocol": protocol,
            "fail_count": 0,
            "last_used": None,
        }
        self.proxies.append(proxy)

    def get_proxy(self) -> Optional[str]:
        """获取下一个可用代理"""
        if not self.proxies:
            return None

        # 轮询
        for _ in range(len(self.proxies)):
            proxy = self.proxies[self.current_index]
            self.current_index = (self.current_index + 1) % len(self.proxies)

            # 跳过失败过多的代理
            if proxy["fail_count"] < 3:
                proxy["last_used"] = datetime.now().isoformat()

                if proxy["username"]:
                    return f"{proxy['protocol']}://{proxy['username']}:{proxy['password']}@{proxy['host']}:{proxy['port']}"
                else:
                    return f"{proxy['protocol']}://{proxy['host']}:{proxy['port']}"

        return None

    def mark_fail(self, proxy_url: str):
        """标记代理失败"""
        for proxy in self.proxies:
            if proxy["host"] in proxy_url:
                proxy["fail_count"] += 1
                logger.warning(
                    f"代理失败: {proxy['host']}, 失败次数: {proxy['fail_count']}"
                )
                break

    def get_proxy_dict(self) -> Optional[Dict]:
        """获取代理字典（用于aiohttp）"""
        proxy_url = self.get_proxy()
        if proxy_url:
            return {"http": proxy_url, "https": proxy_url}
        return None


class RateLimiter:
    """速率限制器"""

    def __init__(self, min_delay: float = 1.0, max_delay: float = 3.0):
        self.min_delay = min_delay
        self.max_delay = max_delay
        self.last_request_time = 0
        self.request_count = 0

    async def wait(self):
        """等待适当时间"""
        delay = random.uniform(self.min_delay, self.max_delay)

        elapsed = time.time() - self.last_request_time
        if elapsed < delay:
            await asyncio.sleep(delay - elapsed)

        self.last_request_time = time.time()
        self.request_count += 1

    def increase_delay(self, factor: float = 1.5):
        """增加延迟（遇到反爬时）"""
        self.min_delay *= factor
        self.max_delay *= factor
        logger.info(f"增加请求延迟: {self.min_delay:.1f}s - {self.max_delay:.1f}s")


class RetryStrategy:
    """重试策略"""

    def __init__(self, max_retries: int = 3, base_delay: float = 1.0):
        self.max_retries = max_retries
        self.base_delay = base_delay

    def calculate_delay(self, retry_count: int) -> float:
        """计算重试延迟（指数退避+抖动）"""
        delay = self.base_delay * (2**retry_count)
        jitter = random.uniform(0, delay * 0.3)
        return delay + jitter

    async def execute(self, func, *args, **kwargs):
        """执行带重试的函数"""
        for retry in range(self.max_retries):
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                if retry < self.max_retries - 1:
                    delay = self.calculate_delay(retry)
                    logger.warning(
                        f"请求失败，{delay:.1f}秒后重试 ({retry + 1}/{self.max_retries}): {e}"
                    )
                    await asyncio.sleep(delay)
                else:
                    logger.error(f"请求失败，已达到最大重试次数: {e}")
                    raise

        return None


# 导入asyncio
import asyncio
