"""
Markdown Generator
将爬取的数据转换为Obsidian兼容的Markdown格式
"""

import os
import re
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional
from urllib.parse import urlparse
from loguru import logger


class MarkdownGenerator:
    """Markdown 生成器 - 生成Obsidian兼容的Markdown"""
    
    def __init__(self):
        self.sanitize_pattern = re.compile(r'[<>:"/\\|?*]')
    
    def _sanitize_filename(self, filename: str) -> str:
        """清理文件名，移除非法字符"""
        return self.sanitize_pattern.sub('_', filename)[:100]
    
    def _format_timestamp(self, timestamp: Any) -> str:
        """格式化时间戳"""
        if isinstance(timestamp, int):
            # Unix timestamp
            return datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S')
        elif isinstance(timestamp, str):
            # ISO format or other string
            try:
                dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                return dt.strftime('%Y-%m-%d %H:%M:%S')
            except:
                return timestamp
        return str(timestamp)
    
    def _generate_frontmatter(self, data: Dict, title: str, tags: List[str] = None) -> str:
        """生成YAML frontmatter"""
        tags = tags or []
        
        frontmatter = "---\n"
        frontmatter += f"title: \"{title}\"\n"
        frontmatter += f"date: {datetime.now().strftime('%Y-%m-%d')}\n"
        frontmatter += f"created: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        
        if tags:
            frontmatter += "tags:\n"
            for tag in tags:
                frontmatter += f"  - {tag}\n"
        
        # 添加平台特定字段
        if 'platform' in data:
            frontmatter += f"platform: {data['platform']}\n"
        
        if 'author' in data:
            frontmatter += f"author: {data['author']}\n"
        
        if 'url' in data:
            frontmatter += f"source_url: {data['url']}\n"
        
        if 'id' in data:
            frontmatter += f"content_id: {data['id']}\n"
        
        frontmatter += "---\n\n"
        return frontmatter
    
    def _format_number(self, num: int) -> str:
        """格式化数字（添加千位分隔符）"""
        if num >= 1000000:
            return f"{num / 1000000:.1f}M"
        elif num >= 1000:
            return f"{num / 1000:.1f}K"
        return str(num)
    
    # ==================== 抖音 (Douyin) ====================
    
    def generate_douyin_list(self, videos: List[Dict], keyword: str) -> str:
        """生成抖音搜索结果Markdown"""
        if not videos:
            return f"# 抖音搜索结果\n\n关键词：{keyword}\n\n未找到相关内容。"
        
        content = self._generate_frontmatter(
            {'keyword': keyword, 'count': len(videos)},
            f"抖音搜索 - {keyword}",
            ['douyin', 'search', 'video']
        )
        
        content += f"# 🔍 抖音搜索结果\n\n"
        content += f"**关键词：** {keyword}\n"
        content += f"**结果数：** {len(videos)}\n"
        content += f"**搜索时间：** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        content += "---\n\n"
        
        for i, video in enumerate(videos, 1):
            content += f"## {i}. {video.get('title', '无标题')}\n\n"
            
            if video.get('cover_url'):
                content += f"![视频封面]({video['cover_url']})\n\n"
            
            content += f"**作者：** {video.get('author', '未知')}\\n"
            content += f"**发布时间：** {video.get('create_time', '未知')}\\n"
            content += f"**时长：** {video.get('duration', 0)}秒\\n"
            content += f"**点赞：** {self._format_number(video.get('like_count', 0))}\\n"
            content += f"**评论：** {self._format_number(video.get('comment_count', 0))}\\n"
            content += f"**分享：** {self._format_number(video.get('share_count', 0))}\\n\\n"
            
            if video.get('desc'):
                content += f"**简介：** {video['desc']}\n\n"
            
            content += f"🔗 [查看视频]({video.get('video_url', '#')})\n\n"
            content += "---\n\n"
        
        return content
    
    def generate_douyin_video(self, video: Dict) -> str:
        """生成抖音视频详情Markdown"""
        content = self._generate_frontmatter(
            video,
            video.get('title', '抖音视频'),
            ['douyin', 'video']
        )
        
        content += f"# 🎬 {video.get('title', '抖音视频')}\n\n"
        
        if video.get('cover_url'):
            content += f"![视频封面]({video['cover_url']})\n\n"
        
        content += "## 📊 视频信息\n\n"
        content += f"- **作者：** {video.get('author', '未知')}
