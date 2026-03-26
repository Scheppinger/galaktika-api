"""
Schneller Vorschau-Test für den Radix-Chart.
Ausführen: docker exec galaktika-api python3 /app/test_chart.py
Ergebnis:  https://galaktika-horoskop.de/gen/chart-test.html
"""
from chart_svg import generate_radix_svg, generate_radix_html_wrapper

# Testdaten (Scheppinger-ähnlich, alle Planeten verteilt)
planets = {
    'sun':     310.5,
    'moon':     45.2,
    'mercury': 295.8,
    'venus':   330.1,
    'mars':    120.4,
    'jupiter':  85.7,
    'saturn':  210.3,
    'uranus':  250.9,
    'neptune': 268.2,
    'pluto':   265.5,
    'lilith':  155.8,
    'knoten':   30.6,
}
ascendant = 175.0

svg = generate_radix_svg(planets, ascendant)
html_widget = generate_radix_html_wrapper(svg)

html = f"""<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <title>Radix Chart – Test</title>
  <style>
    body {{ background: #0a0818; display: flex; justify-content: center; padding: 20px; margin: 0; }}
  </style>
</head>
<body>
{html_widget}
</body>
</html>"""

out = '/horoskope-web/gen/chart-test.html'
with open(out, 'w', encoding='utf-8') as f:
    f.write(html)

print(f'Gespeichert: {out}')
print('Vorschau: https://galaktika-horoskop.de/gen/chart-test.html')
