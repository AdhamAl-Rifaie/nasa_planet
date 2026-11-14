"""FastAPI application for Trend Detective.

Endpoints
    GET  /health
    GET  /v1/catalog
    GET  /v1/methods
    POST /v1/analyses
    GET  /v1/analyses/{job_id}
    GET  /v1/analyses/{job_id}/result
    GET  /v1/receipts/{receipt_id}

Contract rules enforced here:
- unsupported variable/region/period/AOI is rejected before a job is created,
- identical canonical requests return the same job (idempotent),
- a cached result is only reused for the same data_revision + method_revision,
- a failed job never exposes a result or a receipt.
"""
from __future__ import annotations

import json
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles

from . import (canonical, config, db, receipts, registry, schemas, worker)

from ai import explain as ai_explain
from ai import retrieve as ai_retrieve
from ai import validator as ai_validator
from .analysis_runner import AnalysisError


@asynccontextmanager
async def lifespan(app: FastAPI):
    config.ensure_dirs()
    db.init_db()
    reg = registry.load_registry()
    db.sync_catalog(reg.entries(), reg.revision)
    db.recover_stale_jobs()
    worker.start()
    try:
        yield
    finally:
        worker.stop()


app = FastAPI(title="Trend Detective API", version=config.SOFTWARE_REVISION,
              lifespan=lifespan)


def api_error(status: int, code: str, detail: str) -> JSONResponse:
    return JSONResponse(status_code=status,
                        content={"error": {"code": code, "detail": detail}})


def _job_response(job: dict, cached: bool = False) -> dict:
    return {
        "job_id": job["id"],
        "state": job["state"],
        "progress": job["progress"],
        "request_hash": job["request_hash"],
        "created_at": job["created_at"],
        "started_at": job["started_at"],
        "finished_at": job["finished_at"],
        "result_id": job["result_id"],
        "error": ({"code": job["error_code"], "detail": job["error_detail"]}
                  if job["error_code"] else None),
        "cached": cached,
    }


# ------------------------------------------------------------------ health

WEB_DIR = config.REPO_DIR / "web"
if WEB_DIR.exists():
    app.mount("/app", StaticFiles(directory=str(WEB_DIR), html=True),
              name="web")

PRODUCT_DIR = config.REPO_DIR / "dist" / "product"
if PRODUCT_DIR.exists():
    app.mount("/product", StaticFiles(directory=str(PRODUCT_DIR), html=True),
              name="product")


@app.get("/")
def root():
    return RedirectResponse(url="/product/" if PRODUCT_DIR.exists()
                            else "/app/landing.html")


@app.get("/health", response_model=schemas.HealthResponse)
def health():
    reg = registry.load_registry()
    con = db.connect()
    try:
        depth = con.execute(
            "SELECT COUNT(*) FROM jobs WHERE state IN ('queued','running')"
        ).fetchone()[0]
    finally:
        con.close()
    return {
        "status": "ok",
        "software_revision": config.SOFTWARE_REVISION,
        "data_revision": reg.revision,
        "method_revision": reg.method_revision,
        "database": str(config.DB_PATH),
        "queue_depth": int(depth),
    }


# ----------------------------------------------------------------- catalog

@app.get("/v1/catalog", response_model=schemas.CatalogResponse)
def catalog():
    reg = registry.load_registry()
    entries = []
    for e in reg.entries():
        entries.append({
            "variable_id": e["variable_id"],
            "region_id": e["region_id"],
            "product_id": e["product_id"],
            "version": e.get("version"),
            "units": e["units"],
            "label": e.get("label"),
            "bbox": e["bbox"],
            "native_grid": e.get("native_grid"),
            "measurement_ready": e["measurement_ready"],
            "method_ready": e["method_ready"],
            "app_available": e["app_available"],
            "method_revision": e["method_revision"],
            "source_kind": e.get("source_kind"),
            "limitations": e.get("limitations", []),
        })
    return {"data_revision": reg.revision,
            "method_revision": reg.method_revision,
            "entries": entries}


@app.get("/v1/methods", response_model=schemas.MethodResponse)
def methods():
    return registry.load_registry().method_summary()


# ---------------------------------------------------------------- analyses

