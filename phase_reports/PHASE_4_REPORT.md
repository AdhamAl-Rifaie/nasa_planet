# PHASE 4 REPORT - Deterministic Interactive Conclusion Templates

- **Phase:** 4 - Interactive conclusion templates
- **Status:** DONE
- **Date:** 15 November 2026
- **Implementation revision:** role04_phase4_v1
- **Executor:** Role 04 (Senior AI & RAG Engineer)

## Ground truth and scope

Implemented per `AGENT_BRIEF.md` §8 and §10 Phase 4 and `docs/architecture/IMPLEMENTATION.md` (canonical result fields: result/request identity, state, units, counts, coverage, slope, permitted uncertainty fields, artifact references, receipt_id; §8 action names `FOCUS_REGION`, `FOCUS_REGIONAL_CHART`, `REVEAL_CELLS`, `OPEN_SPIN_IT`, `OPEN_RECEIPT` treated as pending Role 05/06 confirmation — comparison actions are NOT invented). Phase 3 was independently audited and approved before starting.

## Implementation — `packages/rag/conclusions.py`

| Component | Content |
|---|---|
| `validate_payload()` | Strict server-side validation of the verified result payload before any rendering: required fields (`analysis_id`, `request_id`, `region_id`, `variable_id`, `period`, `units`, `product`, `regional`); canonical variable/region membership; strict types (numbers are numbers, not strings/bools); `result_state` ∈ {succeeded, insufficient_data, failed}; product identity with **source-type guard** (a payload claiming `source_type: "satellite"` for MERRA-2 is rejected — the renderer derives reanalysis/land-surface/satellite-retrieval wording from the registry mapping itself, never from the caller); `sen_slope` requires `slope_units`; `p_value` requires `significance_alpha`; null `p_value` requires a known `inference_reason_code` (insufficient_sample_size, all_cells_masked, zero_variance, method_not_applicable, inference_not_released); CI low ≤ high; cell-count consistency (eligible + ineligible = total; significant cells ≤ eligible); coverage fraction ∈ [0,1]; sensitivity matching ≤ total; unknown comparison action names rejected. |
| `render_conclusions(payload, language, tracker=None)` | **Zero-LLM deterministic renderer.** No LLM call, no LLM dependency anywhere; `mode: "conclusion_templates"`. Renders a **dynamic** segment list — segments exist only when their data exists: `context`, `regional_trend`, `cell_evidence`, `qa_coverage`, `sensitivity` (only when Spin-It artifact enabled), `comparison` (only when comparison data attached), `provenance` (only when receipt artifact + receipt_id). Non-succeeded states render an explicit bilingual reason message with **no numbers** and no segments. Arabic/English parity: identical segment ids, identical numeric tokens (test-verified set equality). |
| Number formatting | `_fmt()` (≤3 decimals, trailing-zero-stripped) and `_pct()` (1 decimal) — every statistical value (mean, Sen's slope, p, alpha, CI bounds, counts, percentages, window counts) is formatted deterministically from the payload; nothing is generated, rounded twice, or invented. Slope sign selects increase/decrease wording. |
| Scientific wording (brief §7 + tasking) | Non-significant (p ≥ α): "insufficient statistical evidence for a trend under the declared method" / "الأدلة الإحصائية غير كافية على وجود اتجاه عام وفق المنهجية المعلنة", slope reported as effect size only; the words stable/unchanged/no change/ثابت/مستقر never appear (test-scanned). Cells: "show statistical evidence of increase/decrease under the declared method" / "تُظهر أدلة إحصائية على زيادة/انخفاض وفق المنهجية المعلنة" — never "truly increasing/decreasing". Every share states its denominator ("of eligible cells: 200 of 950" / "من الخلايا المؤهلة: 200 من 950"; or weighted-AOI-area shares) and explicitly reports ineligible QA cells ("10 ineligible cells were excluded by quality screening"). MERRA-2/GLDAS always labeled "reanalysis product / land-surface model output, not direct satellite observations". Sensitivity is "a descriptive sensitivity summary, not a probability that any claim is true". |
| Null handling | When `p_value`/`sen_slope`/CI are null, `inference_reason_code` maps to a bilingual human sentence ("Inference was not computed: the sample is too small to support a trend test…"); descriptive stats (mean, n_months, coverage) remain visible; the literal strings None/null/NaN can never appear in user text (renderer never stringifies nulls; word-boundary test scans). |
| Actions | Each segment binds `analysis_id`/`request_id` plus permitted action objects `{action, analysis_id, request_id, target}`: FOCUS_REGION (context, target region_id), FOCUS_REGIONAL_CHART (regional trend, when artifact true), REVEAL_CELLS (cells, when artifact true), OPEN_SPIN_IT (sensitivity, when artifact true), OPEN_RECEIPT (provenance, when receipt artifact true). Unavailable artifacts ⇒ segment and action are **hidden entirely** (never emitted broken). Comparison segments carry no frontend action and an explicit `action_pending_contract: true` marker until Role 05/06 confirm the enum; an unrecognized comparison action name is a payload error. |
| `ActiveRequestTracker` | Deterministic session guard: `register(analysis_id, request_id, region_id, variable_ids, period)` keeps the current identity; `validate(payload)` rejects anything else: period/region/variable change on the active request → `stale_response: … changed`; a previously registered request_id → `superseded by a newer request`; unknown ids → `unknown request for the active session`. `render_conclusions(..., tracker=…)` returns a structured `stale_response` rejection (empty segments/actions) instead of stale conclusions. |

## Files created/changed

- `packages/rag/conclusions.py` (new)
- `tests/test_phase4_conclusions.py` (new, 31 tests)
- `PROGRESS.md`

## Commands run and outcomes

| Command | Outcome |
|---|---|
| `python -m pytest tests -q` (full suite Phase 1+2+3+4) | **PASS — 147 passed, 0 failed** (47 Phase 1 + 33 Phase 2 + 36 Phase 3 + 31 Phase 4) |
| `python -m pytest tests/test_phase4_conclusions.py -q` | **PASS — 31 passed** (isolated) |

Note: the Phase 3 test file now collects 36 tests (an additional markdown-fence prose test was introduced during the Phase 3 audit); 47+33+36+31 = 147 matches the full-suite total.

## Adversarial coverage mapped to tasking requirements

| Requirement | Tests |
|---|---|
| Numeric fidelity + bilingual parity, all 4 variables | `test_bilingual_parity_across_all_four_variables` (×4, numeric-token set equality), `test_numbers_come_from_payload_verbatim` (×4), `test_confidence_interval_rendered_when_significant` |
| Non-significance wording, banned stable/ثابت/مستقر | `test_non_significant_trend_wording` + banned scan in every rendering test |
| Cell evidence wording, no "truly increasing/decreasing" | cells assertions in `test_numbers_come_from_payload_verbatim`, "truly" in banned scan |
| Explicit denominators + ineligible QA reporting | `test_denominator_labels_and_qa_reporting`, `test_weighted_area_cell_denominator_supported` |
| Dataset nature distinction (reanalysis/model vs satellite) | `test_dataset_nature_distinction`, `test_payload_source_type_mismatch_rejected` |
| Null inferential fields + reason codes, descriptive survives, no None/null/NaN | `test_null_inference_keeps_descriptive_stats_and_maps_reason` (×5 reasons), `test_output_json_contains_no_null_literals_in_user_text` |
| Dynamic segments + hidden unavailable actions | `test_dynamic_segments_with_full_artifacts`, `test_unavailable_artifacts_hide_actions_and_segments` |
| Action binding + permitted enums + comparison pending contract | `test_actions_bound_to_active_ids_and_permitted_enums`, `test_comparison_data_renders_segment_without_invented_action`, `test_unrecognized_comparison_action_rejected` |
| Stale response protection | `test_stale_response_on_period_change`, `test_stale_response_on_region_change`, `test_stale_response_on_unknown_request_id`, `test_re_registration_supersedes_old_response`, `test_tracker_accepts_current_request` |
| Non-succeeded result states | `test_insufficient_data_state_renders_no_numbers` |
| Payload integrity | `test_unknown_variable_and_missing_fields_rejected`, `test_inconsistent_cell_counts_rejected`, `test_receipt_flag_without_receipt_id_rejected`, `test_unsupported_language_rejected` |

## Defects found and fixed during Phase 4

1. Alpha formatting collapsed `0.05` to `0` (0-decimal formatting) — alpha now formatted with 2 decimals in both languages; caught by the CI/significance fidelity test.
2. A PowerShell `Get-Content | Set-Content -Encoding utf8` round-trip corrupted the Arabic strings in `conclusions.py` (mojibake) — file rewritten cleanly via the write tool; Arabic correctness now protected by exact Arabic-substring assertions in the test suite. (Tooling lesson recorded: never rewrite source files through PowerShell text pipelines on this machine.)

## Honest scope notes (not claimed)

- The renderer consumes the result-payload contract designed here from IMPLEMENTATION.md concepts; Role 03's actual API schemas do not exist in the repository yet, so field names must be reconciled with Role 03 before `/v1/explanations` integration (Phase 5). No endpoint is implemented — this is the Role 04 rendering engine.
- Comparison segments render evidence text with no frontend action; the comparison action enum remains pending the Role 05/06 contract (nothing invented).
- Numbers come from the verified payload only; the renderer trusts the payload's numbers as Role 02/03 output and does not recompute statistics (no competing statistics engine, per brief §2).
- Spin It sensitivity wording assumes the payload supplies window counts; the underlying Spin It computation belongs to Role 02/06.

## Next phase

Phase 5 — integrated evaluation and presentation: real-data path question → analysis → evidence → receipt, network/LLM-disabled mode, secrets exclusion, receipt/result consistency, honest AI-use disclosure and delivered-vs-planned scope reporting.
