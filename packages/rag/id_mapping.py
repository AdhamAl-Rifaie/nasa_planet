import json
import pathlib

from .source_index import ROOT

SCOPE_PATH = "docs/architecture/scope.v2.json"
RUNTIME_CATALOG_PATH = "data/nasa/runtime_catalog.json"
REGIONAL_VALIDATION_REPORT_PATH = "data/nasa/validation_regional_report.json"


SEMANTIC_VARIABLE_IDS = {"air_temperature", "soil_moisture", "precipitation", "vegetation_greenness"}


def _load_json(rel_path: str):
    with open(ROOT / rel_path, "r", encoding="utf-8") as handle:
        return json.load(handle)


def _month_in_window(month: str, window) -> bool:
    return window[0] <= month <= window[1]


def _window_covers(requested, window) -> bool:
    return window[0] <= requested[0] and requested[1] <= window[1]


class IDMapper:
    def __init__(self, scope_path=SCOPE_PATH, runtime_catalog_path=RUNTIME_CATALOG_PATH):
        self.scope = _load_json(scope_path)
        self.legacy_catalog = _load_json(runtime_catalog_path)
        self.by_semantic = {}
        self.by_product_variable = {}
        self.by_dataset_id = {}
        self.curated_aliases = {
            "ndvi": "vegetation_greenness",
            "NDVI": "vegetation_greenness",
        }
        for entry in self.scope["entries"]:
            vid = entry["variable_id"]
            self.by_semantic.setdefault(vid, []).append(entry)
            self.by_product_variable[(entry["product_id"], entry["source_variable"])] = vid
            self.by_dataset_id.setdefault(entry["source_variable"], vid)
            self.by_dataset_id.setdefault(entry["product_id"], vid)
        for legacy in self.legacy_catalog:
            self.by_dataset_id.setdefault(legacy["id"], None)
        self._casefold_latin = {
            k.lower(): v
            for k, v in self.by_dataset_id.items()
            if v is not None and k.isascii()
        }

    def resolve(self, identifier: str) -> str:
        key = identifier.strip()
        lowered = key.lower()
        if key in self.by_semantic:
            return key
        if lowered in self._casefold_latin:
            return self._casefold_latin[lowered]
        if key in self.curated_aliases:
            return self.curated_aliases[key]
        if lowered in {a.lower() for a in self.curated_aliases}:
            for alias, target in self.curated_aliases.items():
                if alias.lower() == lowered:
                    return target
        raise KeyError(
            f"unknown variable identifier {identifier!r}; no curated mapping in scope.v2.json "
            f"(known semantic ids: {sorted(self.by_semantic)}, known legacy ids: "
            f"{sorted(self.by_dataset_id)}, "
            f"curated aliases: {sorted(self.curated_aliases)})"
        )

    def semantic_ids(self):
        return sorted(self.by_semantic)

    def product_for(self, variable_id: str, region_id: str):
        for entry in self.by_semantic.get(variable_id, []):
            if entry["region_id"] == region_id:
                return entry["product_id"], entry["source_variable"], entry["version"]
        return None


SEMANTIC_CHECK = None


class ReadinessLookup:
    def __init__(self, scope_path=SCOPE_PATH, validation_report_path=REGIONAL_VALIDATION_REPORT_PATH, id_mapper=None):
        self.scope = _load_json(scope_path)
        self.entries = self.scope["entries"]
        self.validation = _load_json(validation_report_path)
        self.data_revision = self.validation["generated"]
        self.mapper = id_mapper or IDMapper(scope_path=scope_path)

    def lookup(self, variable_id: str, region_id: str, period=None, data_revision=None) -> dict:
        try:
            canonical_var_id = self.mapper.resolve(variable_id)
        except KeyError:
            canonical_var_id = variable_id
        matches = [e for e in self.entries if e["variable_id"] == canonical_var_id and e["region_id"] == region_id]
        if not matches:
            return {
                "found": False,
                "reason_code": "unknown_variable_or_region",
                "variable_id": variable_id,
                "region_id": region_id,
                "note": "readiness is read from docs/architecture/scope.v2.json; no entry exists for this pair",
            }
        entry = matches[0]
        result = {
            "found": True,
            "variable_id": canonical_var_id,
            "requested_variable_id": variable_id,
            "region_id": region_id,
            "product_id": entry["product_id"],
            "product_version": entry["version"],
            "source_variable": entry["source_variable"],
            "bbox": entry["bbox"],
            "period": entry["period"],
            "data_revision": self.data_revision,
            "measurement_ready": entry["measurement_ready"],
            "method_ready": entry["method_ready"],
            "app_available": entry["app_available"],
            "status": entry["status"],
            "cube_file": entry.get("cube_file"),
            "monthly_subsets": entry.get("monthly_subsets"),
            "reason_code": None,
        }
        if period is not None:
            requested = tuple(period)
            if not _window_covers(requested, tuple(entry["period"])):
                result["measurement_ready"] = False
                result["reason_code"] = "period_unavailable"
                result["period_note"] = (
                    f"requested {requested[0]}..{requested[1]} outside verified window "
                    f"{entry['period'][0]}..{entry['period'][1]}"
                )
        if data_revision is not None and data_revision != self.data_revision:
            result["reason_code"] = result["reason_code"] or "data_revision_mismatch"
            result["revision_note"] = f"requested revision {data_revision!r} differs from validated {self.data_revision!r}"
        if not result["app_available"] and result["reason_code"] is None:
            result["reason_code"] = "not_app_available"
            result["note"] = "cube verified but method review/app integration not completed"
        return result

    def available_for_period(self, period) -> list:
        out = []
        for entry in self.entries:
            if _window_covers(tuple(period), tuple(entry["period"])):
                out.append(
                    {
                        "variable_id": entry["variable_id"],
                        "region_id": entry["region_id"],
                        "product_id": entry["product_id"],
                        "measurement_ready": entry["measurement_ready"],
                        "method_ready": entry["method_ready"],
                        "app_available": entry["app_available"],
                    }
                )
        return out

    def region_ids(self):
        return sorted({e["region_id"] for e in self.entries})
