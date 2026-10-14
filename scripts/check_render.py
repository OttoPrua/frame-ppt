#!/usr/bin/env python3
"""SVG 检查 + 渲染 + 缩略总览。
用法: check_render.py <svg目录|文件...> [--out png] [--sheet contact_sheet.png]
       [--accent "#D90429" --max-accent 0.10] [--safe 48,40]
检查: XML 解析、viewBox=0 0 1280 720、<text> 宽度估算(中文≈字号, ASCII≈0.56×字号)
是否超出画布/安全区/所在卡片(包含文字起点的最小 rect)、强调色像素占比。退出码 1 表示有错误。
"""
import sys, os, re, glob, argparse, subprocess
import xml.etree.ElementTree as ET
NS = "{http://www.w3.org/2000/svg}"

def tw(s, sz): return sum(sz if ord(c) > 255 else sz * 0.56 for c in s)
def f(v, d=0.0):
    try: return float(re.sub(r"[^\d.\-]", "", str(v)) or d)
    except ValueError: return d

def check(path, safe):
    errs, warns = [], []
    try: root = ET.parse(path).getroot()
    except ET.ParseError as e: return [f"XML 解析失败: {e}"], []
    vb = (root.get("viewBox") or "").split()
    if [x for x in vb] != ["0", "0", "1280", "720"]: errs.append(f"viewBox={root.get('viewBox')}")
    rects = []
    in_defs = {id(e) for d in root.iter(NS + "defs") for e in d.iter()}  # defs/pattern/clipPath 里的形状不是卡片
    for r in root.iter(NS + "rect"):
        if id(r) in in_defs: continue
        x, y, w, h = f(r.get("x")), f(r.get("y")), f(r.get("width")), f(r.get("height"))
        # 装饰层（高光、斜面、描边框）不算作卡片：fill=none 或 opacity<1
        if r.get("fill") == "none" or f(r.get("opacity"), 1) < 1: continue
        if 0 < w < 1280 or 0 < h < 720: rects.append((x, y, w, h))
    sx, sy = safe
    for t in root.iter(NS + "text"):
        sz = f(t.get("font-size"), 16); anchor = t.get("text-anchor", "start")
        spans = list(t.iter(NS + "tspan")) or [t]
        x0 = f(t.get("x")); y = f(t.get("y"))
        for sp in spans:
            s = "".join(sp.itertext()) if sp is not t else (t.text or "")
            if not s.strip(): continue
            x = f(sp.get("x"), x0); y += f(sp.get("dy"), 0)
            w = tw(s, sz); left = x - (w if anchor == "end" else w / 2 if anchor == "middle" else 0)
            right = left + w
            if left < 0 or right > 1280 or y > 720 or y - sz < 0: errs.append(f"超出画布: '{s[:20]}'")
            elif left < sx - 1 or right > 1280 - sx + 1 or y > 720 - sy + 4: warns.append(f"进入安全区边距: '{s[:20]}'")
            if sz < 12: warns.append(f"字号 {sz}<12: '{s[:20]}'")
            box = [r for r in rects if r[0] <= x <= r[0] + r[2] and r[1] <= y - sz * 0.5 <= r[1] + r[3]]
            if box:
                bx, by, bw, bh = min(box, key=lambda r: r[2] * r[3])
                if right > bx + bw + 1 or left < bx - 1 or y > by + bh + 2:
                    errs.append(f"超出卡片: '{s[:20]}' (右缘 {right:.0f} > {bx+bw:.0f} 或底 {y:.0f} > {by+bh:.0f})")
    return errs, warns

def accent_ratio(png, hexc, tol=40):
    from PIL import Image
    im = Image.open(png).convert("RGB").resize((320, 180))
    c = tuple(int(hexc.lstrip("#")[i:i+2], 16) for i in (0, 2, 4))
    px = list(im.get_flattened_data()) if hasattr(im, "get_flattened_data") else list(im.getdata())
    return sum(1 for p in px if sum(abs(p[i] - c[i]) for i in range(3)) < tol) / len(px)

def sheet(pngs, out, cols=4):
    from PIL import Image, ImageDraw
    tw_, th = 480, 270; pad = 16; rows = (len(pngs) + cols - 1) // cols
    S = Image.new("RGB", (cols * (tw_ + pad) + pad, rows * (th + pad + 20) + pad), "white")
    d = ImageDraw.Draw(S)
    from PIL import ImageFont
    font = None
    try:
        fp = subprocess.run(["fc-match", "-f", "%{file}", "Noto Sans CJK SC:style=Regular"], capture_output=True, text=True).stdout.strip()
        font = ImageFont.truetype(fp, 14) if fp else None
    except Exception: font = None
    for i, p in enumerate(pngs):
        im = Image.open(p).convert("RGB").resize((tw_, th))
        x = pad + (i % cols) * (tw_ + pad); y = pad + (i // cols) * (th + pad + 20)
        S.paste(im, (x, y)); d.rectangle([x, y, x + tw_ - 1, y + th - 1], outline="#999")
        d.text((x, y + th + 3), os.path.basename(p), fill="black", font=font)
    S.save(out)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("inputs", nargs="+"); ap.add_argument("--out", default="png")
    ap.add_argument("--sheet"); ap.add_argument("--accent"); ap.add_argument("--max-accent", type=float, default=0.10)
    ap.add_argument("--safe", default="48,40")
    a = ap.parse_args(); safe = tuple(float(v) for v in a.safe.split(","))
    files = []
    for i in a.inputs: files += sorted(glob.glob(os.path.join(i, "*.svg"))) if os.path.isdir(i) else [i]
    os.makedirs(a.out, exist_ok=True); bad = False; pngs = []
    for fp in files:
        errs, warns = check(fp, safe)
        png = os.path.join(a.out, os.path.splitext(os.path.basename(fp))[0] + ".png")
        r = subprocess.run(["rsvg-convert", "-w", "1920", "-o", png, fp], capture_output=True, text=True)
        if r.returncode: errs.append("渲染失败: " + r.stderr.strip()[:200])
        else:
            pngs.append(png)
            if a.accent:
                ratio = accent_ratio(png, a.accent)
                (errs if ratio > a.max_accent else warns if ratio > a.max_accent * 0.8 else []).append(f"强调色面积 {ratio:.1%}") if ratio > a.max_accent * 0.8 else None
        status = "FAIL" if errs else ("WARN" if warns else "OK")
        bad |= bool(errs)
        print(f"[{status}] {os.path.basename(fp)}")
        for e in errs: print("   ✗", e)
        for w in warns: print("   !", w)
    if a.sheet and pngs: sheet(pngs, a.sheet); print("缩略总览:", a.sheet)
    print("提醒：脚本只做估算，仍需打开 PNG 逐页目视检查。")
    sys.exit(1 if bad else 0)

if __name__ == "__main__": main()