"
        content += f"- **发布时间：** {video.get('create_time', '未知')}
"
        content += f"- **视频ID：** `{video.get('aweme_id', 'unknown')}`
"
        content += f"- **时长：** {video.get('duration', 0)}秒\n\n"
        
        content += "## 📈 互动数据\n\n"
        content += f"- 👍 点赞：{self._format_number(video.get('like_count', 0))}
"
        content += f"- 💬 评论：{self._format_number(video.get('comment_count', 0))}
"
        content += f"- ↗️ 分享：{self._format_number(video.get('share_count', 0))}\n\n"
        
        if video.get('desc'):
            content += "## 📝 视频描述\n\n"
            content += f"{video['desc']}\n\n"
        
        # 评论
        comments = video.get('comments', [])
        if comments:
            content += "## 💭 评论\n\n"
            for i, comment in enumerate(comments[:20], 1):
                content += f"> **{comment.get('user', '匿名用户')}：** {comment.get('text', '')}  \n"
                content += f"> 👍 {self._format_number(comment.get('like_count', 0))} · "
                content += f"{comment.get('create_time', '未知时间')}\n\n"
            
            if len(comments) > 20:
                content += f"*...还有 {len(comments) - 20} 条评论*\n\n"
        
        content += f"\n🔗 [原始链接]({video.get('video_url', '#')})\n"
        
        return content
    
    # ==================== 小红书 (Xiaohongshu) ====================
    
    def generate_xiaohongshu_list(self, notes: List[Dict], keyword: str) -> str:
        """生成小红书搜索结果Markdown"""
        if not notes:
            return f"# 小红书搜索结果\n\n关键词：{keyword}\n\n未找到相关内容。"
        
        content = self._generate_frontmatter(
            {'keyword': keyword, 'count': len(notes)},
            f"小红书搜索 - {keyword}",
            ['xiaohongshu', 'search', 'note']
        )
        
        content += f"# 📕 小红书搜索结果\n\n"
        content += f"**关键词：** {keyword}\n"
        content += f"**结果数：** {len(notes)}\n"
        content += f"**搜索时间：** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        content += "---\n\n"
        
        for i, note in enumerate(notes, 1):
            content += f"## {i}. {note.get('title', '无标题')}\n\n"
            
            if note.get('cover_url'):
                content += f"![笔记封面]({note['cover_url']})\n\n"
            
            content += f"**作者：** {note.get('author', '未知')}  
"
            content += f"**发布时间：** {note.get('create_time', '未知')}  
"
            content += f"**点赞：** {self._format_number(note.get('like_count', 0))}  
"
            content += f"**收藏：** {self._format_number(note.get('collect_count', 0))}  
"
            content += f"**评论：** {self._format_number(note.get('comment_count', 0))}\n\n"
            
            if note.get('desc'):
                content += f"**简介：** {note['desc'][:200]}...\n\n"
            
            content += "---\n\n"
        
        return content
    
    def generate_xiaohongshu_note(self, note: Dict) -> str:
        """生成小红书笔记详情Markdown"""
        content = self._generate_frontmatter(
            note,
            note.get('title', '小红书笔记'),
            ['xiaohongshu', 'note']
        )
        
        content += f"# 📕 {note.get('title', '小红书笔记')}\n\n"
        
        # 显示图片
        images = note.get('image_urls', [])
        if images:
            content += "## 📷 笔记图片\n\n"
            for i, img_url in enumerate(images[:9], 1):
                content += f"![图片{i}]({img_url}) "
                if i % 3 == 0:
                    content += "\n"
            content += "\n\n"
        
        content += "## 📊 笔记信息\n\n"
        content += f"- **作者：** {note.get('author', '未知')}
"
        content += f"- **发布时间：** {note.get('create_time', '未知')}
"
        content += f"- **笔记ID：** `{note.get('note_id', 'unknown')}`\n\n"
        
        content += "## 📈 互动数据\n\n"
        content += f"- 👍 点赞：{self._format_number(note.get('like_count', 0))}
"
        content += f"- 🔖 收藏：{self._format_number(note.get('collect_count', 0))}
"
        content += f"- 💬 评论：{self._format_number(note.get('comment_count', 0))}
