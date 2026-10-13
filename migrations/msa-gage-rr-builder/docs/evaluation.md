# Verified evaluation: 2026-10-13

Local environment: Windows, Python 3.13.13, Codex CLI 0.162.0.
18 mathematical, input-validation and CLI tests passed. Golden ANOVA SS values 800, 12, 24, 3 reconcile to 839; variance components produce gage R&R SD 2.5, %study variation 24.6034, %tolerance 37.5 and ndc 5 for the explicitly synthetic demonstration.

An independent Codex agent followed the skill for a quality-technician request, produced actual JSON/HTML and independently verified numerical results using exact Fraction arithmetic. It found uniform underflow, destructive global centering and local-residual underflow cases. Corrections now explicitly reject all demonstrated cases before creating reports; regression tests cover each. The independent final review found no remaining material issue within its scoped inspection.

Codex's native app server skills/list discovered the copied skill in an isolated project's .agents/skills folder as enabled with repo scope. The installed script was executed successfully. Automatic language-based routing is not benchmarked; explicit instruction following and native discovery are exercised separately.

Generated HTML rendered in installed Edge at 1200px and 390px viewport widths. Desktop/mobile screenshots were visually inspected; table scrolling is intentional on mobile, and the document had no overflow or page errors.

The original upstream example's declared part count was tested and rejected. Constant studies, zero gage estimates, negative components, unsupported attribute studies, duplicated/missing measurements, JSON duplicate keys, escaped metadata and overwrite refusal are tested.

GitHub Actions runs the same mathematical/CLI checks on Windows and Ubuntu with Python 3.10 and 3.13. Consult the repository Actions page for actual run outcomes; configuration alone is not CI acceptance.

Evidence and full review chronology are retained in the control repository at reports/2026-10-13 and evidence/2026-10-13. No physical equipment, business adoption, calibration status, standards certification or plugin marketplace install is validated by these software tests.
