import uuid
import os
import urllib.request
from fastapi import FastAPI, HTTPException
from fastapi.responses import Response
from pydantic import BaseModel
from typing import Optional, Dict
from chart_svg import generate_radix_svg, generate_radix_html_wrapper
try:
    import cairosvg
    HAS_CAIRO = True
except ImportError:
    HAS_CAIRO = False

app = FastAPI()

RADIX_DIR = "/horoskope-web/gen/radix"
RADIX_BASE_URL = "https://galaktika-horoskop.de/gen/radix"

IMAGES_DIR      = "/horoskope-web/gen/img"
IMAGES_BASE_URL = "https://galaktika-horoskop.de/gen/img"
OPENAI_API_KEY  = os.environ.get("OPENAI_API_KEY", "")

TEMPLATE_PATH  = "/horoskope-web/premium-template-v2.html"
HOROSKOPE_DIR  = "/horoskope-web/gen"
HOROSKOPE_BASE = "https://galaktika-horoskop.de/gen"

ZODIAC_DE = [
    'Widder', 'Stier', 'Zwillinge', 'Krebs', 'Löwe', 'Jungfrau',
    'Waage', 'Skorpion', 'Schütze', 'Steinbock', 'Wassermann', 'Fische'
]

# Key names as returned by Python Berechnung API
PLANET_KEY_MAP = {
    'sun':     'SONNE',
    'moon':    'MOND',
    'mercury': 'MERKUR',
    'venus':   'VENUS',
    'mars':    'MARS',
    'jupiter': 'JUPITER',
    'saturn':  'SATURN',
    'uranus':  'URANUS',
    'neptune': 'NEPTUN',
    'pluto':   'PLUTO',
    'lilith':  'LILITH',
    'knoten':  'NORDKNOTEN',
}


def calc_lebenszahl(geburtstag: str) -> dict:
    """Calculate numerology life path number from date string like '15.04.1990'."""
    digits = [int(c) for c in geburtstag if c.isdigit()]
    if not digits:
        return {'number': 0, 'is_master': False, 'schritte': ''}
    total = sum(digits)
    parts = [' + '.join(str(d) for d in digits) + f' = {total}']
    MASTER = {11, 22, 33}
    while total > 9 and total not in MASTER:
        new_total = sum(int(c) for c in str(total))
        parts.append(' + '.join(str(d) for d in str(total)) + f' = {new_total}')
        total = new_total
    return {'number': total, 'is_master': total in MASTER, 'schritte': ' \u2192 '.join(parts)}


def lon_to_pos(lon: float) -> str:
    lon = lon % 360
    sign_idx = int(lon / 30)
    deg_in_sign = lon % 30
    d = int(deg_in_sign)
    m = int((deg_in_sign - d) * 60)
    return f"{d}°{m:02d}′ {ZODIAC_DE[sign_idx]}"


def lon_to_deg(lon: float) -> str:
    return f"{lon % 360:.2f}"


def fmt_coord(val: float, pos_label: str, neg_label: str) -> str:
    label = pos_label if val >= 0 else neg_label
    return f"{abs(val):.4f}° {label}"


class ChartRequest(BaseModel):
    planets: dict
    ascendant: Optional[float] = 0.0


class HoroskopHtmlRequest(BaseModel):
    uuid: str
    name: str
    geburtstag: str
    geburtszeit: str
    geburtsort: str
    planets: dict
    ascendant: Optional[float] = 0.0
    content: Dict[str, Optional[str]]
    gamma_url: Optional[str] = ""
    export_url: Optional[str] = ""
    jd_ut: Optional[float] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/chart-svg")
def chart_svg(req: ChartRequest):
    svg = generate_radix_svg(req.planets, req.ascendant)
    return Response(content=svg, media_type="image/svg+xml")


