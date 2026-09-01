# Three-reviewer pre-submission audit

Last updated: 2026-09-01. This internal review evaluates the present manuscript, Supplementary Information, figures, source-data exports and analysis outputs. It is not an editorial decision and does not invent evidence beyond the project.

## Review setup

The review assumes a Nature Cities audience and evaluates technical validity, originality and significance, and interdisciplinary readability. The evidence population is a curated catalogue of documented high-rise building fires, not a complete registry. The prespecified primary estimand is the within-location association between a binary threshold-defined heatwave and a documented event day. Continuous temperature, severity, observation-process and resource-capacity analyses are secondary.

## Reviewer 1: Technical validity and statistical inference

### Summary

The same-location, same-month and same-weekday case-crossover design is appropriate for removing stable spatial and seasonal differences, and the separation of missing values from reported zeros is unusually careful. Two independent weather products, explicit spatial fallback tracking, cohort restrictions and complete reporting of unsuccessful scientific narratives are major strengths.

### Major concerns

1. The primary binary exposure is weakly identified: only 21 of 228 ERA5-Land strata and 17 NASA POWER strata contribute to the primary coefficient. The wide intervals cannot distinguish moderate harm, no association or benefit. The manuscript correctly reports this, but it must remain the leading result.
2. Continuous maximum-temperature anomalies produce positive estimates after adjustment for dewpoint, precipitation and wind, yet attenuate materially in temperature-only models. Low variance-inflation factors rule out severe linear collinearity as a complete explanation, but do not determine whether the other weather variables confound, suppress or mediate the contrast. These models identify conditional associations, not total heat effects.
3. The public-source event catalogue has no known sampling frame or denominator. The design can compare weather within recorded-event strata, but cannot estimate global incidence or fully correct weather-dependent event discovery.
4. Consequence models are vulnerable to complete-case selection, outcome misclassification and missing building size. Inverse-probability weighting addresses only measured injury-reporting predictors and should not be represented as recovering unobserved events or outcomes.
5. The GPW and GHSL layers are static 2018/2020 context assigned to events spanning 2000–2026. They should remain descriptive or secondary and never be described as contemporaneous building occupancy.

### Minor comments

- Preserve exact matched-day and informative-stratum denominators beside every heat estimate.
- Keep Holm-adjusted values for the five continuous timing specifications and avoid significance stars.
- State that NASA POWER uses local solar time and a substantially coarser grid.
- Archive the full source-data tables and a versioned environment without the service-account key.

### Assessment

Technically promising after the current revisions. The central inferences are defensible only if the binary null-leaning result and the continuous adjustment sensitivity remain explicit and co-equal.

## Reviewer 2: Originality, significance and urban-science contribution

### Summary

The most original contribution is the evidence architecture: acute weather is tested within place, approximately 1-km urban substrate is treated as context, and documentation is modelled as an observation process. This is more valuable than presenting another global risk surface from an event-only catalogue.

### Major concerns

1. The paper should not claim priority from a bounded literature search. The distinction from Shi et al. and Yao et al. lies in the high-rise event population and acute matched estimand, not in discovering that temperature can relate to urban fire activity.
2. The current data cannot identify mechanisms linking outdoor heat to electrical demand, cooling equipment, façade behaviour, occupant actions or ignition. Mechanistic pathways should motivate prospective measurement, not be presented as demonstrated.
3. Operational implications must remain restrained. The catalogue does not justify heat-triggered resource allocation, and national CTIF indicators are non-common-year, incomplete and too coarse to represent incident response.
4. The strongest broader contribution is falsifiability: weather product, threshold, lag, adjustment and evidence restrictions can weaken or reverse a simple positive-heat narrative. The Discussion should foreground that lesson.

### Minor comments

- Retain the concentration analysis as a registry-design and planning signal rather than a national ranking.
- Distinguish documented recording intensity from temporal incidence in every annual plot.
- Avoid “first”, “comprehensive”, “global incidence” and “validated risk score”.

### Assessment

Potentially broad urban-science interest if framed as a rigorous test of what a global documented-event catalogue can and cannot establish. Significance would be overstated if centred on a positive heat claim.

## Reviewer 3: Interdisciplinary readability, figures and reproducibility

### Summary

The visual hierarchy is coherent, the main atlas is readable, and the new continuous-temperature forest plot makes the key adjustment dependence visible. The manuscript is generally accessible to urban scientists, fire engineers and climate-health researchers.

### Major concerns

1. Readers may conflate the map's seven-day score, the binary inferential heatwave indicator and the continuous anomaly family. Each occurrence should retain a short definition and explicit analytical role.
2. The catalogue search, source-language coverage, dual-review process and adjudication procedure are not sufficiently documented to permit independent reproduction of event ascertainment. The released row-level provenance helps, but a formal search protocol and inter-rater audit would strengthen the paper.
3. Public reproducibility remains incomplete until the dataset and code receive immutable archival identifiers and author/funder metadata are supplied.
4. The Supplementary Information is quantitatively complete but dense. Table and figure captions should remain self-contained, with product resolution, sample size and causal boundary stated where needed.

### Minor comments

- Keep city annotations in black and avoid visually implying that labelled cities are statistical hotspots.
- Retain editable vector graphics and high-resolution TIFF exports.
- Add author-confirmed contributions, affiliations, funding, ethics or data-governance statements as applicable.

### Assessment

Readable and unusually transparent for a heterogeneous global catalogue. Submission readiness is limited mainly by ascertainment documentation and missing publication metadata, not presentation quality.

## Cross-review synthesis

All three reviewers agree that the manuscript's defensible contribution is methodological and evidential: it separates acute weather, urban context and documentation and reports analyses that do not yield a simple positive heatwave narrative. The priority revisions are to preserve the threshold-defined primary result, present the continuous family as adjustment-sensitive secondary evidence, document catalogue ascertainment more formally, and complete immutable archiving and author metadata. New mechanistic, prospective incident and subnational response data would materially strengthen causal and operational claims but cannot be manufactured from the current workbook.

## Risk and unsupported-claim register

| Claim at risk | Why unsupported | Allowed replacement |
|---|---|---|
| Heatwaves increase global high-rise fire risk | Primary threshold estimate is not positive and is imprecise | Prespecified threshold-defined heatwaves were not positively associated in this documented-event analysis |
| Continuous models prove a temperature effect | Estimates depend on simultaneous weather adjustment | Continuous anomalies showed a positive conditional association after weather adjustment that attenuated in temperature-only models |
| The catalogue measures global incidence | No complete sampling frame or denominator exists | The catalogue represents documented events identifiable through the curated workflow |
| Population colour shows occupants at risk in each building | GPW is a static approximately 1-km grid | Population is co-located neighbourhood context |
| National capacity estimates measure response effectiveness | CTIF values are partial, national and non-common-year | Capacity models are coverage-limited contextual sensitivity analyses |
| Missingness correction removes selection bias | Weighting uses measured predictors only | Reporting models diagnose structured observation and partially address measured injury-reporting selection |
| Findings justify heat-triggered dispatch | No prospective operational validation exists | Findings motivate prospective registration and testing |
