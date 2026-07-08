# Implementation And Deploy

## Default output

Create a static site unless the user or existing project requires a framework:

```text
learn-paper-title/
  index.html
  assets/
    figures/
    diagrams/
    screenshots/
  data/
    learning-site-manifest.json
```

Use semantic HTML, scoped CSS, and small vanilla JS for chapter switching, drawers, popovers, figure hotspots, reading progress, and synchronized notes.

## Required content structures

Represent chapters as structured data when possible:

- id
- title
- short purpose
- source paragraphs
- translations/explanations
- terms
- figures/tables
- generated diagrams
- checkpoints
- source paragraph coverage status
- generated visual provenance
- paragraph anchors and inline term anchors
- public UI copy review status
- omitted source blocks with reasons
- per-chapter source coverage
- per-block explanation quality

This prevents repeated content and makes chapter navigation deterministic.

## Manifest

Create `data/learning-site-manifest.json` for every site:

```json
{
  "source_title": "Paper Title",
  "source_language": "en",
  "source_paragraphs_expected": 120,
  "source_paragraphs_rendered": 120,
  "paper_figures_expected": 9,
  "paper_figures_rendered": 9,
  "generated_visuals_expected": 12,
  "generated_visuals_rendered": 12,
  "image_generation_model": "Image 2",
  "public_ui_clean": true,
  "inline_terms_expected": 40,
  "inline_terms_rendered": 40,
  "term_strip_only_count": 0,
  "paragraph_anchors_expected": 120,
  "paragraph_anchors_rendered": 120,
  "generated_visual_language": "zh-dominant",
  "design_brief": {
    "visual_direction": "lab-notebook reader with crisp evidence panels",
    "topic_motif": "attention routing and information flow",
    "typography_plan": "serif-like source text, high-line-height Chinese reading, compact evidence labels",
    "why_not_generic": "the page uses paper-specific diagrams, evidence cards, and source artifacts instead of a dashboard grid"
  },
  "layout_strategy": {
    "summary": "stacked first-pass reader with figure-led experiment sections",
    "desktop_first_viewport_checked": true,
    "mobile_layout_checked": true
  },
  "source_rendering_modes": ["parallel-bilingual", "stacked-bilingual", "interleaved-close-reading", "figure-led"],
  "source_screenshot_blocks": [
    {
      "source_id": "sec4-formula-02",
      "path": "assets/screenshots/sec4-formula-02.png",
      "reason": "formula layout",
      "selectable_text_fallback_id": "block-sec4-formula-02"
    }
  ],
  "interaction_inventory": {
    "inline_terms": 40,
    "figure_hotspots": 9,
    "formula_breakdowns": 3,
    "comparison_tables": 2,
    "chapter_quizzes": 6,
    "knowledge_map": true,
    "tested_controls": [
      {
        "control_id": "term-self-attention",
        "trigger": "inline term button",
        "state_change": "opens term drawer and sets aria-expanded=true",
        "close_method": "close button and Escape",
        "linked_source_ids": ["sec3-p04"]
      }
    ]
  },
  "source_blocks": [
    {
      "source_id": "sec3-p04",
      "section_id": "3",
      "page_start": 5,
      "page_end": 5,
      "order": 34,
      "source_text_hash": "sha256:...",
      "source_word_count": 92,
      "rendered_block_id": "block-sec3-p04",
      "chapter_id": "chapter-3"
    }
  ],
  "chapter_coverage": [
    {
      "chapter_id": "chapter-3",
      "expected_source_ids": ["sec3-p04"],
      "rendered_source_ids": ["sec3-p04"],
      "missing_source_ids": [],
      "omitted_source_ids": [],
      "source_word_count": 92,
      "translation_char_count": 214,
      "explanation_char_count": 180
    }
  ],
  "term_anchors": [
    {
      "term_id": "self-attention",
      "trigger_text": "Self-attention",
      "source_id": "sec3-p04",
      "rendered_block_id": "block-sec3-p04",
      "anchor_location": "source_text",
      "char_offset": 12,
      "is_inline": true
    }
  ],
  "paper_figures": [
    {
      "figure_id": "fig1",
      "path": "assets/figures/figure-1.png",
      "source_page": 3,
      "primary_rendered_block_id": "block-sec3-p04",
      "linked_source_ids": ["sec3-p04"],
      "explanation_cues_present": ["它是什么", "怎么看", "相比谁", "结论是什么", "不能推出什么", "回到原文"]
    }
  ],
  "generated_visuals": [
    {
      "id": "qkv-map",
      "path": "assets/diagrams/qkv-map.png",
      "model_name": "Image 2",
      "teaches_concept": "Q/K/V roles in attention",
      "reader_question": "Why does attention need three projections instead of one vector?",
      "why_image_needed": "The mechanism is spatial and hard to follow from text alone.",
      "prompt_language": "zh",
      "in_image_text_language": "zh-dominant",
      "chinese_label_ratio": 0.85,
      "linked_source_ids": ["sec3-p04"],
      "linked_claim_ids": [],
      "factual_values_used": [],
      "source_refs_for_values": []
    }
  ],
  "omitted_source_blocks": [],
  "tools_used": {
    "pdf_text": "pdfplumber",
    "figure_rendering": "pdftoppm",
    "browser_qa": "system Chrome headless"
  }
}
```

