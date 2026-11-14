# PROGRESS - Role 04: RAG and Conclusion

Read alongside AGENT_BRIEF.md and the architecture. This file tracks work; actual contracts, source evidence and relevant tests must substantiate DONE. Do not redo completed work without a reason.

## Current status

- Implementation phase: NOT STARTED.
- Brief revision: v2, aligned with competition architecture on 14 November 2026.
- This update changes documentation only; no Role 04 implementation/evaluation is claimed.
- No per-phase approval gate. Continue when implementation is authorized; ask only for unresolved consequential decisions.

## Inputs already available

- Architecture: docs/architecture/PLAN.md and IMPLEMENTATION.md.
- Target scope and semantic IDs: docs/architecture/scope.v2.json.
- Existing source registry: data/nasa/runtime_catalog.json; its analysis_ready means ingestion readiness only.
- Verified measurements: MERRA-2 T2M v5.12.4 and GLDAS SoilMoi0_10cm_inst v2.1, Egypt rectangle, 2001-2024.
- Official source documents, 315-chunk starter corpus and local retrieval script under data/nasa/.

## Dependencies to discover or resolve with owners

- [ ] Role 03 executable API schemas and explicit legacy-to-semantic variable ID mapping.
- [ ] Role 05/06 action enum and payload contract; no fixed five-segment requirement.
- [ ] Role 02 evidence/null reason states and reviewed method configuration.
- [ ] Role 01 expanded variable-region readiness for precipitation, NDVI and other windows.
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
