import re

TASHKEEL = re.compile(r"[\u064b-\u0652\u0670\u0640\u06d6-\u06ed]")
ARABIC_LETTER = re.compile(r"[\u0600-\u06ff]")
TOKEN_SPLIT = re.compile(r"[^\w\u0600-\u06ff]+")
ARABIC_PUNCTUATION = re.compile(r"[\u060c\u061b\u061f\u06d4\u066a-\u066d]")

ARABIC_DIGIT_MAP = {
    "٠": "0", "١": "1", "٢": "2", "٣": "3", "٤": "4",
    "٥": "5", "٦": "6", "٧": "7", "٨": "8", "٩": "9",
    "۰": "0", "۱": "1", "۲": "2", "۳": "3", "۴": "4",
    "۵": "5", "۶": "6", "۷": "7", "۸": "8", "۹": "9",
}

PREFIXES = ("وال", "بال", "كال", "فال", "لل", "ال", "و", "ب", "ل", "ف", "ك")

CHAR_MAP = {
    "أ": "ا",
    "إ": "ا",
    "آ": "ا",
    "ٱ": "ا",
    "ة": "ه",
    "ى": "ي",
    "ؤ": "و",
    "ئ": "ي",
}


def strip_diacritics(text: str) -> str:
    return TASHKEEL.sub("", text)


def normalize_arabic_token(token: str) -> str:
    token = strip_diacritics(token)
    token = token.replace("ـ", "")
    for src, dst in CHAR_MAP.items():
        token = token.replace(src, dst)
    return token


def normalize_query(text: str) -> str:
    lowered = text.lower()
    for d_ar, d_en in ARABIC_DIGIT_MAP.items():
        lowered = lowered.replace(d_ar, d_en)
    lowered = ARABIC_PUNCTUATION.sub(" ", lowered)
    chars = []
    for ch in lowered:
        if ARABIC_LETTER.match(ch):
            chars.append(normalize_arabic_token(ch))
        else:
            chars.append(ch)
    return "".join(chars)


def tokenize(text: str) -> list:
    normalized = normalize_query(text)
    normalized = ARABIC_PUNCTUATION.sub(" ", normalized)
    raw = TOKEN_SPLIT.split(normalized)
    tokens = []
    for tok in raw:
        tok = tok.strip("_")
        if not tok:
            continue
        tokens.append(tok)
        if ARABIC_LETTER.search(tok):
            for prefix in PREFIXES:
                if tok.startswith(prefix) and len(tok) - len(prefix) >= 3:
                    stripped = tok[len(prefix):]
                    tokens.append(stripped)
                    if stripped.startswith("ال") and len(stripped) - 2 >= 3:
                        tokens.append(stripped[2:])
                    break
    return tokens


def has_arabic(text: str) -> bool:
    return bool(ARABIC_LETTER.search(text))


def split_mixed_tokens(text: str) -> dict:
    normalized = normalize_query(text)
    raw = TOKEN_SPLIT.split(normalized)
    arabic, latin = [], []
    for tok in raw:
        tok = tok.strip("_")
        if not tok:
            continue
        if ARABIC_LETTER.search(tok):
            arabic.append(tok)
        else:
            latin.append(tok)
    return {"arabic": arabic, "latin": latin}
