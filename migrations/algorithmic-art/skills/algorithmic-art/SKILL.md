---
name: algorithmic-art
description: Create original generative artwork in code with reproducible seeds and interactive parameter exploration. Use for algorithmic art, flow fields, particle systems, or p5.js sketches; use a site workflow for general websites and an image workflow for raster-only requests.
license: Complete terms in LICENSE.txt
---

<!-- Adapted for Codex on 2026-10-13 from anthropics/skills. Copyright 2026 Anthropic, PBC. Apache-2.0; retain LICENSE.txt. -->

Create a concise artistic concept and a working browser artifact. Follow the user's subject, palette, format, and constraints; choose the mathematical process around that brief.

## Design the process

Describe the visual idea and how seeds, noise, movement, or geometric rules express it. Keep this proportionate to the request; a long manifesto is optional.

Define a small set of meaningful parameters with documented defaults and ranges. State what should be reproducible: for animation, compare the same seed and parameter values at the same frame count, canvas size, and library version.

## Build the artifact

Read [the viewer template](templates/viewer.html) for seed and control structure and [the generator reference](templates/generator_template.js) for seeded p5.js organization. These are starting templates with unfinished algorithm sections, not working artworks.

- Adapt layout, branding, fonts, and palette to the user's brief. The inherited template's fixed-brand comments do not override these instructions.
- Implement every unfinished algorithm and event handler before delivering the generated artifact.
- Seed both random and noise generators before initialization. Keep unseeded randomness out of the artwork's deterministic path; a Random Seed button may choose a new displayed seed.
- Provide seed input, previous/next, regenerate, parameter controls, and reset where useful. Validate numeric inputs and finite ranges; reset must restore arrays and nested settings without aliasing.
- Preserve aspect ratio, include accessible labels, and bound expensive simulation work.
- Default to one HTML file with inline artwork logic. p5.js loaded from a pinned CDN is an external dependency, not an offline self-contained file. The inherited reference pins p5.js 1.7.0; check compatibility before changing it.
- Make library-load failures visible. If offline operation is required, review and supply a licensed local dependency or propose native Canvas; explain any scope change.
- Add image/config export when requested. Capture seed, parameters, frame count, canvas size, and library version needed to recreate exported output.

## Verify and deliver

Use the available browser tools against an allowed local preview if possible. Exercise same-seed regeneration, a changed seed, parameter changes, reset, invalid input, and missing-dependency behavior. Capture actual observed results. If browser execution is unavailable, state the limit and perform applicable syntax and structural checks without claiming visual acceptance.

Save the concept and artifact in the requested output folder. Link to the real files and explain controls, dependency requirements, and verification limits. Use Codex's file/browser handoff tools when available; do not claim a Claude artifact surface or automatically publish a site.

For an unrelated request, follow the appropriate workflow rather than forcing an art artifact. Ask only when a missing preference materially changes the result. Create original compositions and avoid presenting source templates or untested output as finished work.
