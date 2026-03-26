#!/usr/bin/env python3
"""Galaktika - Astrologie Berechnungs-API (FastAPI) v2.0
Endpoint: POST /calculate
Body: { name, date, time, timezone, latitude, longitude, location }
Neu: retrograde Flags, Fixsterne, Chiron
"""

from __future__ import annotations
from datetime import datetime, timezone
from itertools import combinations
from zoneinfo import ZoneInfo

import swisseph as swe
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

EPHE_PATH = "/opt/n8n/horoscope/ephe"

SIGNS = (
    "Widder", "Stier", "Zwillinge", "Krebs", "Löwe", "Jungfrau",
    "Waage", "Skorpion", "Schütze", "Steinbock", "Wassermann", "Fische",
)

PLANETS = {
    "sun":     swe.SUN,
    "moon":    swe.MOON,
    "mercury": swe.MERCURY,
    "venus":   swe.VENUS,
    "mars":    swe.MARS,
    "jupiter": swe.JUPITER,
    "saturn":  swe.SATURN,
    "uranus":  swe.URANUS,
    "neptune": swe.NEPTUNE,
    "pluto":   swe.PLUTO,
    "chiron":  swe.CHIRON,
    "lilith":  swe.MEAN_APOG,
    "knoten":  swe.TRUE_NODE,
}

ASPECTS = {
    "Konjunktion": (0.0,   8.0),
    "Sextil":      (60.0,  5.0),
    "Quadrat":     (90.0,  7.0),
    "Trigon":      (120.0, 7.0),
    "Opposition":  (180.0, 8.0),
}

PLANET_DE = {
    "sun":     "Sonne",
    "moon":    "Mond",
    "mercury": "Merkur",
    "venus":   "Venus",
    "mars":    "Mars",
    "jupiter": "Jupiter",
    "saturn":  "Saturn",
    "uranus":  "Uranus",
    "neptune": "Neptun",
    "pluto":   "Pluto",
    "chiron":  "Chiron",
    "lilith":  "Lilith",
    "knoten":  "Mondknoten",
    "ac":      "Aszendent",
    "mc":      "Midheaven",
}

# Fixsterne die berechnet werden sollen
FIXED_STARS = [
    "Regulus", "Sirius", "Algol", "Spica", "Antares", "Aldebaran",
    "Vega", "Fomalhaut",
]

# Planeten die rückläufig sein können (Sonne/Mond/Knoten/Lilith nie rückläufig)
RETROGRADE_PLANETS = {
    "mercury", "venus", "mars", "jupiter", "saturn",
    "uranus", "neptune", "pluto", "chiron",
}


class BirthData(BaseModel):
    name:      str = "Unbekannte Person"
    date:      str                        # YYYY-MM-DD
    time:      str = "12:00"              # HH:MM
    timezone:  str = "UTC"               # IANA timezone
    latitude:  float
    longitude: float
    location:  str = ""
    email:     str = ""


