import re

from .arabic import normalize_arabic_token, strip_diacritics
from .aliases import ALIAS_PROVENANCE

MAX_ANSWER_CHARS = 4000

ALLOWED_FIELDS = {"answer", "cited_chunk_ids", "suggested_variable_ids", "product_versions", "limitations"}
REQUIRED_FIELDS = {"answer", "cited_chunk_ids"}

INJECTION_PATTERNS = (
    "ignore previous instructions",
    "ignore all instructions",
    "ignore the above",
    "disregard previous",
    "disregard the above",
    "disregard all instructions",
    "reveal your instructions",
    "reveal the api key",
    "reveal your system",
    "system prompt",
    "api key",
    "gemini_api_key",
    "تجاهل التعليمات",
    "تجاهل التعليمات السابقه",
    "اعطني المفتاح",
    "اكتب المفتاح",
)

INTERNAL_FIELD_PATTERNS = ("app_available", "measurement_ready", "method_ready", "analysis_ready")

CAUSAL_PATTERNS = (
    "caused by",
    "caused the",
    "caused this",
    "caused an increase",
    "causes the",
    "due to",
    "because of",
    "results in",
    "resulting in",
    "leads to",
    "led to",
    "is caused",
    "are caused",
    "explains the",
    "بسبب",
    "يؤدي الى",
    "ادى الى",
    "أدى إلى",
    "السبب هو",
    "يعود سببه",
)

CAUSAL_DENIALS = (
    "does not establish",
    "does not prove",
    "cannot establish",
    "cannot prove",
    "not establish cause",
    "association does not",
    "no causal",
    "does not mean",
    "لا يثبت",
    "لا تعني",
    "لا يمكن الجزم",
    "غير مثبت",
)

NEGATION_CUES = (
    "not ",
    "no ",
    "isn't",
    "aren't",
    "rather than",
    "instead of",
    "بدلا من",
    "بدل من",
    "ليس ",
    "ليست ",
    "لا ",
    "غير ",
)

SATTELITE_MISLABEL_PATTERNS = (
    "satellite observation",
    "satellite measurement",
    "satellite-measured",
    "measured by satellite",
    "satellite data",
    "قياسات القمر الصناعي",
    "تقيسه الأقمار",
    "بالأقمار الصناعية",
)

NUMERIC_PERCENT_PATTERNS = (
    re.compile(r"\d+(?:\.\d+)?\s*%"),
    re.compile(r"\d+(?:\.\d+)?\s*(?:percent|percentage|نسبه مئويه|نسبة مئوية)"),
)

GUARDRAILS = {
    "air_temperature": {
        "never": (
            "nasa power",
            "power point sample",
            "cairo station",
            "weather station",
            "محطة قياس",
            "محطة الطقس",
        ),
        "metadata_unless_negated": ("celsius", "°c", "degrees celsius", "درجه مئويه", "درجة مئوية")
        + SATTELITE_MISLABEL_PATTERNS,
    },
    "soil_moisture": {
        "numeric": NUMERIC_PERCENT_PATTERNS,
        "metadata_unless_negated": SATTELITE_MISLABEL_PATTERNS,
    },
    "vegetation_greenness": {
        "metadata_unless_negated": ("crop yield", "yield per", "محصول", "غله", "انتاجيه", "غلة", "إنتاجية"),
    },
    "precipitation": {},
}

SENTENCE_SPLIT = re.compile(r"[.!?\u061f\u061b\u0648?؛\n]")


class EvidenceContext:
    def __init__(
        self,
        query,
        permitted_variable_ids,
        allowed_chunk_ids,
        chunk_records,
        expected_product_versions,
        availability,
        local,
        pipeline_limitations,
        trusted_urls,
    ):
        self.query = query
        self.permitted_variable_ids = list(permitted_variable_ids)
        self.allowed_chunk_ids = set(allowed_chunk_ids)
        self.chunk_records = dict(chunk_records)
        self.expected_product_versions = dict(expected_product_versions)
        self.availability = availability
        self.local = local
        self.pipeline_limitations = list(pipeline_limitations)
        self.trusted_urls = dict(trusted_urls)


class OutputValidationError(Exception):
    def __init__(self, errors):
        self.errors = list(errors)
        super().__init__("; ".join(self.errors))


def _scan_forms(text):
    lowered = text.lower()
    normalized = normalize_arabic_token(strip_diacritics(text)).lower()
    forms = [lowered]
    if normalized != lowered:
        forms.append(normalized)
    return forms


def _first_index(forms, phrase):
    for form in forms:
        index = form.find(phrase)
        if index != -1:
            return form, index
    return None, -1


def _has_negation_before(form, index, window=28):
    start = max(0, index - window)
    prefix = form[start:index]
    return any(cue in prefix for cue in NEGATION_CUES)


