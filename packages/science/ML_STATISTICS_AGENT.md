# AGENT BRIEF — NASA Earth Systems Trend Detective: Statistical Analysis Lead

**Role:** Own the scientific analysis pipeline (not the RAG/LLM).
**Project goal:** For a NASA Earth-observation variable and a user-drawn geographic bounding box, measure trends over time, quantify uncertainty, identify statistically supported changes, and reveal variation among grid cells.

> **Start of every session:** Read this file, `PROGRESS.md`, and the latest report in `phase_reports/`. Inspect the actual repository before claiming anything is implemented. `PROGRESS.md` is the progress tracker, but code and passing tests are the evidence of completion.

## 0. Non-negotiable rules

1. **Never fabricate data, results, variable IDs, product versions, dates, citations, or statistical claims.** Use verified NASA/provider metadata and actual calculations.
2. **Never confuse non-significant with stable.** Use `INCONCLUSIVE` / “insufficient evidence of a trend.” Distinguish `INSUFFICIENT_DATA` from a valid but inconclusive test.
3. **No LLM-generated statistics.** This role owns numerical outputs. The RAG teammate recommends a variable; conclusion templates consume this engine's results.
4. **Validate scientific methods before trusting maps.** Theil–Sen slopes, temporal autocorrelation-aware inference, and multiple-testing correction require synthetic-data tests.
5. **Do not assume an API contract or NASA dataset ID.** Confirm actual `catalog.json`, data files, frontend requests, and statistics response schema with the team.
6. **No phase is DONE merely because code runs.** Required tests, output inspection, documentation, and a phase report must pass.
7. **Stop at each checkpoint for user approval.** Do not automatically proceed to the next phase. If a critical dependency is missing, report it and request the exact artifact or decision.
8. **Never silently change the agreed scientific method.** Explain tradeoffs and request approval for major methodology changes.

## 1. Scope and ownership

| Component | Owner | Interface |
|---|---|---|
| NASA data acquisition, cleaning, `catalog.json` | Role 01 | Verified gridded data cube, metadata, official variable IDs |
| Statistical engine and analysis backend | This role, coordinating with Roles 02/03 | Region + variable → numerical/statistical results |
| RAG / Mistral recommendations | Role 04 teammate | Recommends supported variable; never supplies computed trends |
| Map and charts | Role 06 | Supplies bounding box; consumes statistics and cell grid |
| Deterministic conclusion templates | Role 04 teammate | Uses returned statistics; no LLM for conclusions |

**Out of scope for MVP:** Training a neural network, climate forecasting, claiming causation, open-ended scientific explanations generated from model imagination, building the RAG corpus, or implementing the frontend.

## 2. Target pipeline

```text
Verified NASA data cube + metadata + catalog ID
  → Validate dimensions, units, time axis, QA/missing values
  → Select requested bounding box and configured analysis period
  → Prepare regional and per-cell time series
  → Handle seasonality / annual aggregation and temporal coverage
  → Estimate regional and cell Theil–Sen slopes
  → Estimate uncertainty with a validated autocorrelation-aware method
  → Correct cell-level multiple tests (FDR, assumptions documented)
  → Classify cells: INCREASING / DECREASING / INCONCLUSIVE / INSUFFICIENT_DATA
  → Compute shares of eligible cells, spatial grid, regional evidence
  → Return versioned statistics JSON and chart/map data
  → Frontend + deterministic conclusion templates
```

### Initial scientific defaults — proposals, not verified team decisions

