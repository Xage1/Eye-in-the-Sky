import os
from sqlalchemy import create_engine, text

def main():
    url = (os.getenv("DATABASE_URL_SYNC") or os.getenv("DATABASE_URL", "")).replace("+asyncpg", "")
    eng = create_engine(url)
    with eng.begin() as conn:
        rows = conn.execute(
            text("SELECT id, catalog_id, proper_name FROM stars WHERE catalog_id::text LIKE '%203280%' OR proper_name LIKE '%203280%'")
        ).fetchall()
        print(f"Results for 203280: {rows}")
        
        # Also let's check table columns
        cols = conn.execute(text("SELECT column_name FROM information_schema.columns WHERE table_name = 'stars'")).fetchall()
        print(f"Columns: {[c[0] for c in cols]}")
    eng.dispose()

if __name__ == "__main__":
    main()