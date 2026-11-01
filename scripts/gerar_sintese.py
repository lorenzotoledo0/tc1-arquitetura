"""Gera uso do solo (estimado), cheios e vazios (base ampliada), diagnóstico e diretrizes.

Fontes: Overture Maps (edificações Microsoft + Google; lugares), OpenStreetMap (vias,
córregos, vegetação). Raio de 1.000 m do terreno, mesma escala dos outros mapas.
"""
import json, math, sys, collections

D, OUT = sys.argv[1], sys.argv[2]
LAT0, LON0 = -16.2202211, -47.933783
KX = 111320 * math.cos(math.radians(LAT0)); KY = 110574
VB = 320; C = VB / 2; SC = 0.15; RCLIP = 157
FONT = 'Barlow, Arial, sans-serif'

def m(lon, lat):                       # metros a partir do terreno
    return ((lon - LON0) * KX, (lat - LAT0) * KY)
def u(x, y):                           # metros -> unidades do svg
    return (C + x * SC, C - y * SC)
def path(pts, close=False):
    return 'M' + ' L'.join(f'{x:.1f},{y:.1f}' for x, y in pts) + (' Z' if close else '')

osm = json.load(open(f'{D}/osm.json', encoding='utf-8'))['elements']
ways = [e for e in osm if e['type'] == 'way' and 'geometry' in e]
def wm(e):
    return [m(g['lon'], g['lat']) for g in e['geometry']]
roads = [e for e in ways if 'highway' in e.get('tags', {})]
primary = [wm(e) for e in roads if e['tags']['highway'] in ('primary', 'primary_link')]
unpaved = [wm(e) for e in roads if e['tags']['highway'] == 'track' or e['tags'].get('surface') in ('dirt', 'unpaved', 'ground', 'gravel')]
streams = [wm(e) for e in ways if 'waterway' in e.get('tags', {})]
greens = [wm(e) for e in ways if e.get('tags', {}).get('natural') in ('wood', 'scrub')]
road_segs = [(a, b) for e in roads for a, b in zip(wm(e), wm(e)[1:])]

def seg_dist(p, a, b):
    ax, ay = a; bx, by = b; px, py = p
    dx, dy = bx - ax, by - ay; L = dx*dx + dy*dy
    t = 0 if L == 0 else max(0, min(1, ((px-ax)*dx + (py-ay)*dy) / L))
    return math.hypot(px - ax - t*dx, py - ay - t*dy)

bl = []
for b in json.load(open(f'{D}/buildings_ov.json')):
    g = b['geometry']
    ring = g['coordinates'][0] if g['type'] == 'Polygon' else g['coordinates'][0][0]
    pts = [m(*c) for c in ring]
    a = 0.5 * abs(sum(x1*y2 - x2*y1 for (x1, y1), (x2, y2) in zip(pts, pts[1:] + pts[:1])))
    cx = sum(p[0] for p in pts) / len(pts); cy = sum(p[1] for p in pts) / len(pts)
    if math.hypot(cx, cy) < 1100:
        bl.append({'pts': pts, 'area': a, 'c': (cx, cy)})

def head(bg):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {VB} {VB}" width="{VB}" height="{VB}">'
            f'<defs><clipPath id="c"><circle cx="{C}" cy="{C}" r="{RCLIP}"/></clipPath>'
            f'<pattern id="h" width="5" height="5" patternUnits="userSpaceOnUse" patternTransform="rotate(45)"><rect width="5" height="5" fill="#F4EBD9"/><line x1="0" y1="0" x2="0" y2="5" stroke="#C9B48A" stroke-width="1.6"/></pattern></defs>'
            f'<circle cx="{C}" cy="{C}" r="{RCLIP}" fill="{bg}"/><g clip-path="url(#c)">')
def tail():
    s = '</g>'
    s += f'<circle cx="{C}" cy="{C}" r="{500*SC}" fill="none" stroke="#1F2A2E" stroke-width="1" stroke-dasharray="4 3" opacity="0.7"/>'
    s += f'<rect x="{C-6}" y="{C-6}" width="12" height="12" fill="#C0392B" stroke="#FFFFFF" stroke-width="2"/>'
    s += (f'<g transform="translate({C},18)"><path d="M0,-10 L6,6 L0,2 L-6,6 Z" fill="#1F2A2E"/>'
          f'<text x="0" y="20" font-family="{FONT}" font-size="13" font-weight="700" text-anchor="middle" fill="#1F2A2E">N</text></g>')
    x0 = C - 250*SC; y0 = VB - 34
    s += (f'<rect x="{x0-4}" y="{y0-14}" width="{500*SC+8}" height="26" fill="#FFFFFF" opacity="0.85"/>'
          f'<rect x="{x0}" y="{y0}" width="{250*SC}" height="5" fill="#1F2A2E"/>'
          f'<rect x="{x0+250*SC}" y="{y0}" width="{250*SC}" height="5" fill="#FFFFFF" stroke="#1F2A2E" stroke-width="1"/>'
          f'<text x="{x0}" y="{y0-3}" font-family="{FONT}" font-size="10" fill="#1F2A2E">0</text>'
          f'<text x="{x0+500*SC}" y="{y0-3}" font-family="{FONT}" font-size="10" text-anchor="end" fill="#1F2A2E">500 m</text>')
    return s + f'<circle cx="{C}" cy="{C}" r="{RCLIP}" fill="none" stroke="#1F2A2E" stroke-width="2.5"/></svg>'

