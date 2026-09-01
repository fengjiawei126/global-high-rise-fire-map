# FAIR deposit plan

## Intended records

Create one versioned dataset record in Zenodo or a suitable institutional repository and one archived software release linked by reciprocal related identifiers. GitHub is the development location, not the sole preservation route. Do not deposit service-account JSON, environment secrets, copyrighted full-text articles or third-party files whose licence prohibits redistribution.

## Dataset record

- Proposed title: `Documented global high-rise building fires and linked heat, population and built-environment context, 2000–2026`.
- Resource type: dataset.
- Temporal coverage: 2000-08-02 to 2026-08-23.
- Spatial coverage: 52 countries and regions; point coordinates in WGS84.
- Creators, affiliations, funder and ORCID values: pending author confirmation.
- Licence: pending rights audit of the compiled event fields; licence for original curation must not override third-party terms.
- Files: processed event table, primary ERA5-Land case-crossover table, derived NASA POWER sensitivity table, NASA POWER request manifest, CTIF-derived national-capacity table, data dictionary, source registry, cohort audit, panel source data and checksums.
- Version: use semantic dataset releases beginning with `v1.0.0` only after GEE completion and final provenance review.

## Software record

- Archive a tagged GitHub release with Zenodo after removing credentials and local paths.
- Include notebooks, `src`, tests, environment specification, configuration template and exact run order.
- Use a standard software licence selected by the authors; dependency and upstream dataset licences remain separate.
- Link the software DOI to the dataset DOI and manuscript DOI or preprint when assigned.

## FAIR acceptance gates

| Principle | Required evidence before submission |
|---|---|
| Findable | DOI, rich title and abstract, keywords, creators, temporal and geographic coverage |
| Accessible | Public landing page, explicit access conditions, metadata retained if any file is restricted |
| Interoperable | UTF-8 CSV, ISO dates, WGS84 coordinates, declared units, stable event identifiers |
| Reusable | Licence, provenance, codebook, missing-value rules, processing workflow, version and checksums |

NASA POWER point responses are cached locally to make interrupted extraction recoverable, but the deposit will include the compact request manifest and derived matched-day table only after a provider-terms review. The manifest records API version, data sources, local-solar-time convention, coordinates, request interval and access timestamp. Near-real-time observations within two months of extraction remain explicitly flagged as provisional.

The CTIF-derived table retains Table 1.13 row identifiers, source page, source URL, extraction reference period and report SHA-256. Because the underlying report is copyrighted and country reporting methods differ, the report PDF will not be redistributed by the project. The derived table will be deposited only after a provider-terms review; otherwise the extraction code, field definitions and reproducible source locator will be released without protected report content.

## Blocking items

No central result should be submitted while the primary ERA5-Land case-crossover table is absent, the final DOI does not resolve, the event-data redistribution rights are unresolved, the NASA POWER and CTIF-derived-table redistribution reviews are incomplete, or the repository README and manuscript Data Availability statement disagree.
