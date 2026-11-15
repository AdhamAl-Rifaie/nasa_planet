import copy
import json
import re

import pytest

from packages.rag.conclusions import (
    ActiveRequestTracker,
    PayloadError,
    PERMITTED_ACTIONS,
    render_conclusions,
)

NUMBER_RE = re.compile(r"\d+(?:\.\d+)?")

UNITS = {
    "air_temperature": "K",
    "soil_moisture": "kg m-2",
    "precipitation": "mm",
    "vegetation_greenness": "NDVI index",
}
PRODUCTS = {
    "air_temperature": ("M2TMNXSLV", "5.12.4"),
    "soil_moisture": ("GLDAS_NOAH025_M", "2.1"),
    "precipitation": ("GPM_3IMERGM", "07"),
    "vegetation_greenness": ("MOD13C2", "061"),
}
MEANS = {
    "air_temperature": 295.31,
    "soil_moisture": 42.7,
    "precipitation": 12.4,
    "vegetation_greenness": 0.312,
}
SLOPES = {
    "air_temperature": (0.021, "K per year"),
    "soil_moisture": (-0.034, "kg m-2 per year"),
    "precipitation": (0.007, "mm per year"),
    "vegetation_greenness": (0.0004, "NDVI per year"),
}
INTERVALS = {
    "air_temperature": {"low": 0.012, "high": 0.031},
    "soil_moisture": {"low": -0.05, "high": -0.02},
    "precipitation": {"low": 0.001, "high": 0.012},
    "vegetation_greenness": {"low": 0.0001, "high": 0.0007},
}

BANNED_WORDS = [
    "stable",
    "unchanged",
    "no change",
    "ثابت",
    "مستقر",
    "truly",
    "None",
    "null",
    "NaN",
]


def base_payload(variable="air_temperature", **overrides):
    slope, slope_units = SLOPES[variable]
    payload = {
        "analysis_id": "an_2026_001",
        "request_id": "req_2026_001",
        "region_id": "nile_corridor",
        "variable_id": variable,
        "period": {"start_month": "2001-01", "end_month": "2024-12"},
        "units": UNITS[variable],
        "result_state": "succeeded",
        "product": {"product_id": PRODUCTS[variable][0], "product_version": PRODUCTS[variable][1]},
        "regional": {
            "mean": MEANS[variable],
            "n_months": 288,
            "sen_slope": slope,
            "slope_units": slope_units,
            "p_value": 0.03,
            "significance_alpha": 0.05,
            "confidence_interval": dict(INTERVALS[variable]),
        },
        "method_revision": "m2_sen_mk_hamed_rao_v1",
        "data_revision": "2026-11-14",
        "cells": {
            "denominator": "eligible_cells",
            "total_cells": 960,
            "eligible_cells": 950,
            "ineligible_qa_cells": 10,
            "increasing_cells": 200,
            "decreasing_cells": 40,
            "non_significant_cells": 710,
        },
        "coverage": {"valid_area_fraction": 0.98, "denominator": "weighted_area", "ineligible_cells": 10},
        "sensitivity": {"matching_windows": 3, "total_windows": 5},
        "artifacts": {"regional_chart": True, "cell_reveal": True, "spin_it": True, "receipt": True},
        "receipt_id": "rc_2026_001",
    }
    payload.update(copy.deepcopy(overrides))
    return payload


def texts_of(result):
    return [segment["text"] for segment in result["segments"]]


def render_both(payload):
    return render_conclusions(payload, "en"), render_conclusions(payload, "ar")


NULL_LITERAL_RE = re.compile(r"\b(None|null|NaN)\b")


def assert_no_banned(result):
    for text in texts_of(result):
        lowered = text.lower()
        for banned in BANNED_WORDS[:-3]:
            assert banned.lower() not in lowered, (banned, text)
        assert not NULL_LITERAL_RE.search(text), text


@pytest.mark.parametrize("variable", sorted(UNITS))
def test_bilingual_parity_across_all_four_variables(variable):
    payload = base_payload(variable)
    en, ar = render_both(payload)
    assert en["mode"] == "conclusion_templates"
    assert ar["mode"] == "conclusion_templates"
    assert [s["id"] for s in en["segments"]] == [s["id"] for s in ar["segments"]]
    assert len(en["segments"]) >= 5
    en_numbers = set(NUMBER_RE.findall(" ".join(texts_of(en))))
    ar_numbers = set(NUMBER_RE.findall(" ".join(texts_of(ar))))
    assert en_numbers == ar_numbers, (variable, sorted(en_numbers ^ ar_numbers))
    assert_no_banned(en)
    assert_no_banned(ar)
    for segment in en["segments"] + ar["segments"]:
        assert segment["analysis_id"] == payload["analysis_id"]
        assert segment["request_id"] == payload["request_id"]


