# Statistics workspace

Work branch: `codex/ml-statistics`, based on `origin/main` at
`ecf39088744c7ea01ae7d30d92e5ce6b91d24f6d`.

Read the revised `ML_STATISTICS_AGENT.md`, [PLAN.md](PLAN.md), this directory's
`PROGRESS.md`, and its latest phase report at the start of a statistics session.
The repository-root `AGENT_BRIEF.md` and `PROGRESS.md` belong to Role 04 (RAG).
The statistics brief and plan were revised under the user's 15 November request
to use the actual data. The original brief/report remain in Git history.

Phases 1 and 2 have passed their implementation checks. Stage 2 prepares all
twelve variable-region pairs; its candidate QA/support policy awaits owner
review. Existing inference code on another branch still needs review/repairs;
backend schema sign-off is deferred to the integration phase.

Install the input/exploration dependencies in a repository-local environment:

```powershell
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r packages/science/requirements.txt
.\.venv\Scripts\python.exe -m unittest discover -s packages/science/tests -v
.\.venv\Scripts\python.exe tools/audit_science_inputs.py --output data/derived/input-audit.json
.\.venv\Scripts\python.exe tools/run_science_exploration.py
.\.venv\Scripts\python.exe tools/probe_existing_statistics.py --output data/derived/existing-method-probes.json
```

The combined input/preparation suite has **37 tests** (16 earlier input checks
plus 21 Stage 2 checks). The current input audit passes all twelve field/unit
contracts. The inherited-method probe intentionally still exits **1**
for the two uncorrected regression cases in its pinned historical commit. It
does not test a repaired engine. Neither audit/probe edits source measurements.

Explore [notebooks/01_exploration.ipynb](notebooks/01_exploration.ipynb). It writes
a map/cell-series image to `data/derived/science/phase_1/` and a provenance
summary to `phase_reports/PHASE_1_INPUT_METADATA.json`. This is descriptive input
exploration, with GPM ancillary fields retained and no additional quality-index
cutoff; regional aggregation, product QA policy and inference are later gates.

See [the plan-alignment report](phase_reports/PHASE_0_REPLAN_REPORT.md) and
[Phase 1 report](phase_reports/PHASE_1_REPORT.md) for evidence and remaining work.
The [original Phase 0 report](phase_reports/PHASE_0_REPORT.md) remains historical.

## Stage 2 reproduction

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s packages/science/tests -v
.\.venv\Scripts\python.exe tools/prepare_science_inputs.py
.\.venv\Scripts\python.exe tools/prepare_science_inputs.py --variable-id vegetation_greenness --modis-mode standard --output-dir data/derived/science/phase_2_standard --coverage-report packages/science/phase_reports/PHASE_2_QA_SENSITIVITY.json
.\.venv\Scripts\python.exe tools/validate_prepared_inputs.py
.\.venv\Scripts\python.exe tools/run_science_preprocessing.py
```

[The policy](config/preparation_policy.json) defaults to strict MODIS QA and
fixed complete-reference support. Centre-selected full native cells receive
spherical area weights; this is not exact polygon intersection. The source
cubes and readiness flags remain unchanged. Annual summaries require all twelve
months. Cell masks, coverage, source rates/QA, monthly/annual series and
fixed-reference anomalies are preserved in ignored `data/derived/science/phase_2/`.
Downstream estimators must select `cell_monthly` or `regional_monthly`
explicitly. `qa_monthly` is a diagnostic before fixed-support exclusion;
ancillary QA/error fields are not interchangeable with the analysis series.

Open [02_preprocessing.ipynb](notebooks/02_preprocessing.ipynb),
[the coverage report](phase_reports/PHASE_2_COVERAGE.json),
[QA sensitivity results](phase_reports/PHASE_2_QA_SENSITIVITY.json), and
[the Stage 2 report](phase_reports/PHASE_2_REPORT.md).
Strict complete-period support retains only 14.69% of selected native-cell area
for Sahel NDVI; the standard comparison retains 82.59% but admits marginal data.
Owner review is pending; no slopes or inferential claims are produced here.
