# Codex Gauge R&R skill

A working measurement-system analyzer for quality engineers, technicians, manufacturers, laboratories and students. Converts balanced crossed repeated measurements into populated JSON and accessible HTML, using Python's standard library. No API account or spreadsheet application is required.

## Install in a Codex project

Clone this repository, then copy skills/msa-gage-rr-builder into your project's .agents/skills/ folder. Keep the entire skill folder. Restart Codex if a newly installed skill is not discovered.

Invoke `$msa-gage-rr-builder` with a JSON study or ask to analyze a balanced crossed Gauge R&R study. See [the input contract](skills/msa-gage-rr-builder/references/input.md).

## Try the included demonstration

```text
python skills/msa-gage-rr-builder/scripts/analyze_msa.py skills/msa-gage-rr-builder/examples/balanced-study.json --output-dir sample-report
python -B -m unittest discover -s skills/msa-gage-rr-builder/tests -v
```

The output directory must be new. The example is synthetic; it is not a real equipment qualification.

Supported: balanced crossed variable studies, retained interaction, ANOVA, nonnegative variance components, percentage variation, ndc and optional two-sided tolerance.
Not implemented: nested/unbalanced studies, attribute agreement, bias, linearity, interaction pooling, significance tests, confidence intervals, XLSX generation or automatic acceptance.

Adapted from a Claude skill in Jherrod Thomas's automotive skills suite; [upstream attribution](UPSTREAM.md), [migration changes](docs/migration.md), [compatibility](docs/compatibility.md), [evaluation](docs/evaluation.md).
Installation follows [official Codex skill guidance](https://learn.chatgpt.com/docs/build-skills). The compatibility plugin manifest is included; plugin marketplace installation is not claimed.
