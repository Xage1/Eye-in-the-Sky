import json
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[2]
STARS_PATH = BASE_DIR / "app" / "data" / "stars.json"

def load_star_map() -> dict[str, str]:
    if not STARS_PATH.exists():
        raise FileNotFoundError(f"stars.json not found at {STARS_PATH}")
    
    with STARS_PATH.open("r", encoding="utf-8") as f:
        return json.load(f)