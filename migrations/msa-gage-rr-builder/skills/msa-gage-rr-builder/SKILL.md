---
name: msa-gage-rr-builder
description: Analyze balanced crossed variable Gauge R&R measurement studies, separating equipment, operator, interaction and part variation with reproducible JSON and HTML reports. Use for repeated numerical measurements by multiple operators; attribute agreement and calibration certification require other methods.
---

# Gauge R&R for Codex

Turn actual measurements into a transparent study report for quality engineers, technicians, laboratories and students.

## Analyze a study

Read [references/input.md](references/input.md) when mapping user data. Each operator must measure every part with the same trial count. Confirm the measurement units and the user's supplied tolerance limits; keep supplied observations unchanged. Missing measurements require the user's data, not invented replacements.

Run the bundled Python 3.10+ script from this skill folder:

```text
python scripts/analyze_msa.py study.json --output-dir study-report
```

Use an available Python executable and resolve the script relative to this installed skill. The output directory must be new. Invalid studies return exit code 2 and create no reports.

After success, read results.json and check the warnings. Report gage R&R, repeatability, reproducibility, part variation, number of distinct categories (ndc), and percent tolerance when supplied. Provide the HTML report and explain the operational implication in the user's measurement units.

Read [references/method.md](references/method.md) to interpret the model or explain calculations. The interaction is always retained; this differs from tools that pool a nonsignificant interaction. Percentage study variation is not additive. Clipped negative estimates, zero denominators and undefined ndc must remain visible.

The script supplies numerical analysis, not an automatic accept/reject decision. State the supported study and sampling assumptions. Attribute agreement, bias, linearity, confidence intervals and certification are outside this implementation. If requested, explain that boundary and discuss the appropriate next analysis.

Use [examples/balanced-study.json](examples/balanced-study.json) only for an explicitly identified demonstration. Its measurements are synthetic, never evidence about the user's equipment.
