# Pre-submission rejection-risk audit

Last updated: 2026-09-01.

| Review dimension | Status | Evidence in project | Required action |
|---|---|---|---|
| Central contribution | pass with null-leaning boundary | The distinct acute within-location estimand is complete: ERA5-Land OR 0.72 (0.24–2.18), P=0.563 | Preserve the result as imprecise evidence that does not support a positive association; do not convert it into proof of no effect |
| Prior-art positioning | pass with boundary | `NOVELTY_AND_FALSIFICATION_AUDIT.md` identifies the closest direct prior art and prohibits priority language | Keep the distinction at estimand and evidence-architecture level |
| Catalogue representativeness | needs revision at submission | Figure 1, Figure 3 and observation-process models expose geographic, temporal and outcome-reporting structure | Do not report raw annual counts as incidence; pursue a prospective registry in future work |
| Heat-effect precision | needs new data | ERA5-Land has only 12–46 and NASA POWER only 7–43 informative strata by definition; all intervals include one | Report exact denominators and uncertainty; do not select the largest estimate |
| Product robustness | pass as sensitivity with disagreement | ERA5-Land and NASA POWER extractions are complete; primary point estimates lie on opposite sides of one | Treat direction change as exposure-product sensitivity, not independent confirmation |
| Mechanistic evidence | needs new experiment | No electrical-load, indoor-temperature, material-temperature or ignition-system measurements exist | Frame mechanisms as plausible pathways only; propose targeted engineering or operational studies |
| Consequence missingness | pass with untestable assumption | Missing/zero/positive distinction, reporting GLMs and stabilized injury weights are implemented | State that weighting assumes measured reporting covariates suffice and does not recover missing event discovery |
| Static spatial context | pass with boundary | GPW 2020 and GHSL 2018/2020 are separated from the acute model | Do not call gridded context incident-building occupancy or contemporaneous exposure |
| Fire-service capacity | needs new data | CTIF covers 141 extended events in 26 countries for firefighter metrics; all eight intervals include one | Treat as coverage-limited sensitivity and seek common-year, subnational deployment data |
| Reproducibility | pass | Four STEP notebooks, source modules, authenticated checkpoints, source hashes, panel CSVs and automated QA with zero errors | Deposit without credentials and archive a release DOI |
| Figure completeness | pass | Four main figures and five supplementary figures are complete in SVG PDF PNG and TIFF | Preserve panel source CSVs and inspect final journal-sized exports |
| Citation integrity | pass after current update | Publisher pages checked for Shi 2025, Jones 2022, Fetzer and Garg 2026 and Lee 2025; ENW and HTML review artifacts exported | Recheck correction/retraction status and journal instructions at submission |
| Submission metadata | needs author input | Author names, affiliations, contributions, funders and repository/data DOI remain placeholders | Obtain author-confirmed metadata and archive final release |

## Decision

The manuscript now contains the completed primary analysis and is scientifically auditable, but still requires author-confirmed metadata and archival deposition before submission. The dominant design limitation remains catalogue ascertainment; no amount of modelling can turn the curated public-source catalogue into a complete global incidence registry. The main empirical conclusion is deliberately constrained: current matched evidence does not support a positive acute heat association and is too imprecise to establish a precise null.
