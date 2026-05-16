FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    FFMPEG_API_BASE_URL=http://ffmpeg-api:8000 \
    FFMPEG_MCP_HOST=0.0.0.0 \
    FFMPEG_MCP_PORT=8080

WORKDIR /app

COPY pyproject.toml README.md ./
COPY ffmpeg_mcp ./ffmpeg_mcp

RUN pip install --no-cache-dir .

EXPOSE 8080

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8080/health', timeout=3).read()"

CMD ["ffmpeg-mcp"]

