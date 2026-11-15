import pytest

from packages.rag.text_cleaning import clean_text, mixed_decode


def test_mixed_decode_utf8_passthrough():
    data = "0.1° × 0.1° \u201cstoplight\u201d".encode("utf-8")
    assert mixed_decode(data) == "0.1° × 0.1° \u201cstoplight\u201d"


def test_mixed_decode_repairs_cp1252_degree_inside_utf8():
    data = "half-hourly 0.1\xb0x0.1\xb0 fields".encode("utf-8", "ignore")
    raw = b"half-hourly 0.1\xb0x0.1\xb0 fields"
    assert mixed_decode(raw) == "half-hourly 0.1°x0.1° fields"


def test_mixed_decode_keeps_curly_quotes_when_mixed():
    raw = b"\xe2\x80\x9cstoplight\xe2\x80\x9d and 0.1\xb0"
    assert mixed_decode(raw) == "\u201cstoplight\u201d and 0.1°"


def test_clean_text_maps_known_pua_glyphs():
    text = "delta \uef04 total \uf02b \uf02d \uf0b7"
    cleaned = clean_text(text.replace("\uef04", "\uf044"))
    assert "\u0394" in cleaned
    assert "+" in cleaned and "-" in cleaned and "\u2022" in cleaned


def test_clean_text_drops_unknown_pua():
    cleaned = clean_text("a \uf0fa b")
    assert "\uf0fa" not in cleaned
    assert "a  b" == cleaned or "a b" == cleaned


def test_clean_text_normalizes_whitespace_and_bullets():
    cleaned = clean_text("line one\r\n\u00a0 \tline   two\n\n\n\nline three")
    assert cleaned == "line one\nline two\n\nline three"


@pytest.mark.parametrize(
    "raw,expected",
    [
        (b"plain ascii", "plain ascii"),
        (b"caf\xc3\xa9", "café"),
        (b"\xb0C", "°C"),
    ],
)
def test_mixed_decode_parametrized(raw, expected):
    assert mixed_decode(raw) == expected
