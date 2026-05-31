from fastapi import APIRouter, Depends
from pydantic import BaseModel

from api.deps import verify_api_key
from core.database import SessionLocal
from services.crawl_service import run_batch_crawl

router = APIRouter(prefix="/crawl", dependencies=[Depends(verify_api_key)])


class SourceItem(BaseModel):
    source_id: str
    url: str
    name: str = ""
    category: str = "기타"


class BatchRequest(BaseModel):
    user_id: str
    sources: list[SourceItem]


@router.post("/batch")
def crawl_batch(req: BatchRequest):
    db = SessionLocal()
    try:
        stats = run_batch_crawl(
            db,
            req.user_id,
            [s.model_dump() for s in req.sources],
        )
        return {"status": "ok", "stats": stats}
    finally:
        db.close()


@router.post("/site")
def crawl_site_endpoint(source: SourceItem):
    """단일 소스 테스트 크롤링."""
    from services.crawl_service import _crawl_single_source
    db = SessionLocal()
    try:
        articles = _crawl_single_source(db, source.model_dump())
        return {
            "status": "ok",
            "articles": [
                {"title": a.title, "url": a.url, "summary": a.summary}
                for a in articles
            ],
        }
    finally:
        db.close()
