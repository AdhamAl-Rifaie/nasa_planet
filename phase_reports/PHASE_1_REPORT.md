# PHASE 1 REPORT - Corpus and Contract Alignment

- **Phase:** 1 - Corpus and contract alignment
- **Status:** DONE
- **Date:** 14 November 2026
- **Implementation revision:** role04_phase1_v1
- **Executor:** Role 04 (Senior AI & RAG Engineer)

## Scope of work completed

1. Read all mandated inputs: `AGENT_BRIEF.md`, `docs/architecture/PLAN.md`, `docs/architecture/IMPLEMENTATION.md`, `docs/architecture/scope.v2.json`, `data/nasa/runtime_catalog.json`, `data/nasa/validation_regional_report.json`, `data/nasa/QUALITY_CORRECTION_2026-11-14.md`, `data/nasa/rag/AI_CONTRACT.md`, both corpus files, source material and PROGRESS.md.
2. Phase 0 environment setup: created `.env.example` (LLM_PROVIDER=mistral, MISTRAL_API_KEY empty, LLM_MODEL, LLM_TIMEOUT_SECONDS=8, LLM_MAX_RETRIES). Verified `.gitignore` already excludes `.env`/`.env.*` and whitelists `!.env.example`. No secrets committed anywhere.
3. Built `packages/rag/source_index.py`: cited source index for **15 sources / 515 raw chunks** (315 starter corpus + 200 GPM/MODIS additions). Per-source records carry source_kind (`product_doc` / `method_doc` / `team_authored` reserved), product_version with explicit provenance of the version value, source_url, raw_source_hash, retrieved_timestamp, and hash re-verification against the local file. URLs resolve only from trusted source records. NASA POWER Cairo point sample registered as a strictly **segregated** record (Celsius, point sample, never regional-cube evidence).
4. Built `packages/rag/text_cleaning.py`: hybrid UTF-8/cp1252 decoder and documented PDF font-glyph (PUA) repair table.
5. Built `packages/rag/semantic_corpus.py`: re-chunked the fixed-character starter corpus into **469 topic/paragraph-based semantic chunks** (max 1600 chars, no mid-paragraph cuts except sentence-level splitting of overlong single paragraphs) with full provenance (`source_id`, `chunk_id`, `source_url`, `source_kind`, `product_id`, `product_version`, `section_locator`, `retrieved_timestamp`, `raw_source_hash`, `content_role`). Output: `data/nasa/rag/corpus_semantic.jsonl` + `corpus_semantic_manifest.json` (build metadata, encoding notes, team-authored builder statement). Availability/readiness fields are forbidden in chunks and validated absent.
6. Built `packages/rag/id_mapping.py`: explicit legacy→semantic ID mapping **derived from scope.v2.json entries** (T2M→air_temperature, SoilMoi0_10cm_inst→soil_moisture, precipitation→precipitation, CMG_0_05_Deg_Monthly_NDVI→vegetation_greenness; no invented aliases; unknown IDs raise). `ReadinessLookup` serves measurement_ready/method_ready/app_available keyed by variable_id × region_id × period × data_revision from the registry (never from text chunks); data_revision derived from `validation_regional_report.json` generated date (2026-11-14); out-of-window periods and mismatched revisions return explicit reason codes.
7. Test suite `tests/rag/` (5 files, 44 tests) covering brief §10 Phase 1 checks: provenance/hash verification, ID mappings, planned-vs-available state by AOI/period, POWER segregation, forbidden availability fields, and fully-offline operation (network monkeypatched to raise).

## Files created/changed

- `packages/rag/__init__.py`, `source_index.py`, `text_cleaning.py`, `semantic_corpus.py`, `id_mapping.py` (new)
- `data/nasa/rag/corpus_semantic.jsonl`, `data/nasa/rag/corpus_semantic_manifest.json` (generated)
- `tests/rag/test_text_cleaning.py`, `test_phase1_provenance.py`, `test_phase1_id_mapping.py`, `test_phase1_offline.py` (new)
- `pytest.ini` (new), `.env.example` (new)

## Commands run and outcomes

| Command | Outcome |
|---|---|
| `python -m pytest tests/rag -q` | **PASS — 44 passed, 0 failed** (final run) |
| Hash verification of all 15 source files vs recorded chunk/provenance hashes | PASS (scripted inside test suite; `test_raw_source_hashes_verified_against_local_files`) |

Intermediate runs during development surfaced and fixed: missing `CORPUS_FILES` import (NameError), missing dataclass field, over-strict retrieved_at consistency check (crawl batches legitimately differ; now records earliest per source and per-group timestamps), and a wrong whitespace-normalization expectation.

## Evidence

- Semantic corpus: 469 chunks across 14 chunk-bearing sources + segregated POWER record; 0 residual PUA/font-glyph characters; degree signs and curly quotes repaired from mixed-encoded GPM/MODIS additions file.
- Source hash verification: e.g. M2TMNXSLV snapshot `3ee6dff3…` matches recorded chunk hash; GPM collection snapshot `fab2b747…` matches; all 15 sources verified True.
- Defects found in inputs (logged, handled, not hidden): `data/nasa/expanded_v2/docs/rag_additions.jsonl` contains mixed UTF-8/cp1252 bytes (raw 0xB0) — decoded with hybrid decoder and documented in the manifest; `GLDAS` guide chunks carried a team placeholder version `guide_as_retrieved` — replaced with explicit not-recorded state.

## Architectural discrepancy logged (owner coordination)

- Task wording suggested target semantic ID `ndvi`; repository authority `docs/architecture/scope.v2.json` defines `vegetation_greenness`. Implementation follows the repository; resolve with Role 01/03 before Phase 2 if `ndvi` is intended as an alias.
- `scope.v2.json` entries carry no explicit `data_revision` field; Phase 1 derives revision from the regional validation report date. Explicit revision IDs remain a Role 01/03 dependency for Phase 2+.

## Remaining issues / next actions

- Method-doc software versions for scipy (1.18.0) and statsmodels (0.15.0) were read from the documents themselves; pymannkendall has no stated version (explicit `unknown`) — confirm with Role 02 if a pinned version is required.
- Team-authored Arabic aliases/translations are deliberately NOT yet added to the corpus (they belong to Phase 2 retrieval with `source_kind=team_authored` labels).
- Next: Phase 2 — bilingual BM25 retrieval, Arabic normalization, ambiguity clarification, evaluation against `evaluation_questions.json`.
