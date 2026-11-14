# Trend Detective: verified project data pack

Scope: two variables, monthly January 2001–December 2024, bounding rectangle 24–36 E and 22–32 N. This is a geographic rectangle around Egypt, not a national-boundary mask. Includes adjacent land and sea. Both source grids are retained separately.

## Start here
- measurements/M2TMNXSLV_Egypt_2001_2024.nc — actual 288-month air-temperature cube, T2M, kelvin. Subtract 273.15 to display Celsius; temperature-change units are numerically identical.
- measurements/GLDAS_NOAH025_M_Egypt_2001_2024.nc — actual 288-month upper-soil-moisture cube, SoilMoi0_10cm_inst, kg m-2. Not a percentage.
- measurements/<product>/<month>.nc — all 576 individual regional subsets with source-granule attribution.
- frontend/T2M.json and frontend/SoilMoi0_10cm_inst.json — identical values in a browser-friendly format with explicit dimension order and nulls for missing data. Do not treat nulls as zeros.
- runtime_catalog.json — actual validated availability for your application and AI.
- validation_report.json — tests on every month, units, dimensions, missing data, native coordinates and file hashes. This verifies ingestion, not scientific trend conclusions.
- source_lineage.json and manifests/ — source inventory and local hashes for every month.
- rag/corpus.jsonl — official product and method-documentation chunks with citations. NASA source docs in rag/sources/ and docs/; software-method docs in methods/.
- rag/retrieve.py — minimal offline lexical retrieval; Arabic aliases are limited. This is not a finished or evaluated production RAG system.
- rag/AI_CONTRACT.md and rag/evaluation_questions.json — project-authored behavior requirements and an unexecuted model-evaluation set.
- rag/cairo_temperature_monthly.csv — separate NASA POWER point sample; do not use it as the regional cube or conflate its Celsius units with MERRA-2 kelvin.

## Python example
    import xarray as xr
    ds = xr.open_dataset("measurements/M2TMNXSLV_Egypt_2001_2024.nc")
    temperature_c = ds["T2M"] - 273.15

## Re-download
Install requirements.txt. Run download_recoverable.py in this directory. Enter Earthdata credentials only in its local terminal. Existing monthly files are reused. regional_worker.py contains the regional selection and the GLDAS ancillary-variable workaround. Credentials stay in memory. No passwords or tokens are included in this pack.

## Scope limits
This is the complete numeric source dataset for the stated two-variable, one-domain, 24-year scope, not all NASA data. There are no rainfall, NO2, global, neighborhood-level or administrative-boundary datasets here. Land-only model output has masked cells; use the validation report. Spatial coverage is limited to grid-cell centers inside the rectangle. Source model/reanalysis errors remain; ingestion checks do not prove physical truth.

The RAG corpus is a bounded set of official product and software documents, not an exhaustive scientific literature review. Product versions and source URLs are recorded; verify passage applicability because some guides cover multiple versions. The starter retrieval tests are historical and do not certify the expanded corpus. Statistical outputs (anomalies, slopes, uncertainty, significance, FDR, period-sensitivity matrices, evidence receipts) are computed later from these actual cubes. They are not downloaded facts, and no statistical or causal conclusions have been fabricated here. RAG answer quality remains to be evaluated with your chosen model.

Do not read the original rag/README.md as the final data-availability state; this README and runtime_catalog.json supersede it.