@app.post("/chart-save")
def chart_save(req: ChartRequest):
    os.makedirs(RADIX_DIR, exist_ok=True)
    svg = generate_radix_svg(req.planets, req.ascendant)
    base_name = str(uuid.uuid4())

    svg_filename = f"{base_name}.svg"
    svg_path = os.path.join(RADIX_DIR, svg_filename)
    with open(svg_path, "w", encoding="utf-8") as f:
        f.write(svg)

    png_url = None
    if HAS_CAIRO:
        png_filename = f"{base_name}.png"
        png_path = os.path.join(RADIX_DIR, png_filename)
        with open(svg_path, 'rb') as _f:
            cairosvg.svg2png(bytestring=_f.read(), write_to=png_path, output_width=900)
        png_url = f"{RADIX_BASE_URL}/{png_filename}"

    return {
        "url": f"{RADIX_BASE_URL}/{svg_filename}",
        "png_url": png_url or f"{RADIX_BASE_URL}/{svg_filename}",
    }


class ImageEnsureRequest(BaseModel):
    filename: str        # e.g. "sonne-im-stier.jpg"
    prompt: str          # DALL-E prompt
    size: Optional[str] = "1024x1024"


@app.post("/image-ensure")
def image_ensure(req: ImageEnsureRequest):
    """Check if image exists in library, generate with DALL-E if not."""
    os.makedirs(IMAGES_DIR, exist_ok=True)

    # Sanitize filename
    safe_name = os.path.basename(req.filename)
    path = os.path.join(IMAGES_DIR, safe_name)
    url  = f"{IMAGES_BASE_URL}/{safe_name}"

    if os.path.exists(path):
        return {"url": url, "generated": False}

    if not OPENAI_API_KEY:
        raise HTTPException(status_code=500, detail="OPENAI_API_KEY not set")

    from openai import OpenAI
    client = OpenAI(api_key=OPENAI_API_KEY)
    response = client.images.generate(
        model="dall-e-3",
        prompt=req.prompt,
        size=req.size,
        quality="standard",
        n=1,
    )
    image_url = response.data[0].url
    urllib.request.urlretrieve(image_url, path)
    return {"url": url, "generated": True}


