"""TrendLetter Engine — FastAPI + 스케줄러."""
import logging
import os
import sys

from dotenv import load_dotenv
load_dotenv()

# 엔진 루트를 path에 추가
sys.path.insert(0, os.path.dirname(__file__))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.routes_crawl import router as crawl_router
from services.scheduler_service import start_scheduler

# 로깅
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("trend-letter")

app = FastAPI(title="TrendLetter Engine", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(crawl_router)


@app.get("/health")
def health():
    return {"status": "ok", "service": "trendletter-engine"}


@app.on_event("startup")
def on_startup():
    logger.info("TrendLetter Engine 시작")
    start_scheduler()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
