import math

from .arabic import tokenize
from .semantic_corpus import load_semantic_corpus
from .source_index import SourceIndex
from .id_mapping import IDMapper, ReadinessLookup
from .intent import (
    classify_query,
    STATUS_RECOMMENDED,
    STATUS_DOCUMENTED_ONLY,
    STATUS_AMBIGUOUS,
    STATUS_UNSUPPORTED,
    STATUS_UNAVAILABLE,
)

K1 = 1.5
B = 0.75
TOP_K = 5

PRODUCT_OF_SOURCE = {
    "M2TMNXSLV": "air_temperature",
    "GLDAS_NOAH025_M": "soil_moisture",
    "GPM_3IMERGM": "precipitation",
    "MOD13C2": "vegetation_greenness",
    "IMERG_V07_ATBD": "precipitation",
    "MOD13_User_Guide_V61": "vegetation_greenness",
    "MERRA2_README": "air_temperature",
    "MERRA2_Specification": "air_temperature",
    "MERRA2_Reprocessing": "air_temperature",
    "GLDAS": "soil_moisture",
    "GLDAS_Models": "soil_moisture",
    "pymannkendall.md": None,
    "scipy_theilslopes.html": None,
    "statsmodels_fdr.html": None,
}

LIMITATION_MARKERS = (
    "limitation", "caution", "bias", "uncertain", "uncertainty", "missing",
    "fill value", "quality", "error", "caveat", "representativeness",
)

ALIAS_EXPANSION = {
    "air_temperature": ["temperature", "air", "2-meter", "t2m", "reanalysis", "حراره"],
    "soil_moisture": ["soil", "moisture", "land surface", "hydrology", "رطوبه", "تربه"],
    "precipitation": ["precipitation", "rain", "satellite", "gauge", "مطر", "امطار"],
    "vegetation_greenness": ["ndvi", "vegetation", "greenness", "index", "نباتات"],
}

CAUSALITY_LIMITATION = (
    "No causal claim is supported: trend association does not establish cause. "
    "Documentation describes the product, not a regional trend."
)

NO_REGION_NOTE = (
    "Candidate variable identified from documentation; no region selected, so no executable "
    "coverage is promised. Select an AOI/study window to check actual availability."
)


class BM25:
    def __init__(self, token_lists):
        self.docs = token_lists
        self.n = len(token_lists)
        self.avgdl = sum(len(d) for d in token_lists) / max(self.n, 1)
        self.df = {}
        self.tfs = []
        for doc in token_lists:
            tf = {}
            for tok in doc:
                tf[tok] = tf.get(tok, 0) + 1
            self.tfs.append(tf)
            for tok in tf:
                self.df[tok] = self.df.get(tok, 0) + 1

    def idf(self, term):
        n = self.df.get(term, 0)
        if n == 0:
            return 0.0
        return math.log(1 + (self.n - n + 0.5) / (n + 0.5))

    def score(self, query_tokens, index):
        doc_tf = self.tfs[index]
        dl = len(self.docs[index]) or 1
        total = 0.0
        for term in query_tokens:
            tf = doc_tf.get(term)
            if not tf:
                continue
            total += self.idf(term) * tf * (K1 + 1) / (tf + K1 * (1 - B + B * dl / self.avgdl))
        return total


