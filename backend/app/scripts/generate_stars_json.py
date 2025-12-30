import csv
import json
import requests
from pathlib import Path
from io import StringIO

# ✅ Verified GitHub-hosted HYG v3 CSV
CSV_URL = "https://raw.githubusercontent.com/astronexus/HYG-Database/master/hygdata_v3.csv"

# Output file location
output_path = Path("app/data/stars.json")
output_path.parent.mkdir(parents=True, exist_ok=True)

def fetch_csv(url):
    print("⬇️ Downloading HYG star catalog from GitHub...")
    response = requests.get(url)
    response.raise_for_status()
    return StringIO(response.text)

def process_star(row):
    try:
        return {
            "name": row["proper"] or None,
            "bayer": row["bayer"] or None,
            "ra": float(row["ra"]),
            "dec": float(row["dec"]),
            "mag": float(row["mag"]),
            "spectral_type": row["spect"] or None,
            "constellation": row["con"] or None
        }
    except Exception:
        return None

csv_data = fetch_csv(CSV_URL)
reader = csv.DictReader(csv_data)
stars = [s for s in map(process_star, reader) if s and s["mag"] < 6.5]

with output_path.open("w", encoding="utf-8") as f:
    json.dump(stars, f, indent=2, ensure_ascii=False)

print(f"✅ stars.json generated with {len(stars)} stars at {output_path.resolve()}")