# Retained-interaction crossed random-effects model

Let p = parts, o = operators, r = repetitions. Compute grand, part, operator and cell means.

- SS(part) = o r sum((part mean - grand mean)^2), df = p - 1.
- SS(operator) = p r sum((operator mean - grand mean)^2), df = o - 1.
- SS(interaction) = r sum((cell mean - part mean - operator mean + grand mean)^2), df = (p - 1)(o - 1).
- SS(error) = sum((reading - cell mean)^2), df = p o (r - 1).
- MS = SS / df. Check that the four sums reconcile to total SS.

Variance estimates: repeatability = MS(error); operator = (MS(operator) - MS(interaction)) / (p r); interaction = (MS(interaction) - MS(error)) / r; part = (MS(part) - MS(interaction)) / (o r).
Retain raw estimates and clip negative component estimates to zero with warnings.
Reproducibility = operator + interaction. Gage R&R = repeatability + reproducibility.
Total = gage R&R + part.

Standard deviation = sqrt(variance); study variation = 6 SD.
% contribution = 100 variance / total variance.
% study variation = 100 SD / total SD; these percentages are not additive.
% tolerance = 100 (6 SD) / (upper - lower), only when both limits are supplied.
ndc = max(1, floor(1.41 part SD / gage R&R SD)). A zero denominator returns null with a warning, never an infinite capability claim. Constant studies have undefined percentages.

No significance test, interaction pooling, confidence bound or suitability threshold is implemented. Small designs establish computability, not study adequacy. The study owner reviews representative part selection, random operator effects, independent measurement errors, stable conditions and randomized order. Supplied calibration metadata is not verified.

Primary methodology consulted 2026-10-13:
- [Minitab variance components, study variation and tolerance](https://support.minitab.com/en-us/minitab/help-and-how-to/quality-and-process-improvement/measurement-system-analysis/how-to/gage-study/crossed-gage-r-r-study/methods-and-formulas/gage-r-r-table/)
- [Minitab number of distinct categories](https://support.minitab.com/en-us/minitab/help-and-how-to/quality-and-process-improvement/measurement-system-analysis/supporting-topics/gage-r-r-and-wheeler-s-emp-studies/using-the-number-of-distinct-categories-in-a-gage-r-r-study/)
- [NIST gauge study context](https://www.itl.nist.gov/div898/handbook/mpc/section4/mpc4.htm)

These references support the model; no standards conformance, Minitab default-model equivalence or certification is claimed.
