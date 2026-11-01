"""Gera o diagrama de insolação (carta solar) do terreno, com os solstícios e o equinócio.

Projeção polar da abóbada celeste: centro = zênite, borda = horizonte.
Horas em tempo solar verdadeiro. O lote é desenhado sem escala, orientado
pela Av. Dr. Neilo Rolim (OpenStreetMap).
"""
import json, math, sys

D, OUT = sys.argv[1], sys.argv[2]
LAT0, LON0 = -16.2202211, -47.933783
PHI = math.radians(LAT0)
KX = 111320 * math.cos(PHI); KY = 110574
VB = 320; C = VB / 2; R = 140
FONT = 'Barlow, Arial, sans-serif'

def sun(decl_deg, hour):
    d = math.radians(decl_deg); h = math.radians(15 * (hour - 12))
    e = -math.cos(d) * math.sin(h)
    n = math.cos(PHI) * math.sin(d) - math.sin(PHI) * math.cos(d) * math.cos(h)
    up = math.sin(PHI) * math.sin(d) + math.cos(PHI) * math.cos(d) * math.cos(h)
    alt = math.degrees(math.asin(up)); az = math.atan2(e, n)
    return alt, az

def xy(alt, az):
    r = (90 - alt) / 90 * R
    return (C + r * math.sin(az), C - r * math.cos(az))

DAYS = [(-23.44, '#E07B24', 'verao'), (23.44, '#2C6E9E', 'inverno'), (0.0, '#8A979B', 'equinocio')]

# direção da avenida junto ao lote
osm = json.load(open(f'{D}/osm.json', encoding='utf-8'))['elements']
best = None
for e in osm:
    if e['type'] == 'way' and e.get('tags', {}).get('highway') == 'primary':
        pts = [((g['lon'] - LON0) * KX, (g['lat'] - LAT0) * KY) for g in e['geometry']]
        for a, b in zip(pts, pts[1:]):
            mx, my = (a[0] + b[0]) / 2, (a[1] + b[1]) / 2
            dd = math.hypot(mx, my)
            if best is None or dd < best[0]:
                best = (dd, a, b)
_, a, b = best
bearing = math.atan2(b[0] - a[0], b[1] - a[1])
if math.cos(bearing) < 0:
    bearing += math.pi                      # sentido norte
print('rumo da avenida', round(math.degrees(bearing) % 360, 1))

s = f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {VB} {VB}" width="{VB}" height="{VB}">'
s += f'<circle cx="{C}" cy="{C}" r="{R + 15}" fill="#FFFFFF"/>'
s += f'<circle cx="{C}" cy="{C}" r="{R}" fill="#FBF6EC" stroke="#1F2A2E" stroke-width="2"/>'
for alt in (30, 60):
    s += f'<circle cx="{C}" cy="{C}" r="{(90 - alt) / 90 * R:.1f}" fill="none" stroke="#C9D3D6" stroke-width="0.8"/>'
s += f'<line x1="{C - R}" y1="{C}" x2="{C + R}" y2="{C}" stroke="#C9D3D6" stroke-width="0.8"/><line x1="{C}" y1="{C - R}" x2="{C}" y2="{C + R}" stroke="#C9D3D6" stroke-width="0.8"/>'

# lote (sem escala): frente de 60 m na avenida, fundos de 69,5 m na Rua 4
lot = [(0, 0), (60, 0), (60, 69.5), (0, 60)]
cx, cy = 30, 33; k = 0.62
def rot(p):
    x, y = p[0] - cx, p[1] - cy            # x: perpendicular à avenida (para leste), y: ao longo dela
    ex = x * math.cos(bearing) + y * math.sin(bearing)
    ny = -x * math.sin(bearing) + y * math.cos(bearing)
    return (C + ex * k, C - ny * k)
s += '<path d="M' + ' L'.join(f'{x:.1f},{y:.1f}' for x, y in map(rot, lot)) + ' Z" fill="#F2B8A8" stroke="#C0392B" stroke-width="1.6"/>'

# trajetórias e horas
labels = []
for decl, col, key in DAYS:
    pts = []
    t = 5.0
    while t <= 19.0:
        alt, az = sun(decl, t)
        if alt >= 0:
            pts.append(xy(alt, az))
        t += 0.1
    dash = ' stroke-dasharray="5 4"' if key == 'equinocio' else ''
    s += '<path d="M' + ' L'.join(f'{x:.1f},{y:.1f}' for x, y in pts) + f'" fill="none" stroke="{col}" stroke-width="3"{dash} stroke-linecap="round"/>'
    for hr in (9, 12, 15):
        alt, az = sun(decl, hr)
        x, y = xy(alt, az)
        s += f'<circle cx="{x:.1f}" cy="{y:.1f}" r="4.5" fill="{col}" stroke="#FFFFFF" stroke-width="1.5"/>'
        labels.append((key, hr, round(alt, 1), round(math.degrees(az) % 360, 1)))
# rótulos de hora no inverno (trajetória mais aberta)
for hr in (9, 12, 15):
    alt, az = sun(23.44, hr)
    x, y = xy(alt, az)
    s += f'<text x="{x:.1f}" y="{y - 8:.1f}" font-family="{FONT}" font-size="11" font-weight="700" text-anchor="middle" fill="#2C6E9E">{hr}h</text>'

for t, ang in (('N', 0), ('L', 90), ('S', 180), ('O', 270)):
    a = math.radians(ang)
    x, y = C + (R + 9) * math.sin(a), C - (R + 9) * math.cos(a) + 4.5
    s += f'<text x="{x:.1f}" y="{y:.1f}" font-family="{FONT}" font-size="13" font-weight="700" text-anchor="middle" fill="#1F2A2E">{t}</text>'
s += '</svg>'
open(f'{OUT}/mapa-insolacao.svg', 'w', encoding='utf-8').write(s)
for l in labels:
    print(l)
for decl, _, key in DAYS:
    alt, _ = sun(decl, 12)
    print(key, 'sombra ao meio-dia de 3 m:', round(3 / math.tan(math.radians(alt)), 2), 'm')
