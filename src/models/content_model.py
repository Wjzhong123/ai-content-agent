"""
Content Model - 统一内容模型
定义所有平台抓取内容的标准化结构

这是AI员工系统的核心数据层：
- 统一不同平台的字段差异
- 支持向量化存储
- 便于AI处理和分析
"""

from datetime import datetime
from typing import List, Dict, Any, Optional
from enum import Enum
from pydantic import BaseModel, Field


class PlatformType(str, Enum):
    """平台类型"""

    DOUYIN = "douyin"
    XIAOHONGSHU = "xiaohongshu"
    BILIBILI = "bilibili"
    ZHIHU = "zhihu"
    YOUTUBE = "youtube"
    REDDIT = "reddit"
    WECHAT = "wechat"


class ContentType(str, Enum):
    """内容类型"""

    VIDEO = "video"
    ARTICLE = "article"
    POST = "post"
    ANSWER = "answer"
    COMMENT = "comment"
    IMAGE = "image"
    LIVE = "live"


class Author(BaseModel):
    """
    作者/账号信息
    统一所有平台的作者信息
    """

    platform: PlatformType = Field(..., description="来源平台")
    user_id: str = Field(..., description="平台用户ID")
    username: str = Field(..., description="用户名")
    display_name: Optional[str] = Field(None, description="显示名称")
    avatar_url: Optional[str] = Field(None, description="头像URL")
    bio: Optional[str] = Field(None, description="简介")
    followers_count: int = Field(0, description="粉丝数")
    verified: bool = Field(False, description="是否认证")
    verified_reason: Optional[str] = Field(None, description="认证信息")

    # 平台特有字段
    extra: Dict[str, Any] = Field(default_factory=dict, description="平台特有字段")


class Metrics(BaseModel):
    """
    互动数据指标
    统一所有平台的互动数据
    """

    views: int = Field(0, description="浏览量")
    likes: int = Field(0, description="点赞数")
    shares: int = Field(0, description="分享/转发数")
    comments: int = Field(0, description="评论数")
    favorites: int = Field(0, description="收藏数")
    downloads: int = Field(0, description="下载数")

    # 平台特有指标
    coins: int = Field(0, description="B站投币数")
    danmaku: int = Field(0, description="B站弹幕数")
    collects: int = Field(0, description="小红书收藏数")
    upvotes: int = Field(0, description="知乎赞同数")
    downvotes: int = Field(0, description="Reddit反对数")

    @property
    def engagement_rate(self) -> float:
        """计算互动率"""
        if self.views == 0:
            return 0.0
        total = self.likes + self.comments + self.shares + self.favorites
        return round(total / self.views * 100, 2)

    def to_dict(self) -> Dict[str, int]:
        """转换为字典"""
        return {
            "views": self.views,
            "likes": self.likes,
            "shares": self.shares,
            "comments": self.comments,
            "favorites": self.favorites,
            "downloads": self.downloads,
            "engagement_rate": self.engagement_rate,
        }


class Comment(BaseModel):
    """
    评论数据模型
    """

    comment_id: str = Field(..., description="评论ID")
    parent_id: Optional[str] = Field(None, description="父评论ID（用于回复）")
    user_id: str = Field(..., description="用户ID")
    username: str = Field(..., description="用户名")
    content: str = Field(..., description="评论内容")
    likes: int = Field(0, description="点赞数")
    replies: int = Field(0, description="回复数")
    created_at: datetime = Field(..., description="创建时间")

    # 递归回复
    children: List["Comment"] = Field(default_factory=list, description="子评论")


