"""backend/scripts/seed_star_names.py

Give bright stars their IAU proper names, keyed by Harvard Revised (HR) number and
VALIDATED against the row before use: constellation abbreviation must match and the
magnitude must be within TOL of the star's known V magnitude. Anything that fails the
check is left as 'HR <n>' and reported, never guessed.

Clears all existing proper names first (names are fully re-derived from the table below),
so it is safe to re-run.

Run:  docker exec eyesky_api python -m scripts.seed_star_names
"""
import os

from sqlalchemy import create_engine, text

TOL = 0.3

# (name, HR number, IAU constellation abbreviation, approx V magnitude)
STARS = [
    ("Sirius", 2491, "CMa", -1.46), ("Canopus", 2326, "Car", -0.72), ("Arcturus", 5340, "Boo", -0.04),
    ("Rigil Kentaurus", 5459, "Cen", -0.01), ("Vega", 7001, "Lyr", 0.03), ("Capella", 1708, "Aur", 0.08),
    ("Rigel", 1713, "Ori", 0.12), ("Procyon", 2943, "CMi", 0.38), ("Achernar", 472, "Eri", 0.46),
    ("Betelgeuse", 2061, "Ori", 0.50), ("Hadar", 5267, "Cen", 0.61), ("Altair", 7557, "Aql", 0.77),
    ("Acrux", 4730, "Cru", 1.33), ("Aldebaran", 1457, "Tau", 0.85), ("Antares", 6134, "Sco", 1.06),
    ("Spica", 5056, "Vir", 0.98), ("Pollux", 2990, "Gem", 1.14), ("Fomalhaut", 8728, "PsA", 1.16),
    ("Deneb", 7924, "Cyg", 1.25), ("Mimosa", 4853, "Cru", 1.25), ("Regulus", 3982, "Leo", 1.35),
    ("Adhara", 2618, "CMa", 1.50), ("Castor", 2891, "Gem", 1.98), ("Gacrux", 4763, "Cru", 1.64),
    ("Shaula", 6527, "Sco", 1.63), ("Bellatrix", 1790, "Ori", 1.64), ("Elnath", 1791, "Tau", 1.65),
    ("Miaplacidus", 3685, "Car", 1.68), ("Alnilam", 1903, "Ori", 1.70), ("Alnair", 8425, "Gru", 1.74),
    ("Alnitak", 1948, "Ori", 1.77), ("Alioth", 4905, "UMa", 1.77), ("Dubhe", 4301, "UMa", 1.79),
    ("Mirfak", 1017, "Per", 1.80), ("Wezen", 2693, "CMa", 1.84), ("Kaus Australis", 6879, "Sgr", 1.85),
    ("Alkaid", 5191, "UMa", 1.86), ("Menkalinan", 2088, "Aur", 1.90), ("Alphard", 3748, "Hya", 1.98),
    ("Polaris", 424, "UMi", 2.02), ("Hamal", 617, "Ari", 2.00), ("Diphda", 188, "Cet", 2.04),
    ("Nunki", 7121, "Sgr", 2.02), ("Rasalhague", 6556, "Oph", 2.08), ("Kochab", 5563, "UMi", 2.08),
    ("Saiph", 2004, "Ori", 2.06), ("Denebola", 4534, "Leo", 2.14), ("Algol", 936, "Per", 2.12),
    ("Mizar", 5054, "UMa", 2.23), ("Mintaka", 1852, "Ori", 2.23), ("Alpheratz", 15, "And", 2.06),
    ("Mirach", 337, "And", 2.05), ("Sargas", 6553, "Sco", 1.87), ("Avior", 3307, "Car", 1.86),
    ("Peacock", 7790, "Pav", 1.94), ("Alhena", 2421, "Gem", 1.93), ("Mirzam", 2294, "CMa", 1.98),
    ("Schedar", 168, "Cas", 2.24), ("Caph", 21, "Cas", 2.28), ("Algieba", 4057, "Leo", 2.61),
    ("Alderamin", 8162, "Cep", 2.44), ("Menkar", 911, "Cet", 2.53), ("Izar", 5506, "Boo", 2.70),
    ("Phact", 1956, "Col", 2.64), ("Alphecca", 5793, "CrB", 2.23), ("Sadr", 7796, "Cyg", 2.20),
    ("Albireo", 7417, "Cyg", 3.08), ("Zubeneschamali", 5685, "Lib", 2.61), ("Zubenelgenubi", 5531, "Lib", 2.75),
    ("Eltanin", 6705, "Dra", 2.23), ("Rastaban", 6536, "Dra", 2.79), ("Thuban", 5291, "Dra", 3.65),
    ("Unukalhai", 5854, "Ser", 2.65), ("Dschubba", 5953, "Sco", 2.32), ("Acrab", 5984, "Sco", 2.62),
    ("Rukbat", 7348, "Sgr", 3.97), ("Alchiba", 4623, "Crv", 4.02), ("Enif", 8308, "Peg", 2.39),
    ("Markab", 8781, "Peg", 2.49), ("Scheat", 8775, "Peg", 2.42), ("Algenib", 39, "Peg", 2.83),
    ("Ankaa", 99, "Phe", 2.40), ("Atria", 6217, "TrA", 1.92), ("Sadalsuud", 8232, "Aqr", 2.91),
    ("Sadalmelik", 8414, "Aqr", 2.96), ("Deneb Algedi", 8322, "Cap", 2.87), ("Tarazed", 7525, "Aql", 2.72),
    ("Alshain", 7602, "Aql", 3.71), ("Sheliak", 7106, "Lyr", 3.52), ("Sulafat", 7178, "Lyr", 3.25),
    ("Rasalgethi", 6406, "Her", 3.37), ("Nekkar", 5602, "Boo", 3.50), ("Seginus", 5435, "Boo", 3.04),
    ("Arneb", 1865, "Lep", 2.58), ("Nihal", 1829, "Lep", 2.84), ("Cursa", 1666, "Eri", 2.79),
    ("Acubens", 3572, "Cnc", 4.25), ("Zosma", 4357, "Leo", 2.56), ("Sabik", 6378, "Oph", 2.43),
]


def main():
    url = (os.getenv("DATABASE_URL_SYNC") or os.getenv("DATABASE_URL", "")).replace("+asyncpg", "")
    eng = create_engine(url)
    with eng.begin() as conn:
        rows = {r[0]: r for r in conn.execute(text(
            "SELECT catalog_id, id, iau_abbreviation, magnitude FROM stars"))}
        cleared = conn.execute(text(
            "UPDATE stars SET proper_name = 'HR ' || catalog_id WHERE proper_name NOT LIKE 'HR %'")).rowcount
        print("old names cleared:", cleared)

        named, missing, rejected = 0, [], []
        for name, hr, abbr, v in STARS:
            r = rows.get(hr)
            if r is None:
                missing.append(f"{name} (HR {hr})")
                continue
            if (r[2] or "").lower() != abbr.lower() or r[3] is None or abs(float(r[3]) - v) > TOL:
                rejected.append(f"{name}: HR {hr} is {r[2]} mag {r[3]}, expected {abbr} ~{v}")
                continue
            conn.execute(text("UPDATE stars SET proper_name = :n WHERE catalog_id = :h"), {"n": name, "h": hr})
            named += 1

        print(f"named={named} rejected={len(rejected)} not_in_table={len(missing)} (of {len(STARS)})")
        if rejected:
            print("\nREJECTED (left as HR n):")
            for x in rejected:
                print("  ", x)
        if missing:
            print("\nNOT IN TABLE:", "; ".join(missing))
    eng.dispose()


if __name__ == "__main__":
    main()