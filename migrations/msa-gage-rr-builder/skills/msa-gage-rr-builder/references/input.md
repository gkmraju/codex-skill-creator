# Input contract

A JSON object contains raw_data: an array of {part_id, operator, trial, measurement_value}.
part_id and operator are nonempty strings; trial is an integer starting at 1.
Values are finite numbers in one consistent unit. At least two parts, two operators and two trials are required; every part/operator/trial combination occurs exactly once.

Optional study_design includes num_parts, num_operators and num_trials. Any declared count must match the observations. Optional gage is descriptive metadata, including units, characteristic and id; it does not establish calibration status.
Optional tolerance is exactly {"lower": -20, "upper": 20}. Both finite limits are required; upper exceeds lower, in the same measurement units. The input never infers limits from observed spread.

Nonempty attribute_study is rejected rather than silently ignored. Duplicate JSON keys and duplicate readings are rejected. Missing, unbalanced, nonfinite and extreme numerical ranges are errors.
Outputs are results.json (full ANOVA and variance results, input SHA-256) and report.html (local, escaped, no scripts or external resources).

The nonzero range relative to the first reading must be between 1e-140 and 1e140. Rescale measurement units outside that supported range; tiny variation is rejected rather than mislabeled constant.
Nonzero ANOVA residuals below 1e-140 and precision-destructive centering are also rejected explicitly. Such errors call for consistent unit rescaling or recentering before a reliable analysis.
