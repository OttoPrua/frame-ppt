[English](README.md) | **简体中文**

# frame-ppt

> 给 AI Agent 用的 PPT skill：说一句 `frame`，从一个想法做到一套能直接用的精美 PPT。

> [!IMPORTANT]
> **它不是"一键生成页面"的工具。** frame 会和你一起把 PPT 想清楚：先用选择题问清需求，再用金字塔原理搭大纲，逐页和你确认内容，最后才出设计，交付可编辑、可直接上台的 PPT。

## 快速安装

把这句话发给你的 Agent（Claude Code、Hermes 等都可以）：

```text
请从 https://github.com/ottoprua/frame-ppt 安装这个 skill 到你的 skills 目录。
```

或者手动装到 Claude Code：

```bash
git clone https://github.com/ottoprua/frame-ppt.git ~/.claude/skills/frame-ppt
```

装好后直接说：**`frame：做一套 10 页的"如何开好会"培训 PPT`**

## 效果展示

**流程：先搭框架，再出画面**

<img src="docs/images/workflow.png" width="560" alt="工作流">

**成品示例（swiss 瑞士风）**

![效果展示](docs/images/showcase.png)

**初稿 → 设计稿**：骨架不变，只换皮

![初稿与设计稿](docs/images/draft-vs-final.png)

**拟物风（skeuo）**

![拟物风](docs/images/showcase-skeuo.png)

**磨砂玻璃风（glass）**

![磨砂玻璃风](docs/images/showcase-glass.png)

**发布会深色（apple-dark）** · **咨询风（consulting）** · **科技暗色（tech-dark）**

![apple](docs/images/showcase-apple.png)
![consulting](docs/images/showcase-consulting.png)
![tech](docs/images/showcase-tech.png)

**13 个风格包，同一页内容对比**（单张大图在 [docs/images/styles/](docs/images/styles/)），也支持品牌色或参考图

![风格包](docs/images/style-gallery.png)

导出：可编辑的 PPTX（每页内嵌 SVG，并附 PNG 回退），或单文件 HTML。

## 致谢与许可

[Apache-2.0](LICENSE)。部分规则和提示词改编自 [zhx47/ppt-agent](https://github.com/zhx47/ppt-agent)，详见 [NOTICE.md](NOTICE.md)。