"
        content += f"- ↗️ 分享：{self._format_number(note.get('share_count', 0))}\n\n"
        
        if note.get('desc'):
            content += "## 📝 笔记内容\n\n"
            content += f"{note['desc']}\n\n"
        
        # 评论
        comments = note.get('comments', [])
        if comments:
            content += "## 💭 评论\n\n"
            for i, comment in enumerate(comments[:20], 1):
                content += f"> **{comment.get('user', '匿名用户')}：** {comment.get('text', '')}  \n"
                content += f"> 👍 {self._format_number(comment.get('like_count', 0))} · "
                content += f"{comment.get('create_time', '未知时间')}\n\n"
            
            if len(comments) > 20:
                content += f"*...还有 {len(comments) - 20} 条评论*\n\n"
        
        return content
    
    # ==================== B站 (Bilibili) ====================
    
    def generate_bilibili_list(self, videos: List[Dict], keyword: str) -> str:
        """生成B站搜索结果Markdown"""
        if not videos:
            return f"# B站搜索结果\n\n关键词：{keyword}\n\n未找到相关内容。"
        
        content = self._generate_frontmatter(
            {'keyword': keyword, 'count': len(videos)},
            f"B站搜索 - {keyword}",
            ['bilibili', 'search', 'video']
        )
        
        content += f"# 📺 B站搜索结果\n\n"
        content += f"**关键词：** {keyword}\n"
        content += f"**结果数：** {len(videos)}\n"
        content += f"**搜索时间：** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        content += "---\n\n"
        
        for i, video in enumerate(videos, 1):
            content += f"## {i}. {video.get('title', '无标题')}\n\n"
            
            if video.get('cover_url'):
                content += f"![视频封面]({video['cover_url']})\n\n"
            
            content += f"**UP主：** {video.get('author', '未知')}  
"
            content += f"**BV号：** `{video.get('bvid', 'unknown')}`  
"
            content += f"**时长：** {video.get('duration', '未知')}  
"
            content += f"**播放：** {self._format_number(video.get('view_count', 0))}  
"
            content += f"**点赞：** {self._format_number(video.get('like_count', 0))}  
"
            content += f"**投币：** {self._format_number(video.get('coin_count', 0))}  
"
            content += f"**收藏：** {self._format_number(video.get('favorite_count', 0))}\n\n"
            
            if video.get('desc'):
                content += f"**简介：** {video['desc'][:150]}...\n\n"
            
            content += "---\n\n"
        
        return content
    
    def generate_bilibili_video(self, video: Dict) -> str:
        """生成B站视频详情Markdown"""
        content = self._generate_frontmatter(
            video,
            video.get('title', 'B站视频'),
            ['bilibili', 'video']
        )
        
        content += f"# 📺 {video.get('title', 'B站视频')}\n\n"
        
        if video.get('cover_url'):
            content += f"![视频封面]({video['cover_url']})\n\n"
        
        content += "## 📊 视频信息\n\n"
        content += f"- **UP主：** {video.get('author', '未知')}
"
        content += f"- **BV号：** `{video.get('bvid', 'unknown')}`
"
        content += f"- **发布时间：** {video.get('create_time', '未知')}
"
        content += f"- **时长：** {video.get('duration', '未知')}\n\n"
        
        content += "## 📈 互动数据\n\n"
        content += f"- 👁️ 播放：{self._format_number(video.get('view_count', 0))}
"
        content += f"- 👍 点赞：{self._format_number(video.get('like_count', 0))}
"
        content += f"- 🪙 投币：{self._format_number(video.get('coin_count', 0))}
"
        content += f"- ⭐ 收藏：{self._format_number(video.get('favorite_count', 0))}
"
        content += f"- ↗️ 分享：{self._format_number(video.get('share_count', 0))}
