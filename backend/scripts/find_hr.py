import os
from sqlalchemy import create_engine, text

HR_NAMES = {
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
        for hr_str in HR_NAMES.keys():
            res = conn.execute(
                text("SELECT id, catalog_id, proper_name FROM stars WHERE proper_name = :hr"),
                {"hr": hr_str}
            .fetchone()
            print(f"{hr_str}: {res}")
    eng.dispose()

if __name__ == "__main__":
    main()