def lines(ls, color, w, extra=''):
    return ''.join(f'<path d="{path([u(*p) for p in l])}" fill="none" stroke="{color}" stroke-width="{w}" stroke-linecap="round" stroke-linejoin="round"{extra}/>' for l in ls)
def road_base(color, w):
    return lines([wm(e) for e in roads], color, w)
def polys(items, fill):
    return f'<g fill="{fill}">' + ''.join(f'<path d="{path([u(*p) for p in b["pts"]], True)}"/>' for b in items) + '</g>'
def green_base():
    return ''.join(f'<path d="{path([u(*p) for p in g], True)}" fill="#7DB37F" fill-opacity="0.5" stroke="#4E8F5A" stroke-width="0.8"/>' for g in greens)

# vazios urbanos: células de 40 m sem edificação a 45 m, junto a vias (até 50 m), fora da vegetação
CELL = 40
grid = collections.defaultdict(list)
for b in bl:
    grid[(int(b['c'][0] // 50), int(b['c'][1] // 50))].append(b['c'])
def near_building(p, r=45):
    gx, gy = int(p[0] // 50), int(p[1] // 50)
    return any(math.hypot(p[0]-q[0], p[1]-q[1]) < r for i in (-1, 0, 1) for j in (-1, 0, 1) for q in grid[(gx+i, gy+j)])
rgrid = collections.defaultdict(list)
for a, b in road_segs:
    for q in (a, b, ((a[0]+b[0])/2, (a[1]+b[1])/2)):
        rgrid[(int(q[0] // 100), int(q[1] // 100))].append((a, b))
def near_road(p, r=50):
    gx, gy = int(p[0] // 100), int(p[1] // 100)
    return any(seg_dist(p, a, b) < r for i in (-1, 0, 1) for j in (-1, 0, 1) for a, b in rgrid[(gx+i, gy+j)])
vazios = []
for i in range(-27, 28):
    for j in range(-27, 28):
        p = (i * CELL, j * CELL)
        if math.hypot(*p) > 1080 or near_building(p) or not near_road(p):
            continue
        vazios.append(p)
def vazio_layer(fill):
    h = CELL * SC / 2 + 0.2
    return ''.join(f'<rect x="{u(*p)[0]-h:.1f}" y="{u(*p)[1]-h:.1f}" width="{2*h:.1f}" height="{2*h:.1f}" fill="{fill}"/>' for p in vazios)

# uso do solo: lugares do Overture ligados à edificação mais próxima (até 25 m)
places = json.load(open(f'{D}/places.json', encoding='cp1252'))
cc = collections.Counter((round(p[5], 5), round(p[6], 5)) for p in places)
USO = {
    'institucional': ('#7A2F72', {'courthouse', 'government_office', 'place_of_learning', 'elementary_school'}),
    'religioso': ('#8A6D3B', {'christian_place_of_worship', 'religious_organization'}),
}
def uso_of(cat):
    for k, (_, cs) in USO.items():
        if cat in cs:
            return k
    return 'comercio'
for p in places:
    name, cat, _, conf, status, lon, lat = p
    if (conf or 0) < 0.4 or cc[(round(lon, 5), round(lat, 5))] >= 3:
        continue
    q = m(lon, lat)
    best = min(bl, key=lambda b: math.hypot(b['c'][0]-q[0], b['c'][1]-q[1]))
    if math.hypot(best['c'][0]-q[0], best['c'][1]-q[1]) < 25:
        best['uso'] = uso_of(cat)
COL = {'residencial': '#E8B16B', 'comercio': '#C0392B', 'institucional': '#7A2F72', 'religioso': '#8A6D3B', 'galpao': '#4A585C'}
cnt = collections.Counter()
for b in bl:
    if 'uso' not in b:
        b['uso'] = 'galpao' if b['area'] > 400 else 'residencial'
    if math.hypot(*b['c']) <= 1000:
        cnt[b['uso']] += 1

s = head('#FFFFFF') + vazio_layer('url(#h)') + green_base() + road_base('#D4DADC', 1.3) + lines(streams, '#3B82B8', 2.2)
for k in ('residencial', 'galpao', 'religioso', 'institucional', 'comercio'):
    s += polys([b for b in bl if b['uso'] == k], COL[k])
open(f'{OUT}/mapa-uso-solo.svg', 'w', encoding='utf-8').write(s + tail())

# cheios e vazios com a base ampliada
s = head('#FFFFFF') + polys(bl, '#1F2A2E')
open(f'{OUT}/mapa-cheios-vazios.svg', 'w', encoding='utf-8').write(s + tail())

# pontos de referência
def nearest_on(ls, p=(0, 0)):
    best = None
    for l in ls:
        for a, b in zip(l, l[1:]):
            for t in [k / 20 for k in range(21)]:
                q = (a[0] + t*(b[0]-a[0]), a[1] + t*(b[1]-a[1]))
                d = math.hypot(q[0]-p[0], q[1]-p[1])
                if best is None or d < best[0]:
                    best = (d, q)
    return best[1]
def mid(l):
    return l[len(l) // 2]
art_pt = nearest_on(primary)
far_unpaved = [l for l in unpaved if 300 < math.hypot(*mid(l)) < 850]
long_unpaved = max(far_unpaved, key=lambda l: sum(math.hypot(b[0]-a[0], b[1]-a[1]) for a, b in zip(l, l[1:])))
stream_main = max(streams, key=len)
# maior grupo de vazios até 700 m
vs = set(vazios); seen = set(); groups = []
for p in vazios:
    if p in seen or math.hypot(*p) > 700:
        continue
    st = [p]; g = []; seen.add(p)
    while st:
        q = st.pop(); g.append(q)
        for dx, dy in ((CELL, 0), (-CELL, 0), (0, CELL), (0, -CELL)):
            r = (q[0]+dx, q[1]+dy)
            if r in vs and r not in seen and math.hypot(*r) <= 700:
                seen.add(r); st.append(r)
    groups.append(g)
def center(g):
    c = (sum(p[0] for p in g) / len(g), sum(p[1] for p in g) / len(g))
    return min(g, key=lambda p: math.hypot(p[0]-c[0], p[1]-c[1]))
groups.sort(key=len, reverse=True)
vz_pt = center(groups[0])
vz_pt2 = next(center(g) for g in groups[1:] if math.hypot(center(g)[0]-vz_pt[0], center(g)[1]-vz_pt[1]) > 200)

def dot(p, color, r=5.5):
    x, y = u(*p)
    return f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{r}" fill="{color}" stroke="#FFFFFF" stroke-width="1.6"/>'
def num(p, n, color):
    x, y = u(*p)
    return (f'<circle cx="{x:.1f}" cy="{y:.1f}" r="9" fill="{color}" stroke="#FFFFFF" stroke-width="1.8"/>'
            f'<text x="{x:.1f}" y="{y+4:.1f}" font-family="{FONT}" font-size="11.5" font-weight="700" text-anchor="middle" fill="#FFFFFF">{n}</text>')

eq = json.load(open(f'{OUT}/equipamentos.json', encoding='utf-8'))
escola = next(m(r[3], r[4]) for r in eq if r[0] == 'educacao')
esporte = next(m(r[3], r[4]) for r in eq if r[0] == 'esporte')

# diagnóstico
POT = '#2F8F5B'; FRA = '#C0392B'
s = head('#F7F5F0') + vazio_layer('#CFE6CF') + polys(bl, '#C9CCC6') + road_base('#B9C2C5', 1.2)
s += lines(streams, '#E59A4C', 60 * SC, ' stroke-opacity="0.45"')       # faixa de APP de 30 m de cada lado
s += lines(streams, '#3B82B8', 2.2)
s += lines(primary, POT, 6, ' stroke-opacity="0.85"')
s += lines(unpaved, FRA, 2.2, ' stroke-dasharray="4 3"')
s += dot(escola, POT) + dot(esporte, POT)
open(f'{OUT}/mapa-diagnostico.svg', 'w', encoding='utf-8').write(s + tail())

# diretrizes
DIR = '#2C6E9E'
s = head('#F7F5F0') + polys(bl, '#C9CCC6') + road_base('#B9C2C5', 1.2)
s += lines([stream_main], '#7DB37F', 60 * SC, ' stroke-opacity="0.7"') + lines(streams, '#3B82B8', 2.2)
s += lines(unpaved, '#C9A227', 3, ' stroke-dasharray="4 3"')
s += num((art_pt[0] - 45, art_pt[1] + 35), 1, DIR)
pt2 = mid(long_unpaved)
vz_pt2 = next(center(g) for g in groups[1:] if min(math.hypot(center(g)[0]-q[0], center(g)[1]-q[1]) for q in (vz_pt, pt2, (0, 0))) > 250)
s += num(pt2, 2, DIR)
s += num(mid(stream_main), 3, DIR)
s += num(vz_pt, 4, DIR)
s += num(vz_pt2, 5, DIR)
open(f'{OUT}/mapa-diretrizes.svg', 'w', encoding='utf-8').write(s + tail())

print('edificacoes no raio', sum(1 for b in bl if math.hypot(*b['c']) <= 1000), dict(cnt))
print('celulas vazias', len(vazios), 'area aprox ha', round(len(vazios) * CELL * CELL / 1e4, 1))
print('arterial', [round(v) for v in art_pt], 'vazios', vz_pt, vz_pt2, 'grupos', [len(g) for g in groups[:4]])
