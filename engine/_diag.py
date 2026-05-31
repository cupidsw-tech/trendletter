# -*- coding: utf-8 -*-
"""DB 진단: 사용자 텔레그램 설정 / 소스 / 기사 현황 출력."""
import os
from sqlalchemy import create_engine, text

ENV = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
url = tok = None
for line in open(ENV, encoding="utf-8"):
    line = line.strip()
    if line.startswith("DATABASE_URL="):
        url = line.split("=", 1)[1].strip().strip('"')
    if line.startswith("TELEGRAM_BOT_TOKEN="):
        tok = line.split("=", 1)[1].strip().strip('"')

print("DATABASE_URL loaded:", bool(url), "| TELEGRAM token loaded:", bool(tok))
eng = create_engine(url)
with eng.connect() as c:
    print("\n=== USERS ===")
    for u in c.execute(text(
        "select id,email,deliver_web,deliver_telegram,telegram_chat_id,"
        "schedule_hour,schedule_minute,template_id from users")).fetchall():
        print(dict(u._mapping))

    print("\n=== SOURCES count per user ===")
    for r in c.execute(text(
        "select user_id, count(*) c from sources group by user_id")).fetchall():
        print(dict(r._mapping))

    rows = c.execute(text(
        "select name,url,category,is_active,last_crawled_at "
        "from sources order by created_at")).fetchall()
    print(f"\n=== ALL SOURCES ({len(rows)}) ===")
    for s in rows:
        print(dict(s._mapping))

    print("\n=== ARTICLES total ===",
          c.execute(text("select count(*) from articles")).scalar())
    print("=== DELIVERY LOGS total ===",
          c.execute(text("select count(*) from delivery_logs")).scalar())
