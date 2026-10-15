# Animation diagnosis reference

## Route by symptom

| Symptom | Inspect | Compatible response |
|---|---|---|
| Movement repeatedly triggers layout | Animated top/left/size/margins; trace Layout events | Use a translated inner element if flow and final geometry stay correct |
| Unexpected changes animate | transition: all and actual changed styles | List intended transition properties |
| Jank during navigation/work | Long tasks, animation driver and animated properties | Consider CSS/WAAPI for eligible motion; verify actual compositing rather than promise an off-thread path |
| React work each frame | setState in rAF/pointer/scroll handlers | Keep state for semantic changes; use existing animation/ref mechanism for transient visual writes, with cleanup |
| Cost grows with descendants | Inherited CSS variables and invalidated styles | Scope updates locally or use direct transforms when equivalent |
| Expensive shadows/filter/blur | Paint/raster work and layer size | Profile simpler visual alternatives; no fixed blur cutoff or guaranteed cheaper filter |
| Layer-related artifacts | Actual layer/raster evidence | Try bounded will-change only when justified; remove it after transient use |

## Non-obvious constraints

Transform and opacity often avoid layout, but acceleration is not guaranteed. Filter, clip-path and color are not universally composite-only. CSS or WAAPI still incur layout if they animate layout properties.

Transform movement does not move siblings in document flow. Scale changes rendered content rather than layout dimensions. New transforms affect stacking contexts and containing blocks. Opacity zero does not hide content from keyboard focus or hit-testing. Preserve semantic hiding and pointer/focus behavior with the existing component's lifecycle.

Reduced-motion users should retain final state and functionality without unnecessary motion. Use the existing application preference handling or an appropriate CSS media query. Avoid globally disabling functionality or changing user intent.

At 60Hz a refresh interval is about16.7ms; at120Hz about8.3ms. Actual budget is shared with other browser work. Do not infer FPS, device smoothness or universal speedup from a style change.

## Verification

Compare the same reproduction before/after: final position and dimensions, state, click/keyboard activation, focus and reduced-motion behavior. A browser trace can expose Layout/Paint/long tasks; report observed events and environment, not invented frame-rate claims. Test available target browsers; clearly separate desktop/headless observations from real-device results.

Report each finding as location, suspected/measured mechanism, change and verification boundary. When browser access is absent, give an executable reproduction/trace plan and mark performance measurement pending.

Primary references consulted for the adaptation:
- [Browser rendering and animation performance](https://web.dev/articles/animations-guide)
- [Reduced-motion media preference](https://developer.mozilla.org/en-US/docs/Web/CSS/@media/prefers-reduced-motion)

These are links for further reading, not copied manuals or bundled third-party code.