@pytest.mark.parametrize("variable", sorted(UNITS))
def test_numbers_come_from_payload_verbatim(variable):
    payload = base_payload(variable)
    en, ar = render_both(payload)
    joined = " ".join(texts_of(en))
    assert f"Regional mean {MEANS[variable]} {UNITS[variable]}" in joined
    slope, slope_units = SLOPES[variable]
    expected_slope = f"{slope:.3f}".rstrip("0").rstrip(".")
    assert f"{expected_slope} {slope_units}" in joined
    assert "200 cells show statistical evidence of increase" in joined
    assert "40 cells show statistical evidence of decrease" in joined
    assert "(21.1% of eligible cells: 200 of 950" in joined
    assert "4.2% of eligible cells: 40 of 950" in joined
    assert "98.0% of the weighted AOI area has valid data" in joined
    assert "3 of 5 re-run windows agree in slope sign (60.0% of 5 windows)" in joined
    ar_joined = " ".join(texts_of(ar))
    assert expected_slope in ar_joined
    assert "21.1%" in ar_joined
    assert "98.0%" in ar_joined
    assert "60.0%" in ar_joined


def test_confidence_interval_rendered_when_significant():
    en, ar = render_both(base_payload("air_temperature"))
    joined = " ".join(texts_of(en))
    assert "p = 0.03 < alpha = 0.05" in joined
    assert "95% confidence interval 0.012 to 0.031 K" in joined
    assert "statistically significant evidence of increase under the declared method" in joined
    ar_joined = " ".join(texts_of(ar))
    assert "p = 0.03 < alpha = 0.05" in ar_joined
    assert "أدلة إحصائية معنوية على زيادة وفق المنهجية المعلنة" in ar_joined


def test_non_significant_trend_wording():
    payload = base_payload("air_temperature", regional={
        "mean": 295.31,
        "n_months": 288,
        "sen_slope": 0.004,
        "slope_units": "K per year",
        "p_value": 0.4,
        "significance_alpha": 0.05,
    })
    en, ar = render_both(payload)
    en_joined = " ".join(texts_of(en))
    ar_joined = " ".join(texts_of(ar))
    assert "insufficient statistical evidence for a trend under the declared method" in en_joined
    assert "effect size" in en_joined
    assert "الأدلة الإحصائية غير كافية على وجود اتجاه عام" in ar_joined
    assert "حجم أثر" in ar_joined
    assert_no_banned(en)
    assert_no_banned(ar)


def test_null_inference_keeps_descriptive_stats_and_maps_reason():
    for reason in (
        "insufficient_sample_size",
        "all_cells_masked",
        "zero_variance",
        "method_not_applicable",
        "inference_not_released",
    ):
        payload = base_payload("air_temperature", regional={
            "mean": 295.31,
            "n_months": 120,
            "inference_reason_code": reason,
        })
        en, ar = render_both(payload)
        en_joined = " ".join(texts_of(en))
        ar_joined = " ".join(texts_of(ar))
        assert "Regional mean 295.31 K over 120 monthly values" in en_joined, reason
        assert "Inference was not computed" in en_joined, reason
        assert "لم يُحسب الاستدلال" in ar_joined, reason
        assert_no_banned(en)
        assert_no_banned(ar)


def test_dataset_nature_distinction():
    en_merra, ar_merra = render_both(base_payload("air_temperature"))
    joined = " ".join(texts_of(en_merra))
    assert "a reanalysis product, not direct satellite observations" in joined
    en_gldas, ar_gldas = render_both(base_payload("soil_moisture"))
    joined_gldas = " ".join(texts_of(en_gldas))
    assert "a land-surface model output, not direct satellite observations" in joined_gldas
    en_gpm, _ = render_both(base_payload("precipitation"))
    assert "a satellite-based retrieval product" in " ".join(texts_of(en_gpm))
    assert_no_banned(en_merra)
    assert_no_banned(en_gldas)


def test_payload_source_type_mismatch_rejected():
    payload = base_payload("air_temperature")
    payload["product"]["source_type"] = "satellite"
    with pytest.raises(PayloadError) as excinfo:
        render_conclusions(payload, "en")
    assert any("source_type mismatch" in e for e in excinfo.value.errors)