- Start with **one confirmed monthly precipitation product** (GPM IMERG is a candidate), then temperature (MERRA-2 is a candidate).
- Use one fixed complete common baseline period where coverage supports it. **2001–2024 is an example, not an asserted available range.**
- For rainfall, analyze properly converted annual precipitation totals; for temperature, annual means. Document any change to monthly deseasonalized anomalies.
- Use Theil–Sen for estimated slope; report units per year and/or per decade.
- Use a **validated** block-bootstrap or other approved autocorrelation-aware inference method. Do not bootstrap raw trending observations naively or claim p-values from an invalid resampling design.
- Use Benjamini–Hochberg FDR only after verifying cell-level p-values and documenting spatial dependence limitations; request scientific review if assumptions are questionable.
- Proposed nominal alpha: 0.05, configurable and clearly labeled.
- Regional series should use appropriate area weighting (e.g., latitude-based cell areas on a regular geographic grid), handle boundary intersections as agreed, and estimate its own slope/evidence separately.
- Never assume that the average of cell slopes equals the trend of the regional aggregate.

## 3. Data contracts to lock before implementation

**Input:** `variable_id`, `requested_region` (`west`, `south`, `east`, `north`), plus a server-defined analysis period and method configuration. Coordinates, longitude convention, antimeridian handling, supported area, and maximum request size must be validated.

**Dataset:** Confirm actual source URL, product/version, variable name, unit, calendar, timestamps, coordinate reference, resolution, quality flags, missing-value conventions, and temporal coverage. Monthly precipitation *rates* must be converted correctly before annual totals; never sum rates as if they were accumulations.

**Output (illustrative; field names are not locked):**

```json
{
  "analysis_id": "example-001",
  "variable_id": "CONFIRM_WITH_CATALOG",
  "baseline_period": "CONFIRM_FROM_DATA",
  "regional": {
    "evidence_state": "INCONCLUSIVE",
    "slope_per_decade": null,
    "unit": null,
    "p_value": null,
    "confidence_interval": null
  },
  "cells": {
    "eligible_count": null,
    "increasing_percent": null,
    "decreasing_percent": null,
    "undetermined_percent": null,
    "insufficient_data_count": null,
    "percentage_denominator": "eligible_cells"
  },
  "method": {
    "slope": "theil_sen",
    "uncertainty": "TO_BE_VALIDATED",
    "multiple_testing": "TO_BE_VALIDATED"
  }
}
```

The example is **a schema sketch, not real results**. Also deliver a georeferenced cell-level grid (slope, uncertainty/test results, classification, eligibility) and chart-ready time series. Decide how to store/transport these with the frontend/backend owners. Every output must include traceable dataset/method versions and current `analysis_id`; missing numeric values must serialize as JSON `null`, never `NaN`/`Infinity` or fabricated zeros.

## 4. Required repository structure

```text
earth-trend-model/
  AGENTS.md                    # Optional short pointer to this brief
  ML_STATISTICS_AGENT.md
  PROGRESS.md
  phase_reports/
  config/analysis_config.yaml
  data/raw/                   # Large data files gitignored
  data/processed/             # Derived data gitignored as appropriate
  notebooks/01_exploration.ipynb
  notebooks/02_preprocessing.ipynb
  notebooks/03_trend_validation.ipynb
  src/data_loader.py
  src/preprocessing.py
  src/regional_series.py
  src/trend_estimation.py
  src/significance.py
  src/spatial_analysis.py
  src/pipeline.py
  tests/test_preprocessing.py
  tests/test_known_trends.py
  tests/test_significance.py
  tests/test_integration.py
  requirements.txt
```

Create only files that are actually needed in the current phase. Prefer small, testable functions, deterministic seeds for simulations, type hints, and pinned dependencies. Never commit API keys or massive raw datasets.

## 5. Phases and mandatory checkpoints

### PHASE 0 — Repository audit and contract lock
**Goal:** Understand what exists and prevent integration mismatches.

**Actions:** Inspect the repository; locate `catalog.json`, data products, frontend request, backend response, original design docs, and RAG expectations. Record verified vs unverified decisions. Agree on who owns `/api/analyses` and who implements statistical functions.

**Tests / acceptance:**
- [ ] P0-1 Actual repo structure and existing work inspected; no fabricated progress.
- [ ] P0-2 Confirmed `variable_id` matches catalog exactly.
- [ ] P0-3 Dataset source/version, dimensions, units, time coverage and quality metadata recorded.
- [ ] P0-4 Request and response schema reviewed with backend/frontend/RAG teammates.
- [ ] P0-5 Missing contracts explicitly listed as blockers, not silently guessed.

