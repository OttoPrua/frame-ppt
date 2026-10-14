# NOTICE
scripts/ 下的脚本为原创编写，未复制第三方源码。
- svg2pptx.py 的思路（在 PPTX 中嵌入原生 SVG 图片部件）参考了 zhx47/ppt-agent
  (https://github.com/zhx47/ppt-agent, Apache License 2.0) 中 orchestrator.py 的 SvgImagePart；
  本实现改用标准 a:blip/asvg:svgBlip 扩展 + PNG 回退。
- SKILL.md 中标注 "adapted from zhx47/ppt-agent (Apache-2.0)" 的规则与提示词改编自该项目
  backend/app/services/prompt_contracts.py、generation.py 与 docs/。
  Copyright © zhx47. Licensed under the Apache License, Version 2.0:
  http://www.apache.org/licenses/LICENSE-2.0  —— 已改写与翻译整合，非原样复制。
