import hashlib
import json
import pathlib
from dataclasses import dataclass, field

from .text_cleaning import mixed_decode

ROOT = pathlib.Path(__file__).resolve().parents[2]

SOURCE_KIND_PRODUCT_DOC = "product_doc"
SOURCE_KIND_METHOD_DOC = "method_doc"
SOURCE_KIND_TEAM_AUTHORED = "team_authored"

SOURCE_KINDS = {SOURCE_KIND_PRODUCT_DOC, SOURCE_KIND_METHOD_DOC, SOURCE_KIND_TEAM_AUTHORED}

SOURCE_FILES = {
    "M2TMNXSLV": "data/nasa/rag/sources/M2TMNXSLV.json",
    "GLDAS_NOAH025_M": "data/nasa/rag/sources/GLDAS_NOAH025_M.json",
    "MERRA2_README": "data/nasa/docs/MERRA2_README.pdf",
    "MERRA2_Specification": "data/nasa/docs/MERRA2_Specification.pdf",
    "MERRA2_Reprocessing": "data/nasa/docs/MERRA2_Reprocessing.pdf",
    "GLDAS_Models": "data/nasa/docs/GLDAS_Models.pdf",
    "GLDAS": "data/nasa/rag/sources/README_GLDAS2.pdf",
    "GPM_3IMERGM": "data/nasa/expanded_v2/docs/GPM_3IMERGM_collection.json",
    "MOD13C2": "data/nasa/expanded_v2/docs/MOD13C2_collection.json",
    "IMERG_V07_ATBD": "data/nasa/expanded_v2/docs/IMERG_V07_ATBD.pdf",
    "MOD13_User_Guide_V61": "data/nasa/expanded_v2/docs/MOD13_User_Guide_V61.pdf",
    "pymannkendall.md": "data/nasa/methods/pymannkendall.md",
    "scipy_theilslopes.html": "data/nasa/methods/scipy_theilslopes.html",
    "statsmodels_fdr.html": "data/nasa/methods/statsmodels_fdr.html",
    "POWER_Cairo_monthly": "data/nasa/rag/sources/POWER_Cairo_monthly.json",
}

METHOD_SOURCES = {"pymannkendall.md", "scipy_theilslopes.html", "statsmodels_fdr.html"}

DECLARED_DOCUMENT_VERSIONS = {
    "scipy_theilslopes.html": "1.18.0",
    "statsmodels_fdr.html": "0.15.0",
    "pymannkendall.md": "unknown",
}

CORPUS_FILES = [
    "data/nasa/rag/corpus.jsonl",
    "data/nasa/expanded_v2/docs/rag_additions.jsonl",
]

SEMANTIC_VARIABLE_IDS = {"air_temperature", "soil_moisture", "precipitation", "vegetation_greenness"}


def sha256_file(path: pathlib.Path) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for block in iter(lambda: handle.read(1 << 16), b""):
            digest.update(block)
    return digest.hexdigest()


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


@dataclass
class SourceRecord:
    source_id: str
    source_kind: str
    local_file: str
    source_url: str | None = None
    product_id: str | None = None
    product_version: str | None = None
    version_provenance: str = "not_recorded"
    raw_source_hash: str | None = None
    retrieved_timestamp: str | None = None
    retrieved_timestamp_count: int = 0
    content_roles: set = field(default_factory=set)
    chunk_count: int = 0
    local_hash_verified: bool | None = None
    segregated: bool = False
    segregation_note: str | None = None

    def to_dict(self):
        return {
            "source_id": self.source_id,
            "source_kind": self.source_kind,
            "product_id": self.product_id,
            "product_version": self.product_version,
            "version_provenance": self.version_provenance,
            "source_url": self.source_url,
            "raw_source_hash": self.raw_source_hash,
            "local_file": self.local_file,
            "local_hash_verified": self.local_hash_verified,
            "retrieved_timestamp": self.retrieved_timestamp,
            "content_roles": sorted(self.content_roles),
            "chunk_count": self.chunk_count,
            "segregated": self.segregated,
            "segregation_note": self.segregation_note,
        }


def source_id_of(chunk_id: str) -> str:
    return chunk_id.split(":")[0]


