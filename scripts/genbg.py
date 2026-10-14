#!/usr/bin/env python3
"""生成式背景（只用标准库，输出 SVG）：dotline 点线网络 / flow 流场线 / halftone 半调点阵。颜色只取 tokens.json。
用法: genbg.py <dotline|flow|halftone> tokens.json out.svg [--seed 7] [--w 1280 --h 720] [--transparent]"""
import sys, json, math, random, argparse
def vnoise(seed):
    rnd = random.Random(seed); g = {}
    def grad(i, j):
        if (i, j) not in g: a = rnd.random() * 6.2832; g[(i, j)] = (math.cos(a), math.sin(a))
        return g[(i, j)]
    def n(x, y):
        i, j = int(math.floor(x)), int(math.floor(y)); fx, fy = x - i, y - j
        def d(ii, jj): gx, gy = grad(ii, jj); return gx * (x - ii) + gy * (y - jj)
        s = lambda t: t * t * (3 - 2 * t)
        a = d(i, j) + s(fx) * (d(i + 1, j) - d(i, j)); b = d(i, j + 1) + s(fx) * (d(i + 1, j + 1) - d(i, j + 1))
        return a + s(fy) * (b - a)
    return n
def dotline(t, W, H, r, transparent):
    pts = [(r.uniform(-40, W + 40), r.uniform(-40, H + 40)) for _ in range(150)]
    o = []
    for i, (x1, y1) in enumerate(pts):
        for x2, y2 in pts[i + 1:]:
            d = math.hypot(x1 - x2, y1 - y2)
            if d < 140: o.append(f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" stroke="{t["text_muted"]}" stroke-opacity="{0.55*(1-d/140):.2f}" stroke-width="1"/>')
    for k, (x, y) in enumerate(pts):
        acc = k % 11 == 0
        o.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{4 if acc else 2}" fill="{t["accent"] if acc else t["text"]}" fill-opacity="{1 if acc else 0.7}"/>')
    return o
def flow(t, W, H, r, transparent):
    n = vnoise(r.randint(0, 9999)); o = []
    for k in range(260):
        x, y = r.uniform(0, W), r.uniform(0, H); pts = [(x, y)]
        for _ in range(60):
            a = n(x / 260, y / 260) * 6.0; x += math.cos(a) * 6; y += math.sin(a) * 6; pts.append((x, y))
        acc = k % 23 == 0
        d = "M" + " L".join(f"{a:.1f} {b:.1f}" for a, b in pts)
        o.append(f'<path d="{d}" fill="none" stroke="{t["accent"] if acc else t["text_muted"]}" stroke-opacity="{0.9 if acc else 0.35}" stroke-width="{1.6 if acc else 1}"/>')
    return o
def halftone(t, W, H, r, transparent):
    o = []; step = 18; cx, cy = W * 0.78, H * 0.35
    for y in range(0, H + step, step):
        for x in range(0, W + step, step):
            d = math.hypot(x - cx, y - cy) / math.hypot(W, H)
            rad = max(0, 7 * (1 - d * 1.9))
            if rad > 0.4: o.append(f'<circle cx="{x}" cy="{y}" r="{rad:.2f}" fill="{t["accent"] if d < 0.12 else t["text_muted"]}" fill-opacity="{0.9 if d<0.12 else 0.5}"/>')
    return o
if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("kind"); ap.add_argument("tokens"); ap.add_argument("out")
    ap.add_argument("--seed", type=int, default=7); ap.add_argument("--w", type=int, default=1280); ap.add_argument("--h", type=int, default=720); ap.add_argument("--transparent", action="store_true")
    a = ap.parse_args(); t = json.load(open(a.tokens)); r = random.Random(a.seed)
    body = {"dotline": dotline, "flow": flow, "halftone": halftone}[a.kind](t, a.w, a.h, r, a.transparent)
    bg = "" if a.transparent else f'<rect width="{a.w}" height="{a.h}" fill="{t["bg"]}"/>'
    open(a.out, "w").write(f'<svg xmlns="http://www.w3.org/2000/svg" width="{a.w}" height="{a.h}" viewBox="0 0 {a.w} {a.h}">{bg}{"".join(body)}</svg>')
