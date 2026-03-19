#!/usr/bin/env python3
"""
服务器直接运行脚本
使用标准库，不依赖外部包
"""

import json
import sys
from pathlib import Path
from datetime import datetime

print("=" * 70)
print("🚀 AI Content Agent - 服务器部署验证")
print("=" * 70)
print()
print(f"⏰ 运行时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print(f"📁 项目路径: {Path(__file__).parent.absolute()}")
print(f"🐍 Python版本: {sys.version}")
print()

# 检查文件结构
print("📂 检查项目文件...")
required_files = [
    "src/scrapers/bilibili_v3.py",
    "src/models/content_model.py",
    "src/output/markdown.py",
    "src/utils/anti_crawler.py",
]

base_path = Path(__file__).parent

for file in required_files:
    full_path = base_path / file
    if full_path.exists():
        print(f"  ✅ {file}")
    else:
        print(f"  ❌ {file} (不存在)")

print()

# 检查是否能导入
print("🔧 检查Python模块...")
try:
    sys.path.insert(0, str(base_path / "src"))

    # 尝试导入关键模块
    print("  📦 导入 models.content_model...")
    from models.content_model import ContentItem, Author, Metrics, PlatformType

    print("  ✅ models 导入成功")

    print("  📦 导入 utils.anti_crawler...")
    from utils.anti_crawler import BrowserFingerprint

    print("  ✅ utils 导入成功")

    print()
    print("🎉 所有模块导入成功！")
    print()

    # 创建测试数据
    print("🧪 创建测试数据...")

    test_item = ContentItem(
        id="test_001",
        platform=PlatformType.BILIBILI,
        type=ContentType.VIDEO,
        title="测试视频标题",
        content="这是一个测试内容",
        author=Author(
            platform=PlatformType.BILIBILI,
            user_id="user_001",
            username="测试用户",
            display_name="测试用户",
        ),
        url="https://example.com/video/1",
        created_at=datetime.now(),
        metrics=Metrics(views=1000, likes=100),
        tags=["测试", "Python"],
    )

    print(f"  ✅ 创建测试数据成功")
    print(f"     标题: {test_item.title}")
    print(f"     平台: {test_item.platform.value}")
    print(f"     作者: {test_item.author.username}")
    print()

    # 测试浏览器指纹
    print("🔐 测试浏览器指纹...")
    fp = BrowserFingerprint()
    headers = fp.generate()
    print(f"  ✅ 生成指纹成功")
    print(f"     User-Agent: {headers['User-Agent'][:60]}...")
    print()

    print("=" * 70)
    print("✅ 服务器部署验证成功！")
    print("=" * 70)
    print()
    print("💡 下一步:")
    print("  1. 安装依赖: source venv/bin/activate && pip install -r requirements.txt")
    print("  2. 运行测试: python3 test_multi_platform.py")
    print("  3. 启动MCP Server: python3 -m src.server")

except ImportError as e:
    print(f"  ❌ 导入失败: {e}")
    print()
    print("💡 请先安装依赖:")
    print("  source venv/bin/activate")
    print("  pip install -r requirements.txt")

except Exception as e:
    print(f"  ❌ 错误: {e}")
    import traceback

    traceback.print_exc()

print()
