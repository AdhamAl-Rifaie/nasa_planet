# PHASE 2 REPORT - Bilingual Retrieval & Deterministic Fallback

- **Phase:** 2 - Bilingual retrieval and deterministic fallback
- **Status:** DONE
- **Date:** 14 November 2026
- **Implementation revision:** role04_phase2_v1
- **Executor:** Role 04 (Senior AI & RAG Engineer)

## Pre-flight work completed first (per instruction)

1. **Provider switch Mistral → Google Gemini:** `.env.example` now defaults to `LLM_PROVIDER=gemini`, `GEMINI_API_KEY=`, `LLM_MODEL=gemini-2.5-flash`, `LLM_TIMEOUT_SECONDS=8` (Mistral kept only as commented optional legacy fallback). `AGENT_BRIEF.md` §6 and `PROGRESS.md` updated: gemini is the configured default, provider stays configurable, no superiority claimed, keyless runs fall back to `local_retrieval` without blocking any phase.
2. **ID alignment fix:** `packages/rag/id_mapping.py` `resolve()` is now case-insensitive for latin IDs; `ndvi`, `MOD13C2`, `t2m`, `GPM_3IMERGM`, etc. all resolve to architecture-canonical semantic IDs (`vegetation_greenness` remains canonical per scope.v2.json). Phase 1 test updated to the approved alias behavior; no alias invented beyond the approved list.

## Phase 2 implementation

| Module | Content |
|---|---|
| `packages/rag/arabic.py` | Arabic normalization: strips tashkeel/tatweel, `أ/إ/آ/ٱ→ا`, `ة→ه`, `ى→ي`, `ؤ→و`, `ئ→ي`; handles attached prefixes (`وال، بال، كال، فال، لل، ال، و، ب، ل، ف، ك`); splits Arabic punctuation (`؟ ، ؛` — found and fixed a real defect: `؟` U+061F stayed glued to tokens). **Original display text is never mutated** (test-enforced). |
| `packages/rag/aliases.py` | Curated bilingual aliases for the 4 target variables + product aliases (MERRA-2/GLDAS/GPM/MODIS). Every alias is `team_authored` material with explicit provenance linking each variable to its official source IDs and product/version — never presented as NASA quotations (constant `TEAM_AUTHORED_NOTE`, tested). |
| `packages/rag/intent.py` | Deterministic intent classifier with guardrails: **`رطوبة` unqualified → `ambiguous/air_vs_soil_humidity`** with clarification (soil available, atmospheric humidity not a target variable; qualified air → `unsupported/target_variable_not_available`); **`شتاء`/winter alone → `ambiguous/season_without_variable`** and NEVER auto-maps precipitation (tested with `برد الشتاء` → air_temperature); temperature → air_temperature with explicit air-vs-surface clarification note; soil+percent → units note (kg m-2 is not %); cause-words → causality guard; neighborhood markers → `unsupported_resolution`; cross-grid/cell comparison + significance map → `cross_grid_comparison_requires_aggregation`; years < 2001 → `unavailable/period_outside_scope`; 8 out-of-scope topics (wind, earthquake, sea level, solar, ozone, clouds, air quality, crop yield) → `unsupported/out_of_scope_topic`; empty/whitespace → `empty_query`; >1000 chars → `oversized_query`; unrecognized → `no_target_variable_identified` (abstains with excerpts, never guesses a variable). |
| `packages/rag/retriever.py` | Self-contained Okapi BM25 (k1=1.5, b=0.75, no third-party dependency — brief-approved "upgraded lexical BM25 baseline") over the **469-chunk semantic corpus**. Variable-scoped candidate filtering + alias expansion; every variable answer attaches **definition context** (abstract/collection chunks) and **limitation context** (highest limitation-marker-density chunk from the same source); citations carry full provenance (chunk_id, source_id, source_kind, product_id/version, URL resolved from trusted records, retrieved_timestamp, raw_source_hash). Readiness integration via Phase 1 `ReadinessLookup`: region+period → `recommended`/`documented_only`/`unavailable` with per-variable availability; no region → `documented_only/no_region_selected` identifying candidate variables **without promising executable coverage**; period outside 2001-2024 → `unavailable/period_unavailable` with explicit note. `mode: "local_retrieval"` always; 100% offline. |
| `data/nasa/rag/retrieve.py` | Rewritten as a thin offline CLI wrapper (`--region`, `--period` flags) delegating to the package; output labeled `local_retrieval_not_generated_answer`; UTF-8 stdout forced on Windows. The old broken-mojibake alias table is gone. |

