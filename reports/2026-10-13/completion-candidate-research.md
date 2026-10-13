# Completion candidate research — 13 October 2026

## Recommended candidate: Measurement System Analysis Gauge R&R

Select **msa-gage-rr-builder** from [jherrodthomas/automotive-skills-suite](https://github.com/jherrodthomas/automotive-skills-suite). This is a real Claude skill, not a newly packaged prompt: the [source .skill archive](https://github.com/jherrodthomas/automotive-skills-suite/blob/96afe776dd79d5bdb61b1a266894baffeb0581e8/skills/msa-gage-rr-builder.skill) contains `msa-gage-rr-builder/SKILL.md`, an example JSON, generator, recalculation helper, and LibreOffice wrapper.

Live GitHub API observation: **3,182 repository stars**, default branch `main`, latest revision **96afe776dd79d5bdb61b1a266894baffeb0581e8**, pushed **2026-10-13 11:09:22 UTC**. Stars apply to the collection, not the individual skill. [Repository metadata](https://api.github.com/repos/jherrodthomas/automotive-skills-suite), [revision metadata](https://api.github.com/repos/jherrodthomas/automotive-skills-suite/commits/96afe776dd79d5bdb61b1a266894baffeb0581e8).

The [MIT license](https://github.com/jherrodthomas/automotive-skills-suite/blob/96afe776dd79d5bdb61b1a266894baffeb0581e8/LICENSE) identifies Copyright (c) 2026 Jherrod Thomas and requires preserving its notice. Preserve this exact notice and source revision in the selected standalone public repository.

### Audience and impact

Quality engineers, manufacturers, calibration laboratories, technicians, and students need to distinguish measurement noise from real differences between parts. The underlying measurement problem spans manufacturing, not only automotive: [Minitab's first-party methodology](https://support.minitab.com/en-us/minitab/help-and-how-to/quality-and-process-improvement/measurement-system-analysis/how-to/gage-study/crossed-gage-r-r-study/methods-and-formulas/gage-r-r-table/) separates equipment, operator, interaction, and part variation. A local reproducible analyzer can turn collected measurements into transparent study results without API credentials or physical hardware during software acceptance. This is potential usefulness, not evidence of adoption or business savings.

### Actual runtime and implementation gap

The upstream [README](https://github.com/jherrodthomas/automotive-skills-suite/blob/96afe776dd79d5bdb61b1a266894baffeb0581e8/README.md) targets Claude Desktop/Cowork installation via Save skill and .skill bundles. It does not give Codex installation or a Codex runtime entry point.

Direct archive inspection found a more serious capability gap: `generate_msa.py` builds 12 formatted workbook sheets but leaves variance and acceptance results empty. The ANOVA sheet puts pseudo-formulas such as `=STDEV(Range)` into explanatory cells without defining the referenced data or named ranges. The sample declares 10 parts but supplies measurements only for 2. The SKILL.md overstates this scaffold as audit-ready and mentions unsupported attributes, bias/linearity, and unrelated SPFM/LFM metrics. A direct rename would preserve a broken promise.

A useful Codex recreation should implement and test a deliberately narrower **balanced, crossed variable Gauge R&R study**. Validate complete part × operator × trial coverage, reject duplicate/missing/nonfinite data, compute two-way random-effects ANOVA with explicitly retained interaction, nonnegative variance components, percent study variation, number of distinct categories, and optional percent tolerance. Generate accessible JSON/HTML and, if included, a populated workbook; disclose fixed-interaction modeling and the need for professional approval. Do not claim standards certification, calibration verification, uncertainty analysis, attribute agreement, bias, or linearity without implementing them.

[Minitab formulas](https://support.minitab.com/en-us/minitab/help-and-how-to/quality-and-process-improvement/measurement-system-analysis/how-to/gage-study/crossed-gage-r-r-study/methods-and-formulas/gage-r-r-table/) state that negative variance components are reported as zero and distinguish study variation from tolerance. [Minitab interpretation](https://support.minitab.com/en-us/minitab/help-and-how-to/quality-and-process-improvement/measurement-system-analysis/how-to/gage-study/crossed-gage-r-r-study/interpret-the-results/key-results/) shows that its default can drop a nonsignificant interaction; a retained-interaction implementation must disclose that difference rather than claim exact equivalence to the default. [NIST gauge study overview](https://www.itl.nist.gov/div898/handbook/mpc/section4/mpc4.htm) gives complementary primary measurement context.

### Public Codex ecosystem check

Web queries run today: `"msa-gage-rr-builder" "Codex"`, `"Gauge R&R" "Codex" skill`, `"automotive-skills-suite" "Codex"`. They found no public Codex skill implementing this selected workflow. Results for **Mech Codex** and **Clicarity Codex** are unrelated website names, not OpenAI Codex skills.

GitHub repository searches today each returned **total_count = 0**:

- [msa-gage-rr-builder codex](https://api.github.com/search/repositories?q=msa-gage-rr-builder+codex)
- [gage rr codex skill](https://api.github.com/search/repositories?q=gage+rr+codex+skill)
- [gauge rr codex skill](https://api.github.com/search/repositories?q=gauge+rr+codex+skill)
- [automotive-skills-suite codex](https://api.github.com/search/repositories?q=automotive-skills-suite+codex)

This supports **no equivalent found in these scoped checks**, not proof of universal absence. General statistics/spreadsheet skills can build similar analyses but were not found as the named operational Gauge R&R skill. Additional installed-skill and candidate-registry checks remain the main agent's responsibility.

## Other inspected candidates rejected

- **RinDig/icm-architect**, 1,892 stars, MIT, actual SKILL.md and Claude context templates: rejected after GitHub repository search found [shutori/icm-architect-codex](https://github.com/shutori/icm-architect-codex) and [adrozdenko/icm-architect-codex](https://github.com/adrozdenko/icm-architect-codex), despite weak web indexing. This demonstrates why search-engine nonresults alone are insufficient.
- **danyuchn/asd-ste100-skill**, 4,760 stars, MIT, actual SKILL.md: rejected because [clayleopardlabs/ste100-skill](https://github.com/clayleopardlabs/ste100-skill) already documents native Codex installation, controlled-dictionary references, and the same controlled technical-language purpose.
- **Cocoon-AI/architecture-diagram-generator**, 7,427 stars, MIT: rejected because [kimmandoo/architecture-diagram-generator-codex](https://github.com/kimmandoo/architecture-diagram-generator-codex) already ships a standalone Codex folder.
- **Haojae/scipilot-figure-skill**, 2,625 stars, MIT: rejected due public Codex availability plus [liouhai/plot-is-all-you-need](https://github.com/liouhai/plot-is-all-you-need), which explicitly documents Codex installation and overlapping scientific plotting workflow.
- **zarazhangrui/codebase-to-course**, 5,679 stars, actual SKILL.md: rejected before overlap review because inspected repository metadata/tree had no declared redistributable license.

Discovery used the first-party GitHub repository search API across high-star and 500–10,000-star bands; broad collections commonly already advertise Codex. Only the selected candidate had its archived skill and generator inspected in detail. No claim is made that every skill in a collection was assessed. No source was executed, installed, modified, or published during this research.