@app.post("/horoskop-html")
def horoskop_html(req: HoroskopHtmlRequest):
    os.makedirs(HOROSKOPE_DIR, exist_ok=True)
    with open(TEMPLATE_PATH, "r", encoding="utf-8") as f:
        html = f.read()

    svg = generate_radix_svg(req.planets, req.ascendant)
    radix_widget = generate_radix_html_wrapper(svg)

    # Basic fields
    html = html.replace("{{NAME}}", req.name)
    html = html.replace("{{GEBURTSTAG}}", req.geburtstag)
    html = html.replace("{{GEBURTSZEIT}}", req.geburtszeit)
    html = html.replace("{{GEBURTSORT}}", req.geburtsort)
    html = html.replace("{{RADIX_SVG}}", radix_widget)

    jd_str = f"{req.jd_ut:.2f}" if req.jd_ut is not None else ""
    html = html.replace("{{JD_UT}}", jd_str)

    lat_str = fmt_coord(req.latitude, "N", "S") if req.latitude is not None else ""
    lon_str = fmt_coord(req.longitude, "E", "W") if req.longitude is not None else ""
    html = html.replace("{{LAT}}", lat_str)
    html = html.replace("{{LON}}", lon_str)

    # Planet positions
    for eng_name, de_key in PLANET_KEY_MAP.items():
        raw = req.planets.get(eng_name)
        if raw is None:
            continue
        try:
            if isinstance(raw, dict):
                lon_f = float(raw.get('lon', raw.get('longitude', 0)))
                is_ret = bool(raw.get('retrograde', raw.get('ret', False)))
            else:
                lon_f = float(raw)
                is_ret = False
            html = html.replace(f"{{{{{f'POS_{de_key}'}}}}}", lon_to_pos(lon_f))
            html = html.replace(f"{{{{{f'DEG_{de_key}'}}}}}", lon_to_deg(lon_f))
            html = html.replace(f"{{{{{f'RET_{de_key}'}}}}}", "\u211e" if is_ret else "")
        except (TypeError, ValueError):
            pass

    # Lebenszahl
    lz = calc_lebenszahl(req.geburtstag)
    html = html.replace("{{LEBENSZAHL}}", str(lz['number']))
    html = html.replace("{{LEBENSZAHL_MASTER}}", "&#10022; Meisterzahl" if lz['is_master'] else "")
    html = html.replace("{{LEBENSZAHL_SCHRITTE}}", lz['schritte'])
    # Pass to content so Claude prompt can reference it
    req.content.setdefault("LEBENSZAHL_ZAHL", str(lz['number']))
    req.content.setdefault("LEBENSZAHL_IST_MEISTER", "ja" if lz['is_master'] else "nein")

    # Ascendant / DC / MC / IC
    if req.ascendant:
        ac = req.ascendant
        html = html.replace("{{POS_ASC}}", lon_to_pos(ac))
        html = html.replace("{{DEG_ASC}}", lon_to_deg(ac))
        dsc = (ac + 180) % 360
        html = html.replace("{{POS_DSC}}", lon_to_pos(dsc))
        html = html.replace("{{DEG_DSC}}", lon_to_deg(dsc))
        mc = req.planets.get('mc', (ac + 90) % 360)
        try:
            mc = float(mc)
        except (TypeError, ValueError):
            mc = (ac + 90) % 360
        html = html.replace("{{POS_MC}}", lon_to_pos(mc))
        html = html.replace("{{DEG_MC}}", lon_to_deg(mc))
        ic = (mc + 180) % 360
        html = html.replace("{{POS_IC}}", lon_to_pos(ic))
        html = html.replace("{{DEG_IC}}", lon_to_deg(ic))

    # Claude content fields
    for key, val in req.content.items():
        html = html.replace("{{" + key + "}}", val or "")

    # Gamma embed section
    if req.gamma_url:
        pdf_btn = (
            f' &nbsp;<a href="{req.export_url}" target="_blank" '
            'style="background:transparent;color:#c9a96e;border:1px solid #c9a96e;'
            'padding:14px 28px;border-radius:8px;text-decoration:none;font-weight:bold;font-size:15px;">'
            '&#128196; PDF herunterladen</a>'
        ) if req.export_url else ""
        gamma_embed = (
            '<div style="padding:4mm 8mm;">'
            '<div class="page-header">'
            f'<span class="page-header-name">{req.name} \u00b7 {req.geburtstag}</span>'
            '<span class="page-header-logo">\u2728 GALAKTIKA</span>'
            '</div>'
            '<div style="text-align:center;padding:60px 20px;background:rgba(201,169,110,0.05);'
            'border:1px solid rgba(201,169,110,0.3);border-radius:12px;margin-top:20px;">'
            '<div style="font-size:48px;margin-bottom:16px;">\u2728</div>'
            '<h2 style="color:#c9a96e;font-family:Georgia,serif;margin-bottom:8px;">'
            'Deine Premium-Pr\u00e4sentation</h2>'
            f'<p style="color:#9d89c9;margin-bottom:32px;">'
            f'Pers\u00f6nliches Geburtshoroskop \u00b7 {req.name}</p>'
            f'<a href="{req.gamma_url}" target="_blank" '
            'style="background:#c9a96e;color:#05050f;padding:14px 32px;border-radius:8px;'
            'text-decoration:none;font-weight:bold;font-size:15px;">'
            '&#127775; Pr\u00e4sentation \u00f6ffnen</a>'
            f'{pdf_btn}'
            '</div>'
            '</div>'
        )
    else:
        gamma_embed = ""
    html = html.replace("{{GAMMA_EMBED}}", gamma_embed)

    # PDF download block in outro
    if req.export_url:
        gamma_block = (
            '<div style="text-align:center;margin:2rem 0;">'
            f'<a href="{req.export_url}" target="_blank" '
            'style="background:#c9a96e;color:#05050f;padding:14px 32px;border-radius:8px;'
            'text-decoration:none;font-weight:bold;font-size:15px;">'
            '&#128196; Horoskop als PDF herunterladen</a>'
            '</div>'
        )
    elif req.gamma_url:
        gamma_block = (
            '<div style="text-align:center;margin:2rem 0;">'
            f'<a href="{req.gamma_url}" target="_blank" '
            'style="color:#c9a96e;text-decoration:none;font-size:14px;">'
            'Pr\u00e4sentation \u00f6ffnen</a>'
            '</div>'
        )
    else:
        gamma_block = ""
    html = html.replace("{{GAMMA_DOWNLOAD_BLOCK}}", gamma_block)

    path = os.path.join(HOROSKOPE_DIR, f"{req.uuid}.html")
    with open(path, "w", encoding="utf-8") as f:
        f.write(html)
    return {"url": f"{HOROSKOPE_BASE}/{req.uuid}.html"}
