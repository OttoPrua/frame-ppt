#!/usr/bin/env python3
"""配色角色 token：为 33 个风格包提供默认 token，并能按品牌色重新推导、自动修复对比度。
用法:
  tokens.py --list                                  列出风格包
  tokens.py <pack> -o tokens.json                   写出该风格包的默认 token
  tokens.py <pack> --accent "#00A86B" -o tokens.json  换成品牌主色，自动推导 on_accent / accent_text
  tokens.py --check tokens.json                      只检查 token 配对的对比度
  tokens.py --fix tokens.json                        自动修复不达标的 text_muted / on_accent / accent_text（原地写回）
只依赖标准库。对比度公式：WCAG 2.x (L1+0.05)/(L2+0.05)。
"""
import sys, json, argparse, colorsys

# profile: solid = 纯色强调（严格）；multi = 多色拼贴（面积放宽）；gradient = 渐变/玻璃/霓虹（面积与色相只提示）
# content_bg: 正文实际所在的底（bg 或 surface）
P = lambda bg, surface, line, text, muted, accent, on, at, accent2=None, profile="solid", content_bg="bg": dict(
    bg=bg, surface=surface, line=line, text=text, text_muted=muted, accent=accent, on_accent=on,
    accent_text=at, accent2=accent2, profile=profile, content_bg=content_bg)