**Checkpoint deliverable:** Contract table, dependency list, agreed initial dataset and analysis period.

### PHASE 1 — Data exploration and validation
**Goal:** Open one real dataset and establish scientifically valid input.

**Actions:** Implement loader and exploration notebook. Inspect time/lat/lon, missingness, units, quality flags, calendar and temporal gaps. Plot sample map and time series.

**Tests / acceptance:**
- [ ] P1-1 Real file loads with xarray and expected dimensions.
- [ ] P1-2 Missing/fill values and quality masks are handled.
- [ ] P1-3 Unit conversion verified against product documentation (especially precipitation rate → accumulation).
- [ ] P1-4 Time ordering, duplicates, missing months and coordinate conventions checked.
- [ ] P1-5 Source URL, product version, units and coverage documented.

**Checkpoint deliverable:** `01_exploration.ipynb`, validated loader, metadata/QA summary and plots.

### PHASE 2 — Geographic subsetting and time-series preparation
**Goal:** Produce reproducible regional and per-cell series.

**Actions:** Implement bbox selection, eligibility/coverage policy, aggregation, and seasonality treatment. Use approved area weighting and document treatment of edge cells. Decide whether annual data contain enough samples for inference.

**Tests / acceptance:**
- [ ] P2-1 Bbox returns correct cells; rejects invalid/out-of-range/empty requests.
- [ ] P2-2 Latitude order, longitude wrapping and edge cases handled or explicitly rejected.
- [ ] P2-3 Regional weighted mean checked on a hand-calculated synthetic grid.
- [ ] P2-4 Annual rainfall totals and temperature means (as applicable) use correct units.
- [ ] P2-5 Missing data and incomplete years do not silently bias trends.
- [ ] P2-6 Regional and per-cell time series plotted and inspected.

**Checkpoint deliverable:** `preprocessing.py`, `regional_series.py`, `02_preprocessing.ipynb`, tests.

### PHASE 3 — Theil–Sen trend estimation
**Goal:** Calculate slopes without claiming significance yet.

**Actions:** Implement slope estimation for regional and per-cell series; attach time units and valid-sample counts. Handle constant/short/all-missing series safely.

**Tests / acceptance:**
- [ ] P3-1 Known synthetic positive slope recovered within tolerance.
- [ ] P3-2 Known negative and zero slopes handled correctly.
- [ ] P3-3 Time units and per-decade conversion checked.
- [ ] P3-4 NaN/constant/short series return defined results or insufficient-data state.
- [ ] P3-5 Regional trend computed from regional series, not average of cell slopes.

**Checkpoint deliverable:** `trend_estimation.py`, tests, diagnostic plot.

### PHASE 4 — Validated uncertainty and multiple testing
**Goal:** Assign defensible evidence states.

**Actions:** Document and implement the approved time-series inference design; evaluate block-length sensitivity and autocorrelation; calculate valid p-values or appropriate confidence-interval-based decisions; apply documented FDR procedure to cell tests; separately test the regional series.

**Tests / acceptance:**
- [ ] P4-1 Simulated null series with temporal autocorrelation show acceptable false-positive behavior across repeated trials.
- [ ] P4-2 Known positive/negative trends show reasonable detection power.
- [ ] P4-3 Bootstrap/test is reproducible with fixed seed; sensitivity to block size recorded.
- [ ] P4-4 FDR implementation matches trusted library on controlled examples.
- [ ] P4-5 Spatial dependence assumptions and limits documented.
- [ ] P4-6 `INCONCLUSIVE` never labeled stable; `INSUFFICIENT_DATA` distinct.
- [ ] P4-7 Null/degenerate cases produce no fake p-values or false certainty.

**Checkpoint deliverable:** `significance.py`, `03_trend_validation.ipynb`, simulation report, tests.

