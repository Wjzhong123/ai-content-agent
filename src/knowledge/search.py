"""
Knowledge Search - 知识搜索层
提供智能搜索和内容发现能力
"""

from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Set
from collections import Counter
from loguru import logger

from ..models.content_model import ContentItem, TrendingTopic, CreatorProfile
from .vector_store import VectorStore
from .embedding import EmbeddingService


class KnowledgeSearch:
    """
    知识搜索服务

    提供：
    - 语义搜索
    - 热门话题发现
    - 创作者分析
    - 内容推荐
    - 趋势分析
    """

    def __init__(
        self,
        vector_store: VectorStore = None,
        embedding_service: EmbeddingService = None,
    ):
        """
        初始化搜索服务
        """
        self.vector_store = vector_store or VectorStore()
        self.embedding = embedding_service or EmbeddingService()

        logger.info("初始化知识搜索服务")

    # ========== 语义搜索 ==========

    def semantic_search(
        self,
        query: str,
        limit: int = 10,
        platforms: List[str] = None,
        content_types: List[str] = None,
        date_range: tuple = None,
    ) -> List[Dict]:
        """
        语义搜索

        Args:
            query: 搜索查询
            limit: 返回数量
            platforms: 平台过滤
            content_types: 内容类型过滤
            date_range: 时间范围 (start, end)

        Returns:
            搜索结果列表
        """
        logger.info(f"语义搜索: {query}")

        # 构建过滤器
        filter_dict = {}
        if platforms:
            filter_dict["platform"] = {"in": platforms}
        if content_types:
            filter_dict["type"] = {"in": content_types}

        # 执行向量搜索
        results = self.vector_store.search_by_text(query, self.embedding, limit=limit)

        # 格式化结果
        formatted = []
        for r in results:
            payload = r.get("payload", {})
            formatted.append(
                {
                    "id": r["id"],
                    "title": payload.get("title", ""),
                    "platform": payload.get("platform", ""),
                    "author": payload.get("author_name", ""),
                    "url": payload.get("url", ""),
                    "similarity_score": r["score"],
                    "tags": payload.get("tags", []),
                    "created_at": payload.get("created_at", ""),
                    "summary": payload.get("summary", "")[:200]
                    if payload.get("summary")
                    else "",
                }
            )

        return formatted

    def search_by_keywords(
        self, keywords: List[str], match_all: bool = False, limit: int = 20
    ) -> List[Dict]:
        """
        关键词搜索

        Args:
            keywords: 关键词列表
            match_all: 是否匹配所有关键词
            limit: 返回数量
        """
        logger.info(f"关键词搜索: {keywords}")

        # 这里可以实现基于关键词的精确搜索
        # 简化版本：使用语义搜索
        query = " ".join(keywords)
        return self.semantic_search(query, limit=limit)

    def find_similar_content(self, content_id: str, limit: int = 10) -> List[Dict]:
        """
        查找相似内容

        Args:
            content_id: 参考内容ID
            limit: 返回数量
        """
        logger.info(f"查找相似内容: {content_id}")

        # 获取参考内容的向量
        # 这里简化实现，实际应该从数据库查询
        return []

    # ========== 热门话题 ==========

    def get_trending_topics(
        self, platform: str = None, days: int = 7, limit: int = 20
    ) -> List[TrendingTopic]:
        """
        获取热门话题

        Args:
            platform: 平台过滤
            days: 时间范围（天）
            limit: 返回数量
        """
        logger.info(f"获取热门话题: platform={platform}, days={days}")

        # 模拟热门话题数据
        # 实际应该从数据库聚合分析
        topics = []

        # 示例话题
        trending = [
            ("AI工具", 95.5),
            ("副业赚钱", 88.2),
            ("ChatGPT", 82.1),
            ("短视频运营", 78.9),
            ("个人成长", 75.3),
            ("编程学习", 72.8),
            ("职场技巧", 68.5),
            ("投资理财", 65.2),
            ("生活方式", 62.1),
            ("科技资讯", 58.9),
        ]

        for i, (topic, score) in enumerate(trending[:limit]):
            topics.append(
                TrendingTopic(
                    topic=topic,
                    platform=platform or "all",
                    hot_score=score,
                    content_count=int(score * 10),
                    crawled_at=datetime.now(),
                )
            )

        return topics

    def get_trending_by_platform(
        self, platforms: List[str], limit: int = 10
    ) -> Dict[str, List[TrendingTopic]]:
        """
        获取各平台的热门话题

        Args:
            platforms: 平台列表
            limit: 每个平台返回数量
        """
        result = {}
        for platform in platforms:
            result[platform] = self.get_trending_topics(platform=platform, limit=limit)
        return result

    # ========== 创作者分析 ==========

    def analyze_creator(
        self, author_id: str, platform: str
    ) -> Optional[CreatorProfile]:
        """
        分析创作者档案

        Args:
            author_id: 作者ID
            platform: 平台
        """
        logger.info(f"分析创作者: {author_id} @ {platform}")

        # 实际应该从数据库查询该作者的所有内容
        # 这里返回模拟数据
        return None

    def get_top_creators(
        self, platform: str = None, topic: str = None, limit: int = 10
    ) -> List[Dict]:
        """
        获取热门创作者

        Args:
            platform: 平台过滤
            topic: 话题过滤
            limit: 返回数量
        """
        logger.info(f"获取热门创作者: platform={platform}, topic={topic}")

        # 模拟数据
        creators = [
            {
                "user_id": f"creator_{i}",
                "username": f"创作者{i}",
                "platform": platform or "douyin",
                "followers": 100000 + i * 10000,
                "total_content": 500 + i * 50,
                "avg_engagement": 5.5 + i * 0.5,
                "topics": ["科技", "生活", "创意"],
            }
            for i in range(1, limit + 1)
        ]

        return creators

    # ========== 内容推荐 ==========

    def recommend_content(
        self, user_interests: List[str], history: List[str] = None, limit: int = 10
    ) -> List[Dict]:
        """
        基于兴趣推荐内容

        Args:
            user_interests: 用户兴趣标签
            history: 浏览历史
            limit: 返回数量
        """
        logger.info(f"内容推荐: interests={user_interests}")

        # 构建查询
        query = " ".join(user_interests)

        # 执行搜索
        results = self.semantic_search(query, limit=limit * 2)

        # 过滤已浏览内容
        if history:
            results = [r for r in results if r["id"] not in history]

        return results[:limit]

    def get_content_by_topic(
        self, topic: str, limit: int = 20, sort_by: str = "relevance"
    ) -> List[Dict]:
        """
        获取话题相关内容

        Args:
            topic: 话题
            limit: 返回数量
            sort_by: 排序方式 relevance/time/engagement
        """
        logger.info(f"获取话题内容: {topic}")

        return self.semantic_search(topic, limit=limit)

    # ========== 对比分析 ==========

    def compare_platforms(self, topic: str, platforms: List[str]) -> Dict:
        """
        跨平台对比话题

        Args:
            topic: 话题
            platforms: 平台列表

        Returns:
            对比分析结果
        """
        logger.info(f"跨平台对比: {topic} on {platforms}")

        result = {"topic": topic, "platforms": {}, "summary": ""}

        for platform in platforms:
            # 搜索该平台的内容
            content = self.semantic_search(topic, limit=100, platforms=[platform])

            if content:
                # 计算统计
                total_views = sum(c.get("metrics", {}).get("views", 0) for c in content)
                total_engagement = sum(
                    c.get("metrics", {}).get("likes", 0) for c in content
                )

                # 提取标签
                all_tags = []
                for c in content:
                    all_tags.extend(c.get("tags", []))
                top_tags = Counter(all_tags).most_common(5)

                result["platforms"][platform] = {
                    "content_count": len(content),
                    "total_views": total_views,
                    "total_engagement": total_engagement,
                    "avg_engagement_rate": total_engagement / total_views
                    if total_views > 0
                    else 0,
                    "top_tags": top_tags,
                    "top_content": content[:5],
                }

        # 生成对比摘要
        result["summary"] = self._generate_comparison_summary(result)

        return result

    def _generate_comparison_summary(self, data: Dict) -> str:
        """生成对比摘要"""
        platforms = data.get("platforms", {})

        if not platforms:
            return "暂无数据"

        summary = f"话题『{data['topic']}』跨平台分析:\n\n"

        for platform, stats in platforms.items():
            summary += f"【{platform}】\n"
            summary += f"- 内容数: {stats.get('content_count', 0)}\n"
            summary += f"- 总浏览: {stats.get('total_views', 0):,}\n"
            summary += f"- 互动率: {stats.get('avg_engagement_rate', 0):.2%}\n"
            summary += f"- 热门标签: {', '.join([t[0] for t in stats.get('top_tags', [])[:3]])}\n\n"

        return summary

    # ========== 智能问答 ==========

    def answer_question(self, question: str, context_limit: int = 5) -> Dict:
        """
        基于知识库回答问题

        Args:
            question: 问题
            context_limit: 参考内容数量
        """
        logger.info(f"智能问答: {question}")

        # 搜索相关内容
        relevant = self.semantic_search(question, limit=context_limit)

        # 构建上下文
        context = []
        for r in relevant:
            context.append(
                {
                    "title": r["title"],
                    "content": r.get("summary", "")[:500],
                    "source": r["platform"],
                    "url": r["url"],
                }
            )

        return {
            "question": question,
            "context": context,
            "sources_count": len(relevant),
            "suggested_answer": f"基于 {len(relevant)} 条相关内容可以回答此问题",
        }

    # ========== 统计指标 ==========

    def get_stats(self) -> Dict:
        """
        获取知识库统计
        """
        # 获取向量存储统计
        vector_stats = self.vector_store.get_stats()

        return {
            "vector_store": vector_stats,
            "embedding_model": self.embedding.model_name,
            "embedding_device": self.embedding.device,
            "last_updated": datetime.now().isoformat(),
        }
