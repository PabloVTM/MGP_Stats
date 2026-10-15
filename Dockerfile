FROM python:3.13.16-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt \
    # Supprime pip et ses dépendances vulnérables (inutiles en runtime)
    && pip uninstall -y pip msgpack setuptools urllib3 wheel 2>/dev/null || true \
    && rm -rf /usr/local/lib/python3.13/site-packages/pip* \
              /usr/local/lib/python3.13/site-packages/msgpack* \
              /usr/local/lib/python3.13/site-packages/setuptools* \
              /usr/local/lib/python3.13/site-packages/urllib3* \
              /usr/local/lib/python3.13/site-packages/wheel* \
              /usr/local/lib/python3.13/site-packages/pkg_resources* \
              /usr/local/lib/python3.13/site-packages/_distutils_hack \
              /usr/local/lib/python3.13/ensurepip

COPY server/ server/

RUN useradd --system --uid 10001 app
USER app

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD ["python", "-c", "import httpx; httpx.get('http://localhost:8000/api/v1/health', timeout=5).raise_for_status()"]

CMD ["uvicorn", "server.main:app", "--host", "0.0.0.0", "--port", "8000", "--proxy-headers"]
