import pytest

from packages.rag.source_index import (
    SOURCE_KINDS,
    DECLARED_DOCUMENT_VERSIONS,
    SourceIndex,
    source_id_of,
)
from packages.rag.semantic_corpus import (
    build_semantic_chunks,
    load_semantic_corpus,
    validate_semantic_chunks,
    REQUIRED_PROVENANCE_FIELDS,
)

EXPECTED_SOURCES = {
    "M2TMNXSLV",
    "GLDAS_NOAH025_M",
    "MERRA2_README",
    "MERRA2_Specification",
    "MERRA2_Reprocessing",
    "GLDAS_Models",
    "GLDAS",
    "GPM_3IMERGM",
    "MOD13C2",
    "IMERG_V07_ATBD",
    "MOD13_User_Guide_V61",
    "pymannkendall.md",
    "scipy_theilslopes.html",
    "statsmodels_fdr.html",
    "POWER_Cairo_monthly",
}

PRODUCT_VERSIONS = {
    "M2TMNXSLV": "5.12.4",
    "GLDAS_NOAH025_M": "2.1",
    "GPM_3IMERGM": "07",
    "MOD13C2": "061",
}


@pytest.fixture(scope="module")
def index():
    return SourceIndex()


@pytest.fixture(scope="module")
def semantic():
    chunks = build_semantic_chunks()
    return chunks


def test_index_defects_empty(index):
    assert index.defects == [], index.defects


def test_all_expected_sources_registered(index):
    registered = {r.source_id for r in index.list_sources()}
    assert EXPECTED_SOURCES <= registered


def test_source_kinds_valid(index):
    for rec in index.list_sources():
        assert rec.source_kind in SOURCE_KINDS


def test_method_sources_labeled_method_doc(index):
    for sid in ("pymannkendall.md", "scipy_theilslopes.html", "statsmodels_fdr.html"):
        assert index.get_source(sid).source_kind == "method_doc"
        assert index.get_source(sid).product_version in (
            "unknown",
            DECLARED_DOCUMENT_VERSIONS[sid],
        )


def test_scipy_statsmodels_versions_declared_in_document():
    assert DECLARED_DOCUMENT_VERSIONS["scipy_theilslopes.html"] == "1.18.0"
    assert DECLARED_DOCUMENT_VERSIONS["statsmodels_fdr.html"] == "0.15.0"


def test_product_versions_recorded_not_fabricated(index):
    for sid, expected in PRODUCT_VERSIONS.items():
        assert index.get_source(sid).product_version == expected
        assert index.get_source(sid).version_provenance == "recorded_in_corpus_chunks"


def test_no_version_fabrication_for_pdf_only_sources(index):
    for sid in ("MERRA2_README", "MERRA2_Specification", "MERRA2_Reprocessing", "GLDAS_Models", "GLDAS"):
        rec = index.get_source(sid)
        assert rec.product_version is None
        assert rec.version_provenance in ("not_recorded", "team_placeholder_removed")


def test_raw_source_hashes_verified_against_local_files(index):
    unverified = []
    for rec in index.list_sources():
        if rec.raw_source_hash is None:
            continue
        if rec.local_hash_verified is not True:
            unverified.append(rec.source_id)
    assert unverified == [], unverified


def test_chunk_hashes_match_source_records(index):
    for chunk in index.chunks:
        rec = index.get_source(source_id_of(chunk["chunk_id"]))
        assert chunk["source_sha256"] == rec.raw_source_hash


def test_resolve_url_from_trusted_record(index):
    url = index.resolve_url("M2TMNXSLV")
    assert "cmr.earthdata.nasa.gov" in url
    with pytest.raises(KeyError):
        index.resolve_url("not_a_source")


def test_power_point_sample_segregated(index):
    rec = index.get_source("POWER_Cairo_monthly")
    assert rec.segregated is True
    assert rec.chunk_count == 0
    assert "Celsius" in rec.segregation_note
    power_ids = {source_id_of(c["chunk_id"]) for c in index.chunks}
    assert "POWER_Cairo_monthly" not in power_ids


def test_semantic_chunks_have_full_provenance(semantic):
    assert len(semantic) > 300
    for chunk in semantic:
        for fieldname in REQUIRED_PROVENANCE_FIELDS:
            assert fieldname in chunk
        assert chunk["source_kind"] in SOURCE_KINDS
        assert chunk["text"].strip()
        assert chunk["char_count"] == len(chunk["text"])


def test_semantic_chunk_ids_unique_and_located(semantic):
    ids = [c["chunk_id"] for c in semantic]
    assert len(ids) == len(set(ids))
    for chunk in semantic:
        parts = chunk["chunk_id"].split(":")
        assert parts[0] == chunk["source_id"]
        assert chunk["section_locator"] in chunk["chunk_id"]


def test_semantic_chunks_bounded_by_paragraph_packing(semantic):
    for chunk in semantic:
        assert len(chunk["text"]) <= 3201


def test_no_availability_fields_in_chunks(semantic):
    assert validate_semantic_chunks(semantic) == []


def test_semantic_corpus_roundtrip_and_manifest(tmp_path, semantic):
    from packages.rag.semantic_corpus import write_semantic_corpus

    corpus_path, manifest_path = write_semantic_corpus(semantic)
    loaded = load_semantic_corpus()
    assert len(loaded) == len(semantic)
    import json
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert manifest["chunk_count"] == len(semantic)
    assert manifest["builder_revision"] == "role04_phase1_v1"
