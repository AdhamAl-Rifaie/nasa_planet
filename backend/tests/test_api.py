"""Contract tests for the backend.

Each test maps to an acceptance item in docs/architecture/PLAN.md for
Member 3: duplicate requests, unavailable source rejection, interrupted
worker recovery, stale-cache invalidation, secret exclusion, plus the
canonical request rules from IMPLEMENTATION.md.
"""
from __future__ import annotations

import json
import time

import pytest

from app import config, db, registry

BASE = {
    "region_id": "nile_corridor",
    "variable_ids": ["air_temperature"],
    "start_month": "2001-01",
    "end_month": "2024-12",
}


def wait(client, job_id, timeout=120):
    t0 = time.time()
    while time.time() - t0 < timeout:
        r = client.get(f"/v1/analyses/{job_id}")
        assert r.status_code == 200
        body = r.json()
        if body["state"] in ("succeeded", "failed"):
            return body
        time.sleep(0.3)
    raise AssertionError(f"job {job_id} did not finish within {timeout}s")


def test_health(client):
    r = client.get("/health")
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "ok"
    assert body["method_revision"].startswith("m2-")


def test_catalog_lists_twelve_ready_pairs(client):
    r = client.get("/v1/catalog")
    assert r.status_code == 200
    body = r.json()
    assert len(body["entries"]) == 12
    for e in body["entries"]:
        assert e["measurement_ready"] and e["method_ready"]
        # Member 6 signed the end-to-end path: see docs/acceptance_report.json
        assert e["app_available"] is True
        assert e["units"]


def test_submit_and_result_and_receipt(client):
    r = client.post("/v1/analyses", json=BASE)
    assert r.status_code == 201, r.text
    job_id = r.json()["job_id"]
    job = wait(client, job_id)
    assert job["state"] == "succeeded", job

    res = client.get(f"/v1/analyses/{job_id}/result")
    assert res.status_code == 200
    body = res.json()
    var = body["payload"]["variables"][0]
    assert var["state"] == "succeeded"
    assert var["trend"]["slope_per_year"] is not None
    assert var["trend"]["ci_low"] < var["trend"]["ci_high"]
    assert var["period"]["months"] == 288
    assert var["counts"]["cells"] > 0
    assert body["payload"]["receipt_id"] == body["receipt_id"]

    rc = client.get(f"/v1/receipts/{body['receipt_id']}")
    assert rc.status_code == 200
    payload = rc.json()["payload"]
    for field in ("request", "data_revision", "method_revision",
                  "software_revision", "sources", "qa_policy",
                  "spatial_mask", "aggregation_policy", "anomaly_baseline",
                  "trend_method", "dependence", "bootstrap", "multiplicity"):
        assert field in payload, field
    assert payload["sources"][0]["granule_count"] == 288


def test_duplicate_request_returns_same_job(client):
    first = client.post("/v1/analyses", json=BASE)
    assert first.status_code == 201
    second = client.post("/v1/analyses", json=BASE)
    assert second.status_code in (200, 201)
    assert second.json()["job_id"] == first.json()["job_id"]


def test_canonical_hash_ignores_ring_rotation_and_precision(client):
    ring_a = [[31.0, 30.0], [32.0, 30.0], [32.0, 31.0], [31.0, 31.0],
              [31.0, 30.0]]
    ring_b = [[32.0, 30.0], [32.0, 31.0], [31.0, 31.0], [31.0, 30.0],
              [32.0, 30.0]]          # rotated start, same polygon
    body_a = dict(BASE, variable_ids=["vegetation_greenness"],
                  aoi={"type": "Polygon", "coordinates": [ring_a]})
    body_b = dict(BASE, variable_ids=["vegetation_greenness"],
                  aoi={"type": "Polygon", "coordinates": [ring_b]})
    a = client.post("/v1/analyses", json=body_a)
    b = client.post("/v1/analyses", json=body_b)
    assert a.status_code == 201 and b.status_code in (200, 201)
    assert a.json()["request_hash"] == b.json()["request_hash"]


def test_reject_unknown_region_and_variable(client):
    r = client.post("/v1/analyses", json=dict(BASE, region_id="cairo_city"))
    assert r.status_code == 400
    assert r.json()["error"]["code"] == "UNKNOWN_REGION"
    r2 = client.post("/v1/analyses", json=dict(BASE, variable_ids=["NO2"]))
    assert r2.status_code == 400
    assert r2.json()["error"]["code"] == "UNSUPPORTED_VARIABLE"


def test_reject_invalid_period(client):
    r = client.post("/v1/analyses",
                    json=dict(BASE, start_month="2020-01", end_month="2010-01"))
    assert r.status_code == 400
    assert r.json()["error"]["code"] == "INVALID_PERIOD"
    r2 = client.post("/v1/analyses",
                     json=dict(BASE, start_month="1990-01",
                               end_month="2000-01"))
    assert r2.status_code == 400


