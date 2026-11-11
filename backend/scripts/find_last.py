import os
from sqlalchemy import create_engine, text

def main():
    url = (os.getenv("DATABASE_URL_SYNC") or os.getenv("DATABASE_URL", "")).replace("+asyncpg", "")
    eng = create_engine(url)
    with eng.begin() as conn:
        for pat in ["%8162%", "%8238%"]:
            res = conn.execute(
                text("SELECT id, catalog_id, proper_name FROM stars WHERE proper_name LIKE :pat OR catalog_id::text LIKE :pat"),
                {"pat": pat}
            ).fetchall()
            print(f"Pattern {pat}: {res}")
    eng.dispose()

if __name__ == "__main__":
    main()