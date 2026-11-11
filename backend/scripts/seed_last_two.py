import os
from sqlalchemy import create_engine, text

UPDATES = {
    8162: "Alderamin",
    8322: "Deneb Algedi",
}

def main():
    url = (os.getenv("DATABASE_URL_SYNC") or os.getenv("DATABASE_URL", "")).replace("+asyncpg", "")
    eng = create_engine(url)
    with eng.begin() as conn:
        updated = 0
        for cat_id, name in UPDATES.items():
            res = conn.execute(
                text("UPDATE stars SET proper_name = :n WHERE catalog_id = :cat_id RETURNING id, proper_name"),
                {"n": name, "cat_id": cat_id}
            ).fetchone()
            if res:
                print(f"  Successfully updated catalog_id {cat_id} -> {res[1]}")
                updated += 1
            else:
                print(f"  Could not find catalog_id {cat_id}")
        print(f"\nSuccessfully updated {updated} remaining star(s).")
    eng.dispose()

if __name__ == "__main__":
    main()