"
        content += f"- 📝 弹幕：{self._format_number(video.get('danmaku_count', 0))}\n\n"
        
        if video.get('desc'):
            content += "## 📝 视频简介\n\n"
            content += f"{video['desc']}\n\n"
        
        # 弹幕
        danmaku = video.get('danmaku', [])
        if danmaku:
            content += "## 💬 弹幕\n\n"
            content += "| 时间 | 内容 | 用户 |\n"
            content += "|------|------|------|\n"
            for d in danmaku[:30]:
                content += f"| {d.get('time', '--')} | {d.get('text', '')} | {d.get('user', '匿名')} |\n"
            content += "\n"
        
        # 评论
        comments = video.get('comments', [])
        if comments:
            content += "## 💭 评论\n\n"
            for i, comment in enumerate(comments[:20], 1):
                content += f"> **{comment.get('user', '匿名用户')}：** {comment.get('text', '')}  \n"
                content += f"> 👍 {self._format_number(comment.get('like_count', 0))} · "
                content += f"💬 {comment.get('reply_count', 0)}  · "
                content += f"{comment.get('create_time', '未知时间')}\n\n"
            
            if len(comments) > 20:
                content += f"*...还有 {len(comments) - 20} 条评论*\n\n"
        
        return content
    
    # ==================== 知乎 (Zhihu) ====================
    
    def generate_zhihu_list(self, items: List[Dict], keyword: str) -> str:
        """生成知乎搜索结果Markdown"""
        if not items:
            return f"# 知乎搜索结果\n\n关键词：{keyword}\n\n未找到相关内容。"
        
        content = self._generate_frontmatter(
            {'keyword': keyword, 'count': len(items)},
            f"知乎搜索 - {keyword}",
            ['zhihu', 'search']
        )
        
        content += f"# 🎓 知乎搜索结果\n\n"
        content += f"**关键词：** {keyword}\n"
        content += f"**结果数：** {len(items)}\n"
        content += f"**搜索时间：** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        content += "---\n\n"
        
        for i, item in enumerate(items, 1):
            content_type = "回答" if item.get('type') == 'answer' else "文章" if item.get('type') == 'article' else "内容"
            content += f"## {i}. [{content_type}] {item.get('title', '无标题')}\n\n"
            
            content += f"**作者：** {item.get('author', '未知')}  
"
            content += f"**发布时间：** {item.get('create_time', '未知')}  
"
            content += f"**赞同：** {self._format_number(item.get('voteup_count', 0))}  
"
            content += f"**评论：** {self._format_number(item.get('comment_count', 0))}\n\n"
            
            if item.get('excerpt'):
                content += f"**摘要：** {item['excerpt']}\n\n"
            
            content += f"🔗 [查看原文]({item.get('url', '#')})\n\n"
            content += "---\n\n"
        
        return content
    
    # ==================== YouTube ====================
    
    def generate_youtube_list(self, videos: List[Dict], query: str) -> str:
        """生成YouTube搜索结果Markdown"""
        if not videos:
            return f"# YouTube搜索结果\n\n关键词：{query}\n\n未找到相关内容。"
        
        content = self._generate_frontmatter(
            {'query': query, 'count': len(videos)},
            f"YouTube Search - {query}",
            ['youtube', 'search', 'video']
        )
        
        content += f"# ▶️ YouTube Search Results\n\n"
        content += f"**Query:** {query}\n"
        content += f"**Results:** {len(videos)}\n"
        content += f"**Search Time:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        content += "---\n\n"
        
        for i, video in enumerate(videos, 1):
            content += f"## {i}. {video.get('title', 'No Title')}\n\n"
            
            if video.get('thumbnail'):
                content += f"![Thumbnail]({video['thumbnail']})\n\n"
            
            content += f"**Channel:** {video.get('channel', 'Unknown')}  
"
            content += f"**Upload Date:** {video.get('upload_date', 'Unknown')}  
"
            content += f"**Duration:** {video.get('duration', 0) // 60}:{video.get('duration', 0) % 60:02d}  
"
            content += f"**Views:** {self._format_number(video.get('view_count', 0))}  
"
            content += f"**Likes:** {self._format_number(video.get('like_count', 0))}\n\n"
            
            if video.get('description'):
                content += f"**Description:** {video['description'][:200]}...\n\n"
            
            content += f"🔗 [Watch on YouTube]({video.get('url', '#')})\n\n"
            content += "---\n\n"
        
        return content
    
    def generate_youtube_video(self, video: Dict) -> str:
        """生成YouTube视频详情Markdown"""
        content = self._generate_frontmatter(
            video,
            video.get('title', 'YouTube Video'),
            ['youtube', 'video']
        )
        
        content += f"# ▶️ {video.get('title', 'YouTube Video')}\n\n"
        
        if video.get('thumbnail'):
            content += f"![Thumbnail]({video['thumbnail']})\n\n"
        
        content += "## 📊 Video Information\n\n"
        content += f"- **Channel:** {video.get('channel', 'Unknown')}
"
        content += f"- **Upload Date:** {video.get('upload_date', 'Unknown')}
"
        content += f"- **Video ID:** `{video.get('id', 'unknown')}`
