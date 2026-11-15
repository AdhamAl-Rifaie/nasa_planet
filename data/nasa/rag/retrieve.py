"""Offline retrieval CLI (Role 04 Phase 2). No API key or third-party package required.

Delegates to packages/rag (BM25 over the 469-chunk semantic corpus with bilingual
aliases, ambiguity guards and readiness integration). Output mode is always
"local_retrieval": this is retrieval-only, not a generated answer.
"""
import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from packages.rag.retriever import answer_query  # noqa: E402


def main(argv):
    query = " ".join(argv[1:]).strip()
    region = None
    period = None
    cleaned = []
    i = 0
    while i < len(argv[1:]):
        arg = argv[1:][i]
        if arg == "--region":
            region = argv[1:][i + 1]
            i += 2
            continue
        if arg == "--period":
            period = tuple(argv[1:][i + 1].split(".."))
            i += 2
            continue
        cleaned.append(arg)
        i += 1
    query = " ".join(cleaned)
    result = answer_query(query, region_id=region, period=period)
    result["mode"] = "local_retrieval_not_generated_answer"
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return result


if __name__ == "__main__":
    main(sys.argv)
