import json
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[2]

DATA_PATH = BASE_DIR / "app" / "data" / "constellations.json"

def load_constellations() -> set[str]:
    if not DATA_PATH.exists():
        raise FileNotFoundError(f"Constellations file not found at {DATA_PATH}")

    with DATA_PATH.open("r", encoding="utf-8") as f:
        data = json.load(f)
    return set(data.keys())