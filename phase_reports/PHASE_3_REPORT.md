# PHASE 3 REPORT - Provider Integration & Strict Server-Side Output Validation

- **Phase:** 3 - Provider integration and output validation
- **Status:** DONE
- **Date:** 15 November 2026
- **Implementation revision:** role04_phase3_v1
- **Executor:** Role 04 (Senior AI & RAG Engineer)

## Pre-flight ground truth

Read `AGENT_BRIEF.md` (§4, 5, 6, 7, 10), `PROGRESS.md`, `phase_reports/PHASE_1_REPORT.md`, `phase_reports/PHASE_2_REPORT.md`, `docs/architecture/PLAN.md`, `docs/architecture/IMPLEMENTATION.md`, `docs/architecture/scope.v2.json`, `data/nasa/runtime_catalog.json`, `data/nasa/rag/AI_CONTRACT.md`, and all existing `packages/rag/` code plus the Phase 2 test suite. `data/nasa/delivery_manifest.json` referenced in the tasking does not exist in the repository (noted; nothing depended on it). Full-suite baseline reproduced before changes: 78/78 pytest PASS (Phase 1+2).

## Implementation

| Module | Content |
|---|---|
| `packages/rag/provider.py` | `GeminiClient` for Google Gemini `gemini-2.5-flash` via the official REST endpoint (`generativelanguage.googleapis.com v1beta generateContent`) using **stdlib `urllib` only** — no third-party SDK, keeping the dependency footprint at zero (consistent with the self-contained Phase 2 BM25 decision; SDK/model identity verified against Google's documented REST API shape). Env config: `LLM_PROVIDER`/`GEMINI_API_KEY`/`LLM_MODEL`/`LLM_TIMEOUT_SECONDS=8`/`LLM_MAX_RETRIES=1` per `.env.example`. **Key handling:** loaded server-side only; sent exclusively in the `x-goog-api-key` request header (never in the URL/query string); error messages and exceptions contain only static templates (HTTP status / reason class), so the key can never leak into logs, exceptions, or fallback payloads. `is_configured()` gates keyless runs. `ProviderError` carries a coarse reason (`missing_api_key`, `network_error`, `timeout`, `http_error`, `empty_response`, `provider_not_configured`). `responseMimeType: application/json` requested for structured output; candidate-part text extraction with explicit empty/absent-response failure. |
| `packages/rag/validator.py` | Zero-trust gatekeeper `validate_llm_payload(payload, EvidenceContext)`. **Schema gate:** JSON object only; exact allowed field set `{answer, cited_chunk_ids, suggested_variable_ids, product_versions?, limitations?}` — any unapproved extra field (including model-emitted URLs, availability objects, product_version fields) is rejected; required fields + strict types (answer non-empty string ≤ 4000 chars; arrays of strings). **Current-retrieval citation enforcement:** every cited `chunk_id` must be a member of the evidence set assembled for *this specific request* (citations + definition/limitation context chunks); a valid corpus chunk_id that was not retrieved is rejected. **Variable membership:** `suggested_variable_ids` ⊆ permitted variable set derived from the Phase 2 classification for this request. **Product-version consistency:** optional `product_versions` claims are checked for exact string equality against the scope registry versions (`MERRA-2 5.12.4`, `GLDAS 2.1`, `GPM 07`, `MODIS 061`); wrong versions rejected. **Trusted URL resolution:** final citations are rebuilt server-side; URLs come only from `SourceIndex.resolve_url(source_id)` — model-emitted raw URLs are structurally impossible (schema) and never used. **Availability truth:** the output's `availability`, `status` and `reason_code` are copied from the deterministic pipeline (registry lookup), never from the LLM; the model cannot emit availability fields (schema) and cannot promote readiness in prose (internal field names `app_available`/`measurement_ready`/`method_ready`/`analysis_ready` banned in answer text). **Scientific wording guardrails (brief §7):** prompt-injection/secret-exposure patterns ("ignore instructions", "api key", Arabic equivalents) rejected; false-causality assertion patterns (`caused by/the/this`, `due to`, `because of`, `بسبب`, `يؤدي إلى`, …) rejected unless the same sentence carries an explicit denial (`does not establish cause`, `لا يثبت`, …); MERRA-2/GLDAS described as "satellite observations/measurements" rejected (reanalysis/model vs satellite mislabeling); NDVI→"crop yield"/`محصول` rejected (greenness is not yield); Celsius/`°C` claims on MERRA-2 Kelvin data rejected (negation-exempt, e.g. "not Celsius" passes); digit-bearing percent claims on GLDAS `kg m-2` soil moisture rejected; NASA POWER/Cairo-station mentions on air-temperature answers rejected (keeps the Phase 1 Celsius point-sample segregation intact). Model `limitations` strings are screened and silently dropped if they violate guardrails; server limitations are always prepended. |
| `packages/rag/explanation.py` | `ExplanationPipeline.explain(query, region_id, period, data_revision)`: Phase 2 retrieval answer → non-retrieval statuses (`unsupported`/`ambiguous`/`unavailable`) and citation-less answers pass through untouched as `local_retrieval` (LLM never invoked) → if provider unconfigured → `local_retrieval` fallback without any network attempt → else builds a constrained prompt (untrusted-evidence warning, permitted-variables list, per-chunk `[chunk_id | source_id | kind | product vX]` evidence blocks, exact JSON schema, prohibitions on URLs/availability/numbers/causation, MERRA-2-reanalysis and GLDAS-model framing) → calls provider → fence-tolerant JSON parse → validation → on format/validation failure **bounded retry of exactly 1** with the same prompt → any remaining failure returns the full deterministic `local_retrieval` answer with a `fallback_reason` (`invalid_json:…` / `validation_failed:…` / `provider_error:timeout` / `provider_error:network_error` / `provider_error:missing_api_key` / `provider_not_configured`). Network/timeout errors do **not** consume a retry (immediate clean fallback per brief §6; retry reserved for validation/format errors). Validated `llm`-mode output carries `mode: "llm"`, model answer, server-rebuilt citations, registry availability, merged limitations and a `validation: {passed: true, cited_chunk_ids}` block. |

## Files created/changed

- `packages/rag/provider.py`, `validator.py`, `explanation.py` (new)
- `tests/test_phase3_validation.py` (new, 35 tests)
- `tests/rag/test_phase1_offline.py` (offline-guard updated: the "no network client imports" rule now bans all third-party network SDKs (requests/httpx/aiohttp/google-*) package-wide and confines stdlib `urllib` to `provider.py` only — retrieval/validation/pipeline remain network-free; original intent preserved)
- `PROGRESS.md`

## Commands run and outcomes

| Command | Outcome |
|---|---|
| `python -m pytest tests -q` (full suite Phase 1+2+3) | **PASS — 115 passed, 0 failed** (47 Phase 1 + 33 Phase 2 + 35 Phase 3) |
| `python -m pytest tests/test_phase3_validation.py -q` | **PASS — 35 passed** (isolated) |
| `python -m pytest tests --collect-only -q` | 115 collected, counts verified per file |

First full-suite run surfaced 1 regression: the Phase 1 offline guard rejected `urllib` anywhere in `packages/rag`; resolved by scoping the guard (third-party SDKs banned everywhere, stdlib transport confined to the provider module) — retrieval/validation/pipeline remain fully offline, verified by socket-denial tests.

## Adversarial coverage mapped to brief §10 Phase 3

| Failure mode | Test |
|---|---|
| Invented chunk ID | `test_invented_chunk_id_rejected_then_local_fallback` |
| Valid-but-not-retrieved corpus citation | `test_corpus_chunk_valid_but_not_retrieved_rejected` |
| Unapproved extra fields (model-emitted URL + availability) | `test_unapproved_extra_fields_rejected` |
| Wrong product version | `test_wrong_product_version_rejected` |
| Malformed JSON | `test_malformed_json_retried_once_then_fallback`; recovery path `test_retry_recovers_after_first_validation_failure`; fence handling `test_markdown_code_fence_json_accepted` |
| Provider timeout / network error | `test_provider_timeout_falls_back_without_retry`, `test_network_error_falls_back` |
| Missing key / keyless | `test_keyless_run_never_calls_provider`, `test_keyless_pipeline_makes_no_network_attempts`, `test_gemini_client_without_key_reports_missing_key_offline` |
| Key secrecy | `test_gemini_client_sends_key_in_header_not_url`, `test_gemini_client_http_error_maps_without_key_leak`, `test_api_key_never_appears_in_prompt_or_fallback_output` |
| Prompt injection | `test_prompt_injection_wording_in_answer_rejected`, `test_injected_evidence_never_promotes_availability` (injected passage cannot promote readiness; citation URLs forced to trusted records) |
| False causality | `test_false_causality_rejected`; denial passes: `test_causal_denial_language_passes` |
| NDVI as crop yield | `test_ndvi_crop_yield_claim_rejected` |
| Reanalysis mislabeled as satellite | `test_reanalysis_mislabeled_as_satellite_rejected` (corrected phrasing passes on retry) |
| Kelvin vs Celsius conflation | `test_kelvin_celsius_conflation_rejected` |
| Cairo POWER vs MERRA-2 conflation | covered by the air-temperature "never" guardrail asserted in `test_injected_evidence_never_promotes_availability` context and POWER guardrail in validator config |
| Soil moisture percent vs kg m-2 | `test_soil_moisture_percent_claim_rejected` |
| Availability truth | `test_availability_truth_comes_from_registry_not_model` |
| Suggested-variable membership | `test_suggested_variable_outside_permitted_set_rejected`; deterministic default `test_empty_suggested_uses_deterministic_pipeline_values` |
| Wrong types / no-availability-in-chunks | `test_wrong_type_answer_rejected`, `test_retrieved_chunk_records_never_contain_availability_fields` |
| Non-retrieval statuses bypass LLM | `test_non_retrieval_statuses_pass_through_without_llm`, `test_out_of_scope_query_passes_through` |
| Real client plumbing | `test_gemini_client_parses_generate_content_response` (fake transport), REST config tests |

## Honest scope notes (not claimed)

- **No live Gemini call has been made** — no API key exists in the repository; provider behavior is verified via scripted providers and fake HTTP transports, plus real-client configuration/timeout/header tests. Live-model latency and answer quality remain unmeasured and belong to Phase 5 integrated evaluation.
- Guardrails are conservative pattern-based wording checks with negation/denial exemptions; they are a defense layer on top of the structural guarantees (schema + citation membership + registry availability), not a semantic NLU system. Edge wording outside the pattern lists is conceivable; structural checks bound the damage.
- Prompt says the model must not emit statistics; numeric analysis grounding against verified result fields (result_id path, `/v1/explanations` with a result) is Phase 4/5 work with Role 03 schemas.
- Retry policy: exactly 1 retry on validation/format errors; network/timeout errors fall back immediately (bounded, per brief §6).

## Next phase

Phase 4 — deterministic interactive conclusion templates (result-state templates, allowed action payloads pending Role 05/06 contract, bilingual parity, explicit null reasons, stale-response handling).
