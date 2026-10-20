import json, os, re
from sqlalchemy import create_engine, text

EXPECT = {n: a for n, a in [x.split(":") for x in (
 "Sirius:CMa Canopus:Car Arcturus:Boo Rigil_Kentaurus:Cen Vega:Lyr Capella:Aur Rigel:Ori Procyon:CMi "
 "Achernar:Eri Betelgeuse:Ori Hadar:Cen Altair:Aql Acrux:Cru Aldebaran:Tau Antares:Sco Spica:Vir Pollux:Gem "
 "Fomalhaut:PsA Deneb:Cyg Mimosa:Cru Regulus:Leo Adhara:CMa Castor:Gem Gacrux:Cru Shaula:Sco Bellatrix:Ori "
 "Elnath:Tau Miaplacidus:Car Alnilam:Ori Alnair:Gru Alnitak:Ori Alioth:UMa Dubhe:UMa Mirfak:Per Wezen:CMa "
 "Kaus_Australis:Sgr Alkaid:UMa Menkalinan:Aur Alphard:Hya Polaris:UMi Hamal:Ari Diphda:Cet Nunki:Sgr "
 "Rasalhague:Oph Kochab:UMi Saiph:Ori Denebola:Leo Algol:Per Mizar:UMa Mintaka:Ori Alpheratz:And Mirach:And "
 "Sargas:Sco Avior:Car Peacock:Pav Alhena:Gem Mirzam:CMa Schedar:Cas Caph:Cas Algieba:Leo Alderamin:Cep "
 "Menkar:Cet Izar:Boo Phact:Col Alphecca:CrB Sadr:Cyg Albireo:Cyg Zubeneschamali:Lib Zubenelgenubi:Lib "
 "Eltanin:Dra Rastaban:Dra Thuban:Dra Unukalhai:Ser Dschubba:Sco Acrab:Sco Rukbat:Sgr Alchiba:Crv Enif:Peg "
 "Markab:Peg Scheat:Peg Algenib:Peg Ankaa:Phe Atria:TrA Sadalsuud:Aqr Sadalmelik:Aqr Deneb_Algedi:Cap "
 "Tarazed:Aql Alshain:Aql Sheliak:Lyr Sulafat:Lyr Rasalgethi:Her Nekkar:Boo Seginus:Boo Arneb:Lep Nihal:Lep "
 "Cursa:Eri Acubens:Cnc Zosma:Leo Sabik:Oph").split()]}
EXPECT = {k.replace("_", " "): v for k, v in EXPECT.items()}

def dec_deg(s):
    m = re.match(r"\s*([+-]?)(\d{1,2}):(\d{2}):(\d{2}(?:\.\d+)?)", s or "")
    if not m: return None
    v = int(m.group(2)) + int(m.group(3)) / 60 + float(m.group(4)) / 3600
    return -v if m.group(1) == "-" else v

url = (os.getenv("DATABASE_URL_SYNC") or os.getenv("DATABASE_URL", "")).replace("+asyncpg", "")
eng = create_engine(url)
with eng.begin() as c:
    rows = c.execute(text('SELECT catalog_id, proper_name, iau_abbreviation, constellation, ra, "dec", magnitude FROM stars')).all()
    named = [r for r in rows if r[1] and not r[1].startswith("HR ")]
    print("rows:", len(rows), " named:", len(named))
    bad = [r for r in named if r[1] in EXPECT and (r[2] or "").lower() != EXPECT[r[1]].lower()]
    unknown = [r for r in named if r[1] not in EXPECT]
    print("\nMISMATCH (name sits on a star in the wrong constellation):")
    for r in bad: print("  HR", r[0], r[1], "| db:", r[2], "expected:", EXPECT[r[1]], "| mag", r[6], "| dec", r[5])
    print("\nnamed but not in my reference list (%d):" % len(unknown))
    for r in unknown[:40]: print("  HR", r[0], r[1], r[2], "mag", r[6])
    have = {r[1] for r in named}
    print("\nreference names with no named row:", sorted(n for n in EXPECT if n not in have))
    res = c.execute(text("UPDATE stars SET proper_name = 'HR ' || catalog_id WHERE proper_name = 'Alderamin' AND iau_abbreviation <> 'Cep'"))
    print("\nwrong Alderamin rows reset:", res.rowcount)

    decs = [d for d in (dec_deg(r[5]) for r in rows) if d is not None]
    print("\nTABLE dec range: %.1f .. %.1f ; |dec|>60: %d ; unparsable: %d" % (min(decs), max(decs), sum(1 for d in decs if abs(d) > 60), len(rows) - len(decs)))
    ids = {r[0] for r in rows}
    print("HR present:", {hr: (hr in ids) for hr in (424, 4301, 5267, 5291, 8162, 2491, 7001, 5340)})

p = "/app/app/data/stars.json"
raw = open(p, encoding="utf-8").read()
data = json.loads(raw)
recs = data.get("stars", data) if isinstance(data, dict) else data
print("\nstars.json:", type(data).__name__, "records:", len(recs), " 'polaris' mentions:", raw.lower().count("polaris"))
print("first record:", json.dumps(recs[0], ensure_ascii=False)[:420])