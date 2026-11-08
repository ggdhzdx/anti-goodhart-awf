# Content and evidence for HTML presentations

## Story planning

Start from what the audience should be able to explain, decide, or do after the presentation. Build a sequence that earns that outcome rather than arranging pages only by topic.

For technical and scientific teaching, a useful sequence often moves through:

1. Why the problem matters in its real setting.
2. What system, people, equipment, or material take part.
3. What happens during one operating or reasoning step.
4. Where the data or structures come from and how they are checked.
5. What calculations or models do with those inputs.
6. How candidate results are compared and what evidence supports the conclusion.
7. What the result means for the larger process and what remains an open question.

This is a planning aid. Choose, combine, or reorder stages to match the audience and evidence. Give each page a specific job and a clear transition into the next page.

## One page, one main point

Before styling a page, write down:

- The page's purpose.
- Its main point in one sentence.
- The evidence, example, or action that makes the point understandable.
- What the audience should carry into the next page.

Use a direct title that tells the audience what the page establishes or what action it explains. A question is useful when the audience is meant to predict or investigate; an action statement is usually clearer for an operating procedure. Avoid replacing the actual task with abstract commentary about the presentation.

### Use concrete scientific titles

For a scientific teaching page, prefer one of these title forms:

- a concrete object and phenomenon: “18-crown-6 与 K⁺：尺寸匹配够不够？”
- a direct scientific question: “结合自由能怎样决定结合强弱？”
- a concise relationship: “多种相互作用要在同一个构象中同时成立”
- an experimental decision: “怎样设计实验来检验尺寸匹配？”

The title should sound natural when a lecturer reads it aloud. Do not use the title to announce the lesson workflow or an assistant's reasoning. Phrases such as “先把研究对象说清楚”, “追踪一条可验证的因果链”, “把今天的解释压缩成两句话”, and “最有价值的实验” describe presentation management rather than the chemistry. Move that information into the subtitle, interaction label, or presenter note.

Before accepting a title, ask:

1. Does it name the real molecule, material, measurement, phenomenon, or decision?
2. Does it state or ask one thing the learner can discuss?
3. Would it still sound natural if printed in a textbook table of contents?

## Make evidence legible

Represent information according to its source and status:

| Information | How to present it |
|---|---|
| Published or supplied fact | Keep the wording within what the cited source states. |
| Measured or computed result | Name the data source, method, conditions, and relevant units. |
| Derived value | Show the input values and the transformation needed to reproduce it. |
| Interpretation | Connect it to the evidence and label it as an interpretation. |
| Teaching example or schematic | Mark it as illustrative and keep it visually distinct from source results. |
| Unresolved item | State what is known and what evidence would settle the remaining question. |

Put a concise source beside the chart, image, number, or conclusion it supports. A shared page footer can carry full citation details, provided the audience can still associate each claim with its source. Keep source notes readable and avoid repeating the same provenance statement in several visual regions.

For scientific methods, introduce unfamiliar ideas in reader order: ordinary-language purpose, physical or process picture, mathematical method, assumptions and range of use, comparison with alternatives, then practical implementation. Include a concrete input and output so the audience can follow what a method actually did.

## Explain operations as observable actions

For an operational page, show the input, action, decision rule, and resulting file or state. Explain what the operator or program does at the step where it occurs. If a person must confirm an automated result, identify the report or visual evidence used and the exact review action.

When a quantity or total matters, show how it was formed. When a process includes branches, show the conditions and outcomes on both paths. Keep the source method distinct from any extra teaching explanation introduced to make it easier to follow.

## Ground abstract methods in the concrete system

When a page teaches an algorithm, optimization, screening rule, ranking method, or decision procedure, do not stop at generic labels such as `candidate A`, `objective 1`, `score`, or `better`. A learner should not have to infer what those placeholders mean in the current system.

Before the generic definition or formula, state the concrete-system semantics:

1. **Object or candidate** — say what one point, row, node, trajectory, design, or alternative physically represents.
2. **Inputs** — name the actual measured, computed, predicted, or supplied quantities used by the method.
3. **Objectives and directions** — give every variable, unit when applicable, whether it is minimized, maximized, constrained, or targeted, and what moving in the preferred direction means physically.
4. **Operation** — express the method first as `object + action + result`, using direct verbs such as delete, retain, rank, fit, compare, predict, or allocate.
5. **Output** — identify whether the method produces a value, model, feasible set, shortlist, ranking, next action, or final decision.
6. **Non-answers and downstream steps** — state what the method does not decide and which later rule, person, calculation, or experiment completes the workflow.

For multi-stage selection, separate formal optimization variables from post-filters, constraints, heuristics, uncertainty gates, feasibility checks, and expert review. Do not draw all criteria as axes or call them all objectives when the source method applies them sequentially.

For multi-objective and Pareto diagrams in particular:

- label axes with the real variables and preferred directions, not `objective 1` and `objective 2`;
- say what one point represents;
- use at least one concrete dominance comparison and one genuine trade-off comparison;
- mathematically verify that plotted coordinates satisfy every claimed dominance or non-dominance relationship;
- distinguish the non-dominated set from a ranked list, unique optimum, acquisition priority, or execution batch;
- mark synthetic coordinates as teaching illustrations and keep source-derived values traceable.

Use a generic toy example only when the real system would overload the learner. If so, map every toy object and variable back to the real system on the same page or the immediately following page.

### Acceptance check

A zero-background learner should be able to answer all of these after viewing the page:

- What is one candidate or data point here?
- What exact quantities are compared?
- Which direction is preferred, and why?
- What does this method remove, retain, calculate, or rank?
- What concrete output goes to the next step?
- What decision remains unresolved?

If any answer is absent, the page is not yet concrete enough even if its generic definition and formula are correct.

## Record feedback as a learning loop

Use a compact feedback record with four parts:

1. User's original request or correction.
2. The viewing, learning, or operation issue it addresses.
3. The page change that resolves it.
4. The transferable rule, with its scope stated.

Keep project-specific decisions in project records. Promote a rule into shared guidance only when it describes a reusable decision and the examples support its scope. Where multiple layouts could work, preserve the user's chosen direction as a project preference rather than presenting it as the only valid design.
