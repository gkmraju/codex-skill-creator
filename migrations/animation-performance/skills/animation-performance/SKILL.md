---
name: animation-performance
description: Diagnose and fix web animation jank in CSS, JavaScript and React while preserving interaction and reduced-motion behavior. Use for stutters, expensive animated properties, busy-main-thread motion or per-frame rendering; distinguish code findings from measured browser/device performance.
---

# Animation performance for Codex

Find the cause of costly motion and make the smallest compatible change. Act on the user's supplied question or code immediately. If no target is supplied, request the component, reproduction or recording needed for diagnosis.

## Diagnose and act

Inspect the affected component, styles and animation driver. Search only its relevant code path for transitions/keyframes, requestAnimationFrame loops, per-frame state updates and CSS variables. Identify animated properties and whether the change affects layout, paint or interaction.

Read [references/diagnosis.md](references/diagnosis.md) for the matching symptom and validation choices. Prefer transform/opacity where they preserve the intended geometry, layout and interaction. Keep existing timing/design choices unless the task needs them changed.

Explain the suspected mechanism with file/line evidence. When the user asks for a fix, apply it; for an audit, provide findings without silently changing code. Avoid replacing libraries or redesigning the UI to solve one animation.

## Verify the result

Run existing relevant checks. With an available browser, reproduce the behavior, inspect computed styles and record a comparable performance trace where useful. Check final geometry, click/keyboard behavior, focus, hidden-state semantics and prefers-reduced-motion. A transform can change stacking/positioning, opacity leaves elements interactive, and scaling dimensions can distort content; preserve these semantics explicitly.

Report what changed, why, what was actually exercised, and what still needs a device recording. Static code inspection identifies risks; it does not establish frame rate, GPU acceleration or smoothness. A desktop/headless trace is not a real-phone benchmark.

Use [examples/before.html](examples/before.html) for an explicitly labeled demonstration of an interactive layout-property animation. Its paired after example, when supplied, illustrates the tested correction; never treat demonstration results as measurements of the user's app.

This skill is self-contained. Browser tools are optional; use those available in the user's environment and state measurement limits when unavailable.
