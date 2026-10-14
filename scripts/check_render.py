#!/usr/bin/env python3
"""SVG 检查 + 渲染 + 缩略总览。
用法: check_render.py <svg目录|文件...> [--out png] [--sheet contact_sheet.png]
       [--accent "#D90429" --max-accent 0.10] [--safe 48,40]
       [--colors tokens.json] [--page-type content|cover|section|manifesto]
检查: XML 解析、viewBox=0 0 1280 720、<text> 宽度估算(中文≈字号, ASCII≈0.56×字号)
是否超出画布/安全区/所在卡片(包含文字起点的最小 rect)、强调色像素占比。退出码 1 表示有错误。
--colors: 读 tokens.py 生成的 tokens.json，额外检查 token 配对对比度、每个 <text> 与实际渲染背景的对比度、
小字是否直接用了 accent、accent 面积（按页面类型）、调色板外颜色、色相数。页面类型取自 SVG 根元素
data-page="cover|section|manifesto|content"，否则看文件名（cover/section/manifesto），否则用 --page-type。
"""
import sys, os, re, glob, argparse, subprocess
import xml.etree.ElementTree as ET
NS = "{http://www.w3.org/2000/svg}"
ANY_SIZE = False  # --any-size：README 横幅等非 16:9 图，不查 viewBox 和画布边界

def tw(s, sz): return sum(sz if ord(c) > 255 else sz * 0.56 for c in s)
def f(v, d=0.0):
    try: return float(re.sub(r"[^\d.\-]", "", str(v)) or d)
    except ValueError: return d

def check(path, safe):
    errs, warns = [], []
    try: root = ET.parse(path).getroot()
    except ET.ParseError as e: return [f"XML 解析失败: {e}"], []
    vb = (root.get("viewBox") or "").split()
    if [x for x in vb] != ["0", "0", "1280", "720"] and not ANY_SIZE: errs.append(f"viewBox={root.get('viewBox')}")
    rects = []
    in_defs = {id(e) for d in root.iter(NS + "defs") for e in d.iter()}  # defs/pattern/clipPath 里的形状不是卡片
    for r in root.iter(NS + "rect"):
        if id(r) in in_defs: continue
        x, y, w, h = f(r.get("x")), f(r.get("y")), f(r.get("width")), f(r.get("height"))
        # 装饰层（高光、斜面、描边框）不算作卡片：fill=none 或 opacity<1
        if r.get("fill") == "none" or f(r.get("opacity"), 1) < 1: continue
        if 0 < w < 1280 or 0 < h < 720: rects.append((x, y, w, h))
    sx, sy = safe
    bleed = {id(e) for b in root.iter() if b.get("data-bleed") for e in b.iter()}  # 有意出血的满版巨字
    for t in root.iter(NS + "text"):
        if id(t) in bleed: continue
        sz = f(t.get("font-size"), 16); anchor = t.get("text-anchor", "start")
        spans = list(t.iter(NS + "tspan")) or [t]
        x0 = f(t.get("x")); y = f(t.get("y"))
        for sp in spans:
            s = "".join(sp.itertext()) if sp is not t else (t.text or "")
            if not s.strip(): continue
            x = f(sp.get("x"), x0); y = f(sp.get("y"), y) + f(sp.get("dy"), 0)
            w = tw(s, sz); left = x - (w if anchor == "end" else w / 2 if anchor == "middle" else 0)
            right = left + w
            if ANY_SIZE: continue
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


# ---------- 配色检查（--colors） ----------
def _px(im): return list(im.get_flattened_data()) if hasattr(im, "get_flattened_data") else list(im.getdata())
def _rgb(h): h = h.strip().lstrip("#"); h = "".join(c * 2 for c in h) if len(h) == 3 else h; return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))
def _lum(c):
    v = [x / 255 for x in c]; v = [x / 12.92 if x <= 0.04045 else ((x + 0.055) / 1.055) ** 2.4 for x in v]
    return 0.2126 * v[0] + 0.7152 * v[1] + 0.0722 * v[2]
def _cr(a, b): la, lb = _lum(a), _lum(b); return (max(la, lb) + 0.05) / (min(la, lb) + 0.05)
def _dist(a, b): return sum(abs(a[i] - b[i]) for i in range(3))
NAMED = {"white": "#FFFFFF", "black": "#000000"}

def _style(el, key):
    v = el.get(key)
    if v is None and el.get("style"):
        m = re.search(key + r"\s*:\s*([^;]+)", el.get("style")); v = m.group(1).strip() if m else None
    return v

def page_type(path, root, default):
    v = root.get("data-page")
    if v: return v
    n = os.path.basename(path).lower()
    for k in ("cover", "section", "manifesto"):
        if k in n: return k
    return default

