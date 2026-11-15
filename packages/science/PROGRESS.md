# ML/Statistics Engine ? Progress
Last updated: 2026-11-15 03:43 Africa/Cairo
Current phase: PHASE 1
Current status: DONE_WAITING_APPROVAL

Current plan: [PLAN.md](PLAN.md), revision 2.1. This tracker owns statistics
work; the repository-root PROGRESS.md owns Role 04 (RAG).

| Phase | Status | Tests passed / total | Report | Approved to proceed? |
|---|---|---|---|---|
| 0 Input/plan alignment | DONE | 5/5 revised acceptance checks | [Replan report](phase_reports/PHASE_0_REPLAN_REPORT.md) | Current implementation request covered first input work |
| 1 Data exploration | DONE_WAITING_APPROVAL | 5/5 acceptance checks; 16 automated tests passed | [Report](phase_reports/PHASE_1_REPORT.md) | Awaiting Phase 2 decision |
| 2 Time series and QA | NOT_STARTED | 0/6 | ? | No |
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

## Current task / next action
- Phase 1 checkpoint complete; request Phase 2 as the revised brief specifies.
- Phase 2 defines source-supported QA, coverage and fixed valid support, bbox
  selection, area-aware regional/cell series and seasonal/annual preparation.
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
- QA: retain GPM quality/error and MODIS QA/reliability fields. No new product
  threshold or full screening policy has been adopted by the loader.
- Eligibility/area weighting/seasonal preparation: pending Phase 2 decisions.
- Intended slope: Theil?Sen with explicit elapsed-year axis; pending Phase 3.
- Inference, alpha, FDR: no new method frozen or released. Existing m2-1.0.0
  remains an inherited candidate requiring independent review.
- API: documented /v1 architecture; existing remote branch payloads differ.
  Final owner sign-off and adapter mapping deferred to Phase 6, not removed.

## Open blockers / unresolved questions
- [ ] Full QA rules, minimum coverage, fixed support and AOI boundary weighting
  need source review and controlled validation before regional analysis.
- [ ] Inherited annual path multiplies slopes by 12; repair/revalidate Phase 3.
- [ ] Inherited spatial path admits 48 months despite a 60-month regional
  minimum; repair/revalidate shared eligibility and Phase 5.
- [ ] Inherited inference and bootstrap design, assumptions and calibration
  require review before significance or confidence outputs.
- [ ] Backend branch uses mock bbox/status/result_id contracts; React branch
  uses GeoJSON/state and a different real-data payload. Reconcile at Phase 6.
- [ ] Current checkpoint requires the Phase 2 decision. No need to re-supply
  the catalog, source data or plan already present in the repository.

## Failed tests and regression issues
- Current input suite: 16/16 pass; current twelve-entry audit: 0 issues.
- The original input_audit.json remains historical (three old mapping errors).
  input_audit_current.json describes the corrected metadata contract.
- existing_method_probes.json remains 0/2 at pinned React commit 486fe73.
  These are known later-phase engine defects; no repair attempted in Phase 1.
- Notebook kernel cleanup was corrected and execution rerun successfully.
- No climate trend/inference tests are claimed complete by this input suite.

## User approvals
- User requested separate-branch work; branch isolation remains in place.
- 15 Nov 2026: user requested adapting the plan to the delivered data and
  advancing the solution. Implemented plan alignment and the first real-data
  preparation checkpoint under that scope; major method approval not inferred.
- Phase 2 onward still follow the checkpoint protocol in the revised brief.

## Phase history
- Initial parent workspace audit: source data absent; historical report kept.
- Repository audit: 3/5 original Phase 0 checks passed; explicit mapping and
  incompatible-interface issues discovered with synthetic engine regressions.
- Current revision: original final-interface sign-off moved to Phase 6; revised
  Phase 0 checks pass 5/5 with explicit mapping and library boundary. The old
  blocked criterion is not retroactively marked passed.
- Phase 1: 5/5 acceptance checks, 16 automated tests, executed notebook and
  inspected real-data plot. Ready for Phase 2 checkpoint.
