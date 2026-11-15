# ML/Statistics Engine - Progress
Last updated: 2026-11-15 (Sahel QA/coverage checkpoint)
Current phase: PHASE 2
Current status: DONE_WAITING_APPROVAL

Current plan: [PLAN.md](PLAN.md), revision 2.2. This tracker owns statistics
work; the repository-root PROGRESS.md owns Role 04 (RAG).

| Phase | Status | Tests passed / total | Report | Approved to proceed? |
|---|---|---|---|---|
| 0 Input/plan alignment | DONE | 5/5 revised acceptance checks | [Replan report](phase_reports/PHASE_0_REPLAN_REPORT.md) | Current implementation request covered first input work |
| 1 Data exploration | DONE | 5/5 acceptance checks; 16 automated tests passed | [Report](phase_reports/PHASE_1_REPORT.md) | User authorized Phase 2 |
| 2 Time series and QA | DONE_WAITING_APPROVAL | Original implementation complete; 44 combined tests pass after QA review | [Original report](phase_reports/PHASE_2_REPORT.md), [Sahel checkpoint](phase_reports/SAHEL_NDVI_POLICY_CHECKPOINT.md) | Recommendations ready; default unchanged; Stage 3 decision pending |
| 3 Trend estimation | NOT_STARTED | 0/5 | ? | No |
| 4 Significance | NOT_STARTED | 0/7 | ? | No |
| 5 Spatial analysis | NOT_STARTED | 0/5 | ? | No |
| 6 Integration | NOT_STARTED | 0/7 | ? | No |
| 7 Final review | NOT_STARTED | 0/6 | ? | No |

## Verified completed work
- Separate branch `codex/ml-statistics`, originally based on main `ecf3908`.
- Twelve regional cubes, four variables, three rectangles, 288 ordered months
  each. Available coverage and reference period: 2001-01..2024-12.
- Plan/architecture/READMEs updated to actual delivered inputs. No acquisition
  is needed for the first implementation. Original two Egypt cubes retained.
- Explicit `source_variable`, `cube_variable` and `cube_units` contract; all
  twelve current input checks pass. MODIS raw provider identity is preserved,
  with processed `NDVI` named explicitly. Source cubes are unchanged.
- Read-only validated loader: exact fields/units, product, Gregorian months,
  native axes, ancillary alignment and missing/infinite-value handling.
- Separate calendar-aware precipitation amount conversion (mm/hr to monthly
  mm), preserving rates, ancillary fields and missing values.
- 16 automated input tests passed. Includes real twelve-cube loading, broken
  fixtures, leap/non-leap months, CF missing values and NDVI scaling retention.
- Executed and visually inspected the first real-data exploration notebook:
  Nile precipitation map and fixed-cell series. Metadata records source hash,
  version, units, calendar, ancillary fields and non-inferential status.
- Historical audit and two inherited-method failing probes remain available.
  Their failures are not silently treated as fixes or method approval.

- Stage 2 product QA, bbox validation, spherical native-cell weighting, fixed
  support and annual/anomaly preparation implemented and tested.
- All twelve default-policy artifacts generated and independently reopened:
  288 months, 24 years, fixed support/weights, source/artifact hashes verified.
- Strict MODIS preparation and a three-region standard-mode comparison are
  recorded. Policy remains candidate_pending_owner_review; no release flags changed.
- Combined suite: 38 tests pass (16 earlier input tests, 21 original Stage 2
  checks and one diagnostic-metadata regression).
- Executed 02_preprocessing.ipynb and visually inspected all four diagnostics.
- Completed the requested Sahel QA/coverage supplement with six more controlled
  tests (44 total), separate experimental arrays, three inspected figures,
  monthly/seasonal flag distributions and a Stage 3 handoff recommendation.

## Current task / next action
- Stage 2 Sahel QA review complete under the user's explicit request. See
  [the checkpoint](phase_reports/SAHEL_NDVI_POLICY_CHECKPOINT.md): monthly/seasonal
  detailed QA, geographic selection, regional series, and separate strict/standard
  95%/90% valid-month experiments. No imputation, default change or inference.
- All 44 original policy/source/output/report/notebook files checked by SHA-256
  remain unchanged. Original strict/standard masks and means were reproduced
  read-only; six review artifacts live in a separate ignored derived folder.
- Recommend strict 100% as unchanged default/control, standard 100% as a fixed
  comparison and standard 95% as experimental sensitivity for Stage 3 development.
  Defer standard 90% from the core comparison (only two extra cells); retain strict
  relaxed cases as diagnostics. These are recommendations, not policy approval.
- Standard 95% eligibility retains 99.9751% of native-cell area; monthly observed
  area reaches a minimum 94.6698% of selected area in 2015-07. Carry the changing
  monthly footprint and seasonal missingness into any downstream interpretation.
- Stage 3 will review/repair the shared estimator with explicit elapsed years,
  known-trend tests and no significance release.
- Reuse/repair existing engine code only after relevant tests pass. Final
  HTTP adapter/schema reconciliation is a Phase 6 gate and does not block
  local validated-input work.

