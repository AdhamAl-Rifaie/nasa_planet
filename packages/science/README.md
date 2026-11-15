# Statistics workspace

Work branch: `codex/ml-statistics`, based on `origin/main` at
`ecf39088744c7ea01ae7d30d92e5ce6b91d24f6d`.

Read the revised `ML_STATISTICS_AGENT.md`, [PLAN.md](PLAN.md), this directory's
`PROGRESS.md`, and its latest phase report at the start of a statistics session.
The repository-root `AGENT_BRIEF.md` and `PROGRESS.md` belong to Role 04 (RAG).
The statistics brief and plan were revised under the user's 15 November request
to use the actual data. The original brief/report remain in Git history.

The input mapping is resolved and Phase 1 input exploration has passed its
checkpoint checks. Existing inference code on another branch still needs
review/repairs; backend schema sign-off is deferred to the integration phase.

Install the input/exploration dependencies in a repository-local environment:

```powershell
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r packages/science/requirements.txt
.\.venv\Scripts\python.exe -m unittest discover -s packages/science/tests -v
.\.venv\Scripts\python.exe tools/audit_science_inputs.py --output data/derived/input-audit.json
.\.venv\Scripts\python.exe tools/run_science_exploration.py
.\.venv\Scripts\python.exe tools/probe_existing_statistics.py --output data/derived/existing-method-probes.json
```

The input suite has **16 tests**, and the current input audit passes all twelve
field/unit contracts. The inherited-method probe intentionally still exits **1**
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
