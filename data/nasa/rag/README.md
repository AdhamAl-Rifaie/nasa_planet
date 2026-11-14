# NASA RAG starter — actual downloaded sources

## What is here
- `sources/M2TMNXSLV.json`: official NASA CMR metadata, MERRA-2 monthly single-level collection v5.12.4.
- `sources/GLDAS_NOAH025_M.json`: official NASA CMR metadata, GLDAS Noah monthly collection v2.1.
- `corpus.jsonl`: real abstracts and coverage metadata extracted from those two responses, with source URLs, timestamps, versions and SHA-256 hashes. These are documentation, NOT measurements. Fixed 1,400-character segments are a baseline; improve semantic chunking before production.
- `catalog.json`: candidate products, candidate variable names and official related links. `analysis_ready` is FALSE: downloading metadata does not make a dataset ready for analysis. Variable definitions/units must be checked against file metadata before ingestion.
- `sources/POWER_Cairo_monthly.json`: actual NASA POWER numeric API response for Cairo coordinates (30.0444 N, 31.2357 E), monthly T2M, 2001–2024.
- `cairo_temperature_monthly.csv`: 288 monthly values extracted from that response; annual summaries (month 13) excluded. Unit is copied from the API metadata.
- `sample_provenance.json`: exact API URL, response metadata and checksum. POWER is a separate sample access path, not proof that the selected MERRA-2/GLDAS gridded files have been ingested. A point request represents the corresponding source grid cell, not a station observation or citywide average.
- `retrieve.py`: offline BM25-style lexical retrieval baseline with a small manually authored Arabic query-expansion dictionary. The Arabic aliases are project code, not NASA-authored content. No LLM, embeddings or external packages required.

## Run now
Install Python 3, open a terminal in this folder:

    python retrieve.py "soil moisture"
    python retrieve.py "هل الدلتا بتسخن؟"
    python retrieve.py "رطوبة التربة"

The output contains real retrieved passages and source links. An unsupported question can return an empty result. The dictionary is small: this is not comprehensive Arabic semantic search. Inspect retrieved passages before treating them as answers.

## Connect your AI
1. Call `retrieve(question)` from Python.
2. Pass only returned passages and their chunk IDs to your model.
3. Require JSON fields: answer, cited_chunk_ids, suggested_product_ids, limitations.
4. Validate every cited ID against returned chunks; reject unsupported citations.
5. Restrict suggested products to the runtime AVAILABLE catalog. In this starter both gridded candidates are pending, so suggest them only as data acquisition candidates, never as analyses ready to run.
6. For numerical questions, call the statistics service. Supply its actual result and receipt ID to the model; never ask the language model to invent a slope, significance, time coverage or causal explanation.
7. If evidence is missing, say so. Neither collection abstract proves a trend in Cairo or the Nile Delta.

Suggested system rule:
"Use supplied evidence only. Cite valid chunk IDs for factual source claims. Distinguish reanalysis/model outputs from observations. Do not infer causal explanations or numerical trends from documentation. Do not claim candidate datasets are available. Statistics must come from the separate analysis result, not your own computation. If unsupported, state the missing evidence."

## What the data engineer must still deliver
The main application's Reveal map requires a real time × latitude × longitude cube, not this point CSV. Download a bounded regional subset from the exact product version, commonly using an Earthdata account; inspect actual variable names, units, missing-value flags and dates; harmonize grids only with an explicit documented method; save the cube and its provenance. Only then set the corresponding runtime variable to analysis_ready=true.

MERRA-2 candidate: T2M, near-surface air temperature, reanalysis.
GLDAS candidate: SoilMoi0_10cm_inst, top-layer soil moisture, land-surface model output.
Do not conflate air temperature with land surface temperature, or soil moisture with relative humidity.

The POWER CSV is enough to exercise ingestion, plots and deterministic statistics for one sample location. It cannot validate a regional trend or the spatial-reveal feature.

## Scope and validation
This is a small provenance-preserving starter corpus, not a complete scientific knowledge base. Add official variable/file specifications, product limitations and independently reviewed method documentation next. `validation.json` records checks actually run on these files. No model-generated answer quality, production RAG evaluation or gridded science pipeline has been tested.

Also included: sources/README_GLDAS2.pdf, the official NASA GLDAS guide, with extracted page-tagged passages in corpus.jsonl. It covers multiple products/versions: verify applicability to v2.1. Generic temperature questions can retrieve GLDAS as well as MERRA-2; ask whether air or surface temperature is intended before variable selection.
