# Design Quality Gate

## Benchmark

Use the Agentopia reader quality as a baseline: the first viewport should immediately feel like a designed learning product, not an internal generated note.

The first viewport should usually include:

- paper-specific title and subtitle
- visible language mode such as `中英 / 中文 / EN only` for non-Chinese papers
- chapter map with visual landmarks or strong section affordances
- main reading card with paragraph-level original text and Chinese reading
- synchronized side note, marginalia, or learning panel
- paper-specific visual assets or generated illustrations

## Fail states

Reject and redesign if the page looks like any of these:

- generic gray/white admin dashboard
- plain three-column documentation layout with little typographic hierarchy
- tiny SVG flow boxes used as the main "generated diagrams"
- all source figures or tables pushed to the end
- full paper text hidden in collapsed raw `<pre>` blocks while the main reader shows only excerpts
- no language mode for non-Chinese material
- no theme derived from the paper topic, figures, audience, or user preference

## Visual direction

Before coding, choose a visual direction and write it down:

- paper topic and emotional tone
- visual metaphor or motif
- typography scale
- color palette
- icon/illustration style
- how figures and generated diagrams will sit in the reading flow

For academic learning sites, prefer restrained but distinctive design. Use texture, illustration, chapter landmarks, and clear typography; avoid decorative noise.

## First-screen acceptance

Take a desktop screenshot before final delivery. A reviewer should be able to tell within five seconds:

- what paper this is
- that it is a bilingual/source-text reader
- where to start reading
- how to switch chapters
- where explanations and terms will appear

If not, iterate on layout before polishing content.
