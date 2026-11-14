# PROGRESS — Role 04 (RAG & Conclusion)

> Read this file at the START of every session. Update it at the END of every phase.
> Each finished phase also gets its own `phase_reports/PHASE_<N>_REPORT.md`.
> Do not redo anything marked DONE unless a regression test fails (say so explicitly).

## Current status
- **Current phase:** NOT STARTED
- **Waiting for user permission to start:** Phase 1
- **Last updated:** —

## Inputs still needed from the user (ask before Phase 1)
- [ ] Team's written plan (chat cites pp. 9, 15, 18, 19)
- [ ] Role 01 `catalog.json` + real variable ids
- [ ] Role 06 final `ALLOWED_ACTIONS` + the fifth conclusion segment
- [ ] Role 02/03 real result field names
- [ ] The two loaded variables + NASA product/version for each
- [ ] Can the agent reach official NASA pages? (else: who pastes the text)
- [ ] Final LLM provider/model + key storage

## Phase tracker
| Phase | Name | Status | Tests passed | Report file | Approved by user to continue |
|---|---|---|---|---|---|
| 1 | Corpus setup & contract lock | NOT STARTED | 0/4 | — | — |
| 2 | BM25 retrieval & bilingual search | NOT STARTED | 0/4 | — | — |
| 3 | LLM recommendation & validation | NOT STARTED | 0/7 | — | — |
| 4 | Interactive conclusion templates | NOT STARTED | 0/6 | — | — |
| 5 | Final evaluation, disclosure & pitch | NOT STARTED | 0/5 | — | — |

Status values: NOT STARTED / IN PROGRESS / DONE (waiting for approval) / APPROVED.

## Open problems (max 3 fix attempts per problem, then stop and report)
| # | Phase | Problem | Attempts | Status |
|---|---|---|---|---|
| — | — | — | — | — |

## Unverified claims (do NOT rely on these until sourced or measured)
- "Mistral is one of the strongest models for Arabic" — unverified; measure it.
- "mistral-small-latest answers in about 1 second" — unverified; measure it.
- Mistral model names / `response_format` / `client.chat.parse` details — check official docs.
- Corpus size "< 50 KB", "reads in < 1 ms", "retrieval in 0.001 s" — estimates only.
- Candidate variables/products from the chat (GPM, MERRA-2, GLDAS soil moisture, MODIS NDVI, OMI NO2, ozone, evaporation) — verify each against official NASA pages.
- Anything else taken from the design chat without an official source.

## Open questions from the design chat (resolve with the user)
- Allowed actions: the chat lists `FOCUS_REGION`, `FOCUS_REGIONAL_CHART`, `REVEAL_CELLS`, `OPEN_SPIN_IT`, `OPEN_RECEIPT`, but its example sentence only uses 4 of them (segment 1 uses `FOCUS_REGIONAL_CHART`). Use only the list Role 06 confirms.
- The conclusion is "5 segments" but the chat example shows 4 → the fifth is unknown.
- Variable id: the chat uses `gpm_precipitation` as the example id; `precipitation_gpm` and `gpm_imerg_precip` appear only as examples of a *mismatch*. The real id = Role 01's catalog.
- Result field names (`evidence_state`, `baseline_period`, `analysis_id`, `p_value`, `confidence_interval`, …) are from the chat — confirm with Role 02/03.
- Which tests are from the chat vs added: see AGENT_BRIEF.md section 5.

## Phase log
<!-- Append one entry per finished phase, newest last. Full details go in phase_reports/ -->

### Phase X — <name>
- Date/time:
- Short summary:
- Report file: phase_reports/PHASE_X_REPORT.md
- Tests: x/y passed
- Open problems:
- Arabic summary sent to user: yes/no
- User approval to continue: pending
