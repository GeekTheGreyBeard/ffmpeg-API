FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DEBIAN_FRONTEND=noninteractive \
    FFMPEG_API_UPLOAD_DIR=/data/uploads \
    FFMPEG_API_OUTPUT_DIR=/data/outputs

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends ffmpeg \
    && rm -rf /var/lib/apt/lists/* \
    && mkdir -p /data/uploads /data/outputs

COPY pyproject.toml README.md ./
COPY ffmpeg_api.py launch.sh ./

RUN pip install --no-cache-dir . \
    && chmod +x /app/launch.sh

VOLUME ["/data"]
EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health', timeout=3).read()"

CMD ["/app/launch.sh"]
