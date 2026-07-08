# Reader Interactions

## Base frame

Start from "章节地图 + 旁注 + 图表抽屉 + 术语弹窗", then adapt to the paper.

Recommended layout:

- top chapter map with visual landmarks
- main reading panel with source/translation/explanation blocks; layout can be parallel, stacked, interleaved, figure-led, or facsimile-plus-HTML depending on the section
- side learning panel that changes with the active paragraph
- figure/table drawer for close reading
- term popovers opened from underlined inline terms inside the original paragraph, translation, or explanation
- language mode segmented control for non-Chinese sources

## Interaction rules

- Every popover, drawer, bubble, and floating panel must have an obvious close state.
- Clicking "continue" should move to the next chapter/landmark, not repeat the current content.
- If chapter switching is primary, avoid making the user scroll through unrelated repeated sections.
- Keep terminology and figures close to the paragraph where they matter.
- Terms must be anchored to the exact words they explain. Do not rely on detached tag strips or glossary chips as the only interaction.
- Each paragraph should have a stable anchor so side notes, figure drawers, and popovers can point back to the source sentence.
- Each reading block should expose a stable `data-source-id` that matches the manifest.
- Side panels should track the active paragraph and expose "回到原文" or equivalent anchors for notes, figures, and claims.
- Use semantic highlight colors consistently, for example: method terms, evidence, limitations, and definitions should not share arbitrary colors.
- Let users expand deeper explanations without forcing every detail into the main line.
- Preserve reading flow: the main text should still make sense if all drawers are closed.
- Do not make the reader open an appendix or raw extraction panel to access the paper's real text.
- Do not make a chapter map that only jumps to repeated summaries. Chapter switching should reveal that chapter's original/translation/explanation blocks.
- For layout-sensitive original text, let the reader toggle between `排版截图` and `可选文字`, but keep both tied to the same `data-source-id`.
- Add review actions when useful: "测一下这章", "用自己的话解释", "看概念图", or "回到证据".
- A knowledge map, quiz, or Feynman card must link back to the paragraph/figure that taught the concept; otherwise it becomes disconnected decoration.
- Language mode must be a real stateful interaction. It should update visible layers without losing the active chapter, active paragraph, synchronized side note, or open drawer context.
- Do not leave `href="#"`, unlabeled icon controls, repeated "查看详情", or placeholder buttons in the final page.

## Interaction inventory

Before final delivery, record and test each meaningful interaction:

- trigger: exact button/link/inline term/table cell
- state change: what becomes visible, hidden, active, or selected
- close method: close button, Escape, outside click, back action, or return link
- source linkage: `source_id`, `figure_id`, `claim_id`, or chapter id
- feedback: quiz answer, visualizer state, active tab, or highlighted evidence

Delete interactions that cannot pass this inventory. A static card is better than a fake button.

## Visual design

Choose a style from the paper's subject and artifacts. Examples:

- pixel/game-like for virtual worlds, agents, simulation, or playful AI papers
- editorial/Apple-like for reflective essays or product-like papers
- manga/anime accents when the topic or user asks for it
- consulting-report clarity for business or experiment-heavy reports
- lab-notebook clarity for method-heavy scientific papers
- product-reader clarity for study apps, textbooks, or learning tools

Avoid:

- generic AI gradients, glowing blobs, and empty dashboards
- cards inside cards
- end-loaded figure galleries disconnected from the argument
- text baked into screenshots when it should be selectable HTML
- detached "related terms" rows that force the reader to guess which sentence the term belongs to
- a term popover triggered only from a glossary chip when the term appears unclickable in the paragraph
- visible internal workflow labels such as manifest, preflight, regression, generated asset, reader level, or target audience notes

## Responsive and accessibility checks

- Text must not overlap on mobile or desktop.
- Buttons need visible labels or accessible names.
- Figures need useful alt text.
- Long terms or bilingual labels must wrap cleanly.
- Side panels become bottom sheets or full-width accordions on mobile.
- Keyboard users should be able to reach chapter tabs, term triggers, and drawer close buttons.
