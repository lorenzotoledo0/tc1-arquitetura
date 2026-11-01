"""Diagramas do partido e volumetria do conjunto, redesenhados da planta de locação (Layout2, esc. 1:200).

Coordenadas em metros no referencial da planta: x para a Rua 4, y para a Av. José Rodrigues dos Reis.
Medidas aproximadas, lidas das cotas da planta.
"""
import math, sys

OUT = sys.argv[1]
FONT = 'Barlow, Arial, sans-serif'
BEARING = 29.1          # rumo da Av. Sarah Kubitschek (OSM): o "para cima" da planta aponta para 29° NE

LOT = [(0, 0), (60, 0), (60, 69.52), (54.4, 75.2), (16.5, 87.3), (16.5, 60), (0, 60)]
A01 = [(0, 60), (16.5, 60), (16.5, 87.3), (0, 87.3)]
def ytop(x):
    return 87.3 - (x - 16.5) * 12.1 / 37.9 if x <= 54.4 else 75.2 - (x - 54.4) * 5.68 / 5.6

TCOL = {'01': '#7FA6C2', '02': '#E8B16B', '03': '#B98AB4', '04': '#8DB88F', '05': '#D9946A', '06': '#C9A27E'}

lots = []   # (n, tipo, polígono, casa, permeável, acesso)
for i in range(12):
    y0, y1 = i * 5, i * 5 + 5
    n = 20 + i; t = '02' if i < 6 else '03'
    hx = 8.0 if t == '02' else 6.5
    lots.append((n, t, [(0, y0), (30, y0), (30, y1), (0, y1)], (hx, y0, 23.8, y1), (2.6, y0, hx - 0.6, y1), 'O'))
    n = 19 - i
    lots.append((n, '01', [(30, y0), (60, y0), (60, y1), (30, y1)], (31.5, y0, 50.6, y1), (50.66, y0, 60, y1), 'L'))
xs = [16.5, 21.73, 26.96, 32.5, 38.46, 45.15, 52.45, 60]
top_t = ['01', '01', '01', '01', '04', '05', '06']
for k in range(7):
    a, b = xs[k], xs[k + 1]
    poly = [(a, 60), (b, 60), (b, ytop(b))] + ([(54.4, 75.2)] if a < 54.4 < b else []) + [(a, ytop(a))]
    top = min(ytop(a), ytop(b))
    hy = min(max(top - 5.5, 68.5), top - 0.6)      # casa com no mínimo cerca de 8 m de fundo
    pm = (a + 0.4, hy + 0.4, b - 0.4, top - 0.4) if top - hy > 1.6 else (a + 0.4, hy - 2.4, a + 1.6, hy - 0.4)
    lots.append((k + 1, top_t[k], poly, (a + 0.5, 60.8, b - 0.5, hy), pm, 'N'))

class Frame:
    def __init__(self, W, H, s, ox, oy):
        self.W, self.H, self.s, self.ox, self.oy = W, H, s, ox, oy
    def p(self, x, y):
        return (self.ox + x * self.s, self.oy - y * self.s)
def d(F, pts):
    return 'M' + ' L'.join(f'{x:.1f},{y:.1f}' for x, y in (F.p(*q) for q in pts)) + ' Z'
def rect(F, r):
    x0, y0, x1, y1 = r
    return d(F, [(x0, y0), (x1, y0), (x1, y1), (x0, y1)])

def north(x, y, sz=1.0):
    return (f'<g transform="translate({x},{y}) rotate({-BEARING}) scale({sz})"><path d="M0,-11 L6,6 L0,2 L-6,6 Z" fill="#1F2A2E"/></g>'
            f'<text x="{x}" y="{y + 20 * sz:.1f}" font-family="{FONT}" font-size="{11 * sz:.1f}" font-weight="700" text-anchor="middle" fill="#1F2A2E">N</text>')