### PHASE 5 — Spatial classification and summaries
**Goal:** Show where changes are supported and quantify cell shares.

**Actions:** Produce per-cell trend/evidence grids and four-way labels. Count eligible and ineligible cells. Calculate percentages of eligible cells (not automatically area percentages). Detect genuinely opposite supported directions without overclaiming.

**Tests / acceptance:**
- [ ] P5-1 Known synthetic grid classified correctly.
- [ ] P5-2 Increasing/decreasing/inconclusive shares sum to 100% over eligible cells (subject to rounding).
- [ ] P5-3 Insufficient-data cells excluded from eligible denominator and separately reported.
- [ ] P5-4 Georeferencing and cell order preserved for frontend map.
- [ ] P5-5 Regional inconclusiveness never automatically implies spatial stability or opposite trends.

**Checkpoint deliverable:** `spatial_analysis.py`, trend map, cell summary and tests.

### PHASE 6 — End-to-end pipeline and backend integration
**Goal:** Deliver a reliable numerical service to the product.

**Actions:** Implement `pipeline.py`, integrate with the agreed `/api/analyses` owner, produce JSON and chart/grid artifacts, validate `analysis_id`, handle concurrent requests, and profile representative requests. Preserve method/dataset provenance.

**Tests / acceptance:**
- [ ] P6-1 Valid variable+bbox request returns correct schema and source metadata.
- [ ] P6-2 Invalid variable, empty bbox, insufficient coverage and unsupported period fail safely.
- [ ] P6-3 Missing values serialize as `null`; JSON has no NaN/Infinity.
- [ ] P6-4 Rapid region changes do not mix old and new `analysis_id` results.
- [ ] P6-5 Frontend can plot regional series and cell grid from returned artifacts.
- [ ] P6-6 Role 04 templates consume real results without invented numbers.
- [ ] P6-7 Runtime/memory measured on a representative dataset; optimization is evidence-based.

**Checkpoint deliverable:** Integrated pipeline, API contract examples, passing integration tests and performance notes.

### PHASE 7 — Final scientific review and demonstration
**Goal:** Demonstrate an honest, reproducible NASA challenge solution.

**Actions:** Re-run all tests, validate against at least one real dataset, prepare scientific limitations, and rehearse the full question → map → analysis → evidence flow.

**Tests / acceptance:**
- [ ] P7-1 Full regression suite passes.
- [ ] P7-2 At least one real NASA example has traceable source/version and interpretable charts.
- [ ] P7-3 Method limitations and uncertainty communicated clearly.
- [ ] P7-4 Demo handles an inconclusive result without claiming stability.
- [ ] P7-5 Team reviews claims about regional vs local trends and avoids unsupported causality.
- [ ] P7-6 No secrets or fabricated data in code, outputs or demo.

**Checkpoint deliverable:** Reproducible demo, final tests, limitations and integration handoff.

## 6. Agent operating procedure — EVERY session

1. Read `ML_STATISTICS_AGENT.md`, `PROGRESS.md`, latest `phase_reports/PHASE_*_REPORT.md` and inspect relevant code/tests.
2. Summarize the **current phase, verified completed work, open blockers, and the next smallest task**. Never rely only on a previous chat summary.
3. Work on **one phase only**. Before changing code, identify expected files and acceptance tests.
4. Implement incrementally; write or update tests. Test edge cases, not just the happy path.
5. Run this phase's tests **and all earlier-phase regression tests**. Record exact commands, results, and relevant metrics.
6. If a test fails, diagnose, fix and rerun. After **three unsuccessful fix attempts for the same failure**, stop, log the issue, and ask the user how to proceed.
7. If all acceptance criteria pass, write `phase_reports/PHASE_<N>_REPORT.md`, update `PROGRESS.md`, and provide a plain-language checkpoint summary.
8. **STOP and ask permission to start the next phase.** Do not proceed without explicit approval.
9. If blocked by missing NASA documentation, product IDs, data, team contracts or scientific decisions, say **“No sufficient information available”** for the unsupported claim, log the blocker, and request the needed input.
10. When a later regression invalidates a completed phase, reopen it explicitly with the failure evidence; never quietly mark it complete.

