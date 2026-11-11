import os
from sqlalchemy import create_engine, text

# Mapping of database row id -> proper name for the remaining items
FINAL_MAP = {
    491: "Sirius",
    5267: "Hadar",
    4301: "Dubhe",
    424: "Polaris",
    6789: "Kochab",
    5632: "Zubeneschamali",
    5291: "Thuban",
    # Let's check catalog_id / id lookups for the remaining two if needed, 
    # or match them by catalog_id directly:
}

# Also map by catalog_id for safety (e.g. HR 8162, HR 8238)
CATALOG_MAP = {
    8162: "Alderamin",
    8238: "Deneb Algedi",
}

def main():
    url = (os.getenv("DATABASE_URL_SYNC") or os.getenv("DATABASE_URL", "")).replace("+asyncpg", "")
    eng = create_engine(url)
    with eng.begin() as conn:
        updated = 0
        
        for uid, name in FINAL_MAP.items():
            res = conn.execute(
                text("UPDATE stars SET proper_name = :n WHERE id = :uid RETURNING id, proper_name"),
                {"n": name, "uid": uid}
            ).fetchone()
            if res:
                print(f"  Updated row ID {res[0]} -> {res[1]}")
                updated += 1

        for cat_id, name in CATALOG_MAP.items():
            res = conn.execute(
                text("UPDATE stars SET proper_name = :n WHERE catalog_id = :cat_id RETURNING id, proper_name"),
                {"n": name, "cat_id": cat_id}
            ).fetchone()
            if res:
                print(f"  Updated catalog_id {cat_id} -> {res[1]}")
                updated += 1
            else:
                # Fallback: search by proper_name containing the HR number string
                res2 = conn.execute(
                    text("UPDATE stars SET proper_name = :n WHERE proper_name LIKE :pat RETURNING id, proper_name"),
                    {"n": name, "pat": f"%HR {cat_id}%"}
                ).fetchone()
                if res2:
                    print(f"  Updated via pattern HR {cat_id} -> {res2[1]}")
                    updated += 1

        print(f"\nSuccessfully seeded {updated} final star records.")
    eng.dispose()

if __name__ == "__main__":
    main()