## Decisions and scientific configuration
- Products: M2TMNXSLV 5.12.4; GLDAS_NOAH025_M 2.1; GPM_3IMERGM 07; MOD13C2 061.
- IDs: air_temperature, soil_moisture, precipitation, vegetation_greenness.
- Regions: nile_corridor, morocco_comparison, sahel_comparison; existing scope
  rectangles retained. No national mask, new region or implicit regridding.
- Reference coverage: 2001-01..2024-12. First real input: Nile precipitation.
- Source fields/units: scope.v2.json input contract revision 1.0. Explicit
  processed NDVI mapping resolves the original three field issues.
- Precipitation conversion: mean mm/hr x actual Gregorian calendar-month hours
  -> monthly mm. Annual totals require complete eligible monthly amounts;
  annual aggregation has not yet been implemented.
- Candidate preparation policy: config/preparation_policy.json, prep-1.0.0.
  Strict MODIS good-quality/reliability only; optional standard mode admits
  marginal values. Historical estimation/cloud/snow/fill excluded. IMERG quality
  and error are retained without a quality cutoff or weighting.
- Geometry: centre-inclusive bbox, native ascending grids, full-cell spherical
  area weights; not exact polygon intersection. Reject wrapping/empty/outside AOIs.
- Support: valid after QA in every registered reference month, held fixed for
  shorter queries. Annual values require all twelve valid months. Rainfall sums
  amounts; other annual values use calendar-day weights. Anomaly baseline is
  the full registered calendar-month mean.
- Policy is implemented/validated in software, awaiting owner review. Strict
  retained NDVI area fractions: Nile 57.50%, Morocco 30.62%, Sahel 14.69% of
  selected full native cells. Standard fractions: 90.29%, 63.48%, 82.59%.
  Do not present those subsets as unqualified whole-rectangle coverage.
- Intended slope: Theil?Sen with explicit elapsed-year axis; pending Phase 3.
- Inference, alpha, FDR: no new method frozen or released. Existing m2-1.0.0
  remains an inherited candidate requiring independent review.
- API: documented /v1 architecture; existing remote branch payloads differ.
  Final owner sign-off and adapter mapping deferred to Phase 6, not removed.

## Open blockers / unresolved questions
- [ ] Owner review of candidate strict/standard QA and complete-case spatial
  support is pending. Low strict retention, especially Sahel, can bias which
  land is represented. Geometry is full centre-selected cells, not exact AOI area.
- [ ] Inherited annual path multiplies slopes by 12; repair/revalidate Phase 3.
- [ ] Inherited spatial path admits 48 months despite a 60-month regional
  minimum; repair/revalidate shared eligibility and Phase 5.
- [ ] Inherited inference and bootstrap design, assumptions and calibration
  require review before significance or confidence outputs.
- [ ] Backend branch uses mock bbox/status/result_id contracts; React branch
  uses GeoJSON/state and a different real-data payload. Reconcile at Phase 6.
- [ ] Current checkpoint requires policy review and the Stage 3 decision. No need to re-supply
  the catalog, source data or plan already present in the repository.

## Failed tests and regression issues
- Current combined suite: 38/38 pass; twelve-entry audit: 0 issues; generated artifacts: 12/12 round-trip checks pass.
- The original input_audit.json remains historical (three old mapping errors).
  input_audit_current.json describes the corrected metadata contract.
- existing_method_probes.json remains 0/2 at pinned React commit 486fe73.
  These are known later-phase engine defects; no repair attempted in Phase 1.
- Notebook kernel cleanup was corrected and execution rerun successfully.
- No climate trend/inference tests are claimed complete by this input suite.

## User approvals
- 15 Nov 2026: User explicitly requested implementing Stage 2. QA, selection,
  coverage and series preparation are authorized; inference release is not.
- User requested separate-branch work; branch isolation remains in place.
- 15 Nov 2026: user requested adapting the plan to the delivered data and
  advancing the solution. Implemented plan alignment and the first real-data
  preparation checkpoint under that scope; major method approval not inferred.
- Stage 2 is authorized and implemented. Policy adoption/Stage 3 follow the checkpoint protocol in the revised brief.

## Phase history
- Beginner-guide follow-up: metadata labels for diagnostic masks/fractions and
  weights were reopened after direct inspection, reproduced with a failing
  test, corrected, and revalidated. All numeric/coordinate arrays in 15
  regenerated files are unchanged. Output metadata revision 1.1; policy choices
  and the Stage 3 checkpoint remain pending. Added STAGE_2_EXPLAINED.md.
- Initial parent workspace audit: source data absent; historical report kept.
- Repository audit: 3/5 original Phase 0 checks passed; explicit mapping and
  incompatible-interface issues discovered with synthetic engine regressions.
- Current revision: original final-interface sign-off moved to Phase 6; revised
  Phase 0 checks pass 5/5 with explicit mapping and library boundary. The old
  blocked criterion is not retroactively marked passed.
- Phase 1: 5/5 acceptance checks, 16 automated tests, executed notebook and
  inspected real-data plot. Ready for Phase 2 checkpoint.
- Stage 2: 6/6 implementation acceptance checks, 37 combined tests, 12 strict
  prepared artifacts, 3 standard-MODIS comparison artifacts and inspected plots.
  Policy still awaits owner review; inference/Stage 3 not started.
