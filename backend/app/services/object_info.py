"""Live facts about sky objects: planets, Sun, Moon (pure-Python ephemeris) and stars (HYG v4.2 catalogue)."""
from __future__ import annotations

import csv
import math
import os
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

AU_KM = 149597870.7
C_KM_S = 299792.458
DEG = math.pi / 180.0

# JPL "Keplerian elements for approximate positions" (valid 1800-2050): a, e, I, L, long.peri, long.node (value, rate/century)
_EL = {
    "mercury": (0.38709927, 0.00000037, 0.20563593, 0.00001906, 7.00497902, -0.00594749, 252.25032350, 149472.67411175, 77.45779628, 0.16047689, 48.33076593, -0.12534081),
    "venus": (0.72333566, 0.00000390, 0.00677672, -0.00004107, 3.39467605, -0.00078890, 181.97909950, 58517.81538729, 131.60246718, 0.00268329, 76.67984255, -0.27769418),
    "earth": (1.00000261, 0.00000562, 0.01671123, -0.00004392, -0.00001531, -0.01294668, 100.46457166, 35999.37244981, 102.93768193, 0.32327364, 0.0, 0.0),
    "mars": (1.52371034, 0.00001847, 0.09339410, 0.00007882, 1.84969142, -0.00813131, -4.55343205, 19140.30268499, -23.94362959, 0.44441088, 49.55953891, -0.29257343),
    "jupiter": (5.20288700, -0.00011607, 0.04838624, -0.00013253, 1.30439695, -0.00183714, 34.39644051, 3034.74612775, 14.72847983, 0.21252668, 100.47390909, 0.20469106),
    "saturn": (9.53667594, -0.00125060, 0.05386179, -0.00050991, 2.48599187, 0.00193609, 49.95424423, 1222.49362201, 92.59887831, -0.41897216, 113.66242448, -0.28867794),
    "uranus": (19.18916464, -0.00196176, 0.04725744, -0.00004397, 0.77263783, -0.00242939, 313.23810451, 428.48202785, 170.95427630, 0.40805281, 74.01692503, 0.04240589),
    "neptune": (30.06992276, 0.00026291, 0.00859048, 0.00005105, 1.77004347, 0.00035372, -55.12002969, 218.45945325, 44.96476227, -0.32241464, 131.78422574, -0.00508664),
}
_RADIUS_KM = {"sun": 695700.0, "moon": 1737.4, "mercury": 2439.7, "venus": 6051.8, "mars": 3389.5,
              "jupiter": 69911.0, "saturn": 58232.0, "uranus": 25362.0, "neptune": 24622.0}
_H = {"mercury": -0.42, "venus": -4.40, "mars": -1.52, "jupiter": -9.40, "saturn": -8.88, "uranus": -7.19, "neptune": -6.87}
_PHASE = {"mercury": (0.0380, -0.000273, 2e-6), "venus": (0.0009, 0.000239, -6.5e-7), "mars": (0.016, 0, 0),
          "jupiter": (0.005, 0, 0), "saturn": (0, 0, 0), "uranus": (0, 0, 0), "neptune": (0, 0, 0)}


def _jd(when: datetime) -> float:
    if when.tzinfo is None:
        when = when.replace(tzinfo=timezone.utc)
    return when.timestamp() / 86400.0 + 2440587.5


def _helio(name: str, T: float):
    a0, da, e0, de, i0, di, L0, dL, w0, dw, o0, do = _EL[name]
    a = a0 + da * T
    e = e0 + de * T
    inc = (i0 + di * T) * DEG
    L = L0 + dL * T
    w = w0 + dw * T
    node = (o0 + do * T) * DEG
    arg = (w - (o0 + do * T)) * DEG
    M = math.radians(((L - w) + 180.0) % 360.0 - 180.0)
    E = M
    for _ in range(12):
        E -= (E - e * math.sin(E) - M) / (1.0 - e * math.cos(E))
    xp = a * (math.cos(E) - e)
    yp = a * math.sqrt(1 - e * e) * math.sin(E)
    cw, sw, co, so, ci, si = math.cos(arg), math.sin(arg), math.cos(node), math.sin(node), math.cos(inc), math.sin(inc)
    x = (cw * co - sw * so * ci) * xp + (-sw * co - cw * so * ci) * yp
    y = (cw * so + sw * co * ci) * xp + (-sw * so + cw * co * ci) * yp
    z = (sw * si) * xp + (cw * si) * yp
    return x, y, z


