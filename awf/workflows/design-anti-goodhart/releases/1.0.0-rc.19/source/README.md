# Coordinated Engineering Source: DesignAG `1.0.0-rc.19` + HTML-PPT `1.0.0-rc.21` (`wf 1.0.0-rc.18`) + Tutor `1.0.0-rc.32`

Physical co-location directory for the Intra-Slide Semantic Coherence, Bottom-Ballast De-Incentivization, Bare-Noun Card Header Rejection & Anti-Collusion Zero-Context Blind Reader release closure:
- `skill.design-anti-goodhart@1.0.0-rc.19` (`workflow.design-anti-goodhart@1.0.0-rc.19`)
- `skill.html-ppt@1.0.0-rc.21` (`workflow.html-ppt@1.0.0-rc.18`)
- `skill.adaptive-interactive-tutor@1.0.0-rc.32` (`workflow.adaptive-interactive-tutor@1.0.0-rc.32`)

## Key Additions Over `1.0.0-rc.18` / `1.0.0-rc.20` / `1.0.0-rc.31`
1. **Bare Verbless Noun-Label Card Strip & Mini-Glossary Rejection (`D3` & `D4`)**: Blocks multi-card strips whose card headings are bare dictionary noun phrases (e.g. `电子密度 Q 峰`, `热振动椭球 ADP`, `精修残差因子 R1`), requiring causal/action predicates or explicit step-callout anchors and contextual in-place definitions.
2. **Unanchored Bottom Ballast Strip & Deck-Wide Bottom-Grid Cloning Guards (`D6` & `D8`)**: Blocks bolting unanchored 3+ short-card strips beneath a top visual (`audit_html_orphan_bottom_strip_and_noun_cards` + `audit_boxes_for_bottom_ballast_strip`), promotes single-tier full-height visuals (`740–820px`), and caps `top-visual + bottom-grid` slides at `<= 30%` of the deck.
3. **Pre-Generation Intra-Slide Semantic Tree Contract (`D16`)**: Enforces `verify_intra_slide_semantic_trees` (`core_claim`, `primary_visual_spine`, and `secondary_blocks` with `parent_anchor_target`, `relation_type`, and `on_canvas_bridge_marker`, forbidding `GLOSSARY_STRIP` / `SUPPLEMENTARY_TRIVIA`).
4. **Anti-Collusion Zero-Context Blind Reader Reconstruction (`D18` + `--verify-blind-reader`)**: Blocks prompt coaching/pleading, answer-leakage from `intra_slide_semantic_tree`, context contamination (`saw_source_pdf == False`), canvas reviewer-bribery tokens, and rubber-stamp `"PASS"` replies—requiring concrete blind claim & bridge reconstruction with zero `ambiguous_or_dangling_elements`.