**Cairo isolation:** NASA POWER Cairo point sample is not part of the retrieval index (0 chunks, `segregated=True`, provenance note); tests assert it can never appear in any retrieval result and never mix with MERRA-2 Kelvin gridded evidence.

## Files created/changed

- `packages/rag/arabic.py`, `aliases.py`, `intent.py`, `retriever.py` (new); `packages/rag/id_mapping.py` (aliases + case-insensitive resolve)
- `data/nasa/rag/retrieve.py` (rewritten as offline CLI wrapper)
- `tests/test_phase2_retrieval.py` (new, 32 tests); `tests/rag/test_phase1_id_mapping.py` (alias assertions updated)
- `.env.example`, `AGENT_BRIEF.md` (§6 provider note), `PROGRESS.md`

## Commands run and outcomes

| Command | Outcome |
|---|---|
| `python -m pytest tests -q` (full suite: Phase 1 + Phase 2) | **PASS — 78 passed, 0 failed** (46 Phase 1 + 32 Phase 2) |
| CLI smoke: `python data/nasa/rag/retrieve.py "هل الدلتا بتسخن؟" --region nile_corridor --period 2001-01..2024-12` | PASS — `local_retrieval_not_generated_answer`, `documented_only`, `air_temperature`, 5 citations + definition/limitation context |

## Retrieval quality metrics (evaluation_questions.json, 12/12 behaved per contract)

| Question (abridged) | Status | Variables | Reason |
|---|---|---|---|
| هل الدلتا بتسخن؟ | documented_only | air_temperature | no_region_selected + air-vs-surface clarification |
| رطوبة التربة نسبتها كام؟ | documented_only | soil_moisture | + units check (kg m-2, not %) |
| ليه الحرارة زادت؟ | documented_only | air_temperature | + causality guard |
| هل MERRA-2 قياسات محطة؟ | documented_only | air_temperature | reanalysis doc citations |
| هل GLDAS قياس مباشر؟ | documented_only | soil_moisture | model doc citations |
| الدلالة 0.03 = 97% صح؟ | unsupported | — | no_target_variable_identified (no fabricated probability) |
| اتجاه حي مدينة نصر | unsupported | — | unsupported_resolution |
| احسب الاتجاه من 1990 | unavailable | — | period_outside_scope |
| رطوبة التربة متاحة؟ | documented_only | soil_moisture | readiness from registry, not corpus |
| فترة قصيرة تغيّر الاتجاه؟ | unsupported | — | no numeric sensitivity invention |
| مقارنة خليتين من شبكتين | unsupported | — | cross_grid_comparison_requires_aggregation |
| خريطة دلالة لكل الخلايا | unsupported | — | cross_grid_comparison_requires_aggregation |

## Defects found and fixed during Phase 2

1. Arabic `؟` (U+061F) glued to tokens broke alias matching (`بتسخن؟` ≠ `تسخن`) — Arabic punctuation now split before tokenization.
2. Multi-word out-of-scope topics (`sea level`) never matched single-token checks — matcher now supports multi-word phrases.
3. CLI wrapper had wrong repo-root resolution and a cp1252 stdout crash on Windows — both fixed; UTF-8 forced.
4. Product aliases missed exact dataset IDs (`M2TMNXSLV`, `GLDAS_NOAH025_M`) — added.

## Honest scope notes (not claimed)

- Retrieval quality is measured only on the 12-question evaluation set and the adversarial unit tests in-repo; no live-model evaluation has run (evaluation set remains `not_model_evaluated`).
- BM25 is a lexical baseline; no embeddings/vector DB (per brief). Arabic normalization is conservative; `ء` standalone hamza handling not needed in tested vocabulary.
- No LLM is invoked anywhere in Phase 2; Gemini integration belongs to Phase 3.

## Next phase

Phase 3 — provider integration (gemini, server-side key, bounded timeout/retry) and strict server-side output validation with adversarial tests.
