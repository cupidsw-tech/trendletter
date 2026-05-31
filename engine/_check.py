# -*- coding: utf-8 -*-
import json, os
from sqlalchemy import create_engine, text

URL = [l.split("=",1)[1].strip().strip('"') for l in open(".env",encoding="utf-8") if l.startswith("DATABASE_URL=")][0]
c = create_engine(URL).connect()

out = {}
out["articles_total"] = c.execute(text("select count(*) from articles")).scalar()
out["per_site"] = [list(r) for r in c.execute(text(
    "select s.name, count(*) from articles a join sources s on s.id=a.source_id group by s.name order by 2 desc")).fetchall()]
out["mobidays"] = [{"date": r[0], "title": r[1][:50]} for r in c.execute(text(
    "select a.date,a.title from articles a join sources s on s.id=a.source_id where s.name='모비데이즈'")).fetchall()]
out["latest_crawl"] = str(c.execute(text("select max(crawled_at) from articles")).scalar())

open("_check.json","w",encoding="utf-8").write(json.dumps(out,ensure_ascii=False,indent=2))
print("written")
