# Team reference: Trend Detective

Read in order:

1. [Architecture and six-person plan](architecture/PLAN.md).
2. [Implementation specification](architecture/IMPLEMENTATION.md).
3. [Machine-readable target scope](architecture/scope.v2.json).
4. [Verified existing data](../data/nasa/README.md).
5. [Data validation report](../data/nasa/validation_report.json).

The target is four variables across three study windows, 2001-2024. Delivered measurements currently cover **temperature and soil moisture for the Egypt rectangle only**. GPM precipitation, MODIS NDVI/QA and the Morocco/Sahel extensions are planned, not downloaded. Never present planned scope as available functionality.

Existing data: 576 monthly regional files, two combined NetCDF cubes, frontend JSON, provenance, official source documents and a 315-chunk RAG starter. See data/nasa/runtime_catalog.json for source-ingestion readiness, not proof of a validated statistics service.

No application files are implemented by this documentation/data delivery. The project plan governs future work; adapt proposed module paths to the repository's established structure.
