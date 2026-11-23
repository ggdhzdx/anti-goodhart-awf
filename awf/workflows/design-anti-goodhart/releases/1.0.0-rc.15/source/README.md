# Coordinated Engineering Closure (`DesignAG 1.0.0-rc.15` + `HTML-PPT 1.0.0-rc.17` + `Tutor 1.0.0-rc.28`)

Co-located verification utilities for the Inline-SVG >=18px Typography, Single-Slide Density Budget & Beyond-PDF 4-Rung Background Synthesis upgrade layered on top of D17/D18 cryptographic evidence hardening:

- `skill.design-anti-goodhart@1.0.0-rc.15` (`workflow.design-anti-goodhart@1.0.0-rc.15`): Extends `design_viewport_and_redundancy.py` and Gate `D6` with `audit_inline_svg_typography_and_char_budget` enforcing `MIN_INLINE_SVG_FONT_PX = 18.0` (blocking `<18px` SVG text, missing `font-size` 16px fallbacks, and `viewBox` downscaling spoofs), `MAX_VISIBLE_CHARS_PER_SLIDE = 650`, `MAX_INLINE_SVG_SUBSTANTIVE_LABELS = 22` / `MAX_INLINE_SVG_TOTAL_TEXT_NODES = 30`, and dense-SVG + verbose-body-card crowding prevention.
- `skill.html-ppt@1.0.0-rc.17` (`workflow.html-ppt@1.0.0-rc.14`): Pins `skill.design-anti-goodhart@1.0.0-rc.15` across `audit_single_slide_step` and `assemble_verified_deck`, and expands `--self-test` to 15 checks including negative/positive canaries for `<18px` inline SVG fonts, `viewBox` spoofs, and 1,222-char / 37-label single-slide overloads.
- `skill.adaptive-interactive-tutor@1.0.0-rc.28` (`workflow.adaptive-interactive-tutor@1.0.0-rc.28`): Updates locked delegation closure to `skill.design-anti-goodhart@1.0.0-rc.15` and `skill.html-ppt@1.0.0-rc.17`.
