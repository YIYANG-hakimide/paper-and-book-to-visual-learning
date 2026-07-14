# Visual Page Teaching Contract

Use this contract for image-series and presentation-PDF outputs. A page is not complete merely because it has a title, a beautiful image, and a caption. It must teach a reader who has no presenter beside them.

## Opening Contract

The opening must orient the learner before detailed exposition.

- Page/item 1 may be a cover-thesis page, but it must state the paper's real question and answer.
- An explicit `paper-overview` must appear by item 2.
- An explicit `argument-map` must appear by item 3. One page may combine overview and argument map when the selected size is concise.
- Background or prerequisite teaching must precede the first detailed method, result, or case page.
- A method/framework overview must precede component-level detail when the source has a multi-stage method.
- When a multi-stage method can be demonstrated, include at least one `worked-example` that follows a concrete input through the entire pipeline.

The storyboard must contain `paper_argument_map` with:

- `main_question`
- `thesis`
- `argument_steps[]` with at least three ordered steps
- `evidence_route[]` explaining how the paper tests or supports the thesis
- `conclusion`
- `limitation`

Do not substitute a generic agenda, section list, or chapter menu for this map.

The storyboard also records `prerequisites_required`, `method_stage_count`, `worked_example_required`, and `paper_has_experiments`, each with a short rationale where applicable. A method with at least three stages requires a worked example. Experimental papers must teach experiment setup before result evidence.

## Standalone Page Contract

Every non-cover page/item records:

- `sequence_role`: `cover-thesis`, `paper-overview`, `argument-map`, `prerequisite`, `framework-overview`, `method-detail`, `argument-detail`, `worked-example`, `experiment-setup`, `evidence`, `conclusion`, `limitation`, or `recap`
- `information_groups[]`: the 2-4 distinct teaching groups visible on the page
- `scan_order[]`: at least three short steps telling the intended reading order
- `reader_takeaway`: what the learner should be able to say after reading it
- `teaching_units[]`: each unit names the claim/concept, explanation, visual anchor, and source ids

Minimum information groups:

- cover: 1
- overview, argument map, experiment setup, evidence, recap: 3
- other teaching pages: 2

Low-density presentation pages are allowed only for a deliberate tension, transition, or conclusion beat. Record `low_density_reason`; do not let low-density pages exceed roughly one quarter of teaching pages.

For every hard concept, the teaching inventory records the field definition, plain explanation, meaning in this paper, common misunderstanding, and the final pages that teach it. For every experiment, record comparison objects, sample size, metric and its meaning, evaluator, baseline status, uncertainty or missing details, setup pages, result pages, and limitation pages. When the paper does not report a required detail, write `not_reported_by_paper` and expose that omission on a visible limitation page.

For formulas and algorithms, record the exact expression/name, plain explanation, critical OCR tokens, and render pages. Those tokens must be included in `expected_labels[]` and found by the executable OCR pass; missing operators or replacement glyphs block delivery.

Evidence pages also record `source_evidence_objects[]`. Each source crop/table/chart needs a reader question, annotated regions, and `readable_at_final_size: true`. A full paper page reduced to a thumbnail does not count as evidence teaching.

Every comparison claim records `comparison_validity` and `evidence_strength`. Words such as “证明”, “击败”, “导致”, or a causal “提升了” require a controlled comparison. Cross-benchmark or descriptive comparisons must use weaker wording such as “观察到”, “数值更高”, or “与该解释一致”.

## Visual Semantics

Every substantial generated teaching visual except a purely decorative cover records:

- `diagram_labels[]`: normally 3-7 short, Chinese-dominant labels
- `visual_semantic_map[]`: visual element -> meaning -> paper concept/source
- `visual_relation_type` and `visual_relation_labels[]`: the causal, spatial, comparative, sequential, quantitative, or hierarchical relationship carried by the image
- `scan_order[]`: how the learner follows the image
- `text_integration.mode`: `in-model`, `reserved-zone-overlay`, or `source-annotation`
- `text_integration.planned_before_generation: true`
- `text_integration.native_resolution_composite: true`
- `in_image_text_language`, Chinese-dominant for Chinese readers

For `reserved-zone-overlay`, the generation prompt must reserve specific label/callout zones and the final Chinese text must be composed at the final asset resolution. A single generic caption below an unlabeled illustration does not satisfy this contract.

`expected_labels[]` cannot be empty for a text-bearing teaching visual. OCR must check the labels that explain the diagram, not only the page title or footer.

Store the actual OCR output under `qa/ocr/` and record its path, engine, and SHA256. The audit reads this artifact and compares it with the manifest; a self-declared `ocr_pass: true` without OCR evidence is invalid.

## Page Review Evidence

`qa/qa-report.json` must contain one review entry per final page/item. Each entry includes:

- final item id
- `visual_status`
- `information_status`
- `narrative_status`
- concrete findings
- fixes made, if any
- reviewed screenshot/image path and hash
- final status

The three required independent review lenses are:

1. visual design and aesthetic quality
2. information completeness and self-explanation
3. narrative logic and novice comprehension

A checked boolean or a generic sentence reused across pages is not review evidence. Status values must be `passed` or `fixed`, and the findings must point to the reviewed final asset rather than a manifest-only assertion.
