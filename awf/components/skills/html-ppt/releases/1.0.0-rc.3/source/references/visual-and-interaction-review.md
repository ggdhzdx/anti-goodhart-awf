# Visual and interaction review

## Establish the visual system

Choose the output shape and target screen before detailed layout. For a standard presentation, 16:9 is a practical default; follow an existing project canvas or a user's explicit format when provided. Define a small set of colors, typography, spacing, borders, and diagram styles, then reuse those choices consistently.

Give each page a clear reading order:

1. Page role or section, when useful.
2. Main claim or action.
3. The diagram, data, image, or example that carries the explanation.
4. Concise source and context notes.

Use text size, weight, spacing, alignment, and grouping to show importance. Color can reinforce meaning, while labels, line styles, or shapes keep the page understandable without color alone.

## Keep layout within its real bounds

- Use layout primitives that can shrink: CSS Grid columns such as `minmax(0, 1fr)` and `min-width: 0` on nested items.
- Allow long labels and English terms to wrap intentionally with `overflow-wrap` or an equivalent rule.
- Keep a number with its unit together when splitting them would change how the value is read.
- Check text against the actual target resolution and installed fonts; character counts and DOM dimensions alone do not reveal visual crowding.
- Crop images only when the crop preserves the device, object, or relationship being explained. Record the source for photographs and adapted graphics.

## Draw process diagrams as paths

For every flow line, verify its start point, destination, direction, equipment port, and whether it crosses another line. Give different streams distinct attachment points where their meaning differs. Reroute lines to avoid crossings; if a crossing is necessary, make the bridge or gap visually explicit.

For SVG arrows, keep marker size independent of stroke width when line widths vary. `markerUnits="userSpaceOnUse"` is a reliable default for a consistent arrowhead size. Leave visible line before the arrowhead and end the arrow at the intended boundary. Review the complete path at presentation size so arrowheads do not appear detached, doubled, or merged with a device outline.

For a process explanation, show material flow, energy input, operating stages, and recycle paths when they affect the mechanism. Pair a real installation image with an original simplified diagram when the audience needs both scale and process logic. Label what the source confirms and what the diagram simplifies.

## Place controls with the state they change

Give each interaction one clear owner. A host page can own teaching order and explanatory notes; an embedded scientific viewer can own camera, element display, or geometry controls. Keep a control inside the rendering context when it changes viewer state, and synchronize other page information through a single documented event or interface.

For modal or full-screen viewers, preserve the same rendering instance when state continuity matters. Inspect how parent stacking contexts and backdrops affect pointer input. Test the visible hit target at screen coordinates and operate it with a real pointer event; access through a frame locator alone only proves that the control exists.

Provide visible focus, descriptive button labels, keyboard operation, and a clear way to close overlays. Preserve useful state when opening and closing a larger view. If the host and viewer both display a sequence, define one playback owner and use events to update the other display.

## Browser review checklist

Review at the intended browser, zoom, aspect ratio, and screen resolution. For each page, inspect:

- Text clipping, line breaks, font substitution, and units separated from values.
- Card edges, margins, image crop, and alignment with neighboring pages.
- Diagram paths, arrow direction, connector endpoints, crossings, and occlusion.
- Contrast, text hierarchy, labels, and the distinction between source results and illustrations.
- Keyboard focus and operation, button hit targets, modal open/close, playback state, and resizing.
- Console errors, failed local assets, and unexpected network requests.

For interactive pages, exercise the controls a presenter will actually use. Use screenshots to review appearance and browser events to review behavior; neither check replaces the other.
