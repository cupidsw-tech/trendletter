"""APScheduler: 매분 체크 → 해당 시간의 사용자들 배치 크롤링."""
import logging
from datetime import datetime

from apscheduler.schedulers.background import BackgroundScheduler

from core.database import SessionLocal
from core.models import User, Source
from services.crawl_service import run_batch_crawl

logger = logging.getLogger("trend-letter")

scheduler = BackgroundScheduler(timezone="Asia/Seoul")


def _tick():
    """매분 실행: 현재 시각에 해당하는 사용자들의 크롤링 수행."""
    now = datetime.now()
    hour = now.hour
    minute = now.minute

    db = SessionLocal()
    try:
        users = db.query(User).filter(
            User.schedule_hour == hour,
            User.schedule_minute == minute,
        ).all()

        if not users:
            return

        logger.info(f"[스케줄러] {hour:02d}:{minute:02d} — {len(users)}명 크롤링 시작")

        for user in users:
            sources = db.query(Source).filter(
                Source.user_id == user.id,
                Source.is_active == True,
            ).all()

            if not sources:
                continue

            source_list = [
                {
                    "source_id": s.id,
                    "url": s.url,
                    "name": s.name,
                    "category": s.category,
                }
                for s in sources
            ]

            logger.info(f"  [{user.email}] {len(source_list)}개 소스 크롤링")
            try:
                stats = run_batch_crawl(db, user.id, source_list)
                logger.info(f"  [{user.email}] 완료: {stats}")
            except Exception as e:
                logger.error(f"  [{user.email}] 크롤링 실패: {e}")

    except Exception as e:
        logger.error(f"[스케줄러] 오류: {e}")
    finally:
        db.close()


def start_scheduler():
    """스케줄러 시작."""
    scheduler.add_job(
        _tick,
        trigger="cron",
        minute="*",  # 매분 실행
        id="schedule_tick",
        name="사용자별 크롤링 스케줄 체크",
        max_instances=1,
        misfire_grace_time=60,
    )
    scheduler.start()
    logger.info("[스케줄러] 시작됨 — 매분 사용자 스케줄 체크")