"
        content += f"- **Duration:** {video.get('duration', 0) // 60}:{video.get('duration', 0) % 60:02d}\n\n"
        
        content += "## 📈 Statistics\n\n"
        content += f"- 👁️ Views: {self._format_number(video.get('view_count', 0))}
"
        content += f"- 👍 Likes: {self._format_number(video.get('like_count', 0))}
"
        content += f"- 💬 Comments: {self._format_number(video.get('comment_count', 0))}\n\n"
        
        if video.get('tags'):
            content += "## 🏷️ Tags\n\n"
            content += ", ".join([f"`{tag}`" for tag in video['tags']]) + "\n\n"
        
        if video.get('description'):
            content += "## 📝 Description\n\n"
            content += f"{video['description']}\n\n"
        
        # 字幕
        subtitles = video.get('subtitles', {})
        if subtitles:
            content += "## 📝 Available Subtitles\n\n"
            for lang, sub_info in subtitles.items():
                content += f"- **{lang}:** {sub_info.get('ext', 'unknown')}\n"
            content += "\n"
        
        # 下载信息
        if video.get('downloaded'):
            content += "## 💾 Download Information\n\n"
            content += f"- **Status:** Downloaded ✅\n"
            content += f"- **Path:** `{video.get('download_path', 'N/A')}`\n\n"
        else:
            content += f"\n🔗 [Watch on YouTube]({video.get('url', '#')})\n"
        
        return content
    
    # ==================== Reddit ====================
    
    def generate_reddit_list(self, posts: List[Dict], subreddit: str, keyword: str = "") -> str:
        """生成Reddit搜索结果Markdown"""
        if not posts:
            return f"# Reddit Search Results\n\nSubreddit: r/{subreddit}\nKeyword: {keyword or 'None'}\n\nNo results found."
        
        content = self._generate_frontmatter(
            {'subreddit': subreddit, 'keyword': keyword, 'count': len(posts)},
            f"Reddit r/{subreddit} - {keyword or 'Hot Posts'}",
            ['reddit', 'search', subreddit]
        )
        
        content += f"# 📱 Reddit r/{subreddit}\n\n"
        content += f"**Subreddit:** r/{subreddit}\n"
        content += f"**Keyword:** {keyword or 'None'}\n"
        content += f"**Results:** {len(posts)}\n"
        content += f"**Search Time:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        content += "---\n\n"
        
        for i, post in enumerate(posts, 1):
            is_stickied = "📌 " if post.get('stickied') else ""
            content += f"## {i}. {is_stickied}{post.get('title', 'No Title')}\n\n"
            
            if post.get('selftext'):
                text = post['selftext'][:300]
                content += f"{text}...\n\n"
            
            content += f"**Author:** u/{post.get('author', 'unknown')}  
"
            content += f"**Score:** {self._format_number(post.get('score', 0))} (↑{self._format_number(post.get('upvotes', 0))}/↓{self._format_number(post.get('downvotes', 0))})  
"
            content += f"**Comments:** {self._format_number(post.get('num_comments', 0))}  
"
            content += f"**Posted:** {self._format_timestamp(post.get('created_utc', 0))}\n\n"
            
            content += f"🔗 [View Post]({post.get('url', '#')})\n\n"
            content += "---\n\n"
        
        return content
    
    def generate_reddit_post(self, post: Dict) -> str:
        """生成Reddit帖子详情Markdown"""
        content = self._generate_frontmatter(
            post,
            post.get('title', 'Reddit Post'),
            ['reddit', 'post', post.get('subreddit', 'unknown')]
        )
        
        content += f"# 📱 {post.get('title', 'Reddit Post')}\n\n"
        content += f"**r/{post.get('subreddit', 'unknown')}**\n\n"
        
        if post.get('selftext'):
            content += "## 📝 Post Content\n\n"
            content += f"{post['selftext']}\n\n"
        
        content += "## 📊 Post Information\n\n"
        content += f"- **Author:** u/{post.get('author', 'unknown')}
"
        content += f"- **Posted:** {self._format_timestamp(post.get('created_utc', 0))}
"
        content += f"- **Score:** {self._format_number(post.get('score', 0))} (↑{self._format_number(post.get('upvotes', 0))}/↓{self._format_number(post.get('downvotes', 0))})
"
        content += f"- **Upvote Ratio:** {post.get('upvote_ratio', 0):.1%}
