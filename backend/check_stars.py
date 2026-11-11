import os
from sqlalchemy import create_engine, text
url = (os.getenv("DATABASE_URL_SYNC") or os.getenv("DATABASE_URL", "")).replace("+asyncpg", "")
eng = create_engine(url)
with eng.connect() as c:
    q = text("SELECT catalog_id, proper_name, bayer_designation, constellation, magnitude FROM stars "
             "WHERE catalog_id IN (8161, 8162) OR proper_name = 'Alderamin' ORDER BY catalog_id")
    for r in c.execute(q):
        print(tuple(r))
    n = c.execute(text("SELECT count(*) FROM stars WHERE proper_name NOT LIKE 'HR %'")).scalar()
    print("stars with real names:", n)