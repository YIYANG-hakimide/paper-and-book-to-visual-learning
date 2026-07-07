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
  data/               optional JSON when useful
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

This prevents repeated content and makes chapter navigation deterministic.

## Static reader standards

- No PDF iframe as primary reading mode.
- A source PDF link can exist as secondary reference.
- Text should be selectable and searchable.
- Figure/table screenshots should be local assets with alt text.
- Generated diagrams should be local assets with nearby HTML explanations.
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
