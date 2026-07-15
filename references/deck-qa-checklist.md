# Learning Deck QA Checklist

## Story And Teaching

- [ ] A complete `data/storyboard.json` was locked before final teaching-image generation.
- [ ] The storyboard has a visible problem -> prerequisites -> method -> evidence -> limitations/reconstruction arc.
- [ ] Every slide belongs to an act/chapter and has a necessary transition from the previous slide.
- [ ] Storyboard previous/next ids and bridges match the real adjacent page order.
- [ ] Every final generated image was planned for an existing storyboard slide before generation.
- [ ] The deck opens with the source's real problem, question, or central ideas, not production framing.
- [ ] The opening establishes the source question/ideas, overview, and argument/reading map before detail; simple sources may combine them.
- [ ] The outline follows learner questions and causal logic.
- [ ] Prerequisites appear before technical use.
- [ ] World/data construction, training, simulation/inference, and evaluation are separated where relevant.
- [ ] Every hard concept uses the full explanation ladder.
- [ ] Each slide has one clear learner question and one dominant teaching object.
- [ ] Each normal non-cover slide has 3-7 meaningful information groups, a visible scan order, and a standalone reader takeaway; sparse exceptions have a recorded reason.
- [ ] Dense ideas are split instead of compressed into tiny text.
- [ ] Recaps ask the learner to reconstruct the logic in their own words.
- [ ] The final recap covers problem, method, evidence, conclusion, and limitation.
- [ ] A full-deck contact sheet reads as one coherent lesson rather than unrelated posters.

## Visuals

- [ ] Most teaching slides contain a substantial visual, source evidence object, or formula/example breakdown.
- [ ] Every major concept that benefits from spatial or causal explanation has a generated teaching visual.
- [ ] A real Image 2 / `gpt-image-2` or other capable image-model smoke test was called and its saved bitmap/receipt was recorded before route availability was judged.
- [ ] Every non-trivial deck embeds at least one real generated bitmap, and every storyboard item routed to `generated` or `image-to-image` is fulfilled by a real generated asset.
- [ ] No planned generated visual was silently replaced by simple SVG, generic cards, primitive shapes, or a false manifest entry.
- [ ] Generated visuals are local raster assets and use the recorded real model.
- [ ] Visual style is derived from the source topic and remains coherent across the deck.
- [ ] Generated image labels are short, readable, and Chinese-dominant for Chinese readers.
- [ ] No important generated image is decorative only.
- [ ] No visual is cropped, blurry, too small, or overloaded.
- [ ] Source evidence and generated explanation are visually distinguishable.
- [ ] `assets/visuals/` contains no unused or orphan generated images.
- [ ] Every text-bearing generated visual has OCR results compared with the expected labels.
- [ ] Diagram labels, callouts, and visual meanings were planned before generation; a generic caption does not carry the whole explanation.
- [ ] Every generated visual records `display_width_px`, `display_height_px`, `crop_checked`, `reviewer_status`, and regeneration reason when it failed.
- [ ] Primary visuals occupy a substantial slide area; dense evidence is at least 1100px wide on stage or has a dedicated split/zoom slide.

## Evidence

- [ ] The complete in-scope source was inventoried before slide selection; full books/collections have an explicit whole-source or chapter/volume scope plan.
- [ ] The requested source file hash, page count, title, storyboard, manifest, and final deck all refer to the same source.
- [ ] Important source figures/tables appear in readable form.
- [ ] Multi-panel figures are split or individually annotated when needed.
- [ ] Every important figure/table explains what it shows, how to read it, baseline/metric, result, supported conclusion, and a limitation when relevant.
- [ ] Experimental setup and metric meaning appear before result claims.
- [ ] Every important result states baseline, metric, direction/value, evidence, and limitation.
- [ ] Generated images never serve as the sole proof of a conclusion.
- [ ] “查看原文依据” links or evidence slides land on the correct source object.
- [ ] Exact values, formulas, quotations, and citations are selectable HTML or faithful source crops.

## Design And Runtime

- [ ] Every slide fits the fixed 1920x1080 stage without scrolling.
- [ ] No text or image overlaps at desktop and smaller viewport scales.
- [ ] No missing glyphs, replacement boxes, cropped branches, or leftover template rails/sidebars remain.
- [ ] Typography remains readable when the stage is scaled to a laptop viewport.
- [ ] Previous/next, keyboard, overview, fullscreen, progress, and direct navigation work.
- [ ] No control opens an empty state or blocks the content it explains.
- [ ] Motion supports pacing and respects `prefers-reduced-motion`.
- [ ] Public slides contain no prompt, manifest, QA, reader-level, asset, or internal-review language.
- [ ] The first slide and first content slide feel paper-specific, not templated.
- [ ] Slide `layout_family` distribution was checked; one repeated composition does not dominate without a paper-specific reason.
- [ ] Storyboard order, manifest slide order, HTML order, PNG export order, and PDF order match.
- [ ] Each page has an obvious focal point and scan order.
- [ ] Every teaching page was reviewed without narration and remains understandable on its own.
- [ ] Section beats and evidence-dense pages form a deliberate reading rhythm without empty agenda filler.
- [ ] Report-level information density was checked; low-density pages are rare and justified.
- [ ] Each page records `text_character_count`, `information_group_count`, and `visual_route`; representative overview/concept and evidence/comparison pages meet the structural-density rule or have a specific visual-equivalence reason.
- [ ] Laptop reading and full-page PDF legibility were checked.
- [ ] Public copy passed `public-copy-style.md`, including internal-process leakage, repeated contrast syntax, empty conclusions, and template repetition.

## Export

- [ ] All local images load with no broken paths.
- [ ] PNG export preserves the complete stage and fonts.
- [ ] Editable PPTX and PDF exports both preserve page order, crop, fonts, text legibility, and visual placement; editable-object integrity was checked where practical.
- [ ] At least the title, one image-led slide, one evidence slide, and one dense slide were inspected after export.
- [ ] Every source crop is readable at final display size or has been split, zoomed, or redrawn.
- [ ] Vercel deployment is verified only after local QA passes.

## Adversarial Passes

Run three independent reviews and record one review row per final page:

1. Visual designer: hierarchy, composition, typography, style coherence, image scale, and anti-template quality.
2. Information reviewer: missing prerequisites, unexplained terms, insufficient labels/callouts, evidence interpretation, and whether each page is self-explanatory.
3. Narrative/novice reviewer: opening overview, argument order, causal bridges, and whether an ordinary reader can reconstruct the paper.

Fix concrete findings and rerun the relevant checks before delivery.
