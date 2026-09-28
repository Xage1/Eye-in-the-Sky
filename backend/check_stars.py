import json
from pathlib import Path

p = Path("app/data/stars_catalogue.json")
d = json.loads(p.read_text(encoding="utf-8"))
wanted = {2491: "Sirius", 1713: "Rigel", 2061: "Betelgeuse", 1457: "Aldebaran", 7001: "Vega"}
stars = {s["id"]: s for s in d["stars"]}

for i in wanted:
    s = stars[i]
    print(f"HR {i}: {s['identifiers']['common_name']} | {s['coordinates']['ra']} | {s['coordinates']['dec']} | Mag {s['photometry']['visual_magnitude']} | {s['constellation']['name']} ({s['constellation']['iau_abbreviation']})")
