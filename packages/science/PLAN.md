# Statistics implementation plan — current data revision

Revision: 2.1, 15 November 2026. Working branch: `codex/ml-statistics`.
This replaces the original statistics brief's hypothetical inputs and the
architecture's outdated acquisition assumptions. It is an implementation plan,
not a claim that an inference method or application has passed review.

## Problem and deliverable

For a selected variable, study rectangle and period, estimate how its regional
series changes, reveal variation between its grid cells, and expose how the
answer changes with the period. Return reproducible numerical evidence with
units, coverage, provenance and explicit uncertainty status. Do not promise an
opposite trend or infer causation. No neural-network training is required for
this statistical task.

## Inputs we will actually use

All twelve regional cubes exist in `data/nasa/measurements/`. Each contains 288
ordered months, January 2001 through December 2024. The original two Egypt
cubes are parent/reference assets, not additional independent products.

| Semantic ID | Product/version | Provider field | Processed cube field | Source units | Native spacing lat x lon |
|---|---|---|---|---|---|
| air_temperature | M2TMNXSLV 5.12.4 | T2M | T2M | K | 0.5 x 0.625 degrees |
| soil_moisture | GLDAS_NOAH025_M 2.1 | SoilMoi0_10cm_inst | SoilMoi0_10cm_inst | kg m-2 | 0.25 x 0.25 degrees |
| precipitation | GPM_3IMERGM 07 | precipitation | precipitation | mm/hr | 0.1 x 0.1 degrees |
| vegetation_greenness | MOD13C2 061 | CMG_0_05_Deg_Monthly_NDVI | NDVI | 1 | 0.05 x 0.05 degrees |

| Region ID | Rectangle: west, south, east, north |
|---|---|
| nile_corridor | 29, 24, 33, 32 |
| morocco_comparison | -10, 30, -5, 35 |
| sahel_comparison | -5, 12, 5, 17 |

The machine-readable input contract remains `docs/architecture/scope.v2.json`.
`source_variable` retains provider identity; `cube_variable` names the actual
processed field. `cube_units` is checked against the file. Do not infer aliases
from free text. Existing measurement/method/application flags remain separate.

## Changes from the previous plan

- Use the delivered four-variable, three-region bundle; no acquisition is needed
  for the first implementation. New products/regions remain outside this scope.
- Use 2001-01..2024-12 as the registered full-period reference. Explicit custom
  subperiods may be supported later; reject dates outside source coverage.
- Start with Nile precipitation for the first input/units tests, then exercise
  the same loader on all twelve cubes. Expand analysis only after each product's
  QA and estimand are explicit.
- Keep the numerical library independent of HTTP while its input and scientific
  tests are built. Reconcile backend schemas at the integration phase; a mock
  adapter choice must not prevent local data validation.
- Reuse/repair the existing React-branch engine where it passes review, rather
  than assuming either its delivery claim or a new engine is correct. Preserve
  the two recorded failing probes as regression evidence.
- Do not reset the data-ingestion work or mark the old method validated. Preserve
  the source bytes, legacy catalogs and historical audit reports.

## Scientific preparation

Preserve source timestamps and native grids; calendar month IDs are the selection
axis. Fail on duplicates, gaps, reversed axes, unknown fields/units and unsupported
calendars. Decode missing values, keep them missing, and report coverage before
and after any QA selection.

- Temperature: retain K; explicit Celsius display conversion subtracts 273.15.
  Temperature slopes have the same numeric values in K/year and Celsius/year.
- Soil moisture: retain kg m-2; do not convert to a percentage. Use the corrected
  Morocco cube and exclude missing cells explicitly from relevant denominators.
- Precipitation: retain the source mean rate and provide a separate monthly
  amount = rate x calendar-month hours. Annual precipitation totals must sum
  complete, eligible monthly amounts, never the rates. Label an annual-total
  trend as a change in annual accumulation per elapsed year.
- NDVI: use the already scaled `NDVI` field; do not multiply by 0.0001 again.
  Preserve `VI_Quality` and `pixel_reliability`, verify the source-guide flags,
  and version the selected QA policy before trend analysis.
- IMERG: retain `precipitationQualityIndex` and `randomError`. Do not invent an
  exclusion threshold or treat absence of one as proof of good quality.

For exploration, show a native-grid monthly map and a clearly identified cell's
time series. Phase 2 will define regional/cell eligibility, area-aware weights
and boundary treatment with hand-calculated fixtures. Variable coverage through
time must be visible; an apparently changing regional series may reflect a
changing valid spatial support.

## Trend and uncertainty decisions

Theil–Sen is the intended slope estimator. Pass elapsed time explicitly in years
for both monthly and annual inputs; validate the optional annual path against the
recorded factor-of-twelve regression. Compute the regional slope from the
aggregated series, never from an average of cell slopes.

Monthly charts/anomalies and correctly converted annual summaries serve
different estimands. The primary inferential basis, seasonal adjustment,
minimum-series and coverage thresholds, dependence correction, block length,
replicate count, confidence level, alpha, FDR procedure and test family are
**pending scientific validation**, not newly frozen defaults. Compare candidate
methods with known trends, seasonal nulls, serial dependence and missingness.
The React branch's m2-1.0.0 is an inherited candidate, not automatic approval.