@app.post("/v1/analyses", response_model=schemas.JobResponse, status_code=201)
def submit_analysis(payload: schemas.AnalysisRequest):
    reg = registry.load_registry()
    defaults = reg.defaults()

    # 1. region must exist
    bbox = reg.bbox_for(payload.region_id)
    if bbox is None:
        return api_error(400, "UNKNOWN_REGION",
                         f"region_id {payload.region_id!r} is not supported")

    # 2. every variable must be servable in that region
    entries = []
    for vid in payload.variable_ids:
        entry = reg.servable(vid, payload.region_id)
        if entry is None:
            known = reg.get(vid, payload.region_id)
            code = "UNAVAILABLE_SOURCE" if known else "UNSUPPORTED_VARIABLE"
            return api_error(
                400, code,
                f"{vid} is not available for {payload.region_id} "
                f"(measurement_ready and method_ready are required)")
        entries.append(entry)

    # 3. period must be real, ordered and inside the cube coverage
    try:
        months = canonical.month_range(payload.start_month, payload.end_month)
    except ValueError:
        return api_error(400, "INVALID_PERIOD",
                         "start_month must be <= end_month within 2001-01.."
                         "2024-12")
    if len(months) > 288:
        return api_error(400, "INVALID_PERIOD", "period exceeds the cube span")

    # 4. geometry, area and compute budget
    if payload.aoi:
        try:
            ring = canonical.normalize_aoi(payload.aoi)
        except ValueError as exc:
            code = str(exc)
            return api_error(400, code,
                             canonical.ERROR.get(code, "invalid geometry"))
        for entry in entries:
            try:
                canonical.check_area(ring, bbox, reg.cell_deg(entry))
            except ValueError as exc:
                code = str(exc)
                return api_error(400, code,
                                 canonical.ERROR.get(code, "invalid area"))
    if len(payload.variable_ids) > config.MAX_VARIABLES_PER_REQUEST:
        return api_error(400, "EXCESSIVE_COMPUTE",
                         f"at most {config.MAX_VARIABLES_PER_REQUEST} "
                         "variables per request")

    # 5. revisions must match what is installed
    if payload.method_revision and \
            payload.method_revision != reg.method_revision:
        return api_error(409, "METHOD_REVISION_MISMATCH",
                         f"server is frozen at {reg.method_revision}")
    if payload.data_revision and payload.data_revision != reg.revision:
        return api_error(409, "DATA_REVISION_MISMATCH",
                         "installed data revision differs from the request")

    canonical_req = canonical.canonical_request(
        payload.model_dump(), defaults)
    req_hash = canonical.request_hash(canonical_req)

    # 6. cache: same request, same revisions, already succeeded
    cached = db.find_cached_result(req_hash, reg.revision,
                                   reg.method_revision)
    if cached:
        job = db.get_job(cached["job_id"])
        return JSONResponse(status_code=200,
                            content=_job_response(job, cached=True))

    job, created = db.insert_job(canonical_req, req_hash, reg.revision,
                                 reg.method_revision)
    if not created:
        return JSONResponse(status_code=200, content=_job_response(job))
    return JSONResponse(status_code=201, content=_job_response(job))


@app.get("/v1/analyses/{job_id}", response_model=schemas.JobResponse)
def get_analysis(job_id: str):
    job = db.get_job(job_id)
    if not job:
        return api_error(404, "JOB_NOT_FOUND", f"no job {job_id}")
    return _job_response(job)


@app.get("/v1/analyses/{job_id}/result", response_model=schemas.ResultResponse)
def get_result(job_id: str):
    job = db.get_job(job_id)
    if not job:
        return api_error(404, "JOB_NOT_FOUND", f"no job {job_id}")
    if job["state"] == "failed":
        return api_error(409, "JOB_FAILED",
                         f"{job['error_code']}: {job['error_detail']}")
    if job["state"] != "succeeded":
        return api_error(409, "RESULT_NOT_READY", f"job is {job['state']}")
    row = db.get_result_by_job(job_id)
    if not row:
        return api_error(500, "RESULT_MISSING",
                         "job is marked succeeded but no result row exists")
    return {
        "result_id": row["id"],
        "job_id": job_id,
        "request_hash": row["request_hash"],
        "state": json.loads(row["payload_json"])["state"],
        "data_revision": row["data_revision"],
        "method_revision": row["method_revision"],
        "receipt_id": row["receipt_id"],
        "payload": json.loads(row["payload_json"]),
        "payload_sha256": row["payload_sha256"],
    }


