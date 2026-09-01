# Data dictionary

## Scope

`events_enriched.csv` contains documented high-rise building fire events, analytical cohort flags and linked contextual variables. A row is a documented event, not a population-rate denominator. Empty casualty fields mean unavailable information and must not be recoded as zero.

## Identifiers and provenance

| Field | Definition | Unit or values |
|---|---|---|
| `event_id` | Stable project event identifier | text |
| `source_url` | Traceable public source supplied or curated for the event | URL |
| `source_domain` | Host domain parsed from the source URL | text |
| `source_grade` | Operational provenance grade | project code |
| `source_file_sha256` | SHA-256 of the input workbook used for the audit | hexadecimal digest |
| `metric_provenance` | Origin of linked metrics | `legacy_exact_date_geo_match` or `requires_current_gee` |
| `gee_enrichment_status` | Earth Engine extraction status | status text |

## Event, place and outcomes

| Field | Definition | Unit or values |
|---|---|---|
| `event_date`, `event_year` | Documented fire date and derived calendar year | ISO date; year |
| `continent`, `country`, `location`, `city_label_en` | Geographic labels | text |
| `latitude`, `longitude` | Event coordinates | decimal degrees, WGS84 |
| `deaths`, `injuries`, `evacuated` | Reported people killed, injured or evacuated | persons; missing means unavailable |
| `fire_type`, `cause`, `fire_spread`, `impact` | Documented event descriptors | text |
| `building_use`, `building_use_group` | Reported and harmonised building use | text |
| `building_height_or_floors` | Original mixed height, floor-count or area description | text |
| `building_height_m_reported` | Explicitly metre-labelled building height; area and floor numbers are excluded | metres |
| `building_storeys_reported` | Explicitly storey-labelled floor count | storeys |

## Cohort flags

| Field | Definition | Unit or values |
|---|---|---|
| `valid_geocode` | Coordinates pass range checks | boolean |
| `external_trigger` | Aviation, warfare, missile or comparable external trigger | boolean |
| `arson_trigger`, `construction_related`, `facade_fire` | Prespecified event-category flags | boolean |
| `possible_duplicate` | Exact standardised date-coordinate duplicate candidate | boolean |
| `analysis_extended` | Valid date/geocode and no external trigger | boolean |
| `analysis_core` | Extended cohort with traceable source and no exact duplicate candidate | boolean |
| `cohort_reason` | Machine-readable inclusion or exclusion explanation | text |

## Earth Engine-linked variables

| Field | Definition | Unit or values |
|---|---|---|
| `population_count_2020_1km_cell` | GPWv4.11 2020 population count in the native 30 arc-second cell | persons per native cell |
| `population_density_2020_per_km2` | GPWv4.11 2020 population density | persons km$^{-2}$ |
| `heatwave_days_7d` | Days exceeding the compound threshold in the event-day seven-day window | days |
| `heatwave_degree_days_c` | Sum of positive daily maximum-temperature exceedances | degree-days, °C |
| `heatwave_max_t2m_c` | Maximum daily 2-m air temperature in the seven-day window | °C |
| `heatwave_p90_t2m_c` | Local 1991–2020 same-month 90th percentile of daily maximum temperature | °C |
| `heatwave_score_0_100` | Ten times cumulative exceedance degree-days, truncated to 0–100 for map display | descriptive score |
| `tmax_percentile_0_100` | Event-day daily maximum temperature percentile in the local baseline | percentile |
| `ghsl_built_surface_m2_1km` | GHSL built surface aggregated around the event | m² per approximately 1-km² neighbourhood |
| `ghsl_built_volume_m3_1km` | GHSL built volume aggregated around the event | m³ per approximately 1-km² neighbourhood |
| `ghsl_mean_building_height_m_1km` | GHSL mean building height around the event | metres |
| `ghsl_urbanisation_code_2020` | GHSL degree-of-urbanisation class | GHSL code |

## Country-year context

| Field | Definition | Unit or values |
|---|---|---|
| `iso3` | ISO3-like WDI economy code used for matching | text |
| `context_year`, `context_year_lag` | Matched WDI year and backward lag from event year | year; 0–3 years |
| `gdp_per_capita_ppp_constant_2021` | World Bank GDP per capita, PPP, constant 2021 international dollars | international dollars per person |
| `urban_population_percent` | World Bank urban population share | percent |
| `electricity_access_percent` | World Bank population with electricity access | percent |
| `national_population` | World Bank total national population | persons |