PACKS = {
 "swiss":          P("#F4F4F0","#FFFFFF","#D6D6D0","#111111","#5E5E5E","#D90429","#FFFFFF","#D90429"),
 "minimalism":     P("#FFFFFF","#F5F5F5","#E5E7EB","#1F2937","#6B7280","#002FA7","#FFFFFF","#002FA7"),
 "editorial":      P("#EFE8DC","#F7F3EC","#D8CDBB","#111111","#5E564C","#8A2B1F","#FFFFFF","#8A2B1F","#2E3B32"),
 "consulting":     P("#FFFFFF","#F1F5F9","#CBD5E1","#0F172A","#475569","#003366","#FFFFFF","#005A9E","#FF8C00"),
 "apple-hig":      P("#F2F2F7","#FFFFFF","#C6C6C8","#000000","#6C6C70","#007AFF","#FFFFFF","#0062CC","#34C759", content_bg="surface"),
 "neumorphism":    P("#E0E5EC","#E0E5EC","#C3CBD8","#3D4852","#56606C","#6C63FF","#FFFFFF","#4F46D8"),
 "claymorphism":   P("#F4F1FA","#FFFFFF","#DDD6EE","#332F3A","#5A5562","#C4B5FD","#332F3A","#6D4AE0","#FDE68A", profile="multi"),
 "neo-brutalism":  P("#FFFDF5","#FFFFFF","#000000","#000000","#333333","#FFD93D","#000000","#000000","#FF6B6B", profile="multi"),
 "skeuo":          P("#3F322A","#F3E9D2","#C9B48A","#2B2118","#5E4E3C","#C9A24A","#2B2118","#7A5418", profile="multi", content_bg="surface"),
 "glass":          P("#0B0E2C","#1A1F4A","#3A4180","#F5F7FF","#B8C0EE","#F0ABFC","#0B0E2C","#F0ABFC","#FDE68A", profile="gradient"),
 "aurora":         P("#070B1F","#0B1026","#1E2A4A","#FFFFFF","#CBD5E1","#38BDF8","#070B1F","#7DD3FC", profile="gradient"),
 "apple-dark":     P("#000000","#1C1C1E","#2C2C2E","#F5F5F7","#A1A1A6","#7B61FF","#FFFFFF","#A594FF","#5AC8FA", profile="gradient"),
 "tech-dark":      P("#060B18","#0E1729","#1E2A44","#F8FAFC","#94A3B8","#00E5FF","#060B18","#00E5FF","#22C55E"),
 "saas-launch":    P("#FFFFFF","#F1F5F9","#E2E8F0","#0F172A","#64748B","#4F46E5","#FFFFFF","#4F46E5", profile="gradient"),
 "blueprint":      P("#0B3A6F","#0F4785","#5C8FCC","#E8F3FF","#AEE1FF","#FFD27A","#0B3A6F","#FFD27A"),
 "dashboard":      P("#F8FAFC","#FFFFFF","#E2E8F0","#111827","#5B6472","#2563EB","#FFFFFF","#2563EB","#10B981", profile="multi", content_bg="surface"),
 "neo-fintech":    P("#0A0B0E","#15171C","#262A33","#FFFFFF","#9CA3AF","#C6FF3D","#0A0B0E","#C6FF3D", profile="gradient"),
 "game-hud":       P("#091322","#111C33","#1F3050","#F8FAFC","#94A3B8","#FACC15","#091322","#FACC15","#22C55E", profile="multi"),
 "esports":        P("#0A1320","#141E30","#2A3650","#FFFFFF","#A1A1AA","#FF5A5A","#0A1320","#FF5A5A","#38BDF8", profile="multi"),
 "fantasy-rpg":    P("#1C162E","#2A2140","#4A3D66","#F6E3A1","#CDBF9F","#C9A24A","#1C162E","#D9B65A","#8B5CF6", profile="multi"),
 "gacha":          P("#EBF6FF","#FFFFFF","#C4B5FD","#3B2A63","#5E5280","#FFB86B","#3B2A63","#A2541A","#C4B5FD", profile="multi"),
 "mascot":         P("#FFF8EF","#FFFFFF","#FFE2BF","#3A2A1A","#7A5C40","#FFB547","#3A2A1A","#8E5418", profile="multi"),
 "manga":          P("#FFFFFF","#F5F2EA","#111111","#111111","#444444","#111111","#FFFFFF","#111111"),
 "kawaii-sticker": P("#FFF5F9","#FFFFFF","#FFC2D9","#4A2B3B","#7A5868","#FF6FA5","#4A2B3B","#B3245E","#FFD1E3", profile="multi"),
 "pixel-8bit":     P("#5FB4FF","#FFFFFF","#212529","#212529","#495057","#92CC41","#212529","#212529","#E76E55", profile="multi", content_bg="surface"),
 "vaporwave":      P("#1A0636","#2A0B52","#FF71CE","#FFFFFF","#FFC6EC","#00F0FF","#1A0636","#00F0FF","#FF71CE", profile="gradient"),
 "y2k":            P("#F6E6FE","#FFFFFF","#D9C2F5","#2B2B5E","#4B4B7A","#7B6CFF","#FFFFFF","#5546E0","#FF6EC7", profile="gradient"),
 "risograph":      P("#F7F4EA","#FFFCF2","#1A1A1A","#1A1A1A","#3D3D3D","#FF48B0","#1A1A1A","#B8146E","#0078BF", profile="multi"),
 "sketch":         P("#FBFAF5","#FFFFFF","#2B2B2B","#2B2B2B","#4A4A4A","#E76F51","#2B2B2B","#B4472C","#FFE66D", profile="multi"),
 "art-deco":       P("#0C2721","#123329","#D4AF37","#F7E7B0","#CDBF9F","#D4AF37","#0C2721","#D4AF37"),
 "pop-psychedelic":P("#8E44EC","#2A0A3D","#FFE74C","#FFFFFF","#FFE74C","#FF3D7F","#2A0A3D","#FFE74C","#FF9F1C", profile="gradient", content_bg="surface"),
 "memphis":        P("#FFF6E5","#FFFFFF","#111111","#111111","#333333","#FF4F81","#111111","#B8215A","#FFD23F", profile="multi"),
 "big-type":       P("#0E0E0E","#1C1C1C","#333333","#F2F2F2","#8C8C8C","#FF4A1C","#0E0E0E","#FF4A1C"),
}
# 每种 profile 的限制（accent 面积按页面类型；hue_max = 一页里面积 >1% 的色相桶上限）
LIMITS = {
 "solid":    {"accent_max": {"content": 0.15, "cover": 0.35, "section": 0.35, "manifesto": 0.35}, "accent2_max": 0.05, "hue_max": 3, "off_palette_max": 0.05, "strict_text": True},
 "multi":    {"accent_max": {"content": 0.35, "cover": 0.60, "section": 0.60, "manifesto": 0.60}, "accent2_max": 0.25, "hue_max": 6, "off_palette_max": 0.30, "strict_text": False},
 "gradient": {"accent_max": {"content": 0.40, "cover": 0.70, "section": 0.70, "manifesto": 0.70}, "accent2_max": 0.30, "hue_max": None, "off_palette_max": None, "strict_text": False},
}

