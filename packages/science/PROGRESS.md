# ML/Statistics Engine — Progress
Last updated: 2026-11-15 02:51 Africa/Cairo
Current phase: PHASE 0
Current status: BLOCKED

| Phase | Status | Tests passed / total | Report | Approved to proceed? |
|---|---|---|---|---|
| 0 Contract lock | BLOCKED | 3/5 acceptance checks | [Report](phase_reports/PHASE_0_REPORT.md) | No |
| 1 Data exploration | NOT_STARTED | 0/5 | — | No |
| 2 Time series | NOT_STARTED | 0/6 | — | No |
| 3 Trend estimation | NOT_STARTED | 0/5 | — | No |
| 4 Significance | NOT_STARTED | 0/7 | — | No |
| 5 Spatial analysis | NOT_STARTED | 0/5 | — | No |
| 6 Integration | NOT_STARTED | 0/7 | — | No |
| 7 Final review | NOT_STARTED | 0/6 | — | No |

## Verified completed work
- Downloaded `https://github.com/omar-hossam0/nasa_planet.git` to `D:\projects\NASA\nasa_planet` and checked out the separate local branch `codex/ml-statistics` from `origin/main` (`ecf3908`).
- Read the supplied statistics brief, previous workspace progress/report, repository briefs, architecture, scope, registries, correction note, and relevant remote-branch contracts/source.
- No `AGENTS.md` found in the inspected workspace/ancestor paths or tracked branch inventories.
- Identified all 12 scope entries and their exact semantic variable/region IDs. Opened every combined cube with xarray, hashed the files, recorded actual dimensions/units/QA fields and verified each has all 288 ordered months from 2001-01 through 2024-12.
- Confirmed the corrected Morocco soil-moisture cube contains 32,544 missing values and no remaining literal `-9999` source fills.
- Found three catalog/source-field discrepancies: MODIS catalog source names differ from processed cube field `NDVI`.
- Located an existing statistics implementation on `origin/feature/react-product-ui` (`486fe73`). Two reproducible synthetic probes fail: annual slope units and regional/spatial minimum-length consistency. Its delivered/method-ready claims have not been adopted as validation.
- Located the separate mock backend interface on `origin/backend` (`3142bfe`); it differs from the React product interface.
- Added read-only audit/probe scripts, their JSON evidence, and statistics-specific progress/report files. Root Role 04 tracking is preserved.

## Current task / next action
- Resolve the processed MODIS field mapping with Role 01: keep the original source field distinct from the actual combined-cube variable.
- Resolve the backend integration target and request/result mapping with Role 03; do not silently combine incompatible schemas.
- Review the existing statistics implementation and reopen its affected trend/spatial validation before promoting inference.
- Finish Phase 0 and obtain the statistics brief's checkpoint approval before starting Phase 1. Do not recreate completed code merely because it resides on another branch.

## Decisions and scientific configuration
- Dataset and version: recorded from actual source bundle plus `scope.v2.json`: M2TMNXSLV 5.12.4, GLDAS_NOAH025_M 2.1, GPM_3IMERGM 07, MOD13C2 061.
- Variable IDs: `air_temperature`, `soil_moisture`, `precipitation`, `vegetation_greenness`; exact scope IDs, not the legacy `T2M` / `SoilMoi0_10cm_inst` catalog IDs.
- Region IDs: `nile_corridor`, `morocco_comparison`, `sahel_comparison`.
- Baseline period: available source coverage 2001-01..2024-12; chosen analysis baseline not yet approved. Candidate first input: Nile precipitation cube, consistent with the brief's proposed starting product.
- Temporal aggregation, weighting, eligibility, uncertainty, alpha and FDR: no new choices frozen. The React branch's `m2-1.0.0` configuration exists but failed targeted regression probes; its approval cannot be inferred from its status string.
- API schema version: `/v1` architecture; final executable integration mapping remains unresolved between remote branches. Do not implement the brief's illustrative `/api/analyses` interface as authoritative.
- Local work stays on `codex/ml-statistics`; no other branch was checked out for modification or merged.

## Open blockers / unresolved questions
- [ ] Main scope's MODIS `source_variable` is `CMG_0_05_Deg_Monthly_NDVI`; all three combined cubes expose `NDVI`. Original versus processed field identities require explicit mapping.
- [ ] Backend branch uses bbox AOIs, `status=completed`, `result_id`, and a mock `StatisticsAdapter`; React branch uses GeoJSON, `state=succeeded`, and a different real-data result shape. Integration target/sign-off unresolved.
- [ ] Existing annual path interprets annual values as monthly samples: synthetic truth 1/year produces 12/year.
- [ ] Existing spatial path admits a 48-month cell although configured minimum is 60 months and regional path rejects it.
- [ ] Existing inference design, source QA and broader tests require independent review; these two probes do not validate or exhaustively invalidate other paths.
- [ ] Scientific choices and scope of subsequent phase work require the statistics brief's checkpoint decision.

## Failed tests and regression issues
- `tools/audit_science_inputs.py`: exit 1; 12 cubes inspected, 9 entries without detected contract issues, 3 MODIS field mismatches.
- `tools/probe_existing_statistics.py`: exit 1; 0/2 targeted synthetic invariants passed at React commit `486fe73`.
- These are observed defects, not unsuccessful attempts to fix the methods. No method fixes have been attempted in Phase 0.
- No new statistical inference or full inherited regression suite was run. Probe outputs are synthetic diagnostics, not NASA climate conclusions.

## User approvals
- 2026-11-15: User supplied the statistics brief and requested resource acquisition.
- 2026-11-15: User supplied the repository and requested pulling it and working on a separate branch; branch created.
- 2026-11-15: On the integration-target question, user repeated “make a seprate branch.” This confirms isolation, but does not select or reconcile either interface.
- No subsequent-phase or scientific-method approval recorded.

## Phase history
- Earlier audit in parent workspace was blocked because only the brief was present. This repository resolves the source-download/data-availability blocker; that earlier report remains a historical record.
- 2026-11-15: Repository audit resumed on separate branch; 3/5 Phase 0 checks pass. Actual source and integration issues recorded with reproducible evidence; Phase 0 remains blocked.