def zodiac(longitude: float) -> tuple[str, float]:
    n = longitude % 360.0
    return SIGNS[int(n // 30) % 12], round(n % 30.0, 4)


def angular_distance(a1: float, a2: float) -> float:
    d = abs((a1 - a2) % 360.0)
    return d if d <= 180.0 else 360.0 - d


def calc_chart(data: BirthData) -> dict:
    swe.set_ephe_path(EPHE_PATH)

    local_zone = ZoneInfo(data.timezone)
    dt_local = datetime.fromisoformat(f"{data.date}T{data.time}")
    if dt_local.tzinfo is None:
        dt_local = dt_local.replace(tzinfo=local_zone)
    dt_utc = dt_local.astimezone(timezone.utc)

    hour_ut = dt_utc.hour + dt_utc.minute / 60.0 + dt_utc.second / 3600.0
    jd = swe.julday(dt_utc.year, dt_utc.month, dt_utc.day, hour_ut, swe.GREG_CAL)

    # Planeten berechnen (mit Speed-Flag für Rückläufigkeit)
    positions: dict[str, float] = {}
    retrograde: dict[str, bool] = {}
    for name, body in PLANETS.items():
        try:
            pos, _ = swe.calc_ut(jd, body, swe.FLG_MOSEPH | swe.FLG_SPEED)
            positions[name] = round(pos[0] % 360.0, 6)
            if name in RETROGRADE_PLANETS:
                retrograde[name] = pos[3] < 0
        except Exception:
            pass  # Chiron kann in seltenen Fällen fehlen

    # Häuser (Placidus)
    cusps_raw, ascmc = swe.houses_ex(jd, data.latitude, data.longitude, b"P", swe.FLG_MOSEPH)
    cusps = [round(c % 360.0, 6) for c in cusps_raw[:12]]
    positions["ac"] = round(ascmc[0] % 360.0, 6)
    positions["mc"] = round(ascmc[1] % 360.0, 6)

    # Zodiakzeichen
    planet_signs = {k: list(zodiac(v)) for k, v in positions.items()}
    house_signs = [list(zodiac(c)) for c in cusps]

    # Aspekte
    aspects = []
    for b1, b2 in combinations(positions.keys(), 2):
        sep = angular_distance(positions[b1], positions[b2])
        for aname, (angle, orb) in ASPECTS.items():
            dev = abs(sep - angle)
            if dev <= orb:
                aspects.append({
                    "body1": b1, "body2": b2, "aspect": aname,
                    "angle": angle,
                    "orb": round(dev, 3),
                    "separation": round(sep, 3),
                })
    aspects.sort(key=lambda x: x["orb"])

    # Fixsterne berechnen
    fixstars = {}
    fixstar_conjunctions = []
    for star in FIXED_STARS:
        try:
            result, stnam, serr = swe.fixstar2_ut(star, jd, swe.FLG_MOSEPH)
            star_lon = result[0] % 360.0
            s_sign, s_deg = zodiac(star_lon)
            fixstars[star.lower()] = {
                "lon":    round(star_lon, 4),
                "sign":   s_sign,
                "degree": round(s_deg, 4),
            }
            # Konjunktionen zu Planeten (Orb <= 1.5°)
            for p_name, p_lon in positions.items():
                if p_name in ("ac", "mc"):
                    continue
                dist = angular_distance(star_lon, p_lon)
                if dist <= 1.5:
                    fixstar_conjunctions.append({
                        "star":   star,
                        "planet": p_name,
                        "orb":    round(dist, 3),
                    })
        except Exception:
            pass

    # Lesbares Text-Format für LLM
    lines = ["=== PLANETENKONSTELLATIONEN ==="]
    for k in list(PLANETS.keys()):
        if k not in positions:
            continue
        sign, deg = planet_signs[k]
        rx_marker = " \u211e" if retrograde.get(k) else ""
        lines.append(f"  {PLANET_DE.get(k, k):<12}: {deg:6.2f}° {sign}{rx_marker}")
    lines.append(f"  {'Aszendent':<12}: {planet_signs['ac'][1]:6.2f}° {planet_signs['ac'][0]}")
    lines.append(f"  {'Midheaven':<12}: {planet_signs['mc'][1]:6.2f}° {planet_signs['mc'][0]}")

    # Rückläufige Planeten
    rx_planets = [PLANET_DE.get(k, k) for k, v in retrograde.items() if v]
    if rx_planets:
        lines.append("")
        lines.append("=== RÜCKLÄUFIGE PLANETEN ===")
        for p in rx_planets:
            lines.append(f"  {p} \u211e (rückläufig zum Geburtszeitpunkt)")

    lines.append("")
    lines.append("=== HÄUSER (Placidus) ===")
    for i, c in enumerate(cusps, 1):
        sign, deg = house_signs[i - 1]
        lines.append(f"  Haus {i:>2}: {deg:6.2f}° {sign}")

    lines.append("")
    lines.append("=== ASPEKTE (Major) ===")
    for asp in aspects[:25]:
        n1 = PLANET_DE.get(asp["body1"], asp["body1"])
        n2 = PLANET_DE.get(asp["body2"], asp["body2"])
        lines.append(f"  {n1:<12} {asp['aspect']:<12} {n2:<12}  Orb: {asp['orb']:.1f}°")

    if fixstars:
        lines.append("")
        lines.append("=== FIXSTERNE ===")
        for star_name, info in fixstars.items():
            lines.append(f"  {star_name.capitalize():<12}: {info['degree']:6.2f}° {info['sign']}")

    if fixstar_conjunctions:
        lines.append("")
        lines.append("=== FIXSTERN-KONJUNKTIONEN (Orb <= 1.5°) ===")
        for conj in fixstar_conjunctions:
            p_de = PLANET_DE.get(conj["planet"], conj["planet"])
            lines.append(f"  {conj['star']:<12} Konjunktion {p_de:<12}  Orb: {conj['orb']:.1f}°")

    return {
        "jd_ut":                jd,
        "date":                 data.date,
        "time":                 data.time,
        "timezone":             data.timezone,
        "latitude":             data.latitude,
        "longitude":            data.longitude,
        "name":                 data.name,
        "email":                data.email,
        "location":             data.location,
        "planets":              positions,
        "planet_signs":         planet_signs,
        "retrograde":           retrograde,
        "houses":               cusps,
        "house_signs":          house_signs,
        "ac":                   positions["ac"],
        "mc":                   positions["mc"],
        "aspects":              aspects,
        "fixstars":             fixstars,
        "fixstar_conjunctions": fixstar_conjunctions,
        "chart_text":           "\n".join(lines),
    }


app = FastAPI(title="Galaktika Horoscope Engine", version="2.0")


@app.get("/health")
def health():
    return {"status": "ok", "version": "2.0"}


@app.post("/calculate")
def calculate(data: BirthData):
    try:
        chart = calc_chart(data)
        return chart
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