def _norm(v):
    return math.sqrt(v[0] ** 2 + v[1] ** 2 + v[2] ** 2)


def _angle(a, b):
    d = sum(x * y for x, y in zip(a, b)) / (_norm(a) * _norm(b))
    return math.degrees(math.acos(max(-1.0, min(1.0, d))))


def _fmt(x: float, nd: int = 0) -> str:
    return f"{x:,.{nd}f}"


def _moon_distance_km(T: float) -> float:
    D = math.radians(297.8501921 + 445267.1114034 * T)
    M = math.radians(357.5291092 + 35999.0502909 * T)
    Mp = math.radians(134.9633964 + 477198.8675055 * T)
    F = math.radians(93.2720950 + 483202.0175233 * T)
    return (385000.56 - 20905.355 * math.cos(Mp) - 3699.111 * math.cos(2 * D - Mp)
            - 2955.968 * math.cos(2 * D) - 569.925 * math.cos(2 * Mp) + 48.888 * math.cos(M)
            - 3.149 * math.cos(2 * F) + 246.158 * math.cos(2 * D - 2 * Mp) - 152.138 * math.cos(2 * D - M - Mp))


def _ang_size(radius_km: float, dist_km: float) -> float:
    return math.degrees(2 * math.atan(radius_km / dist_km)) * 3600.0  # arcseconds


def _ang_text(arcsec: float) -> str:
    return f"{arcsec / 60:.1f} arcmin" if arcsec >= 120 else f"{arcsec:.1f} arcsec"


def _light_time(km: float) -> str:
    s = km / C_KM_S
    if s < 120:
        return f"{s:.2f} seconds"
    if s < 7200:
        return f"{int(s // 60)} min {int(s % 60)} s"
    return f"{s / 3600:.2f} hours"


def body_info(key: str, when: Optional[datetime] = None) -> Optional[Dict[str, Any]]:
    key = key.lower()
    when = when or datetime.now(timezone.utc)
    T = (_jd(when) - 2451545.0) / 36525.0
    earth = _helio("earth", T)
    R = _norm(earth)
    rows: List[List[str]] = []
    if key == "sun":
        km = R * AU_KM
        rows = [["Distance from Earth", f"{_fmt(km)} km ({R:.4f} AU)"],
                ["Light travel time", _light_time(km)],
                ["Apparent size", _ang_text(_ang_size(_RADIUS_KM['sun'], km))],
                ["Apparent magnitude", f"{-26.74 + 5 * math.log10(R):.2f}"],
                ["Earth's position", "closest to the Sun in early January, farthest in early July"]]
    elif key == "moon":
        km = _moon_distance_km(T)
        pos = (km - 356500) / (406700 - 356500)
        rows = [["Distance from Earth", f"{_fmt(km)} km"],
                ["Light travel time", _light_time(km)],
                ["Apparent size", _ang_text(_ang_size(_RADIUS_KM['moon'], km))],
                ["Orbit position", f"{max(0, min(1, pos)) * 100:.0f}% of the way from perigee (closest) to apogee (farthest)"],
                ["Approx. brightness at full", "magnitude -12.7"]]
    elif key in _H:
        p = _helio(key, T)
        g = (p[0] - earth[0], p[1] - earth[1], p[2] - earth[2])
        d = _norm(g)
        r = _norm(p)
        sun_dir = (-earth[0], -earth[1], -earth[2])
        elong = _angle(g, sun_dir)
        cos_i = (r * r + d * d - R * R) / (2 * r * d)
        i = math.degrees(math.acos(max(-1.0, min(1.0, cos_i))))
        ill = (1 + cos_i) / 2 * 100
        k1, k2, k3 = _PHASE[key]
        mag = _H[key] + 5 * math.log10(r * d) + k1 * i + k2 * i * i + k3 * i ** 3
        km = d * AU_KM
        # which side of the Sun: compare ecliptic longitudes
        lon_p = math.atan2(g[1], g[0])
        lon_s = math.atan2(sun_dir[1], sun_dir[0])
        diff = (math.degrees(lon_p - lon_s) + 180) % 360 - 180
        side = "east of the Sun (evening sky)" if diff > 0 else "west of the Sun (morning sky)"
        if key in ("mercury", "venus"):
            note = "inner planet, never far from the Sun"
        else:
            note = "outer planet, " + ("near opposition (best time to observe)" if elong > 165 else
                                         "close to the Sun in the sky (poor viewing)" if elong < 30 else "well placed")
        rows = [["Distance from Earth", f"{_fmt(km)} km ({d:.3f} AU)"],
                ["Distance from Sun", f"{_fmt(r * AU_KM)} km ({r:.3f} AU)"],
                ["Light travel time", _light_time(km)],
                ["Apparent size", _ang_text(_ang_size(_RADIUS_KM[key], km))],
                ["Apparent magnitude", f"{mag:.1f}" + (" (ring brightening not included)" if key == "saturn" else "")],
                ["Illuminated", f"{ill:.0f}%"],
                ["Elongation from Sun", f"{elong:.0f}°, {side}"],
                ["Viewing", note]]
    else:
        return None
    return {"kind": "body", "key": key, "time": when.isoformat(),
            "sections": [{"title": "Live data", "rows": rows}]}


