# Statistics workspace

Work branch: `codex/ml-statistics`, based on `origin/main` at
`ecf39088744c7ea01ae7d30d92e5ce6b91d24f6d`.

Read `ML_STATISTICS_AGENT.md`, this directory's `PROGRESS.md`, and its latest
phase report at the start of a statistics session. The repository-root
`AGENT_BRIEF.md` and `PROGRESS.md` belong to Role 04 (RAG); the user assigned
this workspace the separate ML/statistics brief. A copy is retained here with
trailing whitespace normalized and its instructions preserved. Paths in that brief are adapted to the
repository's documented `packages/science/` ownership boundary.

Phase 0 is blocked by recorded source-field and integration-contract issues.
An existing statistics implementation was discovered on another branch; it
must be reviewed rather than independently reimplemented or treated as validated.

Install the audit dependencies in a repository-local virtual environment:

```powershell
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r packages/science/requirements-audit.txt
.\.venv\Scripts\python.exe tools/audit_science_inputs.py --output packages/science/phase_reports/input_audit.json
.\.venv\Scripts\python.exe tools/probe_existing_statistics.py --output packages/science/phase_reports/existing_method_probes.json
```

Both checks currently exit **1** because they reproduce documented problems:
three catalog/source-field mismatches and two failed synthetic method invariants.
Neither script edits measurements, readiness flags or the reviewed branch.
The probes use the exact recorded commit, not a moving branch tip.

See [Phase 0 report](phase_reports/PHASE_0_REPORT.md) for the contract table,
observations, open decisions and next steps. No new statistical method or
inference release has been approved by this audit.