Counts must describe what is rendered in the main reading experience, not what is hidden in a raw appendix.

Use manifest fields to make reader-quality promises auditable:

- `public_ui_clean`: true only after scanning visible text for internal workflow/audience/build notes.
- `inline_terms_rendered`: count terms embedded inside source, translation, or explanation text, not detached glossary chips.
- `term_strip_only_count`: number of term chips that have no inline anchor; should be 0 unless explicitly justified.
- `paragraph_anchors_rendered`: number of source paragraphs with stable ids or `data-source-id`.
- `generated_visual_language`: use values such as `zh-dominant`, `en-dominant`, or `mixed`; Chinese-bilingual sites should usually be `zh-dominant`.
- `design_brief`: public-facing visual direction chosen for this paper. Include visual direction, motif, typography plan, and why the site is not a generic dashboard/template.
- `layout_strategy`: what layout system was chosen and whether desktop/mobile checks were run.
- `source_rendering_modes`: the actual modes used, such as `parallel-bilingual`, `stacked-bilingual`, `interleaved-close-reading`, `figure-led`, or `facsimile-plus-html`.
- `source_screenshot_blocks`: every original-text screenshot/facsimile block with source id, reason, path, and selectable text fallback id.
- `interaction_inventory`: count or describe real learning interactions: inline terms, figure hotspots, formula breakdowns, comparison tables, quizzes, knowledge maps, method chats, visualizers. Include tested controls with trigger, state change, close method, and linked source ids. Delete or implement any button that has no real state change.
- `source_blocks`: per-paragraph evidence that the page can trace rendered text back to the extracted paper.
- `chapter_coverage`: per-chapter expected/rendered source ids. Do not rely only on total counts.
- `term_anchors`: inline trigger inventory. `is_inline` should be true for the main learning entry point.
- `paper_figures`: each source figure/table's primary in-flow location, linked paragraph ids, and explanation cues.
- `generated_visuals`: model, language, source linkage, teaching concept, reader question, why an image was needed, and factual-value provenance for each generated teaching image.
- `omitted_source_blocks`: every skipped paragraph/table/appendix block, with a reader-facing reason.

## Static reader standards

- No PDF iframe as primary reading mode.
- A source PDF link can exist as secondary reference.
- Text should be selectable and searchable.
- Main paper text should be paragraph-level bilingual/Chinese reading blocks, not raw `<pre>` dumps.
- Source/translation layout should be chosen per section. Use side-by-side only when it improves readability; stacked or interleaved layouts are often better for dense paragraphs and mobile.
- Source prose screenshots are allowed only as facsimile aids paired with selectable source text, Chinese reading, and explanation.
- Non-Chinese sources should include visible language controls such as `中英 / 中文 / EN only`.
- Figure/table screenshots should be local assets with alt text.
- Generated diagrams should be local bitmap assets from Image 2 or the available image-generation tool, with nearby HTML explanations. Manual SVG diagrams are acceptable only as fallback after telling the user.
- Generated-diagram captions should explain the learning purpose, not expose asset provenance. Avoid public labels like "生成教学图资产", "Generated explainer", or prompt summaries in visible UI.
- Image `alt`, `title`, and `aria-label` are public UI too. Use learner-facing descriptions such as `Q/K/V 概念图` or `Figure 1 架构解读`, not `Generated explainer diagram`.
- Visible buttons should describe the learning action: `读 Figure 1 架构图`, `放大 Table 2 结果表`, `解释 BLEU`, not repeated generic labels like `打开图表抽屉`.
- Every reading block should carry a stable `data-source-id` and contain source, translation/Chinese reading, and plain-language explanation in the main flow.
- At least one real learning action should appear in each chapter when useful: inspect evidence, explain a term, break down a formula, compare a baseline, answer a quiz, or open a concept map.
- Language mode must actually switch reading layers: `中英` shows original and Chinese reading, `中文` hides or de-emphasizes original text while preserving a return-to-original affordance, and `EN only` shows source text while keeping term/figure anchors usable. The active paragraph and side panel must not lose sync after switching.
- Use `Learn <paper short title>` as title and deployment name.

## Vercel

If the user asked for Vercel:

1. Verify the local site first.
2. Deploy the static directory.
3. Rename the Vercel project to `learn-<paper-short-title>` when feasible.
4. Open or verify the live deployment URL.
5. Report the URL and any domain limitation separately.

## Validation script

Run:

```bash
python3 /path/to/paper-to-learning-site/scripts/audit_learning_site.py <site-dir-or-index.html>
```

Treat script errors as must-fix unless the output clearly identifies a false positive.
For final delivery, run strict mode:

```bash
python3 /path/to/paper-to-learning-site/scripts/audit_learning_site.py <site-dir-or-index.html> --strict
```
