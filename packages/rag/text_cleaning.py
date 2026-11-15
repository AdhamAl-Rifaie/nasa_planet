import codecs
import re

PUA_MAP = {
    0xF020: " ",
    0xF022: '"',
    0xF02B: "+",
    0xF02D: "-",
    0xF02E: ".",
    0xF02F: "/",
    0xF03D: "=",
    0xF0B7: "\u2022",
    0xF0B5: "\u00b5",
    0xF061: "\u03b1",
    0xF062: "\u03b2",
    0xF063: "\u03b3",
    0xF064: "\u03b4",
    0xF065: "\u03b5",
    0xF066: "\u03c6",
    0xF067: "\u03b3",
    0xF068: "\u03b7",
    0xF069: "\u03b9",
    0xF06A: "\u03d5",
    0xF06B: "\u03ba",
    0xF06C: "\u03bb",
    0xF06D: "\u03bc",
    0xF06E: "\u03bd",
    0xF06F: "\u03bf",
    0xF070: "\u03c0",
    0xF071: "\u03b8",
    0xF072: "\u03c1",
    0xF073: "\u03c3",
    0xF074: "\u03c4",
    0xF075: "\u03c5",
    0xF077: "\u03c9",
    0xF078: "\u03be",
    0xF079: "\u03c8",
    0xF07A: "\u03b6",
    0xF041: "\u0391",
    0xF042: "\u0392",
    0xF043: "\u03a7",
    0xF044: "\u0394",
    0xF045: "\u0395",
    0xF046: "\u03a6",
    0xF047: "\u0393",
    0xF048: "\u0397",
    0xF049: "\u0399",
    0xF04B: "\u039a",
    0xF04C: "\u039b",
    0xF04D: "\u039c",
    0xF04E: "\u039d",
    0xF04F: "\u039f",
    0xF050: "\u03a0",
    0xF051: "\u0398",
    0xF052: "\u03a1",
    0xF053: "\u03a3",
    0xF054: "\u03a4",
    0xF055: "\u03a5",
    0xF057: "\u03a9",
    0xF058: "\u039e",
    0xF059: "\u03a8",
    0xF05A: "\u0396",
}

_MISC_FIXES = {
    "\u00a0": " ",
    "\u00ad": "",
    "\r\n": "\n",
    "\r": "\n",
}


def mixed_decode(data: bytes) -> str:
    try:
        return data.decode("utf-8")
    except UnicodeDecodeError:
        pass
    pieces = []
    ascii_run = bytearray()
    i = 0
    n = len(data)
    while i < n:
        if data[i] < 0x80:
            ascii_run.append(data[i])
            i += 1
            continue
        j = i
        while j < n and data[j] >= 0x80:
            j += 1
        if ascii_run:
            pieces.append(ascii_run.decode("ascii"))
            ascii_run.clear()
        pieces.append(_hybrid_decode(data[i:j]))
        i = j
    if ascii_run:
        pieces.append(ascii_run.decode("ascii"))
    return "".join(pieces)


def _hybrid_decode(run: bytes) -> str:
    try:
        return run.decode("utf-8")
    except UnicodeDecodeError:
        pass
    dec = codecs.getincrementaldecoder("utf-8")()
    out = []
    for b in run:
        try:
            piece = dec.decode(bytes([b]))
        except UnicodeDecodeError:
            dec.reset()
            piece = bytes([b]).decode("cp1252", errors="replace")
        if piece:
            out.append(piece)
    tail = dec.decode(b"", True)
    out.append(tail)
    return "".join(out)


def clean_text(text: str) -> str:
    for src, dst in _MISC_FIXES.items():
        text = text.replace(src, dst)
    chars = []
    for ch in text:
        cp = ord(ch)
        if 0xE000 <= cp <= 0xF8FF:
            mapped = PUA_MAP.get(cp)
            if mapped is not None:
                chars.append(mapped)
            continue
        chars.append(ch)
    text = "".join(chars)
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r" ?\n ?", "\n", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()
