# Figure, Table, Data, And Experiment Explanations

## Placement

Show each source figure/table near the paragraph that uses it. Do not place all figures at the end by default.

Each figure/table needs a primary reading position. Galleries, drawers, or zoom views are secondary and do not count as coverage unless the figure/table also appears beside the relevant argument.

For large composite figures:

- keep one overview image if useful
- split into subfigures
- explain each subfigure beside or below it
- use callouts or numbered hotspots when the visual has multiple parts
- if splitting is not feasible, place the full image in a wide image-first module and put explanation below it
- provide a real large-view mode when labels, axes, or table cells are not readable in the default module

For tables:

- place the table on one side and the explanation on the other when space allows
- if the table becomes too small in side-by-side layout, put the table above and explanation below, or split rows/groups into separate cards
- explain rows, columns, metrics, and baselines before discussing conclusions
- highlight the cells that support the current claim
- state the exact comparison: "compared with X, Y is higher/lower by Z" when the source supports it
- avoid saying "提升" or "更好" without naming the baseline, metric, direction, and limitation

## Explanation template

For every figure/table, include:

- **它是什么**: what kind of evidence this is.
- **怎么看**: axes, rows, columns, legends, metrics, units, or components.
- **相比谁**: baseline, control group, previous method, ablation, or earlier condition.
- **结论是什么**: the exact claim supported.
- **为什么重要**: how it advances the paper's argument.
- **不能推出什么**: limitation or common over-reading.
- **回到原文**: which paragraph/claim it supports.

If a figure/table has multiple panels, repeat the template at panel level or provide hotspots that reveal panel-specific explanations. A single generic caption is not enough for a complex multi-panel figure.

## Experiments

Before results, explain:

- task setup
- input/output
- what is being measured
- why the metric matters
- what a higher/lower number means
- what the baseline represents

For ablations, explain what was removed or changed and why that reveals causality.

For training/evaluation papers, distinguish:

- simulation or data generation
- training data construction
- model training/fine-tuning
- evaluation task
- observed performance improvement

Readers often confuse "the simulated world improved" with "the model improved after training"; explicitly separate them when relevant.

## Screenshots

Use source screenshots for figures, tables, UI captures, diagrams, and visual evidence. Do not screenshot long text blocks. Crop tightly enough that the reader can see the relevant evidence without opening a giant image.

If a screenshot contains multiple logical panels, crop each panel separately when the reader needs panel-level interpretation. A single giant screenshot plus one generic caption is not enough for a dense table or multi-panel figure.

## Redrawn Data Visuals

When using Image 2 or another illustration model to redraw a chart/table as a teaching visual, inherit the data semantics only:

- keep chart type, title, axis labels, units, ranges, tick labels, category order, values, and uncertainty/error bars
- discard cramped screenshot styling, arbitrary colors, shadows, and weak layout
- keep exact values in nearby HTML and in the manifest when values appear in the image
- reject attractive visuals with wrong values, swapped order, missing axes, or unreadable labels