Show descriptive slopes only after estimator checks pass. Keep p-values,
confidence intervals and significance overlays unavailable with an explicit
reason until their release gate passes. A valid inconclusive test is different
from insufficient data or inference not yet computed. Missing JSON numbers
serialize as null. Never label inconclusiveness as stability.

Cell shares use eligible cells as their stated denominator; missing/ineligible
cells are counted separately. Optional area shares require their own explicit
weights. Period-window sign agreement is descriptive and must compare each
eligible window to the actual full-period sign, not the majority window sign.

## Execution sequence and evidence gates

| Phase | Work | Acceptance / deliverable |
|---|---|---|
| 0 Input and plan alignment | Inspect actual data, define provider-to-cube mapping and library boundary | Exact IDs/fields/units, 12/12 current input audit, preserved historical probes, plan/report |
| 1 Validated input | Read-only loader, calendar/units/fill checks, retained QA fields, precipitation conversion | Real cube tests plus broken-input fixtures; executed exploration notebook, map/cell series, metadata report |
| 2 Analysis series | QA policies for all four products, bbox selection, fixed support/coverage, area weights, seasonal/annual preparation | Hand-calculated spatial/temporal tests; all twelve coverage summaries; reviewed eligibility decisions |
| 3 Slopes | Review/repair inherited time basis and shared regional/cell estimator | Positive/negative/zero known trends, missing/short/constant cases, reference comparison, no significance claims |
| 4 Inference | Review candidate dependence-aware inference and multiplicity | Repeated correlated-null/power simulations, interval coverage, block sensitivity, trusted FDR comparison, versioned reviewed config |
| 5 Spatial and sensitivity | Four-way labels, eligible-cell shares, native grids, period sensitivity | Correct denominators, scalar/grid eligibility parity, actual reference-sign agreement, no promised reversal |
| 6 Integration | Adapter to chosen existing /v1 service, result/request identities, charts/grid artifacts and receipts | Cross-role schema review, null handling, stale-request isolation, source/method hashes, measured runtime |
| 7 Scientific/demo review | Reproduce real examples and offline end-to-end flow | Regression suite, interpretation/limits, reviewed release flags, reproducible exports |

The original Phase 0 requirement for final backend/frontend/RAG sign-off is
deferred to Phase 6. Phase 0 now requires documenting the available interfaces
and a stable numerical-library boundary. This changes scheduling, not the final
integration or human-review requirement. Historical failed checks remain visible.

## Ownership, branches and checkpoints

Own numerical work under `packages/science/`, reusable checks under `tools/`,
and generated artifacts under ignored `data/derived/`. Keep Role 04's root
progress and implementation scope intact. Source data are immutable; explicit
metadata corrections/mappings are versioned separately. Do not merge either
remote application branch as part of a data-loader change.

The user explicitly authorized Stage 2 after the completed input checkpoint.
Its preparation implementation and tests are now complete; the candidate
policy and its spatial exclusions are awaiting owner review. Report the Stage 2
checkpoint before starting Stage 3. Major method changes and inference release
still require explicit review. Keep tests/reports honest about implemented,
failed, pending and unreviewed work.

## Stage 2 implemented preparation policy

`config/preparation_policy.json` records candidate `prep-1.0.0`; it is not a
NASA-prescribed statistical policy or an approved inference method.

- Bounding boxes select native cell centres inclusively inside a registered
  rectangle; reject wrapping, reversed axes, outside coverage and empty selections.
- Weight full selected native cells by spherical solid angle. Do not imply
  exact polygon-intersection area; the selected footprints can extend beyond
  the bbox edges. Keep native grids separate.
- Default strict MODIS QA accepts good MODLAND bits and good reliability only;
  standard mode explicitly admits marginal observations for comparison. Both
  exclude historical-fill/cloud/snow/unproduced observations. The CMG high bits
  are geospatial flags, not the snow/shadow interpretation of finer products.
- Retain IMERG quality/error fields without inventing a cutoff or quality
  weighting. Keep soil moisture nonnegative and temperature finite. Missing
  values stay missing; QA never imputes values or rescales NDVI.
- Regional and per-cell analysis series use cells valid after QA in every
  registered reference month. That set stays fixed for shorter requested periods.
  Report monthly QA coverage and retained support fractions for both cell count
  and selected native-cell area. A nonempty set permits preparation, not a
  guarantee of representative coverage or enough evidence for a trend.
- Annual rainfall sums twelve monthly amounts. Other annual summaries use
  calendar-day weights across twelve monthly values. Incomplete/missing years
  stay missing. Year coordinates contain actual years, not monthly indices.
- Monthly anomalies subtract the matching calendar-month mean over the same
  full registered reference; the baseline does not change silently with a query.

The strict NDVI fixed-support area fractions are 57.50% (Nile), 30.62%
(Morocco) and 14.69% (Sahel), measured over selected full native cells. Standard
QA retains 90.29%, 63.48% and 82.59%, respectively, while admitting marginal
observations. These are preparation sensitivity results, not uncertainty or
trend evidence. Review the choice before downstream inference; do not call
the retained series an unqualified whole-rectangle average.

## Next concrete implementation

Review the Stage 2 policy, support maps and QA sensitivity table. Once the next
checkpoint is authorized, start Stage 3: review/repair the shared Theil–Sen
estimator, use explicit elapsed years, exercise the inherited annual-unit bug,
and validate regional/cell slope recovery. No inference release is authorized
by a preparation checkpoint.