@app.get("/v1/receipts/{receipt_id}", response_model=schemas.ReceiptResponse)
def get_receipt(receipt_id: str):
    row = db.get_receipt(receipt_id)
    if not row:
        return api_error(404, "RECEIPT_NOT_FOUND", f"no receipt {receipt_id}")
    payload = json.loads(row["payload_json"])
    return {"receipt_id": row["id"],
            "payload": receipts.redact(payload),
            "payload_sha256": row["payload_sha256"],
            "created_at": row["created_at"]}


@app.get("/v1/analyses/{job_id}/series")
def get_series(job_id: str):
    """Monthly area-weighted series for a finished analysis (chart data).

    Recomputed from the verified cube with the same aggregation policy; no
    bootstrap, so this is fast and safe to call on every card render.
    """
    job = db.get_job(job_id)
    if not job:
        return api_error(404, "JOB_NOT_FOUND", f"no job {job_id}")
    if job["state"] != "succeeded":
        return api_error(409, "RESULT_NOT_READY", f"job is {job['state']}")
    row = db.get_result_by_job(job_id)
    if not row:
        return api_error(500, "RESULT_MISSING", "no result row for job")
    payload = json.loads(row["payload_json"])
    request = payload["request"]
    reg = registry.load_registry()
    cfg = reg.method
    out = {"job_id": job_id, "aggregation_policy_id":
           cfg["aggregation"]["policy_id"], "series": []}
    for var in payload["variables"]:
        entry = reg.get(var["variable_id"], request["region_id"])
        if entry is None:
            continue
        from . import analysis_runner
        try:
            detail = analysis_runner.series_only(
                entry, request, cfg, with_trend=True)
        except analysis_runner.AnalysisError as exc:
            out["series"].append({"variable_id": var["variable_id"],
                                  "state": "insufficient_data",
                                  "error": exc.code})
            continue
        out["series"].append(detail)
    return out


@app.post("/v1/compare")
def compare_regions(body: dict):
    """Same variable, same period, same method across the three windows.

    Slopes and p-values only by default; intervals are optional because each
    one costs a bootstrap run.
    """
    reg = registry.load_registry()
    cfg = reg.method
    variable_id = body.get("variable_id")
    region_ids = body.get("region_ids") or [r["id"] for r in reg.scope["regions"]]
    start = body.get("start_month", "2001-01")
    end = body.get("end_month", "2024-12")
    with_ci = bool(body.get("with_ci", False))
    try:
        months = canonical.month_range(start, end)
    except ValueError:
        return api_error(400, "INVALID_PERIOD", "invalid month range")
    from . import analysis_runner
    results = []
    for rid in region_ids:
        entry = reg.servable(variable_id, rid)
        if entry is None:
            results.append({"region_id": rid, "state": "unavailable"})
            continue
        try:
            detail = analysis_runner.series_only(entry, {
                "start_month": start, "end_month": end, "aoi": None},
                cfg, with_trend=True, with_ci=with_ci)
        except analysis_runner.AnalysisError as exc:
            results.append({"region_id": rid, "state": "insufficient_data",
                            "error": exc.code})
            continue
        results.append({
            "region_id": rid,
            "state": "succeeded",
            "units": entry["units"],
            "slope_per_year": detail["trend"]["slope_per_year"],
            "p_value": detail["trend"]["p_value"],
            "ci_low": detail["trend"].get("ci_low"),
            "ci_high": detail["trend"].get("ci_high"),
            "valid_fraction": detail["valid_fraction"],
            "cells": detail["cells"],
        })
    return {
        "variable_id": variable_id,
        "period": {"start": start, "end": end, "months": len(months)},
        "method_revision": reg.method_revision,
        "note": "same variable, period, method and coverage rule; native grids "
                "differ, so compare slopes, not absolute values",
        "regions": results,
    }


