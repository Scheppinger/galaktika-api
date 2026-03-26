"""
Galaktika – Radix-Chart SVG Generator V2
Dark theme, interactive-ready, legend included
"""
import math


ZODIAC_NAMES_DE = [
    'Widder','Stier','Zwillinge','Krebs','Löwe','Jungfrau',
    'Waage','Skorpion','Schütze','Steinbock','Wassermann','Fische'
]


def generate_radix_svg(planets: dict, ascendant: float = 0) -> str:
    cx, cy = 450, 450
    R_OUTER       = 420
    R_ZOD_OUT     = 400
    R_ZOD_SYM     = 373
    R_ZOD_IN      = 348
    R_HOUSE_IN    = 272
    R_PLANET      = 313
    R_PNAME       = 291
    R_TICK_OUT    = 346
    R_TICK_IN     = 276
    R_ASPECT      = 185
    R_INNER       = 135

    # Dark theme
    C_BG          = '#0a0818'
    C_OUTER       = '#3a2060'
    C_ZOD_BG      = '#120a28'
    C_HOUSE_BG    = '#0e0820'
    C_INNER_BG    = '#080614'
    C_GOLD        = '#c9a96e'
    C_DIM         = '#3a2d5a'
    C_HOUSE_LINE  = '#2a1e48'
    C_TEXT        = '#e8e0ff'

    ZODIAC_SYMS = ['Y','B','C','D','E','F','G','H','I','J','K','L']
    # Unicode symbols that render reliably as text fallback
    ZODIAC_UNI  = ['♈','♉','♊','♋','♌','♍','♎','♏','♐','♑','♒','♓']

    ELEM_COLORS = [
        '#e8603a','#88a845','#4a9acc','#4a8898',
        '#e8603a','#88a845','#4a9acc','#4a8898',
        '#e8603a','#88a845','#4a9acc','#4a8898',
    ]

    # All planet symbols as simple ASCII/Latin — render on any system
    PLANET_SYMS = {
        'sun':     '☉',
        'moon':    '☽',
        'mercury': '☿',
        'venus':   '♀',
        'mars':    '♂',
        'jupiter': '♃',
        'saturn':  '♄',
        'uranus':  '♅',
        'neptune': '♆',
        'pluto':   '♇',
        'lilith':  '⚸',
        'knoten':  '☊',
    }

    PLANET_COLORS = {
        'sun':     '#f0c040',
        'moon':    '#a090e0',
        'mercury': '#60c060',
        'venus':   '#e060a0',
        'mars':    '#e04040',
        'jupiter': '#d4a040',
        'saturn':  '#80b0d0',
        'uranus':  '#60c0c0',
        'neptune': '#6080e0',
        'pluto':   '#c060c0',
        'lilith':  '#a06080',
        'knoten':  '#80d080',
    }

    PLANET_LABELS = {
        'sun':     'Sonne',
        'moon':    'Mond',
        'mercury': 'Merkur',
        'venus':   'Venus',
        'mars':    'Mars',
        'jupiter': 'Jupiter',
        'saturn':  'Saturn',
        'uranus':  'Uranus',
        'neptune': 'Neptun',
        'pluto':   'Pluto',
        'lilith':  'Lilith',
        'knoten':  'Knoten',
    }

    def polar(r, angle_deg):
        a = math.radians(angle_deg)
        return cx + r * math.cos(a), cy - r * math.sin(a)

    def ecl_to_angle(lon):
        return 180.0 - (lon - ascendant)

    # SVG canvas — wider to include legend below
    parts = []
    parts.append('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 900 1420" '
                 'width="900" height="1420">')

    # Background
    parts.append(f'<rect width="900" height="1200" fill="{C_BG}"/>')

    # Subtle star field
    import random
    rng = random.Random(42)
    for _ in range(120):
        sx = rng.randint(0, 900)
        sy = rng.randint(0, 900)
        sr = rng.uniform(0.3, 1.2)
        so = rng.uniform(0.2, 0.7)
        parts.append(f'<circle cx="{sx}" cy="{sy}" r="{sr:.1f}" fill="white" fill-opacity="{so:.2f}"/>')

    # Outer ring
    parts.append(f'<circle cx="{cx}" cy="{cy}" r="{R_OUTER}" fill="none" '
                 f'stroke="{C_OUTER}" stroke-width="1.5"/>')

    # Zodiac band
    parts.append(f'<circle cx="{cx}" cy="{cy}" r="{R_ZOD_OUT}" '
                 f'fill="{C_ZOD_BG}" stroke="{C_OUTER}" stroke-width="1"/>')
    parts.append(f'<circle cx="{cx}" cy="{cy}" r="{R_ZOD_IN}" '
                 f'fill="{C_HOUSE_BG}" stroke="{C_DIM}" stroke-width="0.8"/>')

    # Zodiac sectors + symbols
    for i in range(12):
        s_ecl = i * 30.0
        e_ecl = s_ecl + 30.0
        m_ecl = s_ecl + 15.0
        s_ang = ecl_to_angle(s_ecl)
        e_ang = ecl_to_angle(e_ecl)
        m_ang = ecl_to_angle(m_ecl)
        col   = ELEM_COLORS[i]

        x1o,y1o = polar(R_ZOD_OUT, s_ang)
        x2o,y2o = polar(R_ZOD_OUT, e_ang)
        x1i,y1i = polar(R_ZOD_IN,  s_ang)
        x2i,y2i = polar(R_ZOD_IN,  e_ang)
        parts.append(
            f'<path d="M {x1o:.1f},{y1o:.1f} A {R_ZOD_OUT},{R_ZOD_OUT} 0 0,0 {x2o:.1f},{y2o:.1f} '
            f'L {x2i:.1f},{y2i:.1f} A {R_ZOD_IN},{R_ZOD_IN} 0 0,1 {x1i:.1f},{y1i:.1f} Z" '
            f'fill="{col}" fill-opacity="0.18"/>'
        )
        # Divider lines
        xo,yo = polar(R_ZOD_OUT, s_ang)
        xi,yi = polar(R_ZOD_IN,  s_ang)
        parts.append(f'<line x1="{xo:.1f}" y1="{yo:.1f}" x2="{xi:.1f}" y2="{yi:.1f}" '
                     f'stroke="{C_DIM}" stroke-width="0.8"/>')
        # Zodiac symbol
        sx,sy = polar(R_ZOD_SYM, m_ang)
        parts.append(
            f'<text x="{sx:.1f}" y="{sy:.1f}" text-anchor="middle" dominant-baseline="central" '
            f'font-size="32" fill="{col}" fill-opacity="0.95">{ZODIAC_UNI[i]}</text>'
        )

    # House ring background
    parts.append(f'<circle cx="{cx}" cy="{cy}" r="{R_HOUSE_IN}" '
                 f'fill="{C_INNER_BG}" stroke="{C_DIM}" stroke-width="0.8"/>')

    # House lines + numbers
    for h in range(12):
        h_ang = ecl_to_angle(h * 30.0)
        xo,yo = polar(R_ZOD_IN,   h_ang)
        xi,yi = polar(R_HOUSE_IN, h_ang)
        is_angle = h in (0, 3, 6, 9)
        stroke = C_GOLD  if is_angle else C_HOUSE_LINE
        width  = '1.8'   if is_angle else '0.6'
        parts.append(f'<line x1="{xo:.1f}" y1="{yo:.1f}" x2="{xi:.1f}" y2="{yi:.1f}" '
                     f'stroke="{stroke}" stroke-width="{width}"/>')
        hm_ang = ecl_to_angle(h * 30.0 + 15.0)
        R_NUM  = (R_ZOD_IN + R_HOUSE_IN) // 2
        nx,ny  = polar(R_NUM, hm_ang)
        parts.append(
            f'<text x="{nx:.1f}" y="{ny:.1f}" text-anchor="middle" dominant-baseline="central" '
            f'font-size="17" fill="{C_TEXT}" fill-opacity="0.45" font-family="serif">{h+1}</text>'
        )

    # ASC/DSC/MC/IC labels
    for disp_ang, label in ((180,'ASC'),(0,'DSC'),(90,'MC'),(270,'IC')):
        lx,ly = polar(R_ZOD_OUT + 16, disp_ang)
        parts.append(
            f'<text x="{lx:.1f}" y="{ly:.1f}" text-anchor="middle" dominant-baseline="central" '
            f'font-size="17" fill="{C_GOLD}" font-family="sans-serif" font-weight="bold">{label}</text>'
        )

    # Inner circle
    parts.append(f'<circle cx="{cx}" cy="{cy}" r="{R_INNER}" '
                 f'fill="{C_INNER_BG}" stroke="{C_DIM}" stroke-width="0.5"/>')

    # Aspect lines
    ASPECTS = [
        (0,   8, '#c9a96e', '2.0', '0.9'),
        (60,  5, '#4499ee', '1.0', '0.6'),
        (90,  7, '#ee4422', '1.2', '0.7'),
        (120, 8, '#44aacc', '1.5', '0.8'),
        (180, 8, '#aa55ff', '1.2', '0.7'),
    ]

    p_list = [(k, v) for k, v in planets.items() if k in PLANET_SYMS]

    for i in range(len(p_list)):
        for j in range(i+1, len(p_list)):
            _, lon1 = p_list[i]
            _, lon2 = p_list[j]
            diff = abs(lon1 - lon2)
            if diff > 180: diff = 360 - diff
            for asp, orb, col, w, op in ASPECTS:
                if abs(diff - asp) <= orb:
                    a1, a2 = ecl_to_angle(lon1), ecl_to_angle(lon2)
                    x1,y1 = polar(R_ASPECT, a1)
                    x2,y2 = polar(R_ASPECT, a2)
                    parts.append(
                        f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" '
                        f'stroke="{col}" stroke-width="{w}" stroke-opacity="{op}"/>'
                    )
                    break

    # Planet placement with collision avoidance
    placed = []

    def find_r(disp_ang):
        for pa, pr in placed:
            d = abs(disp_ang - pa) % 360
            if d > 180: d = 360 - d
            if d < 13:
                return R_PLANET - 32
        return R_PLANET

    for p_name, p_lon in p_list:
        disp_ang = ecl_to_angle(p_lon)
        r_use    = find_r(disp_ang)
        placed.append((disp_ang, r_use))
        sym   = PLANET_SYMS[p_name]
        col   = PLANET_COLORS[p_name]
        fsize = '34' if p_name in ('sun','moon') else '28'
        px,py = polar(r_use, disp_ang)

        # Background circle for readability
        parts.append(f'<circle cx="{px:.1f}" cy="{py:.1f}" r="17" '
                     f'fill="{C_BG}" fill-opacity="0.88" stroke="{col}" stroke-width="0.6" stroke-opacity="0.5"/>')
        parts.append(
            f'<text x="{px:.1f}" y="{py:.1f}" text-anchor="middle" dominant-baseline="central" '
            f'font-size="{fsize}" fill="{col}" font-family="serif">{sym}</text>'
        )
        # Planet name label — always 20px outside the actual symbol position
        label = PLANET_LABELS[p_name]
        nx,ny = polar(r_use + 30, disp_ang)
        parts.append(
            f'<text x="{nx:.1f}" y="{ny:.1f}" text-anchor="middle" dominant-baseline="central" '
            f'font-size="12" fill="{col}" fill-opacity="0.85" font-family="sans-serif">{label}</text>'
        )
        # Tick line
        t1x,t1y = polar(R_TICK_IN,  disp_ang)
        t2x,t2y = polar(R_TICK_OUT, disp_ang)
        parts.append(
            f'<line x1="{t1x:.1f}" y1="{t1y:.1f}" x2="{t2x:.1f}" y2="{t2y:.1f}" '
            f'stroke="{col}" stroke-width="1.2" stroke-opacity="0.6"/>'
        )

    # ASC marker
    ax,ay = polar(R_PLANET, 180)
    parts.append(f'<circle cx="{ax:.1f}" cy="{ay:.1f}" r="14" '
                 f'fill="{C_BG}" stroke="{C_GOLD}" stroke-width="1.5"/>')
    parts.append(
        f'<text x="{ax:.1f}" y="{ay:.1f}" text-anchor="middle" dominant-baseline="central" '
        f'font-size="14" fill="{C_GOLD}" font-weight="bold" font-family="sans-serif">AC</text>'
    )

    # Center dot
    parts.append(f'<circle cx="{cx}" cy="{cy}" r="5" fill="{C_GOLD}" fill-opacity="0.5"/>')
    parts.append(f'<circle cx="{cx}" cy="{cy}" r="2" fill="{C_GOLD}"/>')

    # ── LEGEND ──────────────────────────────────────────────────────────
    legend_top = 910
    parts.append(
        f'<line x1="60" y1="{legend_top}" x2="840" y2="{legend_top}" '
        f'stroke="{C_DIM}" stroke-width="0.6" stroke-opacity="0.5"/>'
    )
    parts.append(
        f'<text x="450" y="{legend_top + 30}" text-anchor="middle" '
        f'font-size="21" fill="{C_GOLD}" font-family="sans-serif" letter-spacing="3">TIERKREIS-LEGENDE</text>'
    )
    legend_y = legend_top + 80  # generous gap between title and symbols
    # 12 zodiac signs in 2 rows of 6
    for i, (sym, name, col) in enumerate(zip(ZODIAC_UNI, ZODIAC_NAMES_DE, ELEM_COLORS)):
        row = i // 6
        col_pos = i % 6
        lx = 75 + col_pos * 130
        ly = legend_y + row * 60
        parts.append(
            f'<text x="{lx}" y="{ly}" text-anchor="middle" '
            f'font-size="30" fill="{col}">{sym}</text>'
        )
        parts.append(
            f'<text x="{lx}" y="{ly + 26}" text-anchor="middle" '
            f'font-size="18" fill="{C_TEXT}" fill-opacity="0.7" font-family="sans-serif">{name}</text>'
        )

    # ── ASPEKTE-LEGENDE ─────────────────────────────────────────────────
    asp_top = legend_y + 2 * 60 + 50  # below zodiac legend
    parts.append(
        f'<line x1="60" y1="{asp_top}" x2="840" y2="{asp_top}" '
        f'stroke="{C_DIM}" stroke-width="0.6" stroke-opacity="0.5"/>'
    )
    parts.append(
        f'<text x="450" y="{asp_top + 30}" text-anchor="middle" '
        f'font-size="21" fill="{C_GOLD}" font-family="sans-serif" letter-spacing="3">ASPEKTE-LEGENDE</text>'
    )
    ASPECT_LEGEND = [
        ('Konjunktion', '0°',   '±8°', 'Verschmelzung',  '#c9a96e'),
        ('Sextil',      '60°',  '±5°', 'Zusammenarbeit', '#4499ee'),
        ('Quadrat',     '90°',  '±7°', 'Herausforderung','#ee4422'),
        ('Trigon',      '120°', '±8°', 'Talent & Fluss', '#44aacc'),
        ('Opposition',  '180°', '±8°', 'Polarität',      '#aa55ff'),
    ]
    col_w = 180
    ay_base = asp_top + 70
    for i, (name, angle, orb, keyword, col) in enumerate(ASPECT_LEGEND):
        ax = 90 + i * col_w
        # Short colored line as visual sample
        parts.append(
            f'<line x1="{ax - 24}" y1="{ay_base}" x2="{ax + 24}" y2="{ay_base}" '
            f'stroke="{col}" stroke-width="2.5" stroke-opacity="0.9"/>'
        )
        # Aspect name
        parts.append(
            f'<text x="{ax}" y="{ay_base + 20}" text-anchor="middle" '
            f'font-size="14" fill="{col}" font-family="sans-serif" font-weight="bold">{name}</text>'
        )
        # Angle + orb
        parts.append(
            f'<text x="{ax}" y="{ay_base + 36}" text-anchor="middle" '
            f'font-size="12" fill="{C_TEXT}" fill-opacity="0.55" font-family="sans-serif">{angle} ({orb})</text>'
        )
        # Keyword
        parts.append(
            f'<text x="{ax}" y="{ay_base + 52}" text-anchor="middle" '
            f'font-size="12" fill="{C_TEXT}" fill-opacity="0.75" font-family="sans-serif">{keyword}</text>'
        )

    parts.append('</svg>')
    return '\n'.join(parts)


