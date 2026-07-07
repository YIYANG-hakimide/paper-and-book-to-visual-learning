# Image 2 Diagram Guidance

## Use images as teaching tools

Use Image 2 or the available image generation tool to create diagrams that reduce cognitive load. Generate more visuals when the paper has abstract mechanisms, multi-step methods, experiments, or unfamiliar terms.

Do not silently replace requested Image 2 diagrams with hand-written SVG diagrams. If no image-generation tool is available, stop and report that generated teaching visuals are blocked or ask whether a lower-fidelity SVG fallback is acceptable.

Minimum default:

- at least one generated explainer image per chapter
- one generated image for each major hard concept
- additional images for method pipelines, world-building, data construction, training loops, experiment comparisons, and result interpretation

## Diagram types

Choose the type that fits the learning job:

- process flowchart: step-by-step method
- system architecture map: components and data movement
- concept metaphor: vivid analogy for a hard term
- consulting-style framework: 2x2, layered stack, swimlane, or comparison matrix
- experiment setup diagram: input, intervention, measurement, output
- before/after or baseline/variant comparison
- timeline or chapter bridge
- annotated scene diagram for virtual worlds or simulations

## Prompt pattern

For generated visuals, specify:

- target learner: non-specialist college student
- learning purpose: the one thing the image must clarify
- visual form: flowchart, scene, metaphor, consulting diagram, etc.
- style tied to paper topic, not generic AI aesthetics
- no long text baked into image
- leave clean areas for HTML labels if needed
- output should be legible at web card size
- produce bitmap assets (`.png`, `.jpg`, or `.webp`) unless the image tool returns another real generated-image format

Example prompt:

```text
Create a clean explainer diagram for a non-specialist college student. Topic: supervised fine-tuning in this paper. Show three stages: human-labeled examples, model practice, evaluation on new tasks. Use a warm pixel-world classroom metaphor with small characters, arrows, and simple icons. Keep text in the image to tiny labels only; reserve detailed labels for HTML. Avoid generic neon AI dashboard style.
```

## HTML pairing

Every generated image needs nearby HTML explanation:

- what problem the image helps explain
- how to read it
- how it maps to the paper
- what simplification it makes

Do not rely on an image alone for factual explanation.

## Provenance

Record generated visuals in `data/learning-site-manifest.json`:

- file path
- model/tool used
- chapter/section
- teaching purpose
- prompt summary

If the asset was manually drawn SVG, mark it as `manual-svg-fallback` and do not count it as an Image 2 generated visual.
