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
  "tools_used": {
    "pdf_text": "pdfplumber",
    "figure_rendering": "pdftoppm",
    "browser_qa": "system Chrome headless"
  }
}
```

Counts must describe what is rendered in the main reading experience, not what is hidden in a raw appendix.

## Static reader standards

- No PDF iframe as primary reading mode.
- A source PDF link can exist as secondary reference.
- Text should be selectable and searchable.
- Main paper text should be paragraph-level bilingual/Chinese reading blocks, not raw `<pre>` dumps.
- Non-Chinese sources should include visible language controls such as `中英 / 中文 / EN only`.
- Figure/table screenshots should be local assets with alt text.
- Generated diagrams should be local bitmap assets from Image 2 or the available image-generation tool, with nearby HTML explanations. Manual SVG diagrams are acceptable only as fallback after telling the user.
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
