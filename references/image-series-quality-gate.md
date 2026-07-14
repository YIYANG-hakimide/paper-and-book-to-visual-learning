# Image Series Quality Gate

## Product Bar

The result is an ordered visual album, not presentation screenshots, isolated illustrations, or social cards with repeated templates. Each image should stand on its own while making the next image feel necessary.

It must be both informative and aesthetically authored. Reviewers should be able to identify the paper-specific art direction, not merely approve legibility.

## Sequence

- Lock the storyboard before final generation.
- Number every final image and preserve exact order.
- Keep a visible arc: problem, prerequisite, method, evidence, conclusion, limitation, recap.
- End on a recap that reconstructs the problem, method, evidence, conclusion, and limitation; do not place extra teaching pages after it.
- Use transitions or recurring visual motifs so the sequence feels authored as one work.
- Create a full contact sheet and verify the story remains legible at overview scale.
- Record an art-direction thesis, paper-specific visual objects, typography/material rules, and forbidden generic styles.
- Put a paper overview by image 2 and an argument map by image 3. These must explain the whole paper before the sequence enters component detail.

## Information Density

- Image pages may be denser than presentation pages.
- Use one dominant question plus 2-4 supporting information groups.
- Every non-cover image needs a visible scan order and enough integrated labels/callouts to explain the main visual without relying on a generic footer sentence.
- Prefer large diagrams, structured labels, comparisons, timelines, and evidence callouts over long paragraphs.
- Split any page whose labels or evidence become too small.

## Visual Variety

Vary the explanatory form according to content while keeping one visual system:

- scene or metaphor
- mechanism/process
- architecture or layered system
- before/after or baseline comparison
- timeline/map
- annotated source evidence
- deterministic data graphic
- formula/worked example
- limitation and recap map

Reject a series that repeats the same title-top/cards-below template throughout.

Do not repeat one main composition for more than three consecutive images. Medium and detailed albums should normally use at least four materially different composition families.

Reject a series that is technically correct but visually flat, generic, excessively text-heavy, or made from diagrams that could belong to any paper.

Use the deletion test: if removing the main image leaves almost the entire explanation intact, the image is decorative and does not count as a teaching visual. The visual must carry a causal, spatial, comparative, sequential, or quantitative relationship.

## Accuracy

- Verify the requested source file hash and page count against the final manifest before any other review.
- Generated images may explain but may not invent data or serve as proof.
- Exact figures, values, quotations, formulas, dates, and table cells must come from source-linked assets or deterministic overlays.
- OCR all generated text-bearing images and compare key labels.
- Reject any final image containing replacement boxes, garbled formulas, cropped branches, or leftover template rails/sidebars.
- Distinguish source evidence from generated explanation visually.
- Inspect every final image with visual understanding, then inspect the contact sheet for beauty, rhythm, variety, and narrative continuity.
- Verify every source crop is readable at the final image size; split or redraw evidence that only works after zooming.

## Packaging

- Store only final owned images in `assets/images/`.
- Store previews and rejected attempts outside the final image sequence.
- Deliver `001-...png` ordering, a page-matched album PDF, contact sheet, `data/storyboard.json`, `data/learning-series-manifest.json`, and `qa/qa-report.json`.
- No final bitmap may be orphaned or referenced by more than one storyboard item without an explicit reuse reason.
- The album PDF must contain exactly one final image per page in the same order and aspect ratio; verify all pages after export.
