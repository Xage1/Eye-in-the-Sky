import os
from sqlalchemy import create_engine, text

REMAINING = {
    "HR 491": "Sirius",
    "HR 5267": "Hadar",
    "HR 4301": "Dubhe",
    "HR 424": "Polaris",
    "HR 6789": "Kochab",
    "HR 8162": "Alderamin",
    "HR 5632": "Zubeneschamali",
    "HR 5291": "Thuban",
    "HR 8238": "Deneb Algedi",
}

def main():
    url = (os.getenv("DATABASE_URL_SYNC") or os.getenv("DATABASE_URL", "")).replace("+asyncpg", "")
    eng = create_engine(url)
    with eng.begin() as conn:
        updated = 0
        for hr_str, name in REMAINING.items():
            res = conn.execute(
                text("UPDATE stars SET proper_name = :n WHERE proper_name = :hr RETURNING id"),
                {"n": name, "hr": hr_str}
            ).fetchone()
            if res:
                print(f"  Updated {hr_str} -> {name}")
                updated += 1
            else:
                print(f"  Could not find {hr_str}")
        print(f"\nSuccessfully updated {updated} remaining stars.")
    eng.dispose()

if __name__ == "__main__":
    main()