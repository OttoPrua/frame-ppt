#!/usr/bin/env python3
"""第 6.5 步：素材委派（可选，默认关闭）。所有路径都相对 manifest 所在目录。
  assets.py prompt  assets/manifest.json            # 给待委派槽位写提示词和 requests/<slot>.json，打印清单（付费调用前给用户看）
  assets.py compose assets/manifest.json [--placeholders]
        # 生成器槽位就地生成；代理槽位读取返回文件 → 校验 → 重着色 → 写回 SVG 的 <g data-slot>；不合格就用 fallback
提示词 = styles/asset-prompts.json 的风格包预设 + 项目主题（manifest.subject 或 slot.subject）。预设只是起点，
代理可以在 slot.prompt 里直接写改好的版本，脚本不会覆盖已有的 prompt。"""
import json, os, re, sys, base64, subprocess, argparse
from PIL import Image
HERE = os.path.dirname(os.path.abspath(__file__))
PRESETS = os.path.join(HERE, "..", "styles", "asset-prompts.json")
def load(p): return json.load(open(p, encoding="utf-8"))
def save(p, d): json.dump(d, open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=2)

def size_for(b):
    """按 bbox 比例给图像 API 的尺寸：16 的倍数，长边 1024~1536，比例限制在 1:3 到 3:1"""
    r = max(1 / 3, min(3, b["w"] / b["h"])); L = 1536 if max(r, 1 / r) > 1.2 else 1024
    w, h = (L, L / r) if r >= 1 else (L * r, L)
    return f"{int(round(w / 16)) * 16}x{int(round(h / 16)) * 16}"

def build_prompt(M, s, P):
    pk = P["packs"][M["pack"]]; subj = s.get("subject") or M.get("subject") or "项目的核心主题"
    p = P["_模板"].format(subject=subj, look=pk["look"], mono=pk["mono"])
    extra = P["_类型补充"].get(s["type"], "")
    return p + (" " + extra if extra else "")

def cmd_prompt(mp):
    M = load(mp); root = os.path.dirname(os.path.abspath(mp)); P = load(PRESETS); todo = []
    os.makedirs(os.path.join(root, "requests"), exist_ok=True)
    for s in M["slots"]:
        if s["provider"]["kind"] == "generator": continue
        if not s.get("prompt"): s["prompt"] = build_prompt(M, s, P)
        rq = dict(slot=s["id"], page=s.get("page"), type=s["type"], prompt=s["prompt"],
                  request=dict(size=size_for(s["bbox"]), background="transparent", output_format="png", quality=s.get("quality", "medium")),
                  write_to=os.path.join(root, s["output"]), note="单色输出即可，颜色由 recolor.py 统一处理；先写 .tmp 再改名；同目录写 <slot>.meta.json（工具/模型/参数/许可说明）")
        save(os.path.join(root, "requests", s["id"] + ".json"), rq); s["status"] = "requested"; todo.append(rq)
    save(mp, M)
    print(f"{len(todo)} 个槽位待委派（付费图像 API 必须先经用户确认）：")
    for r in todo: print(f"  [{r['slot']}] {r['request']['size']}  {r['prompt'][:60]}…")

def uri(p):
    mime = "image/svg+xml" if p.endswith(".svg") else "image/png"
    return f"data:{mime};base64," + base64.b64encode(open(p, "rb").read()).decode()

def placeholder(s, tok):
    b = s["bbox"]
    return (f'<rect x="{b["x"]}" y="{b["y"]}" width="{b["w"]}" height="{b["h"]}" fill="none" stroke="{tok["line"]}" stroke-width="2" stroke-dasharray="10 8"/>'
            f'<text x="{b["x"] + 14}" y="{b["y"] + 30}" font-family="\'Noto Sans SC\',sans-serif" font-size="16" fill="{tok["text_muted"]}">[{s["id"]}] {s["type"]} {b["w"]}x{b["h"]}</text>')

