import json
import datetime
import pathlib

from .source_index import CORPUS_FILES, ROOT, SourceIndex, source_id_of, SOURCE_KINDS
from .text_cleaning import clean_text

MAX_CHUNK_CHARS = 1600

SENTENCE_SPLIT = __import__("re").compile(r"(?<=[.!?])\s+")

SEMANTIC_CORPUS_PATH = "data/nasa/rag/corpus_semantic.jsonl"
SEMANTIC_MANIFEST_PATH = "data/nasa/rag/corpus_semantic_manifest.json"

REQUIRED_PROVENANCE_FIELDS = [
    "source_id",
    "chunk_id",
    "source_url",
    "source_kind",
    "product_version",
    "section_locator",
    "retrieved_timestamp",
    "raw_source_hash",
]


def _paragraphs(text: str):
    for para in text.split("\n\n"):
        para = para.strip()
        if para:
            yield para


def _split_long_paragraph(para: str):
    if len(para) <= MAX_CHUNK_CHARS:
        return [para]
    sentences = SENTENCE_SPLIT.split(para)
    pieces = []
    current = ""
    for sentence in sentences:
        if not sentence:
            continue
        if current and len(current) + 1 + len(sentence) > MAX_CHUNK_CHARS:
            pieces.append(current)
            current = sentence
        else:
            current = f"{current} {sentence}".strip()
        while len(current) > MAX_CHUNK_CHARS * 2:
            pieces.append(current[:MAX_CHUNK_CHARS])
            current = current[MAX_CHUNK_CHARS:]
    if current:
        pieces.append(current)
    return pieces


def build_semantic_chunks(index: SourceIndex = None) -> list:
    index = index or SourceIndex()
    groups = {}
    for chunk in index.chunks:
        sid = source_id_of(chunk["chunk_id"])
        parts = chunk["chunk_id"].split(":")
        section = ":".join(parts[1:-1]) if len(parts) > 2 else parts[1]
        groups.setdefault((sid, section), []).append(chunk)
    ordered_keys = sorted(groups, key=lambda k: (k[0], k[1]))
    out = []
    for sid, section in ordered_keys:
        rec = index.get_source(sid)
        chunks = groups[(sid, section)]
        chunks.sort(key=lambda c: c["chunk_id"])
        merged_text = "\n\n".join(clean_text(c["text"]) for c in chunks if c["text"] and c["text"].strip())
        if not merged_text:
            continue
        paras = []
        for para in _paragraphs(merged_text):
            paras.extend(_split_long_paragraph(para))
        current = ""
        built = []
        for para in paras:
            if current and len(current) + 1 + len(para) > MAX_CHUNK_CHARS:
                built.append(current)
                current = para
            else:
                current = f"{current}\n\n{para}".strip()
        if current:
            built.append(current)
        for i, text in enumerate(built):
            out.append(
                {
                    "source_id": sid,
                    "chunk_id": f"{sid}:{section}:{i}",
                    "source_url": rec.source_url,
                    "source_kind": rec.source_kind,
                    "product_id": rec.product_id,
                    "product_version": rec.product_version,
                    "section_locator": section,
                    "retrieved_timestamp": min(
                        (c["retrieved_at"] for c in chunks if c.get("retrieved_at")), default=rec.retrieved_timestamp
                    ),
                    "raw_source_hash": rec.raw_source_hash,
                    "content_role": sorted(rec.content_roles)[0] if rec.content_roles else None,
                    "title": chunks[0].get("title"),
                    "text": text,
                    "char_count": len(text),
                }
            )
    return out


def write_semantic_corpus(chunks: list, corpus_path=SEMANTIC_CORPUS_PATH, manifest_path=SEMANTIC_MANIFEST_PATH):
    cpath = ROOT / corpus_path
    cpath.parent.mkdir(parents=True, exist_ok=True)
    with open(cpath, "w", encoding="utf-8", newline="\n") as handle:
        for chunk in chunks:
            handle.write(json.dumps(chunk, ensure_ascii=False) + "\n")
    manifest = {
        "generated_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "builder": "packages/rag/semantic_corpus.py",
        "builder_revision": "role04_phase1_v1",
        "corpus_path": corpus_path,
        "chunk_count": len(chunks),
        "sources": sorted({c["source_id"] for c in chunks}),
        "input_files": list(CORPUS_FILES),
        "content_statement": (
            "Chunks are verbatim excerpts of the recorded official source material, re-grouped by "
            "topic/paragraph with font-artifact character repair only. The builder is team-authored "
            "(Role 04); chunk content is not team-authored and not NASA-authored-by-this-team. "
            "Availability/readiness facts are never stored in chunks; they live only in the "
            "readiness registry module."
        ),
        "encoding_notes": (
            "data/nasa/expanded_v2/docs/rag_additions.jsonl contains mixed UTF-8 and cp1252 bytes "
            "(raw 0xB0 degree signs inside UTF-8 text); decoded with a hybrid UTF-8/cp1252 decoder. "
            "PDF-extracted private-use-area glyphs were mapped through a documented table or dropped "
            "when unknown."
        ),
    }
    with open(ROOT / manifest_path, "w", encoding="utf-8", newline="\n") as handle:
        json.dump(manifest, handle, ensure_ascii=False, indent=2)
    return cpath, ROOT / manifest_path


def load_semantic_corpus(corpus_path=SEMANTIC_CORPUS_PATH) -> list:
    with open(ROOT / corpus_path, "r", encoding="utf-8") as handle:
        return [json.loads(line) for line in handle if line.strip()]


def validate_semantic_chunks(chunks: list) -> list:
    defects = []
    ids = set()
    for chunk in chunks:
        cid = chunk.get("chunk_id")
        if cid in ids:
            defects.append(f"duplicate chunk_id {cid}")
        ids.add(cid)
        for fieldname in REQUIRED_PROVENANCE_FIELDS:
            if fieldname not in chunk:
                defects.append(f"{cid}: missing provenance field {fieldname}")
        if chunk.get("source_kind") not in SOURCE_KINDS:
            defects.append(f"{cid}: invalid source_kind {chunk.get('source_kind')}")
        if not (chunk.get("text") or "").strip():
            defects.append(f"{cid}: empty text")
        for key in ("measurement_ready", "method_ready", "app_available", "analysis_ready"):
            if key in chunk:
                defects.append(f"{cid}: availability field {key} stored in chunk (forbidden)")
    return defects
