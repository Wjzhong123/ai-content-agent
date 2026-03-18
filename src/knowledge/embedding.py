"""
Embedding Service - 文本向量化服务
使用 BGE-M3 模型（支持中英双语）

BGE-M3 特点：
- 多语言支持（100+语言）
- 多粒度（句子、段落、文档）
- 多任务（检索、聚类、分类）
- 开源免费，性能优秀
"""

import os
import json
import hashlib
from typing import List, Optional
import numpy as np
from loguru import logger


class EmbeddingService:
    """
    文本向量化服务

    使用 BGE-M3 模型，支持：
    - 中文/英文/多语言文本
    - 长文本（最长8192 tokens）
    - 高质量的语义表示
    """

    def __init__(self, model_name: str = "BAAI/bge-m3", device: str = None):
        """
        初始化 Embedding 服务

        Args:
            model_name: 模型名称，默认 BAAI/bge-m3
            device: 计算设备，默认自动选择（cuda > mps > cpu）
        """
        self.model_name = model_name
        self.device = device or self._auto_select_device()
        self.model = None
        self.tokenizer = None
        self._cache = {}  # 简单的内存缓存

        logger.info(f"初始化 Embedding 服务: {model_name}, 设备: {self.device}")

    def _auto_select_device(self) -> str:
        """自动选择最佳计算设备"""
        try:
            import torch

            if torch.cuda.is_available():
                return "cuda"
            elif torch.backends.mps.is_available():
                return "mps"
        except ImportError:
            pass
        return "cpu"

    def _load_model(self):
        """延迟加载模型"""
        if self.model is not None:
            return

        try:
            from sentence_transformers import SentenceTransformer

            logger.info(f"正在加载模型: {self.model_name}")
            self.model = SentenceTransformer(self.model_name, device=self.device)
            logger.info("模型加载完成")

        except ImportError:
            logger.warning("sentence-transformers 未安装，使用备用方案")
            self.model = "fallback"

    def _get_cache_key(self, text: str) -> str:
        """生成缓存 key"""
        return hashlib.md5(text.encode()).hexdigest()

    def encode(self, text: str, normalize_embeddings: bool = True) -> List[float]:
        """
        将单个文本编码为向量

        Args:
            text: 输入文本
            normalize_embeddings: 是否归一化向量

        Returns:
            向量列表（1024维）
        """
        # 检查缓存
        cache_key = self._get_cache_key(text)
        if cache_key in self._cache:
            return self._cache[cache_key]

        self._load_model()

        if self.model == "fallback":
            # 备用方案：使用简单的哈希编码
            return self._fallback_encode(text)

        try:
            # 使用 BGE-M3 编码
            embedding = self.model.encode(
                text, normalize_embeddings=normalize_embeddings, show_progress_bar=False
            )

            result = embedding.tolist()

            # 缓存结果
            self._cache[cache_key] = result

            return result

        except Exception as e:
            logger.error(f"编码失败: {e}")
            return self._fallback_encode(text)

    def encode_batch(
        self, texts: List[str], batch_size: int = 32, normalize_embeddings: bool = True
    ) -> List[List[float]]:
        """
        批量编码文本

        Args:
            texts: 文本列表
            batch_size: 批处理大小
            normalize_embeddings: 是否归一化

        Returns:
            向量列表
        """
        if not texts:
            return []

        self._load_model()

        if self.model == "fallback":
            return [self._fallback_encode(t) for t in texts]

        try:
            embeddings = self.model.encode(
                texts,
                batch_size=batch_size,
                normalize_embeddings=normalize_embeddings,
                show_progress_bar=True,
            )

            return embeddings.tolist()

        except Exception as e:
            logger.error(f"批量编码失败: {e}")
            return [self._fallback_encode(t) for t in texts]

    def _fallback_encode(self, text: str, dim: int = 1024) -> List[float]:
        """
        备用编码方案
        使用字符分布的哈希
        """
        # 简单的哈希编码
        vec = np.zeros(dim)

        # 基于字符分布生成向量
        for i, char in enumerate(text[:1000]):
            idx = ord(char) % dim
            vec[idx] += 1

        # 归一化
        norm = np.linalg.norm(vec)
        if norm > 0:
            vec = vec / norm

        return vec.tolist()

    def calculate_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """
        计算两个向量的余弦相似度

        Args:
            vec1: 向量1
            vec2: 向量2

        Returns:
            相似度分数（0-1）
        """
        v1 = np.array(vec1)
        v2 = np.array(vec2)

        dot_product = np.dot(v1, v2)
        norm1 = np.linalg.norm(v1)
        norm2 = np.linalg.norm(v2)

        if norm1 == 0 or norm2 == 0:
            return 0.0

        return float(dot_product / (norm1 * norm2))

    def find_similar(
        self, query_vec: List[float], candidates: List[List[float]], top_k: int = 5
    ) -> List[tuple]:
        """
        在候选向量中查找最相似的

        Args:
            query_vec: 查询向量
            candidates: 候选向量列表
            top_k: 返回前k个

        Returns:
            [(索引, 相似度), ...]
        """
        similarities = [
            (i, self.calculate_similarity(query_vec, cand))
            for i, cand in enumerate(candidates)
        ]

        # 排序并返回前k个
        similarities.sort(key=lambda x: x[1], reverse=True)
        return similarities[:top_k]

    def clear_cache(self):
        """清除缓存"""
        self._cache.clear()
        logger.info("Embedding 缓存已清除")


class LiteEmbeddingService:
    """
    轻量级 Embedding 服务
    不依赖大型模型，使用轻量级方案
    适合快速部署和资源受限环境
    """

    def __init__(self, dim: int = 384):
        """
        初始化轻量级服务

        Args:
            dim: 向量维度
        """
        self.dim = dim
        logger.info(f"初始化轻量级 Embedding 服务: dim={dim}")

    def encode(self, text: str) -> List[float]:
        """
        编码文本（基于关键词哈希）
        """
        import jieba
        import re

        vec = np.zeros(self.dim)

        # 分词
        try:
            words = jieba.lcut(text)
        except:
            words = text.split()

        # 过滤停用词和标点
        words = [w for w in words if len(w) > 1 and not re.match(r"^[\s\d\W]+$", w)]

        # 基于词频生成向量
        for word in words[:500]:
            idx = hash(word) % self.dim
            vec[idx] += 1

        # 归一化
        norm = np.linalg.norm(vec)
        if norm > 0:
            vec = vec / norm

        return vec.tolist()

    def encode_batch(self, texts: List[str]) -> List[List[float]]:
        """批量编码"""
        return [self.encode(t) for t in texts]
