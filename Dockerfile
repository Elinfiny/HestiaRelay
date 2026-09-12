FROM python:3.12.14-slim-bookworm

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app/src \
    HESTIA_STATE_DB=/data/hestiarelay.db \
    HESTIA_BEDROCK_MODEL_ID="" \
    AWS_EC2_METADATA_DISABLED=true

WORKDIR /app
COPY requirements-proof.txt ./
RUN python -m pip install --no-cache-dir -r requirements-proof.txt \
    && python -m pip check \
    && groupadd --gid 10001 hestia \
    && useradd --uid 10001 --gid 10001 --no-create-home hestia \
    && mkdir /data \
    && chown 10001:10001 /data
COPY src ./src
COPY LICENSE ./LICENSE
USER 10001:10001
VOLUME ["/data"]
EXPOSE 8000
HEALTHCHECK --interval=10s --timeout=3s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health', timeout=2)"
CMD ["python", "-m", "uvicorn", "hestiarelay.server:app", "--host", "0.0.0.0", "--port", "8000", "--no-proxy-headers"]
