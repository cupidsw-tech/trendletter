# Playwright 공식 이미지 — Chromium + 폰트 + 의존성 모두 포함 (별도 playwright install 불필요)
FROM mcr.microsoft.com/playwright/python:v1.52.0-noble

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV PYTHONUNBUFFERED=1

# Railway가 주입하는 $PORT 사용
CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}"]