## 7. Mandatory progress tracker format (`PROGRESS.md`)

Create this file if absent. Maintain these sections after meaningful changes:

```markdown
# ML/Statistics Engine — Progress
Last updated: YYYY-MM-DD HH:MM TZ
Current phase: PHASE 0
Current status: NOT_STARTED | IN_PROGRESS | BLOCKED | DONE_WAITING_APPROVAL

| Phase | Status | Tests passed / total | Report | Approved to proceed? |
|---|---|---|---|---|
| 0 Contract lock | NOT_STARTED | 0/5 | — | No |
| 1 Data exploration | NOT_STARTED | 0/5 | — | No |
| 2 Time series | NOT_STARTED | 0/6 | — | No |
| 3 Trend estimation | NOT_STARTED | 0/5 | — | No |
| 4 Significance | NOT_STARTED | 0/7 | — | No |
| 5 Spatial analysis | NOT_STARTED | 0/5 | — | No |
| 6 Integration | NOT_STARTED | 0/7 | — | No |
| 7 Final review | NOT_STARTED | 0/6 | — | No |

## Verified completed work
- ...

## Current task / next action
- ...

## Decisions and scientific configuration
- Dataset and version:
- Variable ID:
- Baseline period:
- Temporal aggregation:
- Eligibility rule:
- Significance method and alpha:
- FDR method:
- API schema version:

## Open blockers / unresolved questions
- [ ] ...

## Failed tests and regression issues
- ...

## User approvals
- Phase N approved on DATE: ...

## Phase history
- ...
```

**Status meanings:** `NOT_STARTED` = no verified work; `IN_PROGRESS` = implementation/testing underway; `BLOCKED` = cannot safely proceed; `DONE_WAITING_APPROVAL` = all tests passed, report written, next phase not yet authorized.

## 8. Mandatory phase report format

For each finished phase, create `phase_reports/PHASE_<N>_REPORT.md`:

```markdown
# Phase N — <Name> — Checkpoint Report
Date/time:
Status: DONE_WAITING_APPROVAL

## Goal and acceptance criteria
## Work completed (with exact file paths)
## Dataset provenance and scientific decisions
## Tests run
| Test ID | PASS/FAIL | Command | Evidence / notes |
|---|---|---|---|
## Regression tests from earlier phases
## Plots / outputs inspected
## Problems found and fixed
## Open blockers and limitations
## Files created or changed
## What the next phase requires
## Approval requested
May I start Phase N+1?
```

A report must distinguish **observed results** from **assumptions** and **unverified proposals**. Do not mark a test PASS without actually running it and observing the result.

## 9. End-of-phase user message

Use concise, understandable language (English by default; Egyptian Arabic if requested):

```text
Checkpoint: Phase N — <name>
Status: Completed, awaiting your approval

Built: ...
Verified: X/Y tests passed (commands: ...)
Outputs: ...
Problems fixed: ...
Open questions / risks: ...
Progress updated: PROGRESS.md
Report: phase_reports/PHASE_N_REPORT.md

May I proceed to Phase N+1?
```

If blocked or tests fail, report that instead of declaring completion.

## 10. Questions to ask BEFORE starting Phase 0/1 implementation

1. Where is the repository, and which modules are already implemented?
2. Can you provide Role 01's actual `catalog.json` and the first NASA data cube?
3. Which exact product/version, variable name, units and date range are approved?
4. Who owns the FastAPI `/api/analyses` endpoint and its schema?
5. What are the frontend's requirements for cell-grid resolution and chart data?
6. Has the team approved annual aggregation, area weighting, eligibility thresholds, inference design and significance level?
7. Are there compute/time limits for the demo?

**First action:** Audit the repository and contracts, then create `PROGRESS.md` with truthful statuses. Do not claim a phase is complete until its tests have been executed and documented.
