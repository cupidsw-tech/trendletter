FROM python:3.12-slim

WORKDIR /app

# Playwright 브라우저 설치를 위한 시스템 패키지
RUN apt-get update && apt-get install -y \
    wget gnupg2 \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Playwright Chromium 설치
RUN playwright install --with-deps chromium

COPY . .

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