def generate_radix_html_wrapper(svg_content: str) -> str:
    """Wraps SVG in interactive HTML with zoom/pan and download button."""
    return f'''<div class="radix-container" style="position:relative;text-align:center;">
  <div style="margin-bottom:12px;display:flex;gap:10px;justify-content:center;flex-wrap:wrap;">
    <button onclick="radixZoom(1.2)" style="background:#1a1030;color:#c9a96e;border:1px solid #3a2060;padding:6px 16px;border-radius:6px;cursor:pointer;font-size:13px;">＋ Zoom</button>
    <button onclick="radixZoom(0.83)" style="background:#1a1030;color:#c9a96e;border:1px solid #3a2060;padding:6px 16px;border-radius:6px;cursor:pointer;font-size:13px;">－ Zoom</button>
    <button onclick="radixReset()" style="background:#1a1030;color:#c9a96e;border:1px solid #3a2060;padding:6px 16px;border-radius:6px;cursor:pointer;font-size:13px;">↺ Reset</button>
    <button onclick="radixDownload()" style="background:#c9a96e;color:#05050f;border:none;padding:6px 16px;border-radius:6px;cursor:pointer;font-size:13px;font-weight:bold;">⬇ SVG herunterladen</button>
  </div>
  <div id="radix-wrap" style="overflow:hidden;display:inline-block;cursor:grab;max-width:100%;">
    <div id="radix-inner" style="transform-origin:center center;transition:transform 0.2s;">
{svg_content}
    </div>
  </div>
</div>
<script>
(function(){{
  var scale = 1, tx = 0, ty = 0;
  var inner = document.getElementById('radix-inner');
  var wrap  = document.getElementById('radix-wrap');
  function applyTransform() {{
    inner.style.transform = 'translate('+tx+'px,'+ty+'px) scale('+scale+')';
  }}
  window.radixZoom = function(f) {{ scale = Math.min(4, Math.max(0.4, scale*f)); applyTransform(); }};
  window.radixReset = function() {{ scale=1; tx=0; ty=0; applyTransform(); }};
  window.radixDownload = function() {{
    var svg = inner.querySelector('svg');
    var blob = new Blob([svg.outerHTML], {{type:'image/svg+xml'}});
    var a = document.createElement('a'); a.href = URL.createObjectURL(blob);
    a.download = 'radix-chart.svg'; a.click();
  }};
  // Touch/mouse pan
  var dragging=false, startX, startY, startTx, startTy;
  wrap.addEventListener('mousedown', function(e){{ dragging=true; startX=e.clientX; startY=e.clientY; startTx=tx; startTy=ty; wrap.style.cursor='grabbing'; }});
  document.addEventListener('mousemove', function(e){{ if(!dragging) return; tx=startTx+(e.clientX-startX); ty=startTy+(e.clientY-startY); applyTransform(); }});
  document.addEventListener('mouseup', function(){{ dragging=false; wrap.style.cursor='grab'; }});
  wrap.addEventListener('wheel', function(e){{ e.preventDefault(); radixZoom(e.deltaY<0?1.1:0.91); }}, {{passive:false}});
}})();
</script>'''
