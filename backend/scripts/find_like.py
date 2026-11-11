import os
from sqlalchemy import create_engine, text

TARGETS = ["491", "5267", "4301", "424", "6789", "8162", "5632", "5291", "8238"]

def main():
    url = (os.getenv("DATABASE_URL_SYNC") or os.getenv("DATABASE_URL", "")).replace("+asyncpg", "")
    eng = create_engine(url)
    with eng.begin() as conn:
        for t in TARGETS:
            res = conn.execute(
                text("SELECT id, catalog_id, proper_name FROM stars WHERE proper_name LIKE :pat"),
                {"pat": f"%{t}%"}
            ).fetchall()
            print(f"Pattern '{t}': {res}")
    eng.dispose()

if __name__ == "__main__":
    main()