def base(F, fill='#FFFFFF', streets=True):
    s = f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {F.W} {F.H}" width="{F.W}" height="{F.H}"><rect width="{F.W}" height="{F.H}" fill="#FFFFFF"/>'
    if streets:
        s += f'<path d="{d(F, [(-9, -4), (-2, -4), (-2, 89), (-9, 89)])}" fill="#D4DADC"/>'
        s += f'<path d="{d(F, [(62, -4), (69, -4), (69, 70), (62, 75)])}" fill="#D4DADC"/>'
        s += f'<path d="{d(F, [(14.5, 89.5), (56, 77), (62, 71), (66, 74), (58, 82), (14.5, 96)])}" fill="#D4DADC"/>'
    s += f'<path d="{d(F, A01)}" fill="#F3F5F5" stroke="#B9C2C5" stroke-width="0.8" stroke-dasharray="3 2"/>'
    s += f'<path d="{d(F, LOT)}" fill="{fill}" stroke="#1F2A2E" stroke-width="1.6"/>'
    return s

W = H = 240
F = Frame(W, H, 2.35, 50, 222)

def save(name, s):
    open(f'{OUT}/{name}.svg', 'w', encoding='utf-8').write(s + '</svg>')

def label(F, x, y, t, size=10, color='#1F2A2E', anchor='middle', rot=0):
    X, Y = F.p(x, y)
    tr = f' transform="rotate({rot} {X:.1f} {Y:.1f})"' if rot else ''
    return f'<text x="{X:.1f}" y="{Y:.1f}" font-family="{FONT}" font-size="{size}" font-weight="700" fill="{color}" text-anchor="{anchor}"{tr}>{t}</text>'

# 1. lote e topografia: curvas paralelas à avenida, caimento de cerca de 4 m para a Rua 4
s = base(F, '#F7F1E3')
for k, x in enumerate((8, 20, 32, 44, 56)):
    s += f'<path d="M{F.p(x, 0)[0]:.1f},{F.p(x, 0)[1]:.1f} L{F.p(x + 1.5, ytop(x) if x > 16.5 else 87.3)[0]:.1f},{F.p(x + 1.5, ytop(x) if x > 16.5 else 87.3)[1]:.1f}" stroke="#C9A27E" stroke-width="1.3" stroke-dasharray="5 3"/>'
ax0, ay0 = F.p(10, 30); ax1, ay1 = F.p(54, 30)
s += (f'<defs><marker id="ar" markerWidth="8" markerHeight="8" refX="6" refY="4" orient="auto"><path d="M0,0 L8,4 L0,8 Z" fill="#8A3F1F"/></marker></defs>'
      f'<line x1="{ax0:.1f}" y1="{ay0:.1f}" x2="{ax1:.1f}" y2="{ay1:.1f}" stroke="#8A3F1F" stroke-width="3" marker-end="url(#ar)"/>')
s += label(F, 32, 34, 'cai cerca de 4 m', 11, '#8A3F1F')
s += label(F, 30, 6, '4.496,61 m²', 11)
s += north(W - 18, 22)
save('partido-topografia', s)

# 2. acessos
s = base(F)
s += ''.join(f'<path d="{rect(F, l[3])}" fill="#E4E8E9"/>' for l in lots)
def arrow(x0, y0, x1, y1, col):
    X0, Y0 = F.p(x0, y0); X1, Y1 = F.p(x1, y1)
    return f'<line x1="{X0:.1f}" y1="{Y0:.1f}" x2="{X1:.1f}" y2="{Y1:.1f}" stroke="{col}" stroke-width="2.4" marker-end="url(#a{col[1:]})"/>'
cols = {'O': '#C0392B', 'L': '#2C6E9E', 'N': '#2F8F5B'}
s += '<defs>' + ''.join(f'<marker id="a{c[1:]}" markerWidth="7" markerHeight="7" refX="5" refY="3.5" orient="auto"><path d="M0,0 L7,3.5 L0,7 Z" fill="{c}"/></marker>' for c in cols.values()) + '</defs>'
for i in range(12):
    yc = i * 5 + 2.5
    s += arrow(-6, yc, 1.5, yc, cols['O']) + arrow(66, yc, 58.5, yc, cols['L'])
