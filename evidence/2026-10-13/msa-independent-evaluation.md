# Independent forward evaluation

Date: 2026-10-13. Scope: supplied demonstration only, isolated CLI fixtures and independent analyzer inspection. No registry, skill, installed source, credential, publication or messaging files changed.

## Realistic task and outcome

Request: Use this Gauge R&R skill to analyze the supplied demonstration study for a quality technician. Produce the actual report and explain whether measurements alone establish calibration certification.

Applied the bundled skill instructions and references/input.md and references/method.md. The demonstration explicitly identifies synthetic data, gage DEMO-01, dimension in mm, 3 parts, 2 operators, 2 trials (12 observations), and supplied tolerance -20 to +20 mm. No replacement observations or inferred tolerances were used.

The documented CLI succeeded (exit 0):

```powershell
python migrations/msa-gage-rr-builder/skills/msa-gage-rr-builder/scripts/analyze_msa.py migrations/msa-gage-rr-builder/skills/msa-gage-rr-builder/examples/balanced-study.json --output-dir tmp/grr-forward-eval/demo-report
```

Observed stdout: `Validated study; wrote results.json and report.html`.

Actual artifacts: demo-report/results.json and demo-report/report.html. Input SHA-256 recorded in results: 73bfd3fa83d1a8d08a8d3f407e0e5415cef9037bd30bd38ef3d7afa8ed39f94f. Independently recomputed from the original bytes and matched.

## Technician explanation

These are synthetic demonstration measurements, not evidence about the user's equipment.

| Source | SD (mm) | Six-SD study variation (mm) | % study variation | % tolerance |
|---|---:|---:|---:|---:|
| Repeatability | 0.707107 | 4.24264 | 6.95889 | 10.6066 |
| Reproducibility | 2.39792 | 14.3875 | 23.5987 | 35.9687 |
| Total Gauge R&R | 2.5 | 15 | 24.6034 | 37.5 |
| Part variation | 9.84886 | 59.0931 | 96.9261 | 147.733 |

Distinct categories (ndc) = 5. Warnings = empty for this demonstration. The operator component estimate is zero and interaction variance is 5.75 mm squared; reproducibility here arises from differences in the operator effect across parts. For example, operators differ by 6 mm on P1 and by 0 mm on P2 and P3. Zero estimated overall operator variance does not establish operator equivalence.

Gauge R&R contributes 6.05327% of total estimated variance, while its 24.6034% study variation is a standard-deviation ratio. The study percentages are not additive. Measurement-system six-SD spread is 15 mm versus supplied tolerance width 40 mm. No automatic suitability decision follows: the process owner must assess requirements, representative part sampling, independent repetitions, stable conditions, randomized order and random-effects assumptions. This tiny synthetic design establishes an executable calculation, not real process adequacy.

Measurements alone in this study do not establish calibration certification. The input supplies no verified reference standard, traceability, calibration procedure, uncertainty assessment or certification evidence. The analyzer measures repeatability and reproducibility and explicitly excludes calibration certification, bias and linearity. The metadata field is descriptive and unverified.

## Independent numerical and input review

Command:

```powershell
python tmp/grr-forward-eval/check.py
```

Observed exit 0. The independent check uses exact Fraction arithmetic on the source observations rather than importing the analyzer implementation. ANOVA SS matches exactly: part=800, operator=12, interaction=24, error=3; total=839. Raw variance estimates match exactly: repeatability=1/2, operator=0, interaction=23/4, part=97. The independent formulas retain interaction, matching the stated model.

check.py captures the exact subprocess argument arrays, exit codes, stdout, stderr and returned JSON in checks.json. Isolated fixtures produced:

- missing-reading: exit 2, balanced/crossed error, no output directory.
- duplicate-reading: exit 2, duplicate measurement error, no output directory.
- attribute-study: exit 2, unsupported attribute error, no output directory.
- constant-study: exit 0 with undefined ndc and % study variation, explicit warnings.
- tiny-scale-study: exit 0, incorrect zero-variation results as detailed below.

Also read the analyzer implementation and generated HTML source. HTML contains escaped owner metadata, no external resources or scripts, and explicit interpretation boundaries. Browser rendering and accessibility acceptance were not performed in this pass.

## Demonstrated defect

Numerical underflow is accepted as a valid constant study. Reproducer in check.py scales every demonstration measurement and tolerance limit by 1e-170, preserving the nonconstant crossed study and all dimensionless ratios. The analyzer returns exit 0 but all squared deviations underflow to zero. It reports Gauge R&R SD=0, % tolerance=0, undefined % study variation and ndc, and the false warning `All observations are constant; percentage variation is undefined`.

The original study has Gauge R&R % tolerance=37.5 and ndc=5; uniform scaling should preserve those quantities. This is a concrete numerical-boundary defect, not an issue affecting the supplied mm-scale demonstration. The input documentation promises extreme numerical ranges are errors, but no lower-scale guard or stable scaled computation enforces that promise. Recommended correction: scale intermediate ANOVA calculations safely or reject underflow-prone measurement ranges with exit 2 before creating reports. No skill edits were made.