# ---------------------------------------------------------------- stars
_CON = {
    "And": "Andromeda", "Ant": "Antlia", "Aps": "Apus", "Aqr": "Aquarius", "Aql": "Aquila", "Ara": "Ara", "Ari": "Aries",
    "Aur": "Auriga", "Boo": "Bootes", "Cae": "Caelum", "Cam": "Camelopardalis", "Cnc": "Cancer", "CVn": "Canes Venatici",
    "CMa": "Canis Major", "CMi": "Canis Minor", "Cap": "Capricornus", "Car": "Carina", "Cas": "Cassiopeia", "Cen": "Centaurus",
    "Cep": "Cepheus", "Cet": "Cetus", "Cha": "Chamaeleon", "Cir": "Circinus", "Col": "Columba", "Com": "Coma Berenices",
    "CrA": "Corona Australis", "CrB": "Corona Borealis", "Crv": "Corvus", "Crt": "Crater", "Cru": "Crux", "Cyg": "Cygnus",
    "Del": "Delphinus", "Dor": "Dorado", "Dra": "Draco", "Equ": "Equuleus", "Eri": "Eridanus", "For": "Fornax", "Gem": "Gemini",
    "Gru": "Grus", "Her": "Hercules", "Hor": "Horologium", "Hya": "Hydra", "Hyi": "Hydrus", "Ind": "Indus", "Lac": "Lacerta",
    "Leo": "Leo", "LMi": "Leo Minor", "Lep": "Lepus", "Lib": "Libra", "Lup": "Lupus", "Lyn": "Lynx", "Lyr": "Lyra",
    "Men": "Mensa", "Mic": "Microscopium", "Mon": "Monoceros", "Mus": "Musca", "Nor": "Norma", "Oct": "Octans", "Oph": "Ophiuchus",
    "Ori": "Orion", "Pav": "Pavo", "Peg": "Pegasus", "Per": "Perseus", "Phe": "Phoenix", "Pic": "Pictor", "Psc": "Pisces",
    "PsA": "Piscis Austrinus", "Pup": "Puppis", "Pyx": "Pyxis", "Ret": "Reticulum", "Sge": "Sagitta", "Sgr": "Sagittarius",
    "Sco": "Scorpius", "Scl": "Sculptor", "Sct": "Scutum", "Ser": "Serpens", "Sex": "Sextans", "Tau": "Taurus",
    "Tel": "Telescopium", "Tri": "Triangulum", "TrA": "Triangulum Australe", "Tuc": "Tucana", "UMa": "Ursa Major",
    "UMi": "Ursa Minor", "Vel": "Vela", "Vir": "Virgo", "Vol": "Volans", "Vul": "Vulpecula",
}
_GREEK = {"Alp": "α", "Bet": "β", "Gam": "γ", "Del": "δ", "Eps": "ε", "Zet": "ζ", "Eta": "η",
          "The": "θ", "Iot": "ι", "Kap": "κ", "Lam": "λ", "Mu": "μ", "Nu": "ν", "Xi": "ξ",
          "Omi": "ο", "Pi": "π", "Rho": "ρ", "Sig": "σ", "Tau": "τ", "Ups": "υ", "Phi": "φ",
          "Chi": "χ", "Psi": "ψ", "Ome": "ω"}