for k in range(7):
    xc = (xs[k] + xs[k + 1]) / 2
    s += arrow(xc + 1.2, ytop(xc) + 5.5, xc, ytop(xc) - 1.5, cols['N'])
s += north(W - 18, 22)
save('partido-acessos', s)

# 3. divisão em lotes
s = base(F)
for n, t, poly, *_ in lots:
    s += f'<path d="{d(F, poly)}" fill="#FFFFFF" stroke="#4A585C" stroke-width="0.8"/>'
    cx = sum(p[0] for p in poly) / len(poly); cy = sum(p[1] for p in poly) / len(poly)
    X, Y = F.p(cx, cy)
    s += f'<text x="{X:.1f}" y="{Y + 3:.1f}" font-family="{FONT}" font-size="7.5" font-weight="700" text-anchor="middle" fill="#1F2A2E">{n:02d}</text>'
s += f'<path d="{d(F, LOT)}" fill="none" stroke="#1F2A2E" stroke-width="1.6"/>' + north(W - 18, 22)
save('partido-lotes', s)

# 4. tipologias
s = base(F)
for n, t, poly, casa, *_ in lots:
    s += f'<path d="{d(F, poly)}" fill="#FFFFFF" stroke="#C9D3D6" stroke-width="0.6"/>'
    s += f'<path d="{rect(F, casa)}" fill="{TCOL[t]}" stroke="#FFFFFF" stroke-width="0.6"/>'
s += f'<path d="{d(F, LOT)}" fill="none" stroke="#1F2A2E" stroke-width="1.6"/>' + north(W - 18, 22)
save('partido-tipologias', s)

# 5. níveis e muros de arrimo
s = base(F)
for n, t, poly, *_ in lots:
    s += f'<path d="{d(F, poly)}" fill="#F7F5F0" stroke="#C9D3D6" stroke-width="0.6"/>'
arr = [[(16.5, 60), (60, 60)], [(30, 0), (30, 60)], [(0, 0), (60, 0)]] + [[(x, 60), (x, ytop(x))] for x in xs[1:-1]]
for a, b in arr:
    A, B = F.p(*a), F.p(*b)
    s += f'<line x1="{A[0]:.1f}" y1="{A[1]:.1f}" x2="{B[0]:.1f}" y2="{B[1]:.1f}" stroke="#8A3F1F" stroke-width="2.6"/>'
for k, lv in enumerate(['+0,28', '+0,30', '+0,28', '+0,20', '+0,22', '+0,05', '+0,05']):
    xc = (xs[k] + xs[k + 1]) / 2
    s += label(F, xc, 63, lv, 7, '#8A3F1F', rot=-90 if True else 0)
s += label(F, 15, 30, '+0,05', 10, '#8A3F1F') + label(F, 45, 30, '+0,05', 10, '#8A3F1F')
s += f'<path d="{d(F, LOT)}" fill="none" stroke="#1F2A2E" stroke-width="1.6"/>' + north(W - 18, 22)
save('partido-arrimos', s)

# 6. verde e permeável
s = base(F)
for n, t, poly, casa, perm, _ in lots:
    s += f'<path d="{d(F, poly)}" fill="#FFFFFF" stroke="#C9D3D6" stroke-width="0.6"/>'
    s += f'<path d="{rect(F, casa)}" fill="#D9D4CC"/>'
    s += f'<path d="{rect(F, perm)}" fill="#4E8F5A"/>'
s += f'<path d="{d(F, LOT)}" fill="none" stroke="#1F2A2E" stroke-width="1.6"/>'
s += label(F, 30, -2.5, '909,59 m² permeáveis · 20,22%', 10.5, '#2F5A33') + north(W - 18, 22)
save('partido-permeavel', s)

