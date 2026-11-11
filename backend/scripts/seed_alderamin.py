import os
from sqlalchemy import create_engine, text

def main():
    url = (os.getenv("DATABASE_URL_SYNC") or os.getenv("DATABASE_URL", "")).replace("+asyncpg", "")
    eng = create_engine(url)
    with eng.begin() as conn:
        res = conn.execute(
            text("UPDATE stars SET proper_name = 'Alderamin' WHERE catalog_id = 8161 RETURNING id, catalog_id, proper_name")
        ).fetchone()
        if res:
            print(f"Successfully updated row ID {res[0]} (catalog_id {res[1]}) -> {res[2]}")
        else:
            print("Could not find catalog_id 8161")
    eng.dispose()

if __name__ == "__main__":
    main()