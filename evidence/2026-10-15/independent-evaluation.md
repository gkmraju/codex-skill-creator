# Independent forward evaluation: animation-performance

Result: PASS for the supplied interactive-card fixture. This is a demonstration, not a benchmark of a user application. Read only the supplied skill, diagnosis reference and before fixture; did not consult any paired after example or previous forward-test output. All generated files are confined to this evaluation directory.

## Diagnosis and change

`examples/before.html:7` uses `transition:all 220ms ease-out`; line 8 changes `left` from 0 to 240px. Animating left is a layout risk. The comparable browser trace below observed repeated Layout events during this fixture's movement.

In `after.html:7-9`, keep left at 0, translate from 0 to 240px, restrict the transition to transform, and retain 220ms ease-out. Add a reduced-motion media query with transition:none. Preserve markup, dimensions, padding, handlers, labels, aria-pressed and the counter. Translation preserves content geometry without scaling it. This fixture has no positioned descendants or overlapping siblings affected by the transform's containing-block/stacking-context change. It has no hidden lifecycle to repair; the visible card and action button remain focusable and clickable.

## Executed command

From `.`:

```powershell
& '$USERPROFILE/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node.exe' 'tmp/animation-eval-20261015/verify.cjs'
```

Exit code 0. The runner uses bundled Playwright and installed Edge channel `msedge`, headless, Windows, browser version 155.0.4283.45. It opens local file URLs, writes results.json and raw before/after trace JSON, and captures after.png. The first ordinary shell read failed before execution with helper_unknown_error/setup refresh had errors; the permitted escalated shell path then worked. No package installation or global change was needed.

## Observations

- Compared baseline and fixed endpoints at viewport widths 960 and 375, height 700. Both begin at x=33 and end at x=273; width=160, height=98. The y position is unchanged: 198.109375 at 960 and 252.109375 at 375. Return movement restores the exact initial rectangle. The original narrow-viewport overflow is preserved.
- Tab order is Move card, Count action. Enter toggles the moved state and aria-pressed. Enter and Space increment the counter. Focus remains on the action button when movement is triggered, and Enter still activates it during the transition.
- Pointer activation succeeds at both endpoints and at an intermediate position. For deterministic intermediate hit testing, the transition is paused at 110ms, its x lies strictly between endpoints, and Playwright clicks the action button there. This tests transformed hit testing; it does not simulate tracking a physically moving target.
- Reduced-motion emulation reports transition duration 0s and no active animation. A synchronous state toggle changes x from 33 to 273 immediately, keeps aria-pressed true, and the action button still works.
- Comparable devtools.timeline traces: eight toggles, 280ms between each, 960x700 viewport, after a 300ms initial settle. Before: Layout=110, UpdateLayoutTree=118, Paint=220. After: Layout=0, UpdateLayoutTree=43, Paint=0. Counts include complete-duration events only and refer to this recorded browser run. CompositeLayers was not emitted in either trace; this supplies no compositing or GPU conclusion.
- Visually inspected after.png for card content, placement and controls.

## Limits and skill feedback

No FPS, real-phone performance, universal smoothness, or GPU acceleration claim is established. No real device, other browser engine or assistive-technology session was tested. The source fixture had no reduced-motion handling; the fix adds preference support while retaining functionality and final state.

The skill and its local reference were sufficient to find and verify a narrowly scoped fix. No material skill or installer issue was encountered. Optional browser-tool availability did not block ordinary local Playwright verification. No credentials, publication, registry, installed skill or upstream source were changed.

## Additional independent negative scenario: audit only, no browser trace

Request: Audit this component only; do not edit any source. I cannot supply a browser trace right now. Tell me what is supported by source inspection and what still needs measurement.

Read the original examples/before.html as numbered source; reused the already-read skill/reference instructions. Did not invoke browser tools or run browser scripts for this case. Wrote only audit-only.md and this evaluation append in the isolated evaluation directory.

Input SHA256 before: 3307535E89A7FFE2B8882F1CD663096083ED5AF1FDBABF85272959DA96BFBFC5

Input SHA256 after: 3307535E89A7FFE2B8882F1CD663096083ED5AF1FDBABF85272959DA96BFBFC5

Observed outcome: Input hashes match. The audit identifies left/transition:all and missing reduced-motion handling from source, describes native buttons and handlers without claiming behavioral validation, proposes a correction without applying it, and explicitly leaves layout-event counts, FPS, compositing and device smoothness unmeasured. It provides a future measurement/behavior verification plan. The audit does not carry earlier browser results into this case. Source no-edit and measurement boundaries were respected. No skill or registry files were written.
