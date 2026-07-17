# Paper and Book to Visual Learning

[简体中文](README.md) | [English](README_EN.md)

> Turn papers, books, articles, and other long-form sources into visual products that are easier to understand and see clearly.

[![Latest tag](https://img.shields.io/github/v/tag/YIYANG-hakimide/paper-and-book-to-visual-learning?display_name=tag&sort=semver&color=1f6f65)](https://github.com/YIYANG-hakimide/paper-and-book-to-visual-learning/tags)
[![Codex Skill](https://img.shields.io/badge/Codex-Skill-171717)](./SKILL.md)
[![License: MIT](https://img.shields.io/badge/license-MIT-b7482a)](./LICENSE)
[![GitHub Pages](https://img.shields.io/badge/preview-GitHub%20Pages-d7a928)](https://yiyang-hakimide.github.io/paper-and-book-to-visual-learning/)
[![GitHub Stars](https://img.shields.io/github/stars/YIYANG-hakimide/paper-and-book-to-visual-learning?style=flat&color=c88b2b)](https://github.com/YIYANG-hakimide/paper-and-book-to-visual-learning/stargazers)

**Paper and Book to Visual Learning** is for readers who want to understand a source rather than skim a summary. It transforms papers, full books, selected chapters, articles, white papers, reports, and manuals into guided visual outputs while preserving the concepts, argument, evidence, and boundaries that matter.

It supports paper visualization, book learning albums, research presentations, and bilingual interactive readers through one shared teaching workflow.

| Learning album | Interactive reader |
| --- | --- |
| [![Paper learning album preview](docs/assets/examples/paper-intervention-results.jpg)](docs/assets/examples/paper-intervention-results.jpg) | [![Interactive HTML reader preview](docs/assets/examples/html-agentopia-reward-reader.jpg)](docs/assets/examples/html-agentopia-reward-reader.jpg) |

Ask Codex to install it directly:

```text
Install this Skill: https://github.com/YIYANG-hakimide/paper-and-book-to-visual-learning
```

[View all samples](https://yiyang-hakimide.github.io/paper-and-book-to-visual-learning/#examples-en) · [Request a source example](https://github.com/YIYANG-hakimide/paper-and-book-to-visual-learning/issues/new?template=example-request.yml) · [Report a problem](https://github.com/YIYANG-hakimide/paper-and-book-to-visual-learning/issues/new?template=bug-report.yml)

## Three Modes

- **Images (personal learning album)**: A coherent sequence of standalone teaching visuals for self-study, review, and sharing, with an optional page-matched PDF album.
- **PPT (present to others, PDF + editable PPTX by default)**: A complete narrative for presentations, teaching, and discussion that also remains useful when read afterward.
- **HTML (interactive reader)**: An explorable reading experience connecting source passages, guided explanations, terms, figures, and evidence.

## Real Samples

### Paper To Learning Album

|  |  |
| --- | --- |
| [![Paper learning album sample one](docs/assets/examples/paper-residual-stream.jpg)](docs/assets/examples/paper-residual-stream.jpg) | [![Paper learning album sample two](docs/assets/examples/paper-intervention-results.jpg)](docs/assets/examples/paper-intervention-results.jpg) |

### Book To Learning Album

|  |  |
| --- | --- |
| [![Book learning album sample one](docs/assets/examples/book-resilience.jpg)](docs/assets/examples/book-resilience.jpg) | [![Book learning album sample two](docs/assets/examples/book-sleep-recovery.jpg)](docs/assets/examples/book-sleep-recovery.jpg) |

### Generated HTML

|  |  |
| --- | --- |
| [![Generated HTML sample one](docs/assets/examples/html-agentopia-figure-atlas.jpg)](docs/assets/examples/html-agentopia-figure-atlas.jpg) | [![Generated HTML sample two](docs/assets/examples/html-agentopia-reward-reader.jpg)](docs/assets/examples/html-agentopia-reward-reader.jpg) |

### Generated PPT

|  |  |
| --- | --- |
| [![Generated PPT sample one](docs/assets/examples/ppt-agentopia-training.jpg)](docs/assets/examples/ppt-agentopia-training.jpg) | [![Generated PPT sample two](docs/assets/examples/ppt-agentopia-argument-map.jpg)](docs/assets/examples/ppt-agentopia-argument-map.jpg) |

### Portrait Visual Learning Sample

<p align="center">
  <a href="docs/assets/examples/visual-courage-reading-map-portrait.jpg"><img src="docs/assets/examples/visual-courage-reading-map-portrait.jpg" alt="Portrait visual learning sample" width="560"></a>
</p>

[View the complete Courage to Be Disliked visual learning album PDF](https://github.com/YIYANG-hakimide/paper-and-book-to-visual-learning/releases/download/v0.2.3/courage-visual-learning-album.pdf)

If this project helps you understand a difficult source, a Star makes it easier for other readers to find it.

## Install And Update

Use Codex's built-in Skill installer:

```bash
python3 "${CODEX_HOME:-$HOME/.codex}/skills/.system/skill-installer/scripts/install-skill-from-github.py" \
  --repo YIYANG-hakimide/paper-and-book-to-visual-learning \
  --path . \
  --name paper-and-book-to-visual-learning
```

The Skill is available from the next task after installation.

It can also be installed as a Codex Plugin:

```bash
codex plugin marketplace add YIYANG-hakimide/paper-and-book-to-visual-learning
codex plugin add paper-and-book-to-visual-learning@paper-visual-learning
```

Or use Git:

```bash
git clone https://github.com/YIYANG-hakimide/paper-and-book-to-visual-learning.git \
  ~/.codex/skills/paper-and-book-to-visual-learning
```

Update an existing checkout:

```bash
git -C ~/.codex/skills/paper-and-book-to-visual-learning pull --ff-only
```

Other Skill-compatible agent platforms can also use this repository. Install it through that platform's Skill-directory or repository-import workflow and make sure the environment has a working image-generation capability.

## Usage

Call `paper-and-book-to-visual-learning`, provide a source file or link, and choose one primary output.

```text
Use $paper-and-book-to-visual-learning to turn this book into Images (personal learning album). Use defaults for everything else.
```

```text
Use $paper-and-book-to-visual-learning to turn this paper into a detailed PPT (PDF + editable PPTX by default).
```

```text
Use $paper-and-book-to-visual-learning to turn this report into HTML (interactive reader).
```

## Image Capability

Image albums and visual presentations require an available image-generation capability. In Codex, the recommended route is the system `imagegen` capability. Other agent platforms need access to a capable image-generation model; model permissions and file-delivery behavior vary by platform.

## Supported Sources

- Academic papers, research reports, and white papers
- Full books, selected chapters, and long-form articles
- Manuals, tutorials, and other structured long-form texts
- Local PDFs, documents, or accessible web sources

## Contribute

- [Request a source example](https://github.com/YIYANG-hakimide/paper-and-book-to-visual-learning/issues/new?template=example-request.yml)
- [Report a problem](https://github.com/YIYANG-hakimide/paper-and-book-to-visual-learning/issues/new?template=bug-report.yml)
- [Suggest an improvement](https://github.com/YIYANG-hakimide/paper-and-book-to-visual-learning/issues/new?template=feature-request.yml)
- [Read the contribution guide](.github/CONTRIBUTING.md)

## License

MIT. See [LICENSE](LICENSE).
