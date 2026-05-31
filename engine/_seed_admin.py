# -*- coding: utf-8 -*-
"""관리자 계정 생성 + 내 18개 소스 + 채널/스케줄 셋팅."""
import json
import os
import uuid
from datetime import datetime
from sqlalchemy import create_engine, text

ENV = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
URL = [l.split("=", 1)[1].strip().strip('"') for l in open(ENV, encoding="utf-8") if l.startswith("DATABASE_URL=")][0]

ADMIN_EMAIL = "datalab@bydream.co.kr"
ADMIN_NAME = "관리자"
PW_HASH = "$2b$10$WT9TQDD1Y9hHkRTBQ7VLkOAuKj8MdMQXSML6Tg5Rm8u6nBRGM7Cco"  # trend1234
TELEGRAM_CHAT = "8563495053"

URLS_JSON = r"C:\Users\jsw\Desktop\트렌드_프로젝트\trend-letter-bot\config\urls.json"


def cuid():
    return "c" + uuid.uuid4().hex[:24]


eng = create_engine(URL)
with eng.begin() as c:
    # 1) 관리자 user upsert
    row = c.execute(text("select id from users where email=:e"), {"e": ADMIN_EMAIL}).fetchone()
    if row:
        uid = row[0]
        c.execute(text("""
            update users set password_hash=:p, name=:n,
              deliver_web=true, deliver_telegram=true, deliver_kakao=false,
              telegram_chat_id=:t, schedule_hour=9, schedule_minute=0,
              timezone='Asia/Seoul', updated_at=now()
            where id=:id
        """), {"p": PW_HASH, "n": ADMIN_NAME, "t": TELEGRAM_CHAT, "id": uid})
        print("UPDATED user", uid)
    else:
        uid = cuid()
        c.execute(text("""
            insert into users (id,email,password_hash,name,created_at,updated_at,
              deliver_web,deliver_telegram,deliver_kakao,telegram_chat_id,
              template_id,schedule_hour,schedule_minute,timezone)
            values (:id,:e,:p,:n,now(),now(),
              true,true,false,:t,'compact',9,0,'Asia/Seoul')
        """), {"id": uid, "e": ADMIN_EMAIL, "p": PW_HASH, "n": ADMIN_NAME, "t": TELEGRAM_CHAT})
        print("CREATED user", uid)

    # 2) 18개 소스 시딩 (중복 url은 건너뜀)
    urls = json.load(open(URLS_JSON, encoding="utf-8"))
    added = 0
    for s in urls:
        ex = c.execute(text("select id from sources where user_id=:u and url=:url"),
                       {"u": uid, "url": s["url"]}).fetchone()
        if ex:
            continue
        c.execute(text("""
            insert into sources (id,user_id,name,url,category,is_active,created_at)
            values (:id,:u,:n,:url,:cat,true,now())
        """), {"id": cuid(), "u": uid, "n": s["name"], "url": s["url"], "cat": s.get("category", "기타")})
        added += 1
    print(f"SOURCES added={added} (total in json={len(urls)})")

    cnt = c.execute(text("select count(*) from sources where user_id=:u"), {"u": uid}).scalar()
    print("USER total sources =", cnt)

print("DONE")
