"""Gera os mapas analíticos da Prancha 01 em SVG (raio de 1.000 m do terreno).

Fontes: OpenStreetMap (vias, hidrografia, vegetação), Microsoft Global ML
Building Footprints (edificações), Overture Maps Places (equipamentos),
SRTM 30 m via OpenTopoData (altitudes).
"""
import json, math, sys, collections

D = sys.argv[1]           # pasta com os dados baixados
OUT = sys.argv[2]         # pasta de saída

LAT0, LON0 = -16.2202211, -47.933783
KX = 111320 * math.cos(math.radians(LAT0)); KY = 110574
VB = 320; C = VB / 2; SC = 0.15          # 1.000 m = 150 unidades
RCLIP = 157

def xy(lon, lat):
    return (C + (lon - LON0) * KX * SC, C - (lat - LAT0) * KY * SC)

def path(pts, close=False):
    s = 'M' + ' L'.join(f'{x:.1f},{y:.1f}' for x, y in pts)
    return s + (' Z' if close else '')

osm = json.load(open(f'{D}/osm.json', encoding='utf-8'))['elements']
ways = [e for e in osm if e['type'] == 'way' and 'geometry' in e]

def roads(cls):
    return [e for e in ways if e.get('tags', {}).get('highway') in cls]

def head(bg='#FFFFFF'):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {VB} {VB}" width="{VB}" height="{VB}">'
            f'<defs><clipPath id="c"><circle cx="{C}" cy="{C}" r="{RCLIP}"/></clipPath></defs>'
            f'<circle cx="{C}" cy="{C}" r="{RCLIP}" fill="{bg}"/><g clip-path="url(#c)">')

def tail(ring=True):
    s = '</g>'
    if ring:
        s += f'<circle cx="{C}" cy="{C}" r="{500*SC}" fill="none" stroke="#1F2A2E" stroke-width="1" stroke-dasharray="4 3" opacity="0.7"/>'
    # terreno
    s += f'<rect x="{C-6}" y="{C-6}" width="12" height="12" fill="#C0392B" stroke="#FFFFFF" stroke-width="2"/>'
    # norte
    s += (f'<g transform="translate({C},18)"><path d="M0,-10 L6,6 L0,2 L-6,6 Z" fill="#1F2A2E"/>'
          f'<text x="0" y="20" font-family="Barlow, Arial, sans-serif" font-size="13" font-weight="700" text-anchor="middle" fill="#1F2A2E">N</text></g>')
    # escala gráfica 500 m
    x0 = C - 250*SC; y0 = VB - 34
    s += (f'<rect x="{x0-4}" y="{y0-14}" width="{500*SC+8}" height="26" fill="#FFFFFF" opacity="0.85"/>'
          f'<rect x="{x0}" y="{y0}" width="{250*SC}" height="5" fill="#1F2A2E"/>'
          f'<rect x="{x0+250*SC}" y="{y0}" width="{250*SC}" height="5" fill="#FFFFFF" stroke="#1F2A2E" stroke-width="1"/>'
          f'<text x="{x0}" y="{y0-3}" font-family="Barlow, Arial, sans-serif" font-size="10" fill="#1F2A2E">0</text>'
          f'<text x="{x0+500*SC}" y="{y0-3}" font-family="Barlow, Arial, sans-serif" font-size="10" text-anchor="end" fill="#1F2A2E">500 m</text>')
    s += f'<circle cx="{C}" cy="{C}" r="{RCLIP}" fill="none" stroke="#1F2A2E" stroke-width="2.5"/></svg>'
    return s

def road_layer(color='#C9D1D3', w=1.6, cls=None):
    cls = cls or ('primary', 'primary_link', 'secondary', 'tertiary', 'residential', 'unclassified', 'service', 'track')
    return ''.join(f'<path d="{path([xy(g["lon"], g["lat"]) for g in e["geometry"]])}" fill="none" stroke="{color}" stroke-width="{w}" stroke-linecap="round"/>'
                   for e in roads(cls))

def water_layer(w=2.2):
    return ''.join(f'<path d="{path([xy(g["lon"], g["lat"]) for g in e["geometry"]])}" fill="none" stroke="#3B82B8" stroke-width="{w}" stroke-linecap="round"/>'
                   for e in ways if 'waterway' in e.get('tags', {}))

def green_layer():
    out = ''
    for e in ways:
        t = e.get('tags', {})
        if t.get('natural') in ('wood', 'scrub') or t.get('leisure') == 'park':
            pts = [xy(g['lon'], g['lat']) for g in e['geometry']]
            out += f'<path d="{path(pts, True)}" fill="#7DB37F" fill-opacity="0.55" stroke="#4E8F5A" stroke-width="0.8"/>'
    return out

bld = json.load(open(f'{D}/buildings.json'))
def bld_layer(fill):
    out = []
    for g in bld:
        for ring in ([g['geometry']['coordinates'][0]] if g['geometry']['type'] == 'Polygon'
                     else [p[0] for p in g['geometry']['coordinates']]):
            out.append(f'<path d="{path([xy(*c) for c in ring], True)}"/>')
    return f'<g fill="{fill}">' + ''.join(out) + '</g>'

