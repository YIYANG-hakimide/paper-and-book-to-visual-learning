# Deck Design Quality Gate

## Product Bar

The result must feel like a deliberately art-directed presentation report: useful for explaining the source to other people and substantial enough to read afterward. It must not resemble an AI dashboard, a document pasted into slides, a low-density keynote deck, or twenty repetitions of one card layout. It should approach strong consulting and securities-research pages in structured information density while remaining more explanatory for a novice reader.

Every page needs a clear focal point, readable scan order, sufficient explanation, and enough breathing room to remain legible. A page that only works when a presenter fills in missing logic fails PPT mode.

## First Three Slides

Within the title slide and first two content slides, a reviewer should understand:

- which source this is
- the real problem or learner question
- the source-specific visual motif
- the deck's reading density and visual language
- that the first content slide already teaches something
- the source's complete argument/reading route from question or ideas to support and conclusion/synthesis

Reject generic agenda slides, audience descriptions, production framing, and template names.

Require the source overview and argument/reading map within the opening sequence before detail. They may share one page when simple. A list of chapter names or three contribution cards is not a map unless it shows how the parts connect and how examples/evidence support the conclusion or synthesis.

## Preview Difference

When multiple style previews are generated, they must differ in at least three of these dimensions:

- composition system
- typography character
- material/texture
- illustration language
- palette and contrast
- information rhythm

All previews must use real paper content. Do not present recolored versions of the same layout. When the direction is already clear, one well-inspected preview is enough and is preferred for speed.

## Slide Composition Families

Use multiple coherent composition families:

- image-led scene or mechanism
- annotated process or sequence
- source evidence close reading
- formula/worked example
- comparison or baseline board
- timeline/map/system view
- quotation or argument transition
- recap/reconstruction

Record `layout_family` on each slide. No single content layout family should occupy more than about 60% of teaching slides unless the design brief explains why the paper genuinely requires it. Avoid consecutive repetition of the same left-text/right-image composition.

Do not repeat one main composition for more than three consecutive teaching slides. Across a medium or detailed deck, use at least four materially different composition families.

## Reading Rhythm

Deliberately alternate framing questions, visual explanation, concrete examples, source evidence, conclusions, and synthesis. Use section beats to reset attention without adding empty agenda pages.

Read each page without narration during review. If a reader cannot reconstruct the claim, mechanism/reasoning, evidence/example, implication, and relevant boundary from the page, add the missing explanation or split the topic. If a page has no obvious first thing to look at, redesign it.

Low-density pages are rare and intentional. A sentence with a few unlabeled boxes does not count as a high-impact page.

## Size And Legibility

- A primary generated visual should normally occupy at least 40% of the slide content area.
- A dense source figure or table should normally render at least 1100px wide on the 1920x1080 stage, or receive a dedicated split/zoom slide.
- Generated full-slide teaching images should normally be at least 1536x864; prefer 1920x1080 or larger.
- At a 1366x768 browser viewport, key HTML text and in-image labels must remain comfortably readable. Treat labels whose rendered height is below roughly 16px as a failure.
- Do not place a complex diagram in a thumbnail beside a long paragraph.
- If a figure cannot meet these constraints, split it or use image-above/explanation-below across multiple slides.
- Meaningful teaching content should normally occupy roughly 55%-80% of the stage. Large empty regions are acceptable only when they create a deliberate tension, transition, or conclusion beat.
- Dense teaching pages should normally contain 3-7 visible information groups. Overview/concept pages normally fall near 350-650 Chinese characters; evidence/comparison pages near 450-900, excluding citations and text already readable inside evidence objects. Treat these as diagnostics, not permission to use tiny text.
- A source crop used as evidence should normally occupy at least 40% of the stage or receive its own zoom page with 2-4 annotations.

## Evidence Styling

Make the distinction visible:

- generated visual: explanation, analogy, mechanism, or orientation
- source crop: original evidence
- HTML chart/table/formula: precise reconstructed evidence
- conclusion: explicitly linked interpretation
- limitation: a visually consistent caution treatment

Do not let generated images imitate a source-paper screenshot so closely that learners may mistake illustration for evidence.

## Anti-Template Failures

Reject the deck when:

- it uses a generic purple/blue AI gradient with no paper-specific reason
- most pages are nested cards or dashboard panels
- every page repeats the same split layout
- decorative images dominate while mechanisms and evidence remain text-only
- the paper motif appears only on the cover
- title scale, body scale, and visual scale do not change with the teaching job
- source figures are too small to read
- image labels are garbled, tiny, or unrelated
- internal prompt, asset, QA, model, manifest, or reader-level text is public
- animations distract from reading or cause layout shifts
- every page has report-card density and no presentational breathing room
- the deck is merely image-series cards resized onto 16:9 pages
- most pages contain too little information to stand alone
- a normal content page has fewer than three meaningful information groups without a recorded reason
- the deck has no successfully embedded real generated bitmap, or a planned generated/image-to-image asset was silently replaced by SVG, cards, or primitive shapes
- the deck has high character count but lacks a conclusion, reasoning chain, evidence/example, implication, or relevant boundary
- a page title names a topic but does not state the question or conclusion
- exact evidence is replaced by a generated illustration

## Required Visual Review

Render every slide, then review:

1. hierarchy and focal point
2. image scale and crop
3. typography and bilingual spacing
4. repeated layout rhythm
5. source/generated distinction
6. label readability
7. overflow, collision, and clipping
8. first-slide and first-content-slide specificity
9. independent-reading completeness
10. conclusion -> explanation -> evidence -> implication structure where relevant

Record concrete failures and fixes in `qa/qa-report.json`. A manifest checkbox without rendered screenshots is not enough.