def color_check(path, png, tok, ptype):
    """返回 (errs, warns, stats)。只在有把握时报错；渐变/多色风格包大多只给提示。"""
    from PIL import Image
    errs, warns = [], []
    lim = tok["limits"]; strict = lim.get("strict_text", True)
    cb = _rgb(tok[tok.get("content_bg", "bg")]); acc = _rgb(tok["accent"])
    acc2 = _rgb(tok["accent2"]) if tok.get("accent2") else None
    try: root = ET.parse(path).getroot()
    except ET.ParseError: return errs, warns, {}
    im = Image.open(png).convert("RGB")
    try: VW = float((ET.parse(path).getroot().get('viewBox') or '0 0 1280 720').split()[2])
    except Exception: VW = 1280.0
    S = im.width / VW
    parent = {c: p for p in root.iter() for c in p}
    in_defs = {id(e) for d in root.iter(NS + "defs") for e in d.iter()}
    def inherited(el, key):
        e = el
        while e is not None:
            v = _style(e, key)
            if v is not None: return v
            e = parent.get(e)
        return None
    def transformed(el):
        e = el
        while e is not None:
            if e.get("transform") or e.tag in (NS + "pattern", NS + "clipPath", NS + "mask"): return True
            e = parent.get(e)
        return False
    seen = 0
    for t in root.iter(NS + "text"):
        if id(t) in in_defs: continue
        s = "".join(t.itertext()).strip()
        if not s: continue
        if len(s) <= 2 and not any(ch.isalnum() for ch in s): continue   # 单个符号（› ✓ ★）按图标处理，不算文字
        fill = (inherited(t, "fill") or "#000000").strip(); fill = NAMED.get(fill.lower(), fill)
        if not fill.startswith("#"): continue                      # none / url(#渐变) / currentColor：跳过
        op = 1.0
        for k in ("opacity", "fill-opacity"):
            try: op *= float(inherited(t, k) or 1)
            except ValueError: pass
        if op < 0.9: continue                                      # 半透明装饰字
        if transformed(t): continue                                # 旋转/位移过的字，坐标不可靠
        sz = f(t.get("font-size") or inherited(t, "font-size"), 16)
        w8 = str(inherited(t, "font-weight") or "400"); bold = w8 in ("bold", "bolder") or (w8.isdigit() and int(w8) >= 700)
        large = sz >= 24 or (bold and sz >= 18.66)
        x, y = f(t.get("x")), f(t.get("y")); anchor = t.get("text-anchor", "start")
        spans = list(t.iter(NS + "tspan"))
        if spans and spans[0].get("x"): x = f(spans[0].get("x"))
        if spans and spans[0].get("y"): y = f(spans[0].get("y"))
        first = (spans[0].text if spans and spans[0].text else s)[:60]
        wd = min(tw(first, sz), VW); left = x - (wd if anchor == "end" else wd / 2 if anchor == "middle" else 0)
        box = (int(max(0, left - 3) * S), int(max(0, y - sz * 0.9) * S), int(min(VW, left + wd + 3) * S), int(min(im.height / S, y + sz * 0.25) * S))
        if box[2] - box[0] < 4 or box[3] - box[1] < 4: continue
        fc = _rgb(fill)
        px = _px(im.crop(box) if (box[2]-box[0])*(box[3]-box[1]) < 60000 else im.crop(box).resize(((box[2]-box[0]) // 3, (box[3]-box[1]) // 3), 0))
        bgpx = [p for p in px if _dist(p, fc) > 90]
        if len(bgpx) < len(px) * 0.25: continue                    # 几乎全是字本身，取不到背景
        from collections import Counter
        q = Counter((p[0] // 16, p[1] // 16, p[2] // 16) for p in bgpx).most_common(1)[0][0]
        grp = [p for p in bgpx if (p[0] // 16, p[1] // 16, p[2] // 16) == q]
        bg = tuple(sum(p[i] for p in grp) // len(grp) for i in range(3))
        uniform = len(grp) / len(bgpx) > 0.5                       # 背景是否单一（渐变/图片上 = 不单一）
        c = _cr(fc, bg); seen += 1
        need = 3.0 if large else 4.5; tag = f"'{s[:16]}' {fill} 于 #{bg[0]:02X}{bg[1]:02X}{bg[2]:02X} 上 {c:.2f}:1（{'大字' if large else '小字'} {sz:g}px）"
        is_acc = _dist(fc, acc) < 30 and _dist(acc, _rgb(tok["accent_text"])) > 30
        if c < need:
            hard = strict and uniform and (c < 3.0 or (is_acc and not large))
            (errs if hard else warns).append(("小字直接用了 accent，改用 accent_text " + tok["accent_text"] + "：" if is_acc and not large else "文字对比度不足：") + tag)
    e2, w2, st = area_check(im, tok, ptype); return errs, warns + w2, dict(st, texts=seen)

def area_check(im, tok, ptype):
    lim = tok["limits"]; warns = []
    acc = _rgb(tok["accent"]); acc2 = _rgb(tok["accent2"]) if tok.get("accent2") else None
    sm = im.resize((320, 180)); px = _px(sm); n = len(px)
    a1 = sum(1 for p in px if _dist(p, acc) < 45) / n
    a2 = (sum(1 for p in px if _dist(p, acc2) < 45) / n) if acc2 else 0.0
    amax = lim["accent_max"].get(ptype, lim["accent_max"]["content"])
    if a1 + (0 if acc2 and _dist(acc, acc2) < 45 else a2) > amax: warns.append(f"accent 面积 {a1+a2:.0%} > {amax:.0%}（{tok['profile']} / {ptype} 页）")
    if acc2 and a2 > lim["accent2_max"]: warns.append(f"accent2 面积 {a2:.0%} > {lim['accent2_max']:.0%}")
    import colorsys
    pal = [_rgb(v) for k, v in tok.items() if k in ("bg", "surface", "line", "text", "text_muted", "accent", "on_accent", "accent_text", "accent2") and v]
    sat = []
    for p in px:
        h, l, s_ = colorsys.rgb_to_hls(*[v / 255 for v in p])
        if s_ > 0.35 and 0.15 < l < 0.9: sat.append((p, h))
    if lim.get("off_palette_max") is not None:
        off = sum(1 for p, _ in sat if min(_dist(p, c) for c in pal) > 60) / n
        if off > lim["off_palette_max"]: warns.append(f"调色板外的高饱和颜色占 {off:.0%}（上限 {lim['off_palette_max']:.0%}）")
    if lim.get("hue_max"):
        from collections import Counter
        hb = Counter(int(h * 12) % 12 for _, h in sat); hues = sum(1 for v in hb.values() if v / n > 0.01)
        if hues > lim["hue_max"]: warns.append(f"一页里的色相数 {hues} > {lim['hue_max']}（彩虹页）")
    return [], warns, {"accent": a1, "accent2": a2}

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
    ap.add_argument("--any-size", action="store_true", help="非 1280×720 的图（README 横幅）")
    ap.add_argument("--colors", help="tokens.json（由 tokens.py 生成）"); ap.add_argument("--page-type", default="content")
    a = ap.parse_args(); safe = tuple(float(v) for v in a.safe.split(","))
    tok = None
    if a.colors:
        import json
        tok = json.load(open(a.colors))
        if "limits" not in tok:
            sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); import tokens as _t; tok["limits"] = _t.LIMITS[tok.get("profile", "solid")]
        print(f"配色 token: {tok.get('pack','?')} / {tok.get('profile','solid')}")
        for fg, bg, target, hard, note in [("text", "@", 7.0, 4.5, "正文"), ("text_muted", "@", 4.5, 4.5, "次要文字"), ("on_accent", "accent", 4.5, 3.0, "accent 上的文字"), ("accent_text", "@", 4.5, 4.5, "小字强调色")]:
            bk = tok.get("content_bg", "bg") if bg == "@" else bg; c = _cr(_rgb(tok[fg]), _rgb(tok[bk]))
            lv = "OK" if c >= target else "WARN" if c >= hard else "FAIL"
            print(f"  [{lv}] {fg}/{bk} {c:.2f}:1 {note}")
            if lv == "FAIL": bad_tokens = True
        if any(_cr(_rgb(tok[fg]), _rgb(tok[tok.get("content_bg","bg") if bg=="@" else bg])) < hard for fg, bg, hard in [("text","@",4.5),("text_muted","@",4.5),("on_accent","accent",3.0),("accent_text","@",4.5)]):
            print("  ✗ token 配对不达标：先运行 tokens.py --fix tokens.json"); tokfail = True
        else: tokfail = False
    global ANY_SIZE; ANY_SIZE = a.any_size
    files = []
    for i in a.inputs: files += sorted(glob.glob(os.path.join(i, "*.svg"))) if os.path.isdir(i) else [i]
    if tok:  # 只有 PNG（如拼图、画廊）：只做面积/色相检查
        from PIL import Image
        for fp in [x for x in files if x.lower().endswith(".png")]:
            _, w2, st = area_check(Image.open(fp).convert("RGB"), tok, a.page_type)
            print(f"[{'WARN' if w2 else 'OK'}] {os.path.basename(fp)}（PNG，仅面积/色相；accent {st['accent']:.0%}）")
            for w in w2: print("   !", w)
        files = [x for x in files if not x.lower().endswith(".png")]
    os.makedirs(a.out, exist_ok=True); bad = False; pngs = []
    for fp in files:
        errs, warns = check(fp, safe)
        png = os.path.join(a.out, os.path.splitext(os.path.basename(fp))[0] + ".png")
        r = subprocess.run(["rsvg-convert", "-z", "1.5", "-o", png, fp], capture_output=True, text=True)
        if r.returncode: errs.append("渲染失败: " + r.stderr.strip()[:200])
        else:
            pngs.append(png)
            if tok:
                try: _root = ET.parse(fp).getroot()
                except ET.ParseError: _root = None
                if _root is not None:
                    ce, cw, _st = color_check(fp, png, tok, page_type(fp, _root, a.page_type)); errs += ce; warns += cw
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
    if tok and tokfail: bad = True
    sys.exit(1 if bad else 0)

if __name__ == "__main__": main()