## Decision and limits

Forward realistic demonstration workflow passes: raw measurements preserved, correct independently checked numerical report produced, boundaries and operational interpretation explainable. Invalid-input examples pass. Numerical extreme-input acceptance has the demonstrated defect above, so unconditional numerical/input acceptance is not recommended until corrected and verified. This pass does not claim installation, physical equipment validity, CI success, public release, or calibration certification.

## Execution notes

Initial project and skill reads used Get-Content on STATUS.md, README.md, SKILL.md, references/input.md, references/method.md, examples/balanced-study.json and scripts/analyze_msa.py. The skill-creator SKILL.md was read for independent forward-testing guidance. All shell calls used explicit reviewed require_escalated execution as directed because the workspace sandbox helper fails. apply_patch could not write the isolated check.py; writing the exact file with a literal PowerShell here-string and Set-Content succeeded. This was a tool failure, not an analyzer failure. The shell fixture invocation completed normally.

## Retest after first correction

The parent changed the analyzer to reject nonzero centered spreads below 1e-140. Independently reran:

```powershell
python -B migrations/msa-gage-rr-builder/skills/msa-gage-rr-builder/scripts/analyze_msa.py tmp/grr-forward-eval/tiny-scale-study.json --output-dir tmp/grr-forward-eval/tiny-scale-retest
```

Observed stderr: `ERROR: Measurement range below supported numerical scale; rescale units`. No tiny-scale-retest directory was created. This resolves the original uniform-scaling reproducer.

A further independently constructed mixed-scale study exposed centering precision loss: all P1 readings -10, all P3 readings +10, both P2 operators' trials -1e-100 and +1e-100. The raw measurements are distinct, and repeatability variance from these raw cell deviations is 4*(1e-100)^2/6 = 6.666666666666667e-201, representable as a Python float. The analyzer instead returns exit 0 and reports zero repeatability and Gauge R&R, because subtracting the global origin (-10) loses the small P2 differences before cell means are calculated. The zero-R&R warning does not disclose that known nonzero variation was lost.

Reproducer command: `python -B tmp/grr-forward-eval/mixed-scale-check.py`. Exact analyzer subprocess command, return code, stdout, stderr and independent expected variance are preserved in mixed-scale-check.json. Input is mixed-scale-representable.json and actual output is mixed-scale-representable/results.json. Also tested ±1e-170 with the same centering failure, but ±1e-100 is the stronger case because its variance is representable.

Parent was informed. Recommended correction: compute within-cell differences using local origins, or reject detected precision-destructive centering before creating reports. This remains an observed unresolved numerical boundary issue at this checkpoint; demonstration arithmetic remains unaffected. All retest commands use -B and do not import the analyzer or create bytecode in the artifact.

## Second correction verification and residual lower-scale case

Parent added a distinct raw/centered value collision guard. `python -B tmp/grr-forward-eval/final-retest.py` succeeded. final-retest.json records: uniform tiny study rejected exit 2; both original mixed cases rejected exit 2 with `Centering loses distinct measurements; rescale or recenter input units`; no failed-case output directories. The supplied demonstration reran exit 0 with its results.json identical to the original.

A final lower-scale fixture reorders mixed-scale-study so P2's ±1e-170 readings come first. This preserves their distinct centered values, but the global spread remains 10 and bypasses the global lower-scale guard. Their nonzero within-cell error squares still underflow and the CLI returns exit 0 with zero repeatability and R&R. Command/log: mixed-local-underflow-check.py and mixed-local-underflow-check.json; raw input: mixed-local-underflow.json. Parent informed. Explicit rejection of a nonzero tiny within-cell residual/range, before squaring, would close this demonstrated residual case. No other material runtime/input/model issue was found in this scoped inspection. Final outcome remains pending this residual correction.

## Final independent disposition

Parent added a guarded square operation for every nonzero ANOVA residual. Independently ran `python -B tmp/grr-forward-eval/acceptance-retest.py` against the current analyzer. The reordered mixed-local-underflow reproducer now returns exit 2 with `ERROR: Nonzero ANOVA residual below supported numerical scale; rescale units`, and creates no output directory. acceptance-retest.json captures the exact command, current analyzer SHA-256, stdout, stderr, exit code and output-existence check.

The original demonstration also reran successfully after the final correction; its complete results.json remains identical to the original independently checked output. Final deliverables are demo-final-accepted/report.html and demo-final-accepted/results.json. The original report and defect outputs are intentionally preserved as historical evidence of observed behavior; they are superseded for final acceptance by the retests.

Decision: scoped independent forward evaluation passes for the stated balanced crossed demonstration workflow and explicit unsupported/calibration boundaries. All numerical defects demonstrated in this pass are now rejected with explicit exit-2 errors before reports are created. No unresolved material issue was found in the remaining inspected code. This is a bounded behavioral evaluation, not proof of all numerical cases or real-equipment suitability. Browser visual acceptance, installation, CI and publication remain outside this independent pass. No test-suite or CI result is inferred from the parent's reported results.