# volumetria isométrica
VW, VH = 620, 400
c30, s30 = math.cos(math.radians(30)), math.sin(math.radians(30))
SC = 5.0
BOUNDS = []
def iso(x, y, z):
    P = ((x - y) * c30 * SC, -(x + y) * s30 * SC - z * SC)
    BOUNDS.append(P)
    return P
def poly(pts, fill, stroke='#4A585C', w=0.6):
    return '<path d="M' + ' L'.join(f'{a:.1f},{b:.1f}' for a, b in (iso(*p) for p in pts)) + f' Z" fill="{fill}" stroke="{stroke}" stroke-width="{w}" stroke-linejoin="round"/>'
def shade(hexc, k):
    r, g, b = (int(hexc[i:i + 2], 16) for i in (1, 3, 5))
    return '#%02X%02X%02X' % tuple(int(v * k) for v in (r, g, b))
s = ''
s += poly([(-9, -6, 0), (70, -6, 0), (70, 76, 0), (58, 88, 0), (14, 100, 0), (-9, 100, 0)], '#D4DADC', 'none')
s += poly([(p[0], p[1], 0) for p in LOT], '#EEF5EC', '#1F2A2E', 1.2)
s += poly([(p[0], p[1], 0) for p in A01], '#F3F5F5', '#B9C2C5', 0.8)
for n, t, pl, casa, perm, _ in lots:
    s += poly([(p[0], p[1], 0) for p in pl], '#F7F5F0', '#C9D3D6', 0.5)
    x0, y0, x1, y1 = perm
    s += poly([(x0, y0, 0), (x1, y0, 0), (x1, y1, 0), (x0, y1, 0)], '#8DB88F', 'none')
boxes = sorted(lots, key=lambda l: -(l[3][0] + l[3][1]))
H3 = 3.2
for n, t, pl, casa, perm, _ in boxes:
    x0, y0, x1, y1 = casa
    col = TCOL[t]
    s += poly([(x0, y0, 0), (x1, y0, 0), (x1, y0, H3), (x0, y0, H3)], shade(col, 0.82))        # face sul (frente)
    s += poly([(x0, y0, 0), (x0, y1, 0), (x0, y1, H3), (x0, y0, H3)], shade(col, 0.68))        # face oeste
    s += poly([(x0, y0, H3), (x1, y0, H3), (x1, y1, H3 + 0.4), (x0, y1, H3 + 0.4)], '#F4F1EA')  # cobertura, i = 5%
txt = lambda x, y, t, sz=13: (lambda P: f'<text x="{P[0]:.1f}" y="{P[1]:.1f}" font-family="{FONT}" font-size="{sz}" font-weight="700" fill="#4A585C" text-anchor="middle">{t}</text>')(iso(x, y, 0))
s += txt(-5, 30, 'Av. Sarah Kubitschek') + txt(66, 30, 'Rua 4') + txt(40, 94, 'Av. José Rodrigues dos Reis')
x0 = min(p[0] for p in BOUNDS) - 70; x1 = max(p[0] for p in BOUNDS) + 70
y0 = min(p[1] for p in BOUNDS) - 12; y1 = max(p[1] for p in BOUNDS) + 12
s = (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{x0:.0f} {y0:.0f} {x1 - x0:.0f} {y1 - y0:.0f}" width="{x1 - x0:.0f}" height="{y1 - y0:.0f}">'
     f'<rect x="{x0:.0f}" y="{y0:.0f}" width="{x1 - x0:.0f}" height="{y1 - y0:.0f}" fill="#FFFFFF"/>' + s + '</svg>')
print('volumetria', round(x1 - x0), 'x', round(y1 - y0))
open(f'{OUT}/volumetria.svg', 'w', encoding='utf-8').write(s)
print('ok', len(lots), 'lotes')
