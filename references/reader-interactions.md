# Reader Interactions

## Base frame

Start from "章节地图 + 旁注 + 图表抽屉 + 术语弹窗", then adapt to the paper.

Recommended layout:

- top chapter map with visual landmarks
- main reading panel with source/translation/explanation blocks
- side learning panel that changes with the active paragraph
- figure/table drawer for close reading
- term popovers opened from underlined inline terms

## Interaction rules

- Every popover, drawer, bubble, and floating panel must have an obvious close state.
- Clicking "continue" should move to the next chapter/landmark, not repeat the current content.
- If chapter switching is primary, avoid making the user scroll through unrelated repeated sections.
- Keep terminology and figures close to the paragraph where they matter.
- Let users expand deeper explanations without forcing every detail into the main line.
- Preserve reading flow: the main text should still make sense if all drawers are closed.

## Visual design

Choose a style from the paper's subject and artifacts. Examples:

- pixel/game-like for virtual worlds, agents, simulation, or playful AI papers
- editorial/Apple-like for reflective essays or product-like papers
- manga/anime accents when the topic or user asks for it
- consulting-report clarity for business or experiment-heavy reports

Avoid:

- generic AI gradients, glowing blobs, and empty dashboards
- cards inside cards
- end-loaded figure galleries disconnected from the argument
- text baked into screenshots when it should be selectable HTML

## Responsive and accessibility checks

- Text must not overlap on mobile or desktop.
- Buttons need visible labels or accessible names.
- Figures need useful alt text.
- Long terms or bilingual labels must wrap cleanly.
- Side panels become bottom sheets or full-width accordions on mobile.
- Keyboard users should be able to reach chapter tabs, term triggers, and drawer close buttons.
