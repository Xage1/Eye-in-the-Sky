import os
from sqlalchemy import create_engine, text

# These are the internal row IDs that corresponded to those 9 stars in our dictionary
IDS = [491, 5267, 4301, 424, 6789, 8162, 5632, 5291, 8238]

def main():
    url = (os.getenv("DATABASE_URL_SYNC") or os.getenv("DATABASE_URL", "")).replace("+asyncpg", "")
    eng = create_engine(url)
    with eng.begin() as conn:
        for uid in IDS:
            res = conn.execute(
                text("SELECT id, catalog_id, proper_name FROM stars WHERE id = :uid"),
                {"uid": uid}
            ).fetchone()
            print(f"Row id {uid}: {res}")
    eng.dispose()

if __name__ == "__main__":
    main()