@app.get("/v1/spatial/{variable_id}/{region_id}")
def get_spatial(variable_id: str, region_id: str):
    """Per-cell slope map on the product's native grid (Member 5 layer).

    Values are the frozen method outputs; the client only colours them. Cells
    that failed the coverage rule are null, never zero.
    """
    import numpy as np
    reg = registry.load_registry()
    entry = reg.get(variable_id, region_id)
    if entry is None:
        return api_error(404, "UNKNOWN_VARIABLE_REGION",
                         f"{variable_id}/{region_id} is not in the catalog")
    path = config.DATA_DIR / "analysis" / "spatial_trends" / \
        f"{entry['product_id']}_{region_id}.npz"
    if not path.exists():
        return api_error(404, "SPATIAL_NOT_AVAILABLE",
                         "no spatial product for this pair")
    z = np.load(path)
    slope = z["slope"]
    pval = z["p_value"]
    sig = z["significant_fdr"]
    nvalid = z["n_valid_months"]

    def rounded(a, digits):
        out = []
        for row in a:
            out.append([None if not np.isfinite(v) else round(float(v), digits)
                        for v in row])
        return out

    return {
        "variable_id": variable_id,
        "region_id": region_id,
        "product_id": entry["product_id"],
        "version": entry.get("version"),
        "units": entry["units"],
        "label": entry.get("label"),
        "method_revision": reg.method_revision,
        "bbox": entry["bbox"],
        "grid": {"lat": [round(float(v), 4) for v in z["lat"]],
                 "lon": [round(float(v), 4) for v in z["lon"]]},
        "slope": rounded(slope, 6),
        "p_value": rounded(pval, 4),
        "significant_fdr": [[int(v) for v in row] for row in sig],
        "n_valid_months": [[int(v) for v in row] for row in nvalid],
        "fdr": {"q": reg.method["multiplicity"]["q"],
                "family": "all eligible cells in this variable x window",
                "m_tested": int(np.isfinite(pval).sum())},
        "limitations": entry.get("limitations", []),
    }


@app.get("/v1/analyses/{job_id}/explanation")
def get_explanation(job_id: str, language: str = "ar"):
    """Grounded explanation for a finished analysis (Member 4 layer).

    Deterministic by default. If a provider is configured it is used, and its
    output is admitted only when the validator passes; otherwise the
    deterministic answer is returned.
    """
    if language not in ("ar", "en"):
        return api_error(400, "INVALID_LANGUAGE", "language must be ar or en")
    job = db.get_job(job_id)
    if not job:
        return api_error(404, "JOB_NOT_FOUND", f"no job {job_id}")
    if job["state"] != "succeeded":
        return api_error(409, "RESULT_NOT_READY", f"job is {job['state']}")
    row = db.get_result_by_job(job_id)
    if not row:
        return api_error(500, "RESULT_MISSING", "no result row for job")
    payload = json.loads(row["payload_json"])
    region_id = payload["request"]["region_id"]
    retriever = ai_retrieve.Retriever()
    terms = {v["product_id"] for v in payload["variables"]}
    terms |= {v["variable_id"].replace("_", " ") for v in payload["variables"]}
    query = " ".join(sorted(terms)) + " units limitations quality flags"
    retrieved = retriever.retrieve(query, k=10)["results"]
    out = ai_explain.generate(payload, retrieved,
                              ai_validator.load_catalog(), region_id,
                              language=language,
                              llm=ai_explain.http_llm_from_env())
    return {
        "job_id": job_id,
        "result_id": row["id"],
        "receipt_id": row["receipt_id"],
        "path": out["path"],
        "validation": out["validation"],
        "explanation": out["explanation"],
        "citations": [
            {"chunk_id": r["chunk_id"], "title": r["title"],
             "product_id": r.get("product_id"), "page": r.get("page"),
             "source_url": r.get("source_url"),
             "authority": r.get("authority")}
            for r in retrieved
            if r["chunk_id"] in out["explanation"]["cited_chunk_ids"]],
    }


@app.exception_handler(AnalysisError)
def _analysis_error_handler(request: Request, exc: AnalysisError):
    return api_error(400, exc.code, exc.detail)
