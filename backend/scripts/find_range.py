import os
from sqlalchemy import create_engine, text

def main():
    url = (os.getenv("DATABASE_URL_SYNC") or os.getenv("DATABASE_URL", "")).replace("+asyncpg", "")
    eng = create_engine(url)
    with eng.begin() as conn:
        rows = conn.execute(
            text("SELECT id, catalog_id, proper_name FROM stars WHERE proper_name LIKE 'HR 81%' OR proper_name LIKE 'HR 82%'")
        ).fetchall()
        for r in rows:
            print(r)
    eng.dispose()

if __name__ == "__main__":
    main()