"
        content += f"- **Comments:** {self._format_number(post.get('num_comments', 0))}\n\n"
        
        # 评论
        comments = post.get('comments', [])
        if comments:
            content += "## 💬 Comments\n\n"
            
            def format_comment(comment, level=0):
                indent = "  " * level
                result = f"{indent}> **u/{comment.get('author', 'unknown')}** "
                result += f"({self._format_number(comment.get('score', 0))} points)  \n"
                result += f"{indent}> {comment.get('body', '')}  \n"
                result += f"{indent}> *{self._format_timestamp(comment.get('created_utc', 0))}*\n\n"
                
                # 递归处理回复
                replies = comment.get('replies', [])
                for reply in replies:
                    result += format_comment(reply, level + 1)
                
                return result
            
            for comment in comments[:10]:
                content += format_comment(comment)
            
            if len(comments) > 10:
                content += f"\n*...and {len(comments) - 10} more comments*\n"
        
        content += f"\n🔗 [View on Reddit]({post.get('url', '#')})\n"
        
        return content
    
    # ==================== 公众号 (WeChat) ====================
    
    def generate_wechat_list(self, articles: List[Dict], keyword: str) -> str:
        """生成公众号文章搜索结果Markdown"""
        if not articles:
            return f"# 公众号搜索结果\n\n关键词：{keyword}\n\n未找到相关内容。"
        
        content = self._generate_frontmatter(
            {'keyword': keyword, 'count': len(articles)},
            f"公众号搜索 - {keyword}",
            ['wechat', 'search', 'article']
        )
        
        content += f"# 📰 公众号文章搜索\n\n"
        content += f"**关键词：** {keyword}\n"
        content += f"**结果数：** {len(articles)}\n"
        content += f"**搜索时间：** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        content += "---\n\n"
        
        for i, article in enumerate(articles, 1):
            content += f"## {i}. {article.get('title', '无标题')}\n\n"
            
            content += f"**公众号：** {article.get('author', '未知')}  
"
            content += f"**发布时间：** {article.get('publish_time', '未知')}  
"
            content += f"**阅读：** {self._format_number(article.get('read_count', 0))}  
"
            content += f"**点赞：** {self._format_number(article.get('like_count', 0))}\n\n"
            
            if article.get('summary'):
                content += f"**摘要：** {article['summary']}\n\n"
            
            content += "---\n\n"
        
        return content
    
    def generate_wechat_article(self, article: Dict) -> str:
        """生成公众号文章详情Markdown"""
        content = self._generate_frontmatter(
            article,
            article.get('title', '公众号文章'),
            ['wechat', 'article']
        )
        
        content += f"# 📰 {article.get('title', '公众号文章')}\n\n"
        
        if article.get('cover_image'):
            content += f"![封面]({article['cover_image']})\n\n"
        
        content += "## 📊 文章信息\n\n"
        content += f"- **公众号：** {article.get('author', '未知')}
"
        content += f"- **账号：** {article.get('account', 'unknown')}
"
        content += f"- **发布时间：** {article.get('publish_time', '未知')}
"
        content += f"- **阅读数：** {self._format_number(article.get('read_count', 0))}
"
        content += f"- **点赞数：** {self._format_number(article.get('like_count', 0))}
"
        content += f"- **评论数：** {self._format_number(article.get('comment_count', 0))}\n\n"
        
        if article.get('content'):
            content += "## 📝 文章内容\n\n"
            content += f"{article['content']}\n\n"
        
        # 图片
        images = article.get('images', [])
        if images:
            content += "## 📷 文章图片\n\n"
            for i, img_url in enumerate(images, 1):
                content += f"![图片{i}]({img_url})\n"
            content += "\n"
        
        content += f"🔗 [原始链接]({article.get('url', '#')})\n"
        
        return content
    
    # ==================== 通用方法 ====================
    
    def save_to_file(self, content: str, filename: str, base_dir: str) -> str:
        """保存Markdown内容到文件"""
        # 清理文件名
        filename = self._sanitize_filename(filename)
        
        # 创建目录
        file_path = Path(base_dir) / filename
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        # 如果文件存在，添加序号
        if file_path.exists():
            stem = file_path.stem
            suffix = file_path.suffix
            counter = 1
            while file_path.exists():
                file_path = file_path.parent / f"{stem}_{counter}{suffix}"
                counter += 1
        
        # 写入文件
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        logger.info(f"Markdown saved to: {file_path}")
        return str(file_path)