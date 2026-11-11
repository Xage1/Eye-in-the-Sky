import os
from sqlalchemy import create_engine, text

IDS = [491, 5267, 4301, 424, 6789, 8162, 5632, 5291, 8238]

def main():
    url = (os.getenv("DATABASE_URL_SYNC") or os.getenv("DATABASE_URL", "")).replace("+asyncpg", "")
    eng = create_engine(url)
    with eng.begin() as conn:
        for cid in IDS:
            res = conn.execute(
                text("SELECT id, catalog_id, proper_name FROM stars WHERE catalog_id = :cid"),
                {"cid": cid}
            ).fetchone()
            print(f"catalog_id {cid}: {res}")
    eng.dispose()

if __name__ == "__main__":
    main()