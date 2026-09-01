# Novelty and falsification audit

Last updated: 2026-09-01. This is an internal claim-positioning document, not manuscript prose.

## Scope and non-priority statement

The audit combined a 2015–2026 Crossref search restricted to Nature Portfolio, the AAAS Science family and Cell Press with targeted checks of publisher abstracts and article pages. Search artifacts are in `citation_review/novelty_audit`. Failure to identify a prior study in this bounded search is not proof of priority. The manuscript must not use “first”, “first-ever”, “unprecedented” or “comprehensive global incidence”.

## One-sentence argument

In a heterogeneous global catalogue of documented high-rise building fires, the study separates acute event-day heat exposure, approximately 1-km population and built context, and the observation process using a same-location time-stratified design, independent weather-product checks and explicit reporting models, while retaining the boundary that the catalogue is not a population registry.

## Locked terminology

| Canonical term | Meaning | Prohibited drift |
|---|---|---|
| documented event catalogue | Events identifiable in the curated public-source workflow | global incidence database; complete registry |
| extended cohort | Valid date and coordinate, excluding external disaster triggers | all fires; population cohort |
| core cohort | Extended cohort with traceable source and no exact duplicate candidate | gold-standard incidence |
| acute heat exposure | Prespecified three-day local extreme-heat indicator | fire-danger index; causal heat score |
| 7-day heat-exceedance score | Bounded map-only descriptive score | probability; validated risk score |
| recorded consequence | Numeric death or injury information in documented records | true population burden |
| national fire-service capacity context | CTIF most-recent national values during 2010–2023 | incident deployment; common-year capacity |

## Contribution matrix

| Proposed contribution | Closest verified prior work | Exact distinction retained here | Internal falsification or boundary test | Current status and allowed wording |
|---|---|---|---|---|
| Acute heat estimand for documented high-rise fires | Shi et al. 2025 analysed temperature–frequency responses for urban fire types in 2,847 cities; Yao et al. 2024 analysed long-run urban fire activity in China | Event-day versus same-weekday control days at the identical high-rise event coordinate and month, rather than a city-level temperature–frequency curve | ERA5-Land and NASA POWER products, six heat definitions, core/recent/event-type exclusions, coastal-fallback exclusion and six leave-one-continent-out refits | Completed; ERA5-Land OR 0.72 (0.24–2.18) does not support a positive association and NASA POWER changes direction. Allowed: “tests a distinct acute within-location estimand”. Prohibited: “proves heat increases high-rise fire risk” |
| Observation process treated as an analysed object | Jones et al. 2022 found structured missingness in EM-DAT; Fetzer and Garg 2026 found cross-border disaster attention varied with event severity, hazard type and social ties | Numeric injury and evacuation reporting is modelled inside the fire catalogue using year, source grade, GDP and continent | Missing/zero/positive separation; reporting GLMs; stabilized injury-reporting weights; core-cohort sensitivity | Completed. Allowed: “shows structured outcome documentation in this catalogue”. Prohibited: “corrects all event under-ascertainment” |
| Evidence architecture that can return a null or sign change | Most urban-fire mapping studies optimize prediction or describe spatial risk | Product, definition, evidence-window and geographic checks are prespecified and reported even when they weaken the heat narrative | ERA5-Land primary estimate is below one; NASA POWER primary estimate is above one; all definition and restriction intervals include one | Completed. Allowed: “quantifies product sensitivity and imprecision”. Prohibited: “independent confirmation” |
| Consequence concentration linked to a resource-planning question | Behrendt et al. 2019 modelled fire-protection allocation; Lee et al. 2025 linked one-city severity prediction to dispatch scenarios | Concentration of recorded global high-rise consequences is separated from exploratory national capacity context | Gini curves, observation-process weighting, four separate CTIF capacity metrics, explicit event/country denominators | Completed but exploratory. Allowed: “identifies tail concentration and data gaps”. Prohibited: “ranks national fire-service effectiveness” |
| Population and vertical built context kept distinct from acute weather | Wu et al. 2026 linked fine-grid population and land use to urban-fire spatial risk in one district; GHSL and GPW provide global gridded context | Static approximately 1-km context is used for mapping and secondary consequence models, not the within-stratum heat coefficient | Self-matching removes time-invariant location context; captions state that GHSL is neighbourhood context rather than incident-building geometry | GEE processing completed for all 233 valid coordinates. Allowed: “co-located context”. Prohibited: “building occupancy” or “1-km causal exposure” |

## Citation support decisions

| Claim segment | Candidate | Support grade | Decision |
|---|---|---|---|
| Warming and urban fire types | Shi et al. 2025, Nature Cities, doi:10.1038/s44284-025-00204-2 | strong direct support | Retain; closest prior art and the key reason to narrow the novelty claim |
| Warming and fire generally | Turco et al. 2018, Nature Communications, doi:10.1038/s41467-018-06358-z | background only | Do not use for building-fire specificity; vegetation-fire context only |
| Structured event-database missingness | Jones et al. 2022, Scientific Data, doi:10.1038/s41597-022-01667-x | strong analogous support | Cite as global disaster-database evidence, with non-fire boundary explicit |
| Uneven public-source visibility | Fetzer and Garg 2026, Nature Human Behaviour, doi:10.1038/s41562-026-02512-6 | partial direct support | Cite for disaster-news selection, not for the completeness of this fire catalogue |
| Urban fire severity and resource planning | Lee et al. 2025, Scientific Reports, doi:10.1038/s41598-025-26006-z | partial support | Cite for one-city operational prediction; preserve simulation and generalisability limits |
| Population and urban-fire spatial risk | Wu et al. 2026, Scientific Reports, doi:10.1038/s41598-026-38373-2 | partial support | Cite only for one-district spatial context, not global or acute inference |

## Rejected metadata-only matches

- Guo et al. 2026 on urban heat islands and heatwaves does not test fires.
- Han et al. 2025 on credit-scoring missingness does not support event-catalogue ascertainment.
- The 2025 time-to-event GWAS ascertainment paper is methodologically unrelated to public fire records.
- Marwal and Silva 2023 characterises residential urban form but does not test urban fires.

## Remaining hard gate

The authenticated ERA5-Land extraction, conditional-logistic estimation, restriction diagnostics and Figure 2 are complete. The result is not a positive finding: the remaining hard gate is author-confirmed metadata and public archival deposition. Any revision that changes “does not support a positive association” into a causal null or positive heat-risk claim fails this audit.
