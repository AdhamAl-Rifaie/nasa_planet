# NASA Planet - Trend Detective

Team reference for **What the Average Hides**: investigate Earth-system trends, test sensitivity to period and location, and export reproducible evidence.

## Start here

- [Team entry point](docs/START_HERE.md)
- [Architecture, scope, six-person responsibilities and delivery plan](docs/architecture/PLAN.md)
- [Implementation specification: components, API, jobs, science, RAG and verification](docs/architecture/IMPLEMENTATION.md)
- [Machine-readable target scope](docs/architecture/scope.v2.json)
- [Data guide](data/nasa/README.md)
- [Verified measurements and validation report](data/nasa/validation_report.json)

## Delivered versus planned

**Delivered:** temperature (MERRA-2) and soil moisture (GLDAS) for the Egypt bounding rectangle, monthly January 2001 through December 2024. Includes 576 monthly regional subsets, two combined NetCDF cubes, browser JSON, source lineage, official documentation and a 315-chunk RAG starter.

**Target:** four variables (temperature, precipitation, soil moisture, vegetation greenness) across Nile, Morocco and Sahel study windows. Precipitation, vegetation/QA and additional geographic coverage are not included yet. The full application and validated statistics pipeline remain implementation work.

Data-ingestion readiness is not scientific-method or application readiness. Follow the separate readiness gates in the architecture.

## Repository map

```text
docs/START_HERE.md             Reading order and current delivery status
docs/architecture/            Plan, implementation contracts and target scope
data/nasa/measurements/       Actual regional source subsets and combined cubes
data/nasa/frontend/           Browser-friendly values, coordinates and units
data/nasa/rag/                Cited corpus, retrieval baseline and AI contract
data/nasa/docs/               NASA product guides
data/nasa/methods/            Software-method documentation
data/nasa/manifests/          NASA granule inventories
data/nasa/source_lineage.json Per-month source IDs and file hashes
```

## Quick start

For dependency-free retrieval:

```bash
python data/nasa/rag/retrieve.py "soil moisture"
```

For numerical work, install the pinned dependencies in a virtual environment:

```bash
python -m venv .venv
# Activate the environment for your shell, then:
python -m pip install -r data/nasa/requirements.txt
```

```python
import xarray as xr

ds = xr.open_dataset("data/nasa/measurements/M2TMNXSLV_Egypt_2001_2024.nc")
temperature_c = ds["T2M"] - 273.15
```

Reading the bundled measurements does not require Earthdata credentials. Re-downloading does; use only the local interactive login. Never commit credentials or tokens.

## Source attribution and limitations

Source URLs, product versions and hashes are preserved in the data bundle and architecture. Temperature is reanalysis and soil moisture is model output; neither is a direct station observation. The rectangle includes adjacent areas and sea and is not a national boundary mask. Different products retain different native grids. Missing values are not zeros.

Official source documents retain their original attribution and applicable terms; this repository does not assign a new blanket license to third-party content. No statistical or causal conclusions are implied by the downloaded data.