def _wording_violations(text, variable_ids):
    violations = []
    forms = _scan_forms(text)
    for phrase in INJECTION_PATTERNS:
        if any(phrase in form for form in forms):
            violations.append(f"prompt-injection or secret-exposure wording rejected: {phrase!r}")
    for phrase in INTERNAL_FIELD_PATTERNS:
        if any(phrase in form for form in forms):
            violations.append(f"internal availability field mentioned in prose: {phrase!r}")
    for variable in variable_ids:
        rules = GUARDRAILS.get(variable, {})
        for phrase in rules.get("never", ()):
            if any(phrase in form for form in forms):
                violations.append(f"ungrounded conflation claim for {variable}: {phrase!r}")
        for phrase in rules.get("metadata_unless_negated", ()):
            form, index = _first_index(forms, phrase)
            if index != -1 and not _has_negation_before(form, index):
                violations.append(f"ungrounded metadata claim for {variable}: {phrase!r}")
        for pattern in rules.get("numeric", ()):
            if any(pattern.search(form) for form in forms):
                violations.append(f"numeric claim with banned unit for {variable}")
    for phrase in CAUSAL_PATTERNS:
        for form in forms:
            start = 0
            while True:
                index = form.find(phrase, start)
                if index == -1:
                    break
                sentence_start = max(
                    0,
                    max((form[:index].rfind(m) for m in (".", "!", "?", "\n", "؟", "؛"))),
                )
                sentence = form[sentence_start : index + 200]
                if any(denial in sentence for denial in CAUSAL_DENIALS):
                    start = index + len(phrase)
                    continue
                violations.append(f"false causality wording rejected: {phrase!r}")
                break
    return violations


def _passes_guardrails(text, variable_ids):
    return not _wording_violations(text, variable_ids)


def expected_product_versions_for(variable_ids, region_id=None):
    versions = {}
    for variable in variable_ids:
        prov = ALIAS_PROVENANCE.get(variable)
        if prov:
            versions[variable] = prov["product_version"]
    return versions


def validate_llm_payload(payload, context):
    if not isinstance(payload, dict):
        raise OutputValidationError(["payload is not a JSON object"])

    errors = []
    extra_fields = sorted(set(payload) - ALLOWED_FIELDS)
    if extra_fields:
        errors.append(f"unapproved extra fields rejected: {extra_fields}")
    missing_fields = sorted(REQUIRED_FIELDS - set(payload))
    if missing_fields:
        errors.append(f"missing required fields: {missing_fields}")
    if errors:
        raise OutputValidationError(errors)

    answer = payload["answer"]
    if not isinstance(answer, str) or not answer.strip():
        errors.append("answer must be a non-empty string")
    elif len(answer) > MAX_ANSWER_CHARS:
        errors.append(f"answer exceeds {MAX_ANSWER_CHARS} characters")

    cited = payload["cited_chunk_ids"]
    if not isinstance(cited, list) or not cited or not all(isinstance(c, str) and c.strip() for c in cited):
        errors.append("cited_chunk_ids must be a non-empty array of chunk id strings")
    else:
        outside = [chunk_id for chunk_id in cited if chunk_id not in context.allowed_chunk_ids]
        if outside:
            errors.append(
                f"cited chunk ids are not part of the current retrieved evidence set: {outside}"
            )

    suggested = payload.get("suggested_variable_ids", [])
    if not isinstance(suggested, list) or not all(isinstance(v, str) for v in suggested):
        errors.append("suggested_variable_ids must be an array of variable id strings")
    else:
        outside_vars = [v for v in suggested if v not in context.permitted_variable_ids]
        if outside_vars:
            errors.append(f"suggested variables outside the permitted set: {outside_vars}")

    versions = payload.get("product_versions", {})
    if not isinstance(versions, dict) or not all(
        isinstance(k, str) and isinstance(v, str) for k, v in versions.items()
    ):
        errors.append("product_versions must be an object of variable id to version string")
    else:
        for variable, version in versions.items():
            if variable not in context.permitted_variable_ids:
                errors.append(f"product_versions key outside the permitted set: {variable}")
            elif context.expected_product_versions.get(variable) != version:
                errors.append(
                    f"product version mismatch for {variable}: claimed {version!r}, "
                    f"registered {context.expected_product_versions.get(variable)!r}"
                )

    limitations = payload.get("limitations", [])
    if not isinstance(limitations, list) or not all(isinstance(s, str) for s in limitations):
        errors.append("limitations must be an array of strings")
        limitations = []

    if isinstance(answer, str) and answer.strip():
        errors.extend(_wording_violations(answer, context.permitted_variable_ids))

    if errors:
        raise OutputValidationError(errors)

    clean_limitations = [
        lim for lim in limitations if _passes_guardrails(lim, context.permitted_variable_ids)
    ]
    return _validated_output(payload, clean_limitations, context)


def _validated_output(payload, clean_limitations, context):
    citations = []
    for chunk_id in payload["cited_chunk_ids"]:
        chunk = context.chunk_records[chunk_id]
        citations.append(
            {
                "chunk_id": chunk["chunk_id"],
                "source_id": chunk["source_id"],
                "source_kind": chunk["source_kind"],
                "product_id": chunk.get("product_id"),
                "product_version": chunk.get("product_version"),
                "source_url": context.trusted_urls.get(chunk["source_id"]) or chunk.get("source_url"),
                "section_locator": chunk["section_locator"],
                "retrieved_timestamp": chunk["retrieved_timestamp"],
                "raw_source_hash": chunk["raw_source_hash"],
                "title": chunk.get("title"),
                "text": chunk["text"],
            }
        )
    return {
        "mode": "llm",
        "query": context.query,
        "status": context.local.get("status"),
        "reason_code": context.local.get("reason_code"),
        "variable_ids": context.local.get("variable_ids", []),
        "suggested_variable_ids": payload.get("suggested_variable_ids")
        or context.local.get("suggested_variable_ids", []),
        "answer": payload["answer"],
        "citations": citations,
        "context": context.local.get("context", {"definition_chunks": [], "limitation_chunks": []}),
        "availability": context.availability,
        "limitations": list(context.pipeline_limitations) + clean_limitations,
        "notes": context.local.get("notes", []),
        "validation": {
            "passed": True,
            "cited_chunk_ids": list(payload["cited_chunk_ids"]),
        },
    }
