# Compatibility

SKILL.md and Markdown reference are independent of Claude-specific tools or sibling skills. Native Codex project installation uses the whole skills/animation-performance folder under .agents/skills; the optional installer uses Python3.10+ standard library and refuses existing installations or linked paths.

The installed skill can diagnose from source without browser tools. Browser profiling uses tools available in the user's environment and must disclose that boundary. Optional developer verification uses Playwright; it is not a runtime requirement for using the skill. The compatibility plugin manifest is structurally checked; plugin marketplace installation is not claimed.
