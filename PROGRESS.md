# PROGRESS - Role 04: RAG and Conclusion

Read alongside AGENT_BRIEF.md and the architecture. This file tracks work; actual contracts, source evidence and relevant tests must substantiate DONE. Do not redo completed work without a reason.

## Current status

- Implementation phase: NOT STARTED.
- Brief revision: v2, aligned with competition architecture on 14 November 2026.
- This update changes documentation only; no Role 04 implementation/evaluation is claimed.
- No per-phase approval gate. Continue when implementation is authorized; ask only for unresolved consequential decisions.

- Statistics (Role 02): method_revision m2-1.0.0 frozen; 12 evidence cards, 12 spatial maps, 9/9 synthetic checks and external agreement with scipy/pyMannKendall/NASA POWER recorded in data/nasa/analysis/. Numbers for Role 04 must be copied from those cards, never recomputed.

- Backend (Role 03): FastAPI service in `backend/` — catalog, analyses (idempotent, canonical hash), polling, results, receipts, health; 14/14 contract tests pass; measured 4.5 s for one variable and 0.013 s cached. Contract published in `backend/CONTRACTS.md` and `backend/openapi.json`; `app_available` stays false until Role 06 signs the end-to-end path.

- Explanations (Role 04): 522-chunk versioned corpus (GPM 141, MODIS 63 added), BM25 retrieval with injection exclusion, strict schema + validator (12 rejection codes), deterministic fallback, `GET /v1/analyses/{id}/explanation`; evaluation 19/19. No real LLM provider was called — generated-answer quality is not claimed.

- Spatial UX (Role 05): `web/` map UI served at `/app/` — native-grid cell layer from `/v1/spatial`, AOI drawing + numeric bounds, per-variable palettes, AR/EN, loading/error/insufficient states, keyboard access; state contract in `web/STATE_CONTRACT.md`; four state screenshots in `docs/screenshots/`. Backend tests 19/19.

- Integration (Role 06): series + compare endpoints, Reality Check, receipt/CSV export, offline build (`dist/offline`, 12 analyses, 2.75 MB, runs from `file://`), release checks 15/15 (`docs/acceptance_report.json`), `app_available` signed for 12/12 entries, 90-second demo script in `docs/DEMO_SCRIPT.md`. Backend tests 22/22.

## Inputs already available

- Architecture: docs/architecture/PLAN.md and IMPLEMENTATION.md.
- Target scope and semantic IDs: docs/architecture/scope.v2.json.
- Existing source registry: data/nasa/runtime_catalog.json; its analysis_ready means ingestion readiness only.
- Verified measurements: MERRA-2 T2M v5.12.4 and GLDAS SoilMoi0_10cm_inst v2.1, Egypt rectangle, 2001-2024.
- Verified measurements (expanded): GPM IMERG precipitation V07 and MOD13C2 NDVI V061, plus Morocco/Sahel T2M/soil moisture and Nile subset cubes. 12/12 cubes, 2,880/2,880 monthly subsets verified.
- Official source documents, 315-chunk starter corpus and local retrieval script under data/nasa/.

## Dependencies to discover or resolve with owners

- [ ] Role 03 executable API schemas and explicit legacy-to-semantic variable ID mapping.
- [ ] Role 05/06 action enum and payload contract; no fixed five-segment requirement.
- [ ] Role 02 evidence/null reason states and reviewed method configuration.
- [x] Role 01 (data) complete: DONE 14 Nov 2026. Twelve cubes, `preprocess.py`, `qa_policy.json`, `coverage_report.json`, `regional_lineage.json` (3,456 hashed entries) and `study_windows.geojson` delivered; see docs/roles/MEMBER_1.md. Original note on expanded readiness: All 12 variable x region cubes verified and in-repo (see data/nasa/validation_regional_report.json and docs/architecture/scope.v2.json: every entry status=verified_cube_ready, measurement_ready=true). Precipitation (GPM_3IMERGM V07) and NDVI (MOD13C2 V061 with QA fields) now cover Nile/Morocco/Sahel; Morocco/Sahel T2M and soil moisture added; Nile windows subset from verified Egypt parent cubes.
- [ ] Configured provider/model and server-side key setup; does not block local retrieval/templates.

## Phase tracker

| Phase | Deliverable | Status | Verification | Report |
|---|---|---|---|---|
| 1 | Corpus and contract alignment | NOT STARTED | NOT RUN | - |
| 2 | Bilingual retrieval | NOT STARTED | NOT RUN | - |
| 3 | Provider integration and validation | NOT STARTED | NOT RUN | - |
| 4 | Interactive conclusion templates | NOT STARTED | NOT RUN | - |
| 5 | Integrated evaluation and presentation | NOT STARTED | NOT RUN | - |

Statuses: NOT STARTED / IN PROGRESS / DONE / BLOCKED. Record a concrete dependency for BLOCKED; continue independent work.

## Open issues

No implementation defects have been evaluated yet. Do not interpret this as evidence of zero defects. Provider capabilities/latency, retrieval quality and current submission requirements remain unmeasured or to be verified. Do not repeat earlier unverified corpus-size or latency claims.

## Change log

### 14 November 2026 - Brief alignment

Replaced outdated two-variable assumptions, per-phase approval loops and chat-page references. Added per-region/period readiness, semantic numeric grounding, explicit null reasons, variable conclusion segments, current architecture paths, source-aware scientific language and executable-contract reconciliation. Updated tracking without claiming any phase completed.

## Phase report convention

Write phase_reports/PHASE_<N>_REPORT.md after meaningful phase completion. Record revision, changed files, exact checks and PASS/FAIL/NOT RUN outcomes, remaining issues and next actions. A repeated failure calls for diagnosis and a different approach, not blind retries or an automatic halt of unrelated work.
