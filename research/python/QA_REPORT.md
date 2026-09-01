# Quality assurance report

Last verified: 2026-09-01 China Standard Time.

## Passed

- Updated workbook SHA-256: `386eb556101286e4dce89060d1d60ca105f5f54e97db3d3f297bcc2be6c291e5`.
- Event audit: 239 total, 233 geocoded, 228 extended, 191 core, 52 countries or regions.
- Mixed building-size text is now unit-aware: 84 explicit metric heights and 154 explicit storey counts were parsed, while the known 10,000-m$^2$ record remains missing for height.
- Casualty-field audit distinguishes 164 numeric injury records, 234 numeric death records, and 43 exact numeric evacuation records from 46 non-empty evacuation descriptions.
- `src/*.py` and `tests/*.py`: Python syntax compilation passed.
- Every non-empty Python source line and Notebook code-cell line has a Chinese end-of-line comment; no blank code lines were detected.
- STEP 1 executed and regenerated the standardized event table and audit manifest.
- STEP 2 completed with authenticated Earth Engine and `RUN_POWER=1`; 233 valid event coordinates received GPW/GHSL and heat fields, all 995 ERA5-Land case-control dates in 228 strata completed, World Bank context was matched for 237 events, NASA POWER completed every requested coordinate, and CTIF Table 1.13 was reproducibly parsed into 65 ISO3-coded national rows.
- NASA POWER produced 1,004 matched dates in 228 strata at 159 unique coordinates; every request status is complete, all 1,004 rows have fixed-baseline P85/P90/P95 thresholds, and 1,001 rows contain the complete adjusted-model covariate set.
- STEP 3 executed the primary ERA5-Land conditional logistic models. The prespecified estimate is OR 0.72 (95% CI 0.24--2.18; P=0.563; 21 informative strata); all six heat definitions include the null, with 12--46 informative strata. The independent NASA POWER estimate is OR 1.14 (95% CI 0.39--3.36; P=0.807), showing product-sensitive direction and persistent imprecision.
- Excluding the five strata that required the documented 20-km coastal fallback gives OR 0.77 (95% CI 0.25--2.36; P=0.651). Twelve ERA5-Land cohort, event-type and leave-one-continent-out models all converge and all intervals include one.
- The corrected exploratory severity model retains only 66 events with both deaths and injuries numerically reported. Per 10 heat-score points, the rate ratio is 1.04 (95% CI 0.90--1.21; P=0.608); missing casualty components are never recoded as zero, and sparse façade or construction indicators are not forced into this model.
- Twelve additional NASA POWER evidence-window models all converged. The primary-definition estimate ranges from 0.94 to 1.81 across cohort or event exclusions and from 0.76 to 1.56 across leave-one-continent-out analyses; all 95% confidence intervals include one, so direction is not described as invariant.
- The recorded-consequence extension distinguishes burden concentration from outcome reporting. Extended-cohort numeric records yield Gini 0.889 for deaths and 0.766 for injuries; the adjusted models contain 177 death and 127 injury records, with stabilized reporting weights used only for injuries.
- CTIF career- and total-firefighter capacity data matched 141 extended-cohort events in 26 countries. Eight prespecified capacity--outcome sensitivity models were exported; every 95% confidence interval includes one, and the manuscript records this as imprecision under partial, non-common-year coverage rather than evidence of no effect.
- Binary heatwave exposures now remain on the 0/1 scale; continuous weather covariates are expressed per IQR, and a synthetic recovery test confirmed interpretable odds-ratio output.
- GEE extraction now stores ordered temperature lags, P85/P90/P95 thresholds and prespecified 2/3/4-day heatwave definitions in one request.
- STEP 4 executed with the registered `global-fire-heatwave` kernel and exported Figures 1--4 and Supplementary Figures S1--S5 as SVG, PDF, PNG and TIFF with panel-level CSV source data; Figure 2 reports the completed ERA5-Land primary and definition-sensitivity estimates.
- A data dictionary, terminology ledger, FAIR deposit plan, citation review bundle and expanded claim-evidence ledger were created.
- A 2015--2026 Nature Portfolio/CNS-scoped novelty audit was completed. Publisher records were checked for the closest global urban-fire, disaster-ascertainment and operational-resource studies; three relevant citations were incorporated, unrelated candidates were rejected, and “first-ever global temperature--building-fire relationship” language is explicitly prohibited.
- Observation-process models were executed on 221 extended-cohort records and exported for injury and evacuation reporting completeness; manuscript claims reproduce their odds ratios, confidence intervals and denominators.
- `manuscript.tex` compiled to a fourteen-page PDF with resolved citations, four completed main figures and no overfull boxes or LaTeX warnings.
- `SI.tex` compiled to a thirteen-page PDF with Supplementary Tables S1--S11 and Supplementary Figures S1--S5; ERA5-Land primary, coastal, evidence-window and corrected severity results are included, continued model tables repeat their headers, and no overfull boxes or LaTeX warnings remain.
- Figures 1, 2 and S1 and Supplementary Tables S5--S11 were rendered and visually inspected after log-axis ticks, table widths, continuation headers and captions were corrected; labels and confidence intervals remain readable without clipping or overlap.
- The complete project QA script passed in the project `.venv` with `error_count=0` after the final figure, source-data and LaTeX edits.

## Deliberately not passed

- The previously supplied 30.68 versus 19.86 fires per 100,000 grid-days cannot be independently reproduced without a defined global grid-day denominator and is not asserted.
- Event-level descriptive heat fields combine 148 exact date-coordinate legacy matches with 85 newly processed GEE records; the inferential ERA5-Land case-control table is fully current for all 228 strata.
- Final author list, affiliations, funders, repository DOI and data DOI require author input or publication-stage deposits.

## Next hard gate

Obtain author-confirmed names, affiliations, contributions and funding, then archive the public code and permitted data with immutable DOIs. The service-account JSON remains outside both projects and must never be committed or shared.
