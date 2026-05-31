# Playwright 공식 이미지 — Chromium + 폰트 + 의존성 모두 포함 (별도 playwright install 불필요)
FROM mcr.microsoft.com/playwright/python:v1.49.0-noble

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV PYTHONUNBUFFERED=1

# main.py __main__ 가 PORT 환경변수를 읽어 기동 (쉘 치환 문제 회피)
CMD ["python", "main.py"]