class Retriever:
    def __init__(self):
        self.chunks = load_semantic_corpus()
        self.index = SourceIndex()
        self.mapper = IDMapper()
        self.readiness = ReadinessLookup(id_mapper=self.mapper)
        token_lists = [tokenize(c["title"] + " " + c["text"]) for c in self.chunks]
        self.bm25 = BM25(token_lists)
        self.source_of = [c["source_id"] for c in self.chunks]
        self.product_of_chunk = [PRODUCT_OF_SOURCE.get(sid) for sid in self.source_of]

    def _candidate_indices(self, variable_ids=None, product_filter=None):
        out = []
        for i, sid in enumerate(self.source_of):
            chunk_variable = self.product_of_chunk[i]
            if variable_ids:
                if chunk_variable is None or chunk_variable not in variable_ids:
                    continue
            if product_filter and sid != product_filter:
                continue
            out.append(i)
        return out

    def _score(self, query_tokens, candidates):
        scored = []
        for i in candidates:
            s = self.bm25.score(query_tokens, i)
            if s > 0:
                scored.append((s, i))
        scored.sort(key=lambda x: (-x[0], x[1]))
        return scored

    def _definition_index_for(self, sid):
        for i, chunk in enumerate(self.chunks):
            if chunk["source_id"] == sid and chunk["section_locator"] in ("abstract", "collection"):
                return i
        for i, chunk in enumerate(self.chunks):
            if chunk["source_id"] == sid:
                return i
        return None

    def _limitation_index_for(self, sid):
        best, best_count = None, 0
        for i, chunk in enumerate(self.chunks):
            if chunk["source_id"] != sid:
                continue
            lowered = chunk["text"].lower()
            count = sum(lowered.count(m) for m in LIMITATION_MARKERS)
            if count > best_count:
                best, best_count = i, count
        return best

    def _citation(self, i, score=None):
        chunk = self.chunks[i]
        citation = {
            "chunk_id": chunk["chunk_id"],
            "source_id": chunk["source_id"],
            "source_kind": chunk["source_kind"],
            "product_id": chunk.get("product_id"),
            "product_version": chunk.get("product_version"),
            "source_url": chunk["source_url"],
            "section_locator": chunk["section_locator"],
            "retrieved_timestamp": chunk["retrieved_timestamp"],
            "raw_source_hash": chunk["raw_source_hash"],
            "title": chunk["title"],
            "text": chunk["text"],
        }
        if score is not None:
            citation["score"] = round(score, 4)
        return citation

    def retrieve(self, query, variable_ids=None, product_filter=None, k=TOP_K):
        tokens = tokenize(query)
        for variable in variable_ids or []:
            tokens = tokens + ALIAS_EXPANSION.get(variable, [])
        candidates = self._candidate_indices(set(variable_ids or []), product_filter)
        scored = self._score(tokens, candidates)[:k]
        return [self._citation(i, score) for score, i in scored]

    def answer_query(self, query, region_id=None, period=None, data_revision=None):
        classification = classify_query(query)
        answer = {
            "mode": "local_retrieval",
            "query": query,
            "status": classification["status"],
            "reason_code": classification["reason_code"],
            "variable_ids": classification.get("variable_ids", []),
            "suggested_variable_ids": [],
            "citations": [],
            "context": {"definition_chunks": [], "limitation_chunks": []},
            "limitations": [],
            "notes": classification.get("notes", []),
        }

        if answer["status"] in (STATUS_UNSUPPORTED, STATUS_AMBIGUOUS, STATUS_UNAVAILABLE):
            for key in ("clarification", "message", "note", "topic"):
                if key in classification:
                    answer[key] = classification[key]
            if answer["reason_code"] == "no_target_variable_identified":
                hits = self._score(tokenize(query), range(len(self.chunks)))[:3]
                answer["excerpts"] = [self._citation(i, score) for score, i in hits]
            return answer

        variable_ids = set(classification["variable_ids"])
        tokens = classification["tokens"] + [t for v in sorted(variable_ids) for t in ALIAS_EXPANSION.get(v, [])]
        scored = self._score(tokens, self._candidate_indices(variable_ids))[:TOP_K]
        answer["citations"] = [self._citation(i, score) for score, i in scored]

        seen_sources = []
        for _, i in scored:
            sid = self.source_of[i]
            if sid not in seen_sources:
                seen_sources.append(sid)
        for sid in seen_sources[:2]:
            di = self._definition_index_for(sid)
            if di is not None:
                answer["context"]["definition_chunks"].append(self._citation(di))
            li = self._limitation_index_for(sid)
            if li is not None and li != di:
                answer["context"]["limitation_chunks"].append(self._citation(li))

        answer["limitations"].append(CAUSALITY_LIMITATION)
        for note in classification.get("notes", []):
            answer["limitations"].append(note["text"])

        period_blocked = None
        availability = {}
        for variable in sorted(variable_ids):
            if region_id:
                readiness = self.readiness.lookup(variable, region_id, period, data_revision)
            else:
                readiness = None
                for reg in self.readiness.region_ids():
                    probe = self.readiness.lookup(variable, reg, period, data_revision)
                    if probe.get("found") and probe["reason_code"] != "period_unavailable":
                        readiness = probe
                        break
            availability[variable] = readiness
            if readiness and readiness.get("found") and readiness["reason_code"] == "period_unavailable":
                period_blocked = readiness
        if period_blocked:
            answer["status"] = STATUS_UNAVAILABLE
            answer["reason_code"] = "period_unavailable"
            answer["availability"] = availability
            answer["suggested_variable_ids"] = []
            answer["period_note"] = period_blocked.get("period_note")
            return answer

        if region_id:
            answer["availability"] = availability
            answer["suggested_variable_ids"] = sorted(variable_ids)
            if all(
                r and r.get("found") and r["measurement_ready"] and r["app_available"]
                for r in availability.values()
            ):
                answer["status"] = STATUS_RECOMMENDED
                answer["reason_code"] = None
            elif all(
                r and r.get("found") and r["measurement_ready"]
                for r in availability.values()
            ):
                answer["status"] = STATUS_DOCUMENTED_ONLY
                answer["reason_code"] = "measurement_ready_app_not_available"
            else:
                answer["status"] = STATUS_UNAVAILABLE
                answer["reason_code"] = "region_unavailable"
        else:
            answer["status"] = STATUS_DOCUMENTED_ONLY
            answer["reason_code"] = "no_region_selected"
            answer["suggested_variable_ids"] = sorted(variable_ids)
            answer["availability"] = {
                variable: {
                    "measurement_ready": bool(r and r.get("measurement_ready")),
                    "note": NO_REGION_NOTE,
                }
                for variable, r in availability.items()
            }
        return answer


def answer_query(query, region_id=None, period=None, data_revision=None):
    return Retriever().answer_query(query, region_id=region_id, period=period, data_revision=data_revision)