def test_denominator_labels_and_qa_reporting():
    en, ar = render_both(base_payload("air_temperature"))
    en_joined = " ".join(texts_of(en))
    ar_joined = " ".join(texts_of(ar))
    assert "of eligible cells: 200 of 950" in en_joined
    assert "denominator: weighted_area" in en_joined
    assert "10 ineligible cells were excluded by quality screening" in en_joined
    assert "10 cells are ineligible/masked and excluded from every share" in en_joined
    assert "من الخلايا المؤهلة: 200 من 950" in ar_joined
    assert "10 خلية غير مؤهلة مستبعدة بفحص الجودة" in ar_joined


def test_weighted_area_cell_denominator_supported():
    payload = base_payload("air_temperature", cells={
        "denominator": "weighted_area",
        "ineligible_qa_cells": 10,
        "increasing_weighted_fraction": 0.215,
        "decreasing_weighted_fraction": 0.04,
    })
    en, ar = render_both(payload)
    en_joined = " ".join(texts_of(en))
    assert "21.5% of the weighted AOI area shows statistical evidence of increase" in en_joined
    assert "4.0% of the weighted AOI area shows statistical evidence of decrease" in en_joined
    assert_no_banned(en)
    assert_no_banned(ar)


def test_dynamic_segments_with_full_artifacts():
    en, ar = render_both(base_payload("air_temperature"))
    expected_ids = ["context", "regional_trend", "cell_evidence", "qa_coverage", "sensitivity", "provenance"]
    assert [s["id"] for s in en["segments"]] == expected_ids
    assert [s["id"] for s in ar["segments"]] == expected_ids


def test_unavailable_artifacts_hide_actions_and_segments():
    payload = base_payload(
        "air_temperature",
        artifacts={"regional_chart": False, "cell_reveal": False, "spin_it": False, "receipt": False},
    )
    en = render_conclusions(payload, "en")
    ids = [s["id"] for s in en["segments"]]
    assert "sensitivity" not in ids
    assert "provenance" not in ids
    assert ids == ["context", "regional_trend", "cell_evidence", "qa_coverage"]
    for segment in en["segments"]:
        for action in segment["actions"]:
            assert action["action"] == "FOCUS_REGION"
    assert en["actions"] == [en["segments"][0]["actions"][0]]


def test_actions_bound_to_active_ids_and_permitted_enums():
    en = render_conclusions(base_payload("air_temperature"), "en")
    names = set()
    for segment in en["segments"]:
        for action in segment["actions"]:
            names.add(action["action"])
            assert action["analysis_id"] == "an_2026_001"
            assert action["request_id"] == "req_2026_001"
    assert names == PERMITTED_ACTIONS
    focus = next(a for s in en["segments"] for a in s["actions"] if a["action"] == "FOCUS_REGION")
    assert focus["target"] == {"region_id": "nile_corridor"}
    receipt = next(a for s in en["segments"] for a in s["actions"] if a["action"] == "OPEN_RECEIPT")
    assert receipt["target"] == {"receipt_id": "rc_2026_001"}


def test_comparison_data_renders_segment_without_invented_action():
    payload = base_payload("air_temperature", comparison={"regions": ["nile_corridor", "sahel_comparison"]})
    en, ar = render_both(payload)
    for result in (en, ar):
        assert [s["id"] for s in result["segments"]][-2] == "comparison"
        comparison_segment = next(s for s in result["segments"] if s["id"] == "comparison")
        assert comparison_segment["actions"] == []
        assert comparison_segment["action_pending_contract"] is True
        names = {a["action"] for s in result["segments"] for a in s["actions"]}
        assert names <= PERMITTED_ACTIONS


def test_unrecognized_comparison_action_rejected():
    payload = base_payload("air_temperature", comparison={
        "regions": ["nile_corridor", "sahel_comparison"],
        "action": "MIRROR_SEARCH",
    })
    with pytest.raises(PayloadError) as excinfo:
        render_conclusions(payload, "en")
    assert any("pending the Role 05/06 contract" in e for e in excinfo.value.errors)


def test_insufficient_data_state_renders_no_numbers():
    payload = base_payload("air_temperature", result_state="insufficient_data", reason_code="insufficient_sample_size")
    en = render_conclusions(payload, "en")
    ar = render_conclusions(payload, "ar")
    assert en["status"] == "insufficient_data"
    assert en["segments"] == [] and en["actions"] == []
    assert "insufficient data" in en["message"]
    assert "بيانات غير كافية" in ar["message"]
    assert "295.31" not in en["message"] and "0.021" not in en["message"]