## National fire-service capacity context

`ctif_fire_service_capacity_2010_2023.csv` is a reproducible fixed-layout extraction of CTIF World Fire Statistics Report No. 30, Table 1.13. It contains 65 country rows and retains the original table row, country label, ISO3 code, national population denominator, fire stations, engines, ladders, career, part-time, volunteer and total firefighters, derived per-100,000-person metrics, the PDF page, source URL, reference-period wording and source-file SHA-256. Each row is the country's most recent available report during 2010–2023, not a common-year measurement.

In `events_enriched.csv`, matched fields carry the `ctif_` prefix. They are static national context variables and must not be interpreted as event-date staffing, incident deployment, service quality or a causal intervention. The career-firefighter metric matches 150 events overall and 141 extended-cohort events across 26 countries.

## Case-crossover weather table

`case_control_weather.csv` has one event-day row and all same-weekday control-day rows in the same month and year for each event stratum. It stores ERA5-Land `tmax_c`, lags 1–3, local P85/P90/P95 thresholds, `tmax_anomaly_c`, event-day percentile, dewpoint, precipitation, wind speed and six prespecified binary heatwave definitions. This file is created only after authenticated Earth Engine extraction.

## Independent weather-product sensitivity table

`case_control_weather_nasa_power_v10.csv` uses the same 1,004 event and matched-control dates for 228 strata but obtains daily meteorology from NASA POWER Release 10. The table contains `T2M_MAX`, `T2MDEW`, `PRECTOTCORR` and `WS10M` mapped to the same analytical field names and recomputes the fixed 1991–2020 same-month P85/P90/P95 thresholds and six heatwave definitions. `weather_source` identifies the MERRA-2/GEOS-IT product, `power_api_version` records the returned service version, `power_time_standard` records local solar time, `power_provisional` flags dates within two months of extraction, and `weather_status` retains request outcomes. `nasa_power_request_manifest.csv` stores one metadata row per requested coordinate, including the request URL and UTC access time. The product grid is approximately 0.5° latitude by 0.625° longitude and is used only for independent weather-product sensitivity, not as building-scale exposure.

`nasa_power_event_window_sensitivity.csv` stores 12 refits of the primary independent-product definition: the extended and core cohorts, four period or event-type exclusions and six leave-one-continent-out analyses. `restriction` names the retained evidence window, `analysis_family` separates event/evidence restrictions from geographic influence analysis, and `n_informative_strata` counts event strata with within-stratum exposure variation. Failed models would remain as status-coded rows. All current models completed, but all 95% confidence intervals include one and the point-estimate direction crosses one across restrictions.

## Recorded-consequence analysis outputs

`death_consequence_association_model.csv` and `injury_consequence_association_model.csv` store exploratory log-linear model coefficients. `building_scale_rank` is computed transiently as the mean within-dataset percentile rank of explicit metric height and explicit storey count, using the available rank when only one is reported; it is a relative evidence measure and not an imputed height. `reporting_probability` is the predicted probability that an outcome has a numeric record, `reporting_weight` is the stabilized inverse probability used for the injury model, and `effective_sample_size` reports the weight-based information size. `multiplicative_ratio` is the exponentiated coefficient from a `log(outcome + 1)` model and therefore describes a ratio of the geometric mean of recorded outcome plus one, not an incidence-rate ratio. Figure 4 source tables retain concentration-curve coordinates, building-size-quartile Wilson intervals and the plotted model estimates.

`ctif_fire_service_capacity_sensitivity.csv` contains eight exploratory extensions of the recorded-consequence model: deaths and injuries crossed with career firefighters, all firefighters, fire stations and fire engines. One `log1p`-transformed capacity metric is scaled per interquartile range and added at a time. `n_observations`, `n_countries`, `effective_sample_size`, `reference_period`, confidence intervals and weighting strategy expose the changing support. All current 95% confidence intervals include one; this is recorded as imprecision rather than evidence of no effect.
