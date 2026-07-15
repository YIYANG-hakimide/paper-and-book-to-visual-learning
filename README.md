# Source to Visual Learning

> 把论文、书籍、文章、研究报告和其他难读长文本，变成看得懂、讲得清、可追溯的视觉学习产品。

[![Version](https://img.shields.io/badge/version-v0.6.0-2563eb)](https://github.com/YIYANG-hakimide/paper-to-learning-site)
[![Codex Skill](https://img.shields.io/badge/Codex-Skill-111827)](./SKILL.md)
[![Outputs](https://img.shields.io/badge/output-Image%20Album%20%7C%20PPT%2FPDF%20%7C%20Interactive%20HTML-16a34a)](#三种输出)

技术标识仍保留为 `paper-to-learning-site`，以兼容已有安装、链接和调用方式；界面名称更新为 **Source to Visual Learning**。论文仍是主要场景，但不再是唯一场景：完整书籍、选定章节、长文、白皮书、研究报告、手册等都可以作为来源。

## 三种输出

- **图片 / 图册**：主要用于个人学习。由 Image 2、`gpt-image-2` 或其他真实生图模型原生生成高信息量中文讲解图，并提供页序一致的 PDF。完整书籍会先确定全书或章节范围，必要时分卷生成。
- **PPT / 演示报告**：主要用于向他人讲述、汇报或讨论。默认同时提供可编辑 PPTX 和 PDF。采用咨询公司、券商研究报告式的结构密度：结论先行，同时给出解释链、证据/案例、含义与边界。
- **HTML / 互动阅读器**：用于逐段阅读、双语对照、术语解释、图表精读和证据跳转；需要时可部署。

图片图册与 PPT 不是同一产品换一个比例：图册追求每张图独立讲懂，PPT 追求在演示中讲清并在会后可独立阅读。

## PPT 的新密度与视觉规则

- 普通正文页通常包含 3–7 个有意义的信息组，而不是一句结论配几个空卡片。
- 总览/概念页通常约 350–650 个中文字符；证据/比较/精读页通常约 450–900 个中文字符。字符数只用于诊断，不能用小字号文字墙冒充信息密度。
- 每页以一个结论式信息为中心，同时组织解释链、证据或案例、`so what` 与必要边界。
- 逐页选择最合适的视觉路线：模型生成图、image-to-image 解释图、确定性图表/表格/公式，或原始图表裁切；不强迫统一格式。
- 每个非简单 PPT 必须真实调用 Image 2 / `gpt-image-2` 或其他可用生图模型，并嵌入至少一张返回的本地位图。所有计划为生成图或 image-to-image 的对象都必须兑现。
- 不能仅凭猜测认定图片无法保存。必须先做一次真实生图 smoke test，检查返回的本地路径。真实调用失败后，手工 SVG/CSS 替代仍需用户明确同意。

## 内容与证据

- 论文/研究报告：问题、必要背景、方法或论证、实验/证据、结论和边界。
- 书籍/文章：核心问题、观点或章节推进、关键例子、论证张力、综合判断；不会硬造“实验”和“贡献”。
- 手册：目标、前置条件、步骤、完整示例和常见失败方式。
- 生成图负责解释；原文、原始图表、公式、数据和实验负责证明。两者不会混淆。

## 安装

```bash
git clone https://github.com/YIYANG-hakimide/paper-to-learning-site.git ~/.codex/skills/paper-to-learning-site
```

也可以尝试：

```bash
npx skills add -g YIYANG-hakimide/paper-to-learning-site
```

## 使用

```text
用 $paper-to-learning-site 帮我把这本书做成个人学习图册，其余全部默认。
```

```text
用 $paper-to-learning-site 把这篇论文做成向团队汇报的 PPT，详细模式。
```

Skill 会一次性询问输出形式、重点、读者水平、规模和视觉偏好。确定输出后，回复“其余全部默认”即可开始。

## English

`paper-to-learning-site` is now presented as **Source to Visual Learning**. It turns papers, books, chapters, articles, reports, white papers, manuals, and other difficult long-form sources into native generated infographic albums, dense presentation reports delivered as both PPTX and PDF, or interactive bilingual HTML readers. The technical skill identifier remains unchanged for backward compatibility.