def rgb(h): h = h.lstrip("#"); return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))
def hexc(c): return "#%02X%02X%02X" % tuple(max(0, min(255, round(v))) for v in c)
def lum(c):
    if isinstance(c, str): c = rgb(c)
    v = [x / 255 for x in c]; v = [x / 12.92 if x <= 0.04045 else ((x + 0.055) / 1.055) ** 2.4 for x in v]
    return 0.2126 * v[0] + 0.7152 * v[1] + 0.0722 * v[2]
def contrast(a, b):
    la, lb = lum(a), lum(b); return (max(la, lb) + 0.05) / (min(la, lb) + 0.05)

def shift_until(color, against, target):
    """保持色相，调明度直到对 against 的对比度 ≥ target。"""
    r, g, b = [x / 255 for x in rgb(color)]; h, l, s = colorsys.rgb_to_hls(r, g, b)
    darker = lum(against) > 0.18
    for _ in range(100):
        if contrast(color, against) >= target: return color
        l = max(0, l - 0.01) if darker else min(1, l + 0.01)
        color = hexc([x * 255 for x in colorsys.hls_to_rgb(h, l, s)])
    return "#000000" if darker else "#FFFFFF"

PAIRS = [  # (前景, 背景, 目标, 硬下限, 说明)
 ("text", "@content", 7.0, 4.5, "正文/标题"),
 ("text_muted", "@content", 4.5, 4.5, "次要文字"),
 ("on_accent", "accent", 4.5, 3.0, "accent 上的文字（≥24px 大字可放宽到 3:1）"),
 ("accent_text", "@content", 4.5, 4.5, "小字强调色"),
]
def check_pairs(t):
    out = []
    for fg, bg, target, hard, note in PAIRS:
        bgk = t.get("content_bg", "bg") if bg == "@content" else bg
        c = contrast(t[fg], t[bgk])
        level = "OK" if c >= target else ("WARN" if c >= hard else "FAIL")
        out.append((level, f"{fg} {t[fg]} / {bgk} {t[bgk]} = {c:.2f}:1（目标 {target}，下限 {hard}）{note}"))
    return out

def fix(t):
    cb = t[t.get("content_bg", "bg")]
    if contrast(t["text_muted"], cb) < 4.5: t["text_muted"] = shift_until(t["text_muted"], cb, 4.6)
    if contrast(t["accent_text"], cb) < 4.5: t["accent_text"] = shift_until(t["accent"], cb, 4.6)
    if contrast(t["on_accent"], t["accent"]) < 3.0:
        t["on_accent"] = max(["#FFFFFF", "#111111", t["text"], t["bg"]], key=lambda c: contrast(c, t["accent"]))
    if contrast(t["text"], cb) < 4.5: t["text"] = shift_until(t["text"], cb, 7.0)
    return t

def build(pack, accent=None, accent2=None):
    t = dict(PACKS[pack]); t["pack"] = pack
    if accent:
        t["accent"] = accent.upper(); t["accent_text"] = accent.upper()
        t["on_accent"] = max(["#FFFFFF", "#111111"], key=lambda c: contrast(c, accent))
    if accent2: t["accent2"] = accent2.upper()
    t = fix(t); t["limits"] = LIMITS[t["profile"]]
    return t

def main():
    ap = argparse.ArgumentParser(); ap.add_argument("pack", nargs="?"); ap.add_argument("-o", "--out")
    ap.add_argument("--accent"); ap.add_argument("--accent2"); ap.add_argument("--list", action="store_true")
    ap.add_argument("--check"); ap.add_argument("--fix")
    a = ap.parse_args()
    if a.list: print("\n".join(f"{k:16s} {v['profile']}" for k, v in PACKS.items())); return
    if a.check or a.fix:
        p = a.check or a.fix; t = json.load(open(p))
        if a.fix: t = fix(t); json.dump(t, open(p, "w"), indent=2, ensure_ascii=False)
        res = check_pairs(t); [print(f"[{l}] {m}") for l, m in res]
        sys.exit(1 if any(l == "FAIL" for l, _ in res) else 0)
    if a.pack not in PACKS: sys.exit(f"未知风格包 {a.pack}；用 --list 查看")
    t = build(a.pack, a.accent, a.accent2); s = json.dumps(t, indent=2, ensure_ascii=False)
    if a.out: open(a.out, "w").write(s + "\n"); print("已写出", a.out)
    else: print(s)
    for l, m in check_pairs(t): print(f"[{l}] {m}", file=sys.stderr)

if __name__ == "__main__": main()