class SourceIndex:
    def __init__(self, corpus_files=None):
        self.corpus_files = corpus_files or CORPUS_FILES
        self.chunks = []
        self.sources = {}
        self.defects = []
        self._build()

    def _build(self):
        raw_by_source = {}
        for rel in self.corpus_files:
            path = ROOT / rel
            data = path.read_bytes()
            text = mixed_decode(data)
            for line in text.splitlines():
                if not line.strip():
                    continue
                chunk = json.loads(line)
                chunk["source_file"] = rel
                self.chunks.append(chunk)
                sid = source_id_of(chunk["chunk_id"])
                raw_by_source.setdefault(sid, []).append(chunk)
        for sid, chunks in raw_by_source.items():
            self._register(sid, chunks)
        self._register_power_point_sample()

    def _register(self, sid, chunks):
        urls = {c.get("source_url") for c in chunks}
        if len(urls) > 1:
            self.defects.append(f"{sid}: inconsistent source_url values {sorted(u or '' for u in urls)}")
        hashes = {c.get("source_sha256") for c in chunks}
        if len(hashes) > 1:
            self.defects.append(f"{sid}: inconsistent source_sha256 values")
        stamps = {c.get("retrieved_at") for c in chunks if c.get("retrieved_at")}
        versions = {c.get("version") for c in chunks} - {None}
        if sid in METHOD_SOURCES:
            kind = SOURCE_KIND_METHOD_DOC
            version = DECLARED_DOCUMENT_VERSIONS.get(sid)
            vprov = "declared_in_document" if version and version != "unknown" else "explicit_unknown"
        else:
            kind = SOURCE_KIND_PRODUCT_DOC
            if len(versions) > 1:
                self.defects.append(f"{sid}: multiple recorded versions {sorted(versions)}")
            version = next(iter(versions), None)
            vprov = "recorded_in_corpus_chunks" if version else "not_recorded"
            if version == "guide_as_retrieved":
                version = None
                vprov = "team_placeholder_removed"
        rec = SourceRecord(
            source_id=sid,
            source_kind=kind,
            local_file=SOURCE_FILES.get(sid),
            source_url=next(iter(urls)) if len(urls) == 1 else None,
            product_id=sid if kind == SOURCE_KIND_PRODUCT_DOC and sid not in METHOD_SOURCES else None,
            product_version=version,
            version_provenance=vprov,
            raw_source_hash=next(iter(hashes)) if len(hashes) == 1 else None,
            retrieved_timestamp=min(stamps) if stamps else None,
            retrieved_timestamp_count=len(stamps),
            content_roles={c.get("content_role") for c in chunks},
            chunk_count=len(chunks),
        )
        self.sources[sid] = rec
        self._verify_hash(rec)

    def _register_power_point_sample(self):
        rel = SOURCE_FILES["POWER_Cairo_monthly"]
        path = ROOT / rel
        rec = SourceRecord(
            source_id="POWER_Cairo_monthly",
            source_kind=SOURCE_KIND_PRODUCT_DOC,
            local_file=rel,
            content_roles={"point_sample_celsius_not_regional_cube"},
            chunk_count=0,
            segregated=True,
            segregation_note=(
                "NASA POWER Cairo point sample in Celsius; kept strictly separate from the "
                "MERRA-2 Kelvin gridded product and the GLDAS soil-moisture cube; never used "
                "as regional-cube evidence."
            ),
        )
        if path.exists():
            prov = json.loads(mixed_decode(path.read_bytes()))
            rec.source_url = prov.get("source_url")
            rec.raw_source_hash = prov.get("sha256")
            rec.retrieved_timestamp = prov.get("retrieved_at")
            rec.product_version = prov.get("header", {}).get("api", {}).get("version")
            rec.version_provenance = "recorded_in_sample_provenance"
            rec.content_roles.add(prov.get("warning", "point_sample_celsius_not_regional_cube"))
            rec.local_hash_verified = sha256_file(path) == rec.raw_source_hash
            csv_path = ROOT / "data/nasa/rag/cairo_temperature_monthly.csv"
            if csv_path.exists():
                rec.segregation_note += " Companion CSV: data/nasa/rag/cairo_temperature_monthly.csv (units C)."
        else:
            rec.local_hash_verified = None
            self.defects.append("POWER_Cairo_monthly: provenance file missing")
        self.sources[rec.source_id] = rec

    def _verify_hash(self, rec: SourceRecord):
        if not rec.local_file or rec.raw_source_hash is None:
            rec.local_hash_verified = None
            return
        path = ROOT / rec.local_file
        if not path.exists():
            rec.local_hash_verified = None
            self.defects.append(f"{rec.source_id}: local source file missing {rec.local_file}")
            return
        actual = sha256_file(path)
        rec.local_hash_verified = actual == rec.raw_source_hash
        if not rec.local_hash_verified:
            self.defects.append(f"{rec.source_id}: hash mismatch recorded={rec.raw_source_hash[:12]} actual={actual[:12]}")

    def get_source(self, source_id: str) -> SourceRecord:
        if source_id not in self.sources:
            raise KeyError(f"unknown source_id {source_id!r}")
        return self.sources[source_id]

    def resolve_url(self, source_id: str) -> str:
        rec = self.get_source(source_id)
        if not rec.source_url:
            raise ValueError(f"source {source_id!r} has no recorded URL")
        return rec.source_url

    def list_sources(self) -> list:
        return [self.sources[sid] for sid in sorted(self.sources)]

    def chunks_for_source(self, source_id: str) -> list:
        return [c for c in self.chunks if source_id_of(c["chunk_id"]) == source_id]
