"""
Content Models - 统一内容模型层
定义所有平台抓取内容的标准化结构
"""

from .content_model import (
    ContentItem,
    Author,
    Metrics,
    Comment,
    PlatformType,
    ContentType,
)

__all__ = ["ContentItem", "Author", "Metrics", "Comment", "PlatformType", "ContentType"]