_CLASS_TXT = {
    "O": ("blue", "over 30,000 K"), "B": ("blue-white", "10,000 to 30,000 K"), "A": ("white", "7,500 to 10,000 K"),
    "F": ("yellow-white", "6,000 to 7,500 K"), "G": ("yellow", "5,200 to 6,000 K"),
    "K": ("orange", "3,700 to 5,200 K"), "M": ("red", "2,400 to 3,700 K"),
}
_LUM_TXT = {"Ia": "bright supergiant", "Iab": "supergiant", "Ib": "supergiant", "I": "supergiant", "II": "bright giant",
            "III": "giant", "IV": "subgiant", "V": "main-sequence star (dwarf)", "VI": "subdwarf"}

_hyg: Dict[int, Dict[str, str]] = {}
_hyg_loaded = False


def _hyg_path() -> Path:
    env = os.environ.get("HYG_CSV")
    if env:
        return Path(env)
    return Path(__file__).resolve().parent.parent / "data" / "hyg" / "hygdata_v42.csv"


def _load_hyg() -> None:
    global _hyg_loaded
    if _hyg_loaded:
        return
    p = _hyg_path()
    if p.exists():
        with open(p, newline="", encoding="utf-8") as f:
            for row in csv.DictReader(f):
                hr = (row.get("hr") or "").strip()
                if hr.isdigit():
                    _hyg[int(hr)] = row
    _hyg_loaded = True


def _f(row: Dict[str, str], k: str) -> Optional[float]:
    v = (row.get(k) or "").strip()
    try:
        return float(v) if v else None
    except ValueError:
        return None


def _temp_from_bv(bv: float) -> float:
    b = max(-0.4, min(2.0, bv))
    return 4600.0 * (1.0 / (0.92 * b + 1.7) + 1.0 / (0.92 * b + 0.62))


def _hms(hours: float) -> str:
    h = int(hours)
    m = int((hours - h) * 60)
    s = (hours - h - m / 60) * 3600
    return f"{h}h {m:02d}m {s:04.1f}s"


def _dms(deg: float) -> str:
    sign = "-" if deg < 0 else "+"
    a = abs(deg)
    d = int(a)
    m = int((a - d) * 60)
    s = (a - d - m / 60) * 3600
    return f"{sign}{d}° {m:02d}' {s:04.1f}\""


