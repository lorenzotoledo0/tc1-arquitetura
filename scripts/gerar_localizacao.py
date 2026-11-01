"""Gera os mapas de localização da Prancha 01: Brasil com Goiás e município de Luziânia.

Fonte: IBGE, malhas territoriais (API de malhas v3).
"""
import json, math, sys

D = sys.argv[1]
OUT = sys.argv[2]
LOT = (-47.933783, -16.2202211)
FONT = 'Barlow, Arial, sans-serif'

def load(name):
    return json.load(open(f'{D}/{name}', encoding='utf-8'))['features']

def rings(geom):
    if geom['type'] == 'Polygon':
        return geom['coordinates']
    return [r for p in geom['coordinates'] for r in p]

class Proj:
    def __init__(self, bbox, W, H, pad):
        x0, y0, x1, y1 = bbox
        self.k = math.cos(math.radians((y0 + y1) / 2))
        sx = (W - 2 * pad) / ((x1 - x0) * self.k); sy = (H - 2 * pad) / (y1 - y0)
        self.s = min(sx, sy)
        self.ox = W / 2 - ((x0 + x1) / 2) * self.k * self.s
        self.oy = H / 2 + ((y0 + y1) / 2) * self.s
    def __call__(self, lon, lat):
        return (self.ox + lon * self.k * self.s, self.oy - lat * self.s)

def d_of(geom, p):
    return ' '.join('M' + ' L'.join(f'{x:.1f},{y:.1f}' for x, y in (p(*c) for c in r)) + ' Z' for r in rings(geom))

def bbox_of(feats):
    xs = [c[0] for f in feats for r in rings(f['geometry']) for c in r]
    ys = [c[1] for f in feats for r in rings(f['geometry']) for c in r]
    return min(xs), min(ys), max(xs), max(ys)

def north(x, y):
    return (f'<g transform="translate({x},{y})"><path d="M0,-9 L5.5,5 L0,1.5 L-5.5,5 Z" fill="#1F2A2E"/>'
            f'<text x="0" y="17" font-family="{FONT}" font-size="11" font-weight="700" text-anchor="middle" fill="#1F2A2E">N</text></g>')

def scalebar(p, x, y, km, lat):
    # comprimento em px de `km` quilômetros na latitude dada
    px = km / 111.32 * p.k * p.s
    return (f'<rect x="{x}" y="{y}" width="{px/2:.1f}" height="4" fill="#1F2A2E"/>'
            f'<rect x="{x+px/2:.1f}" y="{y}" width="{px/2:.1f}" height="4" fill="#FFFFFF" stroke="#1F2A2E" stroke-width="0.8"/>'
            f'<text x="{x}" y="{y-3}" font-family="{FONT}" font-size="9" fill="#1F2A2E">0</text>'
            f'<text x="{x+px:.1f}" y="{y-3}" font-family="{FONT}" font-size="9" text-anchor="end" fill="#1F2A2E">{km} km</text>')

# 1. Brasil com Goiás e DF
W, H = 240, 236
uf = load('br_uf.json')
p = Proj(bbox_of(uf), W, H, 8)
s = f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}"><rect width="{W}" height="{H}" fill="#FFFFFF"/>'
for f in uf:
    code = f['properties']['codarea']
    fill = {'52': '#8A3F1F', '53': '#1F2A2E'}.get(code, '#E4E8E9')
    s += f'<path d="{d_of(f["geometry"], p)}" fill="{fill}" stroke="#FFFFFF" stroke-width="0.8" stroke-linejoin="round"/>'
gx, gy = p(-50.2, -16.6)
s += f'<text x="{gx:.1f}" y="{gy:.1f}" font-family="{FONT}" font-size="13" font-weight="700" fill="#FFFFFF" text-anchor="middle">GO</text>'
s += north(W - 16, 18) + scalebar(p, 12, H - 12, 1000, -15) + '</svg>'
open(f'{OUT}/mapa-brasil-goias.svg', 'w', encoding='utf-8').write(s)

# 2. Luziânia: município, vizinhos e DF
go = load('go_mun.json'); df = load('df_max.json'); luz = load('luz.json')
lb = bbox_of(luz)
# estende ao norte para mostrar parte do DF, vizinho de Luziânia
view = (lb[0] - 0.08, lb[1] - 0.05, lb[2] + 0.08, -15.62)
p = Proj(view, W, H, 6)
s = (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}">'
     f'<defs><clipPath id="v"><rect width="{W}" height="{H}"/></clipPath></defs><rect width="{W}" height="{H}" fill="#F3F5F5"/><g clip-path="url(#v)">')
for f in go:
    if f['properties']['codarea'] != '5212501':
        s += f'<path d="{d_of(f["geometry"], p)}" fill="#E4E8E9" stroke="#FFFFFF" stroke-width="1"/>'
for f in df:
    s += f'<path d="{d_of(f["geometry"], p)}" fill="#C9D3D6" stroke="#FFFFFF" stroke-width="1"/>'
for f in luz:
    s += f'<path d="{d_of(f["geometry"], p)}" fill="#8A3F1F" fill-opacity="0.85" stroke="#5C2A14" stroke-width="1.2"/>'
dx, dy = p(-47.95, -15.76)
s += f'<text x="{dx:.1f}" y="{dy:.1f}" font-family="{FONT}" font-size="12" font-weight="700" fill="#1F2A2E" text-anchor="middle">DF</text>'
lx, ly = p(*LOT)
nx, ny = p(-48.08, -16.55)
s += (f'<text x="{nx:.1f}" y="{ny:.1f}" font-family="{FONT}" font-size="11" font-weight="700" fill="#FFFFFF" text-anchor="middle">LUZIÂNIA</text>'
      f'<rect x="{lx-5:.1f}" y="{ly-5:.1f}" width="10" height="10" fill="#C0392B" stroke="#FFFFFF" stroke-width="1.8"/>')
s += '</g>' + north(W - 16, 18)
s += f'<rect x="6" y="{H-30}" width="{40/111.32*p.k*p.s+16:.0f}" height="24" fill="#FFFFFF" opacity="0.85"/>'
s += scalebar(p, 12, H - 12, 40, -16.3) + '</svg>'
open(f'{OUT}/mapa-luziania.svg', 'w', encoding='utf-8').write(s)
print('ok', view)
