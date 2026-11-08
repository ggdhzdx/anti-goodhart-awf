---
name: html-ppt
description: Create, revise, and review slide presentations built with HTML for teaching, briefings, and scientific communication. Use for standalone slides or browser-playable decks that need clear narrative, diagrams, interaction, or rendered-page review.
---

# AWF HTML-PPT

Create presentation pages that make the audience's next step in understanding visible. Treat each slide as one link in a story: it has a purpose, a main point, evidence or an explanation, and a useful transition.

Use this Skill for slide-based HTML deliverables. First inspect the project's existing instructions, pages, assets, design conventions, and prior feedback. Reuse a working visual system where it fits, and keep project content in the project.

## Workflow

1. Establish the audience, presentation goal, time available, target display, expected files, and review cadence. Support both standalone HTML pages and a navigable single-page deck. When details are already clear, state sensible assumptions and proceed.
2. Map the story before drawing pages. For each page, record its teaching or decision purpose, one main point, evidence or demonstration, and connection to the surrounding pages. Start with why the problem matters when the audience needs that context.
3. Plan the page around its message. Give it a concise claim or action title; use a question at points where inquiry is part of the teaching. Choose a diagram, chart, image, or text layout that makes the relationship easier to understand. For an algorithm, optimization, screening, or decision page, apply the concrete-system semantics contract in `references/content-and-evidence.md`: identify the real candidate or object, name every actual objective and direction, distinguish formal objectives from later filters, and verify that illustrated examples satisfy the stated rule.
4. Build from reusable HTML and CSS patterns. Keep content, visual tokens, and interactive state easy to revise. Prefer local assets and self-contained output unless the user requests network-backed behavior.
5. Keep claims traceable. Cite the source near the relevant claim or in a consistently placed source area. Identify whether displayed material is a published result, a new calculation, an interpretation, or a teaching illustration. For reused media, record its source, author when known, license or use basis, modifications, and a stable identifier such as a file hash when useful.
6. Add interaction only when it improves understanding or presentation. Decide which page or viewer owns each piece of state, keep controls next to the content they change, and provide clear keyboard and pointer operation.
7. Review the rendered pages in the intended browser and at the intended display size. Inspect screenshots for clipped text, unexpected wrapping, crowded cards, overlapping diagrams, image crops, contrast, and consistency. Exercise real controls and confirm the visible state follows them.
8. When the user wants iterative review, deliver pages at the requested cadence. Record feedback as the user's request, the problem it addresses, the implementation, and the reusable lesson. Apply confirmed lessons to later pages and keep old versions recoverable when the user asks to set a page aside.
9. Deliver the HTML, any needed local assets, preview images where useful, and concise instructions for opening or presenting the result. Follow the project's declared path mapping rather than assuming a drive letter.

## Title language for scientific teaching

Write the title as the concrete object, phenomenon, relationship, or question that the learner should confront. Avoid titles that describe the lesson workflow or the assistant's reasoning, such as “先把研究对象说清楚”, “追踪一条可验证的因果链”, or “把今天的解释压缩成两句话”. Put the learner action in a subtitle, control label, or presenter note. Keep the title natural enough to read aloud in a real lecture.

## References

- Read [content-and-evidence.md](references/content-and-evidence.md) when planning a teaching narrative, explaining a scientific method, or distinguishing data from interpretation.
- Read [visual-and-interaction-review.md](references/visual-and-interaction-review.md) when building diagrams, handling responsive slide geometry, adding controls, or diagnosing a browser layout issue.
- Adapt [slide-template.html](assets/slide-template.html) when a clean standalone 16:9 slide scaffold is useful. Its colors and panel arrangement are examples, not fixed styling requirements.

## Boundaries

- HTML rendering and a polished visual establish presentation behavior. Scientific, engineering, or policy claims still need their own source and review.
- Reuse project assets only within their permitted terms, and keep their provenance with the project deliverable.
- A slide can simplify a process for teaching when the simplification is visible and the underlying source remains clear.
