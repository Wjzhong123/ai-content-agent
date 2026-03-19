"""
Markdown Generator - 简化版
修复f-string格式问题
"""

import os
import re
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional
from loguru import logger

from ..models.content_model import ContentItem


class MarkdownGenerator:
    """Markdown 生成器"""

    def __init__(self):
        self.sanitize_pattern = re.compile(r'[<>:"/\\|?*]')

    def _sanitize_filename(self, filename: str) -> str:
        """清理文件名"""
        return self.sanitize_pattern.sub("_", filename)[:100]

    def _generate_frontmatter(
        self, data: Dict, title: str, tags: List[str] = None
    ) -> str:
        """生成YAML frontmatter"""
        tags = tags or []

        fm = "---\n"
        fm += f'title: "{title}"\n'
        fm += f"date: {datetime.now().strftime('%Y-%m-%d')}\n"
        fm += f"created: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"

        if tags:
            fm += "tags:\n"
            for tag in tags:
                fm += f"  - {tag}\n"

        if "platform" in data:
            fm += f"platform: {data['platform']}\n"
        if "author" in data:
            fm += f"author: {data['author']}\n"
        if "url" in data:
            fm += f"source_url: {data['url']}\n"

        fm += "---\n\n"
        return fm

    def _format_number(self, num: int) -> str:
        """格式化数字"""
        if num >= 1000000:
            return f"{num / 1000000:.1f}M"
        elif num >= 1000:
            return f"{num / 1000:.1f}K"
        return str(num)

    def generate_content_list(self, items: List[ContentItem], query: str) -> str:
        """生成内容列表Markdown"""
        if not items:
            return f"# 搜索结果\n\n关键词：{query}\n\n未找到相关内容。"

        content = self._generate_frontmatter(
            {"keyword": query, "count": len(items)},
            f"搜索 - {query}",
            ["search", items[0].platform.value if items else "unknown"],
        )

        content += f"# 🔍 搜索结果\n\n"
        content += f"**关键词：** {query}\n"
        content += f"**结果数：** {len(items)}\n"
        content += f"**搜索时间：** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        content += "---\n\n"

        for i, item in enumerate(items, 1):
            content += f"## {i}. {item.title[:60]}\n\n"

            if item.cover_url:
                content += f"![封面]({item.cover_url})\n\n"

            content += f"**作者：** {item.author.username}  \n"
            content += f"**平台：** {item.platform.value}  \n"
            content += (
                f"**发布时间：** {item.created_at.strftime('%Y-%m-%d %H:%M')}  \n"
            )
            content += f"**浏览：** {self._format_number(item.metrics.views)}  \n"
            content += f"**点赞：** {self._format_number(item.metrics.likes)}  \n"
            content += f"**评论：** {self._format_number(item.metrics.comments)}\n\n"

            if item.content:
                content += f"**简介：** {item.content[:200]}...\n\n"

            content += f"🔗 [查看原文]({item.url})\n\n"
            content += "---\n\n"

        return content

    def generate_content_detail(self, item: ContentItem) -> str:
        """生成内容详情Markdown"""
        content = self._generate_frontmatter(
            item.dict(), item.title, [item.platform.value, item.type.value]
        )

        content += f"# 📄 {item.title}\n\n"

        if item.cover_url:
            content += f"![封面]({item.cover_url})\n\n"

        content += "## 📊 基本信息\n\n"
        content += f"- **作者：** {item.author.username}\n"
        content += f"- **平台：** {item.platform.value}\n"
        content += f"**发布时间：** {item.created_at.strftime('%Y-%m-%d %H:%M')}\n"
        content += f"- **链接：** [{item.url}]({item.url})\n\n"

        content += "## 📈 互动数据\n\n"
        content += f"- 👁️ 浏览：{self._format_number(item.metrics.views)}\n"
        content += f"- 👍 点赞：{self._format_number(item.metrics.likes)}\n"
        content += f"- 💬 评论：{self._format_number(item.metrics.comments)}\n"
        content += f"- ↗️ 分享：{self._format_number(item.metrics.shares)}\n"
        content += f"- ⭐ 收藏：{self._format_number(item.metrics.favorites)}\n\n"

        content += "## 📝 内容\n\n"
        content += f"{item.content}\n\n"

        if item.tags:
            content += "## 🏷️ 标签\n\n"
            content += ", ".join([f"`{tag}`" for tag in item.tags]) + "\n\n"

        return content

    def save_to_file(self, content: str, filename: str, base_dir: str) -> str:
        """保存到文件"""
        filename = self._sanitize_filename(filename)
        file_path = Path(base_dir) / filename
        file_path.parent.mkdir(parents=True, exist_ok=True)

        if file_path.exists():
            stem = file_path.stem
            suffix = file_path.suffix
            counter = 1
            while file_path.exists():
                file_path = file_path.parent / f"{stem}_{counter}{suffix}"
                counter += 1

        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)

        logger.info(f"Markdown saved: {file_path}")
        return str(file_path)
