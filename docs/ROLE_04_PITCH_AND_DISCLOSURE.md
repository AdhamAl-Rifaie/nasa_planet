# Role 04 — RAG & Conclusions: Pitch and Honest AI-Use Disclosure

**NASA Space Apps 2026 — "Trend Detective — What the Average Hides"**

This document is written for judges and teammates. It states exactly what Role 04
delivers, how AI tools and AI models are used, and how to demo the work live.

---

## 1. What Role 04 Delivers (EN)

Role 04 is the "answer and explain" layer of the app. It sits between the data
pipeline (Roles 01–03) and the interactive UI (Roles 05–06) and provides two
capabilities through one entrypoint (`packages/rag/facade.py`, class
`Role04Service`):

### 1.1 Concept & variable Q&A (documentation path)
- A **deterministic bilingual retriever** (BM25 over a curated semantic corpus
  of 469 chunks: MERRA-2, GLDAS, IMERG/GPM, MODIS documentation) that answers
  user questions such as "هل الدلتا بتسخن؟" by identifying the closest
  **documented variable** and returning the product, version, data revision,
  and clickable citations with SHA-256 content hashes.
- **Measurement vs. app honesty**: the retriever can only claim what the
  documentation claims. Today's state is `documented_only` /
  `measurement_ready_app_not_available` — "the measurement is available in the
  source dataset; our app does not yet serve it for that period." No invented
  numbers, ever.
- **Optional, validated LLM explanations**: when a server-side Gemini key is
  configured, one short explanation is drafted and then forced through a
  **zero-trust validator** (numbers must match retrieved values; no
  quantitative claims beyond the corpus; no causal wording). If the key is
  missing, the same flow completes offline with identical citations
  (`local_retrieval` fallback). The app never requires the LLM.

### 1.2 Statistical conclusions (interactive results path)
- **Deterministic bilingual templates** (English + Egyptian Arabic) that
  translate Role 03's statistical payload into judge-readable sentences:
  regional mean, Sen's slope, Mann-Kendall p-value, confidence interval,
  cell-level counts with explicit denominators, and QA coverage.
- **Wording discipline is enforced by code and tests**: a non-significant
  result is always "insufficient statistical evidence for a trend"
  (Arabic: "الأدلة الإحصائية غير كافية على وجود اتجاه عام") — never "stable" or
  "unchanged". Cells that pass significance "show statistical evidence of
  increase/decrease under the declared method". Reanalysis products are never
  called "satellite" data.
- **Stale-response protection**: an `ActiveRequestTracker` rejects any result
  that does not match the currently registered analysis (superseded requests,
  changed region/variable/period), so the UI can never narrate numbers from an
  older query.