def test_reject_bad_geometry(client):
    outside = {"type": "Polygon", "coordinates": [
        [[10.0, 10.0], [11.0, 10.0], [11.0, 11.0], [10.0, 10.0]]]}
    r = client.post("/v1/analyses", json=dict(BASE, aoi=outside))
    assert r.status_code == 400
    assert r.json()["error"]["code"] == "OUT_OF_BOUNDS"

    bowtie = {"type": "Polygon", "coordinates": [
        [[30.0, 25.0], [32.0, 27.0], [32.0, 25.0], [30.0, 27.0],
         [30.0, 25.0]]]}
    r2 = client.post("/v1/analyses", json=dict(BASE, aoi=bowtie))
    assert r2.status_code == 400
    assert r2.json()["error"]["code"] == "SELF_INTERSECTING"


def test_reject_method_revision_mismatch(client):
    r = client.post("/v1/analyses",
                    json=dict(BASE, method_revision="m2-0.0.1"))
    assert r.status_code == 409
    assert r.json()["error"]["code"] == "METHOD_REVISION_MISMATCH"


def test_stale_cache_not_reused_across_method_revision(client):
    """Cache key must include the method revision."""
    from app import canonical
    reg = registry.load_registry()
    req = canonical.canonical_request(
        dict(BASE), reg.defaults())
    h = canonical.request_hash(req)
    # same hash, different method revision -> no cache hit
    assert db.find_cached_result(h, reg.revision, "m2-0.0.0") is None


def test_failed_job_exposes_no_result_or_receipt(client):
    reg = registry.load_registry()
    job, _ = db.insert_job({"region_id": "nile_corridor",
                            "variable_ids": ["air_temperature"],
                            "start_month": "2001-01", "end_month": "2024-12",
                            "aoi": None,
                            "aggregation_policy_id":
                                reg.defaults()["aggregation_policy_id"],
                            "method_revision": reg.method_revision,
                            "data_revision": reg.revision},
                           "deadbeef" * 8, reg.revision,
                           reg.method_revision)
    db.finish_job(job["id"], "failed", "INTERNAL_ERROR", "boom")
    r = client.get(f"/v1/analyses/{job['id']}/result")
    assert r.status_code == 409
    assert r.json()["error"]["code"] == "JOB_FAILED"
    assert db.get_result_by_job(job["id"]) is None


def test_interrupted_worker_recovery(client):
    """A job left 'running' by a crash becomes a retryable failure."""
    reg = registry.load_registry()
    job, _ = db.insert_job({"region_id": "nile_corridor",
                            "variable_ids": ["air_temperature"],
                            "start_month": "2001-01", "end_month": "2024-12",
                            "aoi": None,
                            "aggregation_policy_id":
                                reg.defaults()["aggregation_policy_id"],
                            "method_revision": reg.method_revision,
                            "data_revision": reg.revision},
                           "cafebabe" * 8, reg.revision,
                           reg.method_revision)
    con = db.connect()
    con.execute("UPDATE jobs SET state='running' WHERE id=?", (job["id"],))
    con.commit()
    con.close()
    assert db.recover_stale_jobs() >= 1
    row = db.get_job(job["id"])
    assert row["state"] == "failed"
    assert row["error_code"] == "INTERRUPTED"


def test_no_secrets_in_result_or_receipt(client):
    r = client.post("/v1/analyses", json=BASE)
    job = wait(client, r.json()["job_id"])
    body = client.get(f"/v1/analyses/{job['job_id']}/result").json()
    rc = client.get(f"/v1/receipts/{body['receipt_id']}").json()
    blob = json.dumps(body) + json.dumps(rc)
    for needle in ("password", "token", "secret", "api_key", "apikey",
                   "authorization", "bearer", "netrc"):
        assert needle not in blob.lower(), needle


def test_insufficient_data_state(client):
    """A short period must return insufficient_data, not a number."""
    r = client.post("/v1/analyses",
                    json=dict(BASE, start_month="2023-01", end_month="2024-12"))
    assert r.status_code == 201
    job = wait(client, r.json()["job_id"])
    body = client.get(f"/v1/analyses/{job['job_id']}/result").json()
    var = body["payload"]["variables"][0]
    assert var["state"] == "insufficient_data"
    assert var["trend"]["slope_per_year"] is None
    assert var["warnings"]