def cmd_compose(mp, ph):
    M = load(mp); root = os.path.dirname(os.path.abspath(mp)); P = load(PRESETS)
    tokp = os.path.join(root, M["tokens"]); tok = load(tokp); pk = P["packs"].get(M.get("pack"), {}); log = []
    for s in sorted(M["slots"], key=lambda s: s.get("z", 0)):
        b = s["bbox"]; out = os.path.join(root, s["output"]); frag = ""; recol = False
        if ph: frag = placeholder(s, tok); s["status"] = "placeholder"
        else:
            if s["provider"]["kind"] == "generator" and not os.path.exists(out):
                g = s["provider"]; kind = g.get("generator") or pk.get("background", {}).get("generator", "dotline")
                os.makedirs(os.path.dirname(out), exist_ok=True)
                cmd = [sys.executable, os.path.join(HERE, "genbg.py"), kind, tokp, out, "--seed", str(g.get("seed", 7)), "--w", str(b["w"]), "--h", str(b["h"])]
                subprocess.run(cmd + (["--transparent"] if s.get("transparent", True) else []), check=False)
            s["attempts"] = s.get("attempts", 0) + (0 if s["provider"]["kind"] == "generator" else 1)
            ok, why, use = os.path.exists(out), "未返回", out
            rc = s.get("recolor", pk.get("recolor") if s["type"] in ("figurative", "icon") else None)
            if ok and out.endswith(".png"):
                if rc:
                    use = out[:-4] + ".recolored.png"
                    subprocess.run([sys.executable, os.path.join(HERE, "recolor.py"), out, use, tokp, "--mode", rc["mode"], "--roles", ",".join(rc["roles"])], check=True)
                    recol = True
                im = Image.open(use); r = im.width / im.height; want = b["w"] / b["h"]
                if s.get("transparent", True) and (im.mode != "RGBA" or im.getchannel("A").getextrema()[0] > 10): ok, why = False, "没有透明背景"
                elif abs(r - want) / want > 0.15 and s.get("fit", "meet") == "strict": ok, why = False, f"比例 {r:.2f} 与槽位 {want:.2f} 不符"
            if ok:
                frag = (f'<image data-slot-asset="{s["id"]}" data-asset-type="{s["type"]}" data-recolored="{1 if recol else 0}" x="{b["x"]}" y="{b["y"]}" width="{b["w"]}" height="{b["h"]}"'
                        f' opacity="{s.get("opacity", 1)}" preserveAspectRatio="xMidYMid meet" xlink:href="{uri(use)}"/>')
                s["status"] = "composited"
            else:
                fb = s.get("fallback", {"kind": "builtin-svg", "snippet": ""}); s["status"] = f"fallback:{why}"
                frag = fb.get("snippet", "") if fb.get("kind") == "builtin-svg" else placeholder(s, tok) if fb.get("kind") == "placeholder" else ""
        svgp = os.path.join(root, s["svg"]); svg = open(svgp, encoding="utf-8").read()
        if "xmlns:xlink" not in svg: svg = svg.replace("<svg ", '<svg xmlns:xlink="http://www.w3.org/1999/xlink" ', 1)
        pat = rf'<g data-slot="{re.escape(s["id"])}"([^>]*?)(/>|>.*?</g data-slot-end>|>.*?</g>)'
        new, n = re.subn(pat, lambda m: f'<g data-slot="{s["id"]}"{m.group(1)}>{frag}</g>', svg, count=1, flags=re.S)
        if not n: s["status"] = "错误：SVG 里找不到 <g data-slot>"
        open(svgp, "w", encoding="utf-8").write(new); log.append(f'  {s["id"]} → {s["svg"]}: {s["status"]}')
    save(mp, M); print("\n".join(log))

if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("cmd", choices=["prompt", "compose"]); ap.add_argument("manifest"); ap.add_argument("--placeholders", action="store_true")
    a = ap.parse_args(); cmd_prompt(a.manifest) if a.cmd == "prompt" else cmd_compose(a.manifest, a.placeholders)
