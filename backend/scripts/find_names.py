import os
from sqlalchemy import create_engine, text

def main():
    url = (os.getenv("DATABASE_URL_SYNC") or os.getenv("DATABASE_URL", "")).replace("+asyncpg", "")
    eng = create_engine(url)
    with eng.begin() as conn:
        for name_pat in ["%Alderamin%", "%Deneb Algedi%"]:
            res = conn.execute(
                text("SELECT id, catalog_id, proper_name FROM stars WHERE proper_name ILIKE :pat"),
                {"pat": name_pat}
            ).fetchall()
            print(f"Search {name_pat}: {res}")
    eng.dispose()

if __name__ == "__main__":
    main()