def test_explanation_endpoint_grounded(client):
    """M4 layer over a real result: valid, cited, numbers match the payload."""
    r = client.post("/v1/analyses", json=BASE)
    job = wait(client, r.json()["job_id"])
    exp = client.get(f"/v1/analyses/{job['job_id']}/explanation?language=ar")
    assert exp.status_code == 200, exp.text
    body = exp.json()
    assert body["validation"]["ok"] is True
    assert body["path"] in ("deterministic", "llm",
                            "deterministic_fallback")
    e = body["explanation"]
    assert e["state"] == "answered"
    assert e["numeric_references"], "numbers must be referenced"
    assert body["citations"], "at least one citation expected"
    assert all(c["authority"] == "official_nasa" for c in body["citations"])


def test_explanation_insufficient_data(client):
    r = client.post("/v1/analyses",
                    json=dict(BASE, start_month="2023-01", end_month="2024-12"))
    job = wait(client, r.json()["job_id"])
    exp = client.get(f"/v1/analyses/{job['job_id']}/explanation")
    assert exp.status_code == 200
    e = exp.json()["explanation"]
    assert e["state"] == "insufficient_data"
    assert not e["numeric_references"]


def test_web_app_is_served(client):
    for path in ("/app/", "/app/app.js", "/app/style.css"):
        r = client.get(path)
        assert r.status_code == 200, path
    assert "Trend Detective" in client.get("/app/").text or \
        "كاشف" in client.get("/app/").text


def test_spatial_endpoint_shape_and_units(client):
    r = client.get("/v1/spatial/air_temperature/nile_corridor")
    assert r.status_code == 200
    body = r.json()
    nlat = len(body["grid"]["lat"])
    nlon = len(body["grid"]["lon"])
    assert nlat > 0 and nlon > 0
    assert len(body["slope"]) == nlat and len(body["slope"][0]) == nlon
    assert body["units"] == "K"
    assert body["fdr"]["q"] == 0.1
    # every cell is either a finite slope or an explicit null
    for row in body["slope"]:
        for v in row:
            assert v is None or isinstance(v, float)


def test_spatial_unknown_pair_404(client):
    r = client.get("/v1/spatial/no2/nile_corridor")
    assert r.status_code == 404
    assert r.json()["error"]["code"] == "UNKNOWN_VARIABLE_REGION"


def test_series_endpoint(client):
    r = client.post("/v1/analyses", json=BASE)
    job = wait(client, r.json()["job_id"])
    s = client.get(f"/v1/analyses/{job['job_id']}/series")
    assert s.status_code == 200
    ser = s.json()["series"][0]
    assert len(ser["months"]) == 288
    assert len(ser["values"]) == 288
    assert ser["trend"]["state"] == "succeeded"
    # the trend line must match the slope returned in the result
    res = client.get(f"/v1/analyses/{job['job_id']}/result").json()
    slope = res["payload"]["variables"][0]["trend"]["slope_per_year"]
    assert abs(ser["trend"]["slope_per_year"] - slope) < 1e-12
    first, last = ser["trend_line"][0], ser["trend_line"][-1]
    years = (len(ser["months"]) - 1) / 12
    assert abs((last - first) / years - slope) < 0.002


def test_compare_endpoint_uses_same_method(client):
    r = client.post("/v1/compare", json={"variable_id": "air_temperature"})
    assert r.status_code == 200
    body = r.json()
    assert len(body["regions"]) == 3
    assert body["method_revision"] == client.get("/health").json()["method_revision"]
    for row in body["regions"]:
        assert row["state"] in ("succeeded", "insufficient_data", "unavailable")
        if row["state"] == "succeeded":
            assert row["units"] == "K"
    nile = [x for x in body["regions"]
            if x["region_id"] == "nile_corridor"][0]
    card = client.post("/v1/analyses", json=BASE)
    job = wait(client, card.json()["job_id"])
    res = client.get(f"/v1/analyses/{job['job_id']}/result").json()
    assert abs(nile["slope_per_year"] -
               res["payload"]["variables"][0]["trend"]["slope_per_year"]) < 1e-12


def test_failed_job_is_retryable_on_resubmit(client):
    """A failed canonical request must be requeued, not returned as failed."""
    reg = registry.load_registry()
    canonical_body = {"region_id": "nile_corridor",
                      "variable_ids": ["air_temperature"],
                      "start_month": "2001-01", "end_month": "2024-12"}
    r = client.post("/v1/analyses", json=canonical_body)
    job_id = r.json()["job_id"]
    wait(client, job_id)
    con = db.connect()
    con.execute("UPDATE jobs SET state='failed', error_code='INTERNAL_ERROR' "
                "WHERE id=?", (job_id,))
    con.commit()
    con.close()
    again = client.post("/v1/analyses", json=canonical_body)
    assert again.json()["job_id"] == job_id
    job = wait(client, job_id)
    assert job["state"] == "succeeded"