# 1. Hierarquia viária
s = head('#F7F5F0')
s += water_layer(1.6)
for cls, col, w, dash in [
        (('track',), '#9AA8AC', 1.4, '3 2.5'),
        (('residential', 'unclassified', 'service'), '#8A979B', 1.6, None),
        (('tertiary',), '#2C6E9E', 3.2, None),
        (('primary', 'primary_link'), '#D9822B', 5.5, None)]:
    for e in roads(cls):
        t = e.get('tags', {})
        d = '3 2.5' if (dash or t.get('surface') in ('dirt', 'unpaved', 'ground', 'gravel')) and cls[0] != 'primary' else None
        s += (f'<path d="{path([xy(g["lon"], g["lat"]) for g in e["geometry"]])}" fill="none" stroke="{col}" '
              f'stroke-width="{w}" stroke-linecap="round"' + (f' stroke-dasharray="{d}"' if d else '') + '/>')
open(f'{OUT}/mapa-hierarquia-viaria.svg', 'w', encoding='utf-8').write(s + tail())

# 2. Cheios e vazios
s = head('#FFFFFF') + bld_layer('#1F2A2E')
open(f'{OUT}/mapa-cheios-vazios.svg', 'w', encoding='utf-8').write(s + tail())

# 3. Equipamentos e áreas verdes
places = json.load(open(f'{D}/places.json', encoding='cp1252'))
coord_count = collections.Counter((round(p[5], 5), round(p[6], 5)) for p in places)
CAT = {
    'educacao': ('#2C6E9E', {'place_of_learning', 'elementary_school'}),
    'institucional': ('#7A2F72', {'courthouse', 'government_office'}),
    'saude': ('#2F8F5B', {'pharmacy_and_drug_store', 'diagnostics_imaging_or_lab_service'}),
    'religioso': ('#8A6D3B', {'christian_place_of_worship', 'religious_organization'}),
    'esporte': ('#C9A227', {'sport_or_fitness_facility', 'sports_and_recreation', 'park'}),
}
def cat_of(c):
    for k, (_, cs) in CAT.items():
        if c in cs:
            return k
    return 'comercio'
COLORS = {k: v[0] for k, v in CAT.items()}; COLORS['comercio'] = '#D9822B'
kept = []
for p in places:
    name, cat, _, conf, status, lon, lat = p
    if (conf or 0) < 0.5 or coord_count[(round(lon, 5), round(lat, 5))] >= 3:
        continue
    if status and status != 'open':
        continue
    dist = math.hypot((lon - LON0) * KX, (lat - LAT0) * KY)
    if dist > 1050:
        continue
    kept.append((cat_of(cat), name, round(dist), lon, lat))
s = head('#F7F5F0') + bld_layer('#C4C4BC') + road_layer('#B9C2C5', 1.4) + green_layer() + water_layer()
for k, _, _, lon, lat in sorted(kept, key=lambda r: r[0] == 'comercio', reverse=True):
    x, y = xy(lon, lat)
    s += f'<circle cx="{x:.1f}" cy="{y:.1f}" r="5.5" fill="{COLORS[k]}" stroke="#FFFFFF" stroke-width="1.6"/>'
open(f'{OUT}/mapa-equipamentos.svg', 'w', encoding='utf-8').write(s + tail())
json.dump(sorted(kept, key=lambda r: r[2]), open(f'{OUT}/equipamentos.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=1)

# 4. Hipsometria
E = json.load(open(f'{D}/elev.json'))
N, R, el = E['N'], E['R'], E['el']
grid = [el[j*N:(j+1)*N] for j in range(N)]       # j: sul->norte, i: oeste->leste
UP = 4; M = (N - 1) * UP + 1; step = 2 * R / (N - 1) / UP
def bil(fi, fj):
    i0, j0 = min(int(fi), N - 2), min(int(fj), N - 2); a, b = fi - i0, fj - j0
    return (grid[j0][i0]*(1-a)*(1-b) + grid[j0][i0+1]*a*(1-b) + grid[j0+1][i0]*(1-a)*b + grid[j0+1][i0+1]*a*b)
CLASSES = [(975, '#2F6B4F'), (985, '#6FA65F'), (995, '#C2D98C'), (1005, '#F0E3A0'), (1010, '#E2A660'), (9999, '#A9572F')]
def color(v):
    for lim, c in CLASSES:
        if v < lim:
            return c
s = head('#FFFFFF')
cell = step * SC + 0.25
for j in range(M):
    for i in range(M):
        v = bil(i / UP, j / UP)
        x = C + (-R + i * step) * SC - cell / 2; y = C - (-R + j * step) * SC - cell / 2
        if math.hypot(x - C, y - C) > RCLIP + 6:
            continue
        s += f'<rect x="{x:.1f}" y="{y:.1f}" width="{cell:.2f}" height="{cell:.2f}" fill="{color(v)}"/>'
s += road_layer('#FFFFFF', 0.9) + water_layer(2.4)
open(f'{OUT}/mapa-hipsometria.svg', 'w', encoding='utf-8').write(s + tail())

c = grid[N//2][N//2]
print('altitude no terreno', c, 'min', min(el), 'max', max(el))
for r in sorted(kept, key=lambda r: r[2]):
    print(r[0], r[2], r[1])
