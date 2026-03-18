"""
Content Scheduler - 内容调度系统
实现自动抓取、定时任务、AI触发

让AI员工真正成为"员工"而非"工具"
"""

import asyncio
import json
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Callable
from dataclasses import dataclass, asdict
from loguru import logger
import schedule
import time
from threading import Thread


@dataclass
class CrawlJob:
    """
    抓取任务定义
    """

    id: str
    name: str
    platform: str
    task_type: str  # search / creator / trending / url
    params: Dict[str, Any]
    schedule: str  # cron表达式或描述
    enabled: bool = True
    last_run: Optional[datetime] = None
    next_run: Optional[datetime] = None
    run_count: int = 0
    created_at: datetime = None

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()


class ContentScheduler:
    """
    内容调度器

    功能：
    - 定时抓取任务
    - 热点监控
    - AI触发抓取
    - 任务队列管理
    """

    def __init__(
        self,
        scraper_factory: Callable = None,
        storage_path: str = "./scheduler_state.json",
    ):
        """
        初始化调度器
        """
        self.scraper_factory = scraper_factory
        self.storage_path = storage_path
        self.jobs: Dict[str, CrawlJob] = {}
        self.running = False
        self.scheduler_thread = None

        # 任务队列
        self.task_queue = asyncio.Queue()

        # 加载已有任务
        self._load_jobs()

        logger.info("内容调度器初始化完成")

    # ========== 任务管理 ==========

    def add_job(self, job: CrawlJob) -> str:
        """
        添加定时任务

        Args:
            job: 任务定义

        Returns:
            任务ID
        """
        self.jobs[job.id] = job
        self._register_schedule(job)
        self._save_jobs()

        logger.info(f"添加任务: {job.name} ({job.id})")
        return job.id

    def remove_job(self, job_id: str) -> bool:
        """删除任务"""
        if job_id in self.jobs:
            del self.jobs[job_id]
            self._save_jobs()
            return True
        return False

    def get_job(self, job_id: str) -> Optional[CrawlJob]:
        """获取任务"""
        return self.jobs.get(job_id)

    def list_jobs(self, platform: str = None) -> List[CrawlJob]:
        """列出所有任务"""
        jobs = list(self.jobs.values())
        if platform:
            jobs = [j for j in jobs if j.platform == platform]
        return jobs

    def update_job(self, job_id: str, **updates) -> bool:
        """更新任务"""
        if job_id not in self.jobs:
            return False

        job = self.jobs[job_id]
        for key, value in updates.items():
            if hasattr(job, key):
                setattr(job, key, value)

        self._save_jobs()
        return True

    # ========== 预设任务模板 ==========

    def create_daily_trending_job(self, platform: str, hour: int = 8) -> CrawlJob:
        """
        创建每日热门任务

        Args:
            platform: 平台
            hour: 执行小时
        """
        job = CrawlJob(
            id=f"{platform}_daily_trending",
            name=f"{platform} 每日热门",
            platform=platform,
            task_type="trending",
            params={"limit": 50},
            schedule=f"daily@{hour}:00",
        )
        return job

    def create_keyword_monitor_job(
        self, platform: str, keyword: str, frequency: str = "4h"
    ) -> CrawlJob:
        """
        创建关键词监控任务

        Args:
            platform: 平台
            keyword: 关键词
            frequency: 频率 (1h/4h/12h/daily)
        """
        job = CrawlJob(
            id=f"{platform}_monitor_{hash(keyword) % 10000}",
            name=f"{platform} 监控: {keyword}",
            platform=platform,
            task_type="search",
            params={"keyword": keyword, "limit": 20},
            schedule=frequency,
        )
        return job

    def create_creator_follow_job(
        self, platform: str, creator_id: str, frequency: str = "6h"
    ) -> CrawlJob:
        """
        创建创作者跟踪任务

        Args:
            platform: 平台
            creator_id: 创作者ID
            frequency: 频率
        """
        job = CrawlJob(
            id=f"{platform}_follow_{creator_id}",
            name=f"{platform} 跟踪: {creator_id}",
            platform=platform,
            task_type="creator",
            params={"creator_id": creator_id, "limit": 10},
            schedule=frequency,
        )
        return job

    # ========== 调度执行 ==========

    def start(self):
        """启动调度器"""
        if self.running:
            return

        self.running = True

        # 注册所有任务
        for job in self.jobs.values():
            if job.enabled:
                self._register_schedule(job)

        # 启动调度线程
        self.scheduler_thread = Thread(target=self._run_scheduler, daemon=True)
        self.scheduler_thread.start()

        logger.info("调度器已启动")

    def stop(self):
        """停止调度器"""
        self.running = False
        if self.scheduler_thread:
            self.scheduler_thread.join(timeout=5)
        logger.info("调度器已停止")

    def _run_scheduler(self):
        """调度器主循环"""
        while self.running:
            schedule.run_pending()
            time.sleep(60)  # 每分钟检查一次

    def _register_schedule(self, job: CrawlJob):
        """
        注册任务到调度器

        支持格式：
        - daily@HH:MM
        - hourly
        - every_N_hours
        - cron: 标准cron表达式
        """
        try:
            if job.schedule.startswith("daily@"):
                # 每日任务
                time_str = job.schedule.replace("daily@", "")
                hour, minute = map(int, time_str.split(":"))
                schedule.every().day.at(f"{hour:02d}:{minute:02d}").do(
                    self._execute_job, job.id
                )

            elif job.schedule == "hourly":
                # 每小时
                schedule.every().hour.do(self._execute_job, job.id)

            elif job.schedule.endswith("h"):
                # 每N小时
                hours = int(job.schedule[:-1])
                schedule.every(hours).hours.do(self._execute_job, job.id)

            elif job.schedule == "30m":
                # 每30分钟
                schedule.every(30).minutes.do(self._execute_job, job.id)

            elif job.schedule.startswith("cron:"):
                # Cron表达式（简化版）
                # TODO: 实现完整cron解析
                logger.warning(f"Cron表达式暂不支持: {job.schedule}")

        except Exception as e:
            logger.error(f"注册任务失败 {job.id}: {e}")

    def _execute_job(self, job_id: str):
        """
        执行任务
        """
        job = self.jobs.get(job_id)
        if not job or not job.enabled:
            return

        logger.info(f"执行任务: {job.name}")

        try:
            # 更新状态
            job.last_run = datetime.now()
            job.run_count += 1

            # 添加到队列
            asyncio.create_task(self._process_job(job))

            # 计算下次执行时间
            self._calculate_next_run(job)

            # 保存状态
            self._save_jobs()

        except Exception as e:
            logger.error(f"任务执行失败 {job_id}: {e}")

    async def _process_job(self, job: CrawlJob):
        """
        处理任务
        """
        logger.info(f"处理任务: {job.name}")

        try:
            # 获取爬虫
            if self.scraper_factory:
                scraper = self.scraper_factory(job.platform)

                # 执行抓取
                if job.task_type == "search":
                    result = await scraper.search(**job.params)
                elif job.task_type == "creator":
                    result = await scraper.get_creator_content(**job.params)
                elif job.task_type == "trending":
                    result = await scraper.get_trending(**job.params)
                else:
                    result = await scraper.fetch(**job.params)

                logger.info(
                    f"任务完成: {job.name}, 获取 {len(result) if isinstance(result, list) else 1} 条内容"
                )

                # 触发回调（如果有）
                await self._notify_completion(job, result)

        except Exception as e:
            logger.error(f"任务处理失败: {e}")

    def _calculate_next_run(self, job: CrawlJob):
        """计算下次执行时间"""
        # 简化计算
        if job.schedule.startswith("daily@"):
            job.next_run = job.last_run + timedelta(days=1)
        elif job.schedule == "hourly":
            job.next_run = job.last_run + timedelta(hours=1)
        elif job.schedule.endswith("h"):
            hours = int(job.schedule[:-1])
            job.next_run = job.last_run + timedelta(hours=hours)

    async def _notify_completion(self, job: CrawlJob, result: Any):
        """任务完成通知"""
        # TODO: 实现Webhook通知
        pass

    # ========== AI触发接口 ==========

    async def trigger_crawl(
        self, platform: str, task_type: str, params: Dict, priority: int = 5
    ) -> str:
        """
        AI触发抓取

        Args:
            platform: 平台
            task_type: 任务类型
            params: 参数
            priority: 优先级 (1-10)

        Returns:
            任务ID
        """
        job = CrawlJob(
            id=f"manual_{platform}_{int(time.time())}",
            name=f"AI触发: {task_type}",
            platform=platform,
            task_type=task_type,
            params=params,
            schedule="immediate",
        )

        # 立即执行
        asyncio.create_task(self._process_job(job))

        logger.info(f"AI触发任务: {job.id}")
        return job.id

    def get_stats(self) -> Dict:
        """获取统计信息"""
        total = len(self.jobs)
        enabled = sum(1 for j in self.jobs.values() if j.enabled)

        return {
            "total_jobs": total,
            "enabled_jobs": enabled,
            "running": self.running,
            "platforms": list(set(j.platform for j in self.jobs.values())),
        }

    # ========== 状态持久化 ==========

    def _save_jobs(self):
        """保存任务状态"""
        try:
            data = {
                job_id: {
                    **asdict(job),
                    "created_at": job.created_at.isoformat()
                    if job.created_at
                    else None,
                    "last_run": job.last_run.isoformat() if job.last_run else None,
                    "next_run": job.next_run.isoformat() if job.next_run else None,
                }
                for job_id, job in self.jobs.items()
            }

            with open(self.storage_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)

        except Exception as e:
            logger.error(f"保存任务失败: {e}")

    def _load_jobs(self):
        """加载任务状态"""
        try:
            if not os.path.exists(self.storage_path):
                return

            with open(self.storage_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            for job_id, job_data in data.items():
                # 转换时间字段
                for time_field in ["created_at", "last_run", "next_run"]:
                    if job_data.get(time_field):
                        job_data[time_field] = datetime.fromisoformat(
                            job_data[time_field]
                        )

                self.jobs[job_id] = CrawlJob(**job_data)

            logger.info(f"加载 {len(self.jobs)} 个任务")

        except Exception as e:
            logger.error(f"加载任务失败: {e}")


# ========== 快速创建函数 ==========


def create_default_schedule(scheduler: ContentScheduler):
    """
    创建默认调度任务
    """
    # 每日热门
    for platform in ["douyin", "xiaohongshu", "bilibili", "zhihu"]:
        job = scheduler.create_daily_trending_job(platform, hour=8)
        scheduler.add_job(job)

    # Reddit 趋势
    reddit_job = scheduler.create_daily_trending_job("reddit", hour=10)
    scheduler.add_job(reddit_job)

    # YouTube 新视频
    youtube_job = scheduler.create_daily_trending_job("youtube", hour=12)
    scheduler.add_job(youtube_job)

    logger.info("默认调度任务已创建")
