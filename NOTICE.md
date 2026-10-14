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
- nextlevelbuilder/ui-ux-pro-max-skill（MIT）https://github.com/nextlevelbuilder/ui-ux-pro-max-skill ：styles.csv 中 Neumorphism、Claymorphism、Neubrutalism、Aurora、Editorial Grid、Liquid Glass 等风格的关键词与配色参考。
- nostalgic-css/NES.css（MIT）https://github.com/nostalgic-css/NES.css ：像素边框与 8-bit 视觉语言（pixel-8bit 思路参考）。
- rough-stuff/rough（MIT）https://github.com/rough-stuff/rough ：手绘抖动、双线描边、hachure 填充的视觉思路（sketch 用 SVG 滤镜原创实现）。
- lewislulu/html-ppt-skill 的 blueprint、vaporwave 主题，以及 ui-ux-pro-max-skill styles.csv 的 Dashboard、HUD/Sci-Fi FUI、Pixel Art、Vaporwave、Y2K、Sketch Hand-Drawn 条目：配色与关键词参考。
- 所有角色/吉祥物插画均为本项目原创 SVG 占位图，不含任何第三方 IP。
- Apple Human Interface Guidelines（https://developer.apple.com/design/human-interface-guidelines/ ）：apple-hig 的设计原则与系统色参考，仅为文字与配色描述，未使用任何 Apple 素材或字体文件。
- ui-ux-pro-max-skill styles.csv 的 3D & Hyperrealism、Soft UI Evolution、Y2K Aesthetic、Memphis Design、Kinetic Typography 条目：风格关键词与典型适用行业参考。
- 所有示例页中的品牌、产品、人物、数据均为虚构；角色插画为本项目原创 SVG。

## 配色系统（附录 D、scripts/tokens.py、check_render.py --colors）
代码为原创，只依赖 Python 标准库和 Pillow；以下资料只借鉴规则和思路，未拷贝代码：
- WCAG 2.2 · Understanding 1.4.3 Contrast (Minimum) https://www.w3.org/WAI/WCAG22/Understanding/contrast-minimum.html 与 1.4.11 Non-text Contrast https://www.w3.org/WAI/WCAG22/Understanding/non-text-contrast.html （W3C 文档）：相对亮度与对比度公式、4.5:1 / 3:1 / 7:1 阈值、大字定义。
- Material Design 3 · Color roles https://m3.material.io/styles/color/roles ：角色 token 与 "on-" 配对思路；material-color-utilities（Apache-2.0）https://github.com/material-foundation/material-color-utilities 。
- Radix Colors（MIT）https://github.com/radix-ui/colors ：12 级阶梯的用途划分；亮色系实色配深色文字。
- Tailwind CSS（MIT）https://github.com/tailwindlabs/tailwindcss ：50–950 明度阶梯思路。
- ColorBrewer（Apache-2.0）https://github.com/axismaps/colorbrewer ：图表顺序/发散/类别色板思路。
- Adobe Leonardo（Apache-2.0）https://github.com/adobe/leonardo ：按目标对比度推导颜色的思路（tokens.py 的明度调整）。
- anthropics/skills · theme-factory（Apache-2.0）https://github.com/anthropics/skills/tree/main/skills/theme-factory ：主题先展示、再让用户确认。
- nextlevelbuilder/ui-ux-pro-max-skill（MIT）slide-color-logic.csv：按页面情绪限定 accent 用法。
- Okabe & Ito 色盲友好配色 https://jfly.uni-koeln.de/color/ ：多系列图表类别色。
- 60-30-10 面积比例：通用设计经验法则。
- 未采用 APCA（Myndex/apca-w3，自定义许可，非 MIT/Apache）。


## 素材委派（第 6.5 步，scripts/assets.py、genbg.py、recolor.py、styles/asset-prompts.json）
代码为原创，只依赖 Python 标准库和 Pillow；以下项目只借鉴思路，未拷贝代码：
- VincentGarreau/particles.js（MIT）https://github.com/VincentGarreau/particles.js 、tsparticles/tsparticles（MIT）https://github.com/tsparticles/tsparticles ：点线网络（plexus）背景的视觉思路。
- anthropics/skills algorithmic-art（Apache-2.0）https://github.com/anthropics/skills/tree/main/skills/algorithmic-art ：种子可复现的流场/粒子生成思路。
- OpenAI 图像生成指南 https://developers.openai.com/api/docs/guides/image-generation ：透明背景 PNG、尺寸约束（仅为接口参数说明）。
- 生成素材的使用条款以各生成服务为准；示例中的品牌、人物均为虚构，测试图为本地程序绘制。