def test_unknown_variable_and_missing_fields_rejected():
    with pytest.raises(PayloadError):
        render_conclusions(base_payload("air_temperature", variable_id="wind"), "en")
    payload = base_payload("air_temperature")
    del payload["regional"]
    with pytest.raises(PayloadError) as excinfo:
        render_conclusions(payload, "en")
    assert any("missing required field regional" in e for e in excinfo.value.errors)


def test_inconsistent_cell_counts_rejected():
    payload = base_payload("air_temperature")
    payload["cells"]["eligible_cells"] = 900
    with pytest.raises(PayloadError) as excinfo:
        render_conclusions(payload, "en")
    assert any("cell counts inconsistent" in e for e in excinfo.value.errors)


def test_receipt_flag_without_receipt_id_rejected():
    payload = base_payload("air_temperature")
    del payload["receipt_id"]
    with pytest.raises(PayloadError) as excinfo:
        render_conclusions(payload, "en")
    assert any("receipt_id is required" in e for e in excinfo.value.errors)


def test_unsupported_language_rejected():
    with pytest.raises(ValueError):
        render_conclusions(base_payload("air_temperature"), "fr")


def test_tracker_accepts_current_request():
    payload = base_payload("air_temperature")
    tracker = ActiveRequestTracker()
    tracker.register("an_2026_001", "req_2026_001", "nile_corridor", ["air_temperature"], ("2001-01", "2024-12"))
    result = render_conclusions(payload, "en", tracker=tracker)
    assert result["status"] == "succeeded"


def test_stale_response_on_period_change():
    payload = base_payload("air_temperature")
    tracker = ActiveRequestTracker()
    tracker.register("an_2026_001", "req_2026_001", "nile_corridor", ["air_temperature"], ("2001-01", "2024-12"))
    stale = copy.deepcopy(payload)
    stale["period"] = {"start_month": "2005-01", "end_month": "2020-12"}
    result = render_conclusions(stale, "en", tracker=tracker)
    assert result["status"] == "stale_response"
    assert result["reason_code"] == "stale_response"
    assert "period changed" in result["reason"]
    assert result["segments"] == [] and result["actions"] == []


def test_stale_response_on_region_change():
    payload = base_payload("air_temperature")
    tracker = ActiveRequestTracker()
    tracker.register("an_2026_001", "req_2026_001", "nile_corridor", ["air_temperature"], ("2001-01", "2024-12"))
    stale = copy.deepcopy(payload)
    stale["region_id"] = "sahel_comparison"
    result = render_conclusions(stale, "ar", tracker=tracker)
    assert result["status"] == "stale_response"
    assert "region changed" in result["reason"]
    assert result["segments"] == []


def test_stale_response_on_unknown_request_id():
    payload = base_payload("air_temperature")
    tracker = ActiveRequestTracker()
    tracker.register("an_2026_001", "req_2026_001", "nile_corridor", ["air_temperature"], ("2001-01", "2024-12"))
    stale = copy.deepcopy(payload)
    stale["request_id"] = "req_9999"
    result = render_conclusions(stale, "en", tracker=tracker)
    assert result["status"] == "stale_response"
    assert "unknown request" in result["reason"]


def test_re_registration_supersedes_old_response():
    tracker = ActiveRequestTracker()
    tracker.register("an_2026_001", "req_2026_001", "nile_corridor", ["air_temperature"], ("2001-01", "2024-12"))
    first = render_conclusions(base_payload("air_temperature"), "en", tracker=tracker)
    assert first["status"] == "succeeded"
    tracker.register("an_2026_002", "req_2026_002", "sahel_comparison", ["soil_moisture"], ("2001-01", "2024-12"))
    old = render_conclusions(base_payload("air_temperature"), "en", tracker=tracker)
    assert old["status"] == "stale_response"
    assert "superseded" in old["reason"]
    current = render_conclusions(
        base_payload("soil_moisture", analysis_id="an_2026_002", request_id="req_2026_002",
                     region_id="sahel_comparison"),
        "en",
        tracker=tracker,
    )
    assert current["status"] == "succeeded"


def test_output_json_contains_no_null_literals_in_user_text():
    en, ar = render_both(base_payload("air_temperature"))
    for result in (en, ar):
        for text in texts_of(result):
            assert not NULL_LITERAL_RE.search(text), text
