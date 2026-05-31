# -*- coding: utf-8 -*-
"""웹 발송 테스트: jsw 계정 17개 소스 크롤링 → 기사 DB저장 → web 발송로그만 기록 (텔레그램 X)."""
import os, sys, json, uuid
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from dotenv import load_dotenv
load_dotenv()

from core.database import SessionLocal
from core.models import User, Source, Article, DeliveryLog
from services.crawl_service import _crawl_single_source

EMAIL = "jsw@bydream.co.kr"


def cuid():
    return "c" + uuid.uuid4().hex[:24]


def main():
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.email == EMAIL).first()
        if not user:
            print("NO USER"); return
        sources = db.query(Source).filter(Source.user_id == user.id, Source.is_active == True).all()
        print(f"sources={len(sources)}")

        total_new = 0
        for s in sources:
            info = {"source_id": s.id, "url": s.url, "name": s.name, "category": s.category}
            try:
                new_articles = _crawl_single_source(db, info)
            except Exception as e:
                print(f"  [{s.name}] crawl err: {e}")
                continue
            # web 발송로그 기록 (deliver_web)
            for a in new_articles:
                log = DeliveryLog(
                    id=cuid(), user_id=user.id, article_id=a.id,
                    channel="web", status="sent",
                    sent_at=datetime.utcnow(), created_at=datetime.utcnow(),
                )
                db.add(log)
            db.commit()
            total_new += len(new_articles)
            print(f"  [{s.name}] new={len(new_articles)}")

        # 결과 요약
        art_cnt = db.query(Article).count()
        log_cnt = db.query(DeliveryLog).filter(DeliveryLog.user_id == user.id, DeliveryLog.channel == "web").count()
        print(f"DONE new_this_run={total_new} | total_articles={art_cnt} | web_logs(user)={log_cnt}")
    finally:
        db.close()


if __name__ == "__main__":
    main()
