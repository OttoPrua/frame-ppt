#!/usr/bin/env python3
"""把单色素材（黑线稿/黑剪影/黑白网点，白底或透明底）重着色成 tokens.json 的角色色，输出透明 PNG。
颜色只会是 token 里的精确色值，所以能通过 check_render 的调色板检查。
用法: recolor.py in.png out.png tokens.json [--mode line|flat|duo] [--roles accent[,text]] [--threshold 0.12]
  line/flat：所有墨迹 → roles[0]；duo：深墨迹 → roles[0]，中间调 → roles[1]（适合网点人像、漫画）"""
import json, argparse
from PIL import Image
ap = argparse.ArgumentParser(); ap.add_argument("inp"); ap.add_argument("out"); ap.add_argument("tokens")
ap.add_argument("--mode", default="line", choices=["line", "flat", "duo"]); ap.add_argument("--roles", default="accent")
ap.add_argument("--threshold", type=float, default=0.12)
a = ap.parse_args(); tok = json.load(open(a.tokens))
hexc = lambda h: tuple(int(h.lstrip("#")[i:i+2], 16) for i in (0, 2, 4))
roles = [r.strip() for r in a.roles.split(",")]; cols = [hexc(tok[r]) for r in roles]
if a.mode == "duo" and len(cols) < 2: cols.append(hexc(tok["text"]))
im = Image.open(a.inp).convert("RGBA"); W, H = im.size
src = im.load(); out = Image.new("RGBA", (W, H), (0, 0, 0, 0)); dst = out.load()
t = a.threshold
for y in range(H):
    for x in range(W):
        r, g, b, al = src[x, y]
        if al == 0: continue
        ink = 1 - (0.2126 * r + 0.7152 * g + 0.0722 * b) / 255          # 越黑墨越重
        if ink <= t: continue
        if a.mode == "duo":
            c = cols[0] if ink >= 0.55 else cols[1]; alpha = 255
        else:
            c = cols[0]; alpha = int(min(1, (ink - t) / 0.35) * 255)        # 抗锯齿边缘用 alpha，不产生中间色
        dst[x, y] = (*c, int(alpha * al / 255))
out.save(a.out)
print(f"recolor: {a.inp} → {a.out}（{a.mode}，{'/'.join(roles)}）")
