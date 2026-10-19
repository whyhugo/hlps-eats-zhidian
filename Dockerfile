# 雲端／展示用部署（沒有 micro:bit 的環境，只用網頁 + 虛擬 micro:bit）
FROM python:3.12-slim
WORKDIR /app
ENV PYTHONUNBUFFERED=1 FITWELL_NO_SERIAL=1
COPY pyproject.toml README.md ./
COPY src ./src
RUN pip install --no-cache-dir ".[ai]"
COPY config ./config
COPY data ./data
COPY web ./web
# 以 editable 以外的方式安裝時，ROOT 會指向 site-packages，所以用 PYTHONPATH 指回原始碼
ENV PYTHONPATH=/app/src
EXPOSE 8000
CMD ["python", "-m", "fitwell.cli", "serve", "--port", "8000"]
