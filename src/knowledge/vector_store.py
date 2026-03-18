"""
Vector Store - 向量存储层
使用 Qdrant 作为向量数据库

Qdrant 特点：
- 开源、高性能
- 支持过滤搜索
- RESTful API
- 支持多租户
"""

import os
import uuid
from datetime import datetime
from typing import List, Dict, Any, Optional
from loguru import logger

from ..models.content_model import ContentItem


class VectorStore:
    """
    向量存储服务

    使用 Qdrant 存储内容向量，支持：
    - 语义搜索
    - 相似内容推荐
    - 内容去重
    - 标签聚类
    """

    def __init__(
        self, host: str = None, port: int = 6333, collection_name: str = "content"
    ):
        """
        初始化向量存储

        Args:
            host: Qdrant 服务地址
            port: Qdrant 服务端口
            collection_name: 集合名称
        """
        self.host = host or os.getenv("QDRANT_HOST", "localhost")
        self.port = port or int(os.getenv("QDRANT_PORT", "6333"))
        self.collection_name = collection_name
        self.client = None
        self.embedding_dim = 1024  # BGE-M3 默认维度

        logger.info(f"初始化向量存储: {self.host}:{self.port}/{collection_name}")

    def _get_client(self):
        """获取 Qdrant 客户端（延迟加载）"""
        if self.client is None:
            try:
                from qdrant_client import QdrantClient

                self.client = QdrantClient(host=self.host, port=self.port)

                # 确保集合存在
                self._ensure_collection()

            except ImportError:
                logger.warning("qdrant-client 未安装，使用内存存储")
                self.client = "memory"
            except Exception as e:
                logger.error(f"连接 Qdrant 失败: {e}，使用内存存储")
                self.client = "memory"

        return self.client

    def _ensure_collection(self):
        """确保集合存在"""
        try:
            from qdrant_client.models import Distance, VectorParams

            # 检查集合是否存在
            collections = self.client.get_collections()
            collection_names = [c.name for c in collections.collections]

            if self.collection_name not in collection_names:
                logger.info(f"创建集合: {self.collection_name}")

                self.client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config=VectorParams(
                        size=self.embedding_dim, distance=Distance.COSINE
                    ),
                )

                # 创建索引
                self._create_indexes()

        except Exception as e:
            logger.error(f"创建集合失败: {e}")

    def _create_indexes(self):
        """创建字段索引"""
        try:
            from qdrant_client.models import FieldIndexType

            # 为常用字段创建索引
            indexed_fields = ["platform", "type", "author_id", "created_at", "tags"]

            for field in indexed_fields:
                try:
                    self.client.create_payload_index(
                        collection_name=self.collection_name,
                        field_name=field,
                        field_schema=FieldIndexType.KEYWORD,
                    )
                except:
                    pass  # 索引可能已存在

        except Exception as e:
            logger.warning(f"创建索引失败: {e}")

    def add_content(self, content: ContentItem) -> str:
        """
        添加内容到向量存储

        Args:
            content: 内容对象

        Returns:
            内容ID
        """
        client = self._get_client()

        if client == "memory":
            return self._add_to_memory(content)

        try:
            from qdrant_client.models import PointStruct

            # 准备数据
            point_id = content.id
            vector = content.embedding or []

            if not vector:
                logger.warning(f"内容 {point_id} 没有向量，跳过存储")
                return None

            payload = {
                "title": content.title,
                "content": content.content[:2000],  # 限制长度
                "summary": content.summary or "",
                "platform": content.platform.value,
                "type": content.type.value,
                "author_id": content.author.user_id,
                "author_name": content.author.username,
                "url": content.url,
                "created_at": content.created_at.isoformat(),
                "crawled_at": content.crawled_at.isoformat(),
                "tags": content.tags,
                "keywords": content.keywords,
                "metrics": content.metrics.to_dict(),
                "language": content.language,
            }

            # 添加点
            self.client.upsert(
                collection_name=self.collection_name,
                points=[PointStruct(id=point_id, vector=vector, payload=payload)],
            )

            logger.debug(f"已添加内容到向量库: {point_id}")
            return point_id

        except Exception as e:
            logger.error(f"添加内容失败: {e}")
            return None

    def add_contents(self, contents: List[ContentItem]) -> int:
        """
        批量添加内容

        Args:
            contents: 内容列表

        Returns:
            成功添加数量
        """
        count = 0
        for content in contents:
            if self.add_content(content):
                count += 1
        return count

    def search_similar(
        self, query_vector: List[float], limit: int = 10, filter_dict: Dict = None
    ) -> List[Dict]:
        """
        向量相似度搜索

        Args:
            query_vector: 查询向量
            limit: 返回数量
            filter_dict: 过滤条件

        Returns:
            相似内容列表
        """
        client = self._get_client()

        if client == "memory":
            return self._search_memory(query_vector, limit)

        try:
            from qdrant_client.models import Filter

            # 构建过滤器
            search_filter = None
            if filter_dict:
                search_filter = Filter(**filter_dict)

            # 执行搜索
            results = self.client.search(
                collection_name=self.collection_name,
                query_vector=query_vector,
                limit=limit,
                query_filter=search_filter,
                with_payload=True,
                with_vectors=False,
            )

            # 格式化结果
            return [
                {"id": r.id, "score": r.score, "payload": r.payload} for r in results
            ]

        except Exception as e:
            logger.error(f"搜索失败: {e}")
            return []

    def search_by_text(
        self, text: str, embedding_service, limit: int = 10
    ) -> List[Dict]:
        """
        文本搜索（自动编码）

        Args:
            text: 搜索文本
            embedding_service: 编码服务
            limit: 返回数量

        Returns:
            相似内容列表
        """
        # 编码查询文本
        query_vector = embedding_service.encode(text)

        # 执行搜索
        return self.search_similar(query_vector, limit)

    def delete_content(self, content_id: str) -> bool:
        """
        删除内容

        Args:
            content_id: 内容ID

        Returns:
            是否成功
        """
        client = self._get_client()

        if client == "memory":
            return self._delete_from_memory(content_id)

        try:
            self.client.delete(
                collection_name=self.collection_name, points_selector=[content_id]
            )
            return True
        except Exception as e:
            logger.error(f"删除失败: {e}")
            return False

    def get_stats(self) -> Dict:
        """
        获取统计信息

        Returns:
            统计字典
        """
        client = self._get_client()

        if client == "memory":
            return self._get_memory_stats()

        try:
            collection = self.client.get_collection(self.collection_name)
            return {
                "total_vectors": collection.vectors_count,
                "indexed_vectors": collection.indexed_vectors_count,
                "status": collection.status,
            }
        except Exception as e:
            logger.error(f"获取统计失败: {e}")
            return {}

    # ========== 内存存储模式（备用） ==========

    def _add_to_memory(self, content: ContentItem) -> str:
        """添加到内存存储"""
        if not hasattr(self, "_memory_store"):
            self._memory_store = {}

        self._memory_store[content.id] = {
            "vector": content.embedding,
            "payload": content.dict(),
        }

        return content.id

    def _search_memory(self, query_vector: List[float], limit: int) -> List[Dict]:
        """内存搜索"""
        if not hasattr(self, "_memory_store"):
            return []

        # 计算相似度
        results = []
        query_vec = np.array(query_vector)

        for cid, data in self._memory_store.items():
            if data.get("vector"):
                vec = np.array(data["vector"])
                similarity = np.dot(query_vec, vec) / (
                    np.linalg.norm(query_vec) * np.linalg.norm(vec)
                )
                results.append(
                    {"id": cid, "score": float(similarity), "payload": data["payload"]}
                )

        # 排序并返回前limit个
        results.sort(key=lambda x: x["score"], reverse=True)
        return results[:limit]

    def _delete_from_memory(self, content_id: str) -> bool:
        """从内存删除"""
        if hasattr(self, "_memory_store") and content_id in self._memory_store:
            del self._memory_store[content_id]
            return True
        return False

    def _get_memory_stats(self) -> Dict:
        """获取内存统计"""
        count = len(getattr(self, "_memory_store", {}))
        return {
            "total_vectors": count,
            "mode": "memory",
            "note": "Using in-memory storage (Qdrant not available)",
        }