### 1.3 The "What the average hides" cell evidence
The conclusion templates expose exactly the theme's core message: a regional
trend and its p-value can hide a heterogeneous reality. The templates always
report **cells** (e.g., "200 of 950 eligible cells show statistical evidence of
increase…; 710 cells show insufficient evidence") alongside the regional
result, with explicit denominators and eligible-cell vs. weighted-area
distinction.

---

## 2. Honest AI-Use Disclosure (EN)

We use AI in two clearly separated ways, and we disclose both:

### 2.1 AI assistance while building the app (development-time)
Generative AI coding assistants were used to help draft code, tests, and
documentation for this project. **All code, tests, and scientific wording were
reviewed, corrected, and verified by the team.** In particular:
- All statistical interpretation wording was fixed by us, in both languages,
  and is enforced by tests (`packages/rag/conclusions.py`,
  `tests/test_phase4_conclusions.py`), not by AI judgment at runtime.
- No AI tool ran our science pipeline decisions; the pipeline is deterministic
  Python over documented NASA/GPM/GLDAS/MODIS products.

### 2.2 AI inside the app (runtime)
- **Gemini (`gemini-2.5-flash`) is optional** and is used only to phrase short
  explanations over already-retrieved documentation chunks.
- The model output is never trusted: a **zero-trust validator** re-checks every
  number and wording constraint; on any failure the app silently falls back to
  the deterministic retrieval answer.
- **No API key ships with the code.** Keys live in a server-side `.env`
  (git-ignored; `.env.example` is empty). A repository-wide secrets audit test
  (`tests/test_phase5_e2e.py::test_repository_secrets_audit_no_keys_or_env_files`)
  scans every tracked file for key-like patterns on every test run.
- The LLM is given **only** the retrieved documentation chunks (no user data,
  no inference payloads).

### 2.3 What AI does NOT do in our app
- It does not compute trends, p-values, or confidence intervals (Roles 01–03
  deterministic pipeline does that).
- It does not decide what is "significant" — the declared method (Sen's slope +
  Mann-Kendall with Hamed–Rao correction, alpha = 0.05) decides.
- It never outputs numbers that were not retrieved from documentation or
  produced by the statistical pipeline.

---

## 3. ما نقدّمه (بالعربية) — ما تقوله لفريق التحكيم

الطريق الرابع هو طبقة "الإجابة والشرح" في التطبيق، وليها مسارين:

1. **مسار التوثيق (أسئلة المفاهيم):** بحث حتمي ثنائي اللغة (BM25) على مقتطفات
   موثقة من MERRA-2 و GLDAS و IMERG و MODIS، بيقترح أقرب متغير موثّق وبيرجّع
   الإجابة بمصادر قابلة للنقر (روابط + بصمة SHA-256 للمحتوى). لو مفيش مفتاح
   Gemini، الإجابة بتكمل أوفلاين بنفس المصادر (وضع `local_retrieval`).
2. **مسار النتائج التفاعلية:** قوالب جمل جاهزة ثنائية اللغة بتحوّل نتائج
   الإحصاء لجمل مفهومة: المتوسط الإقليمي، ميل Sen، قيمة Mann-Kendall الاحتمالية،
   فترة الثقة، وعدّاد الخلايا بمقامات معلنة. النتيجة غير الدالة بيتقال عندها
   حرفياً "الأدلة الإحصائية غير كافية على وجود اتجاه عام" — ممنوع نأكد استقرار
   أو عدم تغيّر. كمان الحماية من النتائج القديمة (ActiveRequestTracker) تمنع
   عرض أرقام من استعلام أقدم.

**الإفصاح عن استخدام الذكاء الاصطناعي:**
- وقت التطوير: استخدمنا مساعدين توليديين لصياغة الكود والاختبارات، وكل شيء
  مُراجَع ومُصحَّح ومُختبَر على ايدنا — والصياغة العلمية متثبتة باختبارات،
  مش بحكم موديل.
- داخل التطبيق: Gemini اختياري وباختصار بيصيغ شرح على مقاطع موثقة إحنا
  اللي جبناها، والمخرج بيتحقق منه بالكامل (Zero-Trust) ولو حصل أي مشكلة التطبيق بيرجع
  تلقائياً للإجابة الحتمية. مفيش أي API key جوه الكود، وفي اختبار بيفحص المستودع
  كله عن أي مفاتيح كل مرة.
- الذكاء الاصطناعي **مش** بيحسب اتجاهات ولا قيم احتمالية، ومش بيقرر الدلالة —
  ده شغل خط الإحصاء الحتمي. وأرقامه ممنوع تخرج غير من التوثيق أو من نتائج
  الإحصاء.

---

## 4. Delivered vs. Planned (Role 04 contract)

| Planned capability | Status | Where |
| --- | --- | --- |
| Provenance registry + canonical variables | Done | `packages/rag/source_index.py`, `id_mapping.py` |
| Bilingual BM25 retriever + Arabic normalizer | Done | `packages/rag/retriever.py`, `arabic.py`, `aliases.py` |
| Intent classification (period/region extraction, refusal paths) | Done | `packages/rag/intent.py` |
| Gemini provider (stdlib REST, no SDK, key-safe) | Done | `packages/rag/provider.py` |
| Zero-trust LLM validator + explanation pipeline | Done | `packages/rag/validator.py`, `explanation.py` |
| Deterministic bilingual conclusion templates | Done | `packages/rag/conclusions.py` |
| Stale-response protection | Done | `packages/rag/conclusions.py` (`ActiveRequestTracker`) |
| Unified E2E entrypoint + Role 03 payload adapter | Done (Phase 5) | `packages/rag/facade.py` |
| Evaluation question set (12 Q) end-to-end | Done (Phase 5) | `data/nasa/rag/evaluation_questions.json` + `tests/test_phase5_e2e.py` |
| Secrets audit on every test run | Done (Phase 5) | `tests/test_phase5_e2e.py` |
| Spin-It windows narrative — comparison actions | Template text done; **comparison action names pending Roles 05/06 sign-off** (contract §8) | `packages/rag/conclusions.py` (`COMPARISON_ACTIONS = set()`) |
| Real-time app availability flag | Honest `documented_only` / `measurement_ready_app_not_available` by design | `packages/rag/retriever.py` readiness lookup |

---

## 5. Integration Hooks (for Roles 01/02/03/05/06)

```python
from packages.rag.facade import Role04Service, normalize_result_payload

service = Role04Service()  # keyless-safe: offline local_retrieval mode

# Role 05/06 — concept Q&A (ar | en):
answer = service.answer_question("هل الدلتا بتسخن؟", region_id="nile_corridor", period=("2001-01", "2024-12"))
# answer["mode"] == "llm" | "local_retrieval"; answer["citations"] is always present.

# Role 03 — hand the raw result payload straight in (any documented alias form):
identity = service.register_analysis(raw_result_payload)   # arms stale guard
rendered = service.render_result(raw_result_payload, language="ar")  # or "en"
# rendered["segments"] -> [{id, text, actions:[{action, target}]}]

# Payload adapter (alias mapping lives in one place):
canonical = normalize_result_payload(role03_raw)  # IMPLEMENTATION.md <-> live payload

# Optional bounded live check (skips cleanly without a key):
probe = service.live_probe("هل الدلتا بتسخن؟")     # {"status": "skipped"} when keyless

# New session (user starts a new query round):
service.reset_session()
```

- **Role 03**: send the result payload as produced; the adapter accepts both
  `IMPLEMENTATION.md` canonical names and live aliases (`result_id`,
  `request_hash`, `start_month`/`end_month`, `slope`, `p`, `ci`,
  `cell_distribution`, `qa_coverage`, `spin_it_summary`, `availability_flags`).
- **Role 05/06**: only ever act on `actions[].action` inside
  `PERMITTED_ACTIONS = {focus_region, focus_regional_chart, reveal_cells,
  open_spin_it, open_receipt}`; show `segments[].text` verbatim (do not
  rewrite wording — the discipline is contractual).
- **Role 01/02**: to extend the corpus, add chunks to
  `data/nasa/rag/corpus_semantic.jsonl` (schema documented in
  `packages/rag/semantic_corpus.py`); the index rebuilds deterministically.

---

## 6. Two-Minute Pitch Script (EN)

> "Ask our app 'هل الدلتا بتسخن؟' — is the Delta heating up? Before showing any
> number, we show you the source: MERRA-2 2-meter air temperature, version
> 5.12.4, with a clickable link and a SHA-256 fingerprint of the exact
> documentation page. That's the detective's first rule: every claim has a
> receipt.
>
> When a trend analysis finishes, we don't just say 'the Delta warmed.' Our
> conclusion layer reads the statistics — Sen's slope, Mann-Kendall p-value,
> confidence interval — and says precisely what they support. And here is the
> theme: **the average hides.** A region can show a significant warming trend
> while 710 of 950 grid cells show insufficient evidence of any trend. Our UI
> always shows both: the regional sentence and the cell counts, with explicit
> denominators. If the evidence is weak, our app refuses to say 'stable' — it
> says 'insufficient statistical evidence for a trend.'
>
> And we use AI honestly: an optional Gemini call only phrases explanations
> over documentation we retrieved, checked by a validator that rejects any
> number we didn't produce. No key in the code, verified by a test on every
> run. The statistics are deterministic; the AI never decides what's true."

## النسخة العربية (مختصرة)

> "اسأل التطبيق: هل الدلتا بتسخن؟ قبل أي رقم هتشوف المصدر: MERRA-2 حرارة الهواء
> على ارتفاع 2 متر، بالإصدار واللينك والبصمة الرقمية للصفحة نفسها. ولما يخلص
> التحليل، التطبيق بيقول بالظبط اللي الإحصاء يقوله: ميل Sen وقيمة Mann-Kendall
> وفترة الثقة، وفوقهم عدّاد الخلايا بمقامات معلنة. دي فكرة التحدي: **المتوسط
> بيخفي** — ممكن إقليم يطلع له اتجاه دال والإغلبية العظمى من خلاياه ماعندهاش
> أدلة كافية. ولو الدليل ضعيف التطبيق مش هيقول 'ثابت' — هيقول 'الأدلة
> الإحصائية غير كافية على وجود اتجاه عام'. والذكاء الاصطناعي عندنا شفاف:
> اختياري، وبيتحقق منه بالكامل، والإحصاء حتمي بلا أي تدخل من موديل."

---

## 7. Live Demo Guide (step-by-step, offline-safe)

The full demo runs with **no API key and no network**. Run from the repo root:

```powershell
python -m pytest tests -q   # 170 tests, all green — say this out loud first
```

Then run the smoke sequence (same calls as
`tests/test_phase5_e2e.py::test_full_demo_sequence_smoke`):

```powershell
python -c "import sys; sys.stdout.reconfigure(encoding='utf-8'); from packages.rag.facade import Role04Service; s = Role04Service(); r = s.answer_question('هل الدلتا بتسخن؟', region_id='nile_corridor', period=('2001-01','2024-12')); print(r['mode'], r['status']); [print('-', c['chunk_id'], c['source_url']) for c in r['citations'][:4]]"
```

1. **Concept question** — the command above prints the mode
   (`local_retrieval`) and 4 citations with URLs. Point at the MERRA-2 link.
2. **Conclusion narration** — add a rendered result for the Nile corridor
   (fixtures identical to the tests): the Arabic segments read the regional
   sentence, the significant-increase sentence, the cell counts, the coverage,
   and the Spin-It windows — followed by the five permitted UI actions.
3. **Stale guard** — render the Morocco payload (a different request) and the
   tracker rejects the Nile payload as `stale_response`; the UI would refuse
   to narrate old numbers.
4. **Secrets hygiene** — show `.env.example` (empty `GEMINI_API_KEY=`) and the
   git-ignored `.env`; the audit test prints nothing because there is nothing
   to find.

**For judges with a key (optional):** set `GEMINI_API_KEY` in `.env` and run
`Role04Service().live_probe("هل الدلتا بتسخن؟")` — one bounded call
(8 s timeout, 1 retry), validated output, or an automatic fallback to the
deterministic answer.

---

## 8. Known Limits (disclosed to judges)

- The current readiness state for all 4 variables x 3 regions is
  `measurement_ready_app_not_available`: the sources document the measurements
  for 2001-01–2024-12, while the app's served result artifacts for those
  periods are not yet published by Roles 01–03 (the demo uses test fixtures
  for the conclusion path).
- Comparison/second-region narrative actions are stubbed empty
  (`COMPARISON_ACTIONS = set()`) pending Roles 05/06 sign-off on the exact
  action names (contract §8).
- Gemini explanations are English-drafted; Arabic explanation phrasing from
  the LLM path is not claimed — Arabic Q&A answers come from the deterministic
  templates.