class ContentItem(BaseModel):
    """
    统一内容模型

    这是所有平台抓取内容的统一数据结构。
    无论来源是哪个平台，最终都转换成这个格式。

    核心字段：
    - id: 唯一标识
    - platform: 来源平台
    - type: 内容类型
    - title: 标题
    - content: 正文内容
    - summary: AI生成的摘要
    - author: 作者信息
    - metrics: 互动数据
    - tags: 标签/话题
    - keywords: 关键词提取
    - embedding: 向量表示
    """

    # === 基础信息 ===
    id: str = Field(..., description="内容唯一ID")
    platform: PlatformType = Field(..., description="来源平台")
    type: ContentType = Field(..., description="内容类型")

    # === 内容信息 ===
    title: str = Field(..., description="标题")
    content: str = Field(..., description="正文内容（纯文本）")
    content_html: Optional[str] = Field(None, description="HTML格式内容")
    summary: Optional[str] = Field(None, description="AI生成摘要")

    # === 媒体信息 ===
    cover_url: Optional[str] = Field(None, description="封面图URL")
    media_urls: List[str] = Field(default_factory=list, description="媒体文件URL列表")
    media_files: List[str] = Field(default_factory=list, description="本地媒体文件路径")
    duration: Optional[int] = Field(None, description="视频时长（秒）")

    # === 作者信息 ===
    author: Author = Field(..., description="作者信息")

    # === 链接信息 ===
    url: str = Field(..., description="原始链接")
    short_url: Optional[str] = Field(None, description="短链接")

    # === 时间信息 ===
    created_at: datetime = Field(..., description="发布时间")
    crawled_at: datetime = Field(default_factory=datetime.now, description="抓取时间")

    # === 互动数据 ===
    metrics: Metrics = Field(default_factory=Metrics, description="互动数据")

    # === 评论数据 ===
    comments: List[Comment] = Field(default_factory=list, description="评论列表")
    comments_enabled: bool = Field(True, description="是否允许评论")

    # === AI处理字段 ===
    tags: List[str] = Field(default_factory=list, description="标签/话题")
    keywords: List[str] = Field(default_factory=list, description="关键词")
    embedding: Optional[List[float]] = Field(None, description="向量嵌入")
    sentiment: Optional[str] = Field(None, description="情感分析结果")
    topics: List[str] = Field(default_factory=list, description="主题分类")

    # === 状态字段 ===
    status: str = Field("active", description="状态：active/deleted/hidden")
    language: str = Field("zh", description="语言代码")
    region: Optional[str] = Field(None, description="地区")

    # === 平台特有字段 ===
    platform_data: Dict[str, Any] = Field(
        default_factory=dict, description="平台原始数据"
    )

    class Config:
        json_encoders = {datetime: lambda v: v.isoformat()}

    def to_markdown(self) -> str:
        """转换为Obsidian兼容的Markdown"""
        from datetime import datetime

        md = f"""---
title: "{self.title}"
date: {self.created_at.strftime("%Y-%m-%d")}
platform: {self.platform.value}
type: {self.type.value}
author: {self.author.username}
url: {self.url}
tags:
{chr(10).join(f"  - {tag}" for tag in self.tags)}
keywords:
{chr(10).join(f"  - {kw}" for kw in self.keywords)}
metrics:
  views: {self.metrics.views}
  likes: {self.metrics.likes}
  comments: {self.metrics.comments}
  shares: {self.metrics.shares}
  engagement_rate: {self.metrics.engagement_rate}%
---

# {self.title}

**作者：** [{self.author.display_name or self.author.username}]({self.author.extra.get("profile_url", "")})  
**来源：** {self.platform.value}  
**发布时间：** {self.created_at.strftime("%Y-%m-%d %H:%M:%S")}  
**原始链接：** [{self.url}]({self.url})

## 📊 数据概览

- 👁️ 浏览：{self.metrics.views:,}
- 👍 点赞：{self.metrics.likes:,}
- 💬 评论：{self.metrics.comments:,}
- ↗️ 分享：{self.metrics.shares:,}
- ⭐ 收藏：{self.metrics.favorites:,}
- 📈 互动率：{self.metrics.engagement_rate}%

"""

        # 添加摘要
        if self.summary:
            md += f"""## 📝 内容摘要

{self.summary}

"""

        # 添加正文
        md += f"""## 📄 正文内容

{self.content}

"""

        # 添加评论
        if self.comments:
            md += f"""## 💭 精选评论

"""
            for i, comment in enumerate(self.comments[:10], 1):
                md += f"> **{comment.username}：** {comment.content[:200]}  \n"
                md += f"> 👍 {comment.likes:,} · {comment.created_at.strftime('%Y-%m-%d')}\n\n"

            if len(self.comments) > 10:
                md += f"*...还有 {len(self.comments) - 10} 条评论*\n\n"

        # 添加标签
        if self.tags:
            md += f"""## 🏷️ 标签

{", ".join(f"`{tag}`" for tag in self.tags)}

"""

        # 添加AI分析
        if self.sentiment or self.topics:
            md += """## 🤖 AI分析

"""
            if self.sentiment:
                md += f"- **情感倾向：** {self.sentiment}\n"
            if self.topics:
                md += f"- **主题分类：** {', '.join(self.topics)}\n"
            md += "\n"

        return md

    def to_dict_for_embedding(self) -> Dict[str, Any]:
        """
        转换为适合向量化的字典
        只包含语义相关字段
        """
        return {
            "title": self.title,
            "content": self.content[:2000],  # 限制长度
            "summary": self.summary or "",
            "tags": self.tags,
            "keywords": self.keywords,
            "author": self.author.username,
            "platform": self.platform.value,
            "type": self.type.value,
        }

    def get_text_for_embedding(self) -> str:
        """
        获取用于向量化的文本
        """
        parts = [
            f"标题：{self.title}",
            f"内容：{self.content[:2000]}",
            f"标签：{', '.join(self.tags)}",
            f"关键词：{', '.join(self.keywords)}",
        ]
        return "\n".join(parts)


class ContentBatch(BaseModel):
    """
    内容批次
    用于批量处理
    """

    items: List[ContentItem]
    total: int
    batch_id: str
    created_at: datetime = Field(default_factory=datetime.now)

    class Config:
        json_encoders = {datetime: lambda v: v.isoformat()}


class TrendingTopic(BaseModel):
    """
    热门话题/趋势
    """

    topic: str = Field(..., description="话题名称")
    platform: PlatformType = Field(..., description="平台")
    hot_score: float = Field(..., description="热度分数")
    content_count: int = Field(0, description="相关内容数")
    sample_content: List[ContentItem] = Field(
        default_factory=list, description="示例内容"
    )
    crawled_at: datetime = Field(default_factory=datetime.now, description="抓取时间")


class CreatorProfile(BaseModel):
    """
    创作者档案
    """

    author: Author
    platform: PlatformType
    total_content: int = 0
    avg_metrics: Metrics = Field(default_factory=Metrics)
    top_content: List[ContentItem] = Field(default_factory=list)
    topics: List[str] = Field(default_factory=list)
    content_style: Optional[str] = None  # AI分析的内容风格
    update_frequency: Optional[str] = None  # 更新频率

    def summary(self) -> str:
        """生成创作者摘要"""
        return f"""
创作者：{self.author.display_name or self.author.username}
平台：{self.platform.value}
粉丝数：{self.author.followers_count:,}
内容数：{self.total_content}
平均互动率：{self.avg_metrics.engagement_rate}%
主要内容标签：{", ".join(self.topics[:5])}
        """.strip()


# 更新Comment模型以支持递归
Comment.update_forward_refs()