def star_info(hr: int, when: Optional[datetime] = None) -> Optional[Dict[str, Any]]:
    _load_hyg()
    row = _hyg.get(hr)
    if row is None:
        return None
    when = when or datetime.now(timezone.utc)
    year = when.year
    proper = (row.get("proper") or "").strip()
    bayer = (row.get("bayer") or "").strip()
    flam = (row.get("flam") or "").strip()
    con = (row.get("con") or "").strip()
    con_name = _CON.get(con, con)
    desig = ""
    if bayer:
        g = re.match(r"([A-Za-z]+)(-?\d*)", bayer)
        greek = _GREEK.get(g.group(1), g.group(1)) if g else bayer
        desig = greek + (g.group(2) if g and g.group(2) else "") + " " + con
    elif flam:
        desig = flam + " " + con

    ident = [["Name", proper or desig or f"HR {hr}"]]
    if desig and proper:
        ident.append(["Designation", desig])
    if con_name:
        ident.append(["Constellation", con_name])
    ident.append(["Catalogue numbers", ", ".join(x for x in [f"HR {hr}",
                  f"HD {row['hd']}" if (row.get('hd') or '').strip() else "",
                  f"HIP {row['hip']}" if (row.get('hip') or '').strip() else ""] if x)])
    ra, dec = _f(row, "ra"), _f(row, "dec")
    if ra is not None and dec is not None:
        ident.append(["Position (J2000)", f"RA {_hms(ra)}   Dec {_dms(dec)}"])

    mag, absmag, lum = _f(row, "mag"), _f(row, "absmag"), _f(row, "lum")
    dist_pc = _f(row, "dist")
    if dist_pc is not None and dist_pc >= 99999:
        dist_pc = None
    bright: List[List[str]] = []
    if mag is not None:
        bright.append(["Apparent magnitude", f"{mag:.2f}  (lower is brighter)"])
    if absmag is not None and dist_pc:
        bright.append(["Absolute magnitude", f"{absmag:.2f}  (brightness seen from 10 parsecs)"])
    if lum is None and absmag is not None and dist_pc:
        lum = 10 ** ((4.83 - absmag) / 2.5)
    if lum is not None:
        bright.append(["Luminosity", f"{lum:,.1f} × the Sun" if lum >= 10 else f"{lum:.3g} × the Sun"])

    dist: List[List[str]] = []
    if dist_pc:
        ly = dist_pc * 3.26156
        dist.append(["Distance", f"{ly:,.1f} light-years ({dist_pc:,.1f} parsecs)"])
        dist.append(["Distance in km", f"{ly * 9.4607e12:,.3g} km"])
        dist.append(["You are seeing it as it was", f"in the year {int(year - ly)}  (its light left {ly:,.0f} years ago)"])

    phys: List[List[str]] = []
    spect = (row.get("spect") or "").strip()
    if spect:
        phys.append(["Spectral type", spect])
        m = re.match(r"([OBAFGKM])(\d?)", spect)
        if m:
            colour, temp = _CLASS_TXT[m.group(1)]
            txt = f"Class {m.group(1)}: {colour}, typically {temp}"
            lm = re.search(r"(Iab|Ia|Ib|III|II|IV|VI|V|I)(?![a-z])", spect[1:])
            if lm and lm.group(1) in _LUM_TXT:
                txt += f", a {_LUM_TXT[lm.group(1)]}"
            phys.append(["Meaning", txt])
    ci = _f(row, "ci")
    teff = None
    if ci is not None:
        teff = _temp_from_bv(ci)
        phys.append(["Colour index (B-V)", f"{ci:.2f}"])
        phys.append(["Surface temperature (estimate)", f"about {teff:,.0f} K"])
    if lum is not None and teff:
        rad = math.sqrt(lum) * (5772.0 / teff) ** 2
        phys.append(["Radius (estimate)", f"about {rad:,.1f} × the Sun"])

    motion: List[List[str]] = []
    pmra, pmdec, rv = _f(row, "pmra"), _f(row, "pmdec"), _f(row, "rv")
    if pmra is not None and pmdec is not None:
        motion.append(["Proper motion", f"{math.hypot(pmra, pmdec):,.1f} milliarcsec per year"])
    if rv is not None and rv != 0:
        motion.append(["Radial velocity", f"{abs(rv):.1f} km/s " + ("moving away from us" if rv > 0 else "approaching us")])
    var = (row.get("var") or "").strip()
    if var:
        vmin, vmax = _f(row, "var_min"), _f(row, "var_max")
        motion.append(["Variable star", var + (f", magnitude {vmax:.2f} to {vmin:.2f}" if vmin is not None and vmax is not None else "")])

    secs = [{"title": t, "rows": r} for t, r in
            [("Identity", ident), ("Brightness", bright), ("Distance", dist), ("Physical", phys), ("Motion", motion)] if r]
    return {"kind": "star", "hr": hr, "ci": ci, "name": proper or desig or f"HR {hr}", "constellation": con_name,
            "sections": secs}
