# NOTICE
scripts/ 下的脚本为原创编写，未复制第三方源码。
- svg2pptx.py 的思路（在 PPTX 中嵌入原生 SVG 图片部件）参考了 zhx47/ppt-agent
  (https://github.com/zhx47/ppt-agent, Apache License 2.0) 中 orchestrator.py 的 SvgImagePart；
  本实现改用标准 a:blip/asvg:svgBlip 扩展 + PNG 回退。
- SKILL.md 中标注 "adapted from zhx47/ppt-agent (Apache-2.0)" 的规则与提示词改编自该项目
  backend/app/services/prompt_contracts.py、generation.py 与 docs/。
  Copyright © zhx47. Licensed under the Apache License, Version 2.0:
  http://www.apache.org/licenses/LICENSE-2.0  —— 已改写与翻译整合，非原样复制。

## 风格包参考（仅借鉴思路，未复制代码）
- lewislulu/html-ppt-skill（MIT）https://github.com/lewislulu/html-ppt-skill ：主题 token 结构（glassmorphism、blueprint、pitch-deck-vc、swiss-grid）。
- anthropics/skills frontend-design（Apache-2.0）https://github.com/anthropics/skills/tree/main/skills/frontend-design ：背景要有氛围和层次、避免模板化默认审美。
- courtsimas/glass-lens（MIT）https://github.com/courtsimas/glass-lens 、LeonardSEO/liquid-glass-react（MIT）https://github.com/LeonardSEO/liquid-glass-react 、dpawlikowski/liquid-glass（MIT）https://github.com/dpawlikowski/liquid-glass ：feDisplacementMap 折射、滤镜作用于背景副本、边缘色散。
- nextlevelbuilder/ui-ux-pro-max-skill（MIT）https://github.com/nextlevelbuilder/ui-ux-pro-max-skill ：styles.csv 中 Neumorphism、Claymorphism、Neubrutalism、Material 3、Aurora、Editorial Grid、Liquid Glass 等风格的关键词与配色参考。
- nostalgic-css/NES.css（MIT）https://github.com/nostalgic-css/NES.css ：像素边框与 8-bit 视觉语言（pixel-8bit 思路参考）。
- rough-stuff/rough（MIT）https://github.com/rough-stuff/rough ：手绘抖动、双线描边、hachure 填充的视觉思路（sketch 用 SVG 滤镜原创实现）。
- lewislulu/html-ppt-skill 的 blueprint、vaporwave 主题，以及 ui-ux-pro-max-skill styles.csv 的 Dashboard、HUD/Sci-Fi FUI、Pixel Art、Vaporwave、Y2K、Sketch Hand-Drawn 条目：配色与关键词参考。
- 所有角色/吉祥物插画均为本项目原创 SVG 占位图，不含任何第三方 IP。
