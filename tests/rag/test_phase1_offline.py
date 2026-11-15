import socket

import pytest

from packages.rag.source_index import SourceIndex
from packages.rag.semantic_corpus import build_semantic_chunks, load_semantic_corpus


@pytest.fixture()
def no_network(monkeypatch):
    def denied(*args, **kwargs):
        raise AssertionError("network access attempted during offline operation")

    monkeypatch.setattr(socket, "socket", denied)
    monkeypatch.setattr(socket, "create_connection", denied)


def test_index_builds_without_network(no_network):
    index = SourceIndex()
    assert len(index.chunks) == 515
    assert len(index.sources) >= 15


def test_semantic_build_and_load_without_network(no_network):
    chunks = build_semantic_chunks()
    assert chunks
    loaded = load_semantic_corpus()
    assert loaded


def test_cached_corpus_file_is_usable_offline(no_network, tmp_path):
    loaded = load_semantic_corpus()
    assert all("raw_source_hash" in c for c in loaded)
    assert all(c["source_url"] for c in loaded)


def test_no_third_party_network_sdk_in_rag_package():
    import pathlib
    import re

    pkg = pathlib.Path("packages/rag")
    banned = re.compile(r"\b(import (requests|httpx|aiohttp|google|googleapiclient)|from (requests|httpx|aiohttp|google|googleapiclient))\b")
    for path in pkg.glob("*.py"):
        assert not banned.search(path.read_text(encoding="utf-8")), path


def test_stdlib_urllib_confined_to_provider_module():
    import pathlib
    import re

    pkg = pathlib.Path("packages/rag")
    banned = re.compile(r"\b(import urllib|from urllib)\b")
    for path in pkg.glob("*.py"):
        source = path.read_text(encoding="utf-8")
        if path.name == "provider.py":
            assert banned.search(source), "provider module is the only sanctioned network boundary"
            continue
        assert not banned.search(source), path
