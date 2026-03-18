# Content Scraper MCP Server Dockerfile
# Python 3.10 + Playwright + FFmpeg

FROM python:3.10-slim

# 设置工作目录
WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    curl \
    wget \
    git \
    build-essential \
    libffi-dev \
    libssl-dev \
    ffmpeg \
    chromium \
    chromium-driver \
    fonts-wqy-microhei \
    fonts-wqy-zenhei \
    && rm -rf /var/lib/apt/lists/*

# 安装 Node.js (for Playwright)
RUN curl -fsSL https://deb.nodesource.com/setup_18.x | bash - \
    && apt-get install -y nodejs

# 安装 Playwright 浏览器
RUN pip install playwright && \
    playwright install chromium

# 复制依赖文件
COPY requirements.txt .

# 安装 Python 依赖
RUN pip install --no-cache-dir -r requirements.txt

# 复制源代码
COPY src/ ./src/
COPY scrapers-config/ ./scrapers-config/

# 创建输出目录
RUN mkdir -p /app/scraped_content \
    /app/logs \
    /tmp/mediacrawler_output \
    /tmp/youtube_output

# 设置环境变量
ENV PYTHONPATH=/app
ENV OUTPUT_DIR=/app/scraped_content
ENV PLAYWRIGHT_BROWSERS_PATH=/root/.cache/ms-playwright
ENV PLAYWRIGHT_CHROMIUM_EXECUTABLE_PATH=/usr/bin/chromium

# 暴露端口
EXPOSE 3001

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:3001/health', timeout=5)" || exit 1

# 启动命令
CMD ["python", "-m